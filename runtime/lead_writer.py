from __future__ import annotations

from runtime.contracts import ChapterBrief, ChapterContextPacket, EvaluatorVerdict, RuntimeDecision


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for item in values:
        text = item.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        deduped.append(text)
    return deduped


class LeadWriter:
    def _must_advance(self, packet: ChapterContextPacket) -> list[str]:
        return _dedupe(packet.open_threads[:3] or ([packet.next_goal] if packet.next_goal else []))

    def _must_not_repeat(self, packet: ChapterContextPacket) -> list[str]:
        repeat_markers = [
            warning
            for warning in packet.warnings
            if any(token in warning.lower() for token in ("repeat", "重复", "同一", "3-5"))
        ]
        return _dedupe(repeat_markers)

    def _required_payoff_or_pressure(
        self,
        packet: ChapterContextPacket,
        must_advance: list[str],
    ) -> list[str]:
        pressure = [warning for warning in packet.warnings if warning.strip()]
        if not pressure and must_advance:
            pressure = [f"本章必须兑现或抬高：{must_advance[0]}"]
        if not pressure and packet.next_goal:
            pressure = [f"本章必须制造可见推进：{packet.next_goal}"]
        return _dedupe(pressure[:3])

    def _scene_plan(
        self,
        packet: ChapterContextPacket,
        must_advance: list[str],
        required_payoff_or_pressure: list[str],
    ) -> list[str]:
        plan = [
            f"开场先锁定 {packet.current_place or '当前场域'} 的压力面，不要先讲背景。",
            f"中段必须推进 {must_advance[0] if must_advance else packet.next_goal or '当前目标'}，并落到可见结果。",
            f"章节结尾把钩子收束到 {packet.next_goal or '下一章压力'}，不要停在抽象判断。",
        ]
        if required_payoff_or_pressure:
            plan.insert(2, f"本章至少处理一个 payoff/pressure：{required_payoff_or_pressure[0]}")
        return _dedupe(plan)

    def _success_criteria(
        self,
        packet: ChapterContextPacket,
        must_advance: list[str],
        required_payoff_or_pressure: list[str],
    ) -> list[str]:
        criteria = [
            f"本章功能必须成立：{packet.next_goal or '推进当前目标'}",
            "章节内必须出现结果变化，而不是只补背景。",
            "章节尾部必须留下下一步压力或回收牵引。",
        ]
        if must_advance:
            criteria.append(f"至少推进一个 open thread：{must_advance[0]}")
        if required_payoff_or_pressure:
            criteria.append(f"至少处理一个 payoff/pressure：{required_payoff_or_pressure[0]}")
        return _dedupe(criteria)

    def create_brief(self, packet: ChapterContextPacket) -> ChapterBrief:
        must_advance = self._must_advance(packet)
        required_payoff_or_pressure = self._required_payoff_or_pressure(packet, must_advance)
        return ChapterBrief(
            chapter=packet.chapter,
            chapter_function=packet.next_goal or "推进当前章节目标",
            must_advance=must_advance,
            must_not_repeat=self._must_not_repeat(packet),
            hook_goal="延续当前压力并形成下一章牵引",
            allowed_threads=packet.open_threads,
            disallowed_moves=packet.forbidden_inventions,
            voice_constraints=packet.voice_rules,
            required_payoff_or_pressure=required_payoff_or_pressure,
            scene_plan=self._scene_plan(packet, must_advance, required_payoff_or_pressure),
            success_criteria=self._success_criteria(packet, must_advance, required_payoff_or_pressure),
        )

    def revise_brief(
        self,
        packet: ChapterContextPacket,
        previous_brief: ChapterBrief,
        decision: RuntimeDecision,
        verdicts: list[EvaluatorVerdict],
        *,
        attempt: int,
    ) -> ChapterBrief:
        rewrite_brief = decision.rewrite_brief
        blocking_dimensions = decision.blocking_dimensions or ["runtime"]
        blocking_fixes = [] if rewrite_brief is None else rewrite_brief.must_change
        blocking_reasons = [] if rewrite_brief is None else rewrite_brief.blocking_reasons
        evidence = [
            evidence_item
            for verdict in verdicts
            if verdict.dimension in blocking_dimensions
            for evidence_item in verdict.evidence[:1]
            if evidence_item.strip()
        ]
        return ChapterBrief(
            chapter=previous_brief.chapter,
            chapter_function=previous_brief.chapter_function,
            must_advance=previous_brief.must_advance,
            must_not_repeat=_dedupe(
                [
                    *previous_brief.must_not_repeat,
                    *(f"不要重复触发 {dimension} blocking" for dimension in blocking_dimensions),
                ]
            ),
            hook_goal=previous_brief.hook_goal,
            allowed_threads=previous_brief.allowed_threads,
            disallowed_moves=_dedupe(
                [
                    *previous_brief.disallowed_moves,
                    "不要直接拼接 evaluator 原话到正文",
                    "不要通过新增设定绕过 blocking 问题",
                ]
            ),
            voice_constraints=previous_brief.voice_constraints,
            required_payoff_or_pressure=_dedupe(
                [
                    *previous_brief.required_payoff_or_pressure,
                    *blocking_reasons[:2],
                    *blocking_fixes[:2],
                ]
            ),
            scene_plan=_dedupe(
                [
                    f"第 {attempt + 1} 轮重写先修 {blocking_dimensions[0]}，不要新增支线。",
                    *(f"逐条修复：{item}" for item in blocking_fixes[:3]),
                    *(f"证据回填：{item}" for item in evidence[:2]),
                    *previous_brief.scene_plan,
                ]
            ),
            success_criteria=_dedupe(
                [
                    *(f"通过 {dimension} 复核" for dimension in blocking_dimensions),
                    *(f"修复完成：{item}" for item in blocking_fixes[:3]),
                    *previous_brief.success_criteria,
                ]
            ),
        )
