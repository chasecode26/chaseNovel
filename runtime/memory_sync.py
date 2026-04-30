from __future__ import annotations

import json
from pathlib import Path

from runtime.script_imports import ensure_scripts_on_path

ensure_scripts_on_path()

from novel_utils import derive_plan_target_words, extract_markdown_table_rows, parse_plan_volumes, read_text
from runtime.contracts import ChapterBrief, ChapterContextPacket, EvaluatorVerdict, MemoryPatch, RuntimeDecision


class RuntimeMemorySync:
    def _load_json(self, path: Path) -> dict[str, object]:
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _load_schema(self, schema_path: Path) -> dict[str, object]:
        return self._load_json(schema_path)

    def _default_for_schema_node(self, node: object) -> object:
        if not isinstance(node, dict):
            return None
        declared_type = node.get("type")
        if declared_type == "string":
            return ""
        if declared_type == "integer":
            minimum = node.get("minimum")
            return int(minimum) if isinstance(minimum, int) else 0
        if declared_type == "array":
            return []
        if declared_type == "object":
            properties = node.get("properties", {})
            if isinstance(properties, dict):
                return {
                    str(key): self._default_for_schema_node(value)
                    for key, value in properties.items()
                    if self._default_for_schema_node(value) is not None
                }
            return {}
        return None

    def _schema_defaults(self, schema_name: str, schema_dir: Path) -> dict[str, object]:
        schema = self._load_schema(schema_dir.parent.parent / "schemas" / schema_name)
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            return {}
        defaults: dict[str, object] = {}
        for key, value in properties.items():
            default_value = self._default_for_schema_node(value)
            if default_value is not None:
                defaults[str(key)] = default_value
        return defaults

    def _dedupe_strings(self, values: list[object]) -> list[str]:
        deduped: list[str] = []
        seen: set[str] = set()
        for item in values:
            text = str(item).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            deduped.append(text)
        return deduped

    def _normalize_state_payload(self, payload: dict[str, object], schema_dir: Path) -> dict[str, object]:
        defaults = self._schema_defaults("state.schema.json", schema_dir)
        normalized = dict(defaults)
        normalized.update(payload)
        scene_anchors = normalized.get("sceneAnchors", {})
        if not isinstance(scene_anchors, dict):
            scene_anchors = {}
        scene_defaults = defaults.get("sceneAnchors", {})
        normalized["sceneAnchors"] = {
            **(scene_defaults if isinstance(scene_defaults, dict) else {}),
            **scene_anchors,
        }
        normalized["currentChapter"] = max(0, int(normalized.get("currentChapter", 0) or 0))
        normalized["openThreads"] = self._dedupe_strings(list(normalized.get("openThreads", [])))
        normalized["forbiddenInventions"] = self._dedupe_strings(list(normalized.get("forbiddenInventions", [])))
        normalized["pendingPayoffs"] = self._dedupe_strings(list(normalized.get("pendingPayoffs", [])))
        return normalized

    def _normalize_timeline_payload(self, payload: dict[str, object], schema_dir: Path) -> dict[str, object]:
        defaults = self._schema_defaults("timeline.schema.json", schema_dir)
        normalized = dict(defaults)
        normalized.update(payload)
        normalized["recentEvents"] = self._dedupe_strings(list(normalized.get("recentEvents", [])))
        return normalized

    def _normalize_payoff_payload(self, payload: dict[str, object], schema_dir: Path) -> dict[str, object]:
        defaults = self._schema_defaults("payoff.schema.json", schema_dir)
        normalized = dict(defaults)
        normalized.update(payload)
        promises = normalized.get("promises", [])
        if not isinstance(promises, list):
            promises = []
        normalized_promises: list[dict[str, object]] = []
        seen_ids: set[str] = set()
        for item in promises:
            if not isinstance(item, dict):
                continue
            promise_id = str(item.get("promiseId", "")).strip()
            reader_expectation = str(item.get("readerExpectation", "")).strip()
            if not promise_id or not reader_expectation or promise_id in seen_ids:
                continue
            seen_ids.add(promise_id)
            normalized_promises.append(
                {
                    "promiseId": promise_id,
                    "promiseType": str(item.get("promiseType", "open_thread") or "open_thread"),
                    "readerExpectation": reader_expectation,
                    "status": str(item.get("status", "pending") or "pending"),
                }
            )
        normalized["promises"] = normalized_promises
        return normalized

    def _normalize_expectation_tracking_payload(self, payload: dict[str, object]) -> dict[str, object]:
        chapters = payload.get("chapters", [])
        if not isinstance(chapters, list):
            chapters = []
        normalized_chapters: list[dict[str, object]] = []
        seen: set[int] = set()
        for item in chapters:
            if not isinstance(item, dict):
                continue
            chapter = max(0, int(item.get("chapter", 0) or 0))
            if chapter in seen:
                continue
            seen.add(chapter)
            normalized_chapters.append(
                {
                    "chapter": chapter,
                    "shortExpectations": self._dedupe_strings(list(item.get("shortExpectations", []))),
                    "longExpectations": self._dedupe_strings(list(item.get("longExpectations", []))),
                    "expectationPayoffs": self._dedupe_strings(list(item.get("expectationPayoffs", []))),
                    "newExpectations": self._dedupe_strings(list(item.get("newExpectations", []))),
                    "expectationGapRisks": self._dedupe_strings(list(item.get("expectationGapRisks", []))),
                    "genreFrameworkHints": self._dedupe_strings(list(item.get("genreFrameworkHints", []))),
                    "readerHook": str(item.get("readerHook", "")).strip(),
                    "chapterResult": str(item.get("chapterResult", "")).strip(),
                    "releaseDecision": str(item.get("releaseDecision", "")).strip(),
                    "blockingDimensions": self._dedupe_strings(list(item.get("blockingDimensions", []))),
                    "advisoryDimensions": self._dedupe_strings(list(item.get("advisoryDimensions", []))),
                }
            )
        normalized_chapters.sort(key=lambda item: int(item.get("chapter", 0) or 0))
        return {"chapters": normalized_chapters[-80:]}

    def _normalize_plan_payload(self, payload: dict[str, object], schema_dir: Path) -> dict[str, object]:
        defaults = self._schema_defaults("plan.schema.json", schema_dir)
        normalized = dict(defaults)
        normalized.update(payload)
        normalized["title"] = str(normalized.get("title", "")).strip()
        normalized["genre"] = str(normalized.get("genre", "")).strip()
        normalized["hook"] = str(normalized.get("hook", "")).strip()
        normalized["targetWords"] = max(0, int(normalized.get("targetWords", 0) or 0))
        volumes = normalized.get("volumes", [])
        normalized["volumes"] = volumes if isinstance(volumes, list) else []
        return normalized

    def _normalize_characters_payload(self, payload: dict[str, object], schema_dir: Path) -> dict[str, object]:
        defaults = self._schema_defaults("characters.schema.json", schema_dir)
        normalized = dict(defaults)
        normalized.update(payload)
        characters = normalized.get("characters", [])
        if not isinstance(characters, list):
            characters = []
        deduped: list[dict[str, object]] = []
        seen_ids: set[str] = set()
        for item in characters:
            if not isinstance(item, dict):
                continue
            identifier = str(item.get("id", "")).strip()
            name = str(item.get("name", "")).strip()
            if not identifier or not name or identifier in seen_ids:
                continue
            seen_ids.add(identifier)
            traits = item.get("voiceTraits", [])
            deduped.append(
                {
                    "id": identifier,
                    "name": name,
                    "role": str(item.get("role", "")).strip(),
                    "voiceTraits": self._dedupe_strings(traits if isinstance(traits, list) else []),
                }
            )
        normalized["characters"] = deduped
        return normalized

    def _normalize_character_arcs_payload(self, payload: dict[str, object], schema_dir: Path) -> dict[str, object]:
        defaults = self._schema_defaults("character_arcs.schema.json", schema_dir)
        normalized = dict(defaults)
        normalized.update(payload)
        arcs = normalized.get("arcs", [])
        deduped: list[dict[str, str]] = []
        seen_characters: set[str] = set()
        for item in arcs if isinstance(arcs, list) else []:
            if not isinstance(item, dict):
                continue
            character = str(item.get("character", "")).strip()
            if not character or character in seen_characters:
                continue
            seen_characters.add(character)
            deduped.append(
                {
                    "character": character,
                    "arcType": str(item.get("arcType", "")).strip(),
                    "stage": str(item.get("stage", "")).strip(),
                    "goal": str(item.get("goal", "")).strip(),
                    "blocker": str(item.get("blocker", "")).strip(),
                    "recentChange": str(item.get("recentChange", "")).strip(),
                    "nextWindow": str(item.get("nextWindow", "")).strip(),
                    "risk": str(item.get("risk", "")).strip(),
                }
            )
        normalized["arcs"] = deduped
        return normalized

    def _normalize_foreshadow_payload(self, payload: dict[str, object], schema_dir: Path) -> dict[str, object]:
        normalized = dict(payload)
        threads = normalized.get("threads", [])
        if not isinstance(threads, list):
            threads = []
        deduped: list[dict[str, object]] = []
        seen_ids: set[str] = set()
        for item in threads:
            if not isinstance(item, dict):
                continue
            identifier = str(item.get("id", "")).strip()
            content = str(item.get("content", "")).strip()
            if not identifier or not content or identifier in seen_ids:
                continue
            seen_ids.add(identifier)
            deduped.append(
                {
                    "id": identifier,
                    "seed_chapter": max(0, int(item.get("seed_chapter", 0) or 0)),
                    "content": content,
                    "who_knows": str(item.get("who_knows", "")).strip(),
                    "trigger_condition": str(item.get("trigger_condition", "")).strip(),
                    "invalid_condition": str(item.get("invalid_condition", "")).strip(),
                    "due_chapter": item.get("due_chapter"),
                    "last_reminder_chapter": item.get("last_reminder_chapter"),
                    "reader_memory_heat": str(item.get("reader_memory_heat", "unknown") or "unknown"),
                    "payoff_type": str(item.get("payoff_type", "unknown") or "unknown"),
                    "status": str(item.get("status", "active") or "active"),
                }
            )
        normalized["threads"] = deduped
        return normalized

    def _extract_line_value(self, text: str, label: str) -> str:
        prefix = f"- {label}："
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if line.startswith(prefix):
                return line[len(prefix):].strip()
        return ""

    def _slug(self, text: str) -> str:
        return "".join(char.lower() if char.isalnum() else "-" for char in text).strip("-") or "item"

    def _build_plan_patch(self, project_dir: Path, schema_dir: Path) -> MemoryPatch:
        plan_path = schema_dir / "plan.json"
        before = self._load_json(plan_path)
        after = dict(before)
        plan_text = read_text(project_dir / "00_memory" / "plan.md")
        title = self._extract_line_value(plan_text, "书名")
        genre = self._extract_line_value(plan_text, "题材")
        hook = self._extract_line_value(plan_text, "核心卖点") or self._extract_line_value(plan_text, "核心卖点（一句话）")
        target_words_raw = self._extract_line_value(plan_text, "预计总字数")
        target_words = int("".join(char for char in target_words_raw if char.isdigit()) or "0")
        if title:
            after["title"] = title
        if genre:
            after["genre"] = genre
        if hook:
            after["hook"] = hook
        derived_target_words = derive_plan_target_words(plan_text)
        if target_words or derived_target_words:
            after["targetWords"] = target_words or derived_target_words
        volumes = parse_plan_volumes(plan_text)
        if volumes:
            after["volumes"] = volumes
        after = self._normalize_plan_payload(after, schema_dir)
        return MemoryPatch(schema_file=plan_path.as_posix(), before=before, after=after)

    def _build_characters_patch(self, project_dir: Path, schema_dir: Path) -> MemoryPatch:
        characters_path = schema_dir / "characters.json"
        before = self._load_json(characters_path)
        after = dict(before)
        characters_text = read_text(project_dir / "00_memory" / "characters.md")
        characters: list[dict[str, object]] = []
        current_role = ""
        for raw_line in characters_text.splitlines():
            line = raw_line.strip()
            if line.startswith("## "):
                current_role = line.removeprefix("## ").strip()
                continue
            if not line.startswith("- "):
                continue
            content = line[2:].strip()
            if not content:
                continue
            if "：" in content:
                left, _, right = content.partition("：")
                left = left.strip()
                right = right.strip()
                if left in {"姓名", "name", "Name"}:
                    name = right
                    role = current_role
                else:
                    name = left
                    role = right or current_role
            else:
                name = content
                role = current_role
            name = name.strip()
            if not name:
                continue
            characters.append(
                {
                    "id": self._slug(name),
                    "name": name,
                    "role": role,
                    "voiceTraits": [],
                }
            )
        after["characters"] = characters
        after = self._normalize_characters_payload(after, schema_dir)
        return MemoryPatch(schema_file=characters_path.as_posix(), before=before, after=after)

    def _build_runtime_character_arcs(self, draft_payload: dict[str, object]) -> list[dict[str, object]]:
        constraints = draft_payload.get("character_constraints", {})
        outcome_signature = draft_payload.get("outcome_signature", {})
        if not isinstance(constraints, dict) or not isinstance(outcome_signature, dict):
            return []

        chapter_result = str(outcome_signature.get("chapter_result", "")).strip()
        next_pull = str(outcome_signature.get("next_pull", "")).strip()
        result_type = str(outcome_signature.get("result_type", "")).strip()
        hook_type = str(outcome_signature.get("hook_type", "")).strip()
        if not chapter_result:
            return []

        protagonist = constraints.get("protagonist", {})
        counterpart = constraints.get("counterpart", {})
        if not isinstance(protagonist, dict) or not isinstance(counterpart, dict):
            return []

        stage = hook_type or result_type or "runtime_progress"
        protagonist_name = str(protagonist.get("name", "")).strip()
        counterpart_name = str(counterpart.get("name", "")).strip()
        protagonist_goal = str(constraints.get("protagonist_goal", "")).strip()
        protagonist_taboo = str(constraints.get("protagonist_taboo", "")).strip()
        counterpart_goal = str(constraints.get("counterpart_goal", "")).strip()
        counterpart_fear = str(constraints.get("counterpart_fear", "")).strip()

        runtime_arcs: list[dict[str, object]] = []
        if protagonist_name:
            runtime_arcs.append(
                {
                    "character": protagonist_name,
                    "arcType": "runtime_protagonist",
                    "stage": stage,
                    "goal": protagonist_goal,
                    "blocker": protagonist_taboo,
                    "recentChange": chapter_result,
                    "nextWindow": next_pull,
                    "risk": "",
                }
            )
        if counterpart_name:
            runtime_arcs.append(
                {
                    "character": counterpart_name,
                    "arcType": "runtime_counterpart",
                    "stage": stage,
                    "goal": counterpart_goal,
                    "blocker": counterpart_fear,
                    "recentChange": chapter_result,
                    "nextWindow": next_pull,
                    "risk": "",
                }
            )
        return runtime_arcs

    def _build_character_arcs_patch(
        self,
        project_dir: Path,
        schema_dir: Path,
        draft_payload: dict[str, object] | None = None,
    ) -> MemoryPatch:
        arcs_path = schema_dir / "character_arcs.json"
        before = self._load_json(arcs_path)
        after = dict(before)
        arcs_text = read_text(project_dir / "00_memory" / "character_arcs.md")
        rows = extract_markdown_table_rows(arcs_text, "核心角色弧表")
        arcs: list[dict[str, object]] = []
        for row in rows[1:]:
            if len(row) < 4:
                continue
            character_name = row[0].strip()
            if not character_name:
                continue
            arcs.append(
                {
                    "character": character_name,
                    "arcType": row[1].strip(),
                    "stage": row[2].strip(),
                    "goal": row[3].strip() if len(row) > 3 else "",
                    "blocker": row[4].strip() if len(row) > 4 else "",
                    "recentChange": row[5].strip() if len(row) > 5 else "",
                    "nextWindow": row[6].strip() if len(row) > 6 else "",
                    "risk": row[7].strip() if len(row) > 7 else "",
                }
            )
        if not arcs and isinstance(draft_payload, dict):
            arcs = self._build_runtime_character_arcs(draft_payload)
        after["arcs"] = arcs
        after = self._normalize_character_arcs_payload(after, schema_dir)
        return MemoryPatch(schema_file=arcs_path.as_posix(), before=before, after=after)

    def _build_foreshadow_patch(self, project_dir: Path, schema_dir: Path, chapter: int) -> MemoryPatch:
        foreshadow_path = schema_dir / "foreshadowing.json"
        before = self._load_json(foreshadow_path)
        after = dict(before)
        foreshadow_text = read_text(project_dir / "00_memory" / "foreshadowing.md")
        rows = extract_markdown_table_rows(foreshadow_text, "活跃伏笔")
        if not rows:
            rows = extract_markdown_table_rows(foreshadow_text, "📌 未回收伏笔 (Pending)")
        threads: list[dict[str, object]] = []
        for index, row in enumerate(rows[1:], start=1):
            if len(row) < 1:
                continue
            content = row[0].strip()
            if not content:
                continue
            threads.append(
                {
                    "id": f"foreshadow:{self._slug(content)}",
                    "seed_chapter": chapter,
                    "content": content,
                    "who_knows": "",
                    "trigger_condition": row[1].strip() if len(row) > 1 else "",
                    "invalid_condition": row[2].strip() if len(row) > 2 else "",
                    "due_chapter": None,
                    "last_reminder_chapter": None,
                    "reader_memory_heat": "unknown",
                    "payoff_type": "unknown",
                    "status": "active",
                }
            )
        after["threads"] = threads
        after = self._normalize_foreshadow_payload(after, schema_dir)
        return MemoryPatch(schema_file=foreshadow_path.as_posix(), before=before, after=after)

    def _dump_json(self, path: Path, payload: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _build_state_patch(
        self,
        schema_dir: Path,
        packet: ChapterContextPacket,
        brief: ChapterBrief,
        decision: RuntimeDecision,
    ) -> MemoryPatch:
        state_path = schema_dir / "state.json"
        before = self._load_json(state_path)
        after = dict(before)
        after["currentChapter"] = packet.chapter
        after["currentVolume"] = packet.active_volume
        after["currentArc"] = packet.active_arc
        after["chapterGoal"] = brief.chapter_function
        after["openThreads"] = self._dedupe_strings([*brief.allowed_threads, *packet.open_threads])
        after["forbiddenInventions"] = self._dedupe_strings([*brief.disallowed_moves, *packet.forbidden_inventions])
        after["pendingPayoffs"] = self._dedupe_strings([*brief.must_advance, *brief.allowed_threads])
        after["sceneAnchors"] = {
            **(after.get("sceneAnchors", {}) if isinstance(after.get("sceneAnchors"), dict) else {}),
            "location": packet.current_place,
        }
        after["runtimeDecision"] = decision.decision
        after["runtimeBlockingDimensions"] = decision.blocking_dimensions
        # 运行时回写只持久化阻断维度；告警维度保留在当次 payload，不写入 state，避免历史噪音持续污染仪表盘。
        after["runtimeAdvisoryDimensions"] = []
        after = self._normalize_state_payload(after, schema_dir)
        return MemoryPatch(schema_file=state_path.as_posix(), before=before, after=after)

    def _build_timeline_patch(self, schema_dir: Path, packet: ChapterContextPacket) -> MemoryPatch:
        timeline_path = schema_dir / "timeline.json"
        before = self._load_json(timeline_path)
        after = dict(before)
        if packet.current_place:
            after["currentLocation"] = packet.current_place
        recent_events = after.get("recentEvents", [])
        if not isinstance(recent_events, list):
            recent_events = []
        marker = f"chapter-{packet.chapter}: {packet.next_goal}"
        if packet.chapter > 0 and marker not in recent_events:
            recent_events = [*recent_events, marker][-8:]
        after["recentEvents"] = recent_events
        after = self._normalize_timeline_payload(after, schema_dir)
        return MemoryPatch(schema_file=timeline_path.as_posix(), before=before, after=after)

    def _handle_volume_transition(
        self,
        project_dir: Path,
        packet: ChapterContextPacket,
        retrieval_dir: Path,
    ) -> None:
        if not packet.is_volume_start and not packet.is_volume_end:
            return

        transitions_dir = project_dir / "00_memory" / "volume_transitions"
        transitions_dir.mkdir(parents=True, exist_ok=True)

        if packet.is_volume_start and packet.chapter > 1:
            lines = [
                "# Volume Transition Event",
                "",
                f"- chapter: {packet.chapter}",
                f"- event: volume_start",
                f"- volume: {packet.volume_name}",
                f"- note: 进入新卷，优先从 plan.md 卷纲和 volume-blueprint.md 拉取卷级承诺。",
            ]
            if packet.volume_promises:
                lines.append("- promises_to_fulfill:")
                lines.extend(f"  - {p}" for p in packet.volume_promises)
            event_path = transitions_dir / f"ch{packet.chapter:03d}_volume_start.md"
            event_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        if packet.is_volume_end:
            lines = [
                "# Volume Transition Event",
                "",
                f"- chapter: {packet.chapter}",
                f"- event: volume_end",
                f"- volume: {packet.volume_name}",
                f"- note: 本卷结束，确保卷级承诺已兑现或显式延期。下卷交接清单：",
            ]
            if packet.volume_handoff:
                lines.extend(f"- handoff: {h}" for h in packet.volume_handoff)
            event_path = transitions_dir / f"ch{packet.chapter:03d}_volume_end.md"
            event_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _build_payoff_patch(self, schema_dir: Path, brief: ChapterBrief) -> MemoryPatch:
        payoff_path = schema_dir / "payoff_board.json"
        before = self._load_json(payoff_path)
        after = dict(before)
        promises = after.get("promises", [])
        if not isinstance(promises, list):
            promises = []
        for thread in self._dedupe_strings([*brief.must_advance, *brief.allowed_threads]):
            promise_id = f"thread:{thread}"
            existing = next(
                (item for item in promises if isinstance(item, dict) and str(item.get("promiseId", "")).strip() == promise_id),
                None,
            )
            if existing is not None:
                existing["readerExpectation"] = thread
                existing["promiseType"] = str(existing.get("promiseType", "open_thread") or "open_thread")
                existing["status"] = str(existing.get("status", "pending") or "pending")
                continue
            promises.append(
                {
                    "promiseId": promise_id,
                    "promiseType": "open_thread",
                    "readerExpectation": thread,
                    "status": "pending",
                }
            )
        for item in self._dedupe_strings(brief.required_payoff_or_pressure):
            promise_id = f"runtime:{item}"
            existing = next(
                (entry for entry in promises if isinstance(entry, dict) and str(entry.get("promiseId", "")).strip() == promise_id),
                None,
            )
            if existing is not None:
                existing["readerExpectation"] = item
                existing["promiseType"] = str(existing.get("promiseType", "runtime_pressure") or "runtime_pressure")
                existing["status"] = str(existing.get("status", "pending") or "pending")
                continue
            promises.append(
                {
                    "promiseId": promise_id,
                    "promiseType": "runtime_pressure",
                    "readerExpectation": item,
                    "status": "pending",
                }
            )
        after["promises"] = promises
        after = self._normalize_payoff_payload(after, schema_dir)
        return MemoryPatch(schema_file=payoff_path.as_posix(), before=before, after=after)

    def _expectation_entry_from_runtime(
        self,
        packet: ChapterContextPacket,
        brief: ChapterBrief,
        decision: RuntimeDecision,
        verdicts: list[EvaluatorVerdict],
        draft_payload: dict[str, object] | None,
    ) -> dict[str, object]:
        scene_beat_plan = draft_payload.get("scene_beat_plan", {}) if isinstance(draft_payload, dict) else {}
        beats = scene_beat_plan.get("beats", []) if isinstance(scene_beat_plan, dict) else []
        outcome_signature = draft_payload.get("outcome_signature", {}) if isinstance(draft_payload, dict) else {}
        outcome_signature = outcome_signature if isinstance(outcome_signature, dict) else {}

        short_expectations: list[object] = []
        long_expectations: list[object] = []
        expectation_payoffs: list[object] = []
        new_expectations: list[object] = []
        gap_risks: list[object] = []
        genre_hints: list[object] = []
        for beat in beats:
            if not isinstance(beat, dict):
                continue
            short_expectations.append(beat.get("short_expectation", ""))
            long_expectations.append(beat.get("long_expectation", ""))
            expectation_payoffs.append(beat.get("expectation_payoff", ""))
            new_expectations.append(beat.get("new_expectation", ""))
            gap_risks.append(beat.get("expectation_gap_risk", ""))
            genre_hints.append(beat.get("genre_framework_hint", ""))

        if not short_expectations:
            short_expectations.extend([brief.core_conflict, brief.hook_goal])
        if not long_expectations:
            long_expectations.extend([*brief.allowed_threads, *packet.open_threads, *packet.pending_promises])
        if not new_expectations:
            new_expectations.extend([brief.closing_hook, brief.hook_goal, str(outcome_signature.get("next_pull", ""))])
        if not expectation_payoffs:
            expectation_payoffs.extend([brief.result_change, str(outcome_signature.get("chapter_result", ""))])

        tracked_dimensions = {
            "expectation_integrity",
            "opening_diagnostics",
            "genre_framework_fit",
            "hook_integrity",
            "market_fit",
            "pre_publish_checklist",
            "prose_concreteness",
        }
        blocking_dimensions = [
            item.dimension for item in verdicts if item.blocking and item.dimension in tracked_dimensions
        ]
        advisory_dimensions = [
            item.dimension for item in verdicts if item.status == "warn" and item.dimension in tracked_dimensions
        ]
        for verdict in verdicts:
            if verdict.dimension in {"expectation_integrity", "opening_diagnostics", "genre_framework_fit", "hook_integrity"}:
                gap_risks.extend(verdict.evidence)

        return {
            "chapter": packet.chapter,
            "shortExpectations": self._dedupe_strings(short_expectations),
            "longExpectations": self._dedupe_strings(long_expectations),
            "expectationPayoffs": self._dedupe_strings(expectation_payoffs),
            "newExpectations": self._dedupe_strings(new_expectations),
            "expectationGapRisks": self._dedupe_strings(gap_risks),
            "genreFrameworkHints": self._dedupe_strings(genre_hints),
            "readerHook": str(outcome_signature.get("next_pull", "") or brief.closing_hook or brief.hook_goal).strip(),
            "chapterResult": str(outcome_signature.get("chapter_result", "") or brief.result_change).strip(),
            "releaseDecision": decision.decision,
            "blockingDimensions": self._dedupe_strings(blocking_dimensions),
            "advisoryDimensions": self._dedupe_strings(advisory_dimensions),
        }

    def _build_expectation_tracking_patch(
        self,
        schema_dir: Path,
        packet: ChapterContextPacket,
        brief: ChapterBrief,
        decision: RuntimeDecision,
        verdicts: list[EvaluatorVerdict],
        draft_payload: dict[str, object] | None,
    ) -> MemoryPatch:
        tracking_path = schema_dir / "expectation_tracking.json"
        before = self._load_json(tracking_path)
        after = dict(before)
        chapters = after.get("chapters", [])
        if not isinstance(chapters, list):
            chapters = []
        entry = self._expectation_entry_from_runtime(packet, brief, decision, verdicts, draft_payload)
        chapters = [item for item in chapters if not (isinstance(item, dict) and int(item.get("chapter", -1) or -1) == packet.chapter)]
        chapters.append(entry)
        after["chapters"] = chapters
        after = self._normalize_expectation_tracking_payload(after)
        return MemoryPatch(schema_file=tracking_path.as_posix(), before=before, after=after)

    def _write_expectation_tracking_report(self, retrieval_dir: Path, expectation_patch: MemoryPatch) -> dict[str, str]:
        md_path = retrieval_dir / "expectation_tracking.md"
        json_path = retrieval_dir / "expectation_tracking.latest.json"
        latest = {}
        chapters = expectation_patch.after.get("chapters", [])
        if isinstance(chapters, list) and chapters:
            latest = chapters[-1] if isinstance(chapters[-1], dict) else {}
        json_path.write_text(json.dumps(latest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        lines = [
            "# Expectation Tracking",
            "",
            f"- chapter: {latest.get('chapter', 'missing')}",
            f"- release_decision: {latest.get('releaseDecision', 'missing')}",
            f"- chapter_result: {latest.get('chapterResult', '') or 'missing'}",
            f"- reader_hook: {latest.get('readerHook', '') or 'missing'}",
            "",
            "## Short Expectations",
        ]
        lines.extend(f"- {item}" for item in latest.get("shortExpectations", []) or ["none"])
        lines.extend(["", "## Long Expectations"])
        lines.extend(f"- {item}" for item in latest.get("longExpectations", []) or ["none"])
        lines.extend(["", "## Payoffs"])
        lines.extend(f"- {item}" for item in latest.get("expectationPayoffs", []) or ["none"])
        lines.extend(["", "## New Expectations"])
        lines.extend(f"- {item}" for item in latest.get("newExpectations", []) or ["none"])
        lines.extend(["", "## Gap Risks"])
        lines.extend(f"- {item}" for item in latest.get("expectationGapRisks", []) or ["none"])
        lines.extend(["", "## Genre Framework Hints"])
        lines.extend(f"- {item}" for item in latest.get("genreFrameworkHints", []) or ["none"])
        lines.extend(["", "## Watch Dimensions"])
        lines.append(f"- blocking: {', '.join(latest.get('blockingDimensions', []) or []) or 'none'}")
        lines.append(f"- advisory: {', '.join(latest.get('advisoryDimensions', []) or []) or 'none'}")
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {
            "expectation_tracking_markdown": md_path.as_posix(),
            "expectation_tracking_latest_json": json_path.as_posix(),
        }

    def _changed_keys(self, patch: MemoryPatch) -> list[str]:
        return sorted(
            {
                key
                for key in set(patch.before) | set(patch.after)
                if patch.before.get(key) != patch.after.get(key)
            }
        )

    def _write_patch_files(self, retrieval_dir: Path, patches: list[MemoryPatch]) -> dict[str, str]:
        patches_json_path = retrieval_dir / "leadwriter_memory_patches.json"
        patches_md_path = retrieval_dir / "leadwriter_memory_patches.md"
        patches_json_path.write_text(
            json.dumps([item.to_dict() for item in patches], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        lines = ["# LeadWriter Memory Patches", ""]
        for patch in patches:
            changed = self._changed_keys(patch)
            lines.extend(
                [
                    f"## {Path(patch.schema_file).name}",
                    f"- changed_keys: {', '.join(changed) if changed else 'none'}",
                    "",
                ]
            )
        patches_md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {
            "json": patches_json_path.as_posix(),
            "markdown": patches_md_path.as_posix(),
        }

    def _apply_patches(self, patches: list[MemoryPatch], apply_changes: bool) -> list[dict[str, object]]:
        results: list[dict[str, object]] = []
        for patch in patches:
            path = Path(patch.schema_file)
            changed_keys = self._changed_keys(patch)
            status = "skipped"
            if changed_keys and apply_changes:
                self._dump_json(path, patch.after)
                status = "applied"
            elif changed_keys:
                status = "ready"
            results.append(
                {
                    "schema_file": path.as_posix(),
                    "status": status,
                    "changed_keys": changed_keys,
                }
            )
        return results

    def _write_apply_report(self, retrieval_dir: Path, apply_results: list[dict[str, object]]) -> dict[str, str]:
        report_json = retrieval_dir / "leadwriter_memory_apply.json"
        report_md = retrieval_dir / "leadwriter_memory_apply.md"
        report_json.write_text(json.dumps(apply_results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        lines = ["# LeadWriter Memory Apply", ""]
        for item in apply_results:
            lines.append(
                f"- {Path(str(item['schema_file'])).name}: status={item['status']} / changed_keys="
                f"{', '.join(item['changed_keys']) if item['changed_keys'] else 'none'}"
            )
        report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {"json": report_json.as_posix(), "markdown": report_md.as_posix()}

    def summarize(
        self,
        project_dir: Path,
        packet: ChapterContextPacket,
        brief: ChapterBrief,
        decision: RuntimeDecision,
        verdicts: list[EvaluatorVerdict],
        *,
        draft_payload: dict[str, object] | None = None,
        apply_changes: bool,
    ) -> dict[str, object]:
        retrieval_dir = project_dir / "00_memory" / "retrieval"
        retrieval_dir.mkdir(parents=True, exist_ok=True)
        summary_path = retrieval_dir / "leadwriter_runtime_summary.md"
        schema_dir = project_dir / "00_memory" / "schema"

        expectation_patch = self._build_expectation_tracking_patch(
            schema_dir,
            packet,
            brief,
            decision,
            verdicts,
            draft_payload,
        )
        patches = [
            self._build_plan_patch(project_dir, schema_dir),
            self._build_state_patch(schema_dir, packet, brief, decision),
            self._build_timeline_patch(schema_dir, packet),
            self._build_characters_patch(project_dir, schema_dir),
            self._build_character_arcs_patch(project_dir, schema_dir, draft_payload=draft_payload),
            self._build_foreshadow_patch(project_dir, schema_dir, packet.chapter),
            self._build_payoff_patch(schema_dir, brief),
            expectation_patch,
        ]
        self._handle_volume_transition(project_dir, packet, retrieval_dir)
        patch_paths = self._write_patch_files(retrieval_dir, patches)
        apply_results = self._apply_patches(patches, apply_changes=apply_changes)
        apply_paths = self._write_apply_report(retrieval_dir, apply_results)
        expectation_paths = self._write_expectation_tracking_report(retrieval_dir, expectation_patch)

        lines = [
            "# LeadWriter Runtime Summary",
            "",
            f"- chapter: {packet.chapter}",
            f"- active_volume: {packet.active_volume}",
            f"- active_arc: {packet.active_arc}",
            f"- current_place: {packet.current_place}",
            f"- chapter_function: {brief.chapter_function}",
            f"- hook_goal: {brief.hook_goal}",
            f"- required_payoff_or_pressure: {', '.join(brief.required_payoff_or_pressure) if brief.required_payoff_or_pressure else 'none'}",
            f"- runtime_decision: {decision.decision}",
            f"- blocking_dimensions: {', '.join(decision.blocking_dimensions) if decision.blocking_dimensions else 'none'}",
            f"- advisory_dimensions: {', '.join(decision.advisory_dimensions) if decision.advisory_dimensions else 'none'}",
            f"- apply_changes: {'yes' if apply_changes else 'no'}",
            "",
            "## Scene Plan",
        ]
        if brief.scene_plan:
            lines.extend(f"- {item}" for item in brief.scene_plan)
        else:
            lines.append("- none")
        lines.extend(
            [
                "",
                "## Expectation Tracking",
                f"- expectation_tracking_markdown: {expectation_paths['expectation_tracking_markdown']}",
                f"- expectation_tracking_latest_json: {expectation_paths['expectation_tracking_latest_json']}",
                "",
                "## Success Criteria",
            ]
        )
        if brief.success_criteria:
            lines.extend(f"- {item}" for item in brief.success_criteria)
        else:
            lines.append("- none")
        lines.extend(
            [
                "",
            "## Verdicts",
            ]
        )
        if verdicts:
            for verdict in verdicts:
                lines.append(
                    f"- {verdict.dimension}: status={verdict.status} / blocking={'yes' if verdict.blocking else 'no'}"
                )
        else:
            lines.append("- none")
        lines.extend(
            [
                "",
                "## Memory Patch Outputs",
                f"- patch_markdown: {patch_paths['markdown']}",
                f"- patch_json: {patch_paths['json']}",
                f"- apply_markdown: {apply_paths['markdown']}",
                f"- apply_json: {apply_paths['json']}",
            ]
        )
        summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {
            "markdown": summary_path.as_posix(),
            "memory_patch_markdown": patch_paths["markdown"],
            "memory_patch_json": patch_paths["json"],
            "memory_apply_markdown": apply_paths["markdown"],
            "memory_apply_json": apply_paths["json"],
            **expectation_paths,
        }
