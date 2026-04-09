#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

from novel_utils import detect_existing_chapter_file, read_text
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
SAFE_FORBIDDEN_PHRASE_PATTERNS = {
    "不是试探": (
        r"应该不是试探",
        r"多半不是试探",
        r"大概不是试探",
    ),
}
VAGUE_EXPRESSIONS = (
    "那件事",
    "那个人",
    "那个地方",
    "某种真相",
    "某个答案",
    "说不清",
    "难以言明",
    "不可名状",
    "没有说破",
    "没有点破",
)
OPAQUE_TACTICAL_TERMS = (
    "主口",
    "主杀招",
    "这一口",
    "那一口",
    "压不住",
    "接刃",
    "错灯",
)
OPAQUE_TACTICAL_PATTERNS = (
    "有鬼(?:。|！|？|,|，|$)",
    "不是主杀招",
    "不走主口",
    "事情严重了(?:。|！|？|,|，|$)",
    "局势更坏了(?:。|！|？|,|，|$)",
    "气息一下紧了(?:。|！|？|,|，|$)",
)
OPAQUE_TACTICAL_METAPHOR_PATTERNS = (
    (r"把(?:咱们|我们)?眼睛(?:全)?(?:拽|拖|引)(?:过去|到(?:这|那)边)", "把眼睛拽过去"),
    (r"把(?:咱们|我们)?(?:目光|视线)(?:全)?(?:拽|拖|引)(?:过去|到(?:这|那)边)", "把目光拖过去"),
)
WAR_CONTEXT_MARKERS = (
    "敌军", "敌人", "叛军", "攻城", "守城", "军报", "斥候", "探子", "城墙", "东坡", "西坡",
    "烽火", "烽燧", "粮道", "调兵", "军令", "弓手", "骑兵", "步卒", "前营", "后营", "守军",
)
WAR_FIRST_USE_TERMS = (
    "回风高燧", "高燧", "烽燧", "白甲队", "前屏", "辎重", "哨骑", "游骑", "拒马", "床弩",
    "瓮城", "垛口", "鹿角", "偏师", "疑兵", "督战队", "狼烟台", "烽火台",
)
WAR_TERM_EXPLANATION_PATTERNS = (
    "是", "就是", "指的是", "也就是", "意思是", "其实是", "专门", "负责", "用来", "拿来",
)
WAR_JUDGMENT_MARKERS = (
    "说明", "看来", "显然", "不是试探", "不是主杀招", "不走主口", "多半", "应该", "就是想",
    "这是要", "要断", "要打", "会从", "要从",
)
WAR_FACT_MARKERS = (
    "火把", "脚步", "喊", "鼓", "烟", "箭", "脚印", "军报", "斥候", "探子", "上人", "墙根",
    "东坡", "西坡", "正面", "侧面", "城墙", "粮车", "伤兵", "黑着", "没点", "还在", "前排",
)
WAR_CONSEQUENCE_MARKERS = (
    "不然", "否则", "再拖", "慢一步", "就会", "就要", "会让", "会把", "就得", "守不住",
    "失守", "断粮", "散掉", "摸上来", "空出来", "顶不住",
)
WAR_SHARED_CONDITION_MARKERS = (
    "夜里", "夜色", "天黑", "大雨", "雨夜", "风", "雪", "雾", "地形", "坡", "城墙", "粮道", "山口",
)
OUR_SIDE_MARKERS = ("咱们", "我们", "守军", "城里", "本阵", "自家")
ENEMY_SIDE_MARKERS = ("敌军", "敌人", "他们", "对面", "叛军", "外头", "攻城的")
ORDER_MARKERS = (
    "传令", "下令", "军令", "听令", "号令", "速去", "立刻", "马上", "调", "撤", "守", "封", "补", "点火",
)
ORDER_EXECUTION_PATTERNS = (
    r"(?:你|他|她|他们|亲兵|斥候|弓手|骑兵|步卒|老卒|新兵|守军|白甲队|哨骑).{0,4}(?:去|带|领|押|守|撤|封|补|点|烧|搬|堵|压)",
    r"(?:先|立刻|马上).{0,6}(?:调|撤|守|封|补|点|烧|搬|堵|压)",
)
ORDER_TARGET_MARKERS = (
    "人", "马", "粮", "箭", "门", "坡", "墙", "烽火", "火把", "辎重", "营", "队", "口", "道", "桥",
)
QUESTION_REASON_MARKERS = ("为什么", "凭什么", "怎么判断", "为何", "怎么会")
QUESTION_ACTION_MARKERS = ("怎么办", "怎么做", "现在怎么办", "下一步", "接下来", "先干什么")
QUESTION_YES_NO_MARKERS = ("是不是", "有没有", "能不能", "要不要", "行不行", "对不对", "会不会", "该不该", "你是说")
ANSWER_REASON_MARKERS = (
    "因为", "所以", "看", "听", "前面", "后头", "刚才", "已经", "火把", "人", "马", "粮", "坡", "墙", "门", "探子", "军报",
)
STANCE_ONLY_MARKERS = ("闭嘴", "少废话", "照做", "听令", "先别问", "总之", "反正", "看着就知道")
SUSPENSE_MARKERS = (
    "真相",
    "线索",
    "疑点",
    "破案",
    "凶手",
    "嫌疑",
    "反转",
    "埋伏",
    "身份",
    "暗号",
    "证据",
)
EXPLANATORY_PHRASES = (
    "也就是说", "换句话说", "换言之", "这意味着", "这说明", "显然",
    "其实", "原来", "本质上", "某种程度上", "可以说",
)
OUTLINE_EXPANSION_MARKERS = (
    "说到底",
    "归根结底",
    "真正的问题是",
    "关键在于",
    "问题不在于",
    "本质上",
    "这意味着",
    "这说明",
    "也就是说",
    "换句话说",
)
DIALOGUE_INFO_MARKERS = (
    "也就是说",
    "换句话说",
    "意思是",
    "你要知道",
    "说白了",
    "归根结底",
    "本质上",
    "关键在于",
    "这意味着",
    "这说明",
    "因为",
    "所以",
)
DIALOGUE_CONFLICT_MARKERS = (
    "给我",
    "闭嘴",
    "滚",
    "拿来",
    "交出来",
    "还我",
    "不行",
    "凭什么",
    "现在",
    "马上",
    "先",
    "分",
    "让开",
    "住手",
    "别碰",
)
FAST_VOICE_MARKERS = ("快", "紧", "利落", "凌厉", "直给", "短促")
RESTRAINED_VOICE_MARKERS = ("克制", "冷", "硬", "冷峻", "压住", "收着", "不外放")
ACTION_MARKERS = (
    "说", "问", "看", "走", "退", "冲", "扑", "伸手", "抬手", "落下", "推开",
    "按住", "转身", "咬", "攥", "扯", "拿", "放", "摔", "踢", "站", "跪",
    "拦", "躲", "抬眼", "低头", "掀", "端", "抱", "拖", "砸", "靠近",
)
DEFAULT_THRESHOLDS = {
    "authorial_narration_tolerance": 0,
    "soft_authorial_tolerance": 1,
    "abstract_word_tolerance": 2,
    "repeated_phrase_tolerance": 1,
    "lyrical_paragraph_tolerance": 1,
    "vague_expression_tolerance": 1,
}
LINE_VALUE_RE = re.compile(r"^- ([^：]+)：\s*(.*)$")
STYLE_LIST_FIELD_MAP = {
    "禁止句式": "forbidden_phrases",
    "慎用句式": "caution_phrases",
    "禁止词汇": "forbidden_words",
    "慎用词汇": "caution_words",
    "豁免句式": "allowed_phrases",
    "豁免作者旁白信号": "allowed_authorial_patterns",
    "高频重复预警词": "repetition_alert_words",
}
STYLE_SCALAR_FIELD_MAP = {
    "书名": "title",
    "题材": "genre",
    "节奏基线": "rhythm_baseline",
    "对话占比基线": "dialogue_ratio_baseline",
    "旁白浓度": "narration_density",
    "句式节拍": "sentence_cadence",
    "叙述距离": "narration_distance",
    "必须保住的声音": "must_keep_voice",
    "每章最该留下的读感": "target_reading_feel",
    "信息表达基线": "clarity_baseline",
    "悬疑留白边界": "suspense_reveal_boundary",
}
STYLE_THRESHOLD_FIELD_MAP = {
    "作者式旁白容忍度": ("authorial_narration_tolerance", 0),
    "软作者式旁白容忍度": ("soft_authorial_tolerance", 1),
    "抽象形容词容忍度": ("abstract_word_tolerance", 2),
    "同类句式重复容忍度": ("repeated_phrase_tolerance", 1),
    "纯抒情段落最大连续数": ("lyrical_paragraph_tolerance", 1),
    "隐晦表达容忍度": ("vague_expression_tolerance", 1),
}
VOICE_FIELD_MAP = {
    "叙述距离": "narration_distance",
    "叙述温度": "narration_temperature",
    "句长倾向": "sentence_cadence",
    "节奏倾向": "rhythm_baseline",
    "是否允许作者式旁白": "authorial_permission",
    "必须保住的声音": "must_keep_voice",
    "每章应留下的读感": "target_reading_feel",
    "信息表达基线": "clarity_baseline",
    "悬疑留白边界": "suspense_reveal_boundary",
    "主角": "protagonist_voice",
    "核心配角A": "core_supporting_voice_a",
    "核心配角B": "core_supporting_voice_b",
    "绝不能出现的 AI 味表达": "forbidden_drift",
}


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

