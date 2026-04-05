#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


CHAPTER_PATTERN = re.compile(r"第0*(\d+)章")
FLEXIBLE_CHAPTER_PATTERN = re.compile(
    r"第0*(\d+)章|ch(?:apter)?[-_ ]?0*(\d+)|^0*(\d+)",
    re.IGNORECASE,
)
PLACEHOLDER_PATTERNS = (
    re.compile(r"\{[A-Z0-9_]+\}"),
    re.compile(r"第_{2,}章"),
    re.compile(r"第\{[A-Z0-9_]+\}章"),
)


def normalize_input_text(text: str) -> str:
    return text.lstrip("\ufeff")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return normalize_input_text(path.read_text(encoding="utf-8"))


def extract_line(text: str, label: str) -> str:
    match = re.search(rf"{re.escape(label)}[:：]\s*(.+)", text)
    return match.group(1).strip() if match else ""


def extract_state_value(state_text: str, label: str) -> str:
    return extract_line(state_text, f"- {label}") or extract_line(state_text, label)


def detect_current_chapter(state_text: str) -> int:
    current = extract_state_value(state_text, "当前章节")
    match = re.search(r"(\d+)", current)
    return int(match.group(1)) if match else 0


def has_placeholder(text: str) -> bool:
    normalized = text.strip()
    if not normalized:
        return False
    return any(pattern.search(normalized) for pattern in PLACEHOLDER_PATTERNS)


def chapter_number_from_name(name: str) -> int | None:
    match = FLEXIBLE_CHAPTER_PATTERN.search(name)
    if match:
        for group in match.groups():
            if group:
                return int(group)
    fallback = re.search(r"(\d+)", name)
    return int(fallback.group(1)) if fallback else None


def list_chapter_files(project_dir: Path) -> list[tuple[int, Path]]:
    chapters_dir = project_dir / "03_chapters"
    chapter_files: list[tuple[int, Path]] = []
    if not chapters_dir.exists():
        return chapter_files

    for path in chapters_dir.iterdir():
        if not path.is_file():
            continue
        chapter_no = chapter_number_from_name(path.name)
        if chapter_no is None:
            continue
        chapter_files.append((chapter_no, path))

    chapter_files.sort(key=lambda item: item[0])
    return chapter_files


def count_chapter_files(project_dir: Path) -> int:
    return len(list_chapter_files(project_dir))


def detect_latest_chapter_file(project_dir: Path) -> tuple[int, Path | None]:
    chapter_files = list_chapter_files(project_dir)
    if not chapter_files:
        return 0, None
    return chapter_files[-1]


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
        due_no = chapter_number_from_name(due_text)
        if not item_id or due_no is None:
            continue
        if status and any(flag in status for flag in ("已回收", "已废弃")):
            continue
        if due_no <= target_chapter:
            due_ids.append(item_id)
    return due_ids


def extract_section_body(content: str, heading_variants: list[str]) -> str:
    for heading in heading_variants:
        pattern = re.compile(
            rf"##\s+{re.escape(heading)}\s*\n(?P<body>.*?)(?:\n##\s+|\Z)",
            re.DOTALL,
        )
        match = pattern.search(content)
        if match:
            return match.group("body")
    return ""


def extract_markdown_table_rows(content: str, heading: str) -> list[list[str]]:
    body = extract_section_body(content, [heading])
    return extract_pipe_table_rows(body)


def extract_pipe_table_rows(content: str) -> list[list[str]]:
    if not content:
        return []

    rows: list[list[str]] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if set(stripped.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells:
            rows.append(cells)
    return rows


def render_list(items: list[str], empty_text: str) -> str:
    if not items:
        return f"- {empty_text}"
    return "\n".join(f"- {item}" for item in items)


def clean_value(text: str, fallback: str = "未识别") -> str:
    normalized = text.strip()
    if not normalized or has_placeholder(normalized):
        return fallback
    return normalized


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
        if line.startswith("|") or re.fullmatch(r"\|[-:\s|]+\|?", line):
            continue
        lines.append(line)
        if len(lines) >= limit:
            break
    return lines


def detect_existing_chapter_file(
    project_dir: Path,
    chapter_arg: str | None,
    chapter_no: int | None,
) -> tuple[int, Path]:
    if chapter_arg:
        chapter_path = Path(chapter_arg).resolve()
        detected_no = chapter_no or chapter_number_from_name(chapter_path.name)
        if detected_no is None:
            raise ValueError("无法从 --chapter 推断章节号，请补充 --chapter-no。")
        return detected_no, chapter_path

    chapter_files = list_chapter_files(project_dir)
    if chapter_no is not None:
        for current_no, path in chapter_files:
            if current_no == chapter_no:
                return current_no, path
        raise ValueError(f"未找到第{chapter_no:03d}章文件。")

    if chapter_files:
        return chapter_files[-1]
    raise ValueError("未找到章节文件，请传入 --chapter 或在 03_chapters 下放入章节。")
