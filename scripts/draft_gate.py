#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from novel_utils import (
    detect_existing_chapter_file,
    find_chapter_card_path,
    load_previous_card_defaults,
    parse_chapter_card,
    read_text,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check chapter draft length against chaseNovel chapter card rules.")
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--chapter", help="Path to a specific drafted chapter file")
    parser.add_argument("--chapter-no", type=int, help="Existing drafted chapter number")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Do not write report files")
    return parser.parse_args()


def count_effective_chars(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def resolve_range(chapter_tier: str) -> tuple[int, int]:
    minimum = 2300
    maximum = 4500 if chapter_tier == "climax" else 3500
    return minimum, maximum


def load_chapter_card_context(project_dir: Path, chapter_no: int) -> tuple[Path | None, dict[str, str], dict[str, str]]:
    card_path = find_chapter_card_path(project_dir, chapter_no)
    card_text = read_text(card_path) if card_path else ""
    card = parse_chapter_card(card_text) if card_text else {}
    inferred_defaults: dict[str, str] = {}
    if not card_path:
        inferred_defaults = load_previous_card_defaults(project_dir, chapter_no)
        for key in ("chapter_tier", "target_word_count"):
            inferred_value = str(inferred_defaults.get(key, "")).strip()
            if inferred_value and not str(card.get(key, "")).strip():
                card[key] = inferred_value
    return card_path, card, inferred_defaults


def build_payload(project_dir: Path, chapter_no: int, chapter_path: Path) -> dict[str, object]:
    card_path, card, inferred_defaults = load_chapter_card_context(project_dir, chapter_no)
    chapter_tier = str(card.get("chapter_tier", "")).strip()
    target_word_count_raw = str(card.get("target_word_count", "")).strip()
    target_word_count = int(target_word_count_raw) if target_word_count_raw.isdigit() else 0
    word_count = count_effective_chars(read_text(chapter_path))
    chapter_card_source = "explicit"
    if not card_path:
        chapter_card_source = "previous_chapter_defaults" if inferred_defaults else "missing"

    warnings: list[str] = []
    blockers: list[str] = []

    if not card_path:
        if inferred_defaults:
            warnings.append("未找到本章显式章卡，当前沿用上一章的 `chapter_tier` / `target_word_count` 执行字数门禁。")
        else:
            blockers.append("未找到本章章卡，无法执行正文长度门禁。")
    if not chapter_tier:
        blockers.append("章卡缺少 `chapter_tier`。")
    if not target_word_count:
        blockers.append("章卡缺少 `target_word_count`。")

    min_words = max_words = 0
    if chapter_tier:
        min_words, max_words = resolve_range(chapter_tier)
        if word_count < min_words or word_count > max_words:
            blockers.append(
                f"本章有效字数为 {word_count}，不符合 {chapter_tier} 章节的允许范围 {min_words}-{max_words}。"
            )
        elif target_word_count and abs(word_count - target_word_count) > 600:
            warnings.append(
                f"本章有效字数为 {word_count}，与目标字数 {target_word_count} 偏差超过 600。"
            )

    status = "pass"
    if blockers:
        status = "fail"
    elif warnings:
        status = "warn"

    return {
        "project": project_dir.as_posix(),
        "chapter_no": chapter_no,
        "chapter_path": chapter_path.as_posix(),
        "chapter_card_path": card_path.as_posix() if card_path else "",
        "chapter_card_source": chapter_card_source,
        "chapter_tier": chapter_tier,
        "target_word_count": target_word_count,
        "word_count": word_count,
        "min_words": min_words,
        "max_words": max_words,
        "status": status,
        "warnings": warnings,
        "warning_count": len(warnings),
        "blockers": blockers,
        "blocker_count": len(blockers),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# 正文字数门禁",
        "",
        f"- 章节：`第{int(payload['chapter_no']):03d}章`",
        f"- 正文：`{payload['chapter_path']}`",
        f"- 章卡：`{payload['chapter_card_path'] or '未找到'}`",
        f"- 章卡来源：`{payload['chapter_card_source']}`",
        f"- 章节等级：`{payload['chapter_tier'] or '未填写'}`",
        f"- 目标字数：`{payload['target_word_count'] or '未填写'}`",
        f"- 实际字数：`{payload['word_count']}`",
        f"- 允许范围：`{payload['min_words']}-{payload['max_words']}`" if payload["max_words"] else "- 允许范围：`未判定`",
        f"- 结论：`{str(payload['status']).upper()}`",
        "",
        "## 预警",
    ]
    if payload["warnings"]:
        lines.extend([f"- {item}" for item in payload["warnings"]])
    else:
        lines.append("- 无")
    lines.extend(["", "## 阻断项"])
    if payload["blockers"]:
        lines.extend([f"- {item}" for item in payload["blockers"]])
    else:
        lines.append("- 无")
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    project_dir = Path(args.project).resolve()
    chapter_no, chapter_path = detect_existing_chapter_file(project_dir, args.chapter, args.chapter_no)
    payload = build_payload(project_dir, chapter_no, chapter_path)

    gate_dir = project_dir / "04_gate" / f"ch{chapter_no:03d}"
    report_path = gate_dir / "draft_gate.md"
    result_path = gate_dir / "draft_gate.json"
    payload["report_paths"] = {
        "markdown": report_path.as_posix(),
        "json": result_path.as_posix(),
    }

    if not args.dry_run:
        gate_dir.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render_markdown(payload), encoding="utf-8")
        result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"word_count={payload['word_count']}")
        print(f"report={payload['report_paths']['markdown']}")
    return 1 if payload["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
