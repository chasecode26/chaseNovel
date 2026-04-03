#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


CHAPTER_PATTERN = re.compile(r"第0*(\d+)章")
AUTHORIAL_HARD_PATTERNS = (
    "宿命感",
    "压抑得让人",
    "仿佛整个世界都",
    "空气里弥漫着",
    "某种说不清",
    "仿佛命运",
)
AUTHORIAL_SOFT_PATTERNS = (
    "这一刻",
    "令人窒息",
)
ABSTRACT_WORDS = (
    "压抑", "窒息", "阴冷", "诡异", "冰冷", "危险", "宿命", "沉重", "死寂", "森然"
)
DEFAULT_CAUTION_PHRASES = (
    "不禁", "只见", "此刻", "心中暗道"
)
DEFAULT_THRESHOLDS = {
    "authorial_narration_tolerance": 0,
    "soft_authorial_tolerance": 1,
    "abstract_word_tolerance": 2,
    "repeated_phrase_tolerance": 1,
    "lyrical_paragraph_tolerance": 1,
}
LINE_VALUE_RE = re.compile(r"^- ([^：]+)：\s*(.*)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a lightweight language audit for chaseNovel chapters."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--chapter-no", type=int, help="Target chapter number")
    parser.add_argument("--chapter", help="Path to a specific chapter markdown file")
    parser.add_argument("--style", help="Path to a specific style.md file")
    parser.add_argument(
        "--mode",
        choices=("audit", "suggest"),
        default="audit",
        help="audit only reports issues; suggest also outputs rewrite suggestions and local rewrites",
    )
    parser.add_argument(
        "--rewrite-out",
        help="Optional output path for a full suggested rewrite; only meaningful in suggest mode",
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not write report files")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    return parser.parse_args()


def chapter_number_from_name(name: str) -> int | None:
    match = CHAPTER_PATTERN.search(name)
    if not match:
        return None
    return int(match.group(1))


def detect_target_chapter(project_dir: Path, chapter_arg: str | None, chapter_no: int | None) -> tuple[int, Path]:
    chapters_dir = project_dir / "03_chapters"
    if chapter_arg:
        chapter_path = Path(chapter_arg).resolve()
        detected_no = chapter_no or chapter_number_from_name(chapter_path.name)
        if detected_no is None:
            raise ValueError("无法从 --chapter 推断章节号，请补充 --chapter-no。")
        return detected_no, chapter_path

    chapter_files: list[tuple[int, Path]] = []
    if chapters_dir.exists():
        for path in chapters_dir.iterdir():
            if not path.is_file():
                continue
            detected_no = chapter_number_from_name(path.name)
            if detected_no is not None:
                chapter_files.append((detected_no, path))

    chapter_files.sort(key=lambda item: item[0])
    if chapter_no is not None:
        for current_no, path in chapter_files:
            if current_no == chapter_no:
                return current_no, path
        raise ValueError(f"未找到第{chapter_no:03d}章文件。")

    if chapter_files:
        return chapter_files[-1]
    raise ValueError("未找到章节文件，请传入 --chapter 或在 03_chapters 下放入章节。")


def split_paragraphs(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]


def split_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"[。！？；\n]+", text) if part.strip()]


def normalize_input_text(text: str) -> str:
    return text.lstrip("\ufeff")


def load_json_file(path: Path) -> dict[str, object]:
    return json.loads(normalize_input_text(path.read_text(encoding="utf-8")))


def parse_scalar_int(value: str, default: int) -> int:
    match = re.search(r"\d+", value or "")
    if not match:
        return default
    return int(match.group(0))


def parse_inline_list(value: str) -> list[str]:
    cleaned = (value or "").strip()
    if not cleaned:
        return []
    items = re.split(r"[、，,；; /]+", cleaned)
    return [item.strip().strip("\"'`") for item in items if item.strip().strip("\"'`")]


