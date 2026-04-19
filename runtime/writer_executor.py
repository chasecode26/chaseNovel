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
        personality = character.get("personality", "")
        if any(token in personality for token in ("冷", "稳", "寡言", "谨慎")):
            profile["texture"] = "冷硬"
            profile["sentence_length"] = "中短句"
        elif any(token in personality for token in ("急", "利", "直", "狠")):
            profile["texture"] = "利落"
            profile["sentence_length"] = "短句"
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

    def _is_counterpart(self, speaker: dict[str, str]) -> bool:
        role = speaker.get("role", "")
        relationship = speaker.get("relationship", "")
        role_text = role.lower()
        relationship_text = relationship.lower()
        return any(token in role for token in ("盟友", "搭档", "对手", "反派")) or any(
            token in role_text or token in relationship_text for token in ("ally", "friend", "opponent", "villain")
        )

    def _line_pool(self, speaker: dict[str, str], profile: dict[str, str], intent: str) -> list[str]:
        goal = speaker.get("goal") or "局面必须被压住"
        fear = speaker.get("fear") or "局面彻底失控"
        counterpart_like = self._is_counterpart(speaker)
        tactic = profile.get("tactic", "")
        pressure_mode = profile.get("pressure_mode", "")
        texture = profile.get("texture", "")
        sentence_length = profile.get("sentence_length", "")

        if intent == "probe":
            if counterpart_like and "确认底牌" in pressure_mode:
                return [
                    "你先把底牌掀一角，我才知道这一步该站哪边。",
                    "你先漏一句真话，我才好替你看路。",
                    "别只拿场面压我，先让我知道你手里还扣着什么。",
                ]
            if counterpart_like and "压场" in pressure_mode:
                return [
                    "别绕。你现在就把话落地。",
                    "少兜圈子，把你真正要的那句先说出来。",
                    "把话挑明，别逼我一句句替你拆。",
                ]
            if "先判断" in tactic:
                return [
                    "你先别催，我得先把活路看清。",
                    "先别把我往前推，这一步我得先看明白。",
                    "急着要答案没用，我先得把退路摸出来。",
                ]
            return [
                "你盯结果，我先看这一步能不能走。",
                "结果先别急着算，我先看眼前这道坎怎么过。",
                "你要的是一句准话，我先得把局面站稳。",
            ]
        if intent == "push":
            if "先判断" in tactic:
                return [
                    f"我先认准一件事，{goal}。",
                    f"别的先不谈，我先把{goal}扣死。",
                    f"眼下只剩一条线，{goal}。",
                ]
            if "先顶回去" in tactic:
                return [
                    f"别的先放下，{goal}。",
                    f"你先别吵，我现在只做{goal}。",
                    f"这一步不谈虚的，只看{goal}。",
                ]
            return [
                f"这一步我只看{goal}。",
                f"眼前先办一件事，{goal}。",
                f"现在能落地的只有{goal}。",
            ]
        if intent == "fear":
            if counterpart_like and "压场" in pressure_mode:
                return [
                    f"再拖，{fear}。到时候谁都别想收场。",
                    f"你再慢半步，{fear}，到时候一个都跑不掉。",
                    f"别拿命耗，{fear}已经在往前顶了。",
                ]
            if counterpart_like:
                return [
                    f"再拖下去，{fear}，我兜不住你。",
                    f"你还想拖？{fear}一到，我这边先断。",
                    f"再往后压，{fear}，到时候我也替你补不上。",
                ]
            if "留余地" in pressure_mode:
                return [
                    f"急没有用，{fear}也得先有人扛住。",
                    f"怕归怕，先把{fear}挡在门外再说。",
                    f"现在慌也没用，先有人把{fear}顶住。",
                ]
            return [
                f"怕归怕，{fear}已经到门口了。",
                f"你可以怕，但{fear}不会等人。",
                f"这不是吓唬人，{fear}已经贴脸了。",
            ]
        if intent == "counter":
            if texture == "利落" or sentence_length == "短句":
                return ["这话不算。", "先别替我定输赢。", "轮不到你现在盖棺。"]
            if texture == "冷硬":
                return ["我还没退。", "我还站在这。", "这一步我没让。"]
            return ["现在还轮不到我认输。", "这口气还没到散的时候。", "你现在下结论太早了。"]
        if intent == "cost":
            if texture == "冷硬":
                return ["东西我拿了，账也认。", "该收的我收下，后账我自己背。", "这份好处我不推，代价也不躲。"]
            if texture == "利落":
                return ["好处先收，后账慢慢算。", "这口肉我先咬住，后面的账再说。", "东西到手就行，欠下的我记着。"]
            return ["这份代价我记下，不往外推。", "账我先记着，没人替我扛。", "该落我头上的，我不往别人身上甩。"]
        if intent == "warning":
            if counterpart_like and "压场" in pressure_mode:
                return [
                    "这一刀要是真落下来，后面只会更难看。",
                    "眼前要是压不住，后面的口子只会越撕越大。",
                    "别把这一下当小事，后头那摊更脏。",
                ]
            if counterpart_like:
                return [
                    "你别只看眼前，后面的窟窿比这一下大。",
                    "这一下不是最狠的，真正麻烦的还在后面。",
                    "前面这口气先别松，后头还有更大的洞。",
                ]
            if "留余地" in pressure_mode:
                return [
                    "代价我看见了，所以这一步我不会乱伸手。",
                    "我知道后头有账，所以现在不能乱拿。",
                    "后面还要走路，这一步我得给自己留口气。",
                ]
            return [
                "后面的账还没来，现在不能把路走死。",
                "眼前能顶住，不代表后头也扛得住。",
                "这一下过去了，后面的账照样会找上门。",
            ]
        return [f"{goal}。"]

    def _line_for(self, speaker: dict[str, str], profile: dict[str, str], intent: str, scene_index: int = 0) -> str:
        options = self._line_pool(speaker, profile, intent)
        name = speaker.get("name", "角色")
        offset = sum(ord(char) for char in (name + intent)) + scene_index
        return f"“{options[offset % len(options)]}”"

    def _action_pool(self, actor: str, mood: str) -> list[str]:
        if mood == "observe":
            return [
                f"{actor}先看了一眼门口，又扫了一遍能退开的空当。",
                f"{actor}没急着出声，先把四周的路和人都过了一遍。",
                f"{actor}先把目光从门边、桌角一路带过去，确认哪一处最先会动。",
            ]
        if mood == "pressure":
            return [
                f"{actor}把话往前逼了一寸，连喘气的空当都没留。",
                f"{actor}顺着那点松动继续往里压，明显不打算给人缓口气。",
                f"{actor}盯得更紧，像是非要当场把话逼实。",
            ]
        if mood == "steady":
            return [
                f"{actor}把气息压平，没顺着对面的火气走。",
                f"{actor}站着没动，只把声音一点点收稳。",
                f"{actor}没抢那口气，先把自己的节奏按住。",
            ]
        if mood == "interrupt":
            return [
                f"{actor}抬眼把话截断。",
                f"{actor}没等对面说完，就把那句顶了回去。",
                f"{actor}在对方再开口前先把节奏卡住了。",
            ]
        if mood == "cost":
            return [
                f"{actor}没把情绪露出来，只把那口气硬压回去。",
                f"{actor}指节收紧了一下，面上却没露半点虚。",
                f"{actor}把那点起伏压在喉咙口，面上还是稳的。",
            ]
        if mood == "warning":
            return [
                f"{actor}把声音压低，话却比刚才更重。",
                f"{actor}停了半拍，再开口时已经不带试探。",
                f"{actor}没再抬声，只把后果一层层往前摆。",
            ]
        return [f"{actor}没有再多说。"]

    def _action_for(self, actor: str, mood: str, scene_index: int) -> str:
        options = self._action_pool(actor, mood)
        offset = sum(ord(char) for char in (actor + mood)) + scene_index
        return options[offset % len(options)]

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
        packet: ChapterContextPacket,
        protagonist: dict[str, str],
        counterpart: dict[str, str],
        state: dict[str, str],
        genre_profile: dict[str, str],
    ) -> list[str]:
        win_noun = genre_profile["win_noun"]
        pressure_noun = genre_profile["pressure_noun"]
        beats = [
            f"{protagonist['name']}先判断局面，目标是{state['protagonist_goal']}并拿回{win_noun}",
            f"{counterpart['name']}不断施压，想确认{state['counterpart_goal']}",
            f"{protagonist['name']}始终守住禁忌：{state['protagonist_taboo']}",
            f"章内风险被重新命名成：{state['counterpart_fear']}，并升级成新的{pressure_noun}",
        ]
        if packet.time_anchor or packet.location_anchor:
            beats.insert(0, f"起章时空锚点固定为：{packet.time_anchor or '当前时间'} / {packet.location_anchor or packet.current_place or '当前地点'}")
        if packet.present_characters:
            beats.append(f"当前在场人物限定：{'、'.join(packet.present_characters[:6])}")
        if packet.message_flow:
            beats.append(f"消息传播链必须成立：{packet.message_flow}")
        if packet.who_cannot_know_yet:
            beats.append(f"按理还不能知道的人不能提前得知：{packet.who_cannot_know_yet}")
        if packet.travel_time_floor:
            beats.append(f"跨地行动至少满足：{packet.travel_time_floor}")
        return beats

    def _scene_variant(self, packet: ChapterContextPacket, protagonist: dict[str, str], index: int) -> int:
        seed = f"{packet.chapter}-{protagonist.get('name', '角色')}-{index}"
        mod = 3 if index == 4 else 2
        return sum(ord(char) for char in seed) % mod

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
        hook_phrase = genre_profile["hook_phrase"]
        is_urban_system = genre_profile["genre"] == "urban_system"
        time_anchor = packet.time_anchor or "此刻"
        location_anchor = packet.location_anchor or place
        present_limit = "、".join(packet.present_characters[:6]) if packet.present_characters else ""
        knowledge_boundary = packet.knowledge_boundary
        message_flow = packet.message_flow
        arrival_timing = packet.arrival_timing
        who_knows_now = packet.who_knows_now
        who_cannot_know_yet = packet.who_cannot_know_yet
        travel_time_floor = packet.travel_time_floor
        resource_state = packet.resource_state
        variant = self._scene_variant(packet, protagonist, index)
        if index == 1:
            if variant == 0:
                lines = [
                    f"{time_anchor}，{location_anchor}里静得只剩脚步和呼吸，{self._action_for(protagonist['name'], 'observe', index)}",
                    f"他今晚不是来争口气的，他得把{state['protagonist_goal']}先稳住。",
                    f"{self._action_for(counterpart['name'], 'pressure', index)} {self._line_for(counterpart, counterpart_profile, 'probe', index)}",
                    f"{self._action_for(protagonist['name'], 'steady', index)} {self._line_for(protagonist, protagonist_profile, 'push', index)}",
                    f"{self._action_for(counterpart['name'], 'interrupt', index)} {self._line_for(counterpart, counterpart_profile, 'counter', index)}",
                    f"第一轮还没分出高下，但场子已经没再往失控那边滑。",
                ]
            else:
                lines = [
                    f"{time_anchor}，{location_anchor}里那点安静只撑了一瞬，{self._action_for(counterpart['name'], 'pressure', index)}",
                    f"{self._action_for(protagonist['name'], 'observe', index)} 他先没接话，只在心里把{state['protagonist_goal']}重新扣了一遍。",
                    f"{self._line_for(counterpart, counterpart_profile, 'probe', index)}",
                    f"{self._action_for(protagonist['name'], 'steady', index)} {self._line_for(protagonist, protagonist_profile, 'push', index)}",
                    f"{self._action_for(counterpart['name'], 'interrupt', index)} {self._line_for(counterpart, counterpart_profile, 'counter', index)}",
                    f"这一轮像是刚碰上刀背，火星没炸开，力道却已经压出来了。",
                ]
            if present_limit:
                lines.insert(1, f"此刻真正留在场上的，只有{present_limit}。")
            if knowledge_boundary:
                lines.insert(2 if len(lines) > 2 else len(lines), f"眼下能被看见的只到这一步：{knowledge_boundary}。")
            return lines
        if index == 2:
            if variant == 0:
                lines = [
                    f"{self._action_for(counterpart['name'], 'pressure', index)} 她想当场坐实{counterpart_goal}。",
                    f"{protagonist['name']}沿着墙边让开半步，把最危险的位置空出来，自己却没退。",
                    f"他记着{state['protagonist_taboo']}，所以这一步只换站位，不赌狠。",
                    f"{self._action_for(counterpart['name'], 'warning', index)} {self._line_for(counterpart, counterpart_profile, 'fear', index)}",
                    f"{self._action_for(protagonist['name'], 'interrupt', index)} {self._line_for(protagonist, protagonist_profile, 'counter', index)}",
                    f"{self._action_for(protagonist['name'], 'steady', index)} {self._line_for(protagonist, protagonist_profile, 'push', index)}",
                    "场面还是绷着的，但反击已经落到了实处。",
                ]
            else:
                lines = [
                    f"{protagonist['name']}先沿着墙边挪开半步，把最危险的位置让出来，自己却还钉在原地。",
                    f"{self._action_for(counterpart['name'], 'pressure', index)} 她就是要借这口气把{counterpart_goal}逼成现成的事实。",
                    f"{self._action_for(protagonist['name'], 'steady', index)} 他记着{state['protagonist_taboo']}，所以只换节奏，不换底牌。",
                    f"{self._line_for(counterpart, counterpart_profile, 'fear', index)}",
                    f"{self._action_for(protagonist['name'], 'interrupt', index)} {self._line_for(protagonist, protagonist_profile, 'counter', index)}",
                    f"{self._line_for(protagonist, protagonist_profile, 'push', index)}",
                    "话锋还是尖的，可局面已经不是单向挨打。",
                ]
            if message_flow:
                lines.insert(1, "风声真要散开，也不过是先落进在场人的耳朵里。")
            if who_knows_now:
                lines.insert(2 if len(lines) > 2 else len(lines), f"现在真正能把这件事听明白的人，只有{who_knows_now}。")
            if who_cannot_know_yet:
                lines.append(f"至于{who_cannot_know_yet}，此刻还都隔着一道门，不会这么快摸到这里。")
            return lines
        if index == 3:
            if variant == 0:
                lines = [
                    f"{protagonist['name']}趁那一下停顿把最要紧的信息先抓住，局面终于往自己这边偏了一寸。",
                    f"可东西刚到手，新的{pressure_noun}也跟着压了下来。",
                    "那感觉像刚把门顶住，门外又有人添了一根横木。" if is_urban_system else "那感觉像刚把局面按稳，下一笔账就已经记上了。",
                    f"{counterpart['name']}看着他，眼神第一次变了，像是在重新估这一步值不值。",
                    f"{self._action_for(protagonist['name'], 'cost', index)} {self._line_for(protagonist, protagonist_profile, 'cost', index)}",
                    f"他心里清楚，越往前走，{state['counterpart_fear']}就会压得越近。",
                    f"所以他把那点想继续追打的冲动按了回去，先给自己留出下一步。",
                ]
            else:
                lines = [
                    f"最要紧的那一点终于被{protagonist['name']}攥进手里，局面也跟着偏了过来。",
                    f"可他指尖刚一收紧，新的{pressure_noun}就已经顺着那点空隙压上来。",
                    f"{self._action_for(protagonist['name'], 'cost', index)} {self._line_for(protagonist, protagonist_profile, 'cost', index)}",
                    f"{counterpart['name']}没立刻说话，只是盯着他，像在重新算这一步到底亏不亏。",
                    "那感觉像刚把门顶住，门外又有人添了一根横木。" if is_urban_system else "那感觉像刚把局面按稳，下一笔账就已经记上了。",
                    f"{state['counterpart_fear']}没有退，反而借着这一停顿压得更近。",
                    f"他到底还是把继续追打的冲动压了回去，给后手留了一口气。",
                ]
            if arrival_timing:
                lines.insert(2, self._render_arrival_timing(arrival_timing))
            if travel_time_floor:
                lines.append(self._render_travel_time_floor(travel_time_floor))
            return lines
        scene4_close = self._render_scene4_close(variant, hook_phrase, packet.open_threads[0] if packet.open_threads else "")
        if variant == 0:
            lines = [
                f"{counterpart['name']}最后还是停了一拍，没有再往前逼到底。",
                f"{protagonist['name']}听出了那一瞬的迟疑，也听见更麻烦的事正在逼近：{state['counterpart_fear']}。",
                f"这一下虽然先兜住了，可下一步的{pressure_noun}已经摆上桌。",
                "系统没再留缓冲，新的账单就贴在眼前。" if is_urban_system else "回廊里没人再接话，可那口气并没有散，反而越压越实。",
                f"{self._action_for(counterpart['name'], 'warning', index)} {self._line_for(counterpart, counterpart_profile, 'warning', index)}",
                f"{self._action_for(protagonist['name'], 'warning', index)} {self._line_for(protagonist, protagonist_profile, 'warning', index)}",
                *scene4_close,
            ]
        elif variant == 1:
            lines = [
                f"眼前这一下虽然没崩，可{pressure_noun}也已经明明白白地摆到了桌上。",
                f"{counterpart['name']}先停了半拍，像是把那口气重新压回胸口，随后才把后话一点点递出来。",
                f"{self._line_for(counterpart, counterpart_profile, 'warning', index)}",
                "系统没再留缓冲，新的账单就贴在眼前。" if is_urban_system else "后面的后果并没有散，反而顺着这一停顿继续往前推。",
                f"{protagonist['name']}把那一下迟疑听得很清楚，也知道{state['counterpart_fear']}已经贴到了门口。",
                f"{self._action_for(protagonist['name'], 'warning', index)} {self._line_for(protagonist, protagonist_profile, 'warning', index)}",
                *scene4_close,
            ]
        else:
            lines = [
                f"{self._action_for(counterpart['name'], 'warning', index)} {self._line_for(counterpart, counterpart_profile, 'warning', index)}",
                f"{protagonist['name']}没有立刻顶回去，只把那口气硬生生咽住，听着{state['counterpart_fear']}一点点贴到跟前。",
                f"眼前这一下还不算垮，可{pressure_noun}已经顺着话缝露了头。",
                "系统没再留缓冲，新的账单就贴在眼前。" if is_urban_system else "后面的后果没有退，反而在这一静之间越推越近。",
                f"{self._action_for(protagonist['name'], 'warning', index)} {self._line_for(protagonist, protagonist_profile, 'warning', index)}",
                *scene4_close,
            ]
        if resource_state:
            lines.insert(3, self._render_resource_state(resource_state))
        if who_cannot_know_yet:
            lines.insert(len(lines) - 1, f"所以这一夜的后手还卡在这里，{who_cannot_know_yet}不会比该知道的时间更早收到风声。")
        return lines

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
            scene_summary = self._scene_summary(brief, str(item["summary"]), index)
            scene_targets = self._scene_targets(brief, index)
            beats = self._scene_beats(packet, protagonist, counterpart, state, genre_profile)
            beats = self._augment_scene_beats(brief, beats, index)
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
            draft_lines = self._apply_brief_to_scene_draft(draft_lines, scene_targets, index, genre_profile, brief)
            scenes.append(
                {
                    "label": item["label"],
                    "title": item["title"],
                    "summary": scene_summary,
                    "scene_plan_focus": scene_targets["scene_plan"],
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

    def _scene_summary(self, brief: ChapterBrief, fallback: str, index: int) -> str:
        scene_index = index - 1
        if 0 <= scene_index < len(brief.scene_plan):
            scene_plan = brief.scene_plan[scene_index].strip()
            softened = self._narrativize_scene_plan(scene_plan, index)
            if softened and softened != fallback.strip():
                return f"{softened}。 {fallback}".strip()
            if softened:
                return softened
        return fallback

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

    def _render_message_flow(self, text: str) -> str:
        value = self._normalize_directive(text)
        if not value:
            return ""
        if "只有在场人可见" in value and "尚未外传" in value:
            return "所有人能亲眼看见的，也只有场上这一幕，至于后手，还压着没往外走。"
        return f"这话真要散出去，也只会沿着{self._compress_field_text(value)}这条线慢慢传。"

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
            return f"{value}的{place}，连一点转圜的空隙都没有。"
        return f"{value}这一刻，连一点转圜的空隙都没有。"

    def _render_travel_time_floor(self, text: str) -> str:
        value = self._normalize_directive(text)
        if not value:
            return ""
        if "不能一句话跨城" in value:
            return "真要把动作接到场外，也得一步步走过去，没人能靠一句话就把整段路抹掉。"
        return f"真要把动作接到场外，也得先满足{self._compress_field_text(value)}，没人能在一句话里赶完这段路。"

    def _render_resource_state(self, text: str) -> str:
        value = self._normalize_directive(text)
        if not value:
            return ""
        if "处于弱势" in value and "刚公开站队" in value:
            return "眼下真正能拿来顶事的并不多，一边还在失势，一边也只是刚把态度摆到明面上。"
        return f"可真能立刻动用的东西其实不多：{self._compress_field_text(value)}。"

    def _render_scene4_close(self, variant: int, hook_phrase: str, open_thread: str) -> list[str]:
        if variant == 0:
            return [
                f"两个人都没再往前多逼那半寸，可{hook_phrase}已经顺着这口气压到了眼前。",
                f"回廊里一时静了，可{open_thread}已经被硬生生往前拱了一步。" if open_thread else "回廊里一时静了，可下一步已经被悄悄推着往前走。",
            ]
        if variant == 1:
            return [
                "这一下还不算翻盘，只是把最先塌下来的那块地方硬撑住了。",
                f"可后手并没停，{hook_phrase}。",
            ]
        return [
            "眼前这口气虽然没断，可真正的账反倒从这里开始往后排。",
            f"真要紧的，不是刚才谁赢半寸，而是{hook_phrase}。",
        ]

    def _narrativize_scene_plan(self, scene_plan: str, index: int) -> str:
        plan = self._normalize_directive(scene_plan)
        if not plan:
            return ""
        if plan.startswith("开场先锁定"):
            core = plan.replace("开场先锁定", "", 1).strip()
            core = core.replace("不要先讲背景", "").strip(" ，,、")
            return f"连空气都先被{core}压紧了"
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
        prefix = "眼前先得咬住的是" if index == 1 else "这一段真正往前顶的是"
        return f"{prefix}{plan}"

    def _narrativize_payoff(self, payoff_or_pressure: str, pressure_noun: str) -> str:
        payoff = self._normalize_directive(payoff_or_pressure)
        if not payoff:
            return ""
        if payoff.startswith("本章必须兑现或抬高："):
            core = payoff.split("：", 1)[1].strip()
            return f"眼下最不能松手的，就是{core}这一下，稍一后撤，新的{pressure_noun}立刻就会顶上来。"
        if payoff.startswith("消息传播必须遵守："):
            return self._render_message_flow(payoff.split("：", 1)[1].strip())
        if payoff.startswith("越界知情禁止发生："):
            core = self._compress_field_text(payoff.split("：", 1)[1].strip())
            return f"这口风只能压在这里，{core}，谁都不能比该知道的时候更早听见。"
        return f"眼下最急的还是{payoff}，再拖一步，新的{pressure_noun}就会压上来。"

    def _narrativize_success(self, success_criterion: str, index: int) -> str:
        criterion = self._normalize_directive(success_criterion)
        if not criterion:
            return ""
        if criterion.startswith("本章功能必须成立："):
            core = criterion.split("：", 1)[1].strip()
            return f"这一轮不管怎么绕，最后都得把{core}真正落住，不然前面那些拉扯都白费。"
        if criterion.startswith("章节内必须出现结果变化"):
            return "这一轮不能只把气氛架高，总得真有一寸地方被推过去。"
        if criterion.startswith("章节尾部必须留下下一步压力或回收牵引"):
            return "到收尾时，下一步压力得自己露头，不能还停在原地打转。"
        if criterion.startswith("至少推进一个 open thread："):
            core = criterion.split("：", 1)[1].strip()
            return f"至少也得把{core}往前送一步，不然这一场就还是空转。"
        prefix = "这一轮至少得把" if index < 4 else "收尾前总得把"
        return f"{prefix}{criterion}落下来，不然前面那些话都不算数。"

    def _apply_brief_to_scene_draft(
        self,
        draft_lines: list[str],
        scene_targets: dict[str, str],
        index: int,
        genre_profile: dict[str, str],
        brief: ChapterBrief,
    ) -> list[str]:
        updated = list(draft_lines)
        scene_plan = scene_targets["scene_plan"]
        payoff_or_pressure = scene_targets["payoff_or_pressure"]
        success_criterion = scene_targets["success_criterion"]
        pressure_noun = genre_profile["pressure_noun"]

        scene_plan_line = self._narrativize_scene_plan(scene_plan, index)
        payoff_line = self._narrativize_payoff(payoff_or_pressure, pressure_noun)
        success_line = self._narrativize_success(success_criterion, index)
        guardrail_tokens = (
            "中段推进最多只能到：",
            "本章变化范围只允许：",
            "结尾只能留下压力，不能提前兑现：",
            "本章推进不得越过：",
            "本章禁止提前兑现：",
        )
        if any(scene_plan.startswith(token) for token in guardrail_tokens):
            scene_plan_line = ""
        if any(payoff_or_pressure.startswith(token) for token in ("只可预热不可兑现：",)):
            payoff_line = ""
        if any(success_criterion.startswith(token) for token in ("本章推进不得越过：", "本章禁止提前兑现：", "本章变化范围只允许：")):
            success_line = ""

        if scene_plan_line:
            line = scene_plan_line if scene_plan_line.endswith(("。", "！", "？")) else f"{scene_plan_line}。"
            updated.insert(1 if updated else 0, line)
        if payoff_line:
            insert_at = 3 if len(updated) >= 3 else len(updated)
            updated.insert(insert_at, payoff_line)
        if success_line:
            if index >= 4:
                if not any(token in success_line for token in ("至少也得把", "收尾前总得把")):
                    updated.append(success_line)
            else:
                updated.insert(len(updated) - 1 if updated else 0, success_line)
        return updated

    def _augment_scene_beats(self, brief: ChapterBrief, beats: list[str], index: int) -> list[str]:
        augmented = list(beats)
        scene_index = index - 1
        if 0 <= scene_index < len(brief.required_payoff_or_pressure):
            augmented.append(f"required_payoff_or_pressure: {brief.required_payoff_or_pressure[scene_index]}")
        elif brief.required_payoff_or_pressure:
            augmented.append(f"required_payoff_or_pressure: {brief.required_payoff_or_pressure[0]}")
        if index == 1 and brief.must_not_repeat:
            augmented.extend(f"must_not_repeat: {item}" for item in brief.must_not_repeat[:2])
        if index == 1 and brief.success_criteria:
            augmented.extend(f"success_criteria: {item}" for item in brief.success_criteria[:2])
        if brief.progress_floor:
            augmented.append(f"progress_floor: {brief.progress_floor}")
        if brief.progress_ceiling:
            augmented.append(f"progress_ceiling: {brief.progress_ceiling}")
        if brief.must_not_payoff_yet:
            augmented.extend(f"must_not_payoff_yet: {item}" for item in brief.must_not_payoff_yet[:2])
        if brief.allowed_change_scope:
            augmented.extend(f"allowed_change_scope: {item}" for item in brief.allowed_change_scope[:2])
        return augmented

    def _scene_cards(self, scenes: list[dict[str, object]]) -> list[dict[str, str]]:
        return [
            {
                "scene": str(item["label"]),
                "title": str(item["title"]),
                "summary": str(item["summary"]),
                "scene_plan_focus": str(item.get("scene_plan_focus", "")),
                "payoff_or_pressure": str(item.get("payoff_or_pressure", "")),
                "success_criterion": str(item.get("success_criterion", "")),
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
                    f"- scene_plan_focus: {item.get('scene_plan_focus', '')}",
                    f"- payoff_or_pressure: {item.get('payoff_or_pressure', '')}",
                    f"- success_criterion: {item.get('success_criterion', '')}",
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
                "## Continuity Notes",
                f"- time_anchor: {notes.get('time_anchor', '')}",
                f"- location_anchor: {notes.get('location_anchor', '')}",
                f"- present_characters: {notes.get('present_characters', '')}",
                f"- knowledge_boundary: {notes.get('knowledge_boundary', '')}",
                f"- message_flow: {notes.get('message_flow', '')}",
                f"- arrival_timing: {notes.get('arrival_timing', '')}",
                f"- who_knows_now: {notes.get('who_knows_now', '')}",
                f"- who_cannot_know_yet: {notes.get('who_cannot_know_yet', '')}",
                f"- travel_time_floor: {notes.get('travel_time_floor', '')}",
                f"- resource_state: {notes.get('resource_state', '')}",
                f"- progress_floor: {notes.get('progress_floor', '')}",
                f"- progress_ceiling: {notes.get('progress_ceiling', '')}",
                f"- must_not_payoff_yet: {notes.get('must_not_payoff_yet', '')}",
                f"- allowed_change_scope: {notes.get('allowed_change_scope', '')}",
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
        rewrite_handoff_path: Path | None = None
        rewrite_text = ""
        if decision.decision == "revise":
            rewrite_handoff_path = draft_dir / "rewrite_handoff.md"
            rewrite_text = self._build_rewrite_handoff(brief, decision)

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
                "time_anchor": packet.time_anchor,
                "location_anchor": packet.location_anchor or packet.current_place,
                "present_characters": "、".join(packet.present_characters),
                "knowledge_boundary": packet.knowledge_boundary,
                "message_flow": packet.message_flow,
                "arrival_timing": packet.arrival_timing,
                "who_knows_now": packet.who_knows_now,
                "who_cannot_know_yet": packet.who_cannot_know_yet,
                "travel_time_floor": packet.travel_time_floor,
                "resource_state": packet.resource_state,
                "progress_floor": packet.progress_floor,
                "progress_ceiling": packet.progress_ceiling,
                "must_not_payoff_yet": "、".join(packet.must_not_payoff_yet),
                "allowed_change_scope": "、".join(packet.allowed_change_scope),
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
                "progress_floor": packet.progress_floor,
                "progress_ceiling": packet.progress_ceiling,
                "must_not_payoff_yet": "、".join(packet.must_not_payoff_yet),
                "allowed_change_scope": "、".join(packet.allowed_change_scope),
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
            packet,
        )
        blueprint_text = self._build_chapter_blueprint(scenes, outcome_signature, packet)
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
        if rewrite_handoff_path is not None:
            rewrite_handoff_path.write_text(rewrite_text + "\n", encoding="utf-8")

        return {
            "project": project_dir.as_posix(),
            "chapter": brief.chapter,
            "status": (
                "rewritten-runtime-output"
                if decision.decision == "revise"
                else ("ready-human-review" if dry_run else "drafted-runtime-output")
            ),
            "draft_path": draft_path.as_posix(),
            "review_notes_path": review_notes_path.as_posix(),
            "blueprint_path": blueprint_path.as_posix(),
            "editorial_summary_path": editorial_summary_path.as_posix(),
            "manuscript_path": manuscript_path.as_posix(),
            "rewrite_handoff_path": "" if rewrite_handoff_path is None else rewrite_handoff_path.as_posix(),
            "rewrite_handoff_preview": "\n".join(rewrite_text.splitlines()[:8]) if rewrite_text else "",
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
