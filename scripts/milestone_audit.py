#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from novel_utils import (
    count_chapter_files,
    count_total_chapter_chars,
    detect_current_chapter,
    detect_project_genre,
    detect_project_subgenre,
    extract_markdown_table_rows,
    read_text,
)


GENRE_MILESTONE_PROFILES = {
    "都市/系统流": {
        "checkpoint_words": 80000,
        "due_soon_window": 3,
        "profile_note": "都市系统流快反馈强，阶段复盘要更频繁，关键节点也要更早压近。",
    },
    "历史/权谋": {
        "checkpoint_words": 120000,
        "due_soon_window": 6,
        "profile_note": "历史权谋铺陈更长，十万字节点可放宽，但关键节点窗口要提前看。",
    },
    "末世": {
        "checkpoint_words": 90000,
        "due_soon_window": 4,
        "profile_note": "末世危机密度高，节点复盘应更早，避免连续危机疲劳。",
    },
    "玄幻/修仙": {
        "checkpoint_words": 100000,
        "due_soon_window": 5,
        "profile_note": "玄幻修仙按通用长篇节奏跑，但要盯住升级大节点是否换挡。",
    },
    "仙侠/苟道": {
        "checkpoint_words": 110000,
        "due_soon_window": 6,
        "profile_note": "苟道可略慢，但长期节点不能一直后延成假稳健。",
    },
    "种田": {
        "checkpoint_words": 120000,
        "due_soon_window": 6,
        "profile_note": "种田经营卷幅偏长，节点复盘可稍慢，但阶段目标要盯得更清。",
    },
    "盗墓/民国": {
        "checkpoint_words": 90000,
        "due_soon_window": 4,
        "profile_note": "盗墓民国谜面与危机并行，节点复盘应较早防断谜疲劳。",
    },
    "默认": {
        "checkpoint_words": 100000,
        "due_soon_window": 5,
        "profile_note": "未识别题材时使用通用长篇节点阈值。",
    },
}

SUBGENRE_MILESTONE_OVERRIDES = {
    ("都市/系统流", "低位反压"): {
        "checkpoint_words": 70000,
        "due_soon_window": 3,
        "profile_note": "低位反压卷讲究快翻身，阶段复盘要更早，避免受压段拖长。",
    },
    ("都市/系统流", "身份揭面"): {
        "checkpoint_words": 80000,
        "due_soon_window": 4,
        "profile_note": "身份揭面卷要更频繁检查揭面节奏，防止长期只吐身份胃口。",
    },
    ("都市/系统流", "规则碾压"): {
        "checkpoint_words": 90000,
        "due_soon_window": 4,
        "profile_note": "规则碾压卷允许更大局，但每个阶段都要有规则层结果。",
    },
    ("历史/权谋", "边关争霸"): {
        "checkpoint_words": 100000,
        "due_soon_window": 5,
        "profile_note": "边关争霸要更频繁回看军权、战场与粮道节点，避免边地循环。",
    },
    ("历史/权谋", "朝堂咬合"): {
        "checkpoint_words": 130000,
        "due_soon_window": 6,
        "profile_note": "朝堂咬合铺陈更长，节点可放宽，但关键站队和圣意必须前瞻。",
    },
    ("末世", "囤货"): {
        "checkpoint_words": 80000,
        "due_soon_window": 3,
        "profile_note": "囤货卷最怕一直收集不换局，复盘节点应更早触发。",
    },
    ("末世", "安全屋成型"): {
        "checkpoint_words": 90000,
        "due_soon_window": 4,
        "profile_note": "安全屋成型卷要更快复盘防线、准入和守点压力。",
    },
    ("末世", "秩序治理"): {
        "checkpoint_words": 100000,
        "due_soon_window": 5,
        "profile_note": "秩序治理卷能稍放长，但规则、治理与势力债务不能积压太久。",
    },
}

THRESHOLD_LABELS = {
    "checkpoint_words": "节点字数",
    "due_soon_window": "节点预警窗口",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit hard milestones and checkpoint reviews for a chaseNovel project."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Do not write report files")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(read_text(path))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def parse_chapter_number(text: str) -> int | None:
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else None


def parse_plan_milestones(plan_text: str) -> list[dict[str, object]]:
    rows = extract_markdown_table_rows(plan_text, "关键节点锚点表（写前硬校验，违反则阻断）")
    if len(rows) <= 1:
        rows = extract_markdown_table_rows(plan_text, "关键节点锚点表")

    items: list[dict[str, object]] = []
    for row in rows[1:]:
        if len(row) < 4 or not row[0].strip():
            continue
        items.append(
            {
                "description": row[0].strip(),
                "earliest": parse_chapter_number(row[1]),
                "latest": parse_chapter_number(row[2]),
                "status": row[3].strip(),
            }
        )
    return items


def is_done_status(text: str) -> bool:
    return "已完成" in text or "✔" in text or text.strip() == "完成"


