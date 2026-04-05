#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from language_audit import analyze_text, parse_style_file
from novel_utils import (
    CHAPTER_PATTERN,
    detect_existing_chapter_file,
    detect_latest_chapter_file,
    extract_markdown_table_rows,
    extract_section_body,
    read_text,
    render_list,
)


DANGER_KEYWORDS = (
    "遇刺", "刺杀", "刺客", "追杀", "围杀", "跟踪", "暴露", "身份",
    "搜查", "搜捕", "潜入", "危机", "危险", "截杀", "埋伏", "伏杀"
)
DEFAULT_EMPTY_VALUES = {"", "—", "无", "暂无", "未设定", "未开始", "0"}
GOLDEN_THREE_EVENT_KEYWORDS = {
    1: ("危机", "机会", "羞辱", "异常", "冲突", "追杀", "压迫", "末世", "系统", "入局"),
    2: ("反击", "行动", "选择", "应对", "破局", "尝试", "兑现", "入局", "推进"),
    3: ("目标", "承诺", "路线", "野心", "长期", "阶段", "机缘", "强敌", "站队"),
}
GOLDEN_THREE_HOOK_KEYWORDS = ("危机", "暴露", "强敌", "选择", "真相", "身份", "机缘", "名额", "下一步", "站队")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate chapter-level continuity gate reports for chaseNovel projects."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--chapter-no", type=int, help="Target chapter number")
    parser.add_argument("--chapter", help="Path to a specific chapter markdown file")
    parser.add_argument(
        "--templates-root",
        help="Path to the chaseNovel templates directory; defaults to ../templates",
    )
    parser.add_argument("--style", help="Path to a specific style.md file")
    parser.add_argument("--skip-language", action="store_true", help="Skip language audit integration")
    parser.add_argument("--rewrite-out", help="Optional output path for the full suggested rewrite")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    return parser.parse_args()


def normalize_value(value: str) -> str:
    return value.strip().strip("`").strip()


def is_effectively_empty(value: str) -> bool:
    return normalize_value(value) in DEFAULT_EMPTY_VALUES


def extract_line_value(content: str, label: str) -> str:
    match = re.search(rf"{re.escape(label)}：(.+)", content)
    if not match:
        return ""
    return match.group(1).strip()

def has_non_placeholder_row(rows: list[list[str]]) -> bool:
    if len(rows) <= 1:
        return False
    for row in rows[1:]:
        if any(not is_effectively_empty(cell) and "暂无" not in cell for cell in row):
            return True
    return False


def section_has_meaningful_bullets(content: str, heading_variants: list[str]) -> bool:
    body = extract_section_body(content, heading_variants)
    if not body:
        return False
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("-") or stripped.startswith("1.") or stripped.startswith("2.") or stripped.startswith("3."):
            return True
        if stripped.startswith("**") and "：" in stripped:
            return True
    return False


def extract_absolute_time_from_timeline(content: str) -> str:
    for label in ("故事开局时间点", "绝对纪年"):
        value = extract_line_value(content, f"**{label}**")
        if value:
            return value
    match = re.search(r"故事开局时间点\*\*：(.+)", content)
    if match:
        return match.group(1).strip()
    return ""


def infer_absolute_time_from_chapter(content: str) -> str:
    match = re.search(r"(隆安[^\n。]{0,20})", content)
    if match:
        return match.group(1).strip("，。 ")
    return ""


def infer_current_place_from_chapter(content: str) -> str:
    matches = re.findall(r"[，。]\s*([^，。\n]{1,14}(?:驿|城|关|楼|营|府|宫|殿|阁|坊|巷))", content)
    blocked_tokens = ("殿", "公公", "声音", "北风", "冷风", "火光")
    for item in matches:
        candidate = item.strip("“”\"' ，。")
        if not candidate:
            continue
        if any(candidate.startswith(token) for token in blocked_tokens):
            continue
        if len(candidate) < 2:
            continue
        return candidate
    return ""


