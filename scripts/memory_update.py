#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from novel_utils import (
    count_total_chapter_chars,
    detect_existing_chapter_file,
    detect_latest_chapter_file,
    extract_pipe_table_rows,
    extract_state_value,
    read_text,
    split_summary_entries,
)


PLACE_SUFFIXES = ("驿", "城", "关", "楼", "营", "府", "宫", "殿", "阁", "坊", "巷", "镇", "村")
FORESHADOW_KEYWORDS = ("秘密", "真相", "身份", "线索", "暗号", "布局", "埋伏", "伏笔", "旧账")
PAYOFF_KEYWORDS = ("拿到", "到账", "突破", "奖励", "兑现", "翻盘", "反杀", "告白", "清算", "晋升")
EMOTION_KEYWORDS = (
    ("高压", ("追杀", "围杀", "暴露", "倒计时", "危机", "失守")),
    ("反击", ("翻盘", "反杀", "压住", "破局", "拿下")),
    ("悬压", ("秘密", "真相", "身份", "线索", "疑点")),
    ("拉扯", ("对视", "沉默", "嘴硬", "试探", "让步")),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update project memory and generate structured sync queues after a chapter is drafted."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--chapter", type=int, help="Target chapter number; defaults to the latest chapter")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    return parser.parse_args()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def replace_or_append_line(text: str, label: str, value: str) -> str:
    pattern = re.compile(rf"(^-?\s*{re.escape(label)}[:：]\s*).*$", re.MULTILINE)
    if pattern.search(text):
        return pattern.sub(lambda match: f"{match.group(1)}{value}", text, count=1)
    if text and not text.endswith("\n"):
        text += "\n"
    return text + f"- {label}：{value}\n"


def strip_heading_prefix(line: str) -> str:
    return re.sub(r"^#+\s*", "", line).strip()


def extract_title_and_lines(chapter_path: Path) -> tuple[str, list[str]]:
    content = read_text(chapter_path)
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    title = strip_heading_prefix(lines[0]) if lines else f"第{chapter_path.stem}章"
    body_lines = [line for line in lines[1:] if not line.startswith("#")]
    return title, body_lines


def detect_place(lines: list[str]) -> str:
    for line in lines[:10]:
        matches = re.findall(r"([^\s，。；：]{2,12})", line)
        for candidate in matches:
            if candidate.endswith(PLACE_SUFFIXES):
                return candidate
    return ""


def detect_emotion(lines: list[str]) -> str:
    text = "\n".join(lines[-8:] if len(lines) >= 8 else lines)
    for label, keywords in EMOTION_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return label
    return "推进"


def truncate_line(text: str, limit: int = 36) -> str:
    cleaned = text.strip().strip("，。；")
    return cleaned[:limit] if len(cleaned) > limit else cleaned


def find_signal_lines(lines: list[str], keywords: tuple[str, ...], limit: int = 3) -> list[str]:
    results: list[str] = []
    for line in lines:
        if any(keyword in line for keyword in keywords):
            candidate = truncate_line(line, 48)
            if candidate and candidate not in results:
                results.append(candidate)
        if len(results) >= limit:
            break
    return results


def parse_character_names(memory_dir: Path) -> list[str]:
    names: list[str] = []
    for source in ("character_arcs.md", "characters.md"):
        path = memory_dir / source
        for row in extract_pipe_table_rows(read_text(path))[1:]:
            if not row:
                continue
            name = row[0].strip()
            if not name or name in {"角色", "关系对", "人物"}:
                continue
            if " / " in name or "->" in name:
                continue
            if name not in names:
                names.append(name)
    return names


def find_character_mentions(lines: list[str], names: list[str], limit: int = 4) -> list[str]:
    text = "\n".join(lines)
    mentions = [name for name in names if name and name in text]
    return mentions[:limit]


def chapter_label(chapter_no: int) -> str:
    return f"第{chapter_no:03d}章"