def split_paragraphs(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]


def split_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"[。！？；\n]+", text) if part.strip()]

def load_json_file(path: Path) -> dict[str, object]:
    return json.loads(read_text(path))


def iter_text_lines(path: Path) -> list[str]:
    return read_text(path).splitlines()


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


def apply_platform_direction_item(profile: dict[str, object], item: str) -> None:
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
        profile["narration_rules"].extend(
            [
                "少矫情心理戏，优先动作和局势变化",
                "结果变化优先于抒情铺垫",
            ]
        )


def dedupe_style_profile(profile: dict[str, object]) -> dict[str, object]:
    profile["forbidden_phrases"] = unique_items(profile["forbidden_phrases"])
    profile["caution_phrases"] = unique_items(list(DEFAULT_CAUTION_PHRASES) + list(profile["caution_phrases"]))
    profile["forbidden_words"] = unique_items(profile["forbidden_words"])
    profile["caution_words"] = unique_items(profile["caution_words"])
    profile["allowed_phrases"] = unique_items(profile["allowed_phrases"])
    profile["allowed_authorial_patterns"] = unique_items(profile["allowed_authorial_patterns"])
    profile["repetition_alert_words"] = unique_items(profile["repetition_alert_words"])
    profile["narration_rules"] = unique_items(profile["narration_rules"])
    profile["preferred_patterns"] = unique_items(profile["preferred_patterns"])
    return profile


def build_issue(
    issue_type: str,
    severity: str,
    reason: str,
    position: str = "",
) -> dict[str, object]:
    issue: dict[str, object] = {
        "type": issue_type,
        "severity": severity,
        "reason": reason,
    }
    if position:
        issue["position"] = position
    return issue


