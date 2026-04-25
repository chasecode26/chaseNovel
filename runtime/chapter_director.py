from __future__ import annotations

from pathlib import Path

from runtime.contracts import ChapterBrief, ChapterContextPacket, ChapterDirection


def _clean(text: str) -> str:
    return text.strip().strip("。！？；;,.， ")


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in values:
        text = item.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


class ChapterDirector:
    """把章级 brief 转成“怎么打这一章”的导演单。

    第一版只做轻量、确定性的导演决策：
    - 不读取 evaluator / anti-AI / quality 报告
    - 不直接写正文
    - 只输出 Writer 需要优先执行的节奏、禁解释、章尾落法
    """

    def direct(
        self,
        packet: ChapterContextPacket,
        brief: ChapterBrief,
        *,
        project_dir: Path,
    ) -> ChapterDirection:
        del project_dir  # 第一版不读取额外文件，避免把 Director 变成新型检索入口。

        core_conflict = brief.core_conflict.strip() or self._derive_core_conflict(packet, brief)
        result_change = brief.result_change.strip() or self._derive_result_change(packet, brief)
        closing_hook = brief.closing_hook.strip() or brief.hook_goal.strip()
        one_blade = brief.one_blade.strip() or self._derive_one_blade(closing_hook, core_conflict)

        return ChapterDirection(
            chapter=brief.chapter,
            chapter_function=brief.chapter_function,
            reader_experience_goal=brief.reader_experience_goal.strip() or self._derive_reader_experience_goal(packet, brief),
            dramatic_question=self._dramatic_question(packet, brief, core_conflict, result_change),
            core_conflict=core_conflict,
            opening_image=brief.opening_image.strip(),
            midpoint_collision=brief.midpoint_collision.strip(),
            result_change=result_change,
            closing_hook=closing_hook,
            one_blade=one_blade,
            scene_density_plan=self._scene_density_plan(brief),
            silence_points=self._silence_points(brief),
            explanation_bans=self._explanation_bans(brief),
            role_speaking_limits=self._role_speaking_limits(brief),
            emotional_curve=self._emotional_curve(brief),
            ending_drop_mode=self._ending_drop_mode(brief),
            writer_mission=self._writer_mission(brief, result_change, closing_hook),
            hard_limits=self._hard_limits(packet, brief),
        )

    def _derive_reader_experience_goal(self, packet: ChapterContextPacket, brief: ChapterBrief) -> str:
        if packet.must_not_payoff_yet or brief.must_not_payoff_yet:
            return "紧中带悬"
        if brief.result_change:
            return "压住后给出一寸结果"
        return "清楚、紧凑、有推进"

    def _derive_core_conflict(self, packet: ChapterContextPacket, brief: ChapterBrief) -> str:
        if packet.open_threads:
            return f"{packet.open_threads[0]}不能只停在口头上"
        if brief.must_advance:
            return f"{brief.must_advance[0]}必须被逼出可见结果"
        return brief.chapter_function or packet.next_goal or "这一章必须有真实推进"

    def _derive_result_change(self, packet: ChapterContextPacket, brief: ChapterBrief) -> str:
        if brief.must_advance:
            return brief.must_advance[0]
        if packet.progress_floor:
            return packet.progress_floor
        return brief.chapter_function or packet.next_goal or "局面往前偏了一寸"

    def _derive_one_blade(self, closing_hook: str, core_conflict: str) -> str:
        source = _clean(closing_hook or core_conflict)
        source = (
            source.replace("必须", "")
            .replace("需要", "")
            .replace("应该", "")
            .strip(" ，,。")
        )
        if not source:
            return "这一步还不能松。"
        if len(source) <= 18:
            return source if source.endswith("。") else f"{source}。"
        return "这一步还不能松。"

    def _dramatic_question(
        self,
        packet: ChapterContextPacket,
        brief: ChapterBrief,
        core_conflict: str,
        result_change: str,
    ) -> str:
        if result_change and core_conflict:
            return f"主角能不能在{core_conflict}的压力下，抢到{result_change}？"
        if packet.next_goal:
            return f"这一章能不能把{packet.next_goal}落成可见变化？"
        return f"这一章能不能让{brief.chapter_function or '当前目标'}真正往前动？"

    def _scene_density_plan(self, brief: ChapterBrief) -> list[str]:
        if brief.opening_image or brief.midpoint_collision or brief.result_change or brief.closing_hook:
            return [
                "scene1: short-tight",
                "scene2: dense-collision",
                "scene3: heavy-slow",
                "scene4: short-blade",
            ]
        return [
            "scene1: clear-entry",
            "scene2: pressure-build",
            "scene3: visible-result",
            "scene4: next-pull",
        ]

    def _silence_points(self, brief: ChapterBrief) -> list[str]:
        points = ["scene3-after-cost", "scene4-before-final-blade"]
        if brief.midpoint_collision:
            points.insert(0, "scene2-after-warning")
        return points

    def _explanation_bans(self, brief: ChapterBrief) -> list[str]:
        bans = [
            "不要解释这场戏的意义，让结果自己压出来",
            "不要旁白总结主角成长",
            "不要用分析词替代动作、站位和后果",
        ]
        if brief.one_blade:
            bans.append("章尾一刀后不要再补解释")
        return bans

    def _role_speaking_limits(self, brief: ChapterBrief) -> list[str]:
        limits = ["主角不准把底牌说满", "对手不准自曝真实目的"]
        if brief.core_conflict:
            limits.append("配角只能补压，不准替作者讲解局势")
        return limits

    def _emotional_curve(self, brief: ChapterBrief) -> list[str]:
        if brief.emotional_beat:
            return ["压气", "顶撞", "刺痛", "收刀"]
        return ["入场", "施压", "推进", "留门"]

    def _ending_drop_mode(self, brief: ChapterBrief) -> str:
        if brief.one_blade:
            return "short_blade"
        if brief.closing_hook:
            return "open_pressure"
        return "next_pull"

    def _writer_mission(self, brief: ChapterBrief, result_change: str, closing_hook: str) -> list[str]:
        missions = [
            "先写场面，再写谁在施压，不要先讲道理",
            "对话必须承担试探、回顶、压制或自保，不做设定说明",
            f"结果变化必须落地：{result_change}",
        ]
        if closing_hook:
            missions.append(f"章尾必须把下一步门打开：{closing_hook}")
        if brief.one_blade:
            missions.append(f"最后一刀优先保留：{brief.one_blade}")
        return _dedupe(missions)

    def _hard_limits(self, packet: ChapterContextPacket, brief: ChapterBrief) -> list[str]:
        limits = [
            *(f"不要提前兑现：{item}" for item in brief.must_not_payoff_yet),
            *(f"禁止新增：{item}" for item in brief.disallowed_moves),
            *(f"变化范围只允许：{item}" for item in brief.allowed_change_scope),
        ]
        if packet.progress_ceiling:
            limits.append(f"推进不得越过：{packet.progress_ceiling}")
        if packet.who_cannot_know_yet:
            limits.append(f"不可提前知情：{packet.who_cannot_know_yet}")
        return _dedupe(limits)
