from __future__ import annotations

import json
from pathlib import Path

from runtime.contracts import ChapterBrief, ChapterContextPacket, ChapterDirection
from runtime.agents.prompt_loader import load_agent_prompt, write_agent_prompt_snapshot
from runtime.agents.scene_beat_planner import SceneBeatPlan, SceneBeatPlanner, write_scene_beat_plan


class SceneBeatAgent:
    """Owns concrete beats and keeps the chapter human, market-facing, and playable."""

    name = "SceneBeatAgent"

    def __init__(self, planner: SceneBeatPlanner | None = None) -> None:
        self._planner = planner or SceneBeatPlanner()

    def plan(
        self,
        project_dir: Path,
        packet: ChapterContextPacket,
        brief: ChapterBrief,
        direction: ChapterDirection | None,
    ) -> tuple[SceneBeatPlan, dict[str, str]]:
        prompt = load_agent_prompt("scene-beat-agent")
        prompt_path = write_agent_prompt_snapshot(project_dir, brief.chapter, "scene-beat-agent", prompt)
        plan = self._planner.plan(packet, brief, direction)
        paths = write_scene_beat_plan(project_dir, plan)
        return plan, {**paths, **self._write_report(project_dir, brief.chapter, plan, prompt_path)}

    def _write_report(self, project_dir: Path, chapter: int, plan: SceneBeatPlan, prompt_path: str) -> dict[str, str]:
        gate_dir = project_dir / "04_gate" / f"ch{chapter:03d}"
        gate_dir.mkdir(parents=True, exist_ok=True)
        json_path = gate_dir / "scene_beat_agent_report.json"
        md_path = gate_dir / "scene_beat_agent_report.md"
        checks = {
            "has_three_or_more_beats": len(plan.beats) >= 3,
            "all_have_collision": all(bool(item.first_collision.strip()) for item in plan.beats),
            "all_have_cost": all(bool(item.cost.strip()) for item in plan.beats),
            "all_have_next_pull": all(bool(item.next_pull.strip()) for item in plan.beats),
            "all_have_human_language_rule": all(bool(item.human_language_rule.strip()) for item in plan.beats),
            "all_have_market_hook": all(bool(item.market_reader_hook.strip()) for item in plan.beats),
            "all_have_setting_guardrail": all(bool(item.setting_guardrail.strip()) for item in plan.beats),
            "all_have_timeline_guardrail": all(bool(item.timeline_guardrail.strip()) for item in plan.beats),
            "all_have_short_expectation": all(bool(item.short_expectation.strip()) for item in plan.beats),
            "all_have_long_expectation": all(bool(item.long_expectation.strip()) for item in plan.beats),
            "all_have_new_expectation": all(bool(item.new_expectation.strip()) for item in plan.beats),
            "all_have_expectation_gap_risk": all(bool(item.expectation_gap_risk.strip()) for item in plan.beats),
            "all_have_genre_framework_hint": all(bool(item.genre_framework_hint.strip()) for item in plan.beats),
        }
        payload = {
            "agent": self.name,
            "chapter": chapter,
            "prompt_path": prompt_path,
            "scene_beat_plan": plan.to_dict(),
            "quality_checks": checks,
            "ready_for_writer": all(checks.values()),
        }
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        lines = [
            "# SceneBeatAgent Report",
            "",
            f"- chapter: {chapter}",
            f"- ready_for_writer: {'yes' if payload['ready_for_writer'] else 'no'}",
            f"- prompt: {prompt_path or 'missing'}",
            "",
            "## Quality Checks",
        ]
        lines.extend(f"- {key}: {'yes' if value else 'no'}" for key, value in checks.items())
        lines.extend(["", "## Beat Summary"])
        for beat in plan.beats:
            lines.extend(
                [
                    f"### Beat {beat.index}",
                    f"- goal: {beat.scene_goal}",
                    f"- collision: {beat.first_collision}",
                    f"- cost: {beat.cost}",
                    f"- next_pull: {beat.next_pull}",
                    f"- human_language_rule: {beat.human_language_rule}",
                    f"- market_reader_hook: {beat.market_reader_hook}",
                    f"- short_expectation: {beat.short_expectation}",
                    f"- long_expectation: {beat.long_expectation}",
                    f"- new_expectation: {beat.new_expectation}",
                    f"- expectation_gap_risk: {beat.expectation_gap_risk}",
                    f"- genre_framework_hint: {beat.genre_framework_hint}",
                ]
            )
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {"scene_beat_agent_report_json": json_path.as_posix(), "scene_beat_agent_report_markdown": md_path.as_posix()}
