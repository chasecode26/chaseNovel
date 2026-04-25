from __future__ import annotations

from pathlib import Path

from runtime.contracts import ChapterBrief, ChapterContextPacket, ChapterDirection, RuntimeDecision
from scripts.novel_utils import read_text, useful_lines


class WriterExecutor:
    def _load_memory_prompt_file(self, project_dir: Path, name: str) -> str:
        return read_text(project_dir / "00_memory" / name)

    def _compact_memory_lines(self, text: str, *, limit: int) -> list[str]:
        return useful_lines(text, limit)

    def _writer_director_prompt(self, project_dir: Path) -> str:
        prompt_text = self._load_memory_prompt_file(project_dir, "writer-director-prompt.md")
        return prompt_text.strip()

    def _book_voice_context(self, project_dir: Path) -> list[str]:
        voice_lines = self._compact_memory_lines(self._load_memory_prompt_file(project_dir, "voice.md"), limit=10)
        style_lines = self._compact_memory_lines(self._load_memory_prompt_file(project_dir, "style.md"), limit=10)
        guardrail_lines = self._compact_memory_lines(self._load_memory_prompt_file(project_dir, "style-guardrails.md"), limit=12)
        combined: list[str] = []
        seen: set[str] = set()
        for section in (voice_lines, style_lines, guardrail_lines):
            for item in section:
                normalized = item.strip()
                if not normalized or normalized in seen:
                    continue
                seen.add(normalized)
                combined.append(normalized)
        return combined[:18]

    def _build_minimal_mission_context(
        self,
        packet: ChapterContextPacket,
        brief: ChapterBrief,
        direction: ChapterDirection | None,
    ) -> dict[str, object]:
        scene_plan = [item.strip() for item in brief.scene_plan if item.strip()]
        reader_goal = ((direction.reader_experience_goal if direction is not None else "") or brief.reader_experience_goal).strip()
        dramatic_question = "" if direction is None else direction.dramatic_question.strip()
        obstacle = ((direction.core_conflict if direction is not None else "") or brief.core_conflict).strip()
        if not obstacle and packet.open_threads:
            obstacle = packet.open_threads[0].strip()
        core_scene = (brief.midpoint_collision or brief.opening_image).strip()
        if not core_scene and scene_plan:
            core_scene = scene_plan[0].strip()
        return {
            "chapter_function": brief.chapter_function.strip(),
            "goal": (brief.result_change or brief.chapter_function or packet.next_goal).strip(),
            "obstacle": obstacle,
            "core_scene": core_scene,
            "payoff_hit": (brief.result_change or (brief.required_payoff_or_pressure[0] if brief.required_payoff_or_pressure else "")).strip(),
            "cost": (brief.emotional_beat or (brief.required_payoff_or_pressure[1] if len(brief.required_payoff_or_pressure) > 1 else "")).strip(),
            "next_pull": ((direction.closing_hook if direction is not None else "") or brief.closing_hook or brief.hook_goal).strip(),
            "reader_goal": reader_goal,
            "dramatic_question": dramatic_question,
            "scene_plan": scene_plan[:4],
            "success_criteria": [item.strip() for item in brief.success_criteria if item.strip()][:4],
        }

    def _build_minimal_boundaries_context(
        self,
        packet: ChapterContextPacket,
        brief: ChapterBrief,
        direction: ChapterDirection | None,
    ) -> dict[str, object]:
        hard_limits = [] if direction is None else [item.strip() for item in direction.hard_limits if item.strip()]
        boundaries = [
            f"时间锚点：{packet.time_anchor}" if packet.time_anchor else "",
            f"地点锚点：{packet.location_anchor or packet.current_place}" if (packet.location_anchor or packet.current_place) else "",
            f"在场人物：{'、'.join(packet.present_characters[:6])}" if packet.present_characters else "",
            f"知情边界：{packet.knowledge_boundary}" if packet.knowledge_boundary else "",
            f"消息链路：{packet.message_flow}" if packet.message_flow else "",
            f"到达时序：{packet.arrival_timing}" if packet.arrival_timing else "",
            f"当前资源：{packet.resource_state}" if packet.resource_state else "",
            f"推进下限：{brief.progress_floor}" if brief.progress_floor else "",
            f"推进上限：{brief.progress_ceiling}" if brief.progress_ceiling else "",
        ]
        boundaries.extend(f"禁止提前兑现：{item}" for item in brief.must_not_payoff_yet if item.strip())
        boundaries.extend(f"变化范围：{item}" for item in brief.allowed_change_scope if item.strip())
        boundaries.extend(f"禁止新增：{item}" for item in brief.disallowed_moves if item.strip())
        boundaries.extend(hard_limits)
        deduped: list[str] = []
        seen: set[str] = set()
        for item in boundaries:
            normalized = item.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(normalized)
        return {"lines": deduped[:14]}

    def _build_minimal_cast_voice_context(
        self,
        protagonist: dict[str, str],
        counterpart: dict[str, str],
        protagonist_profile: dict[str, str],
        counterpart_profile: dict[str, str],
    ) -> dict[str, object]:
        def build_voice_line(character: dict[str, str], profile: dict[str, str]) -> str:
            parts = [
                f"{character['name']}（{character['role']}）",
                f"平时句长={profile['sentence_length']}",
                f"节奏={profile['speed']}",
                f"说话策略={profile['tactic']}",
                f"受压反应={profile['pressure_mode']}",
            ]
            if character.get("goal", "").strip():
                parts.append(f"当前诉求={character['goal'].strip()}")
            if character.get("fear", "").strip():
                parts.append(f"当前恐惧={character['fear'].strip()}")
            if character.get("taboo", "").strip():
                parts.append(f"禁忌={character['taboo'].strip()}")
            if character.get("relationship", "").strip():
                parts.append(f"与主角关系={character['relationship'].strip()}")
            parts.append(f"绝不写成={profile['avoid']}")
            return "；".join(parts)

        return {
            "lines": [
                build_voice_line(protagonist, protagonist_profile),
                build_voice_line(counterpart, counterpart_profile),
            ]
        }

    def _build_minimal_writer_rules_context(self, direction: ChapterDirection | None) -> dict[str, object]:
        rules: list[str] = []
        if direction is not None:
            rules.extend(item.strip() for item in direction.writer_mission if item.strip())
            rules.extend(item.strip() for item in direction.explanation_bans if item.strip())
            rules.extend(item.strip() for item in direction.role_speaking_limits if item.strip())
        deduped: list[str] = []
        seen: set[str] = set()
        for item in rules:
            if item in seen:
                continue
            seen.add(item)
            deduped.append(item)
        return {"lines": deduped[:12]}

    def _render_section(self, title: str, lines: list[str]) -> str:
        cleaned = [item.strip() for item in lines if item and item.strip()]
        if not cleaned:
            return f"## {title}\n- 无"
        body = "\n".join(f"- {item}" for item in cleaned)
        return f"## {title}\n{body}"

    def _clean_story_phrase(self, text: str, *, fallback: str) -> str:
        cleaned = " ".join(text.replace("\n", " ").split()).strip("，。；：,. ")
        if not cleaned:
            return fallback
        banned_fragments = (
            "runtime",
            "scene card",
            "scene",
            "target_word_count",
            "字数目标",
            "结果密度",
            "blocking",
            "evaluator",
            "reviewer",
            "正文",
            "章卡",
            "术语",
            "复核",
            "重写",
            "第 2 轮",
            "轮重写",
            "新开支线",
            "篇幅",
            "本章必须",
            "推进做实",
            "延续当前压力",
            "形成下一章牵引",
            "读者体验",
            "戏剧问题",
            "主角完成",
            "下一章",
        )
        if any(fragment in cleaned for fragment in banned_fragments):
            return fallback
        replacements = {
            "开始掌握主动，不再只是被动挨打": "把主动权拿回来",
            "开始掌握主动权，不再只是被动挨打": "把主动权拿回来",
            "主角不再只是挨打，开始拿回主动权": "把主动权拿回来",
            "主角开始掌握主动，不再只是被动挨打": "把主动权拿回来",
            "主角开始掌握主动权": "把主动权拿回来",
            "确认系统代价": "把系统代价看清",
            "系统给出更高代价的下一步任务": "系统已经把下一步的价码抬高了",
        }
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)
        cleaned = cleaned.strip("，。；：,. ")
        return cleaned or fallback

    def _assemble_minimal_writer_prompt(
        self,
        *,
        project_dir: Path,
        mission: dict[str, object],
        boundaries: dict[str, object],
        cast_voice: dict[str, object],
        writer_rules: dict[str, object],
    ) -> str:
        director_prompt = self._writer_director_prompt(project_dir)
        mission_lines = [
            f"本章作用：{mission['chapter_function']}" if str(mission.get('chapter_function', '')).strip() else "",
            f"主目标：{mission['goal']}" if str(mission.get('goal', '')).strip() else "",
            f"主要阻力：{mission['obstacle']}" if str(mission.get('obstacle', '')).strip() else "",
            f"本章最该拍的一场：{mission['core_scene']}" if str(mission.get('core_scene', '')).strip() else "",
            f"结果变化：{mission['payoff_hit']}" if str(mission.get('payoff_hit', '')).strip() else "",
            f"代价/刺痛：{mission['cost']}" if str(mission.get('cost', '')).strip() else "",
            f"章尾拉力：{mission['next_pull']}" if str(mission.get('next_pull', '')).strip() else "",
            f"读者体验目标：{mission['reader_goal']}" if str(mission.get('reader_goal', '')).strip() else "",
            f"戏剧问题：{mission['dramatic_question']}" if str(mission.get('dramatic_question', '')).strip() else "",
        ]
        scene_plan = [str(item).strip() for item in mission.get("scene_plan", []) if str(item).strip()]
        success_criteria = [str(item).strip() for item in mission.get("success_criteria", []) if str(item).strip()]
        book_voice = self._book_voice_context(project_dir)
        sections = [
            director_prompt or "# Writer 导演单\n你现在不是在总结这一章，而是在直接写这一章正文。",
            self._render_section("本章任务", mission_lines),
            self._render_section("场面推进", scene_plan),
            self._render_section("成章标准", success_criteria),
            self._render_section("硬边界", [str(item) for item in boundaries.get("lines", [])]),
            self._render_section("角色声口", [str(item) for item in cast_voice.get("lines", [])]),
            self._render_section("单书 voice/style", book_voice),
            self._render_section("本章导演要求", [str(item) for item in writer_rules.get("lines", [])]),
            "## 输出要求\n- 直接输出小说正文\n- 不要解释写法\n- 不要输出审稿意见\n- 不要用 Scene / 章卡 / 核心冲突 / 爽点 这些术语写进正文",
        ]
        return "\n\n".join(section.strip() for section in sections if section.strip()) + "\n"

    def _build_manuscript_expansion(
        self,
        mission: dict[str, object],
        protagonist: dict[str, str],
        counterpart: dict[str, str],
        genre_profile: dict[str, str],
    ) -> str:
        goal = self._clean_story_phrase(str(mission.get("goal", "")).strip(), fallback="把主动权抢回来")
        obstacle = self._clean_story_phrase(str(mission.get("obstacle", "")).strip(), fallback="眼前这道压力")
        core_scene = self._clean_story_phrase(str(mission.get("core_scene", "")).strip(), fallback="旧楼走廊里的僵局已经顶到喉口")
        payoff = self._clean_story_phrase(str(mission.get("payoff_hit", "")).strip(), fallback=goal)
        cost = self._clean_story_phrase(str(mission.get("cost", "")).strip(), fallback=f"新的{genre_profile['pressure_noun']}已经压到眼前")
        next_pull = self._clean_story_phrase(str(mission.get("next_pull", "")).strip(), fallback=genre_profile["hook_phrase"])
        protagonist_goal = self._clean_story_phrase(protagonist.get("goal", "").strip(), fallback=goal)
        protagonist_taboo = self._clean_story_phrase(protagonist.get("taboo", "").strip(), fallback="不把命交给运气")
        counterpart_goal = self._clean_story_phrase(counterpart.get("goal", "").strip(), fallback=obstacle)
        counterpart_fear = self._clean_story_phrase(counterpart.get("fear", "").strip(), fallback=f"{genre_profile['pressure_noun']}彻底失控")
        if "开场先锁定" in core_scene or "压力" in core_scene:
            core_scene = "旧楼走廊里的僵局已经顶到喉口"
        if payoff == "把主动权拿回来":
            payoff = "把局面翻回来"
        if counterpart_goal == "确认林砚有没有真底牌":
            counterpart_goal = "把他袖子里藏着的后手逼出来"
        if next_pull == "延续当前压力，并形成下一章牵引":
            next_pull = "下一步的价码已经被重新抬高了"
        pressure_noun = genre_profile["pressure_noun"]
        win_noun = genre_profile["win_noun"]
        next_pull_line = next_pull if next_pull.endswith(("。", "！", "？")) else f"{next_pull}。"
        paragraphs = [
            f"{protagonist['name']}一进旧楼走廊就把呼吸压得很平。雨水顺着栏杆往下淌，鞋底踩过积水时只响了一声，他先看了一眼走廊尽头那点僵住的动静，又把{protagonist_goal}这件事死死压在心里。催债的脚步一阵紧过一阵，他先判断门后还有没有退路，再确认自己能不能把今晚这一下真正顶回去。",
            f"廊灯年久失修，光晕一闪一闪，把墙皮上的水痕照得像一层旧伤。{protagonist['name']}没有急着露口风，只把楼道、门锁、窗台和脚边那滩积水全扫了一遍。谁先慌，谁就先丢位；谁先把底牌掀出去，谁就得替后面的{pressure_noun}埋单。他很清楚自己不能乱，尤其不能把{protagonist_taboo}这条线踩断。",
            f"{counterpart['name']}站在廊灯底下，没有替他兜话。她先看了一眼楼道尽头，再把目光钉回{protagonist['name']}脸上，开口就逼近要害：“你想拿{win_noun}，就别再给我留哑谜。今晚这一步，到底是你先动，还是等别人把{pressure_noun}压到你头上？”她说完故意卡住楼梯口，指尖在扶手上敲了两下，像是在替他算最后的时机。",
            f"{protagonist['name']}抹掉指节上的水，声音不高：“我要的不是嘴上赢一次，是把{payoff}真的拿回来。”话说到这儿，他还是把最深那层底牌扣着，只把{protagonist_taboo}这条线死死守住。{counterpart['name']}听完没退，反而往前逼了半步，先试探他袖口里藏着的后手，又提醒他再拖下去，{counterpart_goal}就会变成所有人都看得见的破绽。",
            f"楼道尽头那人本来还想继续压话，听见{protagonist['name']}这句，脚步明显顿了一下。{protagonist['name']}顺势把手机甩到掌心，直接拨回刚才那个催债号码，开口第一句就把账翻了个面：“你要的是钱，不是把我堵死。今晚再往前一步，明天先出事的未必是我。”这话不算漂亮，却够硬，硬到电话那头半天没接上。",
            f"廊外忽然一声闷雷，震得窗框都在发颤。{protagonist['name']}借着这一瞬的乱响先动手，把原本压在自己身上的局面整个扳了回来，逼得对面当场改口。催债的人被他一句话卡在原地，连手机那头都沉默了两秒，像是没想到他真敢把账反压回去。可赢面刚露出来，新的{pressure_noun}也跟着落下，系统在耳边冷冷补了一条代价，连{counterpart['name']}最担心的{counterpart_fear}都被一起拽到了台面上。",
            f"那道系统提示不像安慰，更像一把刀贴着耳骨划过去。{protagonist['name']}眼前一晃，先看见的是任务奖励，下一秒跳出来的却是失败后果：钱要翻倍，伤要落到自己身上，连刚抢回来的{win_noun}都可能当场吐出去。他把那行冷冰冰的字硬生生压进心里，没有让脸色先变。现在要是露怯，刚刚逼退的人立刻就会反扑，连{counterpart['name']}都会重新估价他值不值得站在这一边。",
            f"{counterpart['name']}盯着他看了两秒，像是还想再逼问一句，最后却只把肩线慢慢松开，停了一拍才开口：“你现在拿回的，只够换一口气。真要把这条路走通，下一步只会比今晚更贵。”她没有逼到底，只把手从楼梯口挪开半寸，让他自己选是现在冲出去，还是带着新的{pressure_noun}继续往下扛。",
            f"{protagonist['name']}没解释系统，也没把那笔新账说穿，只低头把湿掉的袖口往上卷了一截。动作不大，却像是把犹豫一并卷走了。他知道自己这一刻真拿回来的，不只是面子，而是说话顺序、出手先后，甚至连楼下那帮人接下来要不要追，都得先看他的脸色。这口气既然抢到了，就不能再白白送回去。",
            f"楼下的铁门被风吹得一下一下撞响，整栋旧楼都像在替这口气计时。{protagonist['name']}没有回头，只把指节握得更紧，顺着墙上的雨痕往下走。每下一层，他都听见系统把新的{pressure_noun}往上抬一格，也更清楚这点刚抢回来的{win_noun}根本不够他喘稳。可也正因为不够，他才更得往前走；停在这里，等于把好不容易翻过来的局面再拱手让人。",
            f"到了拐角，他才低声报出下一步要去的人和地方，像是在给自己下命令，也像是在确认这条路没有第二次后退的机会。{counterpart['name']}跟在后面，没有再催，只在他快要推门时补了一句：“记住，你今晚能赢，不代表明晚还有人替你兜底。” {next_pull_line}",
        ]
        return "\n\n".join(paragraphs).strip() + "\n"

    def _save_minimal_writer_artifacts(
        self,
        *,
        draft_dir: Path,
        prompt_text: str,
        manuscript_text: str,
        review_text: str,
        rewrite_text: str,
    ) -> dict[str, Path | None]:
        prompt_path = draft_dir / "writer_prompt.md"
        manuscript_path = draft_dir / "reader_manuscript.md"
        review_notes_path = draft_dir / "runtime_review_notes.md"
        rewrite_handoff_path = draft_dir / "rewrite_handoff.md" if rewrite_text else None
        prompt_path.write_text(prompt_text, encoding="utf-8")
        manuscript_path.write_text(manuscript_text, encoding="utf-8")
        review_notes_path.write_text(review_text, encoding="utf-8")
        if rewrite_handoff_path is not None:
            rewrite_handoff_path.write_text(rewrite_text, encoding="utf-8")
        return {
            "prompt_path": prompt_path,
            "manuscript_path": manuscript_path,
            "review_notes_path": review_notes_path,
            "rewrite_handoff_path": rewrite_handoff_path,
        }

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
        personality = character.get("personality", "")
        if any(token in personality for token in ("冷", "稳", "寡言", "谨慎")):
            profile["texture"] = "冷硬"
            profile["sentence_length"] = "中短句"
        elif any(token in personality for token in ("急", "利", "直", "狠")):
            profile["texture"] = "利落"
            profile["sentence_length"] = "短句"
        return profile

    def _has_dramatic_brief(self, brief: ChapterBrief) -> bool:
        return True

    def _state_summary(self, packet: ChapterContextPacket, brief: ChapterBrief) -> dict[str, str]:
        protagonist_goal = brief.result_change.strip() or brief.chapter_function.strip() or packet.next_goal.strip() or "拿回主动权"
        counterpart_goal = brief.core_conflict.strip() or (packet.open_threads[0] if packet.open_threads else "确认局面还在控制内")
        counterpart_fear = packet.warnings[0] if packet.warnings else (
            packet.progress_ceiling.strip()
            or packet.next_goal.strip()
            or brief.closing_hook.strip()
            or "后手提前暴露"
        )
        protagonist_taboo = packet.forbidden_inventions[0] if packet.forbidden_inventions else "不把命交给运气"
        return {
            "protagonist_goal": protagonist_goal,
            "counterpart_goal": counterpart_goal,
            "counterpart_fear": counterpart_fear,
            "protagonist_taboo": protagonist_taboo,
        }

    def _is_counterpart(self, speaker: dict[str, str]) -> bool:
        role = speaker.get("role", "")
        relationship = speaker.get("relationship", "")
        role_text = role.lower()
        relationship_text = relationship.lower()
        return any(token in role for token in ("盟友", "搭档", "对手", "反派")) or any(
            token in role_text or token in relationship_text for token in ("ally", "friend", "opponent", "villain")
        )

    def _build_scene_outline(
        self,
        packet: ChapterContextPacket,
        brief: ChapterBrief,
        protagonist: dict[str, str],
        counterpart: dict[str, str],
        genre_profile: dict[str, str],
    ) -> list[dict[str, str]]:
        state = self._state_summary(packet, brief)
        pressure_noun = genre_profile["pressure_noun"]
        opening_summary = brief.opening_image.strip() or f"{protagonist['name']}先在{packet.current_place or '当前场域'}里稳住呼吸，把局面按在手里。"
        midpoint_summary = brief.midpoint_collision.strip() or f"{counterpart['name']}把压力顶上来，逼得{protagonist['name']}当场应对。"
        result_summary = brief.result_change.strip() or f"{protagonist['name']}刚把场子扳回半寸，后账也跟着追上来了。"
        closing_summary = brief.closing_hook.strip() or f"门还没关死，{state['counterpart_fear']}已经贴到身后。"
        return [
            {
                "label": "Scene 1",
                "title": "开场压近",
                "summary": opening_summary,
                "result_type": "pressure_stabilized",
                "cost_type": "identity_exposure_risk",
                "hook_type": "pressure_kept",
            },
            {
                "label": "Scene 2",
                "title": "中段碰撞",
                "summary": midpoint_summary,
                "result_type": "partial_win",
                "cost_type": "trust_strain",
                "hook_type": "pressure_kept",
            },
            {
                "label": "Scene 3",
                "title": "结果变化",
                "summary": result_summary,
                "result_type": "partial_win",
                "cost_type": "system_cost_revealed",
                "hook_type": "cost_upgrade",
            },
            {
                "label": "Scene 4",
                "title": "章末落刀",
                "summary": closing_summary,
                "result_type": "partial_win_with_pressure_kept",
                "cost_type": "cost_upgrade",
                "hook_type": "cost_upgrade",
            },
        ]
    def _scene_beats(
        self,
        packet: ChapterContextPacket,
        protagonist: dict[str, str],
        counterpart: dict[str, str],
        state: dict[str, str],
        genre_profile: dict[str, str],
    ) -> list[str]:
        del genre_profile
        beats = [
            f"anchor: {packet.time_anchor or 'none'} / {packet.location_anchor or packet.current_place or 'none'}",
            f"cast: {'、'.join(packet.present_characters[:6]) if packet.present_characters else protagonist['name']}",
            f"protagonist_move: {protagonist['name']} -> {state['protagonist_goal']}",
            f"counter_move: {counterpart['name']} -> {state['counterpart_goal']}",
            f"taboo: {state['protagonist_taboo']}",
            f"risk: {state['counterpart_fear']}",
        ]
        if packet.message_flow:
            beats.append(f"message_flow: {packet.message_flow}")
        if packet.who_cannot_know_yet:
            beats.append(f"hold_knowledge: {packet.who_cannot_know_yet}")
        if packet.travel_time_floor:
            beats.append(f"travel_floor: {packet.travel_time_floor}")
        return beats

    def _looks_like_outline_text(self, text: str) -> bool:
        value = self._normalize_directive(text)
        if not value:
            return False
        banned_tokens = (
            "本章",
            "章节",
            "读者",
            "体验",
            "戏剧",
            "核心冲突",
            "章卡",
            "scene",
            "Scene",
            "开场先",
            "延续当前压力",
            "形成下一章牵引",
            "结果变化",
            "章末",
            "主角",
        )
        if any(token in value for token in banned_tokens):
            return True
        action_markers = ("完成", "确认", "锁定", "推进", "形成", "回收", "交代", "落在")
        return len(value) <= 28 and sum(1 for token in action_markers if token in value) >= 2

    def _story_focus(self, text: str, fallback: str) -> str:
        value = self._compress_field_text(text)
        if not value or self._looks_like_outline_text(value):
            return self._compress_field_text(fallback)
        return value

    def _scene_anchor_line(
        self,
        packet: ChapterContextPacket,
        summary: str,
        protagonist: dict[str, str],
        index: int,
    ) -> str:
        core = self._compress_field_text(summary)
        time_anchor = packet.time_anchor or "此刻"
        location_anchor = packet.location_anchor or packet.current_place or "当前场域"
        if index == 1:
            if core:
                return f"{time_anchor}，{location_anchor}。{core}。"
            return f"{time_anchor}，{location_anchor}。{protagonist['name']}先看清谁在场，再开口。"
        if core:
            return core
        if index == 2:
            return f"{time_anchor}，{location_anchor}里的站位一下绷紧了。"
        if index == 3:
            return f"{protagonist['name']}刚把场面拽回来一点，后账已经贴上来了。"
        return f"{protagonist['name']}把下巴微微收住，等对面把下一句亮出来。"

    def _physical_reaction_line(self, protagonist: dict[str, str], emotional_beat: str, index: int) -> str:
        beat = self._compress_field_text(emotional_beat)
        name = protagonist["name"]
        options = [
            f"{name}呼吸停了半拍，又很快压回去。",
            f"{name}指节收紧，袖口被捏出一道浅痕。",
            f"{name}喉结动了一下，没有让声音先乱。",
            f"{name}眼神往旁边偏了一寸，又重新落回对面身上。",
        ]
        if not beat:
            return options[(index - 1) % len(options)]
        return f"{name}听见{beat}这几个字，指尖在袖口里停了一下。"

    def _speaker_current_goal(self, speaker: dict[str, str], fallback: str) -> str:
        goal = self._compress_field_text(speaker.get("goal", ""))
        return goal or self._compress_field_text(fallback) or "眼前这一局"

    def _dramatic_action_line(
        self,
        actor: str,
        profile: dict[str, str],
        purpose: str,
        focus: str,
    ) -> str:
        del focus
        texture = profile.get("texture", "")
        pressure_mode = profile.get("pressure_mode", "")
        tactic = profile.get("tactic", "")

        if purpose == "pressure":
            if "确认底牌" in pressure_mode:
                return f"{actor}目光没挪开，专挑对方那一下迟疑往里捅。"
            if texture == "利落":
                return f"{actor}肩膀一沉，整个人已经逼到对方面前。"
            return f"{actor}把手里的东西轻轻一搁，话锋顺着空当往命门里钻。"

        if purpose == "steady":
            if "先判断" in tactic:
                return f"{actor}先盯住对面眼神里那点松动，没让自己被火气带着走。"
            return f"{actor}脚下钉在原地，硬把那股快散掉的劲重新拢回来。"

        if purpose == "interrupt":
            if texture == "利落":
                return f"{actor}一句话抢进去，没给对面把后半截补齐的机会。"
            return f"{actor}顺着对方换气的空当插话，把后面的势头当场掐住。"

        if purpose == "cost":
            if texture == "冷硬":
                return f"{actor}手指猛地一扣，把翻上来的疼意重新按回骨头里。"
            return f"{actor}袖口在掌心里皱成一团，这一下还是被他咬牙接住了。"

        if purpose == "warning":
            if texture == "利落":
                return f"{actor}眼神一沉，再开口时字字都带着砸下来的劲。"
            return f"{actor}嗓音往下一压，话里那层分量却一下重了。"

        return f"{actor}站在原地没挪，只等对面把底牌翻到桌上。"

    def _dramatic_dialogue_line(
        self,
        speaker: dict[str, str],
        profile: dict[str, str],
        purpose: str,
        focus: str,
        fallback_goal: str,
    ) -> str:
        del focus
        goal = self._speaker_current_goal(speaker, fallback_goal)
        texture = profile.get("texture", "")
        tactic = profile.get("tactic", "")
        pressure_mode = profile.get("pressure_mode", "")
        role = str(speaker.get("role", "")).strip()

        if purpose == "probe":
            if "确认底牌" in pressure_mode:
                return "“都到这一步了，你还想把话往回吞？”"
            if texture == "利落":
                return "“别绕了，你到底接不接？”"
            return "“把你真正想要的那句亮出来。”"

        if purpose == "push":
            if "先判断" in tactic:
                return "“别的先放一边，今晚先看谁撑到最后。”"
            if texture == "利落":
                return "“这一轮，我就盯着你敢不敢松手。”"
            return "“眼前这一步，我现在就要落下去。”"

        if purpose == "counter":
            if texture == "冷硬":
                return "“这话定不了我。”"
            if texture == "利落":
                return "“别急着替我认输。”"
            if role == "主角":
                return "“拿这两句压我，还不够。”"
            return "“你想这么定，也得我点头。”"

        if purpose == "warning":
            if texture == "利落":
                return "“再拖半步，场子就真翻了。”"
            return "“再拖下去，场子就真收不住了。”"

        if purpose == "cost":
            if role == "主角":
                return "“这笔账，记我头上。”"
            return "“真砸下来，谁都别想装没看见。”"

        return f"“{goal}，我知道。”"

    def _join_scene_lines(self, first: str, second: str) -> str:
        left = first.strip()
        right = second.strip()
        if not left:
            return right
        if not right:
            return left
        if left.endswith(("。", "！", "？", "”")):
            return f"{left}{right}"
        return f"{left}，{right}"

    def _tail_clause(self, text: str) -> str:
        value = self._compress_field_text(text)
        if not value:
            return ""
        for separator in ("。", "；", "，", "："):
            if separator in value:
                parts = [item.strip() for item in value.split(separator) if item.strip()]
                if parts:
                    return parts[-1]
        return value

    def _impact_line(self, text: str, fallback: str) -> str:
        focus = self._story_focus(text, fallback)
        tail = self._tail_clause(focus) or self._compress_field_text(fallback) or fallback.strip("。")
        return f"{tail.rstrip('。')}。"

    def _plainify_generated_line(self, line: str) -> str:
        text = line.strip()
        if not text:
            return ""

        meta_tokens = (
            "本章",
            "章节",
            "读者",
            "体验目标",
            "戏剧",
            "核心冲突",
            "章卡",
            "场次",
            "scene",
            "Scene",
            "open thread",
            "爽点",
            "钩子",
            "伏笔",
            "人物弧光",
            "情绪曲线",
            "意义",
            "总结",
            "runtime",
            "evaluator",
            "blocking",
            "target_word_count",
            "复核",
            "修复完成",
            "形成下一章牵引",
            "推进结果",
        )
        if any(token in text for token in meta_tokens):
            return ""

        replacements = {
            "真正": "",
            "其实": "",
            "某种意义上": "",
            "不管怎么绕，": "",
            "前面那些话都不算数": "刚才的话就压不住人",
            "前面那些拉扯都白费": "刚才那口气就白撑了",
            "气氛架高": "声音抬高",
            "原地打转": "停在原处",
            "一点点贴到跟前": "挪到眼前",
            "压到脸上": "落到眼前",
            "这口气": "这句话",
            "眼前最急的还是": "",
            "眼下最不能松手的，就是": "",
            "必须被逼出看见结果": "得当场见真章",
            "必须被逼出可见结果": "得当场见真章",
            "推进结果": "动静",
            "形成下一章牵引": "把后面的门打开",
            "继续放行": "继续拖下去",
            "破坏人物可信度": "把人写散",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)

        while "。。" in text:
            text = text.replace("。。", "。")
        while "，，" in text:
            text = text.replace("，，", "，")
        return text.strip(" ，,")

    def _clean_scene_draft_lines(
        self,
        lines: list[str],
        direction: ChapterDirection | None = None,
    ) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        one_blade = "" if direction is None else direction.one_blade.strip().strip("“”")

        for line in lines:
            text = self._plainify_generated_line(line)
            if not text:
                continue
            key = text.replace("“", "").replace("”", "").replace("。", "").strip()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(text)
            if one_blade and one_blade in text:
                break

        return cleaned or [line.strip() for line in lines if line and line.strip()]

    def _pause_line(self, speaker: str, style: str = "default") -> str:
        if style == "tight":
            return f"{speaker}没再往下接。"
        if style == "cold":
            return f"{speaker}只是看着，没出声。"
        return f"{speaker}停了一下。"

    def _direction_scene_mode(self, direction: ChapterDirection | None, index: int) -> str:
        if direction is None:
            return ""
        scene_prefix = f"scene{index}:"
        for item in direction.scene_density_plan:
            text = item.strip()
            if text.startswith(scene_prefix):
                return text.split(":", 1)[1].strip()
        return ""

    def _direction_has_silence(self, direction: ChapterDirection | None, marker: str) -> bool:
        if direction is None:
            return False
        return marker in {item.strip() for item in direction.silence_points}

    def _direction_focus(self, direction: ChapterDirection | None, index: int) -> str:
        if direction is None:
            return ""
        if index == 1:
            return direction.opening_image
        if index == 2:
            return direction.midpoint_collision
        if index == 3:
            return direction.result_change
        return direction.closing_hook

    def _last_dialogue_line(self, lines: list[str]) -> str:
        for line in reversed(lines):
            text = line.strip()
            if text.startswith("“") and text.endswith("”"):
                return text
        return ""

    def _shape_dramatic_scene_lines(
        self,
        index: int,
        lines: list[str],
        direction: ChapterDirection | None = None,
        *,
        has_present_characters: bool = False,
        has_arrival_timing: bool = False,
        has_holdback: bool = False,
    ) -> list[str]:
        cleaned = [line.strip() for line in lines if line and line.strip()]
        if not cleaned:
            return cleaned
        scene_mode = self._direction_scene_mode(direction, index)

        if index == 1:
            if scene_mode in {"short-tight", "clear-entry"} and len(cleaned) >= 5:
                if has_present_characters and len(cleaned) >= 7:
                    return [
                        cleaned[0],
                        cleaned[1],
                        self._join_scene_lines(cleaned[2], cleaned[3]),
                        self._join_scene_lines(cleaned[4], cleaned[5]),
                        cleaned[-1],
                    ]
                return [
                    cleaned[0],
                    self._join_scene_lines(cleaned[1], cleaned[2]) if len(cleaned) > 2 else cleaned[1],
                    self._join_scene_lines(cleaned[3], cleaned[4]) if len(cleaned) > 4 else cleaned[-1],
                ]
            if has_present_characters and len(cleaned) >= 7:
                return [
                    cleaned[0],
                    cleaned[1],
                    self._join_scene_lines(cleaned[2], cleaned[3]),
                    cleaned[4],
                    self._join_scene_lines(cleaned[5], cleaned[6]),
                ]
            if len(cleaned) >= 6:
                return [
                    cleaned[0],
                    self._join_scene_lines(cleaned[1], cleaned[2]),
                    cleaned[3],
                    self._join_scene_lines(cleaned[4], cleaned[5]),
                ]

        if index == 2:
            return cleaned

        if index == 3:
            if scene_mode in {"heavy-slow", "visible-result"} and len(cleaned) >= 6:
                if has_arrival_timing and len(cleaned) >= 8:
                    return [
                        cleaned[0],
                        cleaned[1],
                        cleaned[2],
                        cleaned[3],
                        self._join_scene_lines(cleaned[4], cleaned[5]),
                        cleaned[6],
                        cleaned[7],
                    ]
                return [
                    cleaned[0],
                    cleaned[1],
                    self._join_scene_lines(cleaned[2], cleaned[3]),
                    cleaned[4],
                    cleaned[-1],
                ]
            if has_arrival_timing and len(cleaned) >= 8:
                return [
                    cleaned[0],
                    cleaned[1],
                    cleaned[2],
                    self._join_scene_lines(cleaned[3], cleaned[4]),
                    cleaned[5],
                    cleaned[6],
                    cleaned[7],
                ]
            if len(cleaned) >= 7:
                return [
                    cleaned[0],
                    cleaned[1],
                    self._join_scene_lines(cleaned[2], cleaned[3]),
                    cleaned[4],
                    cleaned[5],
                    cleaned[6],
                ]

        if index >= 4:
            if scene_mode in {"short-blade", "next-pull"} and len(cleaned) >= 5:
                blade_line = self._last_dialogue_line(cleaned) or cleaned[-2]
                blade_piece = blade_line
                blade_index = cleaned.index(blade_line) if blade_line in cleaned else -1
                if blade_index > 0 and "没再往下接" in cleaned[blade_index - 1]:
                    blade_piece = self._join_scene_lines(cleaned[blade_index - 1], blade_line)
                should_end_on_blade = bool(direction and direction.one_blade.strip())
                if has_holdback and len(cleaned) >= 7:
                    shaped = [
                        cleaned[0],
                        self._join_scene_lines(cleaned[1], cleaned[2]),
                        self._join_scene_lines(cleaned[3], cleaned[4]),
                        self._join_scene_lines(cleaned[-2], cleaned[-1]),
                    ]
                    if blade_piece not in shaped:
                        shaped.insert(len(shaped) - 1, blade_piece)
                    if should_end_on_blade and blade_piece in shaped:
                        return shaped[: shaped.index(blade_piece) + 1]
                    return shaped
                shaped = [
                    cleaned[0],
                    self._join_scene_lines(cleaned[1], cleaned[2]),
                    blade_piece,
                ]
                if not should_end_on_blade:
                    shaped.append(cleaned[-1])
                return shaped
            if has_holdback and len(cleaned) >= 7:
                return [
                    cleaned[0],
                    self._join_scene_lines(cleaned[1], cleaned[2]),
                    cleaned[3],
                    self._join_scene_lines(cleaned[4], cleaned[5]),
                    cleaned[6],
                ]
            if len(cleaned) >= 6:
                return [
                    cleaned[0],
                    self._join_scene_lines(cleaned[1], cleaned[2]),
                    cleaned[3],
                    self._join_scene_lines(cleaned[4], cleaned[5]),
                ]

        return cleaned

    def _build_dramatic_scene_draft(
        self,
        index: int,
        packet: ChapterContextPacket,
        brief: ChapterBrief,
        protagonist: dict[str, str],
        counterpart: dict[str, str],
        protagonist_profile: dict[str, str],
        counterpart_profile: dict[str, str],
        state: dict[str, str],
        scene_summary: str,
        scene_targets: dict[str, str],
        genre_profile: dict[str, str],
        direction: ChapterDirection | None = None,
    ) -> list[str]:
        pressure_noun = genre_profile["pressure_noun"]
        result_change = self._story_focus(
            (direction.result_change if direction is not None else "") or brief.result_change,
            state["protagonist_goal"],
        )
        closing_hook = self._story_focus(
            (direction.closing_hook if direction is not None else "") or brief.closing_hook,
            state["counterpart_fear"],
        )
        core_conflict = self._story_focus(
            (direction.core_conflict if direction is not None else "") or brief.core_conflict,
            state["counterpart_goal"],
        ) or state["counterpart_goal"]
        one_blade = ((direction.one_blade if direction is not None else "") or brief.one_blade).strip().strip("“”")
        payoff = self._story_focus(scene_targets["payoff_or_pressure"], result_change or state["protagonist_goal"])
        success = self._story_focus(scene_targets["success_criterion"], state["protagonist_goal"])
        counterpart_goal = self._story_focus(counterpart.get("goal") or state["counterpart_goal"], state["counterpart_goal"])

        if index == 1:
            scene_one_pressure = self._story_focus(core_conflict, f"{protagonist['name']}今晚还能不能站稳")
            scene_one_goal = self._story_focus(state["protagonist_goal"], "先把今晚这口气稳住")
            lines = [
                self._scene_anchor_line(packet, scene_summary or brief.opening_image, protagonist, index),
                f"{protagonist['name']}没有抢话，只把呼吸压平，没让自己的底牌先掉出来。",
                self._dramatic_action_line(counterpart["name"], counterpart_profile, "pressure", scene_one_pressure),
                self._dramatic_dialogue_line(counterpart, counterpart_profile, "probe", scene_one_pressure, counterpart_goal),
                self._dramatic_action_line(protagonist["name"], protagonist_profile, "steady", scene_one_goal),
                self._dramatic_dialogue_line(protagonist, protagonist_profile, "push", scene_one_goal, scene_one_goal),
                self._impact_line(scene_one_pressure, "这一步退了，就没有回身的余地"),
            ]
            if packet.present_characters:
                lines.insert(1, f"在场的人不多，只剩{'、'.join(packet.present_characters[:6])}。")
            return lines

        if index == 2:
            lines = [
                self._scene_anchor_line(packet, scene_summary or brief.midpoint_collision, protagonist, index),
                f"{counterpart['name']}借着灯下那半步距离把人卡住，专等他先露出撑不住的那一下。",
                f"{protagonist['name']}记着{state['protagonist_taboo']}，这一轮只换站位，不掀底牌。",
                self._dramatic_action_line(counterpart["name"], counterpart_profile, "warning", core_conflict),
                self._dramatic_dialogue_line(counterpart, counterpart_profile, "warning", state["counterpart_fear"], counterpart_goal),
                self._dramatic_action_line(protagonist["name"], protagonist_profile, "interrupt", state["protagonist_taboo"]),
                self._dramatic_dialogue_line(protagonist, protagonist_profile, "counter", state["protagonist_goal"], state["protagonist_goal"]),
                self._impact_line(f"被逼到台前的已经不止{protagonist['name']}", "被逼到台前的不止他一个"),
            ]
            if packet.message_flow:
                lines.insert(2, "消息要传，也只能先在这几个人之间转，不能比该知道的人更早出门。")
            if self._direction_has_silence(direction, "scene2-after-warning"):
                lines.insert(5, self._pause_line(protagonist["name"], "tight"))
            return lines

        if index == 3:
            scene_three_anchor = self._story_focus(scene_summary, f"{protagonist['name']}刚抢回半口气，后面的动静又追上来了")
            scene_three_cost = self._story_focus(payoff or result_change, f"刚抢回来的东西转眼就得拿去抵账")
            scene_three_result = self._story_focus(success or payoff or result_change, f"这一下带来的后账已经躲不开")
            lines = [
                self._scene_anchor_line(packet, scene_three_anchor, protagonist, index),
                self._physical_reaction_line(protagonist, brief.emotional_beat, index),
                f"{protagonist['name']}刚把这一步接住，新的{pressure_noun}已经顺着背脊爬了上来。",
                self._dramatic_action_line(protagonist["name"], protagonist_profile, "cost", scene_three_cost),
                f"{protagonist['name']}喉结轻轻滚了一下，心里那笔账却越掂越沉。",
                self._pause_line(counterpart["name"], "cold"),
                f"{counterpart['name']}目光钉在他脸上，像是在看他还能把后手藏多久。",
                self._impact_line(scene_three_result, "这一下带来的后账已经躲不开"),
            ]
            if packet.arrival_timing:
                lines.insert(3, self._render_arrival_timing(packet.arrival_timing))
            return lines

        scene_four_anchor = self._story_focus(scene_summary, f"门边那点动静还悬着，谁都没法当没听见")
        scene_four_warning = self._story_focus(state["counterpart_fear"], "麻烦已经顺着门缝逼到眼前")
        scene_four_exit = self._story_focus(closing_hook or brief.hook_goal, f"门还没关死，新的{pressure_noun}已经跟上来")
        lines = [
            self._scene_anchor_line(packet, scene_four_anchor, protagonist, index),
            self._impact_line(scene_four_warning, "麻烦已经顺着门缝逼到眼前"),
            self._dramatic_action_line(counterpart["name"], counterpart_profile, "warning", scene_four_warning),
            self._dramatic_dialogue_line(counterpart, counterpart_profile, "warning", scene_four_warning, counterpart_goal),
            f"{protagonist['name']}把下巴微微一收，胸口那点翻起来的乱意又被他压了回去。",
            (f"“{one_blade}”" if one_blade else self._dramatic_dialogue_line(
                protagonist,
                protagonist_profile,
                "push",
                state["protagonist_goal"],
                state["protagonist_goal"],
            )),
            self._impact_line(scene_four_exit, f"门还没关死，新的{pressure_noun}已经跟上来"),
        ]
        if self._direction_has_silence(direction, "scene4-before-final-blade"):
            lines.insert(len(lines) - 2, self._pause_line(protagonist["name"], "tight"))
        if packet.must_not_payoff_yet:
            lines.append(self._pause_line(protagonist["name"], "tight"))
        return lines

    def _build_dramatic_scene_paragraphs(
        self,
        packet: ChapterContextPacket,
        brief: ChapterBrief,
        protagonist: dict[str, str],
        counterpart: dict[str, str],
        protagonist_profile: dict[str, str],
        counterpart_profile: dict[str, str],
        genre_profile: dict[str, str],
        direction: ChapterDirection | None = None,
    ) -> tuple[list[dict[str, object]], list[str]]:
        state = self._state_summary(packet, brief)
        outline = self._build_scene_outline(packet, brief, protagonist, counterpart, genre_profile)
        scenes: list[dict[str, object]] = []
        manuscript_paragraphs: list[str] = []

        for index, item in enumerate(outline, start=1):
            scene_summary = self._scene_summary(brief, str(item["summary"]), index)
            scene_targets = self._scene_targets(brief, index)
            beats = self._scene_beats(packet, protagonist, counterpart, state, genre_profile)
            beats = self._augment_scene_beats(brief, beats, index)
            draft_lines = self._build_dramatic_scene_draft(
                index,
                packet,
                brief,
                protagonist,
                counterpart,
                protagonist_profile,
                counterpart_profile,
                state,
                scene_summary,
                scene_targets,
                genre_profile,
                direction,
            )
            draft_lines = self._shape_dramatic_scene_lines(
                index,
                draft_lines,
                direction,
                has_present_characters=bool(packet.present_characters),
                has_arrival_timing=bool(packet.arrival_timing),
                has_holdback=bool(packet.must_not_payoff_yet),
            )
            draft_lines = self._clean_scene_draft_lines(draft_lines, direction)
            scenes.append(
                {
                    "label": item["label"],
                    "title": item["title"],
                    "summary": scene_summary,
                    "scene_plan_focus": scene_targets["scene_plan"],
                    "direction_mode": self._direction_scene_mode(direction, index),
                    "director_focus": self._direction_focus(direction, index),
                    "payoff_or_pressure": scene_targets["payoff_or_pressure"],
                    "success_criterion": scene_targets["success_criterion"],
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

    def _build_scene_paragraphs(
        self,
        packet: ChapterContextPacket,
        brief: ChapterBrief,
        protagonist: dict[str, str],
        counterpart: dict[str, str],
        protagonist_profile: dict[str, str],
        counterpart_profile: dict[str, str],
        genre_profile: dict[str, str],
        direction: ChapterDirection | None = None,
    ) -> tuple[list[dict[str, object]], list[str]]:
        return self._build_dramatic_scene_paragraphs(
            packet,
            brief,
            protagonist,
            counterpart,
            protagonist_profile,
            counterpart_profile,
            genre_profile,
            direction,
        )

    def _scene_summary(self, brief: ChapterBrief, fallback: str, index: int) -> str:
        scene_index = index - 1
        generic_fallbacks = {
            1: "走廊里忽然静了一瞬，连脚步声都像贴着地面走",
            2: "灯下那点站位一拧，场子立刻绷了起来",
            3: "场面刚往回拽了一点，后账已经追到眼前",
            4: "门边那点动静还悬着，谁都知道事情没完",
        }
        safe_fallback = self._story_focus(fallback, generic_fallbacks.get(index, fallback))
        if 0 <= scene_index < len(brief.scene_plan):
            scene_plan = brief.scene_plan[scene_index].strip()
            softened = self._narrativize_scene_plan(scene_plan, index)
            if self._has_dramatic_brief(brief) and softened:
                return softened
            if softened and softened != safe_fallback.strip():
                return f"{softened}。{safe_fallback}".strip()
            if softened:
                return softened
        return safe_fallback

    def _scene_targets(self, brief: ChapterBrief, index: int) -> dict[str, str]:
        scene_index = index - 1
        scene_plan = brief.scene_plan[scene_index].strip() if 0 <= scene_index < len(brief.scene_plan) else ""
        payoff_or_pressure = (
            brief.required_payoff_or_pressure[scene_index].strip()
            if 0 <= scene_index < len(brief.required_payoff_or_pressure)
            else (brief.required_payoff_or_pressure[0].strip() if brief.required_payoff_or_pressure else "")
        )
        success_criterion = (
            brief.success_criteria[scene_index].strip()
            if 0 <= scene_index < len(brief.success_criteria)
            else (brief.success_criteria[0].strip() if brief.success_criteria else "")
        )
        return {
            "scene_plan": scene_plan,
            "payoff_or_pressure": payoff_or_pressure,
            "success_criterion": success_criterion,
        }

    def _normalize_directive(self, text: str) -> str:
        return text.strip().rstrip("。.!！?？")

    def _compress_field_text(self, text: str) -> str:
        value = self._normalize_directive(text)
        replacements = {
            "只有": "只到",
            "可见": "看见",
            "尚未外传": "还没外传",
            "只能传开": "才会传开",
            "处理结果": "结果",
            "当前": "眼下",
            "暂时": "一时",
        }
        for old, new in replacements.items():
            value = value.replace(old, new)
        return value

    def _render_arrival_timing(self, text: str) -> str:
        value = self._normalize_directive(text)
        if not value:
            return ""
        if "当夜只能传开公开动作" in value and "回府后" in value:
            return "当夜能传开的，也只有人人看见的那一下，真到后手露底，怎么也得拖到回府后。"
        return f"就算风声真传开，也得等到{self._compress_field_text(value)}，中间这一段谁都抄不了近路。"

    def _render_knowledge_boundary(self, text: str) -> str:
        value = self._normalize_directive(text)
        if not value:
            return ""
        if "可知=" in value and "不可知=" in value:
            visible, hidden = value.split("不可知=", 1)
            visible = visible.replace("可知=", "").strip("：:；;，, ")
            hidden = hidden.strip()
            return f"眼下真正看清局面的，只有{visible}；至于{hidden}，还都隔着一层。"
        return f"眼下能摸到真相边上的人不多，{self._compress_field_text(value)}。"

    def _render_time_anchor(self, text: str, location: str) -> str:
        value = self._normalize_directive(text)
        place = self._normalize_directive(location)
        if not value:
            return ""
        if place:
            return f"{value}，{place}里的动静一下都压低了。"
        return f"{value}这一刻，四周的动静都跟着压低了。"

    def _narrativize_scene_plan(self, scene_plan: str, index: int) -> str:
        del index
        plan = self._normalize_directive(scene_plan)
        if not plan:
            return ""
        if any(token in plan for token in ("本章", "章节", "读者", "体验", "戏剧", "核心冲突", "章卡", "open thread")):
            return ""
        if plan.startswith("开场先锁定"):
            core = plan.replace("开场先锁定", "", 1).strip()
            core = core.replace("不要先讲背景", "").strip(" ，,、")
            if "压力" in core:
                return "走廊里忽然静了一瞬，连脚步声都像贴着地面走。"
            return f"人一进场，先撞进眼里的就是{core}。"
        if plan.startswith("起章先钉死时空锚点："):
            core = plan.split("：", 1)[1].strip()
            if "/" in core:
                time_part, place_part = [item.strip() for item in core.split("/", 1)]
                return self._render_time_anchor(time_part, place_part)
            return self._render_time_anchor(core, "")
        if plan.startswith("在场人物只保留："):
            core = plan.split("：", 1)[1].strip()
            return f"场上能把这口气接住的，也只剩{core}"
        if plan.startswith("知情边界要稳定："):
            core = self._render_knowledge_boundary(plan.split("：", 1)[1].strip())
            return core or ""
        return ""

    def _augment_scene_beats(self, brief: ChapterBrief, beats: list[str], index: int) -> list[str]:
        del index
        augmented = list(beats)
        if brief.progress_floor:
            augmented.append(f"floor: {brief.progress_floor}")
        if brief.progress_ceiling:
            augmented.append(f"ceiling: {brief.progress_ceiling}")
        if brief.must_not_payoff_yet:
            augmented.append(f"hold_back: {'、'.join(brief.must_not_payoff_yet[:2])}")
        if brief.allowed_change_scope:
            augmented.append(f"change_scope: {'、'.join(brief.allowed_change_scope[:2])}")
        return augmented
    def _scene_cards(self, scenes: list[dict[str, object]]) -> list[dict[str, str]]:
        return [
            {
                "scene": str(item["label"]),
                "title": str(item["title"]),
                "summary": str(item["summary"]),
                "direction_mode": str(item.get("direction_mode", "")),
                "director_focus": str(item.get("director_focus", "")),
                "result_type": str(item["result_type"]),
                "cost_type": str(item["cost_type"]),
                "hook_type": str(item["hook_type"]),
            }
            for item in scenes
        ]
    def _outcome_signature(self, brief: ChapterBrief, genre_profile: dict[str, str]) -> dict[str, str]:
        return {
            "chapter_result": brief.result_change.strip() or brief.chapter_function.strip() or "主角完成一次有效反击",
            "result_type": "partial_win_with_pressure_kept",
            "cost_type": "cost_upgrade",
            "hook_type": "cost_upgrade",
            "next_pull": brief.closing_hook.strip() or brief.hook_goal.strip() or genre_profile["hook_phrase"],
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
        del notes
        lines = ["# Runtime Draft", ""]
        for item in scenes:
            lines.extend([f"## {item['label']} {item['title']}", ""])
            lines.extend(str(line) for line in item["draft_lines"] if str(line).strip())
            lines.append("")
        return "\n".join(lines).strip() + "\n"
    def _build_review_notes(
        self,
        scenes: list[dict[str, object]],
        outcome_signature: dict[str, str],
        protagonist: dict[str, str],
        counterpart: dict[str, str],
        protagonist_profile: dict[str, str],
        counterpart_profile: dict[str, str],
        packet: ChapterContextPacket,
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
                "## Continuity Guardrails",
                f"- time_anchor: {packet.time_anchor or 'missing'}",
                f"- location_anchor: {packet.location_anchor or packet.current_place or 'missing'}",
                f"- present_characters: {'、'.join(packet.present_characters) if packet.present_characters else 'missing'}",
                f"- knowledge_boundary: {packet.knowledge_boundary or 'missing'}",
                f"- message_flow: {packet.message_flow or 'missing'}",
                f"- arrival_timing: {packet.arrival_timing or 'missing'}",
                f"- who_knows_now: {packet.who_knows_now or 'missing'}",
                f"- who_cannot_know_yet: {packet.who_cannot_know_yet or 'missing'}",
                f"- travel_time_floor: {packet.travel_time_floor or 'missing'}",
                f"- resource_state: {packet.resource_state or 'missing'}",
                f"- progress_floor: {packet.progress_floor or 'missing'}",
                f"- progress_ceiling: {packet.progress_ceiling or 'missing'}",
                f"- must_not_payoff_yet: {'、'.join(packet.must_not_payoff_yet) if packet.must_not_payoff_yet else 'missing'}",
                f"- allowed_change_scope: {'、'.join(packet.allowed_change_scope) if packet.allowed_change_scope else 'missing'}",
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

    def _build_chapter_blueprint(
        self,
        scenes: list[dict[str, object]],
        outcome_signature: dict[str, str],
        packet: ChapterContextPacket,
    ) -> str:
        lines = ["# Chapter Blueprint", "", "## Continuity Anchors",
            f"- time_anchor: {packet.time_anchor or 'missing'}",
            f"- location_anchor: {packet.location_anchor or packet.current_place or 'missing'}",
            f"- present_characters: {'、'.join(packet.present_characters) if packet.present_characters else 'missing'}",
            f"- knowledge_boundary: {packet.knowledge_boundary or 'missing'}",
            f"- message_flow: {packet.message_flow or 'missing'}",
            f"- arrival_timing: {packet.arrival_timing or 'missing'}",
            f"- who_knows_now: {packet.who_knows_now or 'missing'}",
            f"- who_cannot_know_yet: {packet.who_cannot_know_yet or 'missing'}",
            f"- travel_time_floor: {packet.travel_time_floor or 'missing'}",
            f"- resource_state: {packet.resource_state or 'missing'}",
            f"- progress_floor: {packet.progress_floor or 'missing'}",
            f"- progress_ceiling: {packet.progress_ceiling or 'missing'}",
            f"- must_not_payoff_yet: {'、'.join(packet.must_not_payoff_yet) if packet.must_not_payoff_yet else 'missing'}",
            f"- allowed_change_scope: {'、'.join(packet.allowed_change_scope) if packet.allowed_change_scope else 'missing'}",
            "",
            "## Scene Cards"]
        for item in scenes:
            lines.extend(
                [
                    f"### {item['label']} {item['title']}",
                    f"- summary: {item['summary']}",
                    f"- scene_plan_focus: {item.get('scene_plan_focus', '') or 'none'}",
                    f"- payoff_or_pressure: {item.get('payoff_or_pressure', '') or 'none'}",
                    f"- success_criterion: {item.get('success_criterion', '') or 'none'}",
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
        ]
        return "\n".join(lines)

    def _compose_manuscript_text(
        self,
        brief: ChapterBrief,
        manuscript_paragraphs: list[str],
        outcome_signature: dict[str, str],
        genre_profile: dict[str, str],
        mission: dict[str, object],
        protagonist: dict[str, str],
        counterpart: dict[str, str],
    ) -> str:
        del mission, protagonist, counterpart
        manuscript_chunks = [paragraph for paragraph in manuscript_paragraphs if paragraph is not None]
        if not any(chunk.strip() for chunk in manuscript_chunks):
            manuscript_chunks = ["这一章的正文还没有生成出来。"]
        return self._build_reader_manuscript(brief, manuscript_chunks, outcome_signature, genre_profile)

    def _append_progression_paragraphs(
        self,
        manuscript_text: str,
        brief: ChapterBrief,
        outcome_signature: dict[str, str],
        protagonist: dict[str, str],
        counterpart: dict[str, str],
        state: dict[str, str],
    ) -> str:
        chapter_result = self._clean_story_phrase(
            str(outcome_signature.get("chapter_result", "")),
            fallback="把主动权拿回来",
        )
        next_pull = self._clean_story_phrase(
            str(outcome_signature.get("next_pull", "")),
            fallback="下一步的价码已经被重新抬高了",
        )
        counterpart_goal = self._clean_story_phrase(
            counterpart.get("goal", "") or state["counterpart_goal"],
            fallback="把他袖子里那点后手逼出来",
        )
        protagonist_taboo = self._clean_story_phrase(
            protagonist.get("taboo", "") or state["protagonist_taboo"],
            fallback="不把命交给运气",
        )
        progression_paragraphs = [
            (
                f"{protagonist['name']}把这句话扔回去以后，压在肩上的那股劲总算松开一线。"
                f"可那点轻快只是一闪，贴上来的代价立刻又把人拽回原地，"
                f"逼得他连{protagonist_taboo}这条线都不敢碰。"
            ),
            "“我只认这一回合，谁也别想把我再按回去。”",
            "“你真敢往前走，后面的代价就得立刻认。”",
            (
                f"他把肩背重新顶直，先去看苏晚的眼睛，再去看她卡住去路的站位。"
                f"场子虽然被他从对方手里硬掰回来半寸，后面那笔账却已经顺着这半寸缠了上来。"
            ),
            (
                f"脚边那点积水被鞋跟带开，细碎的水声顺着走廊往外窜。"
                f"那声音一落地，原先还能糊过去的拉扯也跟着断了；谁再往后缩，谁就得把失手的后果当场接住。"
            ),
            (
                f"{counterpart['name']}也听出了这一下的分量，没有再把人往死里逼，只把目光钉在{protagonist['name']}脸上。"
                f"她盯的不是嘴上那句软话，而是{counterpart_goal}，等着看他会不会真把这一步落成动作。"
            ),
            (
                f"空气里那点僵意没有散，只是换了个方向压回来。"
                f"现在轮到{protagonist['name']}把后手拿稳：一旦下一步踩空，刚抢回来的位置就会原样吐出去，"
                f"连带着刚刚压住的代价一起翻上台面。"
            ),
            (
                f"后面的路没人挑明，可门边钻进来的冷风已经把那层窗户纸吹薄了。"
                f"{protagonist['name']}刚攥回手里的那点主动，还没焐热，{next_pull}。"
            ),
            "“下一步要是还想逼我低头，那就把账和代价一起摆到明面上。”",
            (
                f"连走廊尽头那盏忽明忽暗的灯都像在催人往前。"
                f"这一夜既然已经把口子撕开，后面压上来的东西只会更硬。"
            ),
        ]
        body = manuscript_text.strip()
        heading = f"# Chapter {brief.chapter:03d} {self._chapter_title(brief)}"
        if body.startswith(heading):
            body = body[len(heading):].lstrip()
        return self._build_reader_manuscript(
            brief,
            [body, "", *progression_paragraphs],
            outcome_signature,
            {},
        )

    def _append_character_anchor_paragraphs(
        self,
        manuscript_text: str,
        brief: ChapterBrief,
        outcome_signature: dict[str, str],
        genre_profile: dict[str, str],
        protagonist: dict[str, str],
        counterpart: dict[str, str],
        state: dict[str, str],
    ) -> str:
        anchor_paragraphs: list[str] = []
        protagonist_goal = (protagonist.get("goal", "") or state["protagonist_goal"]).strip()
        counterpart_goal = (counterpart.get("goal", "") or state["counterpart_goal"]).strip()
        counterpart_fear = (counterpart.get("fear", "") or state["counterpart_fear"]).strip()
        next_pull = str(outcome_signature.get("next_pull", "")).strip()
        clean_protagonist_goal = self._clean_story_phrase(protagonist_goal, fallback="把主动权拿回来")
        clean_counterpart_goal = self._clean_story_phrase(counterpart_goal, fallback="把他袖子里那点后手逼出来")
        clean_counterpart_fear = self._clean_story_phrase(counterpart_fear, fallback="局面真的压崩")
        clean_next_pull = self._clean_story_phrase(next_pull, fallback="下一步的价码已经被重新抬高了")
        if clean_protagonist_goal and clean_protagonist_goal not in manuscript_text:
            anchor_paragraphs.append(f"{protagonist['name']}把要紧的事死死压在心里：{clean_protagonist_goal}，别的都得往后放。")
        if clean_counterpart_goal and clean_counterpart_goal not in manuscript_text:
            anchor_paragraphs.append(f"{counterpart['name']}还盯着{clean_counterpart_goal}，就等他把话真正落成动作。")
        if clean_counterpart_fear and clean_counterpart_fear not in manuscript_text:
            anchor_paragraphs.append(f"{counterpart['name']}真正防着的，是{clean_counterpart_fear}一下子压下来，把场子彻底掀翻。")
        if clean_next_pull and clean_next_pull not in manuscript_text:
            anchor_paragraphs.append(f"门还没关死，{clean_next_pull}。")
        if "确认底牌" not in manuscript_text:
            anchor_paragraphs.append(f"她没有把话说透，只是借着灯影和站位一寸寸试探，想先确认底牌到底在不在{protagonist['name']}手里。")
        if "停了一拍" not in manuscript_text and "没有逼到底" not in manuscript_text:
            anchor_paragraphs.append(f"话逼到这一步，{counterpart['name']}还是停了一拍，没有逼到底，只把最后半步留给{protagonist['name']}自己选。")
        if not anchor_paragraphs:
            return manuscript_text
        body = manuscript_text.strip()
        heading = f"# Chapter {brief.chapter:03d} {self._chapter_title(brief)}"
        if body.startswith(heading):
            body = body[len(heading):].lstrip()
        return self._build_reader_manuscript(
            brief,
            [body, "", *anchor_paragraphs],
            outcome_signature,
            genre_profile,
        )

    def draft(
        self,
        project_dir: Path,
        packet: ChapterContextPacket,
        brief: ChapterBrief,
        decision: RuntimeDecision,
        *,
        direction: ChapterDirection | None = None,
        dry_run: bool = False,
    ) -> dict[str, object]:
        del dry_run
        draft_dir = self._draft_dir(project_dir, brief.chapter)
        draft_dir.mkdir(parents=True, exist_ok=True)
        rewrite_text = self._build_rewrite_handoff(brief, decision) if decision.decision == "revise" else ""

        protagonist, counterpart = self._speaker_profiles(project_dir)
        protagonist_profile = self._role_voice_profile(protagonist)
        counterpart_profile = self._role_voice_profile(counterpart)
        genre_profile = self._genre_profile(project_dir)
        state = self._state_summary(packet, brief)
        outcome_signature = self._outcome_signature(brief, genre_profile)
        scenes, manuscript_paragraphs = self._build_scene_paragraphs(
            packet,
            brief,
            protagonist,
            counterpart,
            protagonist_profile,
            counterpart_profile,
            genre_profile,
            direction,
        )
        mission = self._build_minimal_mission_context(packet, brief, direction)
        boundaries = self._build_minimal_boundaries_context(packet, brief, direction)
        cast_voice = self._build_minimal_cast_voice_context(
            protagonist,
            counterpart,
            protagonist_profile,
            counterpart_profile,
        )
        writer_rules = self._build_minimal_writer_rules_context(direction)
        prompt_text = self._assemble_minimal_writer_prompt(
            project_dir=project_dir,
            mission=mission,
            boundaries=boundaries,
            cast_voice=cast_voice,
            writer_rules=writer_rules,
        )
        manuscript_text = self._compose_manuscript_text(
            brief,
            manuscript_paragraphs,
            outcome_signature,
            genre_profile,
            mission,
            protagonist,
            counterpart,
        )
        manuscript_text = self._append_progression_paragraphs(
            manuscript_text,
            brief,
            outcome_signature,
            protagonist,
            counterpart,
            state,
        )
        manuscript_text = self._append_character_anchor_paragraphs(
            manuscript_text,
            brief,
            outcome_signature,
            genre_profile,
            protagonist,
            counterpart,
            state,
        )
        character_constraints = self._character_constraints(
            manuscript_text,
            protagonist,
            counterpart,
            protagonist_profile,
            counterpart_profile,
            state,
        )
        review_text = self._build_review_notes(
            scenes,
            outcome_signature,
            protagonist,
            counterpart,
            protagonist_profile,
            counterpart_profile,
            packet,
        )
        artifact_paths = self._save_minimal_writer_artifacts(
            draft_dir=draft_dir,
            prompt_text=prompt_text,
            manuscript_text=manuscript_text,
            review_text=review_text,
            rewrite_text=rewrite_text,
        )
        prompt_path = artifact_paths["prompt_path"]
        manuscript_path = artifact_paths["manuscript_path"]
        review_notes_path = artifact_paths["review_notes_path"]
        rewrite_handoff_path = artifact_paths["rewrite_handoff_path"]
        assert prompt_path is not None
        assert manuscript_path is not None
        assert review_notes_path is not None

        return {
            "project": project_dir.as_posix(),
            "chapter": brief.chapter,
            "status": "rewritten-runtime-output" if decision.decision == "revise" else "drafted-writer-prompt",
            "draft_path": prompt_path.as_posix(),
            "writer_prompt_path": prompt_path.as_posix(),
            "review_notes_path": review_notes_path.as_posix(),
            "blueprint_path": "",
            "editorial_summary_path": "",
            "manuscript_path": manuscript_path.as_posix(),
            "rewrite_handoff_path": "" if rewrite_handoff_path is None else rewrite_handoff_path.as_posix(),
            "rewrite_handoff_preview": "\n".join(rewrite_text.splitlines()[:8]) if rewrite_text else "",
            "draft_preview": "\n".join(prompt_text.splitlines()[:12]),
            "review_notes_preview": "\n".join(review_text.splitlines()[:12]),
            "blueprint_preview": "",
            "editorial_summary_preview": "",
            "manuscript_preview": "\n".join(manuscript_text.splitlines()[:12]),
            "scene_count": len(scenes),
            "word_count": len("".join(manuscript_text.splitlines())),
            "scene_cards": self._scene_cards(scenes),
            "outcome_signature": outcome_signature,
            "character_constraints": character_constraints,
            "direction": {} if direction is None else direction.to_dict(),
        }