def detect_danger_keywords(content: str) -> list[str]:
    return [keyword for keyword in DANGER_KEYWORDS if keyword in content]


def evaluate_golden_three_progress(chapter_no: int, chapter_content: str) -> list[str]:
    if chapter_no not in (1, 2, 3):
        return []

    warnings: list[str] = []
    keywords = GOLDEN_THREE_EVENT_KEYWORDS[chapter_no]
    if not any(keyword in chapter_content for keyword in keywords):
        if chapter_no == 1:
            warnings.append("第1章未明显识别到危机 / 机会 / 压迫 / 异常信号，开篇抓手可能偏弱。")
        elif chapter_no == 2:
            warnings.append("第2章未明显识别到行动推进 / 破局 / 选择信号，主角主动性可能不足。")
        else:
            warnings.append("第3章未明显识别到长期目标 / 路线 / 强敌 / 站队信号，长期承诺可能没有立住。")

    tail = "\n".join(line.strip() for line in chapter_content.splitlines() if line.strip())[-180:]
    if chapter_no == 3 and not any(keyword in tail for keyword in GOLDEN_THREE_HOOK_KEYWORDS):
        warnings.append("第3章结尾未明显识别到强钩子信号，可能拖不动第4章。")
    return warnings


def chapter_text_matches(chapter_text: str, chapter_no: int) -> bool:
    match = CHAPTER_PATTERN.search(chapter_text)
    if not match:
        return False
    return int(match.group(1)) == chapter_no


def map_overall_verdict(continuity_verdict: str, language_verdict: str, skip_language: bool) -> str:
    if continuity_verdict == "block":
        return "block"
    if not skip_language and language_verdict == "rewrite":
        return "block"
    if continuity_verdict == "warn":
        return "warn"
    if not skip_language and language_verdict == "warn":
        return "warn"
    return "pass"


def summarize_language_analysis(language_analysis: dict[str, object]) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    for item in language_analysis["issues"]:
        message = f"{item.get('position', 'global')} {item['type']}：{item['reason']}"
        if item["severity"] == "high":
            blockers.append(message)
        else:
            warnings.append(message)
    return blockers, warnings


def render_language_suggestions(suggestions: list[dict[str, object]]) -> str:
    if not suggestions:
        return "- 无局部改写建议"

    blocks: list[str] = []
    for item in suggestions:
        blocks.extend([
            f"### {item.get('position', 'global')} / {item.get('issue_type', 'unknown')}",
            f"- 原文：{item.get('original', '')}",
            f"- 建议：{item.get('strategy', '')}",
            f"- 试改：{item.get('suggested_rewrite', '')}",
            "",
        ])
    return "\n".join(blocks).rstrip()


def load_planning_review(project_dir: Path, chapter_no: int) -> dict[str, object]:
    path = project_dir / "04_gate" / f"ch{chapter_no:03d}" / "planning_review.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(read_text(path))
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        return {}