def apply_adjustment(
    profile: dict[str, object],
    base_profile: dict[str, object],
    adjustments: dict[str, dict[str, object]],
    key: str,
    delta: int,
    reason: str,
    minimum: int = 1,
) -> None:
    if not delta:
        return
    current_value = int(profile[key])
    next_value = max(minimum, current_value + delta)
    actual_delta = next_value - current_value
    if not actual_delta:
        return
    profile[key] = next_value
    entry = adjustments.setdefault(
        key,
        {
            "base": int(base_profile[key]),
            "delta": 0,
            "effective": current_value,
            "reasons": [],
        },
    )
    entry["delta"] = int(entry["delta"]) + actual_delta
    entry["effective"] = next_value
    entry["reasons"].append(reason)


def compute_dynamic_profile(
    base_profile: dict[str, object],
    repeat_report: dict[str, object],
    arc_report: dict[str, object],
    foreshadow_report: dict[str, object],
    overdue_count: int,
    chapter_count: int,
) -> tuple[dict[str, object], dict[str, dict[str, object]], dict[str, object]]:
    effective_profile = dict(base_profile)
    adjustments: dict[str, dict[str, object]] = {}

    repeat_warning_count = len(repeat_report.get("warnings", []))
    midgame_summary = repeat_report.get("midgame_fatigue", {}).get("summary", {})
    max_result_streak = int(midgame_summary.get("max_result_streak", 0) or 0)
    max_conflict_streak = int(midgame_summary.get("max_conflict_streak", 0) or 0)
    max_hook_streak = int(midgame_summary.get("max_hook_streak", 0) or 0)
    stalled_arc_count = int(arc_report.get("stalled_arc_count", 0) or 0)
    overdue_foreshadow_count = len(foreshadow_report.get("overdue", []))
    chapter_pressure = max(max_result_streak, max_conflict_streak, max_hook_streak)

    signals = {
        "chapter_count": chapter_count,
        "repeat_warning_count": repeat_warning_count,
        "overdue_milestone_count": overdue_count,
        "stalled_arc_count": stalled_arc_count,
        "overdue_foreshadow_count": overdue_foreshadow_count,
        "midgame_fatigue": {
            "max_result_streak": max_result_streak,
            "max_conflict_streak": max_conflict_streak,
            "max_hook_streak": max_hook_streak,
        },
    }

    if chapter_count < 8:
        return effective_profile, adjustments, signals

    if chapter_pressure >= 3 or repeat_warning_count >= 4:
        apply_adjustment(
            effective_profile,
            base_profile,
            adjustments,
            "checkpoint_words",
            -10000,
            "中盘疲劳抬头，节点复盘提前一档。",
            minimum=60000,
        )

    if overdue_count > 0 or stalled_arc_count > 0:
        apply_adjustment(
            effective_profile,
            base_profile,
            adjustments,
            "due_soon_window",
            1,
            "已有节点或弧线债务，提前拉长前瞻窗口。",
        )

    if overdue_count >= 2 or overdue_foreshadow_count >= 3:
        apply_adjustment(
            effective_profile,
            base_profile,
            adjustments,
            "checkpoint_words",
            -10000,
            "节点/伏笔债务堆积，字数节点继续前压。",
            minimum=60000,
        )

    return effective_profile, adjustments, signals


def build_payload(project_dir: Path) -> dict[str, object]:
    memory_dir = project_dir / "00_memory"
    reports_dir = project_dir / "05_reports"
    plan_text = read_text(memory_dir / "plan.md")
    state_text = read_text(memory_dir / "state.md")
    genre = detect_project_genre(project_dir)
    subgenre = detect_project_subgenre(project_dir, genre)
    base_profile = dict(GENRE_MILESTONE_PROFILES.get(genre, GENRE_MILESTONE_PROFILES["默认"]))
    base_profile.update(SUBGENRE_MILESTONE_OVERRIDES.get((genre, subgenre), {}))
    current_chapter = detect_current_chapter(state_text)
    chapter_count = count_chapter_files(project_dir)
    total_words = count_total_chapter_chars(project_dir)
    milestones = parse_plan_milestones(plan_text)
    repeat_report = load_json(reports_dir / "repeat_report.json")
    arc_report = load_json(reports_dir / "arc_health.json")
    foreshadow_report = load_json(reports_dir / "foreshadow_heatmap.json")

    overdue: list[dict[str, object]] = []
    for item in milestones:
        latest = item["latest"]
        if latest is not None and latest < current_chapter and not is_done_status(str(item["status"])):
            overdue.append(item)

    effective_profile, dynamic_adjustments, dynamic_signals = compute_dynamic_profile(
        base_profile,
        repeat_report,
        arc_report,
        foreshadow_report,
        len(overdue),
        chapter_count,
    )

    due_soon: list[dict[str, object]] = []
    for item in milestones:
        earliest = item["earliest"]
        latest = item["latest"]
        if latest is not None and latest < current_chapter and not is_done_status(str(item["status"])):
            continue
        if (
            earliest is not None
            and earliest <= current_chapter + int(effective_profile["due_soon_window"])
            and not is_done_status(str(item["status"]))
        ):
            due_soon.append(item)

    crossed_nodes = total_words // int(effective_profile["checkpoint_words"])
    missing_node_reviews: list[str] = []
    node_review_dir = project_dir / "05_reports" / "node_reviews"
    for node_index in range(1, crossed_nodes + 1):
        node_name = f"node_{node_index * int(effective_profile['checkpoint_words']) // 1000}k.md"
        if not (node_review_dir / node_name).exists():
            missing_node_reviews.append(node_name)

    warnings: list[str] = []
    if overdue:
        warnings.append(f"存在 {len(overdue)} 个已超期但未完成的关键节点。")
    if missing_node_reviews:
        warnings.append(
            f"{genre} 题材已跨过 {crossed_nodes} 个 {int(effective_profile['checkpoint_words']) // 1000}k 节点，但缺少 {len(missing_node_reviews)} 份节点复盘。"
        )
    if due_soon and not overdue:
        warnings.append(
            f"{genre} 题材未来 {effective_profile['due_soon_window']} 章内有 {len(due_soon)} 个关键节点即将到窗。"
        )

    return {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "warn" if warnings else "pass",
        "genre": genre,
        "subgenre": subgenre or "未识别",
        "genre_profile": base_profile,
        "effective_profile": effective_profile,
        "dynamic_adjustments": dynamic_adjustments,
        "dynamic_signals": dynamic_signals,
        "current_chapter": current_chapter,
        "chapter_count": chapter_count,
        "total_effective_words": total_words,
        "crossed_100k_nodes": crossed_nodes,
        "crossed_checkpoint_nodes": crossed_nodes,
        "checkpoint_words": int(effective_profile["checkpoint_words"]),
        "due_soon_window": int(effective_profile["due_soon_window"]),
        "overdue_milestones": overdue,
        "due_soon_milestones": due_soon[:8],
        "missing_node_reviews": missing_node_reviews,
        "warnings": warnings,
        "warning_count": len(warnings),
    }


