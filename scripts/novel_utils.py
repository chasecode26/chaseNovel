#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


CHAPTER_PATTERN = re.compile(r"第0*(\d+)章")
FLEXIBLE_CHAPTER_PATTERN = re.compile(
    r"第0*(\d+)章|ch(?:apter)?[-_ ]?0*(\d+)|^0*(\d+)",
    re.IGNORECASE,
)
SUMMARY_HEADING_PATTERN = re.compile(r"^##\s*第?0*(\d+)章[：:]\s*(.*)$")
PLACEHOLDER_PATTERNS = (
    re.compile(r"\{[A-Z0-9_]+\}"),
    re.compile(r"第_{2,}章"),
    re.compile(r"第\{[A-Z0-9_]+\}章"),
)
GENRE_HINTS = {
    "都市/系统流": ("都市", "系统", "职场", "现实逆袭"),
    "历史/权谋": ("历史", "权谋", "朝堂", "边关", "军政", "争霸"),
    "末世": ("末世", "囤货", "极寒", "尸潮", "安全屋", "灾变"),
    "玄幻/修仙": ("玄幻", "修仙", "仙侠", "升级", "宗门"),
    "仙侠/苟道": ("苟道", "长生", "稳健", "趋吉避凶"),
    "种田": ("种田", "经营", "农庄", "订单", "基建"),
    "盗墓/民国": ("盗墓", "摸金", "民国", "古墓", "下墓"),
}
SUBGENRE_HINTS = {
    "都市/系统流": {
        "低位反压": ("低位反压", "被压", "翻身", "逆袭", "改命"),
        "身份揭面": ("身份揭面", "揭面", "隐藏身份", "真实能力", "后台关系"),
        "规则碾压": ("规则碾压", "赢一套局", "规则失效", "制度反制", "资本规则"),
    },
    "历史/权谋": {
        "边关争霸": ("边关争霸", "边关", "边军", "军权", "监军", "粮道", "北地", "塞外"),
        "朝堂咬合": ("朝堂咬合", "朝堂", "台谏", "门阀", "圣意", "站队", "中枢"),
    },
    "末世": {
        "囤货": ("囤货", "抢时间", "补给", "物资", "仓库"),
        "安全屋成型": ("安全屋", "据点成形", "守住", "防御", "据点"),
        "秩序治理": ("秩序治理", "规则", "治理", "准入", "分配", "组织"),
    },
}


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


def count_effective_chars(text: str) -> int:
    return len(re.sub(r"\s+", "", normalize_input_text(text)))


def count_total_chapter_chars(project_dir: Path) -> int:
    total = 0
    for _, path in list_chapter_files(project_dir):
        total += count_effective_chars(read_text(path))
    return total


def split_summary_entries(text: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    if not text.strip():
        return entries

    current_heading = ""
    current_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if SUMMARY_HEADING_PATTERN.match(line.strip()):
            if current_heading:
                entries.append(build_summary_entry(current_heading, current_lines))
            current_heading = line.strip()
            current_lines = []
            continue
        if current_heading:
            current_lines.append(line)

    if current_heading:
        entries.append(build_summary_entry(current_heading, current_lines))
    return entries


def build_summary_entry(heading: str, lines: list[str]) -> dict[str, str]:
    match = SUMMARY_HEADING_PATTERN.match(heading)
    chapter = match.group(1) if match else ""
    title = match.group(2).strip() if match else heading.strip("# ").strip()
    body = "\n".join([heading, *lines]).strip()
    return {
        "chapter": chapter,
        "title": title,
        "body": body,
    }


def extract_summary_field(body: str, label: str) -> str:
    match = re.search(rf"-\s*{re.escape(label)}[:：]\s*(.+)", body)
    return match.group(1).strip() if match else ""


def normalize_genre_label(raw_text: str) -> str:
    text = normalize_input_text(raw_text).strip()
    if not text:
        return ""
    for canonical, hints in GENRE_HINTS.items():
        if canonical in text or any(hint in text for hint in hints):
            return canonical
    return text


def detect_project_genre(project_dir: Path) -> str:
    candidates = [
        project_dir / "00_memory" / "style.md",
        project_dir / "00_memory" / "voice.md",
        project_dir / "00_memory" / "plan.md",
    ]
    for path in candidates:
        text = read_text(path)
        for label in ("题材", "类型"):
            value = extract_line(text, f"- {label}") or extract_line(text, label)
            normalized = normalize_genre_label(value)
            if normalized and not has_placeholder(normalized):
                return normalized

    combined = "\n".join(read_text(path) for path in candidates if path.exists())
    normalized = normalize_genre_label(combined)
    return normalized or "未识别"


def detect_project_subgenre(project_dir: Path, genre: str | None = None) -> str:
    resolved_genre = genre or detect_project_genre(project_dir)
    hint_map = SUBGENRE_HINTS.get(resolved_genre, {})
    if not hint_map:
        return ""

    candidates = [
        project_dir / "00_memory" / "style.md",
        project_dir / "00_memory" / "voice.md",
        project_dir / "01_outline" / "volume_blueprint.md",
        project_dir / "00_memory" / "plan.md",
    ]
    explicit_labels = ("子类型", "子风格", "辅风格标签", "主风格标签")
    for path in candidates:
        text = read_text(path)
        for label in explicit_labels:
            value = extract_line(text, f"- {label}") or extract_line(text, label)
            normalized = normalize_input_text(value)
            if not normalized:
                continue
            for canonical, hints in hint_map.items():
                if canonical in normalized or any(hint in normalized for hint in hints):
                    return canonical

    combined = "\n".join(read_text(path) for path in candidates if path.exists())
    for canonical, hints in hint_map.items():
        if canonical in combined or any(hint in combined for hint in hints):
            return canonical
    return ""


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
