from __future__ import annotations

import re
from pathlib import Path

from runtime.script_imports import ensure_scripts_on_path

ensure_scripts_on_path()

from chapter_gate import build_gate_analysis
from draft_gate import build_payload as build_draft_payload
from evaluators.continuity import from_gate_payload
from evaluators.draft import from_draft_payload
from evaluators.repeat import from_repeat_payload
from evaluators.style import from_language_payload
from language_audit import analyze_text, parse_style_file
from novel_utils import detect_existing_chapter_file
from anti_repeat_scan import build_payload as build_repeat_payload
from runtime.contracts import EvaluatorVerdict


RUNTIME_QUALITY_EXCLUDED_DIMENSIONS = {"plan", "foreshadow", "arc"}

# 对白分析常驻标记（与 evaluators/dialogue.py 对齐口径）
_DIALOGUE_RE = re.compile(r'["\u201c]([^"\u201d\n]{2,120})["\u201d]')
_DIALOGUE_EXPLANATORY = ("因为", "其实", "就是", "等于", "你要知道", "意思是", "说明")
_DIALOGUE_PRESSURE = ("吗", "呢", "先", "别", "确认", "底牌", "代价", "局面", "主动权")


class RuntimeQualityService:
    """Runtime-owned facade for collecting quality-facing verdicts."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self._repo_root = repo_root

    def _resolve_repo_root(self) -> Path:
        return self._repo_root or Path(__file__).resolve().parent.parent

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

    def _dedupe_verdicts(self, verdicts: list[EvaluatorVerdict]) -> list[EvaluatorVerdict]:
        deduped: list[EvaluatorVerdict] = []
        seen_dimensions: set[str] = set()
        for verdict in verdicts:
            if verdict.dimension in seen_dimensions:
                continue
            seen_dimensions.add(verdict.dimension)
            deduped.append(verdict)
        return deduped

    def _detect_chapter(self, project_dir: Path, chapter: int) -> tuple[int, Path]:
        return detect_existing_chapter_file(project_dir, None, chapter)

    def _collect_chapter_gate_verdict(self, project_dir: Path, chapter: int) -> tuple[EvaluatorVerdict, list[str]]:
        chapter_no, chapter_path = self._detect_chapter(project_dir, chapter)
        style_path = project_dir / "00_memory" / "style.md"
        analysis = build_gate_analysis(project_dir, chapter_no, chapter_path, style_path, skip_language=True)
        warnings = [str(item) for item in analysis.get("warnings", []) if str(item).strip()]
        blockers = [str(item) for item in analysis.get("blockers", []) if str(item).strip()]
        if blockers:
            warnings = [*warnings, *blockers]
        return self._coerce_verdict(from_gate_payload(analysis)), warnings

    def _collect_draft_gate_verdict(self, project_dir: Path, chapter: int) -> tuple[EvaluatorVerdict, list[str]]:
        chapter_no, chapter_path = self._detect_chapter(project_dir, chapter)
        payload = build_draft_payload(project_dir, chapter_no, chapter_path)
        warnings = [str(item) for item in payload.get("warnings", []) if str(item).strip()]
        blockers = [str(item) for item in payload.get("blockers", []) if str(item).strip()]
        if blockers:
            warnings = [*warnings, *blockers]
        return self._coerce_verdict(from_draft_payload(payload)), warnings

    def _collect_language_verdict(self, project_dir: Path, chapter: int) -> tuple[EvaluatorVerdict, list[str]]:
        _, chapter_path = self._detect_chapter(project_dir, chapter)
        style_path = project_dir / "00_memory" / "style.md"
        text = chapter_path.read_text(encoding="utf-8")
        style_profile = parse_style_file(style_path)
        analysis = analyze_text(text, style_profile, style_path)
        warnings = [str(item) for item in analysis.get("findings", []) if str(item).strip()]
        return self._coerce_verdict(from_language_payload(analysis)), warnings

    def _collect_dialogue_verdict(self, project_dir: Path, chapter: int) -> tuple[EvaluatorVerdict, list[str]]:
        """基于章节正文做基础对白分析（与 evaluators/dialogue.py 口径一致）。"""
        _, chapter_path = self._detect_chapter(project_dir, chapter)
        text = chapter_path.read_text(encoding="utf-8") if chapter_path.exists() else ""
        dialogue_lines = [m.group(1).strip() for m in _DIALOGUE_RE.finditer(text)]
        evidence: list[str] = []

        if not text.strip():
            evidence.append("章节正文为空，无法校验对白承压与角色声线。")
        elif len(dialogue_lines) < 2:
            evidence.append("本章有效对白不足 2 句，冲突交换层过薄。")
        else:
            normalized = [re.sub(r"\s+", "", line) for line in dialogue_lines]
            if len(set(normalized)) <= 1:
                evidence.append("多句对白几乎同一模板回声，角色声线没有真正分开。")
            explanatory_count = sum(any(m in line for m in _DIALOGUE_EXPLANATORY) for line in dialogue_lines)
            if explanatory_count >= max(2, len(dialogue_lines) // 2 + 1):
                evidence.append("对白解释腔偏重，人物更像在替作者补信息而不是争位置。")
            pressure_count = sum(any(m in line for m in _DIALOGUE_PRESSURE) for line in dialogue_lines)
            if pressure_count == 0:
                evidence.append("对白缺少试探、施压或讨价还价，冲突对话失去抓手。")
            if len(dialogue_lines) >= 3:
                bands = {"short", "mid", "long"}
                actual = set()
                for line in dialogue_lines:
                    length = len(line)
                    if length <= 10:
                        actual.add("short")
                    elif length <= 22:
                        actual.add("mid")
                    else:
                        actual.add("long")
                if len(actual) == 1:
                    evidence.append("多句对白长度过于整齐，节拍像同一模板裁出来，角色区分度不足。")

        return self._coerce_verdict({
            "dimension": "dialogue",
            "status": "warn" if evidence else "pass",
            "blocking": False,
            "evidence": evidence,
            "why_it_breaks": "对白若缺少差分、施压和反应层，角色关系会被写平。",
            "minimal_fix": "按角色目标、压力和身份差异重写问答与回击，不要让对白只做解释。",
            "rewrite_scope": "dialogue",
        }), evidence

    def _collect_repeat_verdict(self, project_dir: Path) -> tuple[EvaluatorVerdict, list[str]]:
        payload = build_repeat_payload(project_dir)
        warnings = [str(item) for item in payload.get("warnings", []) if str(item).strip()]
        return self._coerce_verdict(from_repeat_payload(payload)), warnings

    def collect_runtime_verdicts(self, project_dir: Path, chapter: int) -> tuple[list[EvaluatorVerdict], list[str]]:
        if chapter <= 0:
            return [], ["runtime skipped evaluators because no drafted chapter number was provided"]

        repo_root = self._resolve_repo_root()
        if not repo_root.exists():
            return [], ["runtime quality service could not resolve repo root"]

        warnings: list[str] = []
        verdicts: list[EvaluatorVerdict] = []

        chapter_gate_verdict, chapter_gate_warnings = self._collect_chapter_gate_verdict(project_dir, chapter)
        warnings.extend(chapter_gate_warnings)
        verdicts.append(chapter_gate_verdict)

        draft_gate_verdict, draft_gate_warnings = self._collect_draft_gate_verdict(project_dir, chapter)
        warnings.extend(draft_gate_warnings)
        verdicts.append(draft_gate_verdict)

        language_verdict, language_warnings = self._collect_language_verdict(project_dir, chapter)
        warnings.extend(language_warnings)
        verdicts.append(language_verdict)

        repeat_verdict, repeat_warnings = self._collect_repeat_verdict(project_dir)
        warnings.extend(repeat_warnings)
        verdicts.append(repeat_verdict)

        dialogue_verdict, dialogue_warnings = self._collect_dialogue_verdict(project_dir, chapter)
        warnings.extend(dialogue_warnings)
        verdicts.append(dialogue_verdict)

        filtered_verdicts = [
            verdict
            for verdict in verdicts
            if verdict.dimension not in RUNTIME_QUALITY_EXCLUDED_DIMENSIONS
        ]
        return self._dedupe_verdicts(filtered_verdicts), warnings
