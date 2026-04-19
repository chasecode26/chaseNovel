from __future__ import annotations

from pathlib import Path

from evaluators.contracts import build_verdict
from runtime.contracts import ChapterBrief


PROGRESS_OVERSTEP_PAIRS = (
    ("只能起疑", ("确认", "彻底明白", "全都知道")),
    ("不能确认", ("确认", "彻底明白", "坐实")),
    ("不能坐实", ("坐实", "正式", "公开承认")),
    ("不能结盟", ("结盟", "联盟", "同盟")),
    ("不能掉马", ("掉马", "身份暴露", "暴露身份")),
    ("不能揭露", ("揭露", "揭开", "真相大白")),
    ("不能摊牌", ("摊牌", "明说", "挑明")),
)


ALLOWED_SCOPE_PAIRS = {
    "只允许关系公开度半推进": ("正式结盟", "彻底坐实", "公开承认"),
    "只允许现场压力抬高": ("结盟", "掉马", "真相大白"),
    "只允许起疑": ("确认", "彻底明白", "全都知道"),
    "只允许表层结果": ("幕后真相", "全部后手", "完整布局"),
}


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _load_text(path_value: object) -> str:
    path = Path(str(path_value).strip())
    if not str(path).strip() or not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _normalize(text: str) -> str:
    value = text.strip().lower()
    return "".join(char for char in value if char.isalnum() or "\u4e00" <= char <= "\u9fff")


def _contains(haystack: str, needle: str) -> bool:
    expected = _normalize(needle)
    if not expected:
        return False
    return expected in _normalize(haystack)


def from_runtime_output(brief: ChapterBrief, payload: dict[str, object]) -> dict[str, object]:
    outcome_signature = _as_dict(payload.get("outcome_signature", {}))
    manuscript_text = _load_text(payload.get("manuscript_path"))
    scene_summaries = " ".join(
        str(item.get("summary", "")).strip()
        for item in payload.get("scene_cards", [])
        if isinstance(item, dict)
    )
    haystack = " ".join(
        [
            manuscript_text,
            scene_summaries,
            str(outcome_signature.get("chapter_result", "")),
            str(outcome_signature.get("next_pull", "")),
        ]
    )

    evidence: list[str] = []

    for item in brief.must_not_payoff_yet[:3]:
        if _contains(haystack, item):
            evidence.append(f"本章禁止提前兑现“{item}”，但正文/结果链已经直接写到这层内容。")

    ceiling = brief.progress_ceiling.strip()
    if ceiling:
        for ceiling_marker, overstep_markers in PROGRESS_OVERSTEP_PAIRS:
            if ceiling_marker not in ceiling:
                continue
            for overstep in overstep_markers:
                if _contains(haystack, overstep):
                    evidence.append(f"章卡上限写着“{ceiling}”，但正文已经出现“{overstep}”级别的推进。")
                    break

    for scope in brief.allowed_change_scope[:3]:
        for forbidden in ALLOWED_SCOPE_PAIRS.get(scope, ()):
            if _contains(haystack, forbidden):
                evidence.append(f"本章允许变化范围是“{scope}”，但正文已经越到“{forbidden}”。")
                break

    blocking = bool(evidence)
    return build_verdict(
        dimension="chapter_progress",
        status="fail" if blocking else "pass",
        blocking=blocking,
        evidence=evidence,
        why_it_breaks="章节推进越过章卡上限，会把后续应保留的确认、兑现和关系变化提前写穿，直接破坏整段节奏。",
        minimal_fix="把已兑现内容降回试探、怀疑、表层结果或现场压力，删掉超出 allowed_change_scope 的确认式写法。",
        rewrite_scope="scene_beats + manuscript + chapter_result",
    )
