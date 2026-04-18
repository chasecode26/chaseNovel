from __future__ import annotations

import json
from pathlib import Path

from runtime.contracts import ChapterContextPacket
from novel_utils import extract_state_value, read_text


class MemoryCompiler:
    def _load_json(self, path: Path) -> dict[str, object]:
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def build(self, project_dir: Path, chapter: int) -> ChapterContextPacket:
        schema_dir = project_dir / "00_memory" / "schema"
        state = self._load_json(schema_dir / "state.json")
        voice = self._load_json(schema_dir / "voice.json")
        state_text = read_text(project_dir / "00_memory" / "state.md")

        anchors = state.get("sceneAnchors", {})
        current_place = ""
        if isinstance(anchors, dict):
            current_place = str(anchors.get("location", "")).strip()
        if not current_place:
            current_place = extract_state_value(state_text, "当前地点") or "未识别"

        next_goal = str(state.get("chapterGoal", "")).strip() or extract_state_value(state_text, "计划内容") or "待明确"
        current_volume = str(state.get("currentVolume", "")).strip() or extract_state_value(state_text, "当前卷") or "未识别"
        current_arc = str(state.get("currentArc", "")).strip() or extract_state_value(state_text, "当前弧") or "未识别"
        open_threads = [str(item) for item in state.get("openThreads", []) if str(item).strip()]
        forbidden = [str(item) for item in state.get("forbiddenInventions", []) if str(item).strip()]
        voice_rules = [str(item) for item in voice.get("forbiddenCadence", []) if str(item).strip()]

        return ChapterContextPacket(
            project=project_dir.as_posix(),
            chapter=chapter,
            active_volume=current_volume,
            active_arc=current_arc,
            current_place=current_place,
            next_goal=next_goal,
            open_threads=open_threads,
            forbidden_inventions=forbidden,
            voice_rules=voice_rules,
        )
