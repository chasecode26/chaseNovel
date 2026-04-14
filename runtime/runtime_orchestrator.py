from __future__ import annotations

import json
from pathlib import Path

from runtime.contracts import EvaluatorVerdict, RuntimeLoopResult
from runtime.decision_engine import DecisionEngine
from runtime.lead_writer import LeadWriter
from runtime.memory_compiler import MemoryCompiler
from runtime.memory_sync import RuntimeMemorySync
from runtime.writer_executor import WriterExecutor
from scripts.aggregation_utils import run_script_json, safe_write_text, validate_project_root


class LeadWriterRuntime:
    MAX_REWRITE_ITERATIONS = 3
    AUTO_REWRITE_DIMENSIONS = {"style", "dialogue"}

    def _is_auto_rewrite_dimension_set(self, decision_dimensions: list[str]) -> bool:
        if not decision_dimensions:
            return False
        allowed_dimensions = self.AUTO_REWRITE_DIMENSIONS | {"continuity"}
        if any(dimension not in allowed_dimensions for dimension in decision_dimensions):
            return False
        return any(dimension in self.AUTO_REWRITE_DIMENSIONS for dimension in decision_dimensions)

    def _validated_paths(self, project_dir: Path, chapter: int) -> tuple[Path, Path]:
        validated_root = validate_project_root(project_dir)
        if validated_root.is_symlink():
            raise ValueError("project root must not be a symlink")
        chapters_dir = validated_root / "03_chapters"
        gate_dir = validated_root / "04_gate" / f"ch{chapter:03d}"
        if chapters_dir.is_symlink() or gate_dir.is_symlink():
            raise ValueError("runtime loop refuses symlinked write roots")
        return validated_root, gate_dir

    def _build_runtime_verdicts(self, repo_root: Path, project_dir: Path, chapter: int) -> list[EvaluatorVerdict]:
        quality = run_script_json(
            repo_root,
            "quality_gate.py",
            ["--project", project_dir.as_posix(), "--chapter-no", str(chapter)],
        )
        status = run_script_json(
            repo_root,
            "book_health.py",
            ["--project", project_dir.as_posix(), "--chapter", str(chapter)],
        )
        verdicts: list[EvaluatorVerdict] = []
        for payload in (quality, status):
            raw_verdicts = payload.get("verdicts", [])
            if not isinstance(raw_verdicts, list):
                continue
            for item in raw_verdicts:
                if not isinstance(item, dict):
                    continue
                verdicts.append(
                    EvaluatorVerdict(
                        dimension=str(item.get("dimension", "unknown")),
                        status=str(item.get("status", "pass")),
                        blocking=bool(item.get("blocking", False)),
                        evidence=[str(entry) for entry in item.get("evidence", []) if str(entry).strip()],
                        why_it_breaks=str(item.get("why_it_breaks", "")),
                        minimal_fix=str(item.get("minimal_fix", "")),
                        rewrite_scope=str(item.get("rewrite_scope", "")),
                    )
                )
        return verdicts

    def _chapter_path(self, project_dir: Path, chapter: int) -> Path | None:
        return WriterExecutor()._resolve_chapter_path(project_dir, chapter)

    def _can_auto_rewrite(self, decision_dimensions: list[str], loop_results: list[RuntimeLoopResult]) -> bool:
        if len(loop_results) >= self.MAX_REWRITE_ITERATIONS:
            return False
        if not self._is_auto_rewrite_dimension_set(decision_dimensions):
            return False
        if loop_results and not loop_results[-1].applied:
            return False
        return True

    def _run_rewrite_iteration(
        self,
        repo_root: Path,
        project_dir: Path,
        chapter: int,
        chapter_path: Path,
        iteration: int,
    ) -> RuntimeLoopResult:
        validated_root, gate_dir = self._validated_paths(project_dir, chapter)
        rewrite_path = gate_dir / f"runtime_rewrite_{iteration}.md"
        planning_path = gate_dir / "planning_review.json"

        if not planning_path.exists():
            run_script_json(
                repo_root,
                "chapter_planning_review.py",
                ["--project", project_dir.as_posix(), "--target-chapter", str(chapter)],
            )

        chapter_gate = run_script_json(
            repo_root,
            "chapter_gate.py",
            [
                "--project",
                project_dir.as_posix(),
                "--chapter-no",
                str(chapter),
                "--rewrite-out",
                rewrite_path.as_posix(),
            ],
        )
        language = run_script_json(
            repo_root,
            "language_audit.py",
            [
                "--project",
                project_dir.as_posix(),
                "--chapter-no",
                str(chapter),
                "--mode",
                "suggest",
                "--rewrite-out",
                rewrite_path.as_posix(),
            ],
        )

        notes: list[str] = []
        updated_files: list[str] = []
        applied = False

        rewritten_text = ""
        if isinstance(language.get("rewritten_text"), str):
            rewritten_text = str(language.get("rewritten_text", "")).strip()
        if not rewritten_text and rewrite_path.exists():
            rewritten_text = rewrite_path.read_text(encoding="utf-8").strip()

        chapter_gate_verdict = str(chapter_gate.get("verdict", "pass"))
        chapter_gate_blocking = str(chapter_gate.get("blocking", "no")) == "yes" or chapter_gate_verdict == "block"
        gate_blocking_dimensions: list[str] = []
        if str(chapter_gate.get("continuity_verdict", "pass")) == "block":
            gate_blocking_dimensions.append("continuity")
        if str(chapter_gate.get("language_verdict", "pass")) == "rewrite":
            gate_blocking_dimensions.append("style")
        style_safe_block = chapter_gate_blocking and self._is_auto_rewrite_dimension_set(gate_blocking_dimensions)
        if rewritten_text and (not chapter_gate_blocking or style_safe_block):
            safe_write_text(
                chapter_path,
                rewritten_text + ("\n" if not rewritten_text.endswith("\n") else ""),
                root_dir=validated_root,
            )
            updated_files.append(chapter_path.as_posix())
            applied = True
            if style_safe_block:
                notes.append("applied language rewrite suggestion while preserving fact-layer blockers for recheck")
            else:
                notes.append("applied language rewrite suggestion")
        elif rewritten_text and chapter_gate_blocking:
            notes.append("rewrite suggestion generated but gate blockers kept chapter fact layer unresolved")
        else:
            notes.append("no rewrite suggestion generated")

        planning_payload = {}
        if planning_path.exists():
            try:
                planning_payload = json.loads(planning_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                planning_payload = {}

        return RuntimeLoopResult(
            iteration=iteration,
            applied=applied,
            source="chapter_gate + language_audit",
            notes=notes,
            updated_files=updated_files,
            payload={
                "chapter_gate_status": str(chapter_gate.get("status", "pass")),
                "chapter_gate_verdict": chapter_gate_verdict,
                "language_verdict": str(language.get("verdict", "pass")),
                "planning_status": str(planning_payload.get("status", "missing")) if isinstance(planning_payload, dict) else "missing",
                "rewrite_path": rewrite_path.as_posix(),
            },
        )

    def run(self, project_dir: Path, chapter: int) -> dict[str, object]:
        repo_root = Path(__file__).resolve().parent.parent
        packet = MemoryCompiler().build(project_dir, chapter)
        brief = LeadWriter().create_brief(packet)
        chapter_path = self._chapter_path(project_dir, chapter)
        draft = WriterExecutor().build_draft_payload(project_dir, brief, chapter_path=chapter_path)
        verdicts = self._build_runtime_verdicts(repo_root, project_dir, chapter)
        decision = DecisionEngine().decide(verdicts)

        loop_results: list[RuntimeLoopResult] = []
        while decision.decision == "revise" and chapter_path is not None and self._can_auto_rewrite(decision.blocking_dimensions, loop_results):
            loop_result = self._run_rewrite_iteration(repo_root, project_dir, chapter, chapter_path, len(loop_results) + 1)
            loop_results.append(loop_result)
            if not loop_result.applied:
                break
            draft = WriterExecutor().build_draft_payload(project_dir, brief, chapter_path=chapter_path)
            verdicts = self._build_runtime_verdicts(repo_root, project_dir, chapter)
            decision = DecisionEngine().decide(verdicts)

        if decision.decision == "revise" and chapter_path is not None and not loop_results:
            loop_results.append(
                RuntimeLoopResult(
                    iteration=1,
                    applied=False,
                    source="runtime-loop-skip",
                    notes=["blocking dimensions are not eligible for automatic rewrite"],
                    updated_files=[],
                    payload={"blocking_dimensions": decision.blocking_dimensions},
                )
            )

        report_paths = RuntimeMemorySync().summarize(project_dir, packet, brief, draft, verdicts, decision, loop_results=loop_results)
        status = "pass" if decision.decision == "pass" else "fail"
        return {
            "status": status,
            "chapter": chapter,
            "context": packet.to_dict(),
            "brief": brief.to_dict(),
            "decision": decision.to_dict(),
            "draft": draft,
            "verdicts": [item.to_dict() for item in verdicts],
            "runtime_loop": [item.to_dict() for item in loop_results],
            "report_paths": report_paths,
        }
