from __future__ import annotations

from pathlib import Path

from evaluators.contracts import build_verdict
from runtime.contracts import ChapterBrief


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _normalize(text: str) -> str:
    normalized = text.strip().lower()
    for marker in (
        "本章必须兑现或抬高：",
        "本章必须制造可见推进：",
        "至少推进一个 open thread：",
        "至少处理一个 payoff/pressure：",
    ):
        if normalized.startswith(marker):
            normalized = normalized.removeprefix(marker)
            break
    normalized = "".join(char for char in normalized if char.isalnum() or "\u4e00" <= char <= "\u9fff")
    return normalized


def _load_text(path_value: object) -> str:
    path = Path(str(path_value).strip())
    if not str(path).strip() or not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _contains_requirement(haystack: str, requirement: str) -> bool:
    expected = _normalize(requirement)
    if not expected:
        return True
    normalized_haystack = _normalize(haystack)
    if expected in normalized_haystack:
        return True
    if len(expected) < 6:
        return False
    chunks = [expected[index : index + 4] for index in range(0, len(expected) - 3, 2)]
    hits = sum(chunk in normalized_haystack for chunk in chunks)
    return hits >= min(2, len(chunks))


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

    targets: list[str] = []
    targets.extend(item for item in brief.must_advance[:2] if item.strip())
    targets.extend(
        item
        for item in brief.required_payoff_or_pressure[:2]
        if item.strip().startswith("本章必须")
    )

    evidence = [
        f"承诺/压力“{item}”没有进入 chapter_result、scene summary 或正文兑现链。"
        for item in targets
        if not _contains_requirement(haystack, item)
    ]
    blocking = bool(evidence)
    return build_verdict(
        dimension="promise_payoff",
        status="fail" if blocking else "pass",
        blocking=blocking,
        evidence=evidence,
        why_it_breaks="章节承诺或压力没有进入兑现链时，读者会感到只在铺垫，没有真正回收或抬高债务。",
        minimal_fix="把本章必须推进的承诺落到 scene result、chapter_result 或尾钩压力上，不要停在意图层。",
        rewrite_scope="scene_beats + chapter_result + hook",
    )
