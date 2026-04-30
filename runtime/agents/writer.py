from __future__ import annotations

from pathlib import Path

from runtime.contracts import ChapterBrief, ChapterContextPacket, ChapterDirection, RuntimeDecision
from runtime.agents.handoff import write_writer_handoff
from runtime.agents.market_assets import load_market_assets
from runtime.agents.model_gateway import LocalDeterministicGateway, ModelGateway, ModelRequest, write_model_trace
from runtime.agents.prompt_loader import load_agent_prompt, write_agent_prompt_snapshot
from runtime.agents.scene_beat_planner import SceneBeatPlanner, write_scene_beat_plan
from runtime.agents.writer_executor import WriterExecutor


class WriterAgent:
    """Turns a chapter brief into the first manuscript draft."""

    name = "WriterAgent"

    def __init__(self, executor: WriterExecutor | None = None, gateway: ModelGateway | None = None) -> None:
        self._executor = executor or WriterExecutor()
        self._gateway = gateway or LocalDeterministicGateway()

    def draft(
        self,
        project_dir: Path,
        packet: ChapterContextPacket,
        brief: ChapterBrief,
        decision: RuntimeDecision,
        *,
        direction: ChapterDirection | None = None,
        scene_beat_plan: dict[str, object] | None = None,
        scene_beat_paths: dict[str, str] | None = None,
        dry_run: bool = False,
    ) -> dict[str, object]:
        agent_prompt = load_agent_prompt("writer-agent")
        market_assets = load_market_assets(project_dir)
        agent_prompt_path = write_agent_prompt_snapshot(project_dir, brief.chapter, "writer-agent", agent_prompt)
        if scene_beat_plan is None:
            planned = SceneBeatPlanner().plan(packet, brief, direction)
            scene_beat_plan = planned.to_dict()
            scene_beat_paths = write_scene_beat_plan(project_dir, planned)
        else:
            scene_beat_paths = scene_beat_paths or {}
        model_response = self._gateway.complete(
            ModelRequest(
                agent=self.name,
                task="draft",
                prompt=agent_prompt,
                context={
                    "chapter": brief.chapter,
                    "brief": brief.to_dict(),
                    "direction": {} if direction is None else direction.to_dict(),
                    "scene_beat_plan": scene_beat_plan,
                    "market_assets": market_assets,
                },
            )
        )
        model_trace_path = write_model_trace(project_dir, brief.chapter, model_response)
        payload = self._executor.draft(
            project_dir,
            packet,
            brief,
            decision,
            direction=direction,
            dry_run=dry_run,
            scene_beat_plan=scene_beat_plan,
        )
        paths = {
            "writer_prompt_path": str(payload.get("writer_prompt_path", "")),
            "manuscript_path": str(payload.get("manuscript_path", "")),
            "review_notes_path": str(payload.get("review_notes_path", "")),
            **scene_beat_paths,
        }
        handoff_paths = write_writer_handoff(
            project_dir,
            brief.chapter,
            brief=brief.to_dict(),
            direction={} if direction is None else direction.to_dict(),
            scene_beat_plan=scene_beat_plan,
            paths=paths,
            market_assets=market_assets,
        )
        return {
            **payload,
            "agent": self.name,
            "agent_role": "draft",
            "agent_prompt_path": agent_prompt_path,
            "agent_prompt_preview": "\n".join(agent_prompt.splitlines()[:10]),
            "scene_beat_plan": scene_beat_plan,
            **scene_beat_paths,
            "model_trace_path": model_trace_path,
            "model_response": model_response.to_dict(),
            **handoff_paths,
        }