def build_gate_analysis(
    project_dir: Path,
    chapter_no: int,
    chapter_path: Path,
    style_path: Path,
    skip_language: bool,
) -> dict[str, object]:
    chapter_content = read_text(chapter_path)
    state_content = read_text(project_dir / "00_memory" / "state.md")
    timeline_content = read_text(project_dir / "00_memory" / "timeline.md")
    foreshadowing_content = read_text(project_dir / "00_memory" / "foreshadowing.md")
    planning_review = load_planning_review(project_dir, chapter_no)
    latest_chapter_no, _ = detect_latest_chapter_file(project_dir)
    historical_mode = latest_chapter_no > 0 and chapter_no < latest_chapter_no

    warnings: list[str] = []
    blockers: list[str] = []

    absolute_time = extract_line_value(state_content, "当前绝对时间")
    relative_time = extract_line_value(state_content, "距上章过去")
    current_place = extract_line_value(state_content, "当前地点")
    current_chapter = extract_line_value(state_content, "当前章节")

    if is_effectively_empty(absolute_time):
        absolute_time = extract_absolute_time_from_timeline(timeline_content) or infer_absolute_time_from_chapter(chapter_content)
    if is_effectively_empty(current_place):
        current_place = infer_current_place_from_chapter(chapter_content)

    if is_effectively_empty(absolute_time) and not historical_mode:
        blockers.append("`state.md` 缺少“当前绝对时间”，当前章无法可靠落到时间线。")
    if is_effectively_empty(relative_time) and not historical_mode:
        warnings.append("`state.md` 缺少“距上章过去”，容易导致相邻章节的先后顺序失真。")
    if is_effectively_empty(current_place) and not historical_mode:
        warnings.append("`state.md` 未写当前地点，转场与埋伏类场景容易失焦。")
    if not historical_mode and not is_effectively_empty(current_chapter) and not chapter_text_matches(current_chapter, chapter_no):
        warnings.append(f"`state.md` 当前章节为“{current_chapter}”，与目标第{chapter_no:03d}章不一致。")

    timeline_rows = extract_markdown_table_rows(timeline_content, "主线时间线")
    has_legacy_timeline = section_has_meaningful_bullets(timeline_content, ["卷一《困龙出鞘》现阶段时间轴（隆安十三年腊月）", "基础时间锚点", "历史大事件轴（开局八年前）"])
    if len(timeline_rows) <= 2 and not has_legacy_timeline and not historical_mode:
        blockers.append("`timeline.md` 主线时间线为空，无法校验回忆、跳时、年龄推进。")

    arrangement_rows = extract_markdown_table_rows(state_content, "当前有效布置")
    has_arrangements = has_non_placeholder_row(arrangement_rows) or section_has_meaningful_bullets(state_content, ["当前有效布置"])
    active_foreshadow_rows = extract_markdown_table_rows(foreshadowing_content, "活跃伏笔")
    if not active_foreshadow_rows:
        active_foreshadow_rows = extract_markdown_table_rows(foreshadowing_content, "📌 未回收伏笔 (Pending)")
    has_foreshadowing = has_non_placeholder_row(active_foreshadow_rows)

    danger_hits = detect_danger_keywords(chapter_content)
    if danger_hits and not has_arrangements and not historical_mode:
        blockers.append(
            f"本章命中高风险关键词（{', '.join(danger_hits)}），但 `state.md` 没有可用的“当前有效布置”。"
        )
    if danger_hits and not has_foreshadowing:
        warnings.append(
            f"本章命中高风险关键词（{', '.join(danger_hits)}），但 `foreshadowing.md` 没有活跃伏笔，旧账可能失踪。"
        )

    missing_trigger_count = 0
    missing_failure_count = 0
    header = active_foreshadow_rows[0] if active_foreshadow_rows else []
    trigger_idx = 4
    failure_idx = 5
    if header:
        for idx, cell in enumerate(header):
            if "触发" in cell:
                trigger_idx = idx
            if "失效" in cell:
                failure_idx = idx
    for row in active_foreshadow_rows[1:]:
        if len(row) <= max(trigger_idx, failure_idx):
            continue
        if is_effectively_empty(row[trigger_idx]):
            missing_trigger_count += 1
        if is_effectively_empty(row[failure_idx]):
            missing_failure_count += 1
    if missing_trigger_count:
        warnings.append(f"`foreshadowing.md` 有 {missing_trigger_count} 条活跃伏笔缺少“触发条件”。")
    if missing_failure_count:
        warnings.append(f"`foreshadowing.md` 有 {missing_failure_count} 条活跃伏笔缺少“失效条件”。")

    if not chapter_content.strip():
        blockers.append("目标章节正文为空，无法执行 continuity gate。")

    planning_status = str(planning_review.get("status", "missing"))
    planning_verdict = str(planning_review.get("planning_verdict", "missing"))
    planning_blockers = [str(item) for item in planning_review.get("blockers", []) if str(item).strip()]
    planning_warnings = [str(item) for item in planning_review.get("warnings", []) if str(item).strip()]
    planning_report_path = ""
    report_paths = planning_review.get("report_paths", {})
    if isinstance(report_paths, dict):
        planning_report_path = str(report_paths.get("markdown", ""))

    if planning_status == "fail" or planning_verdict == "revise":
        blockers.append("写前章节规划预审未通过，必须先修章卡/下章预告后再认定本章可交稿。")
        blockers.extend([f"规划预审：{item}" for item in planning_blockers[:4]])
    elif planning_status == "warn":
        warnings.append("写前章节规划预审存在预警，建议回看章卡与下章行动变化。")
        warnings.extend([f"规划预审：{item}" for item in planning_warnings[:3]])
    elif planning_status == "missing" and not historical_mode:
        warnings.append("缺少本章 planning_review.json，当前门禁无法确认写前章卡是否曾通过预审。")

    warnings.extend(evaluate_golden_three_progress(chapter_no, chapter_content))

    continuity_verdict = "pass"
    if blockers:
        continuity_verdict = "block"
    elif warnings:
        continuity_verdict = "warn"

    style_profile = parse_style_file(style_path)
    language_analysis = analyze_text(chapter_content, style_profile, style_path) if not skip_language else {
        "verdict": "skipped",
        "issues": [],
        "scores": {},
        "rewrite_plan": [],
        "suggestions": [],
        "style_profile": {
            "title": style_profile["title"],
            "genre": style_profile["genre"],
            "thresholds": style_profile["thresholds"],
        },
    }
    language_blockers, language_warnings = summarize_language_analysis(language_analysis)
    verdict = map_overall_verdict(continuity_verdict, str(language_analysis["verdict"]), skip_language)

    return {
        "chapter_no": chapter_no,
        "chapter_path": chapter_path.as_posix(),
        "style_path": style_path.as_posix(),
        "absolute_time": absolute_time or "未设定",
        "relative_time": relative_time or "未设定",
        "current_place": current_place or "未设定",
        "danger_hits": danger_hits,
        "has_arrangements": has_arrangements,
        "has_foreshadowing": has_foreshadowing,
        "continuity_verdict": continuity_verdict,
        "language_verdict": language_analysis["verdict"],
        "language_scores": language_analysis.get("scores", {}),
        "language_style_profile": language_analysis.get("style_profile", {}),
        "planning_status": planning_status,
        "planning_verdict": planning_verdict,
        "planning_blockers": planning_blockers,
        "planning_warnings": planning_warnings,
        "planning_report_path": planning_report_path,
        "language_blockers": language_blockers,
        "language_warnings": language_warnings,
        "language_rewrite_plan": language_analysis.get("rewrite_plan", []),
        "language_suggestions": language_analysis.get("suggestions", []),
        "language_rewritten_text": language_analysis.get("rewritten_text", chapter_content),
        "warnings": warnings,
        "blockers": blockers,
        "verdict": verdict,
    }


