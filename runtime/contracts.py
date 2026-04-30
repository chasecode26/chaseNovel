from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

Status = Literal["pass", "warn", "fail"]
Decision = Literal["pass", "revise", "fail"]


@dataclass(frozen=True)
class ChapterContextPacket:
    project: str
    chapter: int
    active_volume: str
    active_arc: str
    time_anchor: str
    current_place: str
    location_anchor: str
    next_goal: str
    present_characters: list[str]
    knowledge_boundary: str
    message_flow: str
    arrival_timing: str
    who_knows_now: str
    who_cannot_know_yet: str
    travel_time_floor: str
    resource_state: str
    progress_floor: str
    progress_ceiling: str
    must_not_payoff_yet: list[str]
    allowed_change_scope: list[str]
    open_threads: list[str]
    forbidden_inventions: list[str]
    voice_rules: list[str]
    warnings: list[str] = field(default_factory=list)
    is_volume_start: bool = False
    is_volume_end: bool = False
    volume_name: str = ""
    volume_promises: list[str] = field(default_factory=list)
    volume_handoff: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ChapterBrief:
    chapter: int
    chapter_function: str
    must_advance: list[str]
    must_not_repeat: list[str]
    hook_goal: str
    allowed_threads: list[str]
    disallowed_moves: list[str]
    progress_floor: str
    progress_ceiling: str
    must_not_payoff_yet: list[str]
    allowed_change_scope: list[str]
    voice_constraints: list[str]
    required_payoff_or_pressure: list[str] = field(default_factory=list)
    scene_plan: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    reader_experience_goal: str = ""
    core_conflict: str = ""
    emotional_beat: str = ""
    opening_image: str = ""
    midpoint_collision: str = ""
    result_change: str = ""
    closing_hook: str = ""
    one_blade: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ChapterDirection:
    chapter: int
    chapter_function: str
    reader_experience_goal: str
    dramatic_question: str
    core_conflict: str
    opening_image: str
    midpoint_collision: str
    result_change: str
    closing_hook: str
    one_blade: str
    scene_density_plan: list[str] = field(default_factory=list)
    silence_points: list[str] = field(default_factory=list)
    explanation_bans: list[str] = field(default_factory=list)
    role_speaking_limits: list[str] = field(default_factory=list)
    emotional_curve: list[str] = field(default_factory=list)
    ending_drop_mode: str = ""
    writer_mission: list[str] = field(default_factory=list)
    hard_limits: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class EvaluatorVerdict:
    dimension: str
    status: Status
    blocking: bool
    evidence: list[str]
    why_it_breaks: str
    minimal_fix: str
    rewrite_scope: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RewriteBrief:
    return_to: str
    blocking_reasons: list[str]
    first_fix_priority: str
    rewrite_scope: str
    must_preserve: list[str]
    must_change: list[str]
    recheck_order: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeDecision:
    decision: Decision
    rewrite_brief: RewriteBrief | None
    blocking_dimensions: list[str]
    advisory_dimensions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        if self.rewrite_brief is None:
            payload["rewrite_brief"] = None
        return payload


@dataclass(frozen=True)
class MemoryPatch:
    schema_file: str
    before: dict[str, object]
    after: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
