from __future__ import annotations

import json
from pathlib import Path

from runtime.script_imports import ensure_scripts_on_path

ensure_scripts_on_path()

from evaluators.character import from_runtime_draft
from evaluators.causality import from_runtime_output as from_causality_runtime_output
from evaluators.chapter_progress import from_runtime_output as from_chapter_progress_runtime_output
from evaluators.dialogue import from_runtime_output as from_dialogue_runtime_output
from evaluators.pacing import from_runtime_output as from_pacing_runtime_output
from evaluators.promise_payoff import from_runtime_output as from_promise_payoff_runtime_output
from novel_utils import derive_plan_target_words, read_text
from runtime.agents import DirectorAgent, LeadWriterAgent, ReviewerAgent, RewriterAgent, SceneBeatAgent, WriterAgent
from runtime.contracts import ChapterBrief, ChapterContextPacket, ChapterDirection, EvaluatorVerdict, RuntimeDecision
from runtime.decision_engine import DecisionEngine
from runtime.memory_compiler import MemoryCompiler
from runtime.memory_sync import RuntimeMemorySync
from runtime.quality_service import RuntimeQualityService
from runtime.release_policy import ReleasePolicy, write_release_gate_report


class LeadWriterRuntime:
    def __init__(self, quality_service: RuntimeQualityService | None = None) -> None:
        self._quality_service = quality_service or RuntimeQualityService()

    def _coerce_verdict(self, payload: dict[str, object]) -> EvaluatorVerdict:
        return EvaluatorVerdict(
            dimension=str(payload.get("dimension", "unknown")),
            status=str(payload.get("status", "pass")),
            blocking=bool(payload.get("blocking", False)),
            evidence=[str(item) for item in payload.get("evidence", []) if str(item).strip()],
            why_it_breaks=str(payload.get("why_it_breaks", "")).strip(),
            minimal_fix=str(payload.get("minimal_fix", "")).strip(),
            rewrite_scope=str(payload.get("rewrite_scope", "")).strip(),
        )

    def _build_verdicts(self, project_dir: Path, chapter: int) -> tuple[list[EvaluatorVerdict], list[str]]:
        return self._quality_service.collect_runtime_verdicts(project_dir, chapter)

    def _write_postdraft_report(self, project_dir: Path, verdict: EvaluatorVerdict | None) -> dict[str, str]:
        if verdict is None:
            return {}
        retrieval_dir = project_dir / "00_memory" / "retrieval"
        retrieval_dir.mkdir(parents=True, exist_ok=True)
        json_path = retrieval_dir / "leadwriter_character_verdict.json"
        md_path = retrieval_dir / "leadwriter_character_verdict.md"
        payload = verdict.to_dict()
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        lines = [
            "# LeadWriter Character Verdict",
            "",
            f"- status: {payload['status']}",
            f"- blocking: {'yes' if payload['blocking'] else 'no'}",
            f"- dimension: {payload['dimension']}",
            f"- rewrite_scope: {payload['rewrite_scope']}",
            "",
            "## Evidence",
        ]
        evidence = payload.get("evidence", [])
        if isinstance(evidence, list) and evidence:
            lines.extend(f"- {item}" for item in evidence)
        else:
            lines.append("- none")
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {"character_verdict_json": json_path.as_posix(), "character_verdict_markdown": md_path.as_posix()}

    def _write_runtime_payload(self, project_dir: Path, payload: dict[str, object]) -> dict[str, str]:
        retrieval_dir = project_dir / "00_memory" / "retrieval"
        retrieval_dir.mkdir(parents=True, exist_ok=True)
        json_path = retrieval_dir / "leadwriter_runtime_payload.json"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return {"runtime_payload_json": json_path.as_posix()}

    def _write_agent_replay_report(self, project_dir: Path, payload: dict[str, object]) -> dict[str, str]:
        chapter = int(payload.get("chapter", 0) or 0)
        report_dir = project_dir / "04_gate" / f"ch{chapter:03d}"
        report_dir.mkdir(parents=True, exist_ok=True)
        json_path = report_dir / "agent_replay_report.json"
        md_path = report_dir / "agent_replay_report.md"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        release_policy = payload.get("release_policy", {})
        release_policy = release_policy if isinstance(release_policy, dict) else {}
        lines = [
            "# Agent Replay Report",
            "",
            f"- chapter: {chapter}",
            f"- final_release: {payload.get('final_release', 'unknown')}",
            f"- blocking_dimensions: {', '.join(release_policy.get('blocking_dimensions', [])) if isinstance(release_policy.get('blocking_dimensions', []), list) else 'unknown'}",
            f"- advisory_dimensions: {', '.join(release_policy.get('advisory_dimensions', [])) if isinstance(release_policy.get('advisory_dimensions', []), list) else 'unknown'}",
            "",
            "## Cycles",
        ]
        for cycle in payload.get("cycles", []):
            if not isinstance(cycle, dict):
                continue
            decision = cycle.get("decision", {})
            decision = decision if isinstance(decision, dict) else {}
            lines.extend(
                [
                    f"### Attempt {cycle.get('attempt', '?')}",
                    f"- agent: {cycle.get('agent', 'unknown')}",
                    f"- role: {cycle.get('agent_role', 'unknown')}",
                    f"- draft_status: {cycle.get('draft_status', 'unknown')}",
                    f"- decision: {decision.get('decision', 'unknown')}",
                    f"- blocking_dimensions: {', '.join(decision.get('blocking_dimensions', [])) if isinstance(decision.get('blocking_dimensions', []), list) else 'unknown'}",
                ]
            )
        lines.extend(["", "## Release Reasons"])
        reasons = release_policy.get("reasons", [])
        if isinstance(reasons, list) and reasons:
            lines.extend(f"- {item}" for item in reasons)
        else:
            lines.append("- none")
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {"agent_replay_report_json": json_path.as_posix(), "agent_replay_report_markdown": md_path.as_posix()}

    def _verdict_rank(self, verdict: EvaluatorVerdict) -> tuple[int, int, int]:
        status_rank = {"pass": 0, "warn": 1, "fail": 2}.get(verdict.status, 0)
        return (1 if verdict.blocking else 0, status_rank, len(verdict.evidence))

    def _merge_verdicts(self, verdicts: list[EvaluatorVerdict]) -> list[EvaluatorVerdict]:
        merged: dict[str, EvaluatorVerdict] = {}
        order: list[str] = []
        for verdict in verdicts:
            if verdict.dimension not in merged:
                merged[verdict.dimension] = verdict
                order.append(verdict.dimension)
                continue
            existing = merged[verdict.dimension]
            if self._verdict_rank(verdict) > self._verdict_rank(existing):
                merged[verdict.dimension] = verdict
        return [merged[dimension] for dimension in order]

    def _replace_verdict(
        self,
        verdict: EvaluatorVerdict,
        *,
        status: str | None = None,
        blocking: bool | None = None,
        evidence: list[str] | None = None,
        why_it_breaks: str | None = None,
        minimal_fix: str | None = None,
        rewrite_scope: str | None = None,
    ) -> EvaluatorVerdict:
        return EvaluatorVerdict(
            dimension=verdict.dimension,
            status=verdict.status if status is None else status,
            blocking=verdict.blocking if blocking is None else blocking,
            evidence=verdict.evidence if evidence is None else evidence,
            why_it_breaks=verdict.why_it_breaks if why_it_breaks is None else why_it_breaks,
            minimal_fix=verdict.minimal_fix if minimal_fix is None else minimal_fix,
            rewrite_scope=verdict.rewrite_scope if rewrite_scope is None else rewrite_scope,
        )

    def _apply_decision_policy(self, verdicts: list[EvaluatorVerdict]) -> list[EvaluatorVerdict]:
        verdict_by_dimension = {item.dimension: item for item in verdicts}
        adjusted = list(verdicts)

        character = verdict_by_dimension.get("character")
        if character is not None and not character.blocking and character.status == "warn":
            severe_character_issue = len(character.evidence) >= 2 or any(
                token in evidence for evidence in character.evidence for token in ("禁忌", "越界", "冲动", "行为")
            )
            if severe_character_issue:
                promoted_character = self._replace_verdict(
                    character,
                    status="fail",
                    blocking=True,
                    why_it_breaks="角色约束已经从设定漂移到正文行为层，继续放行会直接破坏人物可信度。",
                    minimal_fix="回到 scene beats 和对白动作层，修正角色行为、禁忌边界和受压反应。",
                    rewrite_scope="scene_beats + dialogue + chapter_result",
                )
                adjusted = [promoted_character if item.dimension == "character" else item for item in adjusted]
                verdict_by_dimension["character"] = promoted_character

        arc = verdict_by_dimension.get("arc")
        character = verdict_by_dimension.get("character")
        if (
            arc is not None
            and not arc.blocking
            and arc.status == "warn"
            and character is not None
            and character.status in {"warn", "fail"}
        ):
            promoted_arc = self._replace_verdict(
                arc,
                status="fail",
                blocking=True,
                evidence=[
                    *arc.evidence,
                    "角色一致性与角色弧信号同时失真，本章结果层需要回到人物推进重新对齐。",
                ],
                why_it_breaks="人物行为与角色弧同时漂移时，本章结果即使成立也会失去长期人物推进的可信度。",
                minimal_fix="补齐角色弧阶段，并把本章行为结果明确挂到人物推进变化上。",
                rewrite_scope="character_arc_memory + scene_beats + chapter_result",
            )
            adjusted = [promoted_arc if item.dimension == "arc" else item for item in adjusted]

        return adjusted

    def _load_json(self, path: Path) -> dict[str, object]:
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _has_runtime_arc_signal(self, draft_payload: dict[str, object]) -> bool:
        character_constraints = draft_payload.get("character_constraints", {})
        outcome_signature = draft_payload.get("outcome_signature", {})
        if not isinstance(character_constraints, dict) or not isinstance(outcome_signature, dict):
            return False
        protagonist = character_constraints.get("protagonist", {})
        counterpart = character_constraints.get("counterpart", {})
        if not isinstance(protagonist, dict) or not isinstance(counterpart, dict):
            return False
        return bool(
            str(protagonist.get("name", "")).strip()
            and str(counterpart.get("name", "")).strip()
            and str(outcome_signature.get("chapter_result", "")).strip()
        )

    def _schema_verdicts(
        self,
        project_dir: Path,
        draft_payload: dict[str, object] | None = None,
    ) -> list[EvaluatorVerdict]:
        schema_dir = project_dir / "00_memory" / "schema"
        reports_dir = project_dir / "05_reports"
        plan_text = read_text(project_dir / "00_memory" / "plan.md")
        plan_json = self._load_json(schema_dir / "plan.json")
        character_arcs_json = self._load_json(schema_dir / "character_arcs.json")
        foreshadow_json = self._load_json(reports_dir / "foreshadow_heatmap.json")
        arc_json = self._load_json(reports_dir / "arc_health.json")

        verdicts: list[EvaluatorVerdict] = []

        plan_evidence: list[str] = []
        plan_hook = str(plan_json.get("hook", "")).strip()
        if not plan_hook and "核心卖点" in plan_text:
            plan_hook = "derived-from-plan-md"
        plan_target_words = int(plan_json.get("targetWords", 0) or 0)
        if plan_target_words <= 0:
            plan_target_words = derive_plan_target_words(plan_text)
        if not plan_hook:
            plan_evidence.append("plan schema 缺少核心 hook。")
        if plan_target_words <= 0:
            plan_evidence.append("plan schema 还没有有效总字数目标。")
        verdicts.append(
            EvaluatorVerdict(
                dimension="plan",
                status="warn" if plan_evidence else "pass",
                blocking=False,
                evidence=plan_evidence,
                why_it_breaks="卷级规划缺口会削弱章节目标与长线推进的一致性。",
                minimal_fix="补齐 plan schema 的 hook 和总字数目标。",
                rewrite_scope="planning_memory",
            )
        )

        overdue = foreshadow_json.get("overdue", [])
        due = foreshadow_json.get("due", [])
        foreshadow_evidence: list[str] = []
        foreshadow_blocking = isinstance(overdue, list) and len(overdue) > 0
        if foreshadow_blocking:
            foreshadow_evidence.append(f"存在 {len(overdue)} 条超期伏笔。")
        elif isinstance(due, list) and len(due) > 0:
            foreshadow_evidence.append(f"当前章节有 {len(due)} 条到期伏笔待回收。")
        verdicts.append(
            EvaluatorVerdict(
                dimension="foreshadow",
                status="fail" if foreshadow_blocking else ("warn" if foreshadow_evidence else "pass"),
                blocking=foreshadow_blocking,
                evidence=foreshadow_evidence,
                why_it_breaks="超期伏笔未处理会直接破坏回收节奏和读者记忆热度。",
                minimal_fix="优先回收或明确延后超期/到期伏笔。",
                rewrite_scope="chapter_result_and_hook",
            )
        )

        stalled_count = int(arc_json.get("stalled_arc_count", 0) or 0)
        arc_evidence: list[str] = []
        arc_blocking = stalled_count > 0
        schema_arcs = character_arcs_json.get("arcs", [])
        report_arcs = arc_json.get("character_arcs", [])
        has_schema_arcs = isinstance(schema_arcs, list) and len(schema_arcs) > 0
        has_report_arcs = isinstance(report_arcs, list) and len(report_arcs) > 0
        has_runtime_arc_signal = self._has_runtime_arc_signal(draft_payload or {})
        if arc_blocking:
            arc_evidence.append(f"存在 {stalled_count} 个角色弧停滞风险。")
        elif not has_report_arcs and not has_schema_arcs and not has_runtime_arc_signal:
            arc_evidence.append("character arc schema/报告仍为空。")
        verdicts.append(
            EvaluatorVerdict(
                dimension="arc",
                status="fail" if arc_blocking else ("warn" if arc_evidence else "pass"),
                blocking=arc_blocking,
                evidence=arc_evidence,
                why_it_breaks="角色弧停滞或缺失时，章节推进会失去人物层结果变化。",
                minimal_fix="补齐角色弧状态，并把本章结果挂到角色阶段变化上。",
                rewrite_scope="character_arc_memory + chapter_result",
            )
        )
        return verdicts

    def _pass_decision(self) -> RuntimeDecision:
        return RuntimeDecision(
            decision="pass",
            rewrite_brief=None,
            blocking_dimensions=[],
            advisory_dimensions=[],
        )

    def _evaluate_cycle(
        self,
        project_dir: Path,
        chapter: int,
        brief: ChapterBrief,
        draft_payload: dict[str, object],
    ) -> tuple[list[EvaluatorVerdict], EvaluatorVerdict | None, list[str], dict[str, str]]:
        verdicts, warnings = self._build_verdicts(project_dir, chapter)
        verdicts = self._merge_verdicts([*verdicts, *self._schema_verdicts(project_dir, draft_payload)])
        agent_report_paths: dict[str, str] = {}
        postdraft_verdict: EvaluatorVerdict | None = None
        verdicts.append(self._coerce_verdict(from_pacing_runtime_output(project_dir, draft_payload)))
        verdicts.append(self._coerce_verdict(from_causality_runtime_output(draft_payload)))
        verdicts.append(self._coerce_verdict(from_promise_payoff_runtime_output(brief, draft_payload)))
        verdicts.append(self._coerce_verdict(from_chapter_progress_runtime_output(brief, draft_payload)))
        verdicts.append(self._coerce_verdict(from_dialogue_runtime_output(draft_payload)))
        reviewer_verdicts, reviewer_report_paths = ReviewerAgent().review_with_report(project_dir, chapter, draft_payload)
        verdicts.extend(reviewer_verdicts)
        agent_report_paths.update(reviewer_report_paths)
        if isinstance(draft_payload.get("character_constraints"), dict):
            postdraft_verdict = self._coerce_verdict(from_runtime_draft(draft_payload))
            verdicts = self._merge_verdicts([*verdicts, postdraft_verdict])
        verdicts = self._merge_verdicts(verdicts)
        verdicts = self._apply_decision_policy(verdicts)
        return verdicts, postdraft_verdict, warnings, agent_report_paths

    def _blocking_signature(self, decision: RuntimeDecision) -> tuple[str, ...]:
        rewrite_brief = decision.rewrite_brief
        must_change = [] if rewrite_brief is None else rewrite_brief.must_change
        return tuple([*decision.blocking_dimensions, *must_change[:2]])

    def run(self, project_dir: Path, chapter: int, dry_run: bool = False) -> dict[str, object]:
        packet = MemoryCompiler().build(project_dir, chapter)
        lead_writer_agent = LeadWriterAgent()
        director_agent = DirectorAgent()
        scene_beat_agent = SceneBeatAgent()
        writer_agent = WriterAgent()
        rewriter_agent = RewriterAgent()
        decision_engine = DecisionEngine()
        agent_report_paths: dict[str, str] = {}

        volume_warnings: list[str] = []
        if packet.is_volume_start and chapter > 1:
            volume_warnings.append(
                f"卷开始: 进入 {packet.volume_name}，确认上一卷交接清单已处理。"
                f"卷级承诺: {', '.join(packet.volume_promises[:5]) if packet.volume_promises else '未加载'}"
            )
        if packet.is_volume_end:
            volume_warnings.append(
                f"卷结束: {packet.volume_name} 最后一章。确认卷级承诺已兑现、伏笔回收到位。"
                f"跨卷交接: {', '.join(packet.volume_handoff[:5]) if packet.volume_handoff else '未加载'}"
            )

        merged_packet = packet
        if volume_warnings:
            merged_packet = type(packet)(**{**packet.to_dict(), "warnings": [*packet.warnings, *volume_warnings]})
        brief, lead_writer_paths = lead_writer_agent.create_brief(project_dir, merged_packet)
        agent_report_paths.update(lead_writer_paths)
        direction, director_paths = director_agent.direct(project_dir, merged_packet, brief)
        agent_report_paths.update(director_paths)
        scene_beat_plan, scene_beat_paths = scene_beat_agent.plan(project_dir, merged_packet, brief, direction)
        agent_report_paths.update(scene_beat_paths)
        decision = self._pass_decision()
        all_verdicts: list[EvaluatorVerdict] = []
        postdraft_verdict: EvaluatorVerdict | None = None
        draft_payload: dict[str, object] = {}
        cycle_history: list[dict[str, object]] = []
        runtime_warnings: list[str] = []
        blocking_signature: tuple[str, ...] | None = None
        repeated_blocking_rounds = 0
        max_rewrite_rounds = 2

        for attempt in range(max_rewrite_rounds + 1):
            if decision.decision == "revise":
                draft_payload = rewriter_agent.rewrite(
                    project_dir,
                    merged_packet,
                    brief,
                    decision,
                    direction=direction,
                    dry_run=dry_run,
                )
            else:
                draft_payload = writer_agent.draft(
                    project_dir,
                    merged_packet,
                    brief,
                    decision,
                    direction=direction,
                    scene_beat_plan=scene_beat_plan.to_dict(),
                    scene_beat_paths=scene_beat_paths,
                    dry_run=dry_run,
                )
            all_verdicts, postdraft_verdict, cycle_warnings, cycle_agent_report_paths = self._evaluate_cycle(
                project_dir,
                chapter,
                brief,
                draft_payload,
            )
            runtime_warnings.extend(cycle_warnings)
            agent_report_paths.update(cycle_agent_report_paths)
            decision = decision_engine.decide(all_verdicts)
            cycle_history.append(
                {
                    "attempt": attempt + 1,
                    "agent": draft_payload.get("agent", "unknown"),
                    "agent_role": draft_payload.get("agent_role", "unknown"),
                    "brief": brief.to_dict(),
                    "direction": direction.to_dict(),
                    "decision": decision.to_dict(),
                    "draft_status": draft_payload.get("status", "unknown"),
                }
            )
            if decision.decision == "pass":
                break

            current_signature = self._blocking_signature(decision)
            repeated_blocking_rounds = repeated_blocking_rounds + 1 if current_signature == blocking_signature else 1
            blocking_signature = current_signature
            if repeated_blocking_rounds >= 2 or attempt >= max_rewrite_rounds:
                decision = RuntimeDecision(
                    decision="fail",
                    rewrite_brief=decision.rewrite_brief,
                    blocking_dimensions=decision.blocking_dimensions,
                    advisory_dimensions=decision.advisory_dimensions,
                )
                cycle_history[-1]["decision"] = decision.to_dict()
                break
            brief, lead_writer_paths = lead_writer_agent.revise_brief(
                project_dir,
                merged_packet,
                brief,
                decision,
                all_verdicts,
                attempt=attempt + 1,
            )
            agent_report_paths.update(lead_writer_paths)
            direction, director_paths = director_agent.direct(project_dir, merged_packet, brief)
            agent_report_paths.update(director_paths)
            scene_beat_plan, scene_beat_paths = scene_beat_agent.plan(project_dir, merged_packet, brief, direction)
            agent_report_paths.update(scene_beat_paths)

        merged_packet = (
            packet
            if not runtime_warnings
            else type(packet)(**{**packet.to_dict(), "warnings": [*packet.warnings, *runtime_warnings]})
        )
        final_decision = decision
        if postdraft_verdict is not None and postdraft_verdict.status != "pass":
            final_decision = RuntimeDecision(
                decision=decision.decision,
                rewrite_brief=decision.rewrite_brief,
                blocking_dimensions=decision.blocking_dimensions,
                advisory_dimensions=[],
            )

        report_paths = RuntimeMemorySync().summarize(
            project_dir,
            merged_packet,
            brief,
            final_decision,
            all_verdicts,
            draft_payload=draft_payload,
            apply_changes=not dry_run,
        )
        report_paths = {
            **report_paths,
            **self._write_postdraft_report(project_dir, postdraft_verdict),
            **agent_report_paths,
        }
        for key in (
            "agent_prompt_path",
            "model_trace_path",
            "scene_beat_plan_json",
            "scene_beat_plan_markdown",
            "lead_writer_agent_report_json",
            "lead_writer_agent_report_markdown",
            "director_agent_report_json",
            "director_agent_report_markdown",
            "scene_beat_agent_report_json",
            "scene_beat_agent_report_markdown",
            "writer_handoff_json",
            "writer_handoff_markdown",
            "rewriter_handoff_json",
            "rewriter_handoff_markdown",
            "original_manuscript_snapshot_path",
            "rewrite_operation_path",
        ):
            value = str(draft_payload.get(key, "")).strip()
            if value:
                report_paths[key] = value

        release_policy = ReleasePolicy().evaluate(final_decision, all_verdicts)
        release_gate_paths = write_release_gate_report(project_dir, brief.chapter, release_policy, all_verdicts)
        report_paths = {**report_paths, **release_gate_paths}
        runtime_status = "fail" if release_policy.final_release == "fail" else "pass"
        if runtime_status == "pass" and (release_policy.final_release in {"revise", "warn"} or merged_packet.warnings):
            runtime_status = "warn"
        if runtime_status == "pass" and postdraft_verdict is not None and postdraft_verdict.status != "pass":
            runtime_status = "warn"

        payload = {
            "status": runtime_status,
            "chapter": chapter,
            "context": merged_packet.to_dict(),
            "brief": brief.to_dict(),
            "direction": direction.to_dict(),
            "decision": final_decision.to_dict(),
            "release_policy": release_policy.to_dict(),
            "final_release": release_policy.final_release,
            "draft": draft_payload,
            "verdicts": [item.to_dict() for item in all_verdicts],
            "postdraft_verdicts": [] if postdraft_verdict is None else [postdraft_verdict.to_dict()],
            "report_paths": report_paths,
            "cycles": cycle_history,
        }
        payload["report_paths"] = {
            **payload["report_paths"],
            **self._write_agent_replay_report(project_dir, payload),
        }
        payload["report_paths"] = {
            **payload["report_paths"],
            **self._write_runtime_payload(project_dir, payload),
        }
        return payload
