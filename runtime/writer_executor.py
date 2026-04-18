from __future__ import annotations

from pathlib import Path

from runtime.contracts import ChapterBrief, ChapterContextPacket, RuntimeDecision
from scripts.novel_utils import read_text


class WriterExecutor:
    def _genre_profile(self, project_dir: Path) -> dict[str, str]:
        plan_text = read_text(project_dir / "00_memory" / "plan.md")
        if "都市" in plan_text and "系统" in plan_text:
            return {
                "genre": "urban_system",
                "pressure_noun": "价码",
                "win_noun": "主动权",
                "hook_phrase": "下一步的价码被系统重新抬高",
            }
        if "末世" in plan_text:
            return {
                "genre": "apocalypse",
                "pressure_noun": "生存代价",
                "win_noun": "生存位",
                "hook_phrase": "下一步的代价会直接吃掉生存余量",
            }
        return {
            "genre": "default",
            "pressure_noun": "代价",
            "win_noun": "主动权",
            "hook_phrase": "下一步的代价被正式抬高",
        }

    def _draft_dir(self, project_dir: Path, chapter: int) -> Path:
        return project_dir / "04_gate" / f"ch{chapter:03d}"

    def _chapter_title(self, brief: ChapterBrief) -> str:
        title = brief.chapter_function.strip() or "推进当前章节目标"
        return title[:32]

    def _extract_bullet_value(self, line: str) -> tuple[str, str] | None:
        stripped = line.strip()
        if not stripped.startswith("- "):
            return None
        payload = stripped[2:]
        for separator in ("：", ":"):
            if separator in payload:
                key, value = payload.split(separator, 1)
                return key.strip(), value.strip()
        return None

    def _character_dict(
        self,
        *,
        name: str,
        role: str,
        personality: str = "",
        decision_style: str = "",
        taboo: str = "",
        goal: str = "",
        fear: str = "",
        relationship: str = "",
    ) -> dict[str, str]:
        return {
            "name": name.strip() or "角色",
            "role": role.strip() or "角色",
            "personality": personality.strip(),
            "decision_style": decision_style.strip(),
            "taboo": taboo.strip(),
            "goal": goal.strip(),
            "fear": fear.strip(),
            "relationship": relationship.strip(),
        }

    def _default_voice_profile(self, role: str) -> dict[str, str]:
        role_text = role.lower()
        if "主角" in role or "protagonist" in role_text:
            return {
                "sentence_length": "中短句",
                "speed": "稳中带压",
                "tactic": "先判断，再卡结论",
                "pressure_mode": "受压先留余地",
                "avoid": "不空喊，不卖惨",
                "texture": "冷硬",
            }
        if "盟友" in role or "搭档" in role or "ally" in role_text or "friend" in role_text:
            return {
                "sentence_length": "短句",
                "speed": "快",
                "tactic": "先刺探，再追问",
                "pressure_mode": "压力上来先确认底牌",
                "avoid": "不长篇解释",
                "texture": "利落",
            }
        if "对手" in role or "反派" in role:
            return {
                "sentence_length": "短句",
                "speed": "急促",
                "tactic": "先压位置，再卡后果",
                "pressure_mode": "越急越想压场",
                "avoid": "不承认自己虚",
                "texture": "硬",
            }
        return {
            "sentence_length": "中句",
            "speed": "稳",
            "tactic": "先表态，再试探",
            "pressure_mode": "压力上来先收一寸",
            "avoid": "不说太满",
            "texture": "平",
        }

    def _parse_characters(self, project_dir: Path) -> list[dict[str, str]]:
        path = project_dir / "00_memory" / "characters.md"
        text = read_text(path)
        if not text.strip():
            return [
                self._character_dict(name="主角", role="主角"),
                self._character_dict(name="对位角色", role="盟友"),
            ]

        characters: list[dict[str, str]] = []
        current_role = ""
        current_name = ""
        current_fields: dict[str, str] = {}

        def flush() -> None:
            nonlocal current_name, current_fields
            if not current_name:
                return
            characters.append(
                self._character_dict(
                    name=current_name,
                    role=current_fields.get("定位") or current_role or "角色",
                    personality=current_fields.get("核心性格") or current_fields.get("性格", ""),
                    decision_style=current_fields.get("决策风格", ""),
                    taboo=current_fields.get("底线/禁忌", ""),
                    goal=current_fields.get("当前诉求", ""),
                    fear=current_fields.get("当前恐惧", ""),
                    relationship=current_fields.get("与主角关系", ""),
                )
            )
            current_name = ""
            current_fields = {}

        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue
            if line.startswith("## "):
                flush()
                current_role = line[3:].strip()
                continue
            if line.startswith("### "):
                flush()
                current_name = line[4:].strip()
                continue
            parsed = self._extract_bullet_value(line)
            if parsed is None:
                continue
            key, value = parsed
            if key == "姓名":
                current_name = value
                continue
            if key and value:
                current_fields[key] = value

        flush()

        if not characters:
            return [
                self._character_dict(name="主角", role="主角"),
                self._character_dict(name="对位角色", role="盟友"),
            ]
        return characters

    def _speaker_profiles(self, project_dir: Path) -> tuple[dict[str, str], dict[str, str]]:
        characters = self._parse_characters(project_dir)
        protagonist = next((item for item in characters if "主角" in item["role"]), characters[0])
        counterpart = next(
            (
                item
                for item in characters
                if item is not protagonist and any(token in item["role"] for token in ("盟友", "对手", "反派", "核心配角"))
            ),
            characters[1] if len(characters) > 1 else self._character_dict(name="对位角色", role="盟友"),
        )
        return protagonist, counterpart

    def _role_voice_profile(self, character: dict[str, str]) -> dict[str, str]:
        profile = self._default_voice_profile(character.get("role", ""))
        decision_style = character.get("decision_style", "")
        relationship = character.get("relationship", "")
        if decision_style == "谨慎":
            profile["tactic"] = "先判断，再卡结论"
            profile["pressure_mode"] = "受压先留余地"
            profile["sentence_length"] = "中短句"
        elif decision_style == "冲动":
            profile["tactic"] = "先顶回去，再补理由"
            profile["pressure_mode"] = "受压会立刻反顶"
            profile["sentence_length"] = "短句"
        if "盟友" in relationship and "确认底牌" not in profile["pressure_mode"]:
            profile["pressure_mode"] = "先确认底牌，再决定站位"
        return profile

    def _state_summary(self, packet: ChapterContextPacket, brief: ChapterBrief) -> dict[str, str]:
        protagonist_goal = brief.chapter_function.strip() or packet.next_goal.strip() or "拿回主动权"
        counterpart_goal = packet.open_threads[0] if packet.open_threads else "确认局面还在控制内"
        counterpart_fear = packet.warnings[0] if packet.warnings else "局面彻底失控"
        protagonist_taboo = packet.forbidden_inventions[0] if packet.forbidden_inventions else "不把命交给运气"
        return {
            "protagonist_goal": protagonist_goal,
            "counterpart_goal": counterpart_goal,
            "counterpart_fear": counterpart_fear,
            "protagonist_taboo": protagonist_taboo,
        }

    def _line_for(self, speaker: dict[str, str], profile: dict[str, str], intent: str) -> str:
        if intent == "probe":
            if "盟友" in speaker.get("relationship", "") or "盟友" in speaker.get("role", ""):
                text = "你先别把话说满，我要先确认你手里到底有什么。"
            else:
                text = "你别以为自己已经翻盘了，我只看结果。"
        elif intent == "push":
            text = f"我现在只认一件事，{speaker.get('goal') or '局面必须被压住'}。"
        elif intent == "fear":
            text = f"再拖下去，{speaker.get('fear') or '局面彻底失控'}。"
        else:
            text = f"{speaker.get('goal') or '先把主动权拿回来'}。"
        return f"“{text}”"

    def _build_scene_outline(
        self,
        packet: ChapterContextPacket,
        brief: ChapterBrief,
        protagonist: dict[str, str],
        counterpart: dict[str, str],
        genre_profile: dict[str, str],
    ) -> list[dict[str, str]]:
        state = self._state_summary(packet, brief)
        win_noun = genre_profile["win_noun"]
        pressure_noun = genre_profile["pressure_noun"]
        return [
            {
                "label": "Scene 1",
                "title": "开场压迫",
                "summary": f"{protagonist['name']}在{packet.current_place or '当前场域'}里先稳住呼吸，准备把{state['protagonist_goal']}和{win_noun}一起拉回自己手里。",
                "result_type": "pressure_stabilized",
                "cost_type": "identity_exposure_risk",
                "hook_type": "pressure_kept",
            },
            {
                "label": "Scene 2",
                "title": "试探反击",
                "summary": f"{counterpart['name']}逼问底牌，{protagonist['name']}用谨慎策略试探性回顶，争夺现实里的{win_noun}。",
                "result_type": "partial_win",
                "cost_type": "trust_strain",
                "hook_type": "pressure_kept",
            },
            {
                "label": "Scene 3",
                "title": "结果兑现",
                "summary": f"{protagonist['name']}拿到局部优势，但必须守住禁忌“{state['protagonist_taboo']}”，并确认新的{pressure_noun}。",
                "result_type": "partial_win",
                "cost_type": "system_cost_revealed",
                "hook_type": "cost_upgrade",
            },
            {
                "label": "Scene 4",
                "title": "代价揭示",
                "summary": f"{counterpart['name']}意识到{state['counterpart_fear']}正在逼近，本章以更高一级的{pressure_noun}收束。",
                "result_type": "partial_win_with_pressure_kept",
                "cost_type": "cost_upgrade",
                "hook_type": "cost_upgrade",
            },
        ]

    def _scene_beats(
        self,
        protagonist: dict[str, str],
        counterpart: dict[str, str],
        state: dict[str, str],
        genre_profile: dict[str, str],
    ) -> list[str]:
        win_noun = genre_profile["win_noun"]
        pressure_noun = genre_profile["pressure_noun"]
        return [
            f"{protagonist['name']}先判断局面，目标是{state['protagonist_goal']}并拿回{win_noun}",
            f"{counterpart['name']}不断施压，想确认{state['counterpart_goal']}",
            f"{protagonist['name']}始终守住禁忌：{state['protagonist_taboo']}",
            f"章内风险被重新命名成：{state['counterpart_fear']}，并升级成新的{pressure_noun}",
        ]

    def _scene_paragraph_template(
        self,
        index: int,
        packet: ChapterContextPacket,
        protagonist: dict[str, str],
        counterpart: dict[str, str],
        protagonist_profile: dict[str, str],
        counterpart_profile: dict[str, str],
        state: dict[str, str],
        counterpart_goal: str,
        genre_profile: dict[str, str],
    ) -> list[str]:
        place = packet.current_place or "昏暗走廊"
        pressure_noun = genre_profile["pressure_noun"]
        win_noun = genre_profile["win_noun"]
        hook_phrase = genre_profile["hook_phrase"]
        is_urban_system = genre_profile["genre"] == "urban_system"
        if index == 1:
            return [
                f"{protagonist['name']}没有急着开口，只是先把视线压在{place}的尽头，确认每一步退路都还在。",
                f"他很清楚，今晚真正要拿回来的不是面子，而是{state['protagonist_goal']}，也是更现实的{win_noun}。",
                "他先确认的不是情绪，而是现实里还有没有能挪动的位置。" if is_urban_system else "他先确认的不是情绪，而是接下来还能不能稳住局面。",
                f"{counterpart['name']}这趟来，不只是盯人，她真正要确认的是{counterpart_goal}。",
                f"{counterpart['name']}盯着他，语气里没有缓冲。{self._line_for(counterpart, counterpart_profile, 'probe')}",
                f"{protagonist['name']}没有立刻抢话，他先把呼吸压稳，再把结论往前送。{self._line_for(protagonist, protagonist_profile, 'push')}",
                "这一轮还没有人真正赢下来，但局面已经从失控边缘，被他硬生生拽回了一寸。",
            ]
        if index == 2:
            return [
                f"{counterpart['name']}没有退，她顺着刚才那点松动继续往里逼，想把{counterpart_goal}彻底坐实。",
                f"{protagonist['name']}顺着墙边挪开半步，把最危险的角度让空，却没有把主动权一起让出去。",
                "他不是单纯顶回去，而是先把现实里的站位换掉，让对面必须跟着他的节奏走。" if is_urban_system else "他不是单纯顶回去，而是先把节奏换掉，让对面必须重新判断。",
                f"他没有碰那条红线，因为{state['protagonist_taboo']}这件事，比一时的漂亮回顶更重要。",
                f"{counterpart['name']}话锋更快，明显在试他到底敢不敢再往前走一步。{self._line_for(counterpart, counterpart_profile, 'fear')}",
                f"{protagonist['name']}只用了一句更硬的结论把节奏截断，逼得对面先停下来算代价。",
                "场面上的胜负还没翻盘，但信任已经开始绷紧，这就是本章第一次真正的反击。",
            ]
        if index == 3:
            return [
                f"{protagonist['name']}抓住那一瞬间的停顿，把最关键的信息先握进自己手里，局部优势终于落袋。",
                f"可他也立刻意识到，系统给出的不是白拿的筹码，而是一笔必须回收的{pressure_noun}。",
                "那感觉像一次冷冰冰的结算，赢面刚到手，账也同时记到了他头上。" if is_urban_system else "那感觉像一记回响，赢面刚到手，账也同时记到了他头上。",
                f"{counterpart['name']}看见他终于不再只会挨打，眼神里第一次出现了迟疑和重新估价。",
                f"这份结果来得够快，却不够轻，越是往前推进，{state['counterpart_fear']}这层阴影就越压得近。",
                f"{protagonist['name']}把那股冲动摁回去，没有为了把局面做满就越界，他要的是能继续赢下去的空间。",
                "于是这一场不是圆满兑现，而是带着回响的局部兑现，赢面刚露出来，代价也跟着露头。",
            ]
        return [
            f"{counterpart['name']}终究还是停了一拍，没有逼到底，她知道再往前一步就会把局面彻底推翻。",
            f"{protagonist['name']}听出了那一点犹豫，也看见了更重的东西正往下压：{state['counterpart_fear']}。",
            f"系统没有再给他喘息，只把下一步的{pressure_noun}冷冰冰抛到眼前，逼他在赢面和代价之间立刻做选择。",
            "这不只是情绪上的悬着，而是现实账面上的下一轮结算已经开始倒计时。" if is_urban_system else "这不只是情绪上的悬着，而是下一轮真正的后果已经开始倒计时。",
            f"{counterpart['name']}低声补了一句，提醒他真正危险的从来不是眼前这一下，而是之后每一次必须继续付出的成本。",
            f"{protagonist['name']}没有回答得很满，他只是把退路、目标和代价一起记住，准备把下一章的主动权继续抓在手里。",
            f"所以本章的结尾不是收平，而是把更高一级的钩子钉住：局面暂时稳住了，{hook_phrase}。",
        ]

    def _build_scene_paragraphs(
        self,
        packet: ChapterContextPacket,
        brief: ChapterBrief,
        protagonist: dict[str, str],
        counterpart: dict[str, str],
        protagonist_profile: dict[str, str],
        counterpart_profile: dict[str, str],
        genre_profile: dict[str, str],
    ) -> tuple[list[dict[str, object]], list[str]]:
        state = self._state_summary(packet, brief)
        outline = self._build_scene_outline(packet, brief, protagonist, counterpart, genre_profile)
        counterpart_goal = counterpart.get("goal") or state["counterpart_goal"]
        scenes: list[dict[str, object]] = []
        manuscript_paragraphs: list[str] = []

        for index, item in enumerate(outline, start=1):
            beats = self._scene_beats(protagonist, counterpart, state, genre_profile)
            draft_lines = self._scene_paragraph_template(
                index,
                packet,
                protagonist,
                counterpart,
                protagonist_profile,
                counterpart_profile,
                state,
                counterpart_goal,
                genre_profile,
            )
            scenes.append(
                {
                    "label": item["label"],
                    "title": item["title"],
                    "summary": item["summary"],
                    "beats": beats,
                    "draft_lines": draft_lines,
                    "result_type": item["result_type"],
                    "cost_type": item["cost_type"],
                    "hook_type": item["hook_type"],
                }
            )
            manuscript_paragraphs.extend(draft_lines)
            if index != len(outline):
                manuscript_paragraphs.append("")
        return scenes, manuscript_paragraphs

    def _scene_cards(self, scenes: list[dict[str, object]]) -> list[dict[str, str]]:
        return [
            {
                "scene": str(item["label"]),
                "title": str(item["title"]),
                "summary": str(item["summary"]),
                "result_type": str(item["result_type"]),
                "cost_type": str(item["cost_type"]),
                "hook_type": str(item["hook_type"]),
            }
            for item in scenes
        ]

    def _outcome_signature(self, brief: ChapterBrief, genre_profile: dict[str, str]) -> dict[str, str]:
        return {
            "chapter_result": brief.chapter_function.strip() or "主角完成一次有效反击",
            "result_type": "partial_win_with_pressure_kept",
            "cost_type": "cost_upgrade",
            "hook_type": "cost_upgrade",
            "next_pull": brief.hook_goal.strip() or genre_profile["hook_phrase"],
        }

    def _behavior_snapshot(
        self,
        draft_text: str,
        protagonist: dict[str, str],
        counterpart: dict[str, str],
    ) -> dict[str, object]:
        return {
            "protagonist_cautious_markers": [marker for marker in ("先判断", "确认", "稳住", "留余地") if marker in draft_text],
            "protagonist_reckless_markers": [marker for marker in ("直接扑上去", "赌一把") if marker in draft_text],
            "taboo_break_markers": [marker for marker in ("把命交给运气", "赌命") if marker in draft_text and f"不{marker}" not in draft_text],
            "counterpart_pressure_markers": [marker for marker in ("逼问", "盯着", "确认底牌", "施压") if marker in draft_text],
            "counterpart_soft_markers": [marker for marker in ("停了一拍", "缓了缓", "没有逼到底") if marker in draft_text],
            "protagonist_name_mentions": draft_text.count(protagonist["name"]),
            "counterpart_name_mentions": draft_text.count(counterpart["name"]),
        }

    def _character_constraints(
        self,
        draft_text: str,
        protagonist: dict[str, str],
        counterpart: dict[str, str],
        protagonist_profile: dict[str, str],
        counterpart_profile: dict[str, str],
        state: dict[str, str],
    ) -> dict[str, object]:
        protagonist_goal = protagonist.get("goal") or state["protagonist_goal"]
        protagonist_taboo = protagonist.get("taboo") or state["protagonist_taboo"]
        counterpart_goal = counterpart.get("goal") or state["counterpart_goal"]
        counterpart_fear = counterpart.get("fear") or state["counterpart_fear"]
        return {
            "protagonist_goal": protagonist_goal,
            "protagonist_taboo": protagonist_taboo,
            "counterpart_goal": counterpart_goal,
            "counterpart_fear": counterpart_fear,
            "protagonist": {
                "name": protagonist["name"],
                "role": protagonist["role"],
                "decision_style": protagonist.get("decision_style", ""),
                "voice_tactic": protagonist_profile["tactic"],
                "pressure_mode": protagonist_profile["pressure_mode"],
                "goal": protagonist_goal,
            },
            "counterpart": {
                "name": counterpart["name"],
                "role": counterpart["role"],
                "relationship": counterpart.get("relationship", ""),
                "goal": counterpart_goal,
                "fear": counterpart_fear,
                "voice_tactic": counterpart_profile["tactic"],
                "pressure_mode": counterpart_profile["pressure_mode"],
            },
            "behavior_snapshot": self._behavior_snapshot(draft_text, protagonist, counterpart),
            "mentions": {
                "protagonist_goal": protagonist_goal in draft_text,
                "protagonist_taboo": protagonist_taboo in draft_text,
                "counterpart_goal": counterpart_goal in draft_text,
                "counterpart_fear": counterpart_fear in draft_text,
            },
        }

    def _build_draft_text(self, scenes: list[dict[str, object]], notes: dict[str, str]) -> str:
        lines = ["# Runtime Draft", ""]
        for item in scenes:
            lines.extend([f"## {item['label']} {item['title']}", "", "### Beats"])
            lines.extend(f"- {beat}" for beat in item["beats"])
            lines.extend(["", "### Draft"])
            lines.extend(str(line) for line in item["draft_lines"])
            lines.extend(
                [
                    "",
                    "### Scene Card",
                    f"- result_type: {item['result_type']}",
                    f"- cost_type: {item['cost_type']}",
                    f"- hook_type: {item['hook_type']}",
                    "",
                ]
            )
        lines.extend(
            [
                "## Runtime Notes",
                f"- protagonist_goal: {notes['protagonist_goal']}",
                f"- protagonist_taboo: {notes['protagonist_taboo']}",
                f"- counterpart_goal: {notes['counterpart_goal']}",
                f"- counterpart_fear: {notes['counterpart_fear']}",
                "",
            ]
        )
        return "\n".join(lines)

    def _build_review_notes(
        self,
        scenes: list[dict[str, object]],
        outcome_signature: dict[str, str],
        protagonist: dict[str, str],
        counterpart: dict[str, str],
        protagonist_profile: dict[str, str],
        counterpart_profile: dict[str, str],
    ) -> str:
        lines = ["# Runtime Draft Review Notes", "", "## Dialogue Check"]
        lines.extend(
            [
                f"- protagonist: {protagonist['name']} / {protagonist['role']}",
                f"- counterpart: {counterpart['name']} / {counterpart['role']}",
                "- dialogue should preserve pressure, restraint, and tactical contrast",
                "",
                "## Voice Profiles",
                f"- {protagonist['name']} 句长={protagonist_profile['sentence_length']} / 速度={protagonist_profile['speed']} / tactic={protagonist_profile['tactic']} / pressure_mode={protagonist_profile['pressure_mode']} / avoid={protagonist_profile['avoid']}",
                f"- {counterpart['name']} 句长={counterpart_profile['sentence_length']} / 速度={counterpart_profile['speed']} / tactic={counterpart_profile['tactic']} / pressure_mode={counterpart_profile['pressure_mode']} / avoid={counterpart_profile['avoid']}",
                f"- {protagonist['name']} 当前诉求={protagonist.get('goal', '') or '无'} / 决策风格={protagonist.get('decision_style', '') or '未设定'}",
                f"- {counterpart['name']} 当前诉求={counterpart.get('goal', '') or '无'} / 决策风格={counterpart.get('decision_style', '') or '未设定'}",
                "",
                "## Outcome Signature",
                f"- chapter_result: {outcome_signature['chapter_result']}",
                f"- result_type: {outcome_signature['result_type']}",
                f"- cost_type: {outcome_signature['cost_type']}",
                f"- hook_type: {outcome_signature['hook_type']}",
                f"- next_pull: {outcome_signature['next_pull']}",
                "",
                "## Review Checklist",
            ]
        )
        lines.extend(f"- {item['label']}: {item['summary']}" for item in scenes)
        lines.append("")
        return "\n".join(lines)

    def _build_rewrite_handoff(self, brief: ChapterBrief, decision: RuntimeDecision) -> str:
        rewrite_brief = decision.rewrite_brief
        blocking_reasons = rewrite_brief.blocking_reasons if rewrite_brief is not None else []
        must_change = rewrite_brief.must_change if rewrite_brief is not None else []
        recheck_order = rewrite_brief.recheck_order if rewrite_brief is not None else []
        reasons = blocking_reasons or ["当前章节存在阻断问题，需要按 brief 重新组织场景和结果。"]
        lines = [
            "# Rewrite Handoff",
            "",
            "## Decision",
            "- blocking: yes",
            f"- blocking_dimensions: {', '.join(decision.blocking_dimensions) if decision.blocking_dimensions else 'runtime_blocking'}",
            "",
            "## Blocking Reasons",
        ]
        lines.extend(f"- {item}" for item in reasons)
        lines.extend(["", "## Must Change"])
        lines.extend(f"- {item}" for item in must_change or ["回到 scene beats 与段落层重写。"])
        lines.extend(["", "## Recheck Order"])
        lines.extend(f"- {item}" for item in recheck_order or ["continuity", "pacing", "style"])
        lines.extend(["", "## Chapter Function", f"- {brief.chapter_function}", ""])
        return "\n".join(lines)

    def _build_chapter_blueprint(self, scenes: list[dict[str, object]], outcome_signature: dict[str, str]) -> str:
        lines = ["# Chapter Blueprint", "", "## Scene Cards"]
        for item in scenes:
            lines.extend(
                [
                    f"### {item['label']} {item['title']}",
                    f"- summary: {item['summary']}",
                    f"- result_type: {item['result_type']}",
                    f"- cost_type: {item['cost_type']}",
                    f"- hook_type: {item['hook_type']}",
                    "",
                ]
            )
        lines.extend(
            [
                "## Chapter Signature",
                f"- chapter_result: {outcome_signature['chapter_result']}",
                f"- result_type: {outcome_signature['result_type']}",
                f"- hook_type: {outcome_signature['hook_type']}",
                "",
            ]
        )
        return "\n".join(lines)

    def _build_editorial_summary(
        self,
        behavior_snapshot: dict[str, object],
        protagonist: dict[str, str],
        counterpart: dict[str, str],
    ) -> str:
        lines = [
            "# Editorial Summary",
            "",
            "## Character Trace",
            f"- protagonist: {protagonist['name']} / {protagonist['role']}",
            f"- counterpart: {counterpart['name']} / {counterpart['role']}",
            "",
            "## Behavior Snapshot",
        ]
        for key, value in behavior_snapshot.items():
            lines.append(f"- {key}: {value}")
        lines.append("")
        return "\n".join(lines)

    def _build_reader_manuscript(
        self,
        brief: ChapterBrief,
        manuscript_paragraphs: list[str],
        outcome_signature: dict[str, str],
        genre_profile: dict[str, str],
    ) -> str:
        body = "\n".join(paragraph for paragraph in manuscript_paragraphs if paragraph is not None).strip()
        lines = [
            f"# Chapter {brief.chapter:03d} {self._chapter_title(brief)}",
            "",
            body,
            "",
            f"这一章真正被拿回来的，是{outcome_signature['chapter_result']}。",
            f"但更重的东西已经压下来：{outcome_signature['next_pull']}，它直接变成了新的{genre_profile['pressure_noun']}。",
            "",
        ]
        return "\n".join(lines)

    def draft(
        self,
        project_dir: Path,
        packet: ChapterContextPacket,
        brief: ChapterBrief,
        decision: RuntimeDecision,
        *,
        dry_run: bool = False,
    ) -> dict[str, object]:
        draft_dir = self._draft_dir(project_dir, brief.chapter)
        draft_dir.mkdir(parents=True, exist_ok=True)

        if decision.decision == "revise":
            rewrite_handoff_path = draft_dir / "rewrite_handoff.md"
            rewrite_text = self._build_rewrite_handoff(brief, decision)
            rewrite_handoff_path.write_text(rewrite_text + "\n", encoding="utf-8")
            return {
                "status": "pending-human-rewrite",
                "rewrite_handoff_path": rewrite_handoff_path.as_posix(),
                "rewrite_handoff_preview": "\n".join(rewrite_text.splitlines()[:8]),
            }

        protagonist, counterpart = self._speaker_profiles(project_dir)
        protagonist_profile = self._role_voice_profile(protagonist)
        counterpart_profile = self._role_voice_profile(counterpart)
        genre_profile = self._genre_profile(project_dir)
        scenes, manuscript_paragraphs = self._build_scene_paragraphs(
            packet,
            brief,
            protagonist,
            counterpart,
            protagonist_profile,
            counterpart_profile,
            genre_profile,
        )
        state = self._state_summary(packet, brief)
        outcome_signature = self._outcome_signature(brief, genre_profile)
        draft_seed_text = self._build_draft_text(
            scenes,
            {
                "protagonist_goal": protagonist.get("goal") or state["protagonist_goal"],
                "protagonist_taboo": protagonist.get("taboo") or state["protagonist_taboo"],
                "counterpart_goal": counterpart.get("goal") or state["counterpart_goal"],
                "counterpart_fear": counterpart.get("fear") or state["counterpart_fear"],
            },
        )
        character_constraints = self._character_constraints(
            draft_seed_text,
            protagonist,
            counterpart,
            protagonist_profile,
            counterpart_profile,
            state,
        )
        draft_text = self._build_draft_text(
            scenes,
            {
                "protagonist_goal": str(character_constraints["protagonist_goal"]),
                "protagonist_taboo": str(character_constraints["protagonist_taboo"]),
                "counterpart_goal": str(character_constraints["counterpart_goal"]),
                "counterpart_fear": str(character_constraints["counterpart_fear"]),
            },
        )
        behavior_snapshot = character_constraints["behavior_snapshot"]
        review_text = self._build_review_notes(
            scenes,
            outcome_signature,
            protagonist,
            counterpart,
            protagonist_profile,
            counterpart_profile,
        )
        blueprint_text = self._build_chapter_blueprint(scenes, outcome_signature)
        editorial_summary_text = self._build_editorial_summary(behavior_snapshot, protagonist, counterpart)
        manuscript_text = self._build_reader_manuscript(brief, manuscript_paragraphs, outcome_signature, genre_profile)

        draft_path = draft_dir / "runtime_draft.md"
        review_notes_path = draft_dir / "runtime_review_notes.md"
        blueprint_path = draft_dir / "chapter_blueprint.md"
        editorial_summary_path = draft_dir / "editorial_summary.md"
        manuscript_path = draft_dir / "reader_manuscript.md"

        draft_path.write_text(draft_text + "\n", encoding="utf-8")
        review_notes_path.write_text(review_text + "\n", encoding="utf-8")
        blueprint_path.write_text(blueprint_text + "\n", encoding="utf-8")
        editorial_summary_path.write_text(editorial_summary_text + "\n", encoding="utf-8")
        manuscript_path.write_text(manuscript_text + "\n", encoding="utf-8")

        return {
            "status": "ready-human-review" if dry_run else "drafted-runtime-output",
            "draft_path": draft_path.as_posix(),
            "review_notes_path": review_notes_path.as_posix(),
            "blueprint_path": blueprint_path.as_posix(),
            "editorial_summary_path": editorial_summary_path.as_posix(),
            "manuscript_path": manuscript_path.as_posix(),
            "draft_preview": "\n".join(draft_text.splitlines()[:12]),
            "review_notes_preview": "\n".join(review_text.splitlines()[:12]),
            "blueprint_preview": "\n".join(blueprint_text.splitlines()[:12]),
            "editorial_summary_preview": "\n".join(editorial_summary_text.splitlines()[:12]),
            "manuscript_preview": "\n".join(manuscript_text.splitlines()[:12]),
            "scene_count": len(scenes),
            "word_count": len("".join(manuscript_paragraphs)),
            "scene_cards": self._scene_cards(scenes),
            "outcome_signature": outcome_signature,
            "character_constraints": character_constraints,
        }
