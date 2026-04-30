from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from runtime.contracts import ChapterBrief, ChapterContextPacket, ChapterDirection


@dataclass(frozen=True)
class SceneBeat:
    index: int
    scene_goal: str
    conflict_object: str
    first_collision: str
    reversal: str
    cost: str
    information_release: str
    next_pull: str
    character_pressure: str = ""
    timeline_guardrail: str = ""
    setting_guardrail: str = ""
    foreshadow_or_payoff: str = ""
    human_language_rule: str = ""
    market_reader_hook: str = ""
    short_expectation: str = ""
    long_expectation: str = ""
    expectation_payoff: str = ""
    new_expectation: str = ""
    expectation_gap_risk: str = ""
    genre_framework_hint: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SceneBeatPlan:
    chapter: int
    beats: list[SceneBeat]

    def to_dict(self) -> dict[str, object]:
        return {"chapter": self.chapter, "beats": [item.to_dict() for item in self.beats]}


def _first(values: list[str], fallback: str) -> str:
    for value in values:
        text = str(value).strip()
        if text:
            return text
    return fallback


class SceneBeatPlanner:
    """Builds a concrete bridge between brief/direction and manuscript drafting."""

    def plan(
        self,
        packet: ChapterContextPacket,
        brief: ChapterBrief,
        direction: ChapterDirection | None,
    ) -> SceneBeatPlan:
        raw_scene_plan = [item.strip() for item in brief.scene_plan if item.strip()]
        scene_plan = raw_scene_plan or [
            brief.opening_image or packet.next_goal or "开场把人物放进压力现场",
            brief.midpoint_collision or brief.core_conflict or "中段让对手逼出选择",
            brief.result_change or "让局面发生不可逆变化",
            brief.closing_hook or brief.hook_goal or "章尾留下下一步代价",
        ]
        scene_plan = scene_plan[:5]
        conflict = (
            (direction.core_conflict if direction else "")
            or brief.core_conflict
            or _first(packet.open_threads, "当前压力")
        )
        result = (direction.result_change if direction else "") or brief.result_change or _first(brief.must_advance, "局面被推到新位置")
        hook = (direction.closing_hook if direction else "") or brief.closing_hook or brief.hook_goal or "新的代价追上来"
        emotional_cost = brief.emotional_beat or _first(brief.required_payoff_or_pressure, "赢面出现，但代价也随之落下")
        short_expectation = brief.core_conflict or brief.hook_goal or "读者想知道眼前这局能不能翻过去"
        long_expectation = _first(
            [*brief.allowed_threads[:1], *packet.open_threads[:1], *packet.pending_promises[:1]],
            "阶段目标、旧伏笔或关系裂缝继续牵引后续章节",
        )
        genre_framework_hint = self._genre_framework_hint(packet, brief)
        foreshadow_or_payoff = _first(
            [*packet.must_not_payoff_yet[:1], *brief.required_payoff_or_pressure[:1]],
            "本场至少留下一个可回收压力点。",
        )
        timeline_guardrail = packet.time_anchor or packet.arrival_timing or packet.travel_time_floor or "不压缩路程、消息抵达和反应时间。"
        setting_guardrail = packet.resource_state or packet.location_anchor or packet.current_place or "不新增未铺垫设定解决问题。"

        beats: list[SceneBeat] = []
        for index, scene_goal in enumerate(scene_plan, start=1):
            is_final = index == len(scene_plan)
            beats.append(
                SceneBeat(
                    index=index,
                    scene_goal=scene_goal,
                    conflict_object=conflict,
                    first_collision=f"用动作或对白先撞上：{conflict}",
                    reversal=result if is_final else f"让“{scene_goal}”出现阻滞或反向压力",
                    cost=emotional_cost if index >= 2 else "先付出一个小的姿态、资源或关系代价",
                    information_release=packet.knowledge_boundary or packet.message_flow or "只释放本场人物能知道的信息",
                    next_pull=hook if is_final else "把压力递到下一场，不提前总结",
                    character_pressure="让人物用动作、停顿或一句带目的的对白承压，不用旁白解释心理。",
                    timeline_guardrail=timeline_guardrail,
                    setting_guardrail=setting_guardrail,
                    foreshadow_or_payoff=foreshadow_or_payoff,
                    human_language_rule="少用判断句，多写人怎么做、怎么躲、怎么顶、怎么付代价。",
                    market_reader_hook="每场结束都要让读者知道：局面变了，下一步更贵。",
                    short_expectation=short_expectation if index == 1 else f"读者想看“{scene_goal}”如何被阻挡后仍推进",
                    long_expectation=long_expectation,
                    expectation_payoff=result if is_final else "给一个小回报：局面、信息、关系或资源至少变一项。",
                    new_expectation=hook if is_final else "场末挂上下一场更贵的问题，不能让期待停住。",
                    expectation_gap_risk="如果本场只解释不交锋，读者会在这里断期待。",
                    genre_framework_hint=genre_framework_hint,
                )
            )
        return SceneBeatPlan(chapter=brief.chapter, beats=beats)

    def _genre_framework_hint(self, packet: ChapterContextPacket, brief: ChapterBrief) -> str:
        fields = " ".join(
            [
                packet.project_name,
                packet.genre,
                packet.next_goal,
                brief.chapter_function,
                brief.core_conflict,
                " ".join(brief.must_advance),
            ]
        )
        if any(token in fields for token in ("系统", "金手指", "任务", "面板")):
            return "系统/金手指：条件清楚、反馈及时，副作用或代价明确。"
        if any(token in fields for token in ("重生", "前世", "复仇", "报仇")):
            return "重生复仇：前世信息差必须转化为当场行动优势。"
        if any(token in fields for token in ("都市", "公司", "职场", "欠债", "直播")):
            return "都市逆袭：现实不爽点先落地，再用行动拿掉不爽点。"
        if any(token in fields for token in ("修仙", "玄幻", "境界", "灵石", "宗门")):
            return "玄幻/仙侠：资源、境界和规则必须服务冲突，不做说明书。"
        if any(token in fields for token in ("感情", "婚", "追妻", "误会", "恋")):
            return "强情绪感情线：试探、让步、翻脸和保护要形成循环。"
        return "通用爽文：目标清楚、阻碍外化、主角主动、反应分层、爽点有代价。"


