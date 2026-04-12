#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from novel_utils import (
    count_total_chapter_chars,
    detect_current_chapter,
    detect_latest_chapter_file,
    extract_markdown_table_rows,
    extract_state_value,
    has_placeholder,
    load_due_foreshadow_ids,
    read_text,
    split_summary_entries,
    extract_summary_field,
    useful_lines,
)


HEALTH_DIGEST_LIMIT = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile layered next-chapter context for a chaseNovel project."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--chapter", type=int, help="Target chapter number")
    parser.add_argument("--output", help="Optional output markdown path")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(read_text(path))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def extract_next_goal(state_text: str) -> str:
    direct = extract_state_value(state_text, "下章预告")
    if direct and not has_placeholder(direct):
        return direct

    section_match = re.search(r"##\s*下章预告\s*(.*?)(?:\n##\s+|\Z)", state_text, re.S)
    if not section_match:
        return ""

    section_text = section_match.group(1)
    result = extract_state_value(section_text, "计划内容") or extract_state_value(section_text, "章节目标")
    return "" if has_placeholder(result) else result


def first_nonempty_lines(text: str, limit: int) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()][:limit]


def collect_latest_chapter_excerpt(project_dir: Path) -> str:
    _, latest_path = detect_latest_chapter_file(project_dir)
    if latest_path is None:
        return ""
    return "\n".join(first_nonempty_lines(read_text(latest_path), 16))


def parse_due_foreshadow_details(memory_dir: Path, target_chapter: int) -> list[dict[str, str]]:
    foreshadow_text = read_text(memory_dir / "foreshadowing.md")
    rows = extract_markdown_table_rows(foreshadow_text, "活跃伏笔")
    if len(rows) <= 1:
        rows = extract_markdown_table_rows(foreshadow_text, "📌 未回收伏笔(Pending)")

    details: list[dict[str, str]] = []
    for row in rows[1:]:
        if len(row) < 9:
            continue
        due_text = row[6].strip()
        chapter_match = re.search(r"(\d+)", due_text)
        if not chapter_match or int(chapter_match.group(1)) > target_chapter:
            continue
        status = row[8].strip()
        if any(flag in status for flag in ("已回收", "已废弃", "宸插洖鏀?", "宸插簾寮?")):
            continue
        details.append(
            {
                "id": row[0].strip(),
                "content": row[2].strip(),
                "who_knows": row[3].strip(),
                "trigger": row[4].strip(),
                "due_chapter": due_text,
                "status": status or "待回收",
            }
        )
    return details


def parse_active_promises(memory_dir: Path, target_chapter: int) -> list[dict[str, str]]:
    payoff_text = read_text(memory_dir / "payoff_board.md")
    rows = extract_markdown_table_rows(payoff_text, "活跃承诺")
    if len(rows) <= 1:
        rows = extract_markdown_table_rows(payoff_text, "娲昏穬鎵胯")

    active: list[dict[str, str]] = []
    for row in rows[1:]:
        if len(row) < 8 or not row[0].strip():
            continue
        expected_window = row[4].strip()
        window_match = re.search(r"(\d+)", expected_window)
        due_soon = bool(window_match and int(window_match.group(1)) <= target_chapter + 3)
        pressure = row[6].strip()
        status = row[5].strip()
        if any(flag in status for flag in ("已兑现", "已废弃", "宸插厬鐜?", "宸插簾寮?")):
            continue
        if due_soon or "🔴" in pressure or "馃敶" in pressure or "延迟" in status or "寤惰繜" in status or "待兑现" in status:
            active.append(
                {
                    "id": row[0].strip(),
                    "type": row[1].strip(),
                    "content": row[2].strip(),
                    "window": expected_window or "未填写",
                    "status": status or "待兑现",
                    "pressure": pressure or "未填写",
                }
            )
    return active


def parse_character_hotspots(memory_dir: Path, target_chapter: int) -> list[dict[str, str]]:
    arc_text = read_text(memory_dir / "character_arcs.md")
    rows = extract_markdown_table_rows(arc_text, "核心角色弧表")
    hotspots: list[dict[str, str]] = []
    for row in rows[1:]:
        if len(row) < 8:
            continue
        next_window = row[6].strip()
        risk = row[7].strip()
        chapter_numbers = [int(match) for match in re.findall(r"(\d+)", next_window)]
        due_now = any(abs(number - target_chapter) <= 3 for number in chapter_numbers)
        if risk or due_now:
            hotspots.append(
                {
                    "character": row[0].strip(),
                    "stage": row[2].strip(),
                    "goal": row[3].strip(),
                    "next_window": next_window or "未填写",
                    "risk": risk or "无显式风险",
                }
            )
    if hotspots:
        return hotspots[:6]

    fallback: list[dict[str, str]] = []
    for row in rows[1:4]:
        if len(row) < 8 or not row[0].strip():
            continue
        fallback.append(
            {
                "character": row[0].strip(),
                "stage": row[2].strip(),
                "goal": row[3].strip(),
                "next_window": row[6].strip() or "未填写",
                "risk": row[7].strip() or "未填写",
            }
        )
    return fallback


