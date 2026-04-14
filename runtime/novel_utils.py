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
    match = re.search(rf"{re.escape(label)}[:：][ \t]*([^\r\n]+)", text)
    return match.group(1).strip() if match else ""


def extract_state_value(state_text: str, label: str) -> str:
    return extract_line(state_text, f"- {label}") or extract_line(state_text, label)


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
    chapters_dir = (project_dir / "03_chapters").resolve()
    chapter_files: list[tuple[int, Path]] = []
    if not chapters_dir.exists():
        return chapter_files

    for path in chapters_dir.iterdir():
        if path.is_symlink() or not path.is_file():
            continue
        try:
            resolved_path = path.resolve(strict=True)
        except FileNotFoundError:
            continue
        if resolved_path.parent != chapters_dir:
            continue
        chapter_no = chapter_number_from_name(path.name)
        if chapter_no is None:
            continue
        chapter_files.append((chapter_no, resolved_path))

    chapter_files.sort(key=lambda item: item[0])
    return chapter_files


def detect_latest_chapter_file(project_dir: Path) -> tuple[int, Path | None]:
    chapter_files = list_chapter_files(project_dir)
    if not chapter_files:
        return 0, None
    return chapter_files[-1]