def write_scene_beat_plan(project_dir: Path, plan: SceneBeatPlan) -> dict[str, str]:
    beat_dir = project_dir / "04_gate" / f"ch{plan.chapter:03d}"
    beat_dir.mkdir(parents=True, exist_ok=True)
    json_path = beat_dir / "scene_beat_plan.json"
    md_path = beat_dir / "scene_beat_plan.md"
    json_path.write_text(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# SceneBeatPlan", "", f"- chapter: {plan.chapter}", "", "## Beats"]
    for beat in plan.beats:
        lines.extend(
            [
                f"### Beat {beat.index}",
                f"- scene_goal: {beat.scene_goal}",
                f"- conflict_object: {beat.conflict_object}",
                f"- first_collision: {beat.first_collision}",
                f"- reversal: {beat.reversal}",
                f"- cost: {beat.cost}",
                f"- information_release: {beat.information_release}",
                f"- next_pull: {beat.next_pull}",
                f"- character_pressure: {beat.character_pressure}",
                f"- timeline_guardrail: {beat.timeline_guardrail}",
                f"- setting_guardrail: {beat.setting_guardrail}",
                f"- foreshadow_or_payoff: {beat.foreshadow_or_payoff}",
                f"- human_language_rule: {beat.human_language_rule}",
                f"- market_reader_hook: {beat.market_reader_hook}",
                f"- short_expectation: {beat.short_expectation}",
                f"- long_expectation: {beat.long_expectation}",
                f"- expectation_payoff: {beat.expectation_payoff}",
                f"- new_expectation: {beat.new_expectation}",
                f"- expectation_gap_risk: {beat.expectation_gap_risk}",
                f"- genre_framework_hint: {beat.genre_framework_hint}",
            ]
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"scene_beat_plan_json": json_path.as_posix(), "scene_beat_plan_markdown": md_path.as_posix()}
