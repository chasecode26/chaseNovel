from __future__ import annotations

import json
from pathlib import Path

from evaluators.character import from_runtime_draft
from evaluators.continuity import from_gate_payload
from evaluators.repeat import from_repeat_payload
from evaluators.style import from_language_payload
from runtime.contracts import EvaluatorVerdict
from runtime.decision_engine import DecisionEngine
from runtime.lead_writer import LeadWriter
from runtime.memory_compiler import MemoryCompiler
from runtime.memory_sync import RuntimeMemorySync
from runtime.writer_executor import WriterExecutor
from scripts.aggregation_utils import run_script_json


class LeadWriterRuntime:
    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parent.parent

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
        if chapter <= 0:
            return [], ["runtime skipped evaluators because no drafted chapter number was provided"]

        repo_root = self._repo_root()
        warnings: list[str] = []
        verdicts: list[EvaluatorVerdict] = []

        quality_payload = run_script_json(
            repo_root,
            "quality_gate.py",
            ["--project", project_dir.as_posix(), "--chapter-no", str(chapter), "--dry-run"],
        )
        if int(quality_payload.get("returncode", 0)) not in (0, 1):
            warnings.append(f"quality evaluator failed: {quality_payload.get('stderr', 'unknown error')}")
        for item in quality_payload.get("verdicts", []):
            if isinstance(item, dict):
                verdicts.append(self._coerce_verdict(item))

        if not any(item.dimension == "continuity" for item in verdicts):
            chapter_gate_payload = run_script_json(
                repo_root,
                "chapter_gate.py",
                ["--project", project_dir.as_posix(), "--chapter-no", str(chapter), "--dry-run"],
            )
            if int(chapter_gate_payload.get("returncode", 0)) in (0, 1):
                verdicts.append(self._coerce_verdict(from_gate_payload(chapter_gate_payload)))
            else:
                warnings.append(f"chapter gate failed: {chapter_gate_payload.get('stderr', 'unknown error')}")

        if not any(item.dimension == "style" for item in verdicts):
            language_payload = run_script_json(
                repo_root,
                "language_audit.py",
                ["--project", project_dir.as_posix(), "--chapter-no", str(chapter), "--dry-run"],
            )
            if int(language_payload.get("returncode", 0)) in (0, 1):
                verdicts.append(self._coerce_verdict(from_language_payload(language_payload)))
            else:
                warnings.append(f"language audit failed: {language_payload.get('stderr', 'unknown error')}")

        repeat_payload = run_script_json(
            repo_root,
            "anti_repeat_scan.py",
            ["--project", project_dir.as_posix(), "--dry-run"],
        )
        if int(repeat_payload.get("returncode", 0)) == 0:
            verdicts.append(self._coerce_verdict(from_repeat_payload(repeat_payload)))
        else:
            warnings.append(f"repeat evaluator failed: {repeat_payload.get('stderr', 'unknown error')}")

        deduped: list[EvaluatorVerdict] = []
        seen_dimensions: set[str] = set()
        for item in verdicts:
            if item.dimension in seen_dimensions:
                continue
            seen_dimensions.add(item.dimension)
            deduped.append(item)
        return deduped, warnings

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

    def _schema_verdicts(self, project_dir: Path) -> list[EvaluatorVerdict]:
        schema_dir = project_dir / "00_memory" / "schema"
        reports_dir = project_dir / "05_reports"
        plan_json = self._load_json(schema_dir / "plan.json")
        foreshadow_json = self._load_json(reports_dir / "foreshadow_heatmap.json")
        arc_json = self._load_json(reports_dir / "arc_health.json")

        verdicts: list[EvaluatorVerdict] = []

        plan_evidence: list[str] = []
        if not str(plan_json.get("hook", "")).strip():
            plan_evidence.append("plan schema 缺少核心 hook。")
        if int(plan_json.get("targetWords", 0) or 0) <= 0:
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
        if arc_blocking:
            arc_evidence.append(f"存在 {stalled_count} 个角色弧停滞风险。")
        elif not arc_json.get("character_arcs"):
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

    def run(self, project_dir: Path, chapter: int, dry_run: bool = False) -> dict[str, object]:
        packet = MemoryCompiler().build(project_dir, chapter)
        verdicts, runtime_warnings = self._build_verdicts(project_dir, chapter)
        merged_packet = packet if not runtime_warnings else type(packet)(
            **{**packet.to_dict(), "warnings": [*packet.warnings, *runtime_warnings]}
        )
        brief = LeadWriter().create_brief(merged_packet)
        draft_payload = WriterExecutor().draft(
            project_dir,
            merged_packet,
            brief,
            DecisionEngine().decide(verdicts),
            dry_run=dry_run,
        )
        postdraft_verdict: EvaluatorVerdict | None = None
        if isinstance(draft_payload.get("character_constraints"), dict):
            postdraft_verdict = self._coerce_verdict(from_runtime_draft(draft_payload))

        all_verdicts = self._merge_verdicts([*verdicts, *self._schema_verdicts(project_dir)])
        if postdraft_verdict is not None:
            all_verdicts = self._merge_verdicts([*all_verdicts, postdraft_verdict])
        all_verdicts = self._apply_decision_policy(all_verdicts)

        decision = DecisionEngine().decide(all_verdicts)
        report_paths = RuntimeMemorySync().summarize(
            project_dir,
            merged_packet,
            brief,
            decision,
            all_verdicts,
            apply_changes=not dry_run,
        )
        report_paths = {
            **report_paths,
            **self._write_postdraft_report(project_dir, postdraft_verdict),
        }

        runtime_status = "pass"
        if decision.decision == "revise" or merged_packet.warnings:
            runtime_status = "warn"
        if postdraft_verdict is not None and postdraft_verdict.status != "pass":
            runtime_status = "warn"

        return {
            "status": runtime_status,
            "chapter": chapter,
            "context": merged_packet.to_dict(),
            "brief": brief.to_dict(),
            "decision": decision.to_dict(),
            "draft": draft_payload,
            "verdicts": [item.to_dict() for item in all_verdicts],
            "postdraft_verdicts": [] if postdraft_verdict is None else [postdraft_verdict.to_dict()],
            "report_paths": report_paths,
        }
