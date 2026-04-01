#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable


CHAPTER_PATTERN = re.compile(r"第0*(\d+)章")
TRACKER_START = "<!-- SELF_CHECK_TRACKER_START -->"
TRACKER_END = "<!-- SELF_CHECK_TRACKER_END -->"
REPORT_PATTERN = re.compile(r"ch(\d{3,})_(minor|major)_self_check\.md$")
DANGER_KEYWORDS = (
    "遇刺", "刺杀", "刺客", "追杀", "围杀", "跟踪", "暴露", "身份",
    "搜查", "搜捕", "潜入", "危机", "危险", "截杀", "埋伏", "伏杀"
)
DEFAULT_EMPTY_VALUES = {"", "—", "无", "暂无", "未设定", "未开始", "0"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate periodic self-check reports for chaseNovel projects."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--chapter-no", type=int, help="Override detected chapter number")
    parser.add_argument(
        "--templates-root",
        help="Path to the chaseNovel templates directory; defaults to ../templates",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rewrite an existing self-check report for the current checkpoint",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write files; only print the detection result",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    return parser.parse_args()


def rel_path(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def chapter_number_from_name(name: str) -> int | None:
    match = CHAPTER_PATTERN.search(name)
    if not match:
        return None
    return int(match.group(1))


def list_chapter_files(chapters_dir: Path) -> list[tuple[int, Path]]:
    if not chapters_dir.exists():
        return []

    files: list[tuple[int, Path]] = []
    for path in chapters_dir.iterdir():
        if not path.is_file():
            continue
        chapter_no = chapter_number_from_name(path.name)
        if chapter_no is None:
            continue
        files.append((chapter_no, path))

    return sorted(files, key=lambda item: item[0])


def parse_current_chapter_from_state(state_path: Path) -> int | None:
    if not state_path.exists():
        return None

    content = state_path.read_text(encoding="utf-8")
    match = re.search(r"当前章节：第0*(\d+)章", content)
    if not match:
        return None
    return int(match.group(1))


def detect_current_chapter(project_dir: Path, override: int | None) -> tuple[int, list[tuple[int, Path]]]:
    chapters = list_chapter_files(project_dir / "03_chapters")
    if override is not None:
        return override, chapters
    if chapters:
        return chapters[-1][0], chapters

    state_chapter = parse_current_chapter_from_state(project_dir / "00_memory" / "state.md")
    return state_chapter or 0, chapters


def detect_checkpoint(chapter_no: int) -> str | None:
    if chapter_no <= 0:
        return None
    if chapter_no % 10 == 0:
        return "major"
    if chapter_no % 5 == 0:
        return "minor"
    return None


def report_files(self_checks_dir: Path) -> Iterable[tuple[int, str]]:
    if not self_checks_dir.exists():
        return []

    reports: list[tuple[int, str]] = []
    for path in self_checks_dir.iterdir():
        if not path.is_file():
            continue
        match = REPORT_PATTERN.match(path.name)
        if not match:
            continue
        reports.append((int(match.group(1)), match.group(2)))
    return reports


def detect_last_reports(self_checks_dir: Path) -> tuple[int, int]:
    last_minor = 0
    last_major = 0
    for chapter_no, level in report_files(self_checks_dir):
        if level == "minor":
            last_minor = max(last_minor, chapter_no)
        if level == "major":
            last_major = max(last_major, chapter_no)
    return last_minor, last_major


def next_checkpoint(chapter_no: int, step: int) -> int:
    if chapter_no <= 0:
        return step
    return ((chapter_no // step) + 1) * step


def render_tracker(
    chapter_no: int,
    last_minor: int,
    last_major: int,
    current_level: str | None,
) -> str:
    if current_level == "minor":
        last_minor = max(last_minor, chapter_no)
    if current_level == "major":
        last_minor = max(last_minor, chapter_no)
        last_major = max(last_major, chapter_no)

    next_minor = next_checkpoint(chapter_no, 5)
    next_major = next_checkpoint(chapter_no, 10)
    latest_result = (
        "第{0:03d}章触发{1}".format(chapter_no, "大自检" if current_level == "major" else "小自检")
        if current_level
        else "本章未触发"
    )

    return "\n".join(
        [
            TRACKER_START,
            "## 周期自检",
            "- 小自检节律：每 5 章触发一次",
            "- 大自检节律：每 10 章触发一次（覆盖当次小自检）",
            f"- 上次小自检：{'第%03d章' % last_minor if last_minor else '未执行'}",
            f"- 上次大自检：{'第%03d章' % last_major if last_major else '未执行'}",
            f"- 下次小自检触发章：第{next_minor:03d}章",
            f"- 下次大自检触发章：第{next_major:03d}章",
            f"- 最近一次判定：{latest_result}",
            TRACKER_END,
        ]
    )


def update_state_tracker(
    state_path: Path,
    chapter_no: int,
    last_minor: int,
    last_major: int,
    current_level: str | None,
    dry_run: bool,
) -> bool:
    if not state_path.exists():
        return False

    content = state_path.read_text(encoding="utf-8")
    tracker_block = render_tracker(chapter_no, last_minor, last_major, current_level)
    pattern = re.compile(
        rf"{re.escape(TRACKER_START)}.*?{re.escape(TRACKER_END)}",
        re.DOTALL,
    )

    if pattern.search(content):
        updated = pattern.sub(tracker_block, content, count=1)
    else:
        updated = content.rstrip() + "\n\n" + tracker_block + "\n"

    if updated == content:
        return False
    if not dry_run:
        state_path.write_text(updated, encoding="utf-8")
    return True


def chapter_window(chapter_no: int, width: int) -> tuple[int, int]:
    start = max(1, chapter_no - width + 1)
    return start, chapter_no


def select_window_chapters(
    chapters: list[tuple[int, Path]], start: int, end: int
) -> list[tuple[int, Path]]:
    return [item for item in chapters if start <= item[0] <= end]


def load_template(templates_root: Path, name: str) -> str:
    return (templates_root / name).read_text(encoding="utf-8")


def read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def extract_line_value(content: str, label: str) -> str:
    match = re.search(rf"{re.escape(label)}：(.+)", content)
    if not match:
        return ""
    return match.group(1).strip()


def normalize_value(value: str) -> str:
    return value.strip().strip("`").strip()


def is_effectively_empty(value: str) -> bool:
    return normalize_value(value) in DEFAULT_EMPTY_VALUES


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
        if not cells:
            continue
        rows.append(cells)
    return rows


def has_non_placeholder_row(rows: list[list[str]]) -> bool:
    if len(rows) <= 1:
        return False
    for row in rows[1:]:
        if any(not is_effectively_empty(cell) and "暂无" not in cell for cell in row):
            return True
    return False


def extract_chapter_contents(chapters: list[tuple[int, Path]]) -> list[tuple[int, str]]:
    contents: list[tuple[int, str]] = []
    for chapter_no, path in chapters:
        try:
            contents.append((chapter_no, path.read_text(encoding="utf-8")))
        except Exception:
            contents.append((chapter_no, ""))
    return contents


def detect_danger_chapters(chapter_contents: list[tuple[int, str]]) -> list[int]:
    result: list[int] = []
    for chapter_no, content in chapter_contents:
        if any(keyword in content for keyword in DANGER_KEYWORDS):
            result.append(chapter_no)
    return result


def build_auto_warnings(project_dir: Path, scoped_chapters: list[tuple[int, Path]]) -> str:
    warnings: list[str] = []
    state_content = read_text_if_exists(project_dir / "00_memory" / "state.md")
    timeline_content = read_text_if_exists(project_dir / "00_memory" / "timeline.md")
    foreshadowing_content = read_text_if_exists(project_dir / "00_memory" / "foreshadowing.md")
    chapter_contents = extract_chapter_contents(scoped_chapters)
    danger_chapters = detect_danger_chapters(chapter_contents)

    absolute_time = extract_line_value(state_content, "当前绝对时间")
    relative_time = extract_line_value(state_content, "距上章过去")
    if is_effectively_empty(absolute_time):
        warnings.append("`state.md` 缺少有效的“当前绝对时间”，高风险导致年份/纪年写乱。")
    if is_effectively_empty(relative_time):
        warnings.append("`state.md` 缺少有效的“距上章过去”，高风险导致章节先后顺序失真。")

    timeline_rows = extract_markdown_table_rows(timeline_content, "主线时间线")
    if len(timeline_rows) <= 2:
        warnings.append("`timeline.md` 的主线时间线仍为空或只有表头，无法为跳时、回忆、年龄变化提供校验锚点。")

    arrangement_rows = extract_markdown_table_rows(state_content, "当前有效布置")
    has_arrangements = has_non_placeholder_row(arrangement_rows)
    if danger_chapters and not has_arrangements:
        chapter_labels = "、".join(f"第{num:03d}章" for num in danger_chapters)
        warnings.append(f"{chapter_labels} 出现高风险场景关键词，但 `state.md` 没有可用的“当前有效布置”，容易出现后手失忆。")

    foreshadow_rows = extract_markdown_table_rows(foreshadowing_content, "活跃伏笔")
    has_active_foreshadowing = has_non_placeholder_row(foreshadow_rows)
    if danger_chapters and not has_active_foreshadowing:
        warnings.append("当前窗口出现高风险场景，但 `foreshadowing.md` 没有活跃伏笔记录，无法自动核对旧伏笔是否该触发。")

    trigger_missing = False
    failure_missing = False
    for row in foreshadow_rows[1:]:
        if len(row) < 9:
            continue
        trigger_missing = trigger_missing or is_effectively_empty(row[4])
        failure_missing = failure_missing or is_effectively_empty(row[5])
    if trigger_missing:
        warnings.append("`foreshadowing.md` 存在活跃伏笔未填写“触发条件”，后续容易出现该触发时没触发。")
    if failure_missing:
        warnings.append("`foreshadowing.md` 存在活跃伏笔未填写“失效条件”，后续容易出现无法解释为什么没生效。")

    if not warnings:
        return "- 未检测到明显的时间线/伏笔连续性硬伤。"
    return "\n".join(f"- [!WARNING] {item}" for item in warnings)


def check_ai_flavor(content: str) -> list[str]:
    black_list = [
        "像...一样", "仿佛", "由于", "导致了", "事实上",
        "那一刻", "就在这时", "此时此刻", "不禁", "不由得",
        "闪过一丝", "值得注意的是", "不得不说", "可以说",
        "不容置疑", "坚定地", "深邃"
    ]
    warnings = []
    for word in black_list:
        if "..." in word:
            parts = word.split("...")
            if parts[0] in content and parts[1] in content:
                warnings.append(word)
        elif word in content:
            warnings.append(word)
    return warnings

def format_chapter_list(chapters: list[tuple[int, Path]], project_dir: Path) -> str:
    if not chapters:
        return "- 本轮章节正文尚未落盘，请手动补充本次窗口内章节。"
    
    lines = []
    for chapter_no, path in chapters:
        try:
            content = path.read_text(encoding="utf-8")
            warnings = check_ai_flavor(content)
            warn_str = f" [!WARNING] AI味词汇: {','.join(warnings)}" if warnings else ""
        except Exception:
            warn_str = ""
            
        lines.append(f"- 第{chapter_no:03d}章：`{rel_path(path, project_dir)}`{warn_str}")
    return "\n".join(lines)


def write_report(
    project_dir: Path,
    templates_root: Path,
    chapter_no: int,
    checkpoint: str,
    chapters: list[tuple[int, Path]],
    force: bool,
    dry_run: bool,
) -> tuple[Path, bool]:
    width = 10 if checkpoint == "major" else 5
    start, end = chapter_window(chapter_no, width)
    scoped_chapters = select_window_chapters(chapters, start, end)
    auto_warnings = build_auto_warnings(project_dir, scoped_chapters)
    report_dir = project_dir / "00_memory" / "self_checks"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"ch{chapter_no:03d}_{checkpoint}_self_check.md"
    created = force or not report_path.exists()

    template_name = "self-check-large.md" if checkpoint == "major" else "self-check-small.md"
    template = load_template(templates_root, template_name)
    rendered = template.format(
        chapter_no=f"{chapter_no:03d}",
        date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        window_start=f"{start:03d}",
        window_end=f"{end:03d}",
        state_rel=rel_path(project_dir / "00_memory" / "state.md", project_dir),
        plan_rel=rel_path(project_dir / "00_memory" / "plan.md", project_dir),
        recent_rel=rel_path(project_dir / "00_memory" / "summaries" / "recent.md", project_dir),
        arc_rel=rel_path(project_dir / "00_memory" / "arc_progress.md", project_dir),
        payoff_rel=rel_path(project_dir / "00_memory" / "payoff_board.md", project_dir),
        character_arcs_rel=rel_path(project_dir / "00_memory" / "character_arcs.md", project_dir),
        foreshadowing_rel=rel_path(project_dir / "00_memory" / "foreshadowing.md", project_dir),
        timeline_rel=rel_path(project_dir / "00_memory" / "timeline.md", project_dir),
        findings_rel=rel_path(project_dir / "00_memory" / "findings.md", project_dir),
        chapter_list=format_chapter_list(scoped_chapters, project_dir),
        auto_warnings=auto_warnings,
    )

    if created and not dry_run:
        report_path.write_text(rendered, encoding="utf-8")
    return report_path, created


def build_result(
    project_dir: Path,
    chapter_no: int,
    checkpoint: str | None,
    report_path: Path | None,
    report_created: bool,
    state_updated: bool,
) -> dict[str, object]:
    return {
        "project": project_dir.as_posix(),
        "chapter_no": chapter_no,
        "checkpoint_due": checkpoint,
        "report_path": report_path.as_posix() if report_path else None,
        "report_created": report_created,
        "state_updated": state_updated,
    }


def print_result(result: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"chapter_no={result['chapter_no']}")
    print(f"checkpoint_due={result['checkpoint_due'] or 'none'}")
    if result["report_path"]:
        print(f"report_path={result['report_path']}")
        print(f"report_created={str(result['report_created']).lower()}")
    print(f"state_updated={str(result['state_updated']).lower()}")


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project).resolve()
    templates_root = (
        Path(args.templates_root).resolve()
        if args.templates_root
        else (Path(__file__).resolve().parent.parent / "templates")
    )

    chapter_no, chapters = detect_current_chapter(project_dir, args.chapter_no)
    checkpoint = detect_checkpoint(chapter_no)
    self_checks_dir = project_dir / "00_memory" / "self_checks"
    last_minor, last_major = detect_last_reports(self_checks_dir)

    report_path: Path | None = None
    report_created = False
    if checkpoint:
        report_path, report_created = write_report(
            project_dir=project_dir,
            templates_root=templates_root,
            chapter_no=chapter_no,
            checkpoint=checkpoint,
            chapters=chapters,
            force=args.force,
            dry_run=args.dry_run,
        )

    state_updated = update_state_tracker(
        state_path=project_dir / "00_memory" / "state.md",
        chapter_no=chapter_no,
        last_minor=last_minor,
        last_major=last_major,
        current_level=checkpoint,
        dry_run=args.dry_run,
    )

    result = build_result(
        project_dir=project_dir,
        chapter_no=chapter_no,
        checkpoint=checkpoint,
        report_path=report_path,
        report_created=report_created,
        state_updated=state_updated,
    )
    print_result(result, args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
