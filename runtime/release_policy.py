from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from runtime.contracts import EvaluatorVerdict, RuntimeDecision
from runtime.agents.market_assets import compact_asset_lines, load_market_assets


MUST_PASS_DIMENSIONS = {
    "continuity",
    "causality",
    "character",
    "prose_concreteness",
    "promise_payoff",
    "story_logic",
    "hook_integrity",
    "scene_density",
    "continuity_guardrail",
    "market_fit",
    "pre_publish_checklist",
    "expectation_integrity",
    "opening_diagnostics",
    "genre_framework_fit",
}

REVISION_DIMENSIONS = {
    "dialogue",
    "hook_integrity",
    "scene_density",
    "chapter_progress",
    "pacing",
    "naturalness",
}


@dataclass(frozen=True)
class ReleasePolicyResult:
    final_release: str
    blocking_dimensions: list[str]
    advisory_dimensions: list[str]
    reasons: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class ReleasePolicy:
    """Converts agent/evaluator verdicts into a stable release gate."""

    def evaluate(self, decision: RuntimeDecision, verdicts: list[EvaluatorVerdict]) -> ReleasePolicyResult:
        blocking = [item for item in verdicts if item.blocking]
        advisory = [item for item in verdicts if not item.blocking and item.status == "warn"]
        reasons: list[str] = []

        if decision.decision == "fail":
            reasons.append("runtime decision 已进入 fail，不能放行。")
            return ReleasePolicyResult(
                final_release="fail",
                blocking_dimensions=decision.blocking_dimensions,
                advisory_dimensions=[item.dimension for item in advisory],
                reasons=reasons,
            )

        must_pass_blockers = [item.dimension for item in blocking if item.dimension in MUST_PASS_DIMENSIONS]
        if must_pass_blockers:
            reasons.append("关键维度未通过：" + ", ".join(must_pass_blockers))
            return ReleasePolicyResult(
                final_release="revise",
                blocking_dimensions=[item.dimension for item in blocking],
                advisory_dimensions=[item.dimension for item in advisory],
                reasons=reasons,
            )

        revision_blockers = [item.dimension for item in blocking if item.dimension in REVISION_DIMENSIONS]
        if revision_blockers:
            reasons.append("修订维度仍有阻断：" + ", ".join(revision_blockers))
            return ReleasePolicyResult(
                final_release="revise",
                blocking_dimensions=[item.dimension for item in blocking],
                advisory_dimensions=[item.dimension for item in advisory],
                reasons=reasons,
            )

        if blocking:
            reasons.append("存在未分类 blocking verdict：" + ", ".join(item.dimension for item in blocking))
            return ReleasePolicyResult(
                final_release="revise",
                blocking_dimensions=[item.dimension for item in blocking],
                advisory_dimensions=[item.dimension for item in advisory],
                reasons=reasons,
            )

        if advisory:
            reasons.append("允许带 warn 放行，但需进入后续修订观察队列。")
            return ReleasePolicyResult(
                final_release="warn",
                blocking_dimensions=[],
                advisory_dimensions=[item.dimension for item in advisory],
                reasons=reasons,
            )

        return ReleasePolicyResult(final_release="pass", blocking_dimensions=[], advisory_dimensions=[], reasons=["全部关键维度通过。"])


def write_release_gate_report(
    project_dir: Path,
    chapter: int,
    result: ReleasePolicyResult,
    verdicts: list[EvaluatorVerdict],
) -> dict[str, str]:
    gate_dir = project_dir / "04_gate" / f"ch{chapter:03d}"
    gate_dir.mkdir(parents=True, exist_ok=True)
    json_path = gate_dir / "release_gate_report.json"
    md_path = gate_dir / "release_gate_report.md"
    market_assets = load_market_assets(project_dir)
    checklist_lines = compact_asset_lines(market_assets.get("pre_publish_checklist", ""), limit=24)
    failed_dimensions = {item.dimension for item in verdicts if item.blocking}
    checklist_status = [
        {
            "item": item,
            "status": "blocked" if result.final_release in {"revise", "fail"} and failed_dimensions else "ready",
        }
        for item in checklist_lines
    ]
    payload = {
        "chapter": chapter,
        "release_policy": result.to_dict(),
        "verdicts": [item.to_dict() for item in verdicts],
        "must_rewrite": result.final_release in {"revise", "fail"},
        "release_allowed": result.final_release in {"pass", "warn"},
        "market_assets": {
            "platform_profile_loaded": bool(market_assets.get("platform_profile")),
            "prose_examples_loaded": bool(market_assets.get("prose_examples")),
            "pre_publish_checklist_loaded": bool(market_assets.get("pre_publish_checklist")),
        },
        "pre_publish_checklist": checklist_status,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Release Gate Report",
        "",
        f"- chapter: {chapter}",
        f"- final_release: {result.final_release}",
        f"- release_allowed: {'yes' if payload['release_allowed'] else 'no'}",
        f"- must_rewrite: {'yes' if payload['must_rewrite'] else 'no'}",
        f"- platform_profile_loaded: {'yes' if payload['market_assets']['platform_profile_loaded'] else 'no'}",
        f"- pre_publish_checklist_loaded: {'yes' if payload['market_assets']['pre_publish_checklist_loaded'] else 'no'}",
        f"- blocking_dimensions: {', '.join(result.blocking_dimensions) or 'none'}",
        f"- advisory_dimensions: {', '.join(result.advisory_dimensions) or 'none'}",
        "",
        "## Reasons",
    ]
    lines.extend(f"- {item}" for item in result.reasons or ["none"])
    lines.extend(["", "## Verdict Summary"])
    for verdict in verdicts:
        lines.append(
            f"- {verdict.dimension}: status={verdict.status}, blocking={'yes' if verdict.blocking else 'no'}, scope={verdict.rewrite_scope or 'none'}"
        )
    lines.extend(["", "## Pre Publish Checklist"])
    if checklist_status:
        lines.extend(f"- [{item['status']}] {item['item']}" for item in checklist_status)
    else:
        lines.append("- missing checklist asset")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"release_gate_report_json": json_path.as_posix(), "release_gate_report_markdown": md_path.as_posix()}
