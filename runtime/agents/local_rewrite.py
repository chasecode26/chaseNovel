from __future__ import annotations

import json
import re
from pathlib import Path


def split_paragraphs(text: str) -> list[str]:
    return [chunk.strip() for chunk in re.split(r"\n\s*\n", text.strip()) if chunk.strip()]


def merge_by_scope(original: str, rewritten: str, rewrite_scope: str) -> tuple[str, dict[str, object]]:
    scope = rewrite_scope.strip().lower()
    original_paragraphs = split_paragraphs(original)
    rewritten_paragraphs = split_paragraphs(rewritten)
    operation = {
        "scope": rewrite_scope,
        "strategy": "full_replace",
        "preserved_paragraphs": 0,
        "replaced_paragraphs": len(rewritten_paragraphs),
    }

    if not original_paragraphs or not rewritten_paragraphs:
        return rewritten, operation

    if "chapter_tail" in scope:
        tail_count = min(3, len(rewritten_paragraphs), len(original_paragraphs))
        merged = [*original_paragraphs[:-tail_count], *rewritten_paragraphs[-tail_count:]]
        operation.update(
            {
                "strategy": "replace_tail",
                "preserved_paragraphs": max(0, len(original_paragraphs) - tail_count),
                "replaced_paragraphs": tail_count,
            }
        )
        return "\n\n".join(merged).strip() + "\n", operation

    if "dialogue" in scope and len(original_paragraphs) == len(rewritten_paragraphs):
        merged = []
        replaced = 0
        for old, new in zip(original_paragraphs, rewritten_paragraphs):
            if any(mark in old or mark in new for mark in ("“", "”", '"')):
                merged.append(new)
                replaced += 1
            else:
                merged.append(old)
        operation.update(
            {
                "strategy": "replace_dialogue_paragraphs",
                "preserved_paragraphs": len(merged) - replaced,
                "replaced_paragraphs": replaced,
            }
        )
        return "\n\n".join(merged).strip() + "\n", operation

    if "flagged_paragraphs" in scope and len(original_paragraphs) == len(rewritten_paragraphs):
        merged = []
        replaced = 0
        abstract_markers = ("意识到", "明白", "本质上", "这意味着", "真正的问题")
        for old, new in zip(original_paragraphs, rewritten_paragraphs):
            if any(marker in old for marker in abstract_markers):
                merged.append(new)
                replaced += 1
            else:
                merged.append(old)
        if replaced:
            operation.update(
                {
                    "strategy": "replace_flagged_abstract_paragraphs",
                    "preserved_paragraphs": len(merged) - replaced,
                    "replaced_paragraphs": replaced,
                }
            )
            return "\n\n".join(merged).strip() + "\n", operation

    return rewritten, operation


def write_rewrite_operation(project_dir: Path, chapter: int, operation: dict[str, object]) -> str:
    path = project_dir / "04_gate" / f"ch{chapter:03d}" / "rewrite_operation.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(operation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path.as_posix()
