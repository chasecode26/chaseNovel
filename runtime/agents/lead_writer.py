from __future__ import annotations

import json
from pathlib import Path

from runtime.contracts import ChapterBrief, ChapterContextPacket, EvaluatorVerdict, RuntimeDecision
from runtime.lead_writer import LeadWriter
from runtime.agents.prompt_loader import load_agent_prompt, write_agent_prompt_snapshot


class LeadWriterAgent:
    """Owns chapter intent: goal, conflict, result, hook, and boundaries."""

    name = "LeadWriterAgent"

    def __init__(self, lead_writer: LeadWriter | None = None) -> None:
        self._lead_writer = lead_writer or LeadWriter()

    def create_brief(self, project_dir: Path, packet: ChapterContextPacket) -> tuple[ChapterBrief, dict[str, str]]:
        prompt = load_agent_prompt("lead-writer-agent")
        prompt_path = write_agent_prompt_snapshot(project_dir, packet.chapter, "lead-writer-agent", prompt)
        brief = self._lead_writer.create_brief(packet)
        return brief, self._write_report(project_dir, packet.chapter, brief, prompt_path, mode="create")

    def revise_brief(
        self,
        project_dir: Path,
        packet: ChapterContextPacket,
        previous_brief: ChapterBrief,
        decision: RuntimeDecision,
        verdicts: list[EvaluatorVerdict],
        *,
        attempt: int,
    ) -> tuple[ChapterBrief, dict[str, str]]:
        prompt = load_agent_prompt("lead-writer-agent")
        prompt_path = write_agent_prompt_snapshot(project_dir, previous_brief.chapter, "lead-writer-agent", prompt)
        brief = self._lead_writer.revise_brief(packet, previous_brief, decision, verdicts, attempt=attempt)
        return brief, self._write_report(project_dir, previous_brief.chapter, brief, prompt_path, mode="revise")

    def _write_report(self, project_dir: Path, chapter: int, brief: ChapterBrief, prompt_path: str, *, mode: str) -> dict[str, str]:
        gate_dir = project_dir / "04_gate" / f"ch{chapter:03d}"
        gate_dir.mkdir(parents=True, exist_ok=True)
        json_path = gate_dir / "lead_writer_agent_report.json"
        md_path = gate_dir / "lead_writer_agent_report.md"
        checks = {
            "has_goal": bool(brief.chapter_function.strip()),
            "has_conflict": bool(brief.core_conflict.strip() or brief.required_payoff_or_pressure),
            "has_result": bool(brief.result_change.strip() or brief.must_advance),
            "has_hook": bool(brief.closing_hook.strip() or brief.hook_goal.strip()),
            "has_boundaries": bool(brief.disallowed_moves or brief.must_not_payoff_yet or brief.progress_ceiling),
            "has_character_pressure": bool(brief.voice_constraints or brief.emotional_beat),
            "has_short_expectation": bool(brief.core_conflict.strip() or brief.hook_goal.strip()),
            "has_long_expectation": bool(brief.allowed_threads or brief.required_payoff_or_pressure or brief.must_not_payoff_yet),
            "has_genre_promise": bool(brief.reader_experience_goal.strip() or brief.chapter_function.strip()),
            "opening_ready": bool(brief.opening_image.strip() or brief.core_conflict.strip()),
        }
        payload = {
            "agent": self.name,
            "mode": mode,
            "chapter": chapter,
            "prompt_path": prompt_path,
            "brief": brief.to_dict(),
            "quality_checks": checks,
            "ready_for_director": all(checks.values()),
        }
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        lines = [
            "# LeadWriterAgent Report",
            "",
            f"- mode: {mode}",
            f"- chapter: {chapter}",
            f"- ready_for_director: {'yes' if payload['ready_for_director'] else 'no'}",
            f"- prompt: {prompt_path or 'missing'}",
            "",
            "## Quality Checks",
        ]
        lines.extend(f"- {key}: {'yes' if value else 'no'}" for key, value in checks.items())
        lines.extend(
            [
                "",
                "## Chapter Intent",
                f"- goal: {brief.chapter_function or 'missing'}",
                f"- conflict: {brief.core_conflict or (brief.required_payoff_or_pressure[0] if brief.required_payoff_or_pressure else 'missing')}",
                f"- result: {brief.result_change or (brief.must_advance[0] if brief.must_advance else 'missing')}",
                f"- hook: {brief.closing_hook or brief.hook_goal or 'missing'}",
                f"- short_expectation: {brief.core_conflict or brief.hook_goal or 'missing'}",
                f"- long_expectation: {(brief.allowed_threads[0] if brief.allowed_threads else (brief.must_not_payoff_yet[0] if brief.must_not_payoff_yet else 'missing'))}",
                f"- genre_promise: {brief.reader_experience_goal or brief.chapter_function or 'missing'}",
            ]
        )
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {"lead_writer_agent_report_json": json_path.as_posix(), "lead_writer_agent_report_markdown": md_path.as_posix()}
