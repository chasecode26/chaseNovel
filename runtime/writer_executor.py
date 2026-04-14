from __future__ import annotations

from pathlib import Path

from runtime.contracts import ChapterBrief
from runtime.novel_utils import list_chapter_files, read_text


class WriterExecutor:
    def _resolve_chapter_path(self, project_dir: Path, chapter: int) -> Path | None:
        for chapter_no, path in list_chapter_files(project_dir):
            if chapter_no == chapter:
                return path
        return None

    def build_draft_payload(
        self,
        project_dir: Path,
        brief: ChapterBrief,
        chapter_path: Path | None = None,
    ) -> dict[str, object]:
        resolved_path = chapter_path or self._resolve_chapter_path(project_dir, brief.chapter)
        chapter_text = read_text(resolved_path) if resolved_path else ""
        body_lines = [line.strip() for line in chapter_text.splitlines() if line.strip() and not line.strip().startswith("#")]
        body_preview = "\n".join(body_lines[:6])
        return {
            "chapter": brief.chapter,
            "mode": "runtime-single-writer",
            "chapter_function": brief.chapter_function,
            "status": "existing-draft-loaded" if resolved_path and chapter_text.strip() else "pending-human-draft",
            "chapter_path": resolved_path.as_posix() if resolved_path else "",
            "word_count": len("".join(body_lines)),
            "body_preview": body_preview,
            "must_advance": brief.must_advance,
            "must_not_repeat": brief.must_not_repeat,
            "allowed_threads": brief.allowed_threads,
            "disallowed_moves": brief.disallowed_moves,
            "voice_constraints": brief.voice_constraints,
        }
