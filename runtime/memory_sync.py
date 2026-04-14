from __future__ import annotations

import json
from pathlib import Path

from runtime.contracts import ChapterBrief, ChapterContextPacket, EvaluatorVerdict, RuntimeDecision, RuntimeLoopResult
from scripts.aggregation_utils import safe_write_text, validate_project_root


class RuntimeMemorySync:
    def summarize(
        self,
        project_dir: Path,
        packet: ChapterContextPacket,
        brief: ChapterBrief,
        draft: dict[str, object],
        verdicts: list[EvaluatorVerdict],
        decision: RuntimeDecision,
        loop_results: list[RuntimeLoopResult] | None = None,
    ) -> dict[str, object]:
        validated_root = validate_project_root(project_dir)
        retrieval_dir = validated_root / "00_memory" / "retrieval"
        retrieval_dir.mkdir(parents=True, exist_ok=True)
        summary_path = retrieval_dir / "leadwriter_runtime_summary.md"
        json_path = retrieval_dir / "leadwriter_runtime_summary.json"
        warning_lines = packet.warnings or ["无"]
        verdict_lines = [
            f"- {item.dimension}: status={item.status} / blocking={'yes' if item.blocking else 'no'}"
            for item in verdicts
        ] or ["- 无"]
        rewrite_lines = (
            [f"- {item}" for item in (decision.rewrite_brief.must_change if decision.rewrite_brief else [])]
            if decision.decision == "revise"
            else ["- 无"]
        )
        loop_entries = loop_results or []
        loop_lines = [
            f"- iteration={item.iteration} / applied={'yes' if item.applied else 'no'} / source={item.source} / files={', '.join(item.updated_files) if item.updated_files else 'none'} / notes={'; '.join(item.notes) if item.notes else 'none'}"
            for item in loop_entries
        ] or ["- 无"]
        safe_write_text(
            summary_path,
            "\n".join(
                [
                    "# LeadWriter Runtime Summary",
                    "",
                    f"- chapter: {packet.chapter}",
                    f"- active_volume: {packet.active_volume}",
                    f"- active_arc: {packet.active_arc}",
                    f"- current_place: {packet.current_place}",
                    f"- chapter_function: {brief.chapter_function}",
                    f"- hook_goal: {brief.hook_goal}",
                    f"- draft_status: {draft.get('status', '')}",
                    f"- decision: {decision.decision}",
                    "",
                    "## Context warnings",
                    *[f"- {item}" for item in warning_lines],
                    "",
                    "## Evaluator verdicts",
                    *verdict_lines,
                    "",
                    "## Rewrite actions",
                    *rewrite_lines,
                    "",
                    "## Runtime loop",
                    *loop_lines,
                ]
            ) + "\n",
            root_dir=validated_root,
        )
        safe_write_text(
            json_path,
            json.dumps(
                {
                    "context": packet.to_dict(),
                    "brief": brief.to_dict(),
                    "draft": draft,
                    "verdicts": [item.to_dict() for item in verdicts],
                    "decision": decision.to_dict(),
                    "runtime_loop": [item.to_dict() for item in loop_entries],
                },
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            root_dir=validated_root,
        )
        return {"markdown": summary_path.as_posix(), "json": json_path.as_posix()}
