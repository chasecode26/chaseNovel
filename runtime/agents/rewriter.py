from __future__ import annotations

from pathlib import Path

from runtime.contracts import ChapterBrief, ChapterContextPacket, ChapterDirection, RuntimeDecision
from runtime.agents.handoff import write_rewriter_handoff
from runtime.agents.local_rewrite import merge_by_scope, write_rewrite_operation
from runtime.agents.model_gateway import LocalDeterministicGateway, ModelGateway, ModelRequest, write_model_trace
from runtime.agents.prompt_loader import load_agent_prompt, write_agent_prompt_snapshot
from runtime.agents.writer_executor import WriterExecutor


class RewriterAgent:
    """Applies a RewriteBrief through the same manuscript executor, scoped by decision."""

    name = "RewriterAgent"

    def __init__(self, executor: WriterExecutor | None = None, gateway: ModelGateway | None = None) -> None:
        self._executor = executor or WriterExecutor()
        self._gateway = gateway or LocalDeterministicGateway()

    def rewrite(
        self,
        project_dir: Path,
        packet: ChapterContextPacket,
        brief: ChapterBrief,
        decision: RuntimeDecision,
        *,
        direction: ChapterDirection | None = None,
        dry_run: bool = False,
    ) -> dict[str, object]:
        agent_prompt = load_agent_prompt("rewriter-agent")
        agent_prompt_path = write_agent_prompt_snapshot(project_dir, brief.chapter, "rewriter-agent", agent_prompt)
        rewrite_brief = decision.rewrite_brief
        manuscript_path = project_dir / "04_gate" / f"ch{brief.chapter:03d}" / "reader_manuscript.md"
        original_text = manuscript_path.read_text(encoding="utf-8") if manuscript_path.exists() else ""
        original_snapshot_path = ""
        if original_text.strip():
            original_snapshot = project_dir / "04_gate" / f"ch{brief.chapter:03d}" / "reader_manuscript.before_rewrite.md"
            original_snapshot.write_text(original_text, encoding="utf-8")
            original_snapshot_path = original_snapshot.as_posix()
        model_response = self._gateway.complete(
            ModelRequest(
                agent=self.name,
                task="rewrite",
                prompt=agent_prompt,
                context={
                    "chapter": brief.chapter,
                    "brief": brief.to_dict(),
                    "direction": {} if direction is None else direction.to_dict(),
                    "rewrite_brief": {} if rewrite_brief is None else rewrite_brief.to_dict(),
                },
                temperature=0.45,
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
            scene_beat_plan=None,
        )
        rewritten_path = Path(str(payload.get("manuscript_path", "")).strip())
        rewrite_operation_path = ""
        if original_text.strip() and rewritten_path.exists() and rewrite_brief is not None:
            rewritten_text = rewritten_path.read_text(encoding="utf-8")
            merged_text, operation = merge_by_scope(original_text, rewritten_text, rewrite_brief.rewrite_scope)
            rewritten_path.write_text(merged_text, encoding="utf-8")
            rewrite_operation_path = write_rewrite_operation(project_dir, brief.chapter, operation)
            payload = {
                **payload,
                "manuscript_preview": "\n".join(merged_text.splitlines()[:12]),
                "word_count": len("".join(merged_text.splitlines())),
            }
        handoff_paths = write_rewriter_handoff(
            project_dir,
            brief.chapter,
            rewrite_brief={} if rewrite_brief is None else rewrite_brief.to_dict(),
            draft_payload={
                **payload,
                "original_manuscript_snapshot_path": original_snapshot_path,
                "rewrite_operation_path": rewrite_operation_path,
            },
            paths={
                "agent_prompt_path": agent_prompt_path,
                "model_trace_path": model_trace_path,
            },
        )
        return {
            **payload,
            "agent": self.name,
            "agent_role": "rewrite",
            "agent_prompt_path": agent_prompt_path,
            "agent_prompt_preview": "\n".join(agent_prompt.splitlines()[:10]),
            "model_trace_path": model_trace_path,
            "model_response": model_response.to_dict(),
            "original_manuscript_snapshot_path": original_snapshot_path,
            "rewrite_operation_path": rewrite_operation_path,
            "rewrite_scope": "" if rewrite_brief is None else rewrite_brief.rewrite_scope,
            "rewrite_priority": "" if rewrite_brief is None else rewrite_brief.first_fix_priority,
            **handoff_paths,
        }