def collect_counted_issues(
    text: str,
    values: list[str],
    issue_type: str,
    severity: str,
    reason_template: str,
    skipped_values: set[str] | None = None,
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    skipped = skipped_values or set()
    for value in values:
        if value in skipped:
            continue
        count = text.count(value)
        for pattern in SAFE_FORBIDDEN_PHRASE_PATTERNS.get(value, ()):
            count -= len(re.findall(pattern, text))
        if not count:
            continue
        issues.append(build_issue(issue_type, severity, reason_template.format(value=value, count=count)))
    return issues


def build_scores(
    issues: list[dict[str, object]],
    style_consistency_issues: list[dict[str, object]],
    dialogue_voice_issues: list[dict[str, object]],
) -> dict[str, int]:
    return {
        "naturalness": max(0, 100 - len(issues) * 8),
        "viewpoint_integrity": max(
            0,
            100
            - sum(12 for item in issues if item["type"] == "authorial_narration")
            - sum(6 for item in issues if item["type"] == "authorial_narration_soft"),
        ),
        "atmosphere_authenticity": max(
            0,
            100 - sum(10 for item in issues if item["type"] in {"forced_atmosphere", "abstract_word_overuse"}),
        ),
        "repetition_risk": min(100, sum(18 for item in issues if item["type"] == "repeated_phrase")),
        "style_consistency": max(
            0,
            100 - sum(12 if item["severity"] == "high" else 7 for item in style_consistency_issues),
        ),
        "dialogue_distinction": max(
            0,
            100 - sum(12 if item["severity"] == "high" else 8 for item in dialogue_voice_issues),
        ),
    }


def build_rewrite_plan(
    issues: list[dict[str, object]],
    text: str,
    effective_profile: dict[str, object],
    rewrite_pairs: list[dict[str, object]],
    positive_patterns: list[dict[str, object]],
    style_consistency_issues: list[dict[str, object]],
    dialogue_voice_issues: list[dict[str, object]],
) -> list[str]:
    rewrite_plan = [
        "先把谁在做事、为什么这么做、结果变了什么写明白",
        "删除或压缩作者跳出的结论句",
        "把抽象气氛词改写为异常细节、动作受阻或身体反应",
        "压缩重复提示短语，避免模板腔",
    ]

    kb_rewrite_steps = unique_items(
        [step for item in issues for step in item.get("kb_rewrite_strategy", [])]
    )
    if kb_rewrite_steps:
        rewrite_plan.extend(kb_rewrite_steps)

    pair_rewrite_steps = unique_items(
        [
            step
            for pair in rewrite_pairs
            if pattern_matches_genre(pair, str(effective_profile.get("genre", "")))
            and pattern_trigger_matches(text, pair)
            for step in pair.get("rewrite_strategy", [])
        ]
    )
    if pair_rewrite_steps:
        rewrite_plan.extend(pair_rewrite_steps)

    recipe_rewrite_steps = unique_items(
        [step for item in issues for step in item.get("recipe_steps", [])]
    )
    if recipe_rewrite_steps:
        rewrite_plan.append("按场景配方重排表达顺序：" + " -> ".join(recipe_rewrite_steps))

    positive_guidance = unique_items(
        [
            str(pattern.get("good_example", "")).strip()
            for pattern in positive_patterns
            if pattern_matches_genre(pattern, str(effective_profile.get("genre", "")))
        ]
    )
    if positive_guidance:
        rewrite_plan.append("参考正向表达样例，优先靠具体反馈、缺口线索或距离变化落地。")

    if effective_profile["forbidden_phrases"] or effective_profile["forbidden_words"]:
        rewrite_plan.append("回查 style.md 的禁写表达与预警词，统一替换为本书允许的表达")
    if effective_profile["narration_rules"]:
        rewrite_plan.append("回查题材口吻基线，确保旁白与反馈方式不偏离当前题材。")
    if style_consistency_issues:
        rewrite_plan.append("回查 voice.md / style.md 的单书 voice DNA，优先修掉解释腔、抒情腔和节拍漂移。")
    if dialogue_voice_issues:
        rewrite_plan.append("回查 character-voice-diff.md，拉开句长、语速、措辞和压力下的失真方式，避免多人同声。")
    if any(item.get("type") == "outline_expansion_feel" for item in issues):
        rewrite_plan.append("把提纲式结论拆回场面：保留判断，但改成动作受阻、体感变化、资源变化和局面变化。")
    if any(item.get("type") == "dialogue_information_shuttle" for item in issues):
        rewrite_plan.append("对白别替作者补课，优先改成争利益、推责任、压人、自保或试探。")
    if any(item.get("type") == "vague_expression" for item in issues):
        rewrite_plan.append("除悬疑关键点外，把“那个人/那件事/某种真相”改成读者一眼能懂的具体对象。")
    if any(item.get("type") == "opaque_tactical_expression" for item in issues):
        rewrite_plan.append("涉及敌情、军报、权谋判断时，直接补清敌人要干什么、从哪动手、为什么这么判断，别拿黑话和半截结论顶现场。")
    return rewrite_plan


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
        "dialogue_ratio_baseline": "",
        "rhythm_baseline": "",
        "narration_density": "",
        "sentence_cadence": "",
        "narration_distance": "",
        "must_keep_voice": "",
        "target_reading_feel": "",
        "clarity_baseline": "",
        "suspense_reveal_boundary": "",
    }
    if not style_path.exists():
        return profile

    section = ""
    subsection = ""
    for raw_line in iter_text_lines(style_path):
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
            if label in STYLE_LIST_FIELD_MAP:
                profile[STYLE_LIST_FIELD_MAP[label]].extend(parse_inline_list(value))
            elif label in STYLE_SCALAR_FIELD_MAP:
                profile[STYLE_SCALAR_FIELD_MAP[label]] = value.strip()
            elif label in STYLE_THRESHOLD_FIELD_MAP:
                threshold_key, default = STYLE_THRESHOLD_FIELD_MAP[label]
                parsed = parse_scalar_int(value, default)
                profile["thresholds"][threshold_key] = parsed
                profile["explicit_thresholds"][threshold_key] = parsed
            continue

        if stripped.startswith("- "):
            item = stripped[2:].strip().strip("\"'`")
            if not item:
                continue
            if section == "平台方向":
                apply_platform_direction_item(profile, item)
            if section == "负向锚点（去AI化红线）" and subsection == "":
                if item not in profile["caution_phrases"]:
                    profile["caution_phrases"].append(item)
            if "禁止句式" in raw_line:
                continue

    return dedupe_style_profile(profile)


def parse_voice_file(voice_path: Path) -> dict[str, str]:
    profile = {
        "narration_distance": "",
        "narration_temperature": "",
        "sentence_cadence": "",
        "rhythm_baseline": "",
        "authorial_permission": "",
        "must_keep_voice": "",
        "target_reading_feel": "",
        "clarity_baseline": "",
        "suspense_reveal_boundary": "",
        "protagonist_voice": "",
        "core_supporting_voice_a": "",
        "core_supporting_voice_b": "",
        "forbidden_drift": "",
    }
    if not voice_path.exists():
        return profile

    for raw_line in iter_text_lines(voice_path):
        stripped = raw_line.strip()
        match = LINE_VALUE_RE.match(stripped)
        if not match:
            continue
        label, value = match.groups()
        if label in VOICE_FIELD_MAP:
            profile[VOICE_FIELD_MAP[label]] = value.strip()
    return profile


