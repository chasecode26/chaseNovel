from __future__ import annotations

import json
from pathlib import Path

from runtime.script_imports import ensure_scripts_on_path

ensure_scripts_on_path()

import re as _re

from runtime.contracts import ChapterContextPacket
from novel_utils import chapter_number_from_name, extract_line, extract_state_value, has_placeholder, parse_plan_volumes, read_text


class MemoryCompiler:
    def _load_json(self, path: Path) -> dict[str, object]:
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _extract_present_line(self, text: str, label: str) -> str:
        value = extract_line(text, label)
        return "" if has_placeholder(value) else value

    def _parse_heading_value(self, text: str, labels: list[str]) -> str:
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line.startswith("-"):
                continue
            body = line[1:].strip()
            for label in labels:
                prefix_a = f"{label}:"
                prefix_b = f"{label}："
                if body.startswith(prefix_a):
                    value = body[len(prefix_a):].strip()
                elif body.startswith(prefix_b):
                    value = body[len(prefix_b):].strip()
                else:
                    continue
                if value and not has_placeholder(value):
                    return value
        return ""

    def _find_chapter_card_path(self, project_dir: Path, chapter: int) -> Path | None:
        candidate_dirs = [
            project_dir / "01_outline",
            project_dir / "01_outline" / "chapter_cards",
            project_dir / "01_outline" / "chapters",
            project_dir / "00_memory",
            project_dir / "00_memory" / "chapter_cards",
            project_dir / "00_memory" / "plans",
            project_dir / "04_gate" / f"ch{chapter:03d}",
        ]
        candidate_names = {
            f"第{chapter:03d}章.md",
            f"第{chapter}章.md",
            f"ch{chapter:03d}.md",
            f"chapter-{chapter:03d}.md",
            f"chapter_{chapter:03d}.md",
            f"plan-{chapter:03d}.md",
            f"plan_{chapter:03d}.md",
        }
        candidate_names_lower = {name.lower() for name in candidate_names}

        for base_dir in candidate_dirs:
            if not base_dir.exists():
                continue
            for path in base_dir.rglob("*.md"):
                lowered = path.name.lower()
                if path.name in candidate_names or lowered in candidate_names_lower:
                    return path
                if any(token in lowered for token in ("章卡", "chapter", "plan")):
                    chapter_no = chapter_number_from_name(path.stem)
                    if chapter_no == chapter:
                        return path
        return None

    def _parse_chapter_card(self, card_text: str) -> dict[str, str]:
        return {
            "time_anchor": self._parse_heading_value(card_text, ["time_anchor", "本章时间", "时间锚点"]),
            "location_anchor": self._parse_heading_value(card_text, ["location_anchor", "本章地点", "地点锚点"]),
            "present_characters": self._parse_heading_value(card_text, ["present_characters", "在场人物"]),
            "knowledge_boundary": self._parse_heading_value(card_text, ["knowledge_boundary", "知情边界"]),
            "message_flow": self._parse_heading_value(card_text, ["message_flow", "消息传播链", "消息传播"]),
            "arrival_timing": self._parse_heading_value(card_text, ["arrival_timing", "最早送达时间", "消息送达时点"]),
            "who_knows_now": self._parse_heading_value(card_text, ["who_knows_now", "谁现在能知道", "当前知情人"]),
            "who_cannot_know_yet": self._parse_heading_value(card_text, ["who_cannot_know_yet", "谁按理还不能知道", "当前不应知情人"]),
            "travel_time_floor": self._parse_heading_value(card_text, ["travel_time_floor", "路程至少多久", "最短路程时间"]),
            "resource_state": self._parse_heading_value(card_text, ["resource_state", "资源状态"]),
            "progress_floor": self._parse_heading_value(card_text, ["progress_floor", "本章至少推进到哪里", "本章推进下限"]),
            "progress_ceiling": self._parse_heading_value(card_text, ["progress_ceiling", "本章最多只能推进到哪里", "本章推进上限"]),
            "must_not_payoff_yet": self._parse_heading_value(card_text, ["must_not_payoff_yet", "本章不能提前兑现", "本章禁止提前兑现"]),
            "allowed_change_scope": self._parse_heading_value(card_text, ["allowed_change_scope", "本章允许变化范围", "允许变化层级"]),
            "open_threads": self._parse_heading_value(card_text, ["open_threads", "开放线索", "开放线程"]),
            "forbidden_inventions": self._parse_heading_value(card_text, ["forbidden_inventions", "禁止发明"]),
            "chapter_goal": self._parse_heading_value(card_text, ["chapter_goal", "本章目标"]),
        }

    def _split_list_field(self, value: str) -> list[str]:
        if not value:
            return []
        normalized = value.replace("；", "，").replace(";", "，").replace("/", "，")
        return [item.strip() for item in normalized.split("，") if item.strip()]

    def _resolve_volume_info(self, project_dir: Path, chapter: int) -> dict[str, object]:
        plan_text = read_text(project_dir / "00_memory" / "plan.md")
        volumes = parse_plan_volumes(plan_text)
        result: dict[str, object] = {
            "is_volume_start": False,
            "is_volume_end": False,
            "volume_name": "",
            "volume_promises": [],
            "volume_handoff": [],
        }
        if not volumes:
            return result

        current_volume = None
        for vol in volumes:
            start = int(vol.get("chapterStart", 0))
            end = int(vol.get("chapterEnd", 0))
            if start <= chapter <= end:
                current_volume = vol
                break

        if current_volume is None:
            return result

        result["volume_name"] = str(current_volume.get("name", ""))
        result["is_volume_start"] = chapter == int(current_volume.get("chapterStart", 0))
        result["is_volume_end"] = chapter == int(current_volume.get("chapterEnd", 0))

        # 下一卷的第一章视同 volume_end 的 handoff 目标
        next_volume = None
        if not result["is_volume_end"]:
            for vol in volumes:
                if int(vol.get("chapterStart", 0)) == chapter + 1:
                    next_volume = vol
                    break
            if next_volume is not None:
                result["is_volume_end"] = True

        # 当前章节是前一卷最后一章+1 → 卷开始
        if not result["is_volume_start"] and chapter > 1:
            for vol in volumes:
                if int(vol.get("chapterEnd", 0)) == chapter - 1:
                    result["is_volume_start"] = True
                    break

        vol_index = current_volume.get("index", 0)
        blueprint_paths = [
            project_dir / "00_memory" / "volumes" / f"volume-{int(vol_index):02d}-blueprint.md",
            project_dir / "00_memory" / f"volume-{int(vol_index):02d}-blueprint.md",
        ]
        blueprint_path: Path | None = None
        for bp in blueprint_paths:
            if bp.exists():
                blueprint_path = bp
                break

        if blueprint_path is not None:
            blueprint_text = read_text(blueprint_path)
            core_section = _re.search(r"核心任务[\s\S]*?(?=##|\Z)", blueprint_text)
            if core_section:
                result["volume_promises"] = [
                    item.strip()
                    for item in _re.findall(r"[-*]\s*(.+)", core_section.group(0))
                    if item.strip()
                ]
            handoff_section = _re.search(r"跨卷交接[\s\S]*?(?=##|\Z)", blueprint_text)
            if handoff_section:
                result["volume_handoff"] = [
                    item.strip()
                    for item in _re.findall(r"[-*]\s*(.+)", handoff_section.group(0))
                    if item.strip()
                ]

        return result

    def build(self, project_dir: Path, chapter: int) -> ChapterContextPacket:
        schema_dir = project_dir / "00_memory" / "schema"
        state = self._load_json(schema_dir / "state.json")
        voice = self._load_json(schema_dir / "voice.json")
        state_text = read_text(project_dir / "00_memory" / "state.md")

        chapter_card_path = self._find_chapter_card_path(project_dir, chapter)
        chapter_card_text = read_text(chapter_card_path) if chapter_card_path else ""
        chapter_card = self._parse_chapter_card(chapter_card_text) if chapter_card_text else {}

        anchors = state.get("sceneAnchors", {})
        current_place = ""
        time_anchor = ""
        if isinstance(anchors, dict):
            current_place = str(anchors.get("location", "")).strip()
            time_anchor = str(anchors.get("time", "")).strip()

        location_anchor = chapter_card.get("location_anchor", "") or current_place or extract_state_value(state_text, "当前地点") or "未识别"
        current_place = location_anchor
        time_anchor = chapter_card.get("time_anchor", "") or time_anchor or self._extract_present_line(state_text, "- 当前绝对时间") or extract_state_value(state_text, "当前绝对时间") or "未识别"

        next_goal = (
            chapter_card.get("chapter_goal", "")
            or str(state.get("chapterGoal", "")).strip()
            or extract_state_value(state_text, "计划内容")
            or "待明确"
        )
        current_volume = str(state.get("currentVolume", "")).strip() or extract_state_value(state_text, "当前卷") or "未识别"
        current_arc = str(state.get("currentArc", "")).strip() or extract_state_value(state_text, "当前弧") or "未识别"

        open_threads = [str(item) for item in state.get("openThreads", []) if str(item).strip()]
        if not open_threads:
            open_threads = self._split_list_field(chapter_card.get("open_threads", ""))

        forbidden = [str(item) for item in state.get("forbiddenInventions", []) if str(item).strip()]
        if not forbidden:
            forbidden = self._split_list_field(chapter_card.get("forbidden_inventions", ""))

        must_not_payoff_yet = self._split_list_field(chapter_card.get("must_not_payoff_yet", ""))
        allowed_change_scope = self._split_list_field(chapter_card.get("allowed_change_scope", ""))
        present_characters = self._split_list_field(chapter_card.get("present_characters", ""))
        voice_rules = [str(item) for item in voice.get("forbiddenCadence", []) if str(item).strip()]

        packet = ChapterContextPacket(
            project=project_dir.as_posix(),
            chapter=chapter,
            active_volume=current_volume,
            active_arc=current_arc,
            time_anchor=time_anchor,
            current_place=current_place,
            location_anchor=location_anchor,
            next_goal=next_goal,
            present_characters=present_characters,
            knowledge_boundary=chapter_card.get("knowledge_boundary", ""),
            message_flow=chapter_card.get("message_flow", ""),
            arrival_timing=chapter_card.get("arrival_timing", ""),
            who_knows_now=chapter_card.get("who_knows_now", ""),
            who_cannot_know_yet=chapter_card.get("who_cannot_know_yet", ""),
            travel_time_floor=chapter_card.get("travel_time_floor", ""),
            resource_state=chapter_card.get("resource_state", ""),
            progress_floor=chapter_card.get("progress_floor", ""),
            progress_ceiling=chapter_card.get("progress_ceiling", ""),
            must_not_payoff_yet=must_not_payoff_yet,
            allowed_change_scope=allowed_change_scope,
            open_threads=open_threads,
            forbidden_inventions=forbidden,
            voice_rules=voice_rules,
        )

        volume_info = self._resolve_volume_info(project_dir, chapter)
        return ChapterContextPacket(**{**packet.to_dict(), **{k: v for k, v in volume_info.items() if v}})