def load_template(templates_root: Path, name: str) -> str:
    return (templates_root / name).read_text(encoding="utf-8")


def write_outputs(
    project_dir: Path,
    templates_root: Path,
    analysis: dict[str, object],
    dry_run: bool,
    rewrite_out: Path | None,
) -> tuple[Path, Path]:
    chapter_no = int(analysis["chapter_no"])
    gate_dir = project_dir / "04_gate" / f"ch{chapter_no:03d}"
    report_path = gate_dir / "continuity_report.md"
    result_path = gate_dir / "result.json"
    gate_dir.mkdir(parents=True, exist_ok=True)

    template = load_template(templates_root, "continuity-report.md")
    rendered = template.format(
        chapter_no=f"{chapter_no:03d}",
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        chapter_path=analysis["chapter_path"],
        style_path=analysis["style_path"],
        absolute_time=analysis["absolute_time"],
        relative_time=analysis["relative_time"],
        current_place=analysis["current_place"],
        danger_hits=", ".join(analysis["danger_hits"]) if analysis["danger_hits"] else "无",
        arrangement_status="是" if analysis["has_arrangements"] else "否",
        foreshadow_status="是" if analysis["has_foreshadowing"] else "否",
        planning_status=str(analysis["planning_status"]).upper(),
        planning_verdict=str(analysis["planning_verdict"]).upper(),
        planning_report_path=analysis["planning_report_path"] or "未找到",
        planning_blockers=render_list(list(analysis["planning_blockers"]), "无规划预审阻断项"),
        planning_warnings=render_list(list(analysis["planning_warnings"]), "无规划预审预警项"),
        continuity_verdict=str(analysis["continuity_verdict"]).upper(),
        language_verdict=str(analysis["language_verdict"]).upper(),
        language_style_title=analysis["language_style_profile"].get("title", "未命名") or "未命名",
        language_style_genre=analysis["language_style_profile"].get("genre", "未设定") or "未设定",
        language_scores=json.dumps(analysis["language_scores"], ensure_ascii=False),
        language_blockers=render_list(list(analysis["language_blockers"]), "无语言阻断项"),
        language_warnings=render_list(list(analysis["language_warnings"]), "无语言预警项"),
        language_rewrite_plan=render_list(list(analysis["language_rewrite_plan"]), "无需额外语言改写"),
        language_suggestions=render_language_suggestions(list(analysis["language_suggestions"])),
        verdict=str(analysis["verdict"]).upper(),
        blockers=render_list(list(analysis["blockers"]), "无阻断项"),
        warnings=render_list(list(analysis["warnings"]), "无预警项"),
    )

    if not dry_run:
        report_path.write_text(rendered, encoding="utf-8")
        result_path.write_text(
            json.dumps(analysis, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if rewrite_out is not None and str(analysis["language_verdict"]) != "skipped":
            rewrite_out.parent.mkdir(parents=True, exist_ok=True)
            rewrite_out.write_text(str(analysis["language_rewritten_text"]), encoding="utf-8")
    return report_path, result_path


def print_result(payload: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"chapter_no={payload['chapter_no']}")
    print(f"verdict={payload['verdict']}")
    print(f"report_path={payload['report_path']}")
    print(f"result_path={payload['result_path']}")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    project_dir = Path(args.project).resolve()
    style_path = Path(args.style).resolve() if args.style else (project_dir / "00_memory" / "style.md")
    rewrite_out = Path(args.rewrite_out).resolve() if args.rewrite_out else None
    templates_root = (
        Path(args.templates_root).resolve()
        if args.templates_root
        else (Path(__file__).resolve().parent.parent / "templates")
    )

    try:
        chapter_no, chapter_path = detect_existing_chapter_file(project_dir, args.chapter, args.chapter_no)
    except ValueError as exc:
        print(str(exc))
        return 1

    analysis = build_gate_analysis(project_dir, chapter_no, chapter_path, style_path, args.skip_language)
    report_path, result_path = write_outputs(project_dir, templates_root, analysis, args.dry_run, rewrite_out)

    payload = {
        "chapter_no": chapter_no,
        "verdict": analysis["verdict"],
        "continuity_verdict": analysis["continuity_verdict"],
        "language_verdict": analysis["language_verdict"],
        "style_path": analysis["style_path"],
        "planning_status": analysis["planning_status"],
        "planning_verdict": analysis["planning_verdict"],
        "planning_report_path": analysis["planning_report_path"],
        "report_path": report_path.as_posix(),
        "result_path": result_path.as_posix(),
        "rewrite_out": rewrite_out.as_posix() if rewrite_out else "",
        "warnings": analysis["warnings"],
        "blockers": analysis["blockers"],
        "planning_warnings": analysis["planning_warnings"],
        "planning_blockers": analysis["planning_blockers"],
        "language_warnings": analysis["language_warnings"],
        "language_blockers": analysis["language_blockers"],
        "language_suggestions": analysis["language_suggestions"],
        "language_rewritten_text": analysis["language_rewritten_text"] if rewrite_out else "",
    }
    print_result(payload, args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