def parse_style_file(style_path: Path) -> dict[str, object]:
    profile = {
        "title": "",
        "genre": "",
        "forbidden_phrases": [],
        "caution_phrases": [],
        "forbidden_words": [],
        "caution_words": [],
        "allowed_phrases": [],
        "allowed_authorial_patterns": [],
        "repetition_alert_words": [],
        "thresholds": dict(DEFAULT_THRESHOLDS),
        "explicit_thresholds": {},
        "narration_rules": [],
        "preferred_patterns": [],
    }
    if not style_path.exists():
        return profile

    section = ""
    subsection = ""
    for raw_line in normalize_input_text(style_path.read_text(encoding="utf-8")).splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("## "):
            section = stripped[3:].strip()
            subsection = ""
            continue
        if stripped.startswith("### "):
            subsection = stripped[4:].strip()
            continue

        match = LINE_VALUE_RE.match(stripped)
        if match:
            label, value = match.groups()
            if label == "书名":
                profile["title"] = value.strip()
            elif label == "题材":
                profile["genre"] = value.strip()
            elif label == "禁止句式":
                profile["forbidden_phrases"].extend(parse_inline_list(value))
            elif label == "慎用句式":
                profile["caution_phrases"].extend(parse_inline_list(value))
            elif label == "禁止词汇":
                profile["forbidden_words"].extend(parse_inline_list(value))
            elif label == "慎用词汇":
                profile["caution_words"].extend(parse_inline_list(value))
            elif label == "豁免句式":
                profile["allowed_phrases"].extend(parse_inline_list(value))
            elif label == "豁免作者旁白信号":
                profile["allowed_authorial_patterns"].extend(parse_inline_list(value))
            elif label == "高频重复预警词":
                profile["repetition_alert_words"].extend(parse_inline_list(value))
            elif label == "作者式旁白容忍度":
                parsed = parse_scalar_int(value, 0)
                profile["thresholds"]["authorial_narration_tolerance"] = parsed
                profile["explicit_thresholds"]["authorial_narration_tolerance"] = parsed
            elif label == "软作者式旁白容忍度":
                parsed = parse_scalar_int(value, 1)
                profile["thresholds"]["soft_authorial_tolerance"] = parsed
                profile["explicit_thresholds"]["soft_authorial_tolerance"] = parsed
            elif label == "抽象形容词容忍度":
                parsed = parse_scalar_int(value, 2)
                profile["thresholds"]["abstract_word_tolerance"] = parsed
                profile["explicit_thresholds"]["abstract_word_tolerance"] = parsed
            elif label == "同类句式重复容忍度":
                parsed = parse_scalar_int(value, 1)
                profile["thresholds"]["repeated_phrase_tolerance"] = parsed
                profile["explicit_thresholds"]["repeated_phrase_tolerance"] = parsed
            elif label == "纯抒情段落最大连续数":
                parsed = parse_scalar_int(value, 1)
                profile["thresholds"]["lyrical_paragraph_tolerance"] = parsed
                profile["explicit_thresholds"]["lyrical_paragraph_tolerance"] = parsed
            continue

        if stripped.startswith("- "):
            item = stripped[2:].strip().strip("\"'`")
            if not item:
                continue
            if section == "平台方向":
                lowered = item.lower()
                if "权谋" in item and not profile["genre"]:
                    profile["genre"] = "历史/权谋"
                elif "悬疑" in item and not profile["genre"]:
                    profile["genre"] = "悬疑/推理"
                elif "系统" in item and not profile["genre"]:
                    profile["genre"] = "都市/系统流"
                elif "番茄" in item:
                    profile["preferred_patterns"].extend(["快反馈", "结果先行"])
                if "快反馈" in item or "快节奏" in item:
                    profile["preferred_patterns"].extend(["快反馈", "动作结果"])
                if "男频" in item or "权谋" in item:
                    profile["narration_rules"].extend([
                        "少矫情心理戏，优先动作和局势变化",
                        "结果变化优先于抒情铺垫",
                    ])
            if section == "负向锚点（去AI化红线）" and subsection == "":
                if item not in profile["caution_phrases"]:
                    profile["caution_phrases"].append(item)
            if "禁止句式" in raw_line:
                continue

    profile["caution_phrases"] = unique_items(list(DEFAULT_CAUTION_PHRASES) + list(profile["caution_phrases"]))
    profile["forbidden_phrases"] = unique_items(profile["forbidden_phrases"])
    profile["caution_phrases"] = unique_items(profile["caution_phrases"])
    profile["forbidden_words"] = unique_items(profile["forbidden_words"])
    profile["caution_words"] = unique_items(profile["caution_words"])
    profile["allowed_phrases"] = unique_items(profile["allowed_phrases"])
    profile["allowed_authorial_patterns"] = unique_items(profile["allowed_authorial_patterns"])
    profile["repetition_alert_words"] = unique_items(profile["repetition_alert_words"])
    profile["narration_rules"] = unique_items(profile["narration_rules"])
    profile["preferred_patterns"] = unique_items(profile["preferred_patterns"])
    return profile


def merge_style_profiles(base: dict[str, object], override: dict[str, object]) -> dict[str, object]:
    merged = {
        "title": str(override.get("title") or override.get("name") or base.get("title") or ""),
        "genre": str(override.get("genre") or base.get("genre") or ""),
        "forbidden_phrases": unique_items(list(base.get("forbidden_phrases", [])) + list(override.get("forbidden_phrases", []))),
        "caution_phrases": unique_items(list(base.get("caution_phrases", [])) + list(override.get("caution_phrases", []))),
        "forbidden_words": unique_items(list(base.get("forbidden_words", [])) + list(override.get("forbidden_words", []))),
        "caution_words": unique_items(list(base.get("caution_words", [])) + list(override.get("caution_words", []))),
        "allowed_phrases": unique_items(list(base.get("allowed_phrases", [])) + list(override.get("allowed_phrases", []))),
        "allowed_authorial_patterns": unique_items(list(base.get("allowed_authorial_patterns", [])) + list(override.get("allowed_authorial_patterns", []))),
        "repetition_alert_words": unique_items(list(base.get("repetition_alert_words", [])) + list(override.get("repetition_alert_words", []))),
        "narration_rules": unique_items(list(base.get("narration_rules", [])) + list(override.get("narration_rules", []))),
        "preferred_patterns": unique_items(list(base.get("preferred_patterns", [])) + list(override.get("preferred_patterns", []))),
        "thresholds": dict(base.get("thresholds", DEFAULT_THRESHOLDS)),
        "explicit_thresholds": dict(base.get("explicit_thresholds", {})),
    }
    override_thresholds = dict(override.get("explicit_thresholds", override.get("thresholds", {})))
    merged["thresholds"].update(override_thresholds)
    merged["explicit_thresholds"].update(override_thresholds)
    return merged


