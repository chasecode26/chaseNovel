#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


PLACEHOLDER_PATTERNS = (
    re.compile(r"\{[A-Z0-9_]+\}"),
    re.compile(r"第_{2,}章"),
    re.compile(r"第\{[A-Z0-9_]+\}章"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile the minimum next-chapter context for a chaseNovel project."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--chapter", type=int, help="Target chapter number")
    parser.add_argument("--output", help="Optional output markdown path")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    return parser.parse_args()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").lstrip("\ufeff")


def detect_current_chapter(state_text: str) -> int:
    match = re.search(r"当前章节[:：]\s*第?(\d+)章", state_text)
    return int(match.group(1)) if match else 0


def extract_line(text: str, label: str) -> str:
    match = re.search(rf"{re.escape(label)}[:：]\s*(.+)", text)
    return match.group(1).strip() if match else ""


def has_placeholder(text: str) -> bool:
    normalized = text.strip()
    if not normalized:
        return False
    return any(pattern.search(normalized) for pattern in PLACEHOLDER_PATTERNS)


def useful_lines(text: str, limit: int) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or has_placeholder(line):
            continue
        if line.startswith("#") or line.startswith(">"):
            continue
        if line.startswith("<!--") or line.startswith("-->"):
            continue
        if line.startswith("|"):
            continue
        if re.fullmatch(r"\|[-:\s|]+\|?", line):
            continue
        lines.append(line)
        if len(lines) >= limit:
            break
    return lines


def extract_next_goal(state_text: str) -> str:
    direct = extract_line(state_text, "- 下章预告") or extract_line(state_text, "下章预告")
    if direct and not has_placeholder(direct):
        return direct

    section_match = re.search(
        r"##\s*下章预告\s*(.*?)(?:\n##\s+|\Z)",
        state_text,
        re.S,
    )
    if not section_match:
        return ""

    section_text = section_match.group(1)
    result = (
        extract_line(section_text, "- 计划内容")
        or extract_line(section_text, "计划内容")
        or extract_line(section_text, "- 章节号")
        or extract_line(section_text, "章节号")
    )
    return "" if has_placeholder(result) else result


def first_nonempty_lines(text: str, limit: int) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[:limit]


def collect_latest_chapter_excerpt(project_dir: Path) -> str:
    chapters_dir = project_dir / "03_chapters"
    if not chapters_dir.exists():
        return ""

    latest_path = None
    latest_no = -1
    for path in chapters_dir.iterdir():
        if not path.is_file():
            continue
        match = re.search(r"(\d+)", path.stem)
        if not match:
            continue
        chapter_no = int(match.group(1))
        if chapter_no > latest_no:
            latest_no = chapter_no
            latest_path = path

    if latest_path is None:
        return ""

    content = read_text(latest_path)
    return "\n".join(first_nonempty_lines(content, 12))


def load_due_foreshadow_ids(project_dir: Path, target_chapter: int) -> list[str]:
    path = project_dir / "00_memory" / "foreshadowing.md"
    if not path.exists():
        return []

    due_ids: list[str] = []
    for line in read_text(path).splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "----" in stripped or "ID" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 8:
            continue
        item_id = cells[0]
        due_text = cells[6]
        status = cells[8] if len(cells) > 8 else ""
        match = re.search(r"(\d+)", due_text)
        if not item_id or not match:
            continue
        if status and any(flag in status for flag in ("已回收", "已废弃")):
            continue
        if int(match.group(1)) <= target_chapter:
            due_ids.append(item_id)
    return due_ids


def build_markdown(project_dir: Path, target_chapter: int) -> str:
    memory_dir = project_dir / "00_memory"
    plan_text = read_text(memory_dir / "plan.md")
    state_text = read_text(memory_dir / "state.md")
    arc_text = read_text(memory_dir / "arc_progress.md")
    findings_text = read_text(memory_dir / "findings.md")
    recent_text = read_text(memory_dir / "summaries" / "recent.md")
    voice_text = read_text(memory_dir / "voice.md")
    style_text = read_text(memory_dir / "style.md")
    due_ids = load_due_foreshadow_ids(project_dir, target_chapter)

    active_volume = extract_line(state_text, "- 当前卷") or extract_line(state_text, "当前卷")
    active_arc = extract_line(state_text, "- 当前弧") or extract_line(state_text, "当前弧")
    next_goal = extract_next_goal(state_text)

    sections = [
        f"# Next Context - 第{target_chapter:03d}章",
        "",
        f"- 生成时间：{datetime.now().isoformat(timespec='seconds')}",
        f"- 项目：{project_dir.as_posix()}",
        f"- 当前卷：{active_volume or '未识别'}",
        f"- 当前弧：{active_arc or '未识别'}",
        f"- 下章目标：{next_goal or '待明确'}",
        "",
        "## 全书主线摘要",
        *([f"- {line}" for line in useful_lines(plan_text, 8)] or ["- 缺少 plan.md 摘要"]),
        "",
        "## 当前状态摘要",
        *([f"- {line}" for line in useful_lines(state_text, 12)] or ["- 缺少 state.md 摘要"]),
        "",
        "## 卷级推进摘要",
        *([f"- {line}" for line in useful_lines(arc_text, 10)] or ["- 缺少 arc_progress.md 摘要"]),
        "",
        "## 待跟进发现",
        *([f"- {line}" for line in useful_lines(findings_text, 8)] or ["- 暂无 findings.md"]),
        "",
        "## 近章摘要",
        *([f"- {line}" for line in useful_lines(recent_text, 10)] or ["- 暂无 recent.md"]),
        "",
        "## 书级声音约束",
        *([f"- {line}" for line in useful_lines(voice_text or style_text, 10)] or ["- 暂无 voice/style 约束"]),
        "",
        "## 本章到期伏笔",
        *([f"- {item_id}" for item_id in due_ids] or ["- 当前无到期伏笔"]),
        "",
        "## 上一章摘录",
        "```md",
        collect_latest_chapter_excerpt(project_dir) or "暂无章节正文",
        "```",
    ]
    return "\n".join(sections) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    project_dir = Path(args.project).resolve()
    state_text = read_text(project_dir / "00_memory" / "state.md")
    target_chapter = args.chapter or max(detect_current_chapter(state_text) + 1, 1)
    output_path = Path(args.output).resolve() if args.output else project_dir / "00_memory" / "retrieval" / "next_context.md"
    markdown = build_markdown(project_dir, target_chapter)

    result = {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "pass",
        "chapter": target_chapter,
        "output": output_path.as_posix(),
        "warnings": [],
        "warning_count": 0,
        "report_paths": {
            "markdown": output_path.as_posix(),
        },
    }
    if not collect_latest_chapter_excerpt(project_dir):
        result["warnings"].append("当前没有正文章节，上一章摘录将为空。")
    if not load_due_foreshadow_ids(project_dir, target_chapter):
        result["warnings"].append("当前未识别到到期伏笔。")
    result["warning_count"] = len(result["warnings"])
    if result["warnings"]:
        result["status"] = "warn"

    if not args.dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"status={result['status']}")
        print(f"warning_count={result['warning_count']}")
        print(f"chapter={target_chapter}")
        print(f"output={output_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