def render_summary_snapshot(entries: list[dict[str, str]], limit: int) -> list[str]:
    lines: list[str] = []
    for entry in entries[-limit:]:
        chapter = entry.get("chapter", "") or "?"
        title = entry.get("title", "") or "未命名"
        core_event = extract_summary_field(entry["body"], "核心事件") or title
        hook = extract_summary_field(entry["body"], "启下") or extract_summary_field(entry["body"], "伏笔")
        try:
            chapter_label = f"第{int(chapter):03d}章"
        except ValueError:
            chapter_label = f"第{chapter}章"
        lines.append(f"{chapter_label}《{title}》：{core_event}")
        if hook:
            lines.append(f"  启下：{hook}")
    return lines


def parse_mid_archive(memory_dir: Path) -> list[str]:
    mid_path = memory_dir / "summaries" / "mid.md"
    if not mid_path.exists():
        return []
    return useful_lines(read_text(mid_path), 8)


def load_health_digest(project_dir: Path) -> list[str]:
    candidates = [
        project_dir / "05_reports" / "pipeline_report.json",
        project_dir / "00_memory" / "retrieval" / "health_digest.json",
        project_dir / "00_memory" / "retrieval" / "dashboard_cache.json",
    ]
    for path in candidates:
        payload = load_json(path)
        digest = payload.get("health_digest", [])
        if isinstance(digest, list) and digest:
            return [str(item) for item in digest[:HEALTH_DIGEST_LIMIT]]
    return []


def build_payload(project_dir: Path, target_chapter: int, output_path: Path) -> dict[str, object]:
    memory_dir = project_dir / "00_memory"
    reports_dir = project_dir / "05_reports"
    plan_text = read_text(memory_dir / "plan.md")
    state_text = read_text(memory_dir / "state.md")
    arc_text = read_text(memory_dir / "arc_progress.md")
    findings_text = read_text(memory_dir / "findings.md")
    recent_text = read_text(memory_dir / "summaries" / "recent.md")
    voice_text = read_text(memory_dir / "voice.md")
    style_text = read_text(memory_dir / "style.md")
    volume_blueprint_text = read_text(project_dir / "01_outline" / "volume_blueprint.md")

    active_volume = extract_state_value(state_text, "当前卷")
    active_arc = extract_state_value(state_text, "当前弧")
    current_place = extract_state_value(state_text, "当前地点")
    next_goal = extract_next_goal(state_text)
    due_ids = load_due_foreshadow_ids(project_dir, target_chapter)
    due_foreshadows = parse_due_foreshadow_details(memory_dir, target_chapter)
    active_promises = parse_active_promises(memory_dir, target_chapter)
    character_hotspots = parse_character_hotspots(memory_dir, target_chapter)
    repeat_report = load_json(reports_dir / "repeat_report.json")
    volume_report = load_json(reports_dir / "volume_audit.json")
    milestone_report = load_json(reports_dir / "milestone_audit.json")
    recent_entries = split_summary_entries(recent_text)
    health_digest = load_health_digest(project_dir)

    payload = {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "chapter": target_chapter,
        "output": output_path.as_posix(),
        "output_json": output_path.with_suffix(".json").as_posix(),
        "active_volume": active_volume or "未识别",
        "active_arc": active_arc or "未识别",
        "current_place": current_place or "未识别",
        "next_goal": next_goal or "待明确",
        "total_effective_words": count_total_chapter_chars(project_dir),
        "plan_lines": useful_lines(plan_text, 8),
        "volume_blueprint_lines": useful_lines(volume_blueprint_text, 10),
        "state_lines": useful_lines(state_text, 12),
        "arc_lines": useful_lines(arc_text, 10),
        "finding_lines": useful_lines(findings_text, 8),
        "recent_snapshot": render_summary_snapshot(recent_entries, 3),
        "mid_snapshot": parse_mid_archive(memory_dir),
        "voice_lines": useful_lines(voice_text or style_text, 10),
        "due_foreshadow_ids": due_ids,
        "due_foreshadows": due_foreshadows,
        "active_promises": active_promises,
        "character_hotspots": character_hotspots,
        "repeat_warnings": [str(item) for item in repeat_report.get("warnings", [])[:4]],
        "volume_warnings": [str(item) for item in volume_report.get("warnings", [])[:4]],
        "milestone_warnings": [str(item) for item in milestone_report.get("warnings", [])[:4]],
        "health_digest": health_digest,
        "latest_excerpt": collect_latest_chapter_excerpt(project_dir),
        "warnings": [],
    }

    warnings = payload["warnings"]
    if not payload["plan_lines"]:
        warnings.append("缺少 plan.md 主线摘要，深记忆检索将失去全书主线锚。")
    if not payload["volume_blueprint_lines"]:
        warnings.append("缺少 volume_blueprint.md，卷级目标和收束节点无法前置压入上下文。")
    if not payload["character_hotspots"]:
        warnings.append("未识别到角色弧热点，人物推进提醒会偏弱。")
    if not payload["active_promises"] and target_chapter >= 10:
        warnings.append("当前未识别到高压承诺，可能是 payoff_board 没同步，而不是真的没有债务。")
    if not payload["latest_excerpt"]:
        warnings.append("当前没有正文章节，上一章摘录将为空。")
    if not due_foreshadows:
        warnings.append("当前未识别到到期伏笔详情。")
    if not payload["health_digest"]:
        warnings.append("当前未收到风险摘要，建议先运行 chase check 或 dashboard 生成总控摘要。")
    payload["warning_count"] = len(warnings)
    payload["status"] = "warn" if warnings else "pass"
    payload["report_paths"] = {
        "markdown": output_path.as_posix(),
        "json": output_path.with_suffix(".json").as_posix(),
    }
    return payload


