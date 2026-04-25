from __future__ import annotations

from pathlib import Path

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


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _parse_markdown_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("- "):
            continue
        payload = line[2:]
        for separator in ("：", ":"):
            if separator not in payload:
                continue
            key, value = payload.split(separator, 1)
            key = key.strip()
            value = value.strip()
            if key and value:
                fields[key] = value
            break
    return fields


def _pick_field(fields: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = fields.get(key, "").strip()
        if value:
            return value
    return ""


class LeadWriter:
    def _must_advance(self, packet: ChapterContextPacket) -> list[str]:
        if packet.progress_floor:
            return _dedupe([packet.progress_floor, *packet.open_threads[:2]])
        return _dedupe(packet.open_threads[:3] or ([packet.next_goal] if packet.next_goal else []))

    def _must_not_repeat(self, packet: ChapterContextPacket) -> list[str]:
        repeat_markers = [
            warning
            for warning in packet.warnings
            if any(token in warning.lower() for token in ("repeat", "重复", "同一", "3-5"))
        ]
        return _dedupe(repeat_markers)

    def _load_dramatic_card(self, packet: ChapterContextPacket) -> dict[str, str]:
        project_dir = Path(packet.project)
        text = _read_text(project_dir / "00_memory" / "chapter-dramatic-card.md")
        if not text.strip():
            return {}
        return _parse_markdown_fields(text)

    def _required_payoff_or_pressure(
        self,
        packet: ChapterContextPacket,
        must_advance: list[str],
        dramatic_card: dict[str, str],
    ) -> list[str]:
        pressure: list[str] = []
        result_change = _pick_field(dramatic_card, "结果变化", "result_change")
        midpoint_collision = _pick_field(dramatic_card, "中段碰撞", "midpoint_collision")
        closing_hook = _pick_field(dramatic_card, "章末钩子", "closing_hook")
        core_conflict = _pick_field(dramatic_card, "核心冲突", "core_conflict")

        pressure.extend(item for item in (midpoint_collision, result_change, closing_hook, core_conflict) if item)
        if not pressure:
            pressure.extend(warning for warning in packet.warnings if warning.strip())
        if not pressure and must_advance:
            pressure.append(f"本章必须把这条推进做实：{must_advance[0]}")
        if not pressure and packet.next_goal:
            pressure.append(f"本章必须制造可见推进：{packet.next_goal}")
        if packet.message_flow:
            pressure.append(f"消息传递链不能乱：{packet.message_flow}")
        if packet.who_cannot_know_yet:
            pressure.append(f"知情边界不能越线：{packet.who_cannot_know_yet}")
        if packet.must_not_payoff_yet:
            pressure.append(f"这条线只能预热不能兑现：{packet.must_not_payoff_yet[0]}")
        return _dedupe(pressure[:4])

    def _scene_plan(
        self,
        packet: ChapterContextPacket,
        must_advance: list[str],
        required_payoff_or_pressure: list[str],
        dramatic_card: dict[str, str],
    ) -> list[str]:
        opening_image = _pick_field(dramatic_card, "开场画面", "opening_image")
        midpoint_collision = _pick_field(dramatic_card, "中段碰撞", "midpoint_collision")
        result_change = _pick_field(dramatic_card, "结果变化", "result_change")
        closing_hook = _pick_field(dramatic_card, "章末钩子", "closing_hook")

        if any((opening_image, midpoint_collision, result_change, closing_hook)):
            plan = [opening_image, midpoint_collision, result_change, closing_hook]
            if packet.time_anchor or packet.location_anchor:
                plan.insert(
                    1,
                    f"起章先钉死时空锚点：{packet.time_anchor or '当前时间'} / {packet.location_anchor or packet.current_place or '当前地点'}。",
                )
            if packet.present_characters:
                plan.insert(2, f"在场人物只保留：{'、'.join(packet.present_characters[:6])}。")
            if packet.who_knows_now or packet.who_cannot_know_yet:
                plan.append(
                    f"知情边界要稳住：可知={packet.who_knows_now or '未明'}；不可知={packet.who_cannot_know_yet or '未明'}。"
                )
            if packet.must_not_payoff_yet:
                plan.append(f"结尾只能留压，不能提前兑现：{packet.must_not_payoff_yet[0]}。")
            return _dedupe(plan)

        plan = [
            f"开场先锁定 {packet.current_place or '当前场域'} 的压力，不要先讲背景。",
            f"中段必须推进 {must_advance[0] if must_advance else packet.next_goal or '当前目标'}，并落到可见结果。",
            f"章节结尾把钩子收束到 {packet.next_goal or '下一章压力'}，不要停在抽象判断。",
        ]
        if packet.time_anchor or packet.location_anchor:
            plan.insert(
                1,
                f"起章先钉死时空锚点：{packet.time_anchor or '当前时间'} / {packet.location_anchor or packet.current_place or '当前地点'}。",
            )
        if packet.present_characters:
            plan.insert(2, f"在场人物只保留：{'、'.join(packet.present_characters[:6])}。")
        if packet.who_knows_now or packet.who_cannot_know_yet:
            plan.insert(3, f"知情边界要稳住：可知={packet.who_knows_now or '未明'}；不可知={packet.who_cannot_know_yet or '未明'}。")
        if packet.progress_ceiling:
            plan.insert(4, f"中段推进最多只能到：{packet.progress_ceiling}。")
        if packet.allowed_change_scope:
            plan.insert(5, f"本章变化范围只允许：{'、'.join(packet.allowed_change_scope[:3])}。")
        if required_payoff_or_pressure:
            plan.insert(6, f"本章至少处理一个压力点：{required_payoff_or_pressure[0]}")
        if packet.must_not_payoff_yet:
            plan.append(f"结尾只能留下压力，不能提前兑现：{packet.must_not_payoff_yet[0]}。")
        return _dedupe(plan)

    def _success_criteria(
        self,
        packet: ChapterContextPacket,
        must_advance: list[str],
        required_payoff_or_pressure: list[str],
        dramatic_card: dict[str, str],
    ) -> list[str]:
        result_change = _pick_field(dramatic_card, "结果变化", "result_change")
        emotional_beat = _pick_field(dramatic_card, "情绪拍点", "emotional_beat")
        closing_hook = _pick_field(dramatic_card, "章末钩子", "closing_hook")

        criteria = [
            f"本章功能必须成立：{result_change or packet.next_goal or '推进当前目标'}",
            "章节内必须出现结果变化，而不是只补背景。",
            f"章尾必须留出追读拉力：{closing_hook or '让下一步压力更具体'}。",
        ]
        if emotional_beat:
            criteria.append(f"读者情绪要能跟到这一下：{emotional_beat}")
        if must_advance:
            criteria.append(f"至少推进一条 open thread：{must_advance[0]}")
        if required_payoff_or_pressure:
            criteria.append(f"至少处理一个 payoff/pressure：{required_payoff_or_pressure[0]}")
        if packet.message_flow:
            criteria.append(f"消息传播不能违背既定链路：{packet.message_flow}")
        if packet.arrival_timing:
            criteria.append(f"消息到达时序必须成立：{packet.arrival_timing}")
        if packet.travel_time_floor:
            criteria.append(f"跨地行动不得压缩短于：{packet.travel_time_floor}")
        if packet.progress_ceiling:
            criteria.append(f"本章推进不得越过：{packet.progress_ceiling}")
        if packet.must_not_payoff_yet:
            criteria.append(f"本章禁止提前兑现：{packet.must_not_payoff_yet[0]}")
        if packet.allowed_change_scope:
            criteria.append(f"本章变化范围只允许：{'、'.join(packet.allowed_change_scope[:3])}")
        return _dedupe(criteria)

    def create_brief(self, packet: ChapterContextPacket) -> ChapterBrief:
        dramatic_card = self._load_dramatic_card(packet)
        must_advance = self._must_advance(packet)

        chapter_function = _pick_field(dramatic_card, "本章作用", "chapter_function") or packet.next_goal or "推进当前章节目标"
        hook_goal = _pick_field(dramatic_card, "章末钩子", "closing_hook") or "延续当前压力，并形成下一章牵引"
        result_change = _pick_field(dramatic_card, "结果变化", "result_change")
        emotional_beat = _pick_field(dramatic_card, "情绪拍点", "emotional_beat")
        core_conflict = _pick_field(dramatic_card, "核心冲突", "core_conflict")
        opening_image = _pick_field(dramatic_card, "开场画面", "opening_image")
        midpoint_collision = _pick_field(dramatic_card, "中段碰撞", "midpoint_collision")
        one_blade = _pick_field(dramatic_card, "一刀句", "one_blade")
        reader_experience_goal = _pick_field(dramatic_card, "读者体验目标", "reader_experience_goal")

        must_advance = _dedupe(([result_change] if result_change else []) + must_advance)
        required_payoff_or_pressure = self._required_payoff_or_pressure(packet, must_advance, dramatic_card)

        return ChapterBrief(
            chapter=packet.chapter,
            chapter_function=chapter_function,
            must_advance=must_advance,
            must_not_repeat=self._must_not_repeat(packet),
            hook_goal=hook_goal,
            allowed_threads=packet.open_threads,
            disallowed_moves=_dedupe(
                [
                    *packet.forbidden_inventions,
                    *(f"不要提前兑现：{item}" for item in packet.must_not_payoff_yet[:2]),
                    *(f"不要越过推进上限：{packet.progress_ceiling}" for _ in [0] if packet.progress_ceiling),
                ]
            ),
            progress_floor=packet.progress_floor,
            progress_ceiling=packet.progress_ceiling,
            must_not_payoff_yet=packet.must_not_payoff_yet,
            allowed_change_scope=packet.allowed_change_scope,
            voice_constraints=packet.voice_rules,
            required_payoff_or_pressure=required_payoff_or_pressure,
            scene_plan=self._scene_plan(packet, must_advance, required_payoff_or_pressure, dramatic_card),
            success_criteria=self._success_criteria(packet, must_advance, required_payoff_or_pressure, dramatic_card),
            reader_experience_goal=reader_experience_goal,
            core_conflict=core_conflict,
            emotional_beat=emotional_beat,
            opening_image=opening_image,
            midpoint_collision=midpoint_collision,
            result_change=result_change,
            closing_hook=hook_goal,
            one_blade=one_blade,
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
            progress_floor=previous_brief.progress_floor,
            progress_ceiling=previous_brief.progress_ceiling,
            must_not_payoff_yet=previous_brief.must_not_payoff_yet,
            allowed_change_scope=previous_brief.allowed_change_scope,
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
                    f"第 {attempt + 1} 轮重写先修 {blocking_dimensions[0]}，不要新开支线。",
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
            reader_experience_goal=previous_brief.reader_experience_goal,
            core_conflict=previous_brief.core_conflict,
            emotional_beat=previous_brief.emotional_beat,
            opening_image=previous_brief.opening_image,
            midpoint_collision=previous_brief.midpoint_collision,
            result_change=previous_brief.result_change,
            closing_hook=previous_brief.closing_hook,
            one_blade=previous_brief.one_blade,
        )
