from __future__ import annotations

import json
from pathlib import Path

from runtime.chapter_director import ChapterDirector
from runtime.contracts import ChapterBrief, ChapterContextPacket, ChapterDirection
from runtime.agents.prompt_loader import load_agent_prompt, write_agent_prompt_snapshot


class DirectorAgent:
    """Owns staging: rhythm, pressure, scene order, and ending drop."""

    name = "DirectorAgent"

    def __init__(self, director: ChapterDirector | None = None) -> None:
        self._director = director or ChapterDirector()

    def direct(self, project_dir: Path, packet: ChapterContextPacket, brief: ChapterBrief) -> tuple[ChapterDirection, dict[str, str]]:
        prompt = load_agent_prompt("director-agent")
        prompt_path = write_agent_prompt_snapshot(project_dir, brief.chapter, "director-agent", prompt)
        direction = self._director.direct(packet, brief, project_dir=project_dir)
        return direction, self._write_report(project_dir, brief.chapter, direction, prompt_path)

    def _write_report(self, project_dir: Path, chapter: int, direction: ChapterDirection, prompt_path: str) -> dict[str, str]:
        gate_dir = project_dir / "04_gate" / f"ch{chapter:03d}"
        gate_dir.mkdir(parents=True, exist_ok=True)
        json_path = gate_dir / "director_agent_report.json"
        md_path = gate_dir / "director_agent_report.md"
        checks = {
            "has_dramatic_question": bool(direction.dramatic_question.strip()),
            "has_emotional_curve": bool(direction.emotional_curve),
            "has_scene_density_plan": bool(direction.scene_density_plan),
            "has_writer_mission": bool(direction.writer_mission),
            "has_ending_mode": bool(direction.ending_drop_mode.strip()),
            "has_explanation_bans": bool(direction.explanation_bans),
            "has_expectation_staging": bool(direction.closing_hook.strip() and direction.result_change.strip()),
            "has_opening_pressure": bool(direction.opening_image.strip() or direction.core_conflict.strip()),
            "has_genre_promise_staging": bool(direction.reader_experience_goal.strip() or direction.writer_mission),
        }
        payload = {
            "agent": self.name,
            "chapter": chapter,
            "prompt_path": prompt_path,
            "direction": direction.to_dict(),
            "quality_checks": checks,
            "ready_for_scene_beats": all(checks.values()),
        }
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        lines = [
            "# DirectorAgent Report",
            "",
            f"- chapter: {chapter}",
            f"- ready_for_scene_beats: {'yes' if payload['ready_for_scene_beats'] else 'no'}",
            f"- prompt: {prompt_path or 'missing'}",
            "",
            "## Quality Checks",
        ]
        lines.extend(f"- {key}: {'yes' if value else 'no'}" for key, value in checks.items())
        lines.extend(
            [
                "",
                "## Direction",
                f"- dramatic_question: {direction.dramatic_question or 'missing'}",
                f"- core_conflict: {direction.core_conflict or 'missing'}",
                f"- result_change: {direction.result_change or 'missing'}",
                f"- closing_hook: {direction.closing_hook or 'missing'}",
                f"- ending_drop_mode: {direction.ending_drop_mode or 'missing'}",
                f"- expectation_staging: result={direction.result_change or 'missing'} / new_pull={direction.closing_hook or 'missing'}",
                f"- genre_promise_staging: {direction.reader_experience_goal or (direction.writer_mission[0] if direction.writer_mission else 'missing')}",
            ]
        )
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {"director_agent_report_json": json_path.as_posix(), "director_agent_report_markdown": md_path.as_posix()}