def render_markdown(payload: dict[str, object]) -> str:
    def render_items(items: list[str], empty_text: str) -> list[str]:
        return [f"- {item}" for item in items] if items else [f"- {empty_text}"]

    due_foreshadow_lines = [
        f"- `{item['id']}` {item['content']} / 触发：{item['trigger'] or '未写'} / 谁知道：{item['who_knows'] or '未写'} / 状态：{item['status']}"
        for item in payload["due_foreshadows"]
    ] or ["- 当前无到期伏笔详情"]

    promise_lines = [
        f"- `{item['id']}` [{item['type']}] {item['content']} / 窗口：{item['window']} / 状态：{item['status']} / 压力：{item['pressure']}"
        for item in payload["active_promises"]
    ] or ["- 当前未识别到高压承诺"]

    hotspot_lines = [
        f"- `{item['character']}` 阶段：{item['stage']} / 目标：{item['goal']} / 下一窗口：{item['next_window']} / 风险：{item['risk']}"
        for item in payload["character_hotspots"]
    ] or ["- 当前未识别到角色热点"]

    lines = [
        f"# Next Context - 第{int(payload['chapter']):03d}章",
        "",
        f"- 生成时间：{payload['generated_at']}",
        f"- 项目：{payload['project']}",
        f"- 当前卷 / 当前弧：{payload['active_volume']} / {payload['active_arc']}",
        f"- 当前地点：{payload['current_place']}",
        f"- 下章目标：{payload['next_goal']}",
        f"- 当前有效总字数：{payload['total_effective_words']}",
        "",
        "## 全书主线摘要",
        *render_items(payload["plan_lines"], "缺少 plan.md 摘要"),
        "",
        "## 当前卷蓝图",
        *render_items(payload["volume_blueprint_lines"], "缺少 volume_blueprint.md"),
        "",
        "## 当前状态摘要",
        *render_items(payload["state_lines"], "缺少 state.md 摘要"),
        "",
        "## 卷级推进摘要",
        *render_items(payload["arc_lines"], "缺少 arc_progress.md 摘要"),
        "",
        "## 角色与关系热点",
        *hotspot_lines,
        "",
        "## 承诺债务",
        *promise_lines,
        "",
        "## 本章到期伏笔",
        *due_foreshadow_lines,
        "",
        "## 最近三章快照（L1）",
        *render_items(payload["recent_snapshot"], "暂无 recent.md 摘要"),
        "",
        "## 中层归档（L2）",
        *render_items(payload["mid_snapshot"], "暂无 mid.md 归档"),
        "",
        "## 待跟进发现",
        *render_items(payload["finding_lines"], "暂无 findings.md"),
        "",
        "## 风格与声音约束",
        *render_items(payload["voice_lines"], "暂无 voice/style 约束"),
        "",
        "## 风险摘要",
        *render_items(payload["health_digest"], "暂无 health_digest"),
        "",
        "## 外部审计预警",
        *render_items(payload["repeat_warnings"], "暂无 repeat_report 预警"),
        *render_items(payload["volume_warnings"], "暂无 volume_audit 预警"),
        *render_items(payload["milestone_warnings"], "暂无 milestone_audit 预警"),
        "",
        "## 上一章摘录",
        "```md",
        payload["latest_excerpt"] or "暂无章节正文",
        "```",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    project_dir = Path(args.project).resolve()
    state_text = read_text(project_dir / "00_memory" / "state.md")
    target_chapter = args.chapter or max(detect_current_chapter(state_text) + 1, 1)
    output_path = (
        Path(args.output).resolve()
        if args.output
        else project_dir / "00_memory" / "retrieval" / "next_context.md"
    )

    payload = build_payload(project_dir, target_chapter, output_path)
    markdown = render_markdown(payload)

    if not args.dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        output_path.with_suffix(".json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"warning_count={payload['warning_count']}")
        print(f"chapter={payload['chapter']}")
        print(f"output={payload['report_paths']['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