def load_kb_genre_profile(kb_root: Path, genre: str) -> dict[str, object]:
    empty_profile = {
        "name": "",
        "genre": genre,
        "forbidden_phrases": [],
        "forbidden_words": [],
        "caution_phrases": [],
        "caution_words": [],
        "allowed_phrases": [],
        "allowed_authorial_patterns": [],
        "narration_rules": [],
        "preferred_patterns": [],
        "thresholds": dict(DEFAULT_THRESHOLDS),
        "explicit_thresholds": {},
    }
    if not genre:
        return empty_profile

    profiles_dir = kb_root / "profiles" / "genre"
    if not profiles_dir.exists():
        return empty_profile

    for path in profiles_dir.glob("*.json"):
        payload = load_json_file(path)
        if str(payload.get("genre", "")).strip() == genre.strip():
            return {
                "name": payload.get("name", ""),
                "genre": payload.get("genre", genre),
                "forbidden_phrases": payload.get("forbidden_phrases", []),
                "forbidden_words": payload.get("forbidden_words", []),
                "caution_phrases": payload.get("caution_phrases", []),
                "caution_words": payload.get("caution_words", []),
                "allowed_phrases": payload.get("allowed_phrases", []),
                "allowed_authorial_patterns": payload.get("allowed_authorial_patterns", []),
                "narration_rules": payload.get("narration_rules", []),
                "preferred_patterns": payload.get("preferred_patterns", []),
                "thresholds": payload.get("thresholds", dict(DEFAULT_THRESHOLDS)),
                "explicit_thresholds": payload.get("thresholds", {}),
            }
    return empty_profile


def normalize_profile_key(value: str) -> str:
    return re.sub(r"[\W_]+", "", (value or "").strip().lower())


def load_kb_book_profile(kb_root: Path, style_path: Path, title: str) -> dict[str, object]:
    empty_profile = {
        "name": title,
        "genre": "",
        "forbidden_phrases": [],
        "forbidden_words": [],
        "caution_phrases": [],
        "caution_words": [],
        "allowed_phrases": [],
        "allowed_authorial_patterns": [],
        "narration_rules": [],
        "preferred_patterns": [],
        "thresholds": dict(DEFAULT_THRESHOLDS),
        "explicit_thresholds": {},
    }
    profiles_dir = kb_root / "profiles" / "book"
    if not profiles_dir.exists():
        return empty_profile

    style_stem = normalize_profile_key(style_path.stem)
    title_key = normalize_profile_key(title)
    project_name_key = ""
    if len(style_path.parts) >= 3:
        project_name = style_path.parent.parent.name
        project_name_key = normalize_profile_key(re.sub(r"^novel[_-]?", "", project_name, flags=re.IGNORECASE))
    candidates = []
    if title_key:
        candidates.append(title_key)
        candidates.append(f"book_{title_key}")
    if style_stem:
        candidates.append(style_stem)
        candidates.append(f"book_{style_stem}")
    if project_name_key:
        candidates.append(project_name_key)
        candidates.append(f"book_{project_name_key}")

    for path in profiles_dir.glob("*.json"):
        payload = load_json_file(path)
        path_key = normalize_profile_key(path.stem)
        name_key = normalize_profile_key(str(payload.get("name", "")))
        if any(candidate and candidate in {path_key, name_key} for candidate in candidates):
            return {
                "name": payload.get("name", title or path.stem),
                "genre": payload.get("genre", ""),
                "forbidden_phrases": payload.get("forbidden_phrases", []),
                "forbidden_words": payload.get("forbidden_words", []),
                "caution_phrases": payload.get("caution_phrases", []),
                "caution_words": payload.get("caution_words", []),
                "allowed_phrases": payload.get("allowed_phrases", []),
                "allowed_authorial_patterns": payload.get("allowed_authorial_patterns", []),
                "narration_rules": payload.get("narration_rules", []),
                "preferred_patterns": payload.get("preferred_patterns", []),
                "thresholds": payload.get("thresholds", dict(DEFAULT_THRESHOLDS)),
                "explicit_thresholds": payload.get("thresholds", {}),
            }
    return empty_profile


def load_negative_patterns(kb_root: Path) -> list[dict[str, object]]:
    patterns_dir = kb_root / "patterns" / "negative"
    if not patterns_dir.exists():
        return []

    items: list[dict[str, object]] = []
    for path in patterns_dir.glob("*.json"):
        items.append(load_json_file(path))
    return items


def load_positive_patterns(kb_root: Path) -> list[dict[str, object]]:
    patterns_dir = kb_root / "patterns" / "positive"
    if not patterns_dir.exists():
        return []

    items: list[dict[str, object]] = []
    for path in patterns_dir.glob("*.json"):
        items.append(load_json_file(path))
    return items


def load_rewrite_pairs(kb_root: Path) -> list[dict[str, object]]:
    pairs_dir = kb_root / "patterns" / "rewrite_pairs"
    if not pairs_dir.exists():
        return []

    items: list[dict[str, object]] = []
    for path in pairs_dir.glob("*.json"):
        items.append(load_json_file(path))
    return items


def load_scene_recipes(kb_root: Path) -> list[dict[str, object]]:
    recipes_dir = kb_root / "recipes" / "scene"
    if not recipes_dir.exists():
        return []

    items: list[dict[str, object]] = []
    for path in recipes_dir.glob("*.json"):
        items.append(load_json_file(path))
    return items


def pattern_matches_genre(pattern: dict[str, object], genre: str) -> bool:
    applicable = [str(item) for item in pattern.get("applicable_genres", [])]
    return not genre or not applicable or genre in applicable


def pattern_trigger_matches(text: str, pattern: dict[str, object]) -> bool:
    trigger_phrases = [str(item).strip() for item in pattern.get("trigger_phrases", []) if str(item).strip()]
    if trigger_phrases:
        return any(phrase in text for phrase in trigger_phrases)
    bad_example = str(pattern.get("bad_example", "")).strip()
    return bool(bad_example and bad_example in text)


