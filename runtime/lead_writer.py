from __future__ import annotations

from runtime.contracts import ChapterBrief, ChapterContextPacket


class LeadWriter:
    def create_brief(self, packet: ChapterContextPacket) -> ChapterBrief:
        must_advance = packet.open_threads[:3]
        return ChapterBrief(
            chapter=packet.chapter,
            chapter_function=packet.next_goal or "推进当前章节目标",
            must_advance=must_advance,
            must_not_repeat=[],
            hook_goal="延续当前压力并形成下一章牵引",
            allowed_threads=packet.open_threads,
            disallowed_moves=packet.forbidden_inventions,
            voice_constraints=packet.voice_rules,
        )