def render_dynamic_adjustments(payload: dict[str, object]) -> list[str]:
    adjustments = payload.get("dynamic_adjustments", {})
    if not adjustments:
        return ["- 动态修正：无"]
    lines: list[str] = []
    for key, value in adjustments.items():
        label = THRESHOLD_LABELS.get(key, key)
        reasons = "；".join(value.get("reasons", []))
        lines.append(
            f"- {label}：{value['base']} → {value['effective']} ({value['delta']:+d}) / {reasons}"
        )
    return lines


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# 关键节点与字数审计",
        "",
        f"- 项目：`{payload['project']}`",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 题材：`{payload['genre']}`",
        f"- 子类型：`{payload['subgenre']}`",
        f"- 当前章节：`第{payload['current_chapter']:03d}章`",
        f"- 当前章节文件数：`{payload['chapter_count']}`",
        f"- 有效总字数：`{payload['total_effective_words']}`",
        f"- 生效节点字数：`{payload['checkpoint_words']}`",
        f"- 已跨越节点数：`{payload['crossed_checkpoint_nodes']}`",
        "",
        "## 题材阈值",
        f"- 说明：{payload['genre_profile']['profile_note']}",
        f"- 基础节点字数：{payload['genre_profile']['checkpoint_words']}",
        f"- 基础预警窗口：{payload['genre_profile']['due_soon_window']} 章",
        "",
        "## 动态阈值",
        f"- 生效节点字数：{payload['effective_profile']['checkpoint_words']}",
        f"- 生效预警窗口：{payload['effective_profile']['due_soon_window']} 章",
    ]
    lines.extend(render_dynamic_adjustments(payload))
    lines.extend(["", "## 超期关键节点"])
    if payload["overdue_milestones"]:
        for item in payload["overdue_milestones"]:
            lines.append(
                f"- {item['description']} / 最晚={item['latest']} / 当前状态={item['status']}"
            )
    else:
        lines.append("- 无")
    lines.extend(["", "## 即将到窗节点"])
    if payload["due_soon_milestones"]:
        for item in payload["due_soon_milestones"]:
            lines.append(
                f"- {item['description']} / 最早={item['earliest']} / 最晚={item['latest']} / 当前状态={item['status']}"
            )
    else:
        lines.append("- 无")
    lines.extend(["", "## 缺失节点复盘"])
    if payload["missing_node_reviews"]:
        lines.extend(f"- {item}" for item in payload["missing_node_reviews"])
    else:
        lines.append("- 无")
    lines.extend(["", "## 预警"])
    if payload["warnings"]:
        lines.extend(f"- {item}" for item in payload["warnings"])
    else:
        lines.append("- 无")
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    project_dir = Path(args.project).resolve()
    reports_dir = project_dir / "05_reports"
    payload = build_payload(project_dir)
    md_path = reports_dir / "milestone_audit.md"
    json_path = reports_dir / "milestone_audit.json"
    payload["report_paths"] = {
        "markdown": md_path.as_posix(),
        "json": json_path.as_posix(),
    }

    if not args.dry_run:
        reports_dir.mkdir(parents=True, exist_ok=True)
        (reports_dir / "node_reviews").mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_markdown(payload), encoding="utf-8")
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"warning_count={payload['warning_count']}")
        print(f"markdown={payload['report_paths']['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
