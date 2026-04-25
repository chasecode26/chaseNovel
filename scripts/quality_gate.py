#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from aggregation_utils import (
    build_aggregate_payload,
    configure_utf8_stdio,
    run_step_specs,
    write_aggregate_reports,
)
from evaluators.continuity import from_gate_payload
from evaluators.contracts import build_verdict
from evaluators.draft import from_draft_payload
from evaluators.style import from_language_payload
from novel_utils import derive_plan_target_words, read_text

RUNTIME_ONLY_DIMENSIONS = ["character", "causality", "promise_payoff", "pacing", "dialogue"]

QUOTE_PATTERN = re.compile(r"[\"“”「」『』](.*?)[\"“”「」『』]")


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_optional_character_verdict(project_dir: Path) -> dict[str, object] | None:
    payload = load_json(project_dir / "00_memory" / "retrieval" / "leadwriter_character_verdict.json")
    return payload if payload else None


def load_optional_runtime_payload(project_dir: Path, chapter_no: int | None) -> dict[str, object] | None:
    if chapter_no is None:
        return None
    payload = load_json(project_dir / "00_memory" / "retrieval" / "leadwriter_runtime_payload.json")
    if not payload:
        return None
    if int(payload.get("chapter", 0) or 0) != chapter_no:
        return None
    return payload


