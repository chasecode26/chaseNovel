from __future__ import annotations

from runtime.contracts import EvaluatorVerdict, RewriteBrief, RuntimeDecision

CORE_PRIORITY = [
    "continuity",
    "causality",
    "promise_payoff",
    "repeat",
    "pacing",
    "style",
    "dialogue",
]

EXTENDED_PRIORITY = [
    *CORE_PRIORITY,
    "character",
    "foreshadow",
    "arc",
]


class DecisionEngine:
    def decide(self, verdicts: list[EvaluatorVerdict]) -> RuntimeDecision:
        blocking = [item for item in verdicts if item.blocking]
        advisory = [item for item in verdicts if not item.blocking and item.status == "warn"]
        if not blocking:
            return RuntimeDecision(
                decision="pass",
                rewrite_brief=None,
                blocking_dimensions=[],
                advisory_dimensions=[item.dimension for item in advisory],
            )

        blocking.sort(
            key=lambda item: (
                EXTENDED_PRIORITY.index(item.dimension) if item.dimension in EXTENDED_PRIORITY else len(EXTENDED_PRIORITY)
            )
        )
        primary = blocking[0]
        rewrite_brief = RewriteBrief(
            return_to="LeadWriter + WriterExecutor",
            blocking_reasons=[item.why_it_breaks for item in blocking],
            first_fix_priority=primary.dimension,
            rewrite_scope=primary.rewrite_scope,
            must_preserve=[],
            must_change=[item.minimal_fix for item in blocking],
            recheck_order=[item.dimension for item in blocking],
        )
        return RuntimeDecision(
            decision="revise",
            rewrite_brief=rewrite_brief,
            blocking_dimensions=[item.dimension for item in blocking],
            advisory_dimensions=[item.dimension for item in advisory],
        )
