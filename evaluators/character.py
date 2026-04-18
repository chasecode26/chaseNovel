from __future__ import annotations

from evaluators.contracts import build_verdict


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _join_markers(values: list[object]) -> str:
    markers = [str(item) for item in values if str(item).strip()]
    return "、".join(markers)


def from_runtime_draft(payload: dict[str, object]) -> dict[str, object]:
    constraints = _as_dict(payload.get("character_constraints", {}))
    mentions = _as_dict(constraints.get("mentions", {}))
    protagonist = _as_dict(constraints.get("protagonist", {}))
    counterpart = _as_dict(constraints.get("counterpart", {}))
    behavior_snapshot = _as_dict(constraints.get("behavior_snapshot", {}))

    evidence: list[str] = []
    label_map = {
        "protagonist_goal": "主角当前诉求",
        "protagonist_taboo": "主角禁忌",
        "counterpart_goal": "对位角色诉求",
        "counterpart_fear": "对位角色恐惧",
    }
    for key, label in label_map.items():
        value = str(constraints.get(key, "")).strip()
        if not value:
            continue
        if not bool(mentions.get(key, False)):
            evidence.append(f"{label}“{value}”没有进入 runtime 正文约束。")

    protagonist_style = str(protagonist.get("decision_style", "")).strip()
    protagonist_tactic = str(protagonist.get("voice_tactic", "")).strip()
    protagonist_pressure = str(protagonist.get("pressure_mode", "")).strip()
    protagonist_name = str(protagonist.get("name", "")).strip()
    protagonist_taboo = str(constraints.get("protagonist_taboo", "")).strip()
    counterpart_goal = str(counterpart.get("goal", "")).strip()
    counterpart_pressure = str(counterpart.get("pressure_mode", "")).strip()
    counterpart_relationship = str(counterpart.get("relationship", "")).strip()

    cautious_markers = _as_list(behavior_snapshot.get("protagonist_cautious_markers", []))
    reckless_markers = _as_list(behavior_snapshot.get("protagonist_reckless_markers", []))
    taboo_break_markers = _as_list(behavior_snapshot.get("taboo_break_markers", []))
    counterpart_pressure_markers = _as_list(behavior_snapshot.get("counterpart_pressure_markers", []))
    counterpart_soft_markers = _as_list(behavior_snapshot.get("counterpart_soft_markers", []))
    protagonist_name_mentions = int(behavior_snapshot.get("protagonist_name_mentions", 0) or 0)
    counterpart_name_mentions = int(behavior_snapshot.get("counterpart_name_mentions", 0) or 0)

    if protagonist_style == "谨慎":
        if protagonist_tactic and "先判断" not in protagonist_tactic:
            evidence.append("主角标记为谨慎，但 voice tactic 没有体现“先判断”的策略。")
        if protagonist_pressure and "留余地" not in protagonist_pressure:
            evidence.append("主角标记为谨慎，但受压反应没有体现“留余地”。")
        if not cautious_markers:
            evidence.append("主角标记为谨慎，但正文行为里没有“先判断/确认/稳住/留余地”的痕迹。")
        if reckless_markers:
            evidence.append(f"主角标记为谨慎，但正文出现了偏冲动的动作标记：{_join_markers(reckless_markers)}。")

    if protagonist_style == "冲动" and protagonist_tactic and "先顶回去" not in protagonist_tactic:
        evidence.append("主角标记为冲动，但正文策略没有体现直接顶回去的倾向。")

    if protagonist_taboo and taboo_break_markers:
        evidence.append(f"主角禁忌是“{protagonist_taboo}”，但正文已经出现越界动作：{_join_markers(taboo_break_markers)}。")

    if counterpart_goal and not bool(mentions.get("counterpart_goal", False)):
        evidence.append(f"对位角色当前诉求“{counterpart_goal}”没有进入冲突推进。")

    if counterpart_pressure and "确认底牌" in counterpart_pressure and not bool(mentions.get("counterpart_fear", False)):
        evidence.append("对位角色受压策略依赖确认底牌，但正文没有把对应风险写出来。")

    if counterpart_goal and not counterpart_pressure_markers:
        evidence.append("对位角色有明确目标，但正文没有出现确认底牌、卡位或试探等具体施压动作。")

    if "盟友" in counterpart_relationship and not counterpart_soft_markers:
        evidence.append("对位角色与主角是盟友，但正文完全没有留出收手、迟疑或缓冲层。")

    if protagonist_name and protagonist_name_mentions <= 0:
        evidence.append("正文没有把主角拉到前台，角色行为承载不足。")

    if counterpart_name_mentions <= 0:
        evidence.append("正文没有把对位角色拉进冲突现场，对位压力不成形。")

    status = "warn" if evidence else "pass"
    return build_verdict(
        dimension="character",
        status=status,
        blocking=False,
        evidence=evidence,
        why_it_breaks="角色诉求、禁忌和策略如果只停留在设定层，正文会重新滑回通用型推进。",
        minimal_fix="把角色的诉求、禁忌、恐惧和行为策略直接落进 scene 目标、动作选择和对白反馈。",
        rewrite_scope="scene_beats + dialogue",
    )
