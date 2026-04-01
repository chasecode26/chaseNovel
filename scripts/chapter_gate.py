#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path


CHAPTER_PATTERN = re.compile(r"第0*(\d+)章")
DANGER_KEYWORDS = (
    "遇刺", "刺杀", "刺客", "追杀", "围杀", "跟踪", "暴露", "身份",
    "搜查", "搜捕", "潜入", "危机", "危险", "截杀", "埋伏", "伏杀"
)
DEFAULT_EMPTY_VALUES = {"", "—", "无", "暂无", "未设定", "未开始", "0"}


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
    parser.add_argument("--dry-run", action="store_true", help="Do not write files")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    return parser.parse_args()


def chapter_number_from_name(name: str) -> int | None:
    match = CHAPTER_PATTERN.search(name)
    if not match:
        return None
    return int(match.group(1))


def read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def normalize_value(value: str) -> str:
    return value.strip().strip("`").strip()


def is_effectively_empty(value: str) -> bool:
    return normalize_value(value) in DEFAULT_EMPTY_VALUES


def extract_line_value(content: str, label: str) -> str:
    match = re.search(rf"{re.escape(label)}：(.+)", content)
    if not match:
        return ""
    return match.group(1).strip()


def extract_markdown_table_rows(content: str, heading: str) -> list[list[str]]:
    pattern = re.compile(
        rf"##\s+{re.escape(heading)}\s*\n(?P<body>.*?)(?:\n##\s+|\Z)",
        re.DOTALL,
    )
    match = pattern.search(content)
    if not match:
        return []

    rows: list[list[str]] = []
    for line in match.group("body").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if set(stripped.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells:
            rows.append(cells)
    return rows


def has_non_placeholder_row(rows: list[list[str]]) -> bool:
    if len(rows) <= 1:
        return False
    for row in rows[1:]:
        if any(not is_effectively_empty(cell) and "暂无" not in cell for cell in row):
            return True
    return False


def detect_target_chapter(project_dir: Path, chapter_arg: str | None, chapter_no: int | None) -> tuple[int, Path]:
    chapters_dir = project_dir / "03_chapters"
    if chapter_arg:
        chapter_path = Path(chapter_arg).resolve()
        detected_no = chapter_no or chapter_number_from_name(chapter_path.name)
        if detected_no is None:
            raise ValueError("无法从 --chapter 推断章节号，请补充 --chapter-no。")
        return detected_no, chapter_path

    chapter_files: list[tuple[int, Path]] = []
    if chapters_dir.exists():
        for path in chapters_dir.iterdir():
            if not path.is_file():
                continue
            detected_no = chapter_number_from_name(path.name)
            if detected_no is not None:
                chapter_files.append((detected_no, path))

    chapter_files.sort(key=lambda item: item[0])
    if chapter_no is not None:
        for current_no, path in chapter_files:
            if current_no == chapter_no:
                return current_no, path
        raise ValueError(f"未找到第{chapter_no:03d}章文件。")

    if chapter_files:
        return chapter_files[-1]

    raise ValueError("未找到章节文件，请传入 --chapter 或在 03_chapters 下放入章节。")


def detect_danger_keywords(content: str) -> list[str]:
    return [keyword for keyword in DANGER_KEYWORDS if keyword in content]


def chapter_text_matches(chapter_text: str, chapter_no: int) -> bool:
    match = CHAPTER_PATTERN.search(chapter_text)
    if not match:
        return False
    return int(match.group(1)) == chapter_no


def build_gate_analysis(project_dir: Path, chapter_no: int, chapter_path: Path) -> dict[str, object]:
    chapter_content = read_text_if_exists(chapter_path)
    state_content = read_text_if_exists(project_dir / "00_memory" / "state.md")
    timeline_content = read_text_if_exists(project_dir / "00_memory" / "timeline.md")
    foreshadowing_content = read_text_if_exists(project_dir / "00_memory" / "foreshadowing.md")

    warnings: list[str] = []
    blockers: list[str] = []

    absolute_time = extract_line_value(state_content, "当前绝对时间")
    relative_time = extract_line_value(state_content, "距上章过去")
    current_place = extract_line_value(state_content, "当前地点")
    current_chapter = extract_line_value(state_content, "当前章节")

    if is_effectively_empty(absolute_time):
        blockers.append("`state.md` 缺少“当前绝对时间”，当前章无法可靠落到时间线。")
    if is_effectively_empty(relative_time):
        warnings.append("`state.md` 缺少“距上章过去”，容易导致相邻章节的先后顺序失真。")
    if is_effectively_empty(current_place):
        warnings.append("`state.md` 未写当前地点，转场与埋伏类场景容易失焦。")
    if not is_effectively_empty(current_chapter) and not chapter_text_matches(current_chapter, chapter_no):
        warnings.append(f"`state.md` 当前章节为“{current_chapter}”，与目标第{chapter_no:03d}章不一致。")

    timeline_rows = extract_markdown_table_rows(timeline_content, "主线时间线")
    if len(timeline_rows) <= 2:
        blockers.append("`timeline.md` 主线时间线为空，无法校验回忆、跳时、年龄推进。")

    arrangement_rows = extract_markdown_table_rows(state_content, "当前有效布置")
    has_arrangements = has_non_placeholder_row(arrangement_rows)
    active_foreshadow_rows = extract_markdown_table_rows(foreshadowing_content, "活跃伏笔")
    has_foreshadowing = has_non_placeholder_row(active_foreshadow_rows)

    danger_hits = detect_danger_keywords(chapter_content)
    if danger_hits and not has_arrangements:
        blockers.append(
            f"本章命中高风险关键词（{', '.join(danger_hits)}），但 `state.md` 没有可用的“当前有效布置”。"
        )
    if danger_hits and not has_foreshadowing:
        warnings.append(
            f"本章命中高风险关键词（{', '.join(danger_hits)}），但 `foreshadowing.md` 没有活跃伏笔，旧账可能失踪。"
        )

    missing_trigger_count = 0
    missing_failure_count = 0
    for row in active_foreshadow_rows[1:]:
        if len(row) < 9:
            continue
        if is_effectively_empty(row[4]):
            missing_trigger_count += 1
        if is_effectively_empty(row[5]):
            missing_failure_count += 1
    if missing_trigger_count:
        warnings.append(f"`foreshadowing.md` 有 {missing_trigger_count} 条活跃伏笔缺少“触发条件”。")
    if missing_failure_count:
        warnings.append(f"`foreshadowing.md` 有 {missing_failure_count} 条活跃伏笔缺少“失效条件”。")

    if not chapter_content.strip():
        blockers.append("目标章节正文为空，无法执行 continuity gate。")

    verdict = "pass"
    if blockers:
        verdict = "block"
    elif warnings:
        verdict = "warn"

    return {
        "chapter_no": chapter_no,
        "chapter_path": chapter_path.as_posix(),
        "absolute_time": absolute_time or "未设定",
        "relative_time": relative_time or "未设定",
        "current_place": current_place or "未设定",
        "danger_hits": danger_hits,
        "has_arrangements": has_arrangements,
        "has_foreshadowing": has_foreshadowing,
        "warnings": warnings,
        "blockers": blockers,
        "verdict": verdict,
    }


def render_list(items: list[str], empty_text: str) -> str:
    if not items:
        return f"- {empty_text}"
    return "\n".join(f"- {item}" for item in items)


def load_template(templates_root: Path, name: str) -> str:
    return (templates_root / name).read_text(encoding="utf-8")


def write_outputs(
    project_dir: Path,
    templates_root: Path,
    analysis: dict[str, object],
    dry_run: bool,
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
        absolute_time=analysis["absolute_time"],
        relative_time=analysis["relative_time"],
        current_place=analysis["current_place"],
        danger_hits=", ".join(analysis["danger_hits"]) if analysis["danger_hits"] else "无",
        arrangement_status="是" if analysis["has_arrangements"] else "否",
        foreshadow_status="是" if analysis["has_foreshadowing"] else "否",
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
    args = parse_args()
    project_dir = Path(args.project).resolve()
    templates_root = (
        Path(args.templates_root).resolve()
        if args.templates_root
        else (Path(__file__).resolve().parent.parent / "templates")
    )

    try:
        chapter_no, chapter_path = detect_target_chapter(project_dir, args.chapter, args.chapter_no)
    except ValueError as exc:
        print(str(exc))
        return 1

    analysis = build_gate_analysis(project_dir, chapter_no, chapter_path)
    report_path, result_path = write_outputs(project_dir, templates_root, analysis, args.dry_run)

    payload = {
        "chapter_no": chapter_no,
        "verdict": analysis["verdict"],
        "report_path": report_path.as_posix(),
        "result_path": result_path.as_posix(),
        "warnings": analysis["warnings"],
        "blockers": analysis["blockers"],
    }
    print_result(payload, args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