def locate_chapter_path(project_dir: Path, chapter_no: int | None) -> Path | None:
    if chapter_no is None or chapter_no <= 0:
        return None
    candidates = [
        project_dir / "03_chapters" / f"ch{chapter_no:03d}.md",
        project_dir / "03_chapters" / f"chapter-{chapter_no:03d}.md",
        project_dir / "03_chapters" / f"chapter_{chapter_no:03d}.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def locate_chapter_card_path(project_dir: Path, chapter_no: int | None) -> Path | None:
    if chapter_no is None or chapter_no <= 0:
        return None
    candidates = [
        project_dir / "01_outline" / "chapter_cards" / f"ch{chapter_no:03d}.md",
        project_dir / "01_outline" / "chapter_cards" / f"chapter-{chapter_no:03d}.md",
        project_dir / "01_outline" / "chapter_cards" / f"chapter_{chapter_no:03d}.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def normalize_text(text: str) -> str:
    lowered = text.strip().lower()
    return "".join(char for char in lowered if char.isalnum() or "\u4e00" <= char <= "\u9fff")


def load_characters_markdown(project_dir: Path) -> str:
    return read_text(project_dir / "00_memory" / "characters.md")


def extract_character_profiles(characters_text: str) -> dict[str, dict[str, str]]:
    profiles: dict[str, dict[str, str]] = {}
    current_role = ""
    current_name = ""
    current_fields: dict[str, str] = {}

    def flush() -> None:
        nonlocal current_name, current_fields
        if not current_name:
            return
        profiles[current_name] = {
            "role": current_fields.get("定位", "") or current_role,
            "goal": current_fields.get("当前诉求", ""),
            "fear": current_fields.get("当前恐惧", ""),
            "taboo": current_fields.get("底线/禁忌", ""),
            "decision_style": current_fields.get("决策风格", ""),
            "relationship": current_fields.get("与主角关系", ""),
        }
        current_name = ""
        current_fields = {}

    for raw_line in characters_text.splitlines():
        line = raw_line.strip()
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
        if not line.startswith("- "):
            continue
        payload = line[2:]
        if "：" in payload:
            key, value = payload.split("：", 1)
        elif ":" in payload:
            key, value = payload.split(":", 1)
        else:
            continue
        current_fields[key.strip()] = value.strip()
        if key.strip() == "姓名":
            current_name = value.strip()

    flush()
    return profiles


def extract_card_value(card_text: str, label: str) -> str:
    for raw_line in card_text.splitlines():
        line = raw_line.strip()
        if line.startswith(f"- {label}"):
            _, _, value = line.partition("：")
            if not value:
                _, _, value = line.partition(":")
            return value.strip()
    return ""


def contains_hint(haystack: str, needle: str) -> bool:
    normalized_haystack = normalize_text(haystack)
    normalized_needle = normalize_text(needle)
    if not normalized_needle:
        return True
    if normalized_needle in normalized_haystack:
        return True
    if len(normalized_needle) < 6:
        return False
    chunks = [normalized_needle[index : index + 4] for index in range(0, len(normalized_needle) - 3, 2)]
    hits = sum(chunk in normalized_haystack for chunk in chunks)
    return hits >= min(2, len(chunks))


def count_hint_hits(haystack: str, needles: list[str]) -> int:
    hits = 0
    seen: set[str] = set()
    for needle in needles:
        normalized = normalize_text(needle)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        if contains_hint(haystack, needle):
            hits += 1
    return hits


def split_semantic_phrases(text: str) -> list[str]:
    raw_parts = re.split(r"[，。；：！？、\s]+", str(text))
    phrases: list[str] = []
    seen: set[str] = set()
    weak_tokens = {
        "主角",
        "章节",
        "正文",
        "系统",
        "本章",
        "当前",
        "继续",
        "开始",
        "形成",
        "出现",
        "处理",
        "留下",
        "推进",
        "结果",
        "代价",
        "任务",
        "压力",
        "下一步",
        "下一章",
    }
    for raw in raw_parts:
        phrase = raw.strip("`\"'[]()（）【】《》“”‘’ ")
        normalized = normalize_text(phrase)
        if len(normalized) < 4:
            continue
        if normalized in weak_tokens:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        phrases.append(phrase)
    return phrases


def has_semantic_coverage(haystack: str, text: str, *, min_hits: int = 2) -> bool:
    if contains_hint(haystack, text):
        return True
    phrases = split_semantic_phrases(text)
    if not phrases:
        return False
    required_hits = min(min_hits, len(phrases))
    return count_hint_hits(haystack, phrases) >= required_hits


def collect_body_paragraphs(chapter_lines: list[str]) -> list[str]:
    return [line for line in chapter_lines if line and not line.startswith("#")]


def analyze_repeated_paragraphs(paragraphs: list[str]) -> tuple[int, int, int]:
    normalized = [normalize_text(item) for item in paragraphs]
    normalized = [item for item in normalized if len(item) >= 10]
    if not normalized:
        return (0, 0, 0)

    counts: dict[str, int] = {}
    for item in normalized:
        counts[item] = counts.get(item, 0) + 1

    repeated_total = sum(count for count in counts.values() if count > 1)
    repeated_groups = sum(1 for count in counts.values() if count > 1)

    longest_run = 1
    current_run = 1
    for index in range(1, len(normalized)):
        if normalized[index] == normalized[index - 1]:
            current_run += 1
            longest_run = max(longest_run, current_run)
        else:
            current_run = 1
    return (repeated_total, repeated_groups, longest_run)


def analyze_progression_density(paragraphs: list[str]) -> dict[str, object]:
    marker_groups = {
        "result": [
            "结果",
            "拿回",
            "反击",
            "主动权",
            "赢面",
            "变化",
            "稳住",
            "压住",
            "扳回",
            "兑现",
        ],
        "cost": [
            "代价",
            "价码",
            "成本",
            "结算",
            "回收",
            "押上",
            "负担",
            "牺牲",
            "风险",
        ],
        "pull": [
            "下一步",
            "下一章",
            "继续",
            "钩子",
            "牵引",
            "升级",
            "抬高",
            "逼",
            "倒计时",
            "后面",
        ],
    }
    normalized_paragraphs = [normalize_text(item) for item in paragraphs if normalize_text(item)]
    if not normalized_paragraphs:
        return {
            "progression_paragraphs": 0,
            "deep_progression_paragraphs": 0,
            "longest_flat_run": 0,
            "categories_seen": set(),
        }

    progression_paragraphs = 0
    deep_progression_paragraphs = 0
    longest_flat_run = 0
    current_flat_run = 0
    categories_seen: set[str] = set()

    for paragraph in normalized_paragraphs:
        paragraph_categories = {
            category
            for category, markers in marker_groups.items()
            if any(marker in paragraph for marker in markers)
        }
        if paragraph_categories:
            progression_paragraphs += 1
            categories_seen.update(paragraph_categories)
        if paragraph_categories and ("cost" in paragraph_categories or "pull" in paragraph_categories or len(paragraph_categories) >= 2):
            deep_progression_paragraphs += 1
            current_flat_run = 0
        else:
            current_flat_run += 1
            longest_flat_run = max(longest_flat_run, current_flat_run)

    return {
        "progression_paragraphs": progression_paragraphs,
        "deep_progression_paragraphs": deep_progression_paragraphs,
        "longest_flat_run": longest_flat_run,
        "categories_seen": categories_seen,
    }


def analyze_dialogue_signals(dialogue_lines: list[str]) -> dict[str, int]:
    normalized_lines = [normalize_text(line) for line in dialogue_lines if normalize_text(line)]
    lengths = [len(normalize_text(line)) for line in dialogue_lines if normalize_text(line)]
    unique_count = len(set(normalized_lines))
    question_count = sum(1 for line in dialogue_lines if "?" in line or "？" in line)
    pressure_count = sum(
        1
        for line in dialogue_lines
        if any(token in line for token in ("别", "敢", "必须", "不能", "立刻", "赔", "塌", "代价", "底牌", "输"))
    )
    if lengths:
        min_length = min(lengths)
        max_length = max(lengths)
    else:
        min_length = max_length = 0
    alternating_pairs = 0
    for index in range(1, len(normalized_lines)):
        if normalized_lines[index] != normalized_lines[index - 1]:
            alternating_pairs += 1
    return {
        "unique_count": unique_count,
        "question_count": question_count,
        "pressure_count": pressure_count,
        "alternating_pairs": alternating_pairs,
        "min_length": min_length,
        "max_length": max_length,
    }


def analyze_dialogue_progression(dialogue_lines: list[str]) -> dict[str, int]:
    commitment_markers = [
        "我现在",
        "我只认",
        "我收下",
        "我不会",
        "我看见",
        "记住",
        "拿回主动权",
        "还没输",
    ]
    pressure_markers = [
        "别",
        "必须",
        "不能",
        "立刻",
        "代价",
        "底牌",
        "再拖",
        "彻底失控",
        "到时候",
    ]
    consequence_markers = [
        "局面",
        "主动权",
        "价码",
        "代价",
        "系统",
        "赢面",
        "账",
        "失控",
        "下一步",
    ]
    normalized_lines = [normalize_text(line) for line in dialogue_lines if normalize_text(line)]
    commitment_hits = sum(1 for line in normalized_lines if any(marker in line for marker in commitment_markers))
    pressure_hits = sum(1 for line in normalized_lines if any(marker in line for marker in pressure_markers))
    consequence_hits = sum(1 for line in normalized_lines if any(marker in line for marker in consequence_markers))
    return {
        "commitment_hits": commitment_hits,
        "pressure_hits": pressure_hits,
        "consequence_hits": consequence_hits,
    }


def analyze_character_tension(chapter_haystack: str, protagonist_name: str, counterpart_name: str) -> dict[str, int]:
    interaction_markers = [
        "盯着",
        "压低",
        "试探",
        "追问",
        "没退",
        "停了",
        "迟疑",
        "松动",
        "重新估价",
        "主动权",
        "让出",
        "拉回",
        "收住",
    ]
    normalized_haystack = normalize_text(chapter_haystack)
    name_hits = 0
    if protagonist_name and contains_hint(chapter_haystack, protagonist_name):
        name_hits += 1
    if counterpart_name and contains_hint(chapter_haystack, counterpart_name):
        name_hits += 1
    marker_hits = sum(1 for marker in interaction_markers if marker in normalized_haystack)
    return {"name_hits": name_hits, "marker_hits": marker_hits}


def analyze_relationship_shift(chapter_haystack: str, relationship_text: str, counterpart_name: str) -> dict[str, int]:
    normalized_haystack = normalize_text(chapter_haystack)
    relationship_markers = [
        "信任",
        "戒备",
        "收了一寸",
        "松动",
        "重新估价",
        "不再只会",
        "站位变化",
        "偏移",
        "肯承认",
        "盯着",
    ]
    relationship_hits = sum(1 for marker in relationship_markers if marker in normalized_haystack)
    counterpart_visible = 1 if counterpart_name and contains_hint(chapter_haystack, counterpart_name) else 0
    baseline_relation_visible = 1 if relationship_text and contains_hint(chapter_haystack, relationship_text) else 0
    return {
        "relationship_hits": relationship_hits,
        "counterpart_visible": counterpart_visible,
        "baseline_relation_visible": baseline_relation_visible,
    }


def analyze_information_shift(chapter_haystack: str, dialogue_lines: list[str]) -> dict[str, int]:
    normalized_haystack = normalize_text(chapter_haystack)
    reveal_markers = [
        "听出",
        "看见",
        "意识到",
        "确认",
        "知道",
        "判断",
        "底牌",
        "真话",
        "试出来",
        "估价",
        "看穿",
    ]
    transfer_markers = [
        "第一次",
        "终于",
        "不再",
        "换了人",
        "收了一寸",
        "松动",
        "重新估价",
        "记住",
        "承认",
        "偏移",
    ]
    dialogue_reveal_markers = [
        "你刚才不是",
        "我知道",
        "我看见",
        "你终于",
        "我记住",
        "底牌",
        "真底牌",
    ]
    reveal_hits = sum(1 for marker in reveal_markers if marker in normalized_haystack)
    transfer_hits = sum(1 for marker in transfer_markers if marker in normalized_haystack)
    normalized_dialogue = [normalize_text(line) for line in dialogue_lines if normalize_text(line)]
    dialogue_reveal_hits = sum(
        1 for line in normalized_dialogue if any(marker in line for marker in dialogue_reveal_markers)
    )
    return {
        "reveal_hits": reveal_hits,
        "transfer_hits": transfer_hits,
        "dialogue_reveal_hits": dialogue_reveal_hits,
    }


def analyze_promise_layers(chapter_haystack: str, tail_window: str, result_change: str, hook_text: str) -> dict[str, bool]:
    result_landed = bool(result_change) and has_result_strength(chapter_haystack, result_change)
    tail_landed = bool(hook_text) and has_result_strength(tail_window or chapter_haystack, hook_text)

    escalation_markers = [
        "代价",
        "价码",
        "系统",
        "下一步",
        "下一章",
        "重新抬高",
        "更高",
        "倒计时",
        "继续",
        "牵引",
    ]
    normalized_tail = normalize_text(tail_window or chapter_haystack)
    tail_escalated = any(marker in normalized_tail for marker in escalation_markers)
    return {
        "result_landed": result_landed,
        "tail_landed": tail_landed,
        "tail_escalated": tail_escalated,
    }


def style_behavior_markers(style_text: str) -> list[str]:
    markers: list[str] = []
    style = str(style_text)
    mapping = {
        "谨慎": ["先", "确认", "判断", "稳住", "没有急着", "压稳", "记住"],
        "冷": ["压", "盯", "稳", "硬", "冷", "收住"],
        "硬": ["截断", "顶回", "不退", "更硬", "压回去"],
        "克制": ["没有急着", "压住", "摁回去", "不", "收住"],
        "快": ["立刻", "马上", "直接", "追", "更快"],
        "利": ["掀", "刺", "逼", "压", "截"],
        "嘴硬": ["还没输", "嘴上", "顶", "回顶"],
    }
    for key, values in mapping.items():
        if key in style:
            markers.extend(values)
    deduped: list[str] = []
    seen: set[str] = set()
    for item in markers:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def count_marker_hits(haystack: str, markers: list[str]) -> int:
    hits = 0
    seen: set[str] = set()
    for marker in markers:
        token = str(marker).strip()
        if not token or token in seen:
            continue
        seen.add(token)
        if token in haystack:
            hits += 1
    return hits


def collect_tail_window(lines: list[str], size: int = 6) -> str:
    meaningful = [line for line in lines if line and not line.startswith("#")]
    if not meaningful:
        return ""
    return " ".join(meaningful[-size:])


def result_strength_markers(text: str) -> list[str]:
    phrases = split_semantic_phrases(text)
    markers = list(phrases)
    normalized = normalize_text(text)
    if any(token in normalized for token in ("主动", "反击", "掌握", "赢面", "结果", "兑现")):
        markers.extend(["主动权", "反击", "赢面", "结果", "局部兑现", "不再", "拿回"])
    if any(token in normalized for token in ("代价", "任务", "下一步", "钩子", "升级", "牵引")):
        markers.extend(["代价", "价码", "下一步", "重新抬高", "更高", "牵引", "钩子"])
    deduped: list[str] = []
    seen: set[str] = set()
    for marker in markers:
        token = str(marker).strip()
        normalized_token = normalize_text(token)
        if len(normalized_token) < 2 or normalized_token in seen:
            continue
        seen.add(normalized_token)
        deduped.append(token)
    return deduped


def has_result_strength(haystack: str, text: str, *, min_marker_hits: int = 2) -> bool:
    if has_semantic_coverage(haystack, text):
        return True
    markers = result_strength_markers(text)
    if not markers:
        return False
    return count_marker_hits(haystack, markers) >= min(min_marker_hits, len(markers))


def build_quality_fallback_runtime_verdicts(project_dir: Path, chapter_no: int | None) -> list[dict[str, object]]:
    chapter_path = locate_chapter_path(project_dir, chapter_no)
    if chapter_path is None:
        return []

    chapter_text = read_text(chapter_path)
    card_path = locate_chapter_card_path(project_dir, chapter_no)
    card_text = read_text(card_path) if card_path is not None else ""
    verdicts: list[dict[str, object]] = []

    chapter_lines = [line.strip() for line in chapter_text.splitlines() if line.strip()]
    body_paragraphs = collect_body_paragraphs(chapter_lines)
    paragraph_count = len(body_paragraphs)
    result_change = extract_card_value(card_text, "result_change")
    hook_text = extract_card_value(card_text, "hook_text")
    chapter_haystack = " ".join(chapter_lines)
    chapter_tail_window = collect_tail_window(chapter_lines)
    chapter_char_count = len("".join(line for line in chapter_lines if not line.startswith("#")))
    repeated_total, repeated_groups, longest_repeat_run = analyze_repeated_paragraphs(body_paragraphs)
    progression_signals = analyze_progression_density(body_paragraphs)
    dialogue_lines = [match.group(1).strip() for match in QUOTE_PATTERN.finditer(chapter_text) if match.group(1).strip()]
    information_signals = analyze_information_shift(chapter_haystack, dialogue_lines)

    causality_evidence: list[str] = []
    if paragraph_count < 3:
        causality_evidence.append("正文有效段落过少，难以形成可见因果推进链。")
    if result_change and not has_result_strength(chapter_haystack, result_change):
        causality_evidence.append("章节正文没有明显承接 chapter card 的 result_change。")
    if hook_text and not has_result_strength(chapter_tail_window or chapter_haystack, hook_text):
        causality_evidence.append("章节正文没有把 chapter card 的 hook_text 落到可见尾压。")
    if (
        dialogue_lines
        and information_signals["dialogue_reveal_hits"] > 0
        and information_signals["transfer_hits"] == 0
        and chapter_char_count >= 1200
    ):
        causality_evidence.append("正文出现了试探、看穿或确认底牌的信息信号，但没有把这次信息得知转成后续判断变化或局面位移。")
    if causality_evidence:
        verdicts.append(
            build_verdict(
                dimension="causality",
                status="warn",
                blocking=False,
                evidence=causality_evidence,
                why_it_breaks="章节结果、尾压或信息转手没有落到正文时，会出现卡片成立但读者感受不到推进的断层。",
                minimal_fix="补齐 result_change / hook_text 在正文中的承接，让结果、代价和章尾牵引都有可见证据。",
                rewrite_scope="chapter_result + hook",
            )
        )

    pacing_evidence: list[str] = []
    target_word_count_raw = extract_card_value(card_text, "target_word_count")
    target_word_count = int("".join(char for char in target_word_count_raw if char.isdigit()) or "0")
    if target_word_count > 0:
        min_word_count = max(900, int(target_word_count * 0.45))
        max_word_count = max(target_word_count + 1200, int(target_word_count * 1.6))
        if chapter_char_count < min_word_count:
            pacing_evidence.append(f"正文长度 {chapter_char_count} 低于 runtime 节奏下限 {min_word_count}。")
        elif chapter_char_count > max_word_count:
            pacing_evidence.append(f"正文长度 {chapter_char_count} 高于 runtime 节奏上限 {max_word_count}。")
    if paragraph_count < 3 and chapter_char_count >= max(900, int(target_word_count * 0.35) if target_word_count > 0 else 900):
        pacing_evidence.append("正文有效段落过少，runtime 视角下难以形成层次化 scene 推进。")
    repeated_ratio = (repeated_total / paragraph_count) if paragraph_count else 0.0
    if repeated_total >= 4 and (repeated_ratio >= 0.35 or longest_repeat_run >= 3):
        pacing_evidence.append("正文段落或句群重复度偏高，节奏更像同一拍点的重复铺陈。")
    elif repeated_groups >= 2 and longest_repeat_run >= 2 and repeated_ratio >= 0.45:
        pacing_evidence.append("正文连续重复段较多，scene 推进层次被重复铺陈稀释。")
    progression_paragraphs = int(progression_signals["progression_paragraphs"])
    deep_progression_paragraphs = int(progression_signals["deep_progression_paragraphs"])
    longest_flat_run = int(progression_signals["longest_flat_run"])
    categories_seen = set(progression_signals["categories_seen"])
    if chapter_char_count >= 1200 and paragraph_count >= 4:
        min_progression_paragraphs = max(2, paragraph_count // 4)
        if progression_paragraphs < min_progression_paragraphs:
            pacing_evidence.append(
                f"正文 {paragraph_count} 个有效段落中只有 {progression_paragraphs} 个出现结果、代价或下一步的推进信号，目前更像气氛铺陈而不是 scene 持续前行。"
            )
    if chapter_char_count >= 1500 and paragraph_count >= 5:
        min_deep_progression_paragraphs = max(2, paragraph_count // 5)
        if deep_progression_paragraphs < min_deep_progression_paragraphs:
            pacing_evidence.append("正文缺少“结果+代价/下一步”的深层推进段，可能有表面变化，但没有把后续压力或价码继续抬高。")
    if paragraph_count >= 6 and longest_flat_run >= max(3, paragraph_count // 2):
        pacing_evidence.append(f"正文连续 {longest_flat_run} 个段落没有明显的代价抬升或下一步牵引，scene 推进出现空档。")
    if chapter_char_count >= 1200 and paragraph_count >= 4 and len(categories_seen) <= 1:
        pacing_evidence.append("正文推进信号过于单一，只有局部结果或只有章尾钩子，代价与后续牵引没有在篇幅内拉开。")
    if pacing_evidence:
        verdicts.append(
            build_verdict(
                dimension="pacing",
                status="warn",
                blocking=False,
                evidence=pacing_evidence,
                why_it_breaks="节奏、段落层次和推进密度明显失衡时，章节会像平铺说明或重复铺垫，追读感会断。",
                minimal_fix="补齐 chapter card 的字数目标、场面层次、结果密度和下一步牵引。",
                rewrite_scope="full_chapter",
            )
        )

    promise_evidence: list[str] = []
    promise_layers = analyze_promise_layers(chapter_haystack, chapter_tail_window, result_change, hook_text)
    if hook_text and not promise_layers["tail_landed"]:
        promise_evidence.append("chapter card 的 hook_text 没有在正文里形成明确承诺压力。")
    if result_change and not promise_layers["result_landed"]:
        promise_evidence.append("chapter card 的 result_change 没有在正文里形成可辨识兑现。")
    if result_change and hook_text and promise_layers["result_landed"] and not promise_layers["tail_landed"]:
        promise_evidence.append("正文只落下了短兑现，没有把章尾继续抬成下一步压力，承诺链停在本章。")
    if hook_text and promise_layers["tail_landed"] and not promise_layers["tail_escalated"] and chapter_char_count >= 1200:
        promise_evidence.append("章尾虽然提到了 hook，但没有带出更高代价、倒计时或下一步牵引，长线钩子抬升不足。")
    if promise_evidence:
        verdicts.append(
            build_verdict(
                dimension="promise_payoff",
                status="warn",
                blocking=False,
                evidence=promise_evidence,
                why_it_breaks="承诺如果只留在 chapter card、不进入正文，就会出现卡片成立但读感未兑现的断层。",
                minimal_fix="把 result_change 和 hook_text 映射到正文结果、可见代价和章尾牵引里。",
                rewrite_scope="chapter_result + chapter_tail",
            )
        )

    characters_text = load_characters_markdown(project_dir)
    profiles = extract_character_profiles(characters_text)
    character_evidence: list[str] = []
    if profiles:
        protagonist_name = next(iter(profiles.keys()))
        protagonist = profiles[protagonist_name]
        protagonist_goal = protagonist.get("goal", "").strip()
        protagonist_taboo = protagonist.get("taboo", "").strip()
        protagonist_style = protagonist.get("decision_style", "").strip()
        protagonist_role_hits = count_hint_hits(chapter_haystack, ["主角", protagonist_name, protagonist_goal])
        protagonist_style_hits = count_marker_hits(chapter_text, style_behavior_markers(protagonist_style))
        if protagonist_name and protagonist_name not in chapter_text and protagonist_role_hits < 3:
            character_evidence.append(f"正文没有明确拉出主角“{protagonist_name}”，人物承载不足。")
        if protagonist_goal and protagonist_role_hits < 2 and not contains_hint(chapter_haystack, protagonist_goal):
            character_evidence.append(f"主角当前诉求“{protagonist_goal}”没有明显进入正文推进。")
        if protagonist_style and protagonist_style_hits == 0 and protagonist_role_hits < 3:
            character_evidence.append(f"主角决策风格“{protagonist_style}”没有落到可见动作里。")
        if protagonist_taboo and contains_hint(chapter_haystack, "赌命"):
            character_evidence.append(f"主角禁忌“{protagonist_taboo}”与正文动作存在潜在冲突，需要 runtime 细查。")

        counterpart_name = ""
        counterpart: dict[str, str] = {}
        for name, profile in profiles.items():
            if name == protagonist_name:
                continue
            counterpart_name = name
            counterpart = profile
            break
        should_check_counterpart = bool(dialogue_lines) or counterpart_name in chapter_text or contains_hint(card_text, counterpart_name)
        if counterpart_name and should_check_counterpart:
            counterpart_goal = counterpart.get("goal", "").strip()
            counterpart_fear = counterpart.get("fear", "").strip()
            counterpart_style = counterpart.get("decision_style", "").strip() or counterpart.get("role", "").strip()
            counterpart_relationship = counterpart.get("relationship", "").strip()
            counterpart_hits = count_hint_hits(chapter_haystack, [counterpart_name, counterpart_goal, counterpart_fear])
            counterpart_style_hits = count_marker_hits(chapter_text, style_behavior_markers(counterpart_style))
            tension_signals = analyze_character_tension(chapter_haystack, protagonist_name, counterpart_name)
            relationship_signals = analyze_relationship_shift(chapter_haystack, counterpart_relationship, counterpart_name)
            if counterpart_name not in chapter_text and counterpart_hits < 2:
                character_evidence.append(f"正文没有把对位角色“{counterpart_name}”拉进冲突现场。")
            if counterpart_goal and counterpart_hits < 2 and not contains_hint(chapter_haystack, counterpart_goal):
                character_evidence.append(f"对位角色诉求“{counterpart_goal}”没有进入正文冲突。")
            if counterpart_fear and counterpart_hits < 2 and not contains_hint(chapter_haystack, counterpart_fear):
                character_evidence.append(f"对位角色恐惧“{counterpart_fear}”没有在正文形成压力反馈。")
            if counterpart_style and counterpart_style_hits == 0 and counterpart_hits < 3 and dialogue_lines:
                character_evidence.append(f"对位角色压力风格“{counterpart_style}”没有落到可见反应里。")
            if tension_signals["name_hits"] >= 2 and tension_signals["marker_hits"] == 0 and chapter_char_count >= 1000:
                character_evidence.append(f"主角与对位角色“{counterpart_name}”虽然同场，但缺少可见的施压、迟疑或关系位移，人物张力没有真正起势。")
            elif tension_signals["name_hits"] >= 2 and tension_signals["marker_hits"] <= 1 and dialogue_lines and chapter_char_count >= 1500:
                character_evidence.append(f"主角与对位角色“{counterpart_name}”的对位变化偏弱，正文还没拉出足够明确的压制-反应-再判断链。")
            if (
                relationship_signals["counterpart_visible"]
                and (relationship_signals["baseline_relation_visible"] or dialogue_lines)
                and relationship_signals["relationship_hits"] == 0
                and chapter_char_count >= 1200
            ):
                character_evidence.append(f"主角与对位角色“{counterpart_name}”虽然已建立关系基线，但正文没有写出信任、戒备或站位的可见位移。")
            if (
                counterpart_visible := relationship_signals["counterpart_visible"]
            ) and information_signals["dialogue_reveal_hits"] > 0 and information_signals["transfer_hits"] == 0 and chapter_char_count >= 1200:
                character_evidence.append(f"对位角色“{counterpart_name}”虽然已经试出信息或听出表态，但人物关系没有因此发生可见变化，信息差还没真正转手。")
    if character_evidence:
        verdicts.append(
            build_verdict(
                dimension="character",
                status="warn",
                blocking=False,
                evidence=character_evidence,
                why_it_breaks="没有 runtime character verdict 时，至少要防止人物诉求、禁忌和对位关系完全脱离正文。",
                minimal_fix="把主角诉求、禁忌和对位角色压力直接落到动作、对白与结果变化里。",
                rewrite_scope="scene_beats + dialogue",
            )
        )

    dialogue_evidence: list[str] = []
    if len(dialogue_lines) < 2:
        dialogue_evidence.append("正文有效对白少于 2 句，难以观察角色问答与施压差分。")
    else:
        dialogue_signals = analyze_dialogue_signals(dialogue_lines)
        dialogue_progression = analyze_dialogue_progression(dialogue_lines)
        if dialogue_signals["unique_count"] <= 1:
            dialogue_evidence.append("多句对白几乎是同一模板回声，角色区分度不足。")
        if dialogue_signals["alternating_pairs"] < max(1, len(dialogue_lines) // 3):
            dialogue_evidence.append("对白回合切换太少，来回施压和反击感不足。")
        if dialogue_signals["question_count"] == 0 and dialogue_signals["pressure_count"] == 0:
            dialogue_evidence.append("对白里缺少追问或施压信号，更像平铺说明而不是交锋。")
        if dialogue_signals["max_length"] > 0 and dialogue_signals["min_length"] > 0:
            if dialogue_signals["max_length"] - dialogue_signals["min_length"] <= 4 and len(dialogue_lines) >= 3:
                dialogue_evidence.append("多句对白句长过于整齐，身份和情绪节奏差分不够。")
        if len(dialogue_lines) >= 3 and dialogue_progression["commitment_hits"] == 0:
            dialogue_evidence.append("对白虽然成段出现，但没有拉出明确站位、决定或表态，交锋之后缺少角色把话钉死的力道。")
        if len(dialogue_lines) >= 3 and dialogue_progression["pressure_hits"] == 0 and dialogue_signals["question_count"] <= 1:
            dialogue_evidence.append("对白缺少持续施压或逼问，更多是在轮流发声，没有把对话推成真正的攻防。")
        if len(dialogue_lines) >= 3 and dialogue_progression["consequence_hits"] == 0 and chapter_char_count >= 1000:
            dialogue_evidence.append("对白没有把局面变化、代价或下一步牵引说实，听感像情绪交换而不是推动剧情。")
        if (
            len(dialogue_lines) >= 3
            and information_signals["dialogue_reveal_hits"] > 0
            and information_signals["transfer_hits"] == 0
            and chapter_char_count >= 1000
        ):
            dialogue_evidence.append("对白里已经出现试探、看穿或确认信息的信号，但没有把信息差转成新的站位、压制或关系变化。")
    if dialogue_evidence:
        verdicts.append(
            build_verdict(
                dimension="dialogue",
                status="warn",
                blocking=False,
                evidence=dialogue_evidence,
                why_it_breaks="没有 runtime dialogue verdict 时，至少要防止对白层完全空转或模板化。",
                minimal_fix="补足成对问答、回击和施压，不要让对白只剩单一口气或作者转述。",
                rewrite_scope="dialogue",
            )
        )
    return verdicts


def build_schema_verdicts(project_dir: Path) -> list[dict[str, object]]:
    schema_dir = project_dir / "00_memory" / "schema"
    reports_dir = project_dir / "05_reports"
    plan_text = read_text(project_dir / "00_memory" / "plan.md")
    plan_json = load_json(schema_dir / "plan.json")
    character_arcs_json = load_json(schema_dir / "character_arcs.json")
    foreshadow_json = load_json(reports_dir / "foreshadow_heatmap.json")
    arc_json = load_json(reports_dir / "arc_health.json")

    verdicts: list[dict[str, object]] = []

    plan_evidence: list[str] = []
    if not str(plan_json.get("title", "")).strip():
        plan_evidence.append("plan schema 缺少书名。")
    if not str(plan_json.get("genre", "")).strip():
        plan_evidence.append("plan schema 缺少题材。")
    plan_hook = str(plan_json.get("hook", "")).strip()
    if not plan_hook and "核心卖点" in plan_text:
        plan_hook = "derived-from-plan-md"
    if not plan_hook:
        plan_evidence.append("plan schema 缺少核心 hook。")
    plan_target_words = int(plan_json.get("targetWords", 0) or 0)
    if plan_target_words <= 0:
        plan_target_words = derive_plan_target_words(plan_text)
    if plan_target_words <= 0:
        plan_evidence.append("plan schema 还没有有效总字数目标。")
    verdicts.append(
        build_verdict(
            dimension="plan",
            status="warn" if plan_evidence else "pass",
            blocking=False,
            evidence=plan_evidence,
            why_it_breaks="卷级规划缺口会削弱章节目标与长线推进的一致性。",
            minimal_fix="补齐 plan schema 的书名、题材、hook 和总字数目标。",
            rewrite_scope="planning_memory",
        )
    )

    foreshadow_evidence: list[str] = []
    overdue = foreshadow_json.get("overdue", [])
    due = foreshadow_json.get("due", [])
    if isinstance(overdue, list) and overdue:
        foreshadow_evidence.append(f"存在 {len(overdue)} 条超期伏笔。")
    if isinstance(due, list) and due:
        foreshadow_evidence.append(f"当前章节有 {len(due)} 条到期伏笔待回收。")
    verdicts.append(
        build_verdict(
            dimension="foreshadow",
            status="warn" if foreshadow_evidence else "pass",
            blocking=False,
            evidence=foreshadow_evidence,
            why_it_breaks="伏笔到期但未调度时，会削弱回收节奏和读者记忆热度。",
            minimal_fix="安排到期/超期伏笔的回收窗口，或明确延后策略。",
            rewrite_scope="chapter_result_and_hook",
        )
    )

    arc_evidence: list[str] = []
    stalled_count = int(arc_json.get("stalled_arc_count", 0) or 0)
    schema_arcs = character_arcs_json.get("arcs", [])
    report_arcs = arc_json.get("character_arcs", [])
    has_schema_arcs = isinstance(schema_arcs, list) and len(schema_arcs) > 0
    has_report_arcs = isinstance(report_arcs, list) and len(report_arcs) > 0
    if stalled_count > 0:
        arc_evidence.append(f"存在 {stalled_count} 个角色弧停滞风险。")
    if not has_report_arcs and not has_schema_arcs:
        arc_evidence.append("character arc schema/报告仍为空。")
    verdicts.append(
        build_verdict(
            dimension="arc",
            status="warn" if arc_evidence else "pass",
            blocking=False,
            evidence=arc_evidence,
            why_it_breaks="角色弧停滞或缺失时，章节推进会失去人物层结果变化。",
            minimal_fix="补齐角色弧状态，并把本章结果挂到角色阶段变化上。",
            rewrite_scope="character_arc_memory + chapter_result",
        )
    )
    return verdicts


def build_verdicts(steps: list[dict[str, object]]) -> list[dict[str, object]]:
    verdicts: list[dict[str, object]] = []
    for step in steps:
        script_name = str(step.get("script", ""))
        if script_name == "chapter_gate.py":
            verdicts.append(from_gate_payload(step))
        elif script_name == "draft_gate.py":
            verdicts.append(from_draft_payload(step))
        elif script_name == "language_audit.py":
            verdicts.append(from_language_payload(step))
    return verdicts


def build_runtime_verdicts(runtime_payload: dict[str, object]) -> list[dict[str, object]]:
    verdicts = runtime_payload.get("verdicts", [])
    if not isinstance(verdicts, list):
        return []
    return [
        verdict
        for verdict in verdicts
        if isinstance(verdict, dict) and str(verdict.get("dimension", "")).strip() in set(RUNTIME_ONLY_DIMENSIONS)
    ]


def verdict_rank(verdict: dict[str, object]) -> tuple[int, int, int]:
    status_rank = {"pass": 0, "warn": 1, "fail": 2}.get(str(verdict.get("status", "pass")), 0)
    evidence = verdict.get("evidence", [])
    evidence_count = len(evidence) if isinstance(evidence, list) else 0
    return (1 if bool(verdict.get("blocking")) else 0, status_rank, evidence_count)


def merge_verdicts(verdicts: list[dict[str, object]]) -> list[dict[str, object]]:
    merged: dict[str, dict[str, object]] = {}
    order: list[str] = []
    for verdict in verdicts:
        if not isinstance(verdict, dict):
            continue
        dimension = str(verdict.get("dimension", "")).strip()
        if not dimension:
            continue
        if dimension not in merged:
            merged[dimension] = verdict
            order.append(dimension)
            continue
        if verdict_rank(verdict) > verdict_rank(merged[dimension]):
            merged[dimension] = verdict
    return [merged[dimension] for dimension in order]


def summarize_verdict_status(step_status: str, verdicts: list[dict[str, object]]) -> str:
    has_blocking = any(bool(item.get("blocking")) for item in verdicts if isinstance(item, dict))
    has_warn = any(str(item.get("status", "pass")).strip() == "warn" for item in verdicts if isinstance(item, dict))
    if step_status == "fail" or has_blocking:
        return "fail"
    if step_status == "warn" or has_warn:
        return "warn"
    return "pass"


def summarize_final_release(step_status: str, verdicts: list[dict[str, object]]) -> str:
    has_blocking = any(bool(item.get("blocking")) for item in verdicts if isinstance(item, dict))
    has_fail = any(str(item.get("status", "pass")).strip() == "fail" for item in verdicts if isinstance(item, dict))
    if step_status == "fail" or has_blocking or has_fail:
        return "revise"
    return "pass"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run draft / chapter / language gates as one quality step.")
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument(
        "--check",
        choices=["all", "chapter", "draft", "language", "batch"],
        default="all",
        help="Quality sub-check to run; defaults to all chapter-level checks",
    )
    parser.add_argument("--chapter-no", type=int, help="Target chapter number")
    parser.add_argument("--from", dest="chapter_from", type=int, help="Batch start chapter")
    parser.add_argument("--to", dest="chapter_to", type=int, help="Batch end chapter")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    parser.add_argument("--skip-runtime-verdicts", action="store_true", help="Ignore persisted runtime verdicts")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    return parser.parse_args()


def main() -> int:
    configure_utf8_stdio()
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    shared = ["--project", args.project]
    if args.dry_run:
        shared.append("--dry-run")

    if args.check == "batch" or args.chapter_from is not None or args.chapter_to is not None:
        batch_args = shared[:]
        if args.chapter_from is not None:
            batch_args.extend(["--from", str(args.chapter_from)])
        if args.chapter_to is not None:
            batch_args.extend(["--to", str(args.chapter_to)])
        step_specs = [("batch_gate.py", batch_args)]
    else:
        if args.chapter_no is None:
            raise SystemExit("--chapter-no is required unless running batch mode")
        chapter_args = [*shared, "--chapter-no", str(args.chapter_no)]
        if args.check == "chapter":
            step_specs = [("chapter_gate.py", chapter_args)]
        elif args.check == "draft":
            step_specs = [("draft_gate.py", chapter_args)]
        elif args.check == "language":
            step_specs = [("language_audit.py", chapter_args)]
        else:
            step_specs = [
                ("chapter_gate.py", chapter_args),
                ("draft_gate.py", chapter_args),
                ("language_audit.py", chapter_args),
            ]

    steps = run_step_specs(repo_root, step_specs)
    payload = build_aggregate_payload(project=args.project, steps=steps, extra_fields={"check": args.check})

    project_dir = Path(args.project).resolve()
    verdicts = build_verdicts(steps)
    verdicts.extend(build_schema_verdicts(project_dir))

    runtime_payload: dict[str, object] | None = None
    runtime_verdicts: list[dict[str, object]] = []
    fallback_runtime_verdicts: list[dict[str, object]] = []
    if not args.skip_runtime_verdicts:
        runtime_payload = load_optional_runtime_payload(project_dir, args.chapter_no)
        if isinstance(runtime_payload, dict):
            runtime_verdicts = build_runtime_verdicts(runtime_payload)
            verdicts.extend(runtime_verdicts)
        else:
            fallback_runtime_verdicts = build_quality_fallback_runtime_verdicts(project_dir, args.chapter_no)
            verdicts.extend(fallback_runtime_verdicts)

    character_verdict = load_optional_character_verdict(project_dir)
    if (
        isinstance(character_verdict, dict)
        and str(character_verdict.get("dimension", "")).strip() == "character"
        and not any(str(item.get("dimension", "")).strip() == "character" for item in verdicts if isinstance(item, dict))
    ):
        verdicts.append(character_verdict)

    verdicts = merge_verdicts(verdicts)
    loaded_runtime_dimensions = [
        str(item.get("dimension", "")).strip()
        for item in runtime_verdicts
        if isinstance(item, dict) and str(item.get("dimension", "")).strip()
    ]
    fallback_runtime_dimensions = [
        str(item.get("dimension", "")).strip()
        for item in fallback_runtime_verdicts
        if isinstance(item, dict) and str(item.get("dimension", "")).strip()
    ]
    missing_runtime_dimensions = [
        dimension
        for dimension in RUNTIME_ONLY_DIMENSIONS
        if dimension not in loaded_runtime_dimensions and dimension not in fallback_runtime_dimensions
    ]
    payload["verdicts"] = verdicts
    payload["status"] = summarize_verdict_status(str(payload.get("status", "pass")), verdicts)
    payload["final_release"] = summarize_final_release(str(payload.get("status", "pass")), verdicts)
    payload["runtime_only_dimensions"] = RUNTIME_ONLY_DIMENSIONS
    payload["loaded_runtime_dimensions"] = loaded_runtime_dimensions
    payload["fallback_runtime_dimensions"] = fallback_runtime_dimensions
    payload["missing_runtime_dimensions"] = [] if args.skip_runtime_verdicts else missing_runtime_dimensions
    payload["runtime_verdict_source"] = (
        "skipped"
        if args.skip_runtime_verdicts
        else (
            "persisted_runtime_payload"
            if isinstance(runtime_payload, dict)
            else ("quality_fallback" if fallback_runtime_dimensions else "not_available")
        )
    )
    payload["blocking_dimensions"] = [
        str(item.get("dimension", "")).strip()
        for item in verdicts
        if isinstance(item, dict) and (bool(item.get("blocking")) or str(item.get("status", "pass")).strip() == "fail")
    ]
    payload["advisory_dimensions"] = [
        str(item.get("dimension", "")).strip()
        for item in verdicts
        if isinstance(item, dict)
        and not bool(item.get("blocking"))
        and str(item.get("status", "pass")).strip() == "warn"
    ]
    payload["report_paths"] = {
        **payload.get("report_paths", {}),
        **(
            {}
            if args.dry_run
            else write_aggregate_reports(
                project_dir,
                payload,
                base_name="quality_gate_report",
                heading="质量闸门汇总报告",
                mode_line=f"- 检查模式：`{args.check}`",
            )
        ),
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"check={payload['check']}")
        print(f"warning_count={payload['warning_count']}")
        if isinstance(payload.get("report_paths"), dict) and payload["report_paths"].get("markdown"):
            print(f"report={payload['report_paths']['markdown']}")
    return 0 if payload["status"] != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
