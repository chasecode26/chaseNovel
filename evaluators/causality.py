from __future__ import annotations

from evaluators.contracts import build_verdict


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def from_runtime_output(payload: dict[str, object]) -> dict[str, object]:
    scene_cards = [item for item in _as_list(payload.get("scene_cards", [])) if isinstance(item, dict)]
    outcome_signature = _as_dict(payload.get("outcome_signature", {}))

    evidence: list[str] = []
    if len(scene_cards) < 3:
        evidence.append("scene cards 少于 3 段，因果推进容易直接跳结论。")

    result_types = {
        str(item.get("result_type", "")).strip()
        for item in scene_cards
        if str(item.get("result_type", "")).strip()
    }
    if scene_cards and len(result_types) < 2:
        evidence.append("本章 result_type 变化不足，推进更像同一结果的平移重复。")

    chapter_result = str(outcome_signature.get("chapter_result", "")).strip()
    next_pull = str(outcome_signature.get("next_pull", "")).strip()
    if not chapter_result:
        evidence.append("outcome signature 缺少 chapter_result，正文结果没有落点。")
    if not next_pull:
        evidence.append("outcome signature 缺少 next_pull，结果没有后续压力承接。")

    first_result = str(scene_cards[0].get("result_type", "")).strip() if scene_cards else ""
    last_result = str(scene_cards[-1].get("result_type", "")).strip() if scene_cards else ""
    if first_result and last_result and first_result == last_result:
        evidence.append("首尾 scene result_type 没有变化，章节因果链没有形成阶段位移。")

    blocking = bool(evidence)
    return build_verdict(
        dimension="causality",
        status="fail" if blocking else "pass",
        blocking=blocking,
        evidence=evidence,
        why_it_breaks="章节结果、代价与尾钩没有串成因果链时，正文会变成只有情绪和姿态的平铺推进。",
        minimal_fix="把 scene result -> chapter_result -> next_pull 串成一条可见因果链，避免只写状态不写结果。",
        rewrite_scope="scene_cards + chapter_result + hook",
    )