def detect_negative_pattern_hits(
    paragraphs: list[str],
    genre: str,
    negative_patterns: list[dict[str, object]],
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for index, paragraph in enumerate(paragraphs, start=1):
        for pattern in negative_patterns:
            if not pattern_matches_genre(pattern, genre):
                continue
            if not pattern_trigger_matches(paragraph, pattern):
                continue
            issues.append({
                "type": str(pattern.get("tags", ["kb_pattern"])[0]),
                "severity": "high",
                "position": f"p{index}",
                "reason": f"命中知识库负面模式“{pattern.get('title', pattern.get('id', 'unknown'))}”：{pattern.get('problem', '')}",
                "kb_id": pattern.get("id", ""),
                "kb_rewrite_strategy": pattern.get("rewrite_strategy", []),
                "kb_good_example": pattern.get("good_example", ""),
            })
    return issues


def detect_scene_recipe_hits(
    paragraphs: list[str],
    genre: str,
    scene_recipes: list[dict[str, object]],
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    scene_terms = {
        "pressure": ("压抑", "窒息", "危险", "宿命", "威压", "空气里弥漫着"),
        "danger": ("追杀", "暴露", "危险", "刺杀", "埋伏", "失手", "代价"),
        "suspense": ("不对劲", "疑点", "线索", "可疑", "不在场", "档案", "异常"),
        "romance": ("靠近", "心跳", "目光", "指尖", "呼吸", "耳尖", "偏爱"),
        "daily": ("吃饭", "回家", "收拾", "坐下", "日子", "日常", "闲聊"),
        "cultivation_breakthrough": ("灵气", "经脉", "瓶颈", "突破", "丹田", "反噬", "关窍"),
        "farming_progress": ("庄稼", "田里", "收成", "苗", "作坊", "集市", "订单", "灶台"),
        "system_reward": ("系统", "面板", "任务", "奖励", "经验", "等级", "提示"),
        "apocalypse_scarcity": ("物资", "弹药", "感染", "尸群", "据点", "药品", "断电", "发电机"),
        "opening_grab": ("异常", "危机", "机会", "压迫", "羞辱", "追杀", "系统", "末世", "翻身"),
        "golden_three_progress": ("行动", "反击", "入局", "推进", "目标", "承诺", "路线", "强敌", "站队"),
        "chapter_hook": ("结果", "暴露", "真相", "选择", "名额", "机缘", "强敌", "下一步", "站队"),
    }
    for index, paragraph in enumerate(paragraphs, start=1):
        for recipe in scene_recipes:
            scene = str(recipe.get("scene", "")).strip()
            if not pattern_matches_genre(recipe, genre):
                continue
            terms = scene_terms.get(scene, ())
            if not terms:
                continue
            hit_count = sum(1 for term in terms if term in paragraph)
            if hit_count >= 2:
                issues.append({
                    "type": f"scene_recipe_{scene}",
                    "severity": "medium",
                    "position": f"p{index}",
                    "reason": f"该段更适合按场景配方“{recipe.get('id', scene)}”重写，避免直接按旧套路平推。",
                    "recipe_id": recipe.get("id", ""),
                    "recipe_steps": recipe.get("steps", []),
                    "recipe_avoid": recipe.get("avoid", []),
                    "scene": scene,
                })
    return issues


def unique_items(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def repeated_phrases(sentences: list[str], style_profile: dict[str, object]) -> list[dict[str, object]]:
    phrases = unique_items(
        list(style_profile["forbidden_phrases"])
        + list(style_profile["caution_phrases"])
    )
    allowed_phrases = set(style_profile.get("allowed_phrases", []))
    tolerance = int(style_profile["thresholds"]["repeated_phrase_tolerance"])
    phrase_hits: Counter[str] = Counter()
    for sentence in sentences:
        for phrase in phrases:
            if phrase in allowed_phrases:
                continue
            if phrase in sentence:
                phrase_hits[phrase] += 1

    items: list[dict[str, object]] = []
    for phrase, count in phrase_hits.items():
        if count > tolerance:
            items.append({
                "type": "repeated_phrase",
                "severity": "medium",
                "reason": f"提示短语“{phrase}”重复出现 {count} 次，超过风格阈值 {tolerance}。",
            })
    return items


def abstract_word_counts(text: str, style_profile: dict[str, object]) -> dict[str, int]:
    tracked_words = unique_items(
        list(ABSTRACT_WORDS)
        + list(style_profile["forbidden_words"])
        + list(style_profile["caution_words"])
        + list(style_profile["repetition_alert_words"])
    )
    counts: dict[str, int] = {}
    for word in tracked_words:
        count = text.count(word)
        if count:
            counts[word] = count
    return counts


def detect_lyrical_paragraph(paragraph: str) -> bool:
    sentences = split_sentences(paragraph)
    if not sentences:
        return False
    action_markers = ("说", "问", "看", "走", "退", "冲", "伸手", "抬手", "落下", "推开", "按住", "转身")
    abstract_hits = sum(paragraph.count(word) for word in ABSTRACT_WORDS)
    has_action = any(marker in paragraph for marker in action_markers)
    return abstract_hits >= 2 and not has_action and len(sentences) >= 2


def replace_terms(text: str, replacements: dict[str, str]) -> str:
    updated = text
    for source, target in replacements.items():
        updated = updated.replace(source, target)
    return updated


def build_local_rewrite(paragraph: str, style_profile: dict[str, object]) -> str:
    rewrite_pairs = list(style_profile.get("rewrite_pairs", []))
    for pair in rewrite_pairs:
        if not pattern_matches_genre(pair, str(style_profile.get("genre", ""))):
            continue
        good_example = str(pair.get("good_example", "")).strip()
        bad_example = str(pair.get("bad_example", "")).strip()
        if bad_example and good_example and bad_example in paragraph:
            return paragraph.replace(bad_example, good_example)
        if good_example and pattern_trigger_matches(paragraph, pair):
            return good_example

    for recipe in style_profile.get("scene_recipes", []):
        scene = str(recipe.get("scene", ""))
        if scene == "pressure" and any(term in paragraph for term in ("压抑", "窒息", "危险", "宿命", "空气里弥漫着")):
            if "系统" in paragraph:
                return "走廊尽头的灯闪了两下，他刚站定，呼吸先紧了一分。系统提示弹出来时，像是在催他立刻作出选择。"
            return "门缝里的光忽明忽暗，他刚抬手，指节先凉了一截，连呼吸都短了一分。"
        if scene == "danger" and any(term in paragraph for term in ("追杀", "暴露", "刺杀", "埋伏", "危险")):
            return "巷口先传来一声短促的响动，他立刻收住脚步。再往前半步，整条退路都可能被人掐死。"
        if scene == "suspense" and any(term in paragraph for term in ("不对劲", "疑点", "线索", "可疑", "异常")):
            return "桌上的档案少了一页，偏偏是最该留着的那一页。他先压住追问的冲动，只把这个缺口记在心里。"
        if scene == "romance" and any(term in paragraph for term in ("心跳", "目光", "指尖", "呼吸", "耳尖", "靠近")):
            return "她刚抬眼，他已经先停了半步。两个人谁都没碰到谁，空气却像被那点迟疑悄悄拉紧了。"
        if scene == "daily" and any(term in paragraph for term in ("吃饭", "回家", "收拾", "日常", "闲聊")):
            return "饭桌上没什么大事，筷子起落间却多了一句从前不会说出口的话。那顿饭吃到最后，气氛已经和来时不一样了。"
        if scene == "cultivation_breakthrough" and any(term in paragraph for term in ("灵气", "经脉", "瓶颈", "突破", "丹田", "反噬")):
            return "灵气刚撞上瓶颈，他的经脉先是一阵刺痛，紧接着丹田猛地一沉。下一息，原本死死卡住的那层壁障终于裂开了一线。"
        if scene == "farming_progress" and any(term in paragraph for term in ("庄稼", "田", "收成", "地里", "作坊", "集市")):
            return "他先蹲下扒开土层看了一眼，苗根已经扎稳了。等到这批收成落地，不光眼前的窘境能缓一口气，后面的日子也总算有了可见的进账。"
        if scene == "system_reward" and any(term in paragraph for term in ("系统", "面板", "任务", "奖励", "经验", "等级")):
            return "面板刚一跳出奖励提示，他先确认能换来什么现实变化。等他把那条信息看完，眼前最棘手的缺口已经有了补法。"
        if scene == "apocalypse_scarcity" and any(term in paragraph for term in ("物资", "弹药", "感染", "尸群", "据点", "药品", "断电")):
            return "仓库里能用的东西只剩下最底下一层，药品和弹药都在见底。再拖半天，他们要面对的就不只是外面的怪物，还有队伍自己先垮掉。"

    rewritten = paragraph
    phrase_replacements = {
        "空气里弥漫着": "四周先露出异样",
        "令人窒息": "让呼吸先紧了一分",
        "宿命感": "不祥的预兆",
        "仿佛整个世界都": "周围的一切像是同时",
        "某种说不清": "那股难以忽视的",
        "这一刻": "",
        "不禁": "",
        "只见": "",
        "此刻": "",
        "心中暗道": "在心里迅速过了一遍",
    }
    word_replacements = {
        "压抑": "发闷",
        "窒息": "呼吸发紧",
        "阴冷": "透着凉意",
        "诡异": "不对劲",
        "冰冷": "发凉",
        "危险": "出事的征兆",
        "宿命": "预兆",
        "沉重": "发紧",
        "死寂": "静得过分",
        "森然": "冷硬",
    }
    for phrase in style_profile["forbidden_phrases"]:
        phrase_replacements.setdefault(phrase, "")
    for word in style_profile["forbidden_words"]:
        word_replacements.setdefault(word, "具体异样")

    rewritten = replace_terms(rewritten, phrase_replacements)
    rewritten = replace_terms(rewritten, word_replacements)
    rewritten = re.sub(r"[，、]{2,}", "，", rewritten)
    rewritten = re.sub(r"\s+", "", rewritten)
    rewritten = re.sub(r"^，", "", rewritten)
    if rewritten == paragraph:
        rewritten = paragraph + "（建议改成可见异常、动作受阻或身体反应。）"
    return rewritten


def build_suggestions(
    text: str,
    paragraphs: list[str],
    issues: list[dict[str, object]],
    style_profile: dict[str, object],
) -> list[dict[str, object]]:
    suggestions: list[dict[str, object]] = []
    seen_positions: set[str] = set()
    rewrite_pairs = list(style_profile.get("rewrite_pairs", []))
    positive_patterns = list(style_profile.get("positive_patterns", []))
    recipe_map = {
        str(recipe.get("id", "")): recipe
        for recipe in style_profile.get("scene_recipes", [])
    }
    ordered_issues = sorted(
        issues,
        key=lambda item: (
            0 if str(item.get("type", "")).startswith("scene_recipe_") else 1,
            0 if item.get("severity") == "high" else 1,
        ),
    )
    for issue in ordered_issues:
        position = str(issue.get("position", "global"))
        if position.startswith("p") and position[1:].isdigit():
            paragraph_index = int(position[1:]) - 1
            if 0 <= paragraph_index < len(paragraphs) and position not in seen_positions:
                seen_positions.add(position)
                original = paragraphs[paragraph_index]
                matched_pair_id = ""
                for pair in rewrite_pairs:
                    if pattern_matches_genre(pair, str(style_profile.get("genre", ""))) and pattern_trigger_matches(original, pair):
                        matched_pair_id = str(pair.get("id", ""))
                        break
                matched_positive_id = ""
                positive_example = ""
                for pattern in positive_patterns:
                    if not pattern_matches_genre(pattern, str(style_profile.get("genre", ""))):
                        continue
                    tags = [str(tag) for tag in pattern.get("tags", [])]
                    issue_type = str(issue.get("type", ""))
                    scene_name = str(issue.get("scene", ""))
                    if (
                        issue_type in tags
                        or scene_name in tags
                        or (scene_name and scene_name in str(pattern.get("id", "")))
                    ):
                        matched_positive_id = str(pattern.get("id", ""))
                        positive_example = str(pattern.get("good_example", ""))
                        break
                recipe_id = str(issue.get("recipe_id", ""))
                recipe_steps = recipe_map.get(recipe_id, {}).get("steps", [])
                strategy = issue["reason"] if not recipe_steps else issue["reason"] + " 建议顺序：" + " -> ".join(recipe_steps)
                if positive_example:
                    strategy += f" 正向参照：{positive_example}"
                suggestions.append({
                    "position": position,
                    "issue_type": issue["type"],
                    "strategy": strategy,
                    "original": original,
                    "suggested_rewrite": build_local_rewrite(original, style_profile),
                    "rewrite_pair_id": matched_pair_id,
                    "recipe_id": recipe_id,
                    "scene": issue.get("scene", ""),
                    "positive_pattern_id": matched_positive_id,
                })

    repeated_words = unique_items(list(style_profile["repetition_alert_words"]) + list(style_profile["caution_words"]))
    for word in repeated_words:
        count = text.count(word)
        if count >= 2:
            suggestions.append({
                "position": "global",
                "issue_type": "word_repetition",
                "strategy": f"词语“{word}”出现 {count} 次，建议替换部分为动作、细节或更具体的结果词。",
                "original": word,
                "suggested_rewrite": f"将部分“{word}”改成更具体的感知或结果描述。",
            })
    return suggestions


def build_full_rewrite(text: str, suggestions: list[dict[str, object]]) -> str:
    paragraphs = split_paragraphs(text)
    for item in suggestions:
        position = str(item.get("position", ""))
        if position.startswith("p") and position[1:].isdigit():
            paragraph_index = int(position[1:]) - 1
            if 0 <= paragraph_index < len(paragraphs):
                paragraphs[paragraph_index] = str(item.get("suggested_rewrite", paragraphs[paragraph_index]))
    return "\n\n".join(paragraphs)


def analyze_text(text: str, style_profile: dict[str, object], style_path: Path | None = None) -> dict[str, object]:
    paragraphs = split_paragraphs(text)
    sentences = split_sentences(text)
    issues: list[dict[str, object]] = []

    kb_root = Path(__file__).resolve().parent.parent / "technique-kb"
    kb_genre_profile = load_kb_genre_profile(kb_root, str(style_profile.get("genre", "")))
    kb_book_profile = load_kb_book_profile(kb_root, style_path or Path(""), str(style_profile.get("title", "")))
    effective_profile = merge_style_profiles(kb_genre_profile, kb_book_profile)
    effective_profile = merge_style_profiles(effective_profile, style_profile)
    negative_patterns = load_negative_patterns(kb_root)
    positive_patterns = load_positive_patterns(kb_root)
    rewrite_pairs = load_rewrite_pairs(kb_root)
    scene_recipes = load_scene_recipes(kb_root)
    effective_profile["rewrite_pairs"] = rewrite_pairs
    effective_profile["scene_recipes"] = scene_recipes
    effective_profile["positive_patterns"] = positive_patterns
    lyrical_streak = 0
    lyrical_tolerance = int(effective_profile["thresholds"]["lyrical_paragraph_tolerance"])
    authorial_tolerance = int(effective_profile["thresholds"]["authorial_narration_tolerance"])
    soft_authorial_tolerance = int(effective_profile["thresholds"].get("soft_authorial_tolerance", 1))
    abstract_tolerance = int(effective_profile["thresholds"]["abstract_word_tolerance"])
    allowed_authorial_patterns = set(effective_profile.get("allowed_authorial_patterns", []))
    allowed_phrases = set(effective_profile.get("allowed_phrases", []))

    for index, paragraph in enumerate(paragraphs, start=1):
        hard_authorial_hits = [
            pattern for pattern in AUTHORIAL_HARD_PATTERNS
            if pattern not in allowed_authorial_patterns and pattern in paragraph
        ]
        soft_authorial_hits = [
            pattern for pattern in AUTHORIAL_SOFT_PATTERNS
            if pattern not in allowed_authorial_patterns and pattern in paragraph
        ]
        if len(hard_authorial_hits) > authorial_tolerance:
            issues.append({
                "type": "authorial_narration",
                "severity": "high",
                "position": f"p{index}",
                "reason": f"段落含作者式旁白高风险信号：{', '.join(hard_authorial_hits)}，超过风格阈值 {authorial_tolerance}。",
            })
        if len(soft_authorial_hits) > soft_authorial_tolerance:
            issues.append({
                "type": "authorial_narration_soft",
                "severity": "medium",
                "position": f"p{index}",
                "reason": f"段落含过渡型作者旁白信号：{', '.join(soft_authorial_hits)}，超过软阈值 {soft_authorial_tolerance}。",
            })

        abstract_hits = [word for word in unique_items(list(ABSTRACT_WORDS) + list(effective_profile["forbidden_words"]) + list(effective_profile["caution_words"])) if word in paragraph]
        if len(abstract_hits) > abstract_tolerance:
            issues.append({
                "type": "forced_atmosphere",
                "severity": "high",
                "position": f"p{index}",
                "reason": f"段落堆叠抽象气氛词：{', '.join(abstract_hits)}，超过风格阈值 {abstract_tolerance}。",
            })

        if detect_lyrical_paragraph(paragraph):
            lyrical_streak += 1
        else:
            lyrical_streak = 0
        if lyrical_streak > lyrical_tolerance:
            issues.append({
                "type": "lyrical_overflow",
                "severity": "medium",
                "position": f"p{index}",
                "reason": f"连续抒情段落达到 {lyrical_streak} 段，超过风格阈值 {lyrical_tolerance}。",
            })

    issues.extend(detect_negative_pattern_hits(paragraphs, str(effective_profile.get("genre", "")), negative_patterns))
    issues.extend(detect_scene_recipe_hits(paragraphs, str(effective_profile.get("genre", "")), scene_recipes))

    for phrase in effective_profile["forbidden_phrases"]:
        if phrase in allowed_phrases:
            continue
        count = text.count(phrase)
        if count:
            issues.append({
                "type": "forbidden_phrase",
                "severity": "high",
                "reason": f"命中风格禁写句式“{phrase}” {count} 次。",
            })

    for phrase in effective_profile["caution_phrases"]:
        if phrase in allowed_phrases:
            continue
        count = text.count(phrase)
        if count:
            issues.append({
                "type": "caution_phrase",
                "severity": "medium",
                "reason": f"命中风格慎用句式“{phrase}” {count} 次。",
            })

    for word in effective_profile["forbidden_words"]:
        count = text.count(word)
        if count:
            issues.append({
                "type": "forbidden_word",
                "severity": "medium",
                "reason": f"命中风格禁写词“{word}” {count} 次。",
            })

    issues.extend(repeated_phrases(sentences, effective_profile))
    abstract_counts = abstract_word_counts(text, effective_profile)
    high_freq_abstract = {
        word: count for word, count in abstract_counts.items()
        if count > abstract_tolerance and word in ABSTRACT_WORDS + tuple(effective_profile["repetition_alert_words"])
    }
    if high_freq_abstract:
        issues.append({
            "type": "abstract_word_overuse",
            "severity": "medium",
            "reason": "高频抽象词或预警词过多：" + ", ".join(f"{word}x{count}" for word, count in high_freq_abstract.items()),
        })

    scores = {
        "naturalness": max(0, 100 - len(issues) * 8),
        "viewpoint_integrity": max(0, 100 - sum(12 for item in issues if item["type"] == "authorial_narration") - sum(6 for item in issues if item["type"] == "authorial_narration_soft")),
        "atmosphere_authenticity": max(0, 100 - sum(10 for item in issues if item["type"] in {"forced_atmosphere", "abstract_word_overuse"})),
        "repetition_risk": min(100, sum(18 for item in issues if item["type"] == "repeated_phrase")),
    }

    rewrite_plan = [
        "删除或压缩作者跳出的结论句",
        "把抽象气氛词改写为异常细节、动作受阻或身体反应",
        "压缩重复提示短语，避免模板腔",
    ]
    kb_rewrite_steps = unique_items([
        step
        for item in issues
        for step in item.get("kb_rewrite_strategy", [])
    ])
    if kb_rewrite_steps:
        rewrite_plan.extend(kb_rewrite_steps)
    pair_rewrite_steps = unique_items([
        step
        for pair in rewrite_pairs
        if pattern_matches_genre(pair, str(effective_profile.get("genre", ""))) and pattern_trigger_matches(text, pair)
        for step in pair.get("rewrite_strategy", [])
    ])
    if pair_rewrite_steps:
        rewrite_plan.extend(pair_rewrite_steps)
    recipe_rewrite_steps = unique_items([
        step
        for item in issues
        for step in item.get("recipe_steps", [])
    ])
    if recipe_rewrite_steps:
        rewrite_plan.append("按场景配方重排表达顺序：" + " -> ".join(recipe_rewrite_steps))
    positive_guidance = unique_items([
        str(pattern.get("good_example", "")).strip()
        for pattern in positive_patterns
        if pattern_matches_genre(pattern, str(effective_profile.get("genre", "")))
    ])
    if positive_guidance:
        rewrite_plan.append("参考正向表达样例，优先靠具体反馈、缺口线索或距离变化落地。")
    if effective_profile["forbidden_phrases"] or effective_profile["forbidden_words"]:
        rewrite_plan.append("回查 style.md 的禁写表达与预警词，统一替换为本书允许的表达")
    if effective_profile["narration_rules"]:
        rewrite_plan.append("回查题材口吻基线，确保旁白与反馈方式不偏离当前题材。")

    suggestions = build_suggestions(text, paragraphs, issues, effective_profile)
    rewritten_text = build_full_rewrite(text, suggestions) if suggestions else text

    verdict = "pass"
    if any(item["severity"] == "high" for item in issues):
        verdict = "rewrite"
    elif issues:
        verdict = "warn"

    return {
        "issues": issues,
        "scores": scores,
        "rewrite_plan": rewrite_plan,
        "suggestions": suggestions,
        "rewritten_text": rewritten_text,
        "verdict": verdict,
        "stats": {
            "paragraphs": len(paragraphs),
            "sentences": len(sentences),
            "abstract_word_counts": abstract_counts,
        },
        "style_profile": {
            "title": effective_profile["title"],
            "genre": effective_profile["genre"],
            "book_profile_name": kb_book_profile.get("name", ""),
            "forbidden_phrases": effective_profile["forbidden_phrases"],
            "caution_phrases": effective_profile["caution_phrases"],
            "forbidden_words": effective_profile["forbidden_words"],
            "caution_words": effective_profile["caution_words"],
            "allowed_phrases": effective_profile["allowed_phrases"],
            "narration_rules": effective_profile["narration_rules"],
            "preferred_patterns": effective_profile["preferred_patterns"],
            "thresholds": effective_profile["thresholds"],
            "rewrite_pair_ids": [
                str(pair.get("id", ""))
                for pair in rewrite_pairs
                if pattern_matches_genre(pair, str(effective_profile.get("genre", "")))
            ],
            "positive_pattern_ids": [
                str(pattern.get("id", ""))
                for pattern in positive_patterns
                if pattern_matches_genre(pattern, str(effective_profile.get("genre", "")))
            ],
            "scene_recipe_ids": [
                str(recipe.get("id", ""))
                for recipe in scene_recipes
                if pattern_matches_genre(recipe, str(effective_profile.get("genre", "")))
            ],
        },
    }


def render_markdown(chapter_no: int, chapter_path: Path, analysis: dict[str, object], mode: str) -> str:
    issues = analysis["issues"]
    issue_lines = ["- 无明显语言问题"] if not issues else [
        f"- [{item['severity']}] {item.get('position', 'global')} {item['type']}：{item['reason']}"
        for item in issues
    ]
    rewrite_lines = "\n".join(f"- {line}" for line in analysis["rewrite_plan"])
    suggestion_lines = []
    for item in analysis["suggestions"]:
        suggestion_lines.extend([
            f"### {item['position']} / {item['issue_type']}",
            f"- 原文：{item['original']}",
            f"- 建议：{item['strategy']}",
            f"- 试改：{item['suggested_rewrite']}",
            "",
        ])
    scores = analysis["scores"]
    stats = analysis["stats"]
    style_profile = analysis["style_profile"]
    lines = [
        f"# 第{chapter_no:03d}章语言审计报告",
        "",
        f"- 章节文件：`{chapter_path.as_posix()}`",
        f"- 审计结论：`{analysis['verdict']}`",
        f"- 模式：`{mode}`",
        f"- 风格档案：`{style_profile['title'] or '未命名'}` / 题材：`{style_profile['genre'] or '未设定'}`",
        "",
        "## 评分",
        f"- naturalness: {scores['naturalness']}",
        f"- viewpoint_integrity: {scores['viewpoint_integrity']}",
        f"- atmosphere_authenticity: {scores['atmosphere_authenticity']}",
        f"- repetition_risk: {scores['repetition_risk']}",
        "",
        "## 统计",
        f"- 段落数：{stats['paragraphs']}",
        f"- 句子数：{stats['sentences']}",
        f"- 抽象词频：{json.dumps(stats['abstract_word_counts'], ensure_ascii=False)}",
        f"- 风格阈值：{json.dumps(style_profile['thresholds'], ensure_ascii=False)}",
        "",
        "## 问题清单",
        *issue_lines,
        "",
        "## 改写策略",
        rewrite_lines,
        "",
    ]
    if mode == "suggest":
        suggestion_block = suggestion_lines if suggestion_lines else ["- 无局部改写建议", ""]
        lines.extend([
            "## 局部改写建议",
            *suggestion_block,
            "## 整章建议稿",
            analysis["rewritten_text"] if analysis["rewritten_text"].strip() else "无建议稿",
        ])
    return "\n".join(lines)


def write_outputs(
    project_dir: Path,
    chapter_no: int,
    chapter_path: Path,
    analysis: dict[str, object],
    dry_run: bool,
    mode: str,
    rewrite_out: Path | None,
) -> tuple[Path, Path]:
    gate_dir = project_dir / "04_gate" / f"ch{chapter_no:03d}"
    report_path = gate_dir / "language_report.md"
    result_path = gate_dir / "language_report.json"
    gate_dir.mkdir(parents=True, exist_ok=True)

    if not dry_run:
        report_path.write_text(render_markdown(chapter_no, chapter_path, analysis, mode), encoding="utf-8")
        result_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
        if mode == "suggest" and rewrite_out is not None:
            rewrite_out.parent.mkdir(parents=True, exist_ok=True)
            rewrite_out.write_text(str(analysis["rewritten_text"]), encoding="utf-8")
    return report_path, result_path


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    project_dir = Path(args.project).resolve()
    style_path = Path(args.style).resolve() if args.style else (project_dir / "00_memory" / "style.md")
    rewrite_out = Path(args.rewrite_out).resolve() if args.rewrite_out else None

    try:
        chapter_no, chapter_path = detect_target_chapter(project_dir, args.chapter, args.chapter_no)
    except ValueError as exc:
        print(str(exc))
        return 1

    text = normalize_input_text(chapter_path.read_text(encoding="utf-8"))
    style_profile = parse_style_file(style_path)
    analysis = analyze_text(text, style_profile, style_path)
    report_path, result_path = write_outputs(
        project_dir,
        chapter_no,
        chapter_path,
        analysis,
        args.dry_run,
        args.mode,
        rewrite_out,
    )

    payload = {
        "chapter_no": chapter_no,
        "chapter_path": chapter_path.as_posix(),
        "style_path": style_path.as_posix(),
        "mode": args.mode,
        "verdict": analysis["verdict"],
        "report_path": report_path.as_posix(),
        "result_path": result_path.as_posix(),
        "rewrite_out": rewrite_out.as_posix() if rewrite_out else "",
        "issues": analysis["issues"],
        "scores": analysis["scores"],
        "suggestions": analysis["suggestions"] if args.mode == "suggest" else [],
        "rewritten_text": analysis["rewritten_text"] if args.mode == "suggest" else "",
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"chapter_no={chapter_no}")
        print(f"verdict={analysis['verdict']}")
        print(f"report_path={report_path.as_posix()}")
        print(f"result_path={result_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
