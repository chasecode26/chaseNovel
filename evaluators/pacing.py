from __future__ import annotations

import re
from pathlib import Path

from evaluators.contracts import build_verdict


def _load_text(path_value: object) -> str:
    path = Path(str(path_value).strip())
    if not str(path).strip() or not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _effective_chars(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def _chapter_card_path(project_dir: Path, chapter: int) -> Path | None:
    candidates = [
        project_dir / "01_outline" / "chapter_cards" / f"ch{chapter:03d}.md",
        project_dir / "01_outline" / "chapter_cards" / f"chapter-{chapter:03d}.md",
        project_dir / "01_outline" / "chapter_cards" / f"chapter_{chapter:03d}.md",
        project_dir / "00_memory" / "chapter_cards" / f"ch{chapter:03d}.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _resolve_project_dir(project_dir: Path, payload: dict[str, object]) -> Path:
    payload_project = Path(str(payload.get("project", "")).strip())
    if str(payload_project).strip() and payload_project.exists():
        return payload_project

    context = payload.get("context", {})
    if isinstance(context, dict):
        context_project = Path(str(context.get("project", "")).strip())
        if str(context_project).strip() and context_project.exists():
            return context_project
    return project_dir


def _resolve_chapter(payload: dict[str, object]) -> int:
    for source in (payload, payload.get("context", {})):
        if not isinstance(source, dict):
            continue
        chapter_value = int(source.get("chapter", 0) or 0)
        if chapter_value > 0:
            return chapter_value
    return 0


def _extract_target_word_count(card_text: str) -> int:
    match = re.search(r"target_word_count[:：]\s*(\d+)", card_text, re.IGNORECASE)
    return int(match.group(1)) if match else 0


def from_runtime_output(project_dir: Path, payload: dict[str, object]) -> dict[str, object]:
    project_dir = _resolve_project_dir(project_dir, payload)
    chapter = _resolve_chapter(payload)
    manuscript_text = _load_text(payload.get("manuscript_path"))
    scene_cards = [item for item in payload.get("scene_cards", []) if isinstance(item, dict)]
    scene_count = int(payload.get("scene_count", 0) or 0) or len(scene_cards)
    word_count = int(payload.get("word_count", 0) or 0) or _effective_chars(manuscript_text)

    blockers: list[str] = []
    warnings: list[str] = []

    if scene_count <= 0:
        blockers.append("runtime draft 没有产出 scene cards，无法确认章节节奏骨架。")
    elif scene_count < 3:
        blockers.append(f"runtime draft 仅生成 {scene_count} 个 scene，章节推进层次不足。")
    elif scene_count > 6:
        warnings.append(f"runtime draft 生成了 {scene_count} 个 scene，节奏切分可能过碎。")

    card_path = _chapter_card_path(project_dir, chapter) if chapter > 0 else None
    if chapter <= 0:
        blockers.append("runtime draft 缺少有效 chapter 编号，无法锚定章节节奏目标。")
        target_word_count = 0
    elif card_path is None:
        blockers.append("未找到本章章卡，runtime 无法锚定章节节奏目标。")
        target_word_count = 0
    else:
        card_text = card_path.read_text(encoding="utf-8")
        target_word_count = _extract_target_word_count(card_text)
        if target_word_count <= 0:
            blockers.append("章卡缺少 `target_word_count`，runtime 无法校验正文节奏密度。")

    if word_count <= 0:
        blockers.append("runtime manuscript 为空，无法确认本章是否形成有效推进。")
    elif target_word_count > 0:
        min_word_count = max(900, int(target_word_count * 0.45))
        max_word_count = max(target_word_count + 1200, int(target_word_count * 1.6))
        if word_count < min_word_count:
            blockers.append(
                f"runtime manuscript 仅 {word_count} 字，低于节奏下限 {min_word_count}，结果密度不足。"
            )
        elif word_count > max_word_count:
            blockers.append(
                f"runtime manuscript 达到 {word_count} 字，高于节奏上限 {max_word_count}，章节可能拖滞。"
            )

    result_types = {
        str(item.get("result_type", "")).strip()
        for item in scene_cards
        if str(item.get("result_type", "")).strip()
    }
    if scene_cards and len(result_types) <= 1:
        warnings.append("scene cards 的 result_type 几乎没有变化，章节推进容易只剩单一重复拍点。")

    evidence = blockers or warnings
    return build_verdict(
        dimension="pacing",
        status="fail" if blockers else ("warn" if warnings else "pass"),
        blocking=bool(blockers),
        evidence=evidence,
        why_it_breaks="章节节奏如果没有字数目标、scene 分层和结果密度共同约束，runtime 会重新滑回失衡篇幅。",
        minimal_fix="回到 scene card 与正文密度层，补齐 target_word_count，并让每个 scene 都承担明确推进结果。",
        rewrite_scope="full_chapter" if blockers else "scene_cards + chapter_result",
    )