def ensure_trailing_newline(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"


def normalize_heading(line: str) -> str:
    return line.strip().lstrip("#").strip()


def find_section_bounds(lines: list[str], heading_variants: list[str]) -> tuple[int, int] | None:
    section_start = None
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("##"):
            continue
        heading = normalize_heading(stripped)
        if any(variant in heading for variant in heading_variants):
            section_start = idx
            break
    if section_start is None:
        return None

    section_end = len(lines)
    for idx in range(section_start + 1, len(lines)):
        if lines[idx].strip().startswith("##"):
            section_end = idx
            break
    return section_start, section_end


def append_rows_to_section_table(
    text: str,
    heading_variants: list[str],
    rows: list[str],
    fallback_heading: str,
    fallback_header: str,
    fallback_separator: str,
) -> str:
    if not rows:
        return ensure_trailing_newline(text)

    lines = ensure_trailing_newline(text).splitlines()
    bounds = find_section_bounds(lines, heading_variants)
    if bounds is None:
        block = ["", f"## {fallback_heading}", "", fallback_header, fallback_separator, *rows]
        return ensure_trailing_newline("\n".join(lines + block).strip("\n"))

    section_start, section_end = bounds
    table_start = None
    for idx in range(section_start + 1, section_end):
        if lines[idx].strip().startswith("|"):
            table_start = idx
            break
    if table_start is None:
        insertion = [fallback_header, fallback_separator, *rows]
        new_lines = lines[: section_start + 1] + [""] + insertion + lines[section_start + 1 :]
        return ensure_trailing_newline("\n".join(new_lines))

    table_end = table_start
    while table_end < section_end and lines[table_end].strip().startswith("|"):
        table_end += 1
    new_lines = lines[:table_end] + rows + lines[table_end:]
    return ensure_trailing_newline("\n".join(new_lines))


def render_unified_patch(path: Path, before: str, after: str) -> str:
    if ensure_trailing_newline(before) == ensure_trailing_newline(after):
        return ""
    diff = difflib.unified_diff(
        ensure_trailing_newline(before).splitlines(),
        ensure_trailing_newline(after).splitlines(),
        fromfile=path.as_posix(),
        tofile=path.as_posix(),
        lineterm="",
    )
    return "\n".join(diff).strip()


def sha256_text(text: str) -> str:
    return hashlib.sha256(ensure_trailing_newline(text).encode("utf-8")).hexdigest()


def next_numeric_suffix(existing_ids: list[str], prefix: str) -> int:
    max_suffix = 0
    pattern = re.compile(rf"{re.escape(prefix)}(\d+)(?:-(\d+))?")
    for item_id in existing_ids:
        match = pattern.search(item_id)
        if not match:
            continue
        if match.group(2):
            max_suffix = max(max_suffix, int(match.group(2)))
        elif match.group(1):
            max_suffix = max(max_suffix, int(match.group(1)))
    return max_suffix + 1


def collect_existing_ids(text: str, prefix: str) -> list[str]:
    return re.findall(rf"{re.escape(prefix)}\d+(?:-\d+)?", text)


def infer_payoff_type(text: str) -> str:
    if any(keyword in text for keyword in ("身份", "真相", "秘密", "线索")):
        return "悬念"
    if any(keyword in text for keyword in ("告白", "信任", "关系", "心软")):
        return "感情"
    if any(keyword in text for keyword in ("突破", "升级", "反杀", "拿到", "到账")):
        return "爽点"
    return "成长"


def build_summary_fields(title: str, lines: list[str], characters: list[str]) -> dict[str, str]:
    core_event = truncate_line(lines[0], 48) if lines else title
    character_change = "、".join(characters) + " 被卷入本章变化" if characters else (truncate_line(lines[1], 40) if len(lines) > 1 else "待人工补充")
    detected_place = detect_place(lines)
    foreshadow_lines = find_signal_lines(lines, FORESHADOW_KEYWORDS)
    payoff_lines = find_signal_lines(lines, PAYOFF_KEYWORDS)
    hook_source = truncate_line(lines[-1], 48) if lines else title
    return {
        "核心事件": core_event or title,
        "人物变化": character_change or "待人工补充",
        "新增设定": detected_place or "无明显新增",
        "伏笔": " / ".join(foreshadow_lines or ["待人工补充"]),
        "情感基调": detect_emotion(lines),
        "承上": truncate_line(lines[1], 48) if len(lines) > 1 else "承接上一章推进",
        "启下": " / ".join(payoff_lines or [hook_source or "待人工补充"]),
        "关键台词": hook_source or "待人工补充",
    }


def render_summary_entry(chapter_no: int, title: str, fields: dict[str, str]) -> str:
    ordered_labels = ["核心事件", "人物变化", "新增设定", "伏笔", "情感基调", "承上", "启下", "关键台词"]
    lines = [f"## 第{chapter_no:03d}章：{title}"]
    lines.extend(f"- {label}：{fields.get(label, '待人工补充')}" for label in ordered_labels)
    return "\n".join(lines)


def upsert_recent_entry(recent_text: str, chapter_no: int, entry_text: str) -> str:
    entries = split_summary_entries(recent_text)
    for entry in entries:
        if entry.get("chapter") == str(chapter_no):
            return recent_text
    chunks = [entry["body"] for entry in entries]
    chunks.append(entry_text)
    return "\n\n".join(chunk.strip() for chunk in chunks if chunk.strip()) + "\n"


def extract_summary_field_from_entry(entry: dict[str, str], label: str) -> str:
    match = re.search(rf"-\s*{re.escape(label)}[:：]\s*(.+)", entry["body"])
    return match.group(1).strip() if match else ""


def archive_entries(entries: list[dict[str, str]], mid_text: str) -> str:
    if not entries:
        return mid_text
    start = int(entries[0]["chapter"])
    end = int(entries[-1]["chapter"])
    heading = f"## 第{start:03d}章 ~ 第{end:03d}章"
    if heading in mid_text:
        return mid_text

    core_events = [extract_summary_field_from_entry(entry, "核心事件") or entry["title"] for entry in entries[:4]]
    character_changes = [extract_summary_field_from_entry(entry, "人物变化") for entry in entries[:4] if extract_summary_field_from_entry(entry, "人物变化")]
    debts = [extract_summary_field_from_entry(entry, "伏笔") for entry in entries[:4] if extract_summary_field_from_entry(entry, "伏笔")]
    hooks = [extract_summary_field_from_entry(entry, "启下") for entry in entries[-2:] if extract_summary_field_from_entry(entry, "启下")]
    block = "\n".join(
        [
            heading,
            f"- 主线推进：{' / '.join(core_events[:3]) or '待人工补充'}",
            f"- 角色变化：{' / '.join(character_changes[:3]) or '待人工补充'}",
            f"- 伏笔与承诺：{' / '.join(debts[:3]) or '待人工补充'}",
            f"- 节奏问题 / 风险：{' / '.join(hooks[:2]) or '待人工补充'}",
        ]
    )
    prefix = mid_text.rstrip()
    if prefix:
        prefix += "\n\n"
    return prefix + block + "\n"


def rotate_recent_entries(recent_text: str, mid_text: str) -> tuple[str, str, int]:
    entries = split_summary_entries(recent_text)
    if len(entries) <= 10:
        normalized_recent = "\n\n".join(entry["body"].strip() for entry in entries if entry["body"].strip())
        return (normalized_recent + "\n") if normalized_recent else "", mid_text, 0

    archived = entries[:-10]
    kept = entries[-10:]
    new_recent = "\n\n".join(entry["body"].strip() for entry in kept if entry["body"].strip()) + "\n"
    new_mid = archive_entries(archived, mid_text)
    return new_recent, new_mid, len(archived)


def build_sync_queue(
    project_dir: Path,
    chapter_no: int,
    title: str,
    lines: list[str],
    summary_fields: dict[str, str],
    characters: list[str],
    total_words: int,
) -> dict[str, list[dict[str, str]]]:
    queue: dict[str, list[dict[str, str]]] = {
        "state.md": [
            {
                "confidence": "high",
                "reason": "已自动回写当前章节、最后更新与总字数。",
                "candidate": f"当前章节=第{chapter_no:03d}章 / 总字数={total_words}",
            }
        ],
        "timeline.md": [
            {
                "confidence": "medium",
                "reason": "本章核心事件已形成时间线候选。",
                "candidate": summary_fields["核心事件"],
            }
        ],
        "foreshadowing.md": [],
        "character_arcs.md": [],
        "payoff_board.md": [],
    }

    detected_place = detect_place(lines)
    if detected_place:
        queue["timeline.md"][0]["candidate"] += f" / 地点={detected_place}"

    for item in find_signal_lines(lines, FORESHADOW_KEYWORDS):
        queue["foreshadowing.md"].append(
            {
                "confidence": "medium",
                "reason": "命中秘密/身份/线索类信号，可能需要登记新伏笔或更新旧伏笔状态。",
                "candidate": item,
            }
        )

    for item in find_signal_lines(lines, PAYOFF_KEYWORDS):
        queue["payoff_board.md"].append(
            {
                "confidence": "medium",
                "reason": "命中兑现/收获/反杀类信号，可能需要推进承诺表。",
                "candidate": item,
            }
        )

    for name in characters:
        queue["character_arcs.md"].append(
            {
                "confidence": "medium",
                "reason": "本章出现核心角色，建议确认是否发生阶段变化或关系刷新。",
                "candidate": name,
            }
        )

    if not queue["foreshadowing.md"]:
        queue["foreshadowing.md"].append(
            {
                "confidence": "low",
                "reason": "未识别到显式伏笔信号，仍建议人工确认是否有延后或回收。",
                "candidate": title,
            }
        )
    if not queue["payoff_board.md"]:
        queue["payoff_board.md"].append(
            {
                "confidence": "low",
                "reason": "未识别到显式兑现信号，仍建议核对承诺是否被推进或继续拖欠。",
                "candidate": summary_fields["启下"],
            }
        )
    if not queue["character_arcs.md"]:
        queue["character_arcs.md"].append(
            {
                "confidence": "low",
                "reason": "未识别到核心角色命中，建议人工确认边缘角色是否发生弧线变化。",
                "candidate": summary_fields["人物变化"],
            }
        )
    return queue


def build_timeline_patch(
    memory_dir: Path,
    chapter_no: int,
    title: str,
    lines: list[str],
    characters: list[str],
    state_text: str,
) -> dict[str, str]:
    path = memory_dir / "timeline.md"
    before = read_text(path)
    absolute_time = extract_state_value(state_text, "当前绝对时间") or "待确认时间"
    relative_time = extract_state_value(state_text, "距上章过去") or "待确认间隔"
    event = truncate_line(lines[0], 32) if lines else title
    people = "、".join(characters) if characters else "待确认角色"
    note = detect_place(lines) or title
    row = f"| {absolute_time} | {relative_time} | {event} | {people} | {chapter_label(chapter_no)} | {note} |"
    if row in before:
        return {}
    after = append_rows_to_section_table(
        before,
        ["主线时间线"],
        [row],
        "主线时间线",
        "| 时间点 | 相对时间 | 事件 | 涉及人物 | 章节 | 备注 |",
        "|--------|---------|------|---------|------|------|",
    )
    return {
        "target": "timeline.md",
        "path": path.as_posix(),
        "confidence": "high",
        "summary": f"追加 {chapter_label(chapter_no)} 的主线时间线事件",
        "before_sha256": sha256_text(before),
        "after_content": ensure_trailing_newline(after),
        "patch": render_unified_patch(path, before, after),
    }


def build_foreshadow_patch(
    memory_dir: Path,
    chapter_no: int,
    title: str,
    lines: list[str],
    characters: list[str],
) -> dict[str, str]:
    path = memory_dir / "foreshadowing.md"
    before = read_text(path)
    signals = find_signal_lines(lines, FORESHADOW_KEYWORDS, limit=2) or [title]
    existing_ids = collect_existing_ids(before, "FL")
    start_suffix = next_numeric_suffix(existing_ids, f"FL{chapter_no:03d}-")
    rows: list[str] = []
    who_knows = "、".join(characters) if characters else "待确认角色"
    for offset, signal in enumerate(signals, start=start_suffix):
        row = (
            f"| FL{chapter_no:03d}-{offset} | {chapter_label(chapter_no)} | {signal} | {who_knows} | "
            f"{truncate_line(lines[0], 20) if lines else title} | 若本章判断失真则作废 | 第{chapter_no + 2:03d}章 | 🟡中 | 待回收 |"
        )
        if signal in before or row in before:
            continue
        rows.append(row)
    if not rows:
        return {}
    after = append_rows_to_section_table(
        before,
        ["活跃伏笔"],
        rows,
        "活跃伏笔",
        "| ID | 埋设章节 | 伏笔内容 | 谁知道 | 触发条件 | 失效条件 | 预计回收章节 | 紧急度 | 状态 |",
        "|----|---------|---------|--------|---------|---------|------------|-------|------|",
    )
    return {
        "target": "foreshadowing.md",
        "path": path.as_posix(),
        "confidence": "medium",
        "summary": f"补入 {len(rows)} 条待确认伏笔候选",
        "before_sha256": sha256_text(before),
        "after_content": ensure_trailing_newline(after),
        "patch": render_unified_patch(path, before, after),
    }


def build_payoff_patch(
    memory_dir: Path,
    chapter_no: int,
    title: str,
    lines: list[str],
) -> dict[str, str]:
    path = memory_dir / "payoff_board.md"
    before = read_text(path)
    signals = find_signal_lines(lines, PAYOFF_KEYWORDS, limit=2) or [title]
    existing_ids = collect_existing_ids(before, "PO")
    suffix = next_numeric_suffix(existing_ids, "PO")
    rows: list[str] = []
    for signal in signals:
        row = (
            f"| PO{suffix:03d} | {infer_payoff_type(signal)} | {signal} | {chapter_label(chapter_no)} | "
            f"第{chapter_no + 2:03d}章 | 待兑现 | 🟡中 | 自动同步候选 |"
        )
        suffix += 1
        if signal in before or row in before:
            continue
        rows.append(row)
    if not rows:
        return {}
    after = append_rows_to_section_table(
        before,
        ["活跃承诺"],
        rows,
        "活跃承诺",
        "| 承诺ID | 类型 | 承诺内容 | 首次立下章节 | 预期兑现窗口 | 当前状态 | 当前压力 | 备注 |",
        "|--------|------|---------|-------------|-------------|---------|---------|------|",
    )
    return {
        "target": "payoff_board.md",
        "path": path.as_posix(),
        "confidence": "medium",
        "summary": f"补入 {len(rows)} 条承诺/兑现候选",
        "before_sha256": sha256_text(before),
        "after_content": ensure_trailing_newline(after),
        "patch": render_unified_patch(path, before, after),
    }


def build_character_arc_patch(
    memory_dir: Path,
    chapter_no: int,
    title: str,
    lines: list[str],
    characters: list[str],
) -> dict[str, str]:
    path = memory_dir / "character_arcs.md"
    before = read_text(path)
    subjects = characters[:2] or ["待确认角色"]
    rows: list[str] = []
    performance = truncate_line(lines[1], 24) if len(lines) > 1 else title
    for subject in subjects:
        row = f"| {chapter_label(chapter_no)} | {subject} | 待确认推进 | {performance} | 确认是否进入新阶段或刷新关系位置 |"
        if row in before:
            continue
        rows.append(row)
    if not rows:
        return {}
    after = append_rows_to_section_table(
        before,
        ["角色弧风险记录"],
        rows,
        "角色弧风险记录",
        "| 章节 | 角色 | 风险类型 | 表现 | 修正建议 |",
        "|------|------|---------|------|---------|",
    )
    return {
        "target": "character_arcs.md",
        "path": path.as_posix(),
        "confidence": "medium",
        "summary": f"追加 {len(rows)} 条角色弧确认记录",
        "before_sha256": sha256_text(before),
        "after_content": ensure_trailing_newline(after),
        "patch": render_unified_patch(path, before, after),
    }


def build_sync_patches(
    memory_dir: Path,
    chapter_no: int,
    title: str,
    lines: list[str],
    characters: list[str],
    state_text: str,
) -> dict[str, dict[str, str]]:
    patches = {}
    for item in (
        build_timeline_patch(memory_dir, chapter_no, title, lines, characters, state_text),
        build_foreshadow_patch(memory_dir, chapter_no, title, lines, characters),
        build_payoff_patch(memory_dir, chapter_no, title, lines),
        build_character_arc_patch(memory_dir, chapter_no, title, lines, characters),
    ):
        if item and item.get("patch"):
            patches[item["target"]] = item
    return patches


def render_sync_patches_markdown(chapter_no: int, patches: dict[str, dict[str, str]]) -> str:
    lines = [
        f"# {chapter_label(chapter_no)} 记忆落表 Patch",
        "",
        "> 以下 patch 仅供确认，不会自动写入四张记忆表。",
        "",
    ]
    if not patches:
        lines.append("- 本章未生成新的落表 patch。")
        return "\n".join(lines) + "\n"

    for target, item in patches.items():
        lines.extend(
            [
                f"## {target}",
                f"- confidence: {item.get('confidence', 'medium')}",
                f"- summary: {item.get('summary', '待确认')}",
                "```diff",
                item.get("patch", "").strip(),
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def render_sync_queue(
    chapter_no: int,
    queue: dict[str, list[dict[str, str]]],
    patches: dict[str, dict[str, str]],
) -> str:
    recommended_order = [target for target in ("timeline.md", "foreshadowing.md", "payoff_board.md", "character_arcs.md") if target in patches]
    lines = [
        f"# {chapter_label(chapter_no)} 记忆同步队列",
        "",
        "> 同步队列仍然只是候选，但已为四张核心记忆表附带可确认 patch。",
        "",
    ]
    if recommended_order:
        lines.append(f"- 推荐应用顺序：{' -> '.join(recommended_order)}")
        lines.append("")
    for target, items in queue.items():
        lines.append(f"## {target}")
        if target in patches:
            lines.append(f"- [patch-ready] {patches[target].get('summary', '已生成候选 patch')}")
        for item in items:
            lines.append(f"- [{item['confidence']}] {item['candidate']} | 原因：{item['reason']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_memory_report(
    chapter_no: int,
    title: str,
    archive_count: int,
    queue_markdown_path: Path,
    patch_markdown_path: Path,
    patch_count: int,
) -> str:
    return "\n".join(
        [
            "# 记忆回写报告",
            "",
            f"- 章节：{chapter_label(chapter_no)}",
            f"- 标题：{title}",
            f"- 生成时间：{datetime.now().isoformat(timespec='seconds')}",
            "",
            "## 已自动完成",
            "- 更新 `state.md` 的当前章节、最后更新与总字数",
            "- 追加 `summaries/recent.md` 的结构化章节摘要",
            "- 超过 10 章时自动把更早摘要归档到 `summaries/mid.md`",
            f"- 生成多文件记忆同步队列：`{queue_markdown_path.as_posix()}`",
            f"- 生成可确认的半自动落表 patch：`{patch_markdown_path.as_posix()}`",
            "",
            "## 本次归档情况",
            f"- 从 recent 归档到 mid 的章节数：{archive_count}",
            f"- 本次生成的 patch 数量：{patch_count}",
            "",
            "## 待人工确认",
            "- 核对 `timeline.md` 候选事件是否需要落地",
            "- 核对 `foreshadowing.md` 是否需要新增/回收/延后条目",
            "- 核对 `character_arcs.md` 是否需要更新阶段或风险",
            "- 核对 `payoff_board.md` 是否需要推进承诺或记录拖欠",
            "",
        ]
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    project_dir = Path(args.project).resolve()
    latest_chapter_no, _ = detect_latest_chapter_file(project_dir)
    target_chapter = args.chapter or latest_chapter_no

    if target_chapter <= 0:
        payload = {
            "project": project_dir.as_posix(),
            "updated": False,
            "reason": "no chapters found",
            "status": "warn",
            "warnings": ["当前未检测到章节文件，无法执行记忆回写。"],
            "warning_count": 1,
            "report_paths": {},
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print("status=warn")
            print("warning_count=1")
            print("updated=false")
            print("reason=no chapters found")
        return 0

    _, chapter_path = detect_existing_chapter_file(project_dir, None, target_chapter)
    memory_dir = project_dir / "00_memory"
    state_path = memory_dir / "state.md"
    recent_path = memory_dir / "summaries" / "recent.md"
    mid_path = memory_dir / "summaries" / "mid.md"
    queue_md_path = memory_dir / "retrieval" / "memory_sync_queue.md"
    queue_json_path = memory_dir / "retrieval" / "memory_sync_queue.json"
    patch_md_path = memory_dir / "retrieval" / "memory_sync_patches.md"
    patch_json_path = memory_dir / "retrieval" / "memory_sync_patches.json"
    report_path = project_dir / "04_gate" / f"ch{target_chapter:03d}" / "memory_update.md"

    title, body_lines = extract_title_and_lines(chapter_path)
    total_words = count_total_chapter_chars(project_dir)
    state_text = read_text(state_path)
    state_text = replace_or_append_line(state_text, "当前章节", f"第{target_chapter:03d}章")
    state_text = replace_or_append_line(state_text, "最后更新", datetime.now().strftime("%Y-%m-%d"))
    state_text = replace_or_append_line(state_text, "总字数", str(total_words))
    if not extract_state_value(state_text, "当前地点"):
        detected_place = detect_place(body_lines)
        if detected_place:
            state_text = replace_or_append_line(state_text, "当前地点", detected_place)

    character_names = parse_character_names(memory_dir)
    character_mentions = find_character_mentions(body_lines, character_names)
    summary_fields = build_summary_fields(title, body_lines, character_mentions)
    recent_text = upsert_recent_entry(read_text(recent_path), target_chapter, render_summary_entry(target_chapter, title, summary_fields))
    recent_text, mid_text, archived_count = rotate_recent_entries(recent_text, read_text(mid_path))
    sync_queue = build_sync_queue(project_dir, target_chapter, title, body_lines, summary_fields, character_mentions, total_words)
    sync_patches = build_sync_patches(memory_dir, target_chapter, title, body_lines, character_mentions, state_text)

    payload = {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "pass",
        "updated": True,
        "chapter": target_chapter,
        "title": title,
        "state_path": state_path.as_posix(),
        "recent_path": recent_path.as_posix(),
        "mid_path": mid_path.as_posix(),
        "report_path": report_path.as_posix(),
        "queue_markdown_path": queue_md_path.as_posix(),
        "queue_json_path": queue_json_path.as_posix(),
        "patch_markdown_path": patch_md_path.as_posix(),
        "patch_json_path": patch_json_path.as_posix(),
        "archived_from_recent": archived_count,
        "total_effective_words": total_words,
        "summary_fields": summary_fields,
        "sync_queue": sync_queue,
        "sync_patches": sync_patches,
        "recommended_apply_order": [target for target in ("timeline.md", "foreshadowing.md", "payoff_board.md", "character_arcs.md") if target in sync_patches],
        "warnings": [],
        "warning_count": 0,
        "report_paths": {
            "memory_report": report_path.as_posix(),
            "state": state_path.as_posix(),
            "recent": recent_path.as_posix(),
            "mid": mid_path.as_posix(),
            "queue_markdown": queue_md_path.as_posix(),
            "queue_json": queue_json_path.as_posix(),
            "patch_markdown": patch_md_path.as_posix(),
            "patch_json": patch_json_path.as_posix(),
        },
    }

    if not character_mentions:
        payload["warnings"].append("本章未识别到核心角色命中，角色弧同步队列需要人工重点确认。")
    if not detect_place(body_lines):
        payload["warnings"].append("本章未自动识别到明确地点，timeline/state 的地点锚点建议人工补写。")
    if args.dry_run:
        payload["warnings"].append("dry-run 模式未实际写入 state.md、recent.md、mid.md 与同步队列。")
        payload["status"] = "warn"
    payload["warning_count"] = len(payload["warnings"])
    if payload["warning_count"] and payload["status"] == "pass":
        payload["status"] = "warn"

    if not args.dry_run:
        write_text(state_path, state_text)
        write_text(recent_path, recent_text)
        write_text(mid_path, mid_text)
        write_text(queue_md_path, render_sync_queue(target_chapter, sync_queue, sync_patches))
        write_text(queue_json_path, json.dumps(payload["sync_queue"], ensure_ascii=False, indent=2))
        write_text(patch_md_path, render_sync_patches_markdown(target_chapter, sync_patches))
        write_text(patch_json_path, json.dumps(sync_patches, ensure_ascii=False, indent=2))
        write_text(
            report_path,
            build_memory_report(
                target_chapter,
                title,
                archived_count,
                queue_md_path,
                patch_md_path,
                len(sync_patches),
            ),
        )

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"warning_count={payload['warning_count']}")
        print("updated=true")
        print(f"chapter={target_chapter}")
        print(f"report={payload['report_paths']['memory_report']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



