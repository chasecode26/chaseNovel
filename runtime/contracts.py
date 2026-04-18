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
    current_place: str
    next_goal: str
    open_threads: list[str]
    forbidden_inventions: list[str]
    voice_rules: list[str]
    warnings: list[str] = field(default_factory=list)

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
    voice_constraints: list[str]

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