def parse_character_voice_diff(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw_line in iter_text_lines(path):
        stripped = raw_line.strip()
        if stripped.startswith("## 角色"):
            if current:
                entries.append(current)
            current = {"name": stripped.replace("## ", "").strip()}
            continue
        if current is None:
            continue
        match = LINE_VALUE_RE.match(stripped)
        if not match:
            continue
        label, value = match.groups()
        current[label.strip()] = value.strip()
    if current:
        entries.append(current)
    return entries


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
        "dialogue_ratio_baseline": str(override.get("dialogue_ratio_baseline") or base.get("dialogue_ratio_baseline") or ""),
        "rhythm_baseline": str(override.get("rhythm_baseline") or base.get("rhythm_baseline") or ""),
        "narration_density": str(override.get("narration_density") or base.get("narration_density") or ""),
        "sentence_cadence": str(override.get("sentence_cadence") or base.get("sentence_cadence") or ""),
        "narration_distance": str(override.get("narration_distance") or base.get("narration_distance") or ""),
        "must_keep_voice": str(override.get("must_keep_voice") or base.get("must_keep_voice") or ""),
        "target_reading_feel": str(override.get("target_reading_feel") or base.get("target_reading_feel") or ""),
        "clarity_baseline": str(override.get("clarity_baseline") or base.get("clarity_baseline") or ""),
        "suspense_reveal_boundary": str(override.get("suspense_reveal_boundary") or base.get("suspense_reveal_boundary") or ""),
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
        "dialogue_ratio_baseline": "",
        "rhythm_baseline": "",
        "narration_density": "",
        "sentence_cadence": "",
        "narration_distance": "",
        "must_keep_voice": "",
        "target_reading_feel": "",
        "thresholds": dict(DEFAULT_THRESHOLDS),
        "explicit_thresholds": {},
        "clarity_baseline": "",
        "suspense_reveal_boundary": "",
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
                "dialogue_ratio_baseline": payload.get("dialogue_ratio_baseline", ""),
                "rhythm_baseline": payload.get("rhythm_baseline", ""),
                "narration_density": payload.get("narration_density", ""),
                "sentence_cadence": payload.get("sentence_cadence", ""),
                "narration_distance": payload.get("narration_distance", ""),
                "must_keep_voice": payload.get("must_keep_voice", ""),
                "target_reading_feel": payload.get("target_reading_feel", ""),
                "clarity_baseline": payload.get("clarity_baseline", ""),
                "suspense_reveal_boundary": payload.get("suspense_reveal_boundary", ""),
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
        "dialogue_ratio_baseline": "",
        "rhythm_baseline": "",
        "narration_density": "",
        "sentence_cadence": "",
        "narration_distance": "",
        "must_keep_voice": "",
        "target_reading_feel": "",
        "thresholds": dict(DEFAULT_THRESHOLDS),
        "explicit_thresholds": {},
        "clarity_baseline": "",
        "suspense_reveal_boundary": "",
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
                "dialogue_ratio_baseline": payload.get("dialogue_ratio_baseline", ""),
                "rhythm_baseline": payload.get("rhythm_baseline", ""),
                "narration_density": payload.get("narration_density", ""),
                "sentence_cadence": payload.get("sentence_cadence", ""),
                "narration_distance": payload.get("narration_distance", ""),
                "must_keep_voice": payload.get("must_keep_voice", ""),
                "target_reading_feel": payload.get("target_reading_feel", ""),
                "clarity_baseline": payload.get("clarity_baseline", ""),
                "suspense_reveal_boundary": payload.get("suspense_reveal_boundary", ""),
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


def shorten_text(text: str, limit: int = 18) -> str:
    compact = re.sub(r"\s+", "", text)
    if len(compact) <= limit:
        return compact
    return compact[:limit] + "..."


def extract_dialogue_turns(text: str) -> list[dict[str, object]]:
    turns: list[dict[str, object]] = []
    for index, match in enumerate(re.finditer(r"[\u201c\"]([^\u201d\"]+)[\u201d\"]", text), start=1):
        content = match.group(1).strip()
        if not content:
            continue
        turns.append({"index": index, "text": content})
    return turns


def is_war_context(text: str) -> bool:
    return any(marker in text for marker in WAR_CONTEXT_MARKERS)


def term_is_explained(term: str, text: str) -> bool:
    if re.search(rf"{re.escape(term)}[\uff08(][^\uff09)]{{1,24}}[\uff09)]", text):
        return True
    return any(
        re.search(rf"{re.escape(term)}.{{0,10}}{pattern}", text)
        or re.search(rf"{pattern}.{{0,10}}{re.escape(term)}", text)
        for pattern in WAR_TERM_EXPLANATION_PATTERNS
    )


def detect_war_term_explanation_issues(
    paragraph: str,
    next_paragraph: str,
    index: int,
    seen_terms: set[str],
) -> list[dict[str, object]]:
    if not is_war_context(paragraph + next_paragraph):
        return []

    issues: list[dict[str, object]] = []
    window = paragraph + "\n" + next_paragraph
    for term in WAR_FIRST_USE_TERMS:
        if term not in paragraph or term in seen_terms:
            continue
        seen_terms.add(term)
        if term_is_explained(term, window):
            continue
        issues.append(
            build_issue(
                "war_term_first_use_unexplained",
                "high",
                f"术语“{term}”第一次出现时没有就地解释清楚。默认要在同句或下一句写明它是什么、现在拿来做什么、会影响谁。",
                f"p{index}",
            )
        )
    return issues


def line_looks_like_question(line: str) -> bool:
    return (
        "？" in line
        or "?" in line
        or any(marker in line for marker in QUESTION_REASON_MARKERS + QUESTION_ACTION_MARKERS + QUESTION_YES_NO_MARKERS)
    )


def line_has_yes_no_answer(line: str) -> bool:
    return any(token in line for token in ("是", "不是", "有", "没有", "能", "不能", "要", "不要", "行", "不行", "会", "不会", "该", "不该"))


def line_has_reason_answer(line: str) -> bool:
    return any(marker in line for marker in ANSWER_REASON_MARKERS)


def line_has_action_answer(line: str) -> bool:
    return any(marker in line for marker in ACTION_MARKERS + ORDER_MARKERS)


def line_is_stance_only(line: str) -> bool:
    return any(marker in line for marker in STANCE_ONLY_MARKERS) and not (
        line_has_yes_no_answer(line) or line_has_reason_answer(line) or line_has_action_answer(line)
    )


def detect_dialogue_question_answer_issues(text: str) -> tuple[list[dict[str, object]], dict[str, object]]:
    turns = extract_dialogue_turns(text)
    issues: list[dict[str, object]] = []
    checked_pairs = 0
    mismatch_count = 0

    for current, nxt in zip(turns, turns[1:]):
        question = str(current["text"])
        answer = str(nxt["text"])
        if not line_looks_like_question(question):
            continue

        checked_pairs += 1
        if any(marker in question for marker in QUESTION_REASON_MARKERS):
            matched = line_has_reason_answer(answer) or line_has_action_answer(answer)
        elif any(marker in question for marker in QUESTION_ACTION_MARKERS):
            matched = line_has_action_answer(answer) or line_has_reason_answer(answer)
        elif any(marker in question for marker in QUESTION_YES_NO_MARKERS):
            matched = line_has_yes_no_answer(answer) or line_has_reason_answer(answer) or line_has_action_answer(answer)
        else:
            matched = line_has_yes_no_answer(answer) or line_has_reason_answer(answer) or line_has_action_answer(answer)

        if matched and not line_is_stance_only(answer):
            continue

        mismatch_count += 1
        issues.append(
            build_issue(
                "dialogue_question_missed_answer",
                "high",
                f"对白问答没对位：前一句问“{shorten_text(question)}”，后一句答“{shorten_text(answer)}”，没有正面落到结论、原因或下一步动作。",
                f"q{current['index']}",
            )
        )

    return issues, {
        "qa_pairs_checked": checked_pairs,
        "qa_mismatch_count": mismatch_count,
    }


def detect_military_order_issues(
    paragraph: str,
    next_paragraph: str,
    index: int,
) -> list[dict[str, object]]:
    context = paragraph + "\n" + next_paragraph
    if not is_war_context(context):
        return []
    if not any(marker in paragraph for marker in ORDER_MARKERS):
        return []

    actor_action = any(re.search(pattern, context) for pattern in ORDER_EXECUTION_PATTERNS)
    target_or_resource = any(marker in context for marker in ORDER_TARGET_MARKERS)
    consequence = any(marker in context for marker in WAR_CONSEQUENCE_MARKERS)
    if sum((actor_action, target_or_resource, consequence)) >= 2:
        return []

    return [
        build_issue(
            "military_order_execution_chain_missing",
            "high",
            "军令已经下了，但 1-3 句内没交代谁去做、先动什么、慢一步会怎样，像口号，不像执行链。",
            f"p{index}",
        )
    ]


def detect_war_causality_issues(
    paragraph: str,
    next_paragraph: str,
    index: int,
) -> list[dict[str, object]]:
    context = paragraph + "\n" + next_paragraph
    if not is_war_context(context):
        return []

    has_judgment = (
        any(marker in paragraph for marker in WAR_JUDGMENT_MARKERS)
        or any(term in paragraph for term in OPAQUE_TACTICAL_TERMS)
        or any(re.search(pattern, paragraph) for pattern in OPAQUE_TACTICAL_PATTERNS)
    )
    if not has_judgment:
        return []

    has_fact = any(marker in paragraph for marker in WAR_FACT_MARKERS)
    has_consequence = any(marker in context for marker in WAR_CONSEQUENCE_MARKERS)
    issues: list[dict[str, object]] = []

    if not has_fact or not has_consequence:
        missing = []
        if not has_fact:
            missing.append("前置事实")
        if not has_consequence:
            missing.append("后果")
        issues.append(
            build_issue(
                "war_causality_incomplete",
                "high",
                f"战争文判断链不完整，缺少{'和'.join(missing)}。默认先写现场事实，再写判断，最后落到不处理会怎样。",
                f"p{index}",
            )
        )

    if not has_fact and any(marker in paragraph for marker in ("说明", "显然", "多半", "应该", "就是想", "不是")):
        issues.append(
            build_issue(
                "war_reasoning_gap",
                "high",
                "这段更像直接下判断，读者看不到判断依据；先把人、火、坡、墙、兵力变化这些现场证据摆出来。",
                f"p{index}",
            )
        )

    shared_condition = any(marker in context for marker in WAR_SHARED_CONDITION_MARKERS)
    only_our_side = any(marker in context for marker in OUR_SIDE_MARKERS) and not any(marker in context for marker in ENEMY_SIDE_MARKERS)
    if shared_condition and only_our_side and has_judgment:
        issues.append(
            build_issue(
                "war_shared_conditions_missing",
                "high",
                "写了夜色、地形、粮道这类双方共用条件，却只写我方，不写敌方为什么也能借这个条件行动，因果仍是半截。",
                f"p{index}",
            )
        )

    return issues


def build_gate_stats(issues: list[dict[str, object]]) -> dict[str, dict[str, str]]:
    issue_types = {str(item.get("type", "")) for item in issues}
    inference_gap_types = {
        "opaque_tactical_expression",
        "war_term_first_use_unexplained",
        "war_causality_incomplete",
        "war_reasoning_gap",
        "dialogue_question_missed_answer",
        "military_order_execution_chain_missing",
        "war_shared_conditions_missing",
    }
    return {
        "language_block": {
            "plain_language_pass": "no" if issue_types & {"opaque_tactical_expression", "war_term_first_use_unexplained", "vague_expression", "forced_atmosphere"} else "yes",
            "term_explained_on_first_use": "no" if "war_term_first_use_unexplained" in issue_types else "yes",
            "qa_matched": "no" if "dialogue_question_missed_answer" in issue_types else "yes",
            "order_can_execute": "no" if "military_order_execution_chain_missing" in issue_types else "yes",
        },
        "causality_block": {
            "fact_judgment_consequence_clear": "no" if "war_causality_incomplete" in issue_types else "yes",
            "protagonist_reasoning_clear": "no" if issue_types & {"war_reasoning_gap", "opaque_tactical_expression"} else "yes",
            "shared_conditions_checked": "no" if "war_shared_conditions_missing" in issue_types else "yes",
            "reader_inference_gap": "yes" if issue_types & inference_gap_types else "no",
        },
    }



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
    abstract_hits = sum(paragraph.count(word) for word in ABSTRACT_WORDS)
    has_action = any(marker in paragraph for marker in ACTION_MARKERS)
    return abstract_hits >= 2 and not has_action and len(sentences) >= 2


def count_marker_hits(text: str, markers: tuple[str, ...]) -> int:
    return sum(text.count(marker) for marker in markers)


def detect_outline_expansion_issues(paragraphs: list[str]) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    summary_nouns = ("问题", "局势", "局面", "代价", "压力", "结果", "后果", "处境", "选择", "风险")
    scene_action_markers = (
        "伸手", "抬手", "转身", "推开", "按住", "扑过去", "掀开", "端起", "攥紧",
        "扯住", "抬眼", "低头", "站起", "跪下", "抱住", "拖住", "砸下", "踢开",
        "拦住", "躲开",
    )
    for index, paragraph in enumerate(paragraphs, start=1):
        if "“" in paragraph or "\"" in paragraph:
            continue
        sentences = split_sentences(paragraph)
        if len(sentences) < 2:
            continue
        summary_hits = count_marker_hits(paragraph, OUTLINE_EXPANSION_MARKERS)
        abstract_summary_hits = sum(paragraph.count(word) for word in summary_nouns)
        action_hits = count_marker_hits(paragraph, scene_action_markers)
        if summary_hits >= 2 and abstract_summary_hits >= 2 and action_hits == 0:
            issues.append(build_issue(
                "outline_expansion_feel",
                "high" if summary_hits >= 3 else "medium",
                "段落有明显提纲扩写感：结论词和判断词偏多，但没有对应动作、体感或局面变化承载。",
                f"p{index}",
            ))
    return issues


def genre_prefers_suspense(profile: dict[str, object]) -> bool:
    markers = " ".join(
        [
            str(profile.get("genre", "")),
            str(profile.get("suspense_reveal_boundary", "")),
            str(profile.get("clarity_baseline", "")),
        ]
    )
    return any(token in markers for token in ("悬疑", "推理", "探案", "诡异"))


def detect_vague_expression_issues(
    paragraph: str,
    index: int,
    effective_profile: dict[str, object],
) -> list[dict[str, object]]:
    hits = [phrase for phrase in VAGUE_EXPRESSIONS if phrase in paragraph]
    tolerance = int(effective_profile["thresholds"].get("vague_expression_tolerance", 1))
    if len(hits) <= tolerance:
        return []

    suspense_like = genre_prefers_suspense(effective_profile) and any(
        marker in paragraph for marker in SUSPENSE_MARKERS
    )
    if suspense_like and len(hits) <= tolerance + 1:
        return []

    severity = "medium" if suspense_like else "high"
    reason = (
        f"段落用词太虚：{', '.join(hits)}。默认要保持清晰可判读，把人、事、结果落到场面里；"
        "只有悬疑关键点才允许少量留白。"
    )
    return [build_issue("vague_expression", severity, reason, f"p{index}")]


def detect_opaque_tactical_expression_issues(
    paragraph: str,
    index: int,
) -> list[dict[str, object]]:
    hits = [term for term in OPAQUE_TACTICAL_TERMS if term in paragraph]
    regex_hits = [pattern for pattern in OPAQUE_TACTICAL_PATTERNS if re.search(pattern, paragraph)]
    metaphor_hits = [
        label for pattern, label in OPAQUE_TACTICAL_METAPHOR_PATTERNS
        if re.search(pattern, paragraph)
    ]
    if not hits and not regex_hits and not metaphor_hits:
        return []

    normalized_hits = [
        pattern.replace(r"(?:。|！|？|,|，|$)", "")
        for pattern in regex_hits
    ]
    markers = unique_items(hits + normalized_hits + metaphor_hits)
    reason = (
        f"段落用了半截战术黑话或悬空判断：{', '.join(markers)}。"
        "敌情、军报、推理句要直接说清敌人准备怎么打、从哪打、为什么这么判断，"
        "不要只写“有鬼”“主口”“主杀招”或“把眼睛拽过去”这种作者脑内简称和比喻。"
    )
    return [build_issue("opaque_tactical_expression", "high", reason, f"p{index}")]


def count_dialogue_ratio(text: str) -> float:
    dialogue_chars = sum(len(item) for item in re.findall(r"[“\"]([^”\"]+)[”\"]", text))
    total_chars = max(len(re.sub(r"\s+", "", text)), 1)
    return dialogue_chars / total_chars


def voice_prefers_low_dialogue(value: str) -> bool:
    return any(token in value for token in ("低", "少", "克制", "中低", "稀疏"))


def voice_prefers_high_dialogue(value: str) -> bool:
    return any(token in value for token in ("高", "多", "中高", "密"))


def voice_prefers_fast_cadence(value: str) -> bool:
    return any(token in value for token in FAST_VOICE_MARKERS)


def voice_prefers_restrained_tone(text: str) -> bool:
    return any(token in text for token in RESTRAINED_VOICE_MARKERS)


def detect_style_consistency_issues(
    text: str,
    paragraphs: list[str],
    sentences: list[str],
    effective_profile: dict[str, object],
    voice_profile: dict[str, str],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    issues: list[dict[str, object]] = []
    dialogue_ratio = count_dialogue_ratio(text)
    sentence_lengths = [len(sentence) for sentence in sentences if sentence.strip()]
    long_sentence_ratio = (
        sum(1 for length in sentence_lengths if length >= 28) / len(sentence_lengths)
        if sentence_lengths else 0.0
    )
    short_sentence_ratio = (
        sum(1 for length in sentence_lengths if length <= 10) / len(sentence_lengths)
        if sentence_lengths else 0.0
    )
    exclamation_count = text.count("！") + text.count("!")
    question_count = text.count("？") + text.count("?")
    explanatory_hits = {
        phrase: text.count(phrase)
        for phrase in EXPLANATORY_PHRASES
        if text.count(phrase)
    }
    lyrical_paragraphs = sum(1 for paragraph in paragraphs if detect_lyrical_paragraph(paragraph))

    dialogue_baseline = str(effective_profile.get("dialogue_ratio_baseline", ""))
    rhythm_baseline = " ".join(
        part for part in (
            str(effective_profile.get("rhythm_baseline", "")),
            voice_profile.get("rhythm_baseline", ""),
            str(effective_profile.get("must_keep_voice", "")),
            voice_profile.get("must_keep_voice", ""),
            str(effective_profile.get("target_reading_feel", "")),
            voice_profile.get("target_reading_feel", ""),
        ) if part
    )
    cadence_baseline = " ".join(
        part for part in (
            str(effective_profile.get("sentence_cadence", "")),
            voice_profile.get("sentence_cadence", ""),
        ) if part
    )
    authorial_permission = voice_profile.get("authorial_permission", "") or str(effective_profile.get("narration_density", ""))

    if voice_prefers_low_dialogue(dialogue_baseline) and dialogue_ratio >= 0.58:
        issues.append({
            "type": "style_dialogue_ratio_drift",
            "severity": "medium",
            "reason": f"当前对话占比约为 {dialogue_ratio:.0%}，高于书级设定的低对话基线，章节读感可能偏离原书叙述重心。",
        })
    if voice_prefers_high_dialogue(dialogue_baseline) and dialogue_ratio <= 0.12:
        issues.append({
            "type": "style_dialogue_ratio_drift",
            "severity": "medium",
            "reason": f"当前对话占比约为 {dialogue_ratio:.0%}，低于书级设定的高对话基线，信息交换密度可能不足。",
        })

    if voice_prefers_fast_cadence(cadence_baseline) and long_sentence_ratio >= 0.45:
        issues.append({
            "type": "style_cadence_drift",
            "severity": "medium",
            "reason": f"长句比例约为 {long_sentence_ratio:.0%}，与本书偏快、利落的句式节拍不一致。",
        })

    if voice_prefers_restrained_tone(rhythm_baseline) and exclamation_count + question_count >= max(4, len(paragraphs) // 2 + 2):
        issues.append({
            "type": "style_emotion_drift",
            "severity": "medium",
            "reason": "感叹号/问号密度偏高，章节情绪外放程度可能压过本书克制、冷硬的底色。",
        })

    if (
        any(token in authorial_permission for token in ("否", "低", "弱", "克制"))
        and sum(explanatory_hits.values()) >= 3
    ):
        issues.append({
            "type": "style_explanatory_drift",
            "severity": "high" if sum(explanatory_hits.values()) >= 5 else "medium",
            "reason": "解释腔信号偏多："
            + ", ".join(f"{phrase}x{count}" for phrase, count in explanatory_hits.items())
            + "。当前章可能在替读者下判断，而不是让结果自己说话。",
        })

    if voice_prefers_fast_cadence(rhythm_baseline) and lyrical_paragraphs >= max(2, len(paragraphs) // 3):
        issues.append({
            "type": "style_lyrical_drift",
            "severity": "medium",
            "reason": f"疑似抒情段落 {lyrical_paragraphs} 段，偏离本书快反馈/硬反馈的节奏要求。",
        })

    stats = {
        "dialogue_ratio": round(dialogue_ratio, 4),
        "long_sentence_ratio": round(long_sentence_ratio, 4),
        "short_sentence_ratio": round(short_sentence_ratio, 4),
        "exclamation_count": exclamation_count,
        "question_count": question_count,
        "explanatory_hits": explanatory_hits,
        "lyrical_paragraphs": lyrical_paragraphs,
    }
    return issues, stats


def extract_dialogue_lines(text: str) -> list[str]:
    lines = [item.strip() for item in re.findall(r"[“\"]([^”\"]+)[”\"]", text)]
    return [line for line in lines if line]


def dialogue_feature_signature(line: str) -> tuple[str, ...]:
    suffix_tokens = tuple(token for token in ("吗", "呢", "吧", "啊", "了", "罢了", "就是", "行", "可") if token in line)
    prefix = line[:2]
    punctuation = "!" if "！" in line or "!" in line else "?"
    if "？" not in line and "?" not in line and punctuation == "?":
        punctuation = "."
    length_band = "short" if len(line) <= 8 else "mid" if len(line) <= 18 else "long"
    return (prefix, punctuation, length_band, *suffix_tokens[:3])


def detect_dialogue_voice_issues(
    text: str,
    voice_entries: list[dict[str, str]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    issues: list[dict[str, object]] = []
    dialogue_lines = extract_dialogue_lines(text)
    if len(dialogue_lines) < 4:
        return issues, {"dialogue_lines": len(dialogue_lines), "signature_uniqueness": 0.0, "configured_roles": len(voice_entries)}

    signatures = [dialogue_feature_signature(line) for line in dialogue_lines]
    uniqueness = len(set(signatures)) / len(signatures)
    explanatory_dialogue_count = sum(
        1 for line in dialogue_lines if any(phrase in line for phrase in EXPLANATORY_PHRASES)
    )
    same_length_count = sum(1 for line in dialogue_lines if 8 <= len(line) <= 16)
    information_shuttle_count = sum(
        1
        for line in dialogue_lines
        if any(marker in line for marker in DIALOGUE_INFO_MARKERS)
        and not any(marker in line for marker in DIALOGUE_CONFLICT_MARKERS)
        and (len(line) >= 16 or line.count("，") + line.count(",") >= 2)
    )

    if uniqueness <= 0.45 and len(dialogue_lines) >= 6:
        issues.append({
            "type": "dialogue_voice_uniformity",
            "severity": "medium",
            "reason": f"对白签名离散度偏低（{uniqueness:.0%}），多句对白像同一人在说话，存在多人同声风险。",
        })
    if explanatory_dialogue_count >= max(2, len(dialogue_lines) // 3):
        issues.append({
            "type": "dialogue_explanatory_overload",
            "severity": "medium",
            "reason": "对白中的解释腔偏多，人物像在替作者补设定，而不是各自带着立场说话。",
        })
    if same_length_count >= max(4, len(dialogue_lines) - 1):
        issues.append({
            "type": "dialogue_cadence_uniformity",
            "severity": "medium",
            "reason": "多句对白长度过于整齐，节拍像同一模板裁出来，角色区分度不足。",
        })
    if information_shuttle_count >= max(2, len(dialogue_lines) // 3):
        issues.append({
            "type": "dialogue_information_shuttle",
            "severity": "high" if information_shuttle_count >= max(3, len(dialogue_lines) // 2) else "medium",
            "reason": "多句对白更像在搬运信息或代作者讲道理，不像在争利益、压位置、试探底牌或自保。",
        })
    if voice_entries and uniqueness <= 0.6:
        issues.append({
            "type": "dialogue_voice_diff_not_applied",
            "severity": "medium",
            "reason": "项目里已有角色说话差分表，但当前对白仍然偏同声，说明差分没有真正落进正文。",
        })

    stats = {
        "dialogue_lines": len(dialogue_lines),
        "signature_uniqueness": round(uniqueness, 4),
        "explanatory_dialogue_count": explanatory_dialogue_count,
        "same_length_count": same_length_count,
        "information_shuttle_count": information_shuttle_count,
        "configured_roles": len(voice_entries),
    }
    return issues, stats


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
        "主口": "正门",
        "主杀招": "真正的进攻方向",
        "把咱们眼睛全拽过去": "把我们的注意都引到正面",
        "把我们眼睛全拽过去": "把我们的注意都引到正面",
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
    if "有鬼" in rewritten:
        rewritten = rewritten.replace("有鬼", "有埋伏或后手")
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
    voice_root = style_path.parent if style_path is not None else Path(".")
    voice_profile = parse_voice_file(voice_root / "voice.md")
    character_voice_entries = parse_character_voice_diff(voice_root / "character-voice-diff.md")
    lyrical_streak = 0
    seen_war_terms: set[str] = set()
    lyrical_tolerance = int(effective_profile["thresholds"]["lyrical_paragraph_tolerance"])
    authorial_tolerance = int(effective_profile["thresholds"]["authorial_narration_tolerance"])
    soft_authorial_tolerance = int(effective_profile["thresholds"].get("soft_authorial_tolerance", 1))
    abstract_tolerance = int(effective_profile["thresholds"]["abstract_word_tolerance"])
    allowed_authorial_patterns = set(effective_profile.get("allowed_authorial_patterns", []))
    allowed_phrases = set(effective_profile.get("allowed_phrases", []))

    for index, paragraph in enumerate(paragraphs, start=1):
        next_paragraph = paragraphs[index] if index < len(paragraphs) else ""
        issues.extend(detect_vague_expression_issues(paragraph, index, effective_profile))
        issues.extend(detect_opaque_tactical_expression_issues(paragraph, index))
        issues.extend(detect_war_term_explanation_issues(paragraph, next_paragraph, index, seen_war_terms))
        issues.extend(detect_war_causality_issues(paragraph, next_paragraph, index))
        issues.extend(detect_military_order_issues(paragraph, next_paragraph, index))
        hard_authorial_hits = [
            pattern for pattern in AUTHORIAL_HARD_PATTERNS
            if pattern not in allowed_authorial_patterns and pattern in paragraph
        ]
        soft_authorial_hits = [
            pattern for pattern in AUTHORIAL_SOFT_PATTERNS
            if pattern not in allowed_authorial_patterns and pattern in paragraph
        ]
        if len(hard_authorial_hits) > authorial_tolerance:
            issues.append(
                build_issue(
                    "authorial_narration",
                    "high",
                    f"段落含作者式旁白高风险信号：{', '.join(hard_authorial_hits)}，超过风格阈值 {authorial_tolerance}。",
                    f"p{index}",
                )
            )
        if len(soft_authorial_hits) > soft_authorial_tolerance:
            issues.append(
                build_issue(
                    "authorial_narration_soft",
                    "medium",
                    f"段落含过渡型作者旁白信号：{', '.join(soft_authorial_hits)}，超过软阈值 {soft_authorial_tolerance}。",
                    f"p{index}",
                )
            )

        abstract_hits = [word for word in unique_items(list(ABSTRACT_WORDS) + list(effective_profile["forbidden_words"]) + list(effective_profile["caution_words"])) if word in paragraph]
        if len(abstract_hits) > abstract_tolerance:
            issues.append(
                build_issue(
                    "forced_atmosphere",
                    "high",
                    f"段落堆叠抽象气氛词：{', '.join(abstract_hits)}，超过风格阈值 {abstract_tolerance}。",
                    f"p{index}",
                )
            )

        if detect_lyrical_paragraph(paragraph):
            lyrical_streak += 1
        else:
            lyrical_streak = 0
        if lyrical_streak > lyrical_tolerance:
            issues.append(
                build_issue(
                    "lyrical_overflow",
                    "medium",
                    f"连续抒情段落达到 {lyrical_streak} 段，超过风格阈值 {lyrical_tolerance}。",
                    f"p{index}",
                )
            )

    issues.extend(detect_negative_pattern_hits(paragraphs, str(effective_profile.get("genre", "")), negative_patterns))
    issues.extend(detect_scene_recipe_hits(paragraphs, str(effective_profile.get("genre", "")), scene_recipes))

    issues.extend(
        collect_counted_issues(
            text,
            list(effective_profile["forbidden_phrases"]),
            "forbidden_phrase",
            "high",
            "命中风格禁写句式“{value}” {count} 次。",
            allowed_phrases,
        )
    )
    issues.extend(
        collect_counted_issues(
            text,
            list(effective_profile["caution_phrases"]),
            "caution_phrase",
            "medium",
            "命中风格慎用句式“{value}” {count} 次。",
            allowed_phrases,
        )
    )
    issues.extend(
        collect_counted_issues(
            text,
            list(effective_profile["forbidden_words"]),
            "forbidden_word",
            "medium",
            "命中风格禁写词“{value}” {count} 次。",
        )
    )

    issues.extend(repeated_phrases(sentences, effective_profile))
    abstract_counts = abstract_word_counts(text, effective_profile)
    high_freq_abstract = {
        word: count for word, count in abstract_counts.items()
        if count > abstract_tolerance and word in ABSTRACT_WORDS + tuple(effective_profile["repetition_alert_words"])
    }
    if high_freq_abstract:
        issues.append(
            build_issue(
                "abstract_word_overuse",
                "medium",
                "高频抽象词或预警词过多：" + ", ".join(f"{word}x{count}" for word, count in high_freq_abstract.items()),
            )
        )

    issues.extend(detect_outline_expansion_issues(paragraphs))

    style_consistency_issues, style_consistency_stats = detect_style_consistency_issues(
        text,
        paragraphs,
        sentences,
        effective_profile,
        voice_profile,
    )
    issues.extend(style_consistency_issues)
    dialogue_voice_issues, dialogue_voice_stats = detect_dialogue_voice_issues(
        text,
        character_voice_entries,
    )
    issues.extend(dialogue_voice_issues)
    dialogue_qa_issues, dialogue_qa_stats = detect_dialogue_question_answer_issues(text)
    issues.extend(dialogue_qa_issues)
    gate_stats = build_gate_stats(issues)

    scores = build_scores(issues, style_consistency_issues, dialogue_voice_issues)
    rewrite_plan = build_rewrite_plan(
        issues,
        text,
        effective_profile,
        rewrite_pairs,
        positive_patterns,
        style_consistency_issues,
        dialogue_voice_issues,
    )

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
            "style_consistency": style_consistency_stats,
            "dialogue_voice": dialogue_voice_stats,
            "dialogue_qa": dialogue_qa_stats,
            "hard_gates": gate_stats,
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
            "dialogue_ratio_baseline": effective_profile["dialogue_ratio_baseline"],
            "rhythm_baseline": effective_profile["rhythm_baseline"],
            "sentence_cadence": effective_profile["sentence_cadence"],
            "narration_distance": effective_profile["narration_distance"],
            "must_keep_voice": effective_profile["must_keep_voice"],
            "target_reading_feel": effective_profile["target_reading_feel"],
            "clarity_baseline": effective_profile.get("clarity_baseline", ""),
            "suspense_reveal_boundary": effective_profile.get("suspense_reveal_boundary", ""),
            "voice_profile": voice_profile,
            "character_voice_diff_count": len(character_voice_entries),
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
    rewrite_lines = [f"- {line}" for line in analysis["rewrite_plan"]]
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
        *render_score_lines(scores),
        "",
        *render_stats_lines(stats, style_profile),
        "",
        "## 问题清单",
        *issue_lines,
        "",
        "## 改写策略",
        *(rewrite_lines or ["- 无改写策略"]),
        "",
    ]
    if mode == "suggest":
        lines.extend(render_suggest_section(analysis))
    return "\n".join(lines)


def render_suggestion_lines(items: list[dict[str, object]]) -> list[str]:
    lines: list[str] = []
    for item in items:
        lines.extend(
            [
                f"### {item['position']} / {item['issue_type']}",
                f"- 原文：{item['original']}",
                f"- 建议：{item['strategy']}",
                f"- 试改：{item['suggested_rewrite']}",
                "",
            ]
        )
    return lines


def render_score_lines(scores: dict[str, object]) -> list[str]:
    return [
        "## 评分",
        f"- naturalness: {scores['naturalness']}",
        f"- viewpoint_integrity: {scores['viewpoint_integrity']}",
        f"- atmosphere_authenticity: {scores['atmosphere_authenticity']}",
        f"- repetition_risk: {scores['repetition_risk']}",
        f"- style_consistency: {scores['style_consistency']}",
        f"- dialogue_distinction: {scores['dialogue_distinction']}",
    ]


def render_stats_lines(stats: dict[str, object], style_profile: dict[str, object]) -> list[str]:
    return [
        "## 统计",
        f"- 段落数：{stats['paragraphs']}",
        f"- 句子数：{stats['sentences']}",
        f"- 抽象词频：{json.dumps(stats['abstract_word_counts'], ensure_ascii=False)}",
        f"- 风格一致性信号：{json.dumps(stats['style_consistency'], ensure_ascii=False)}",
        f"- 对白差分信号：{json.dumps(stats['dialogue_voice'], ensure_ascii=False)}",
        f"- 风格阈值：{json.dumps(style_profile['thresholds'], ensure_ascii=False)}",
    ]


def render_suggest_section(analysis: dict[str, object]) -> list[str]:
    suggestion_lines = render_suggestion_lines(analysis["suggestions"])
    suggestion_block = suggestion_lines if suggestion_lines else ["- 无局部改写建议", ""]
    return [
        "## 局部改写建议",
        *suggestion_block,
        "## 整章建议稿",
        analysis["rewritten_text"] if analysis["rewritten_text"].strip() else "无建议稿",
    ]


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
        chapter_no, chapter_path = detect_existing_chapter_file(project_dir, args.chapter, args.chapter_no)
    except ValueError as exc:
        print(str(exc))
        return 1

    text = read_text(chapter_path)
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
