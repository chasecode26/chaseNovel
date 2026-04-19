#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from novel_utils import (
    chapter_number_from_name,
    detect_current_chapter,
    extract_line,
    extract_markdown_table_rows,
    extract_state_value,
    has_placeholder,
    load_due_foreshadow_ids,
    read_text,
    render_list,
    useful_lines,
)


HEALTH_DIGEST_LIMIT = 3


UPGRADE_KEYWORDS = (
    "反击",
    "破局",
    "摊牌",
    "翻盘",
    "拿下",
    "获得",
    "失去",
    "突破",
    "晋升",
    "暴露",
    "揭开",
    "兑现",
    "结盟",
    "开战",
    "站队",
    "掌握",
    "改命",
    "追上",
    "反杀",
    "夺下",
)
ACTION_KEYWORDS = (
    "查",
    "追",
    "杀",
    "退",
    "潜",
    "谈",
    "问",
    "拿",
    "换",
    "走",
    "守",
    "破",
    "探",
    "夺",
    "守住",
    "逼近",
    "布局",
    "试探",
    "回京",
    "截",
    "埋伏",
)
HOOK_KEYWORDS = (
    "危机",
    "压力",
    "代价",
    "牵引",
    "真相",
    "身份",
    "暴露",
    "强敌",
    "名额",
    "站队",
    "追杀",
    "倒计时",
    "期限",
    "赌约",
    "下一步",
    "交易",
    "反转",
    "伏笔",
    "旧账",
)

PRIORITY_DEBT_RULES = (
    {
        "key": "repeat_variation",
        "label": "重复债",
        "markers": ("repeat_warning_threshold", "重复阈值"),
        "reason": "近章重复风险已经抬头，本章不能只是复写旧冲突或旧钩子。",
        "action": "优先做结果升级或钩子换型，让本章产生不同于近章的净变化。",
    },
    {
        "key": "promise_payoff",
        "label": "承诺债",
        "markers": ("promise_threshold", "承诺阈值"),
        "reason": "高压承诺积压过多，爽点与兑现不能继续后拖。",
        "action": "优先推进或兑现至少一条高压承诺，并明确代价变化。",
    },
    {
        "key": "foreshadow_payoff",
        "label": "伏笔债",
        "markers": ("overdue_foreshadow_threshold", "伏笔阈值"),
        "reason": "到期伏笔正在堆积，读者会开始感到悬念只埋不收。",
        "action": "优先回收一条到期伏笔，或让它进入明确可见的兑现链路。",
    },
    {
        "key": "arc_progression",
        "label": "弧线债",
        "markers": ("stalled_arc_threshold", "停滞阈值"),
        "reason": "角色/主线弧存在停滞风险，本章需要给弧线一个可见位移。",
        "action": "优先推进当前弧线阶段，让人物关系、目标或局势至少有一格变化。",
    },
    {
        "key": "milestone_delivery",
        "label": "节点债",
        "markers": ("checkpoint_words", "due_soon_window", "节点字数", "预警窗口"),
        "reason": "阶段节点已经逼近，本章不能继续空转铺垫。",
        "action": "优先落地阶段性结果，让本章承担节点前的关键推进职责。",
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a pre-draft chapter planning review for chaseNovel projects."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument(
        "--chapter",
        type=int,
        help="Existing drafted current chapter number. Planning review targets the next chapter by default.",
    )
    parser.add_argument("--target-chapter", type=int, help="Explicit target chapter number")
    parser.add_argument("--output", help="Optional output markdown path")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(read_text(path))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_health_digest(project_dir: Path) -> list[str]:
    candidates = [
        project_dir / "05_reports" / "pipeline_report.json",
        project_dir / "00_memory" / "retrieval" / "health_digest.json",
        project_dir / "00_memory" / "retrieval" / "dashboard_cache.json",
    ]
    for path in candidates:
        payload = load_json(path)
        digest = payload.get("health_digest", [])
        if isinstance(digest, list) and digest:
            return [str(item) for item in digest[:HEALTH_DIGEST_LIMIT]]
    return []


def derive_priority_debt(health_digest: list[str]) -> dict[str, str]:
    if not health_digest:
        return {}

    for digest_line in health_digest:
        lowered = digest_line.lower()
        for rule in PRIORITY_DEBT_RULES:
            if any(marker.lower() in lowered for marker in rule["markers"]):
                return {
                    "key": str(rule["key"]),
                    "label": str(rule["label"]),
                    "reason": str(rule["reason"]),
                    "action": str(rule["action"]),
                    "source": digest_line,
                }

    return {
        "key": "general_health_debt",
        "label": "健康债",
        "reason": "health_digest 已提示跨步骤风险，本章需要优先处理其中最紧的一项。",
        "action": "优先回应首条风险，不让新的章节继续累积旧债。",
        "source": health_digest[0],
    }


def extract_present_line(text: str, label: str) -> str:
    value = extract_line(text, label)
    return "" if has_placeholder(value) else value


def detect_target_chapter(state_text: str, chapter: int | None, target_chapter: int | None) -> int:
    if target_chapter is not None:
        return max(target_chapter, 1)
    if chapter is not None:
        return max(chapter + 1, 1)
    return max(detect_current_chapter(state_text) + 1, 1)


def extract_next_goal(state_text: str) -> str:
    direct = extract_present_line(state_text, "- 下章预告") or extract_present_line(state_text, "下章预告")
    if direct:
        return direct

    section_match = re.search(r"##\s*下章预告\s*(.*?)(?:\n##\s+|\Z)", state_text, re.S)
    if not section_match:
        return ""

    section_text = section_match.group(1)
    return (
        extract_present_line(section_text, "- 计划内容")
        or extract_present_line(section_text, "计划内容")
        or extract_present_line(section_text, "- 章节目标")
        or extract_present_line(section_text, "章节目标")
    )


def load_runtime_context(project_dir: Path, target_chapter: int) -> dict[str, object]:
    previous_chapter = max(target_chapter - 1, 0)
    context_parts: list[str] = []
    excerpt_lines: list[str] = []
    next_goal = ""

    if previous_chapter <= 0:
        return {"text": "", "excerpt": [], "next_goal": "", "source": ""}

    retrieval_dir = project_dir / "00_memory" / "retrieval"
    runtime_payload = load_json(retrieval_dir / "leadwriter_runtime_payload.json")
    if int(runtime_payload.get("chapter", 0) or 0) == previous_chapter:
        draft = runtime_payload.get("draft", {})
        brief = runtime_payload.get("brief", {})
        if isinstance(draft, dict):
            outcome_signature = draft.get("outcome_signature", {})
            if isinstance(outcome_signature, dict):
                next_goal = str(outcome_signature.get("next_pull", "")).strip()
                chapter_result = str(outcome_signature.get("chapter_result", "")).strip()
                if chapter_result:
                    excerpt_lines.append(f"chapter_result: {chapter_result}")
                if next_goal:
                    excerpt_lines.append(f"next_pull: {next_goal}")
            character_constraints = draft.get("character_constraints", {})
            if isinstance(character_constraints, dict):
                protagonist_goal = str(character_constraints.get("protagonist_goal", "")).strip()
                counterpart_goal = str(character_constraints.get("counterpart_goal", "")).strip()
                if protagonist_goal:
                    excerpt_lines.append(f"protagonist_goal: {protagonist_goal}")
                if counterpart_goal:
                    excerpt_lines.append(f"counterpart_goal: {counterpart_goal}")
        if isinstance(brief, dict):
            scene_plan = brief.get("scene_plan", [])
            success_criteria = brief.get("success_criteria", [])
            if isinstance(scene_plan, list):
                excerpt_lines.extend(str(item).strip() for item in scene_plan[:3] if str(item).strip())
            if isinstance(success_criteria, list):
                excerpt_lines.extend(str(item).strip() for item in success_criteria[:2] if str(item).strip())
        if excerpt_lines:
            context_parts.append("\n".join(excerpt_lines))

    gate_dir = project_dir / "04_gate" / f"ch{previous_chapter:03d}"
    blueprint_text = read_text(gate_dir / "chapter_blueprint.md")
    runtime_draft_text = read_text(gate_dir / "runtime_draft.md")
    if blueprint_text:
        context_parts.append("\n".join(useful_lines(blueprint_text, 8)))
    if runtime_draft_text:
        context_parts.append("\n".join(useful_lines(runtime_draft_text, 8)))

    combined = "\n".join(part for part in context_parts if part.strip())
    excerpt = useful_lines(combined, 8)
    return {
        "text": combined,
        "excerpt": excerpt,
        "next_goal": next_goal,
        "source": "runtime" if combined else "",
    }


def parse_chapter_number(text: str) -> int | None:
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else None


def parse_heading_value(text: str, labels: list[str]) -> str:
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


def find_chapter_card_path(project_dir: Path, target_chapter: int) -> Path | None:
    candidate_dirs = [
        project_dir / "01_outline",
        project_dir / "01_outline" / "chapter_cards",
        project_dir / "01_outline" / "chapters",
        project_dir / "00_memory",
        project_dir / "00_memory" / "chapter_cards",
        project_dir / "00_memory" / "plans",
        project_dir / "04_gate" / f"ch{target_chapter:03d}",
    ]
    candidate_names = {
        f"第{target_chapter:03d}章.md",
        f"第{target_chapter}章.md",
        f"ch{target_chapter:03d}.md",
        f"chapter-{target_chapter:03d}.md",
        f"chapter_{target_chapter:03d}.md",
        f"plan-{target_chapter:03d}.md",
        f"plan_{target_chapter:03d}.md",
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
                if chapter_no == target_chapter:
                    return path
    return None


def parse_chapter_card(card_text: str) -> dict[str, str]:
    return {
        "chapter_tier": parse_heading_value(card_text, ["chapter_tier", "章节等级", "本章等级"]),
        "target_word_count": parse_heading_value(card_text, ["target_word_count", "目标字数", "本章目标字数"]),
        "time_anchor": parse_heading_value(card_text, ["time_anchor", "本章时间", "时间锚点"]),
        "location_anchor": parse_heading_value(card_text, ["location_anchor", "本章地点", "地点锚点"]),
        "present_characters": parse_heading_value(card_text, ["present_characters", "在场人物"]),
        "knowledge_boundary": parse_heading_value(card_text, ["knowledge_boundary", "知情边界"]),
        "resource_state": parse_heading_value(card_text, ["resource_state", "资源状态"]),
        "open_threads": parse_heading_value(card_text, ["open_threads", "开放线索", "开放线程"]),
        "forbidden_inventions": parse_heading_value(card_text, ["forbidden_inventions", "禁止发明"]),
        "chapter_function": parse_heading_value(card_text, ["chapter_function", "本章功能"]),
        "chapter_goal": parse_heading_value(card_text, ["chapter_goal", "本章目标"]),
        "conflict_type": parse_heading_value(card_text, ["conflict_type", "本章冲突"]),
        "result_change": parse_heading_value(card_text, ["result_change", "本章结果变化"]),
        "result_type": parse_heading_value(card_text, ["result_type", "本章结果类型"]),
        "emotion_point": parse_heading_value(card_text, ["emotion_point", "本章爽点 / 情绪点", "本章爽点/情绪点"]),
        "relationship_shift": parse_heading_value(card_text, ["relationship_shift", "本章关系刷新点"]),
        "promise_progress": parse_heading_value(
            card_text,
            ["promise_progress", "本章承诺推进 / 延后说明", "本章承诺推进/延后说明"],
        ),
        "hook_type": parse_heading_value(card_text, ["hook_type", "章尾钩子类型"]),
        "hook_text": parse_heading_value(card_text, ["hook_text", "本章章尾钩子"]),
        "opening_focus": parse_heading_value(card_text, ["opening_focus", "开头先落什么"]),
        "mid_focus": parse_heading_value(card_text, ["mid_focus", "中段必须推进什么"]),
        "ending_focus": parse_heading_value(card_text, ["ending_focus", "结尾必须留下什么"]),
    }


def load_previous_card_defaults(project_dir: Path, target_chapter: int) -> dict[str, str]:
    if target_chapter <= 1:
        return {}
    previous_path = find_chapter_card_path(project_dir, target_chapter - 1)
    if not previous_path:
        return {}
    previous_text = read_text(previous_path)
    if not previous_text.strip():
        return {}
    previous_card = parse_chapter_card(previous_text)
    return {
        "chapter_tier": previous_card.get("chapter_tier", ""),
        "target_word_count": previous_card.get("target_word_count", ""),
    }


def parse_plan_milestones(plan_text: str) -> list[dict[str, object]]:
    rows = extract_markdown_table_rows(plan_text, "关键节点锚点表（写前硬校验，违反则阻断）")
    if len(rows) <= 1:
        rows = extract_markdown_table_rows(plan_text, "关键节点锚点表")

    items: list[dict[str, object]] = []
    for row in rows[1:]:
        if len(row) < 4:
            continue
        description = row[0].strip()
        earliest = parse_chapter_number(row[1])
        latest = parse_chapter_number(row[2])
        status = row[3].strip()
        if not description or has_placeholder(description):
            continue
        items.append(
            {
                "description": description,
                "earliest": earliest,
                "latest": latest,
                "status": status,
            }
        )
    return items


def detect_keyword_hits(text: str, keywords: tuple[str, ...]) -> list[str]:
    return [keyword for keyword in keywords if keyword in text]


def resolve_planning_verdict(blockers: list[str]) -> str:
    return "revise" if blockers else "pass"


def is_done_status(text: str) -> bool:
    return "已完成" in text or "✅" in text or "完成" == text.strip()


def derive_first_fix_priority(
    chapter_card: dict[str, str],
    next_goal: str,
    blockers: list[str],
    warnings: list[str],
    priority_debt: dict[str, str],
) -> str:
    if not next_goal and not chapter_card.get("chapter_function", ""):
        return "chapter_function"
    if not chapter_card.get("result_change", ""):
        return "result_change"
    if not chapter_card.get("hook_text", ""):
        return "hook_and_next_action"
    if any("voice.md" in item or "style.md" in item for item in blockers):
        return "style_voice_guardrails"
    if any("absolute" in item.lower() or "state.md" in item for item in blockers):
        return "state_anchors"
    if priority_debt.get("key", ""):
        return priority_debt["key"]
    if warnings:
        return "planning_consistency"
    return "chapter_card"


def build_planning_contract(
    target_chapter: int,
    chapter_card: dict[str, str],
    next_goal: str,
    blockers: list[str],
    warnings: list[str],
    health_digest: list[str],
    priority_debt: dict[str, str],
) -> dict[str, object]:
    blocking = "yes" if blockers else "no"
    hook_line = chapter_card.get("hook_text", "") or chapter_card.get("ending_focus", "")
    rewrite_scope = "chapter_card" if chapter_card else "state.md + planning_context"
    priority_label = priority_debt.get("label", "")
    priority_action = priority_debt.get("action", "")
    priority_source = priority_debt.get("source", "")
    first_fix_priority = derive_first_fix_priority(chapter_card, next_goal, blockers, warnings, priority_debt)
    return {
        "target_chapter": target_chapter,
        "blocking": blocking,
        "return_to": "Planner" if blockers else "",
        "rewrite_scope": rewrite_scope if blockers else "",
        "first_fix_priority": first_fix_priority if blockers or warnings or priority_label else "",
        "recheck_order": "Planner -> HookEmotion -> planning" if blockers or warnings or priority_label else "",
        "planner_contract": {
            "chapter_function": chapter_card.get("chapter_function", "") or next_goal,
            "result_change": chapter_card.get("result_change", ""),
            "hook_type": chapter_card.get("hook_type", ""),
            "chapter_tier": chapter_card.get("chapter_tier", ""),
            "target_word_count": chapter_card.get("target_word_count", ""),
            "time_anchor": chapter_card.get("time_anchor", ""),
            "location_anchor": chapter_card.get("location_anchor", ""),
            "present_characters": chapter_card.get("present_characters", ""),
            "scene_focal_character": chapter_card.get("present_characters", ""),
            "knowledge_boundary": chapter_card.get("knowledge_boundary", ""),
            "resource_state": chapter_card.get("resource_state", ""),
            "open_threads": chapter_card.get("open_threads", ""),
            "forbidden_inventions": chapter_card.get("forbidden_inventions", ""),
            "health_digest": health_digest,
            "priority_debt": priority_label,
            "priority_debt_hint": priority_action,
            "priority_debt_source": priority_source,
            "planning_verdict": resolve_planning_verdict(blockers),
        },
        "hook_emotion_contract": {
            "entry_pressure": chapter_card.get("opening_focus", "") or next_goal,
            "midpoint_pressure": chapter_card.get("mid_focus", "") or chapter_card.get("conflict_type", ""),
            "peak_moment": chapter_card.get("result_change", "") or chapter_card.get("emotion_point", ""),
            "aftershock": chapter_card.get("ending_focus", "") or hook_line,
            "hook_type": chapter_card.get("hook_type", ""),
            "hook_line_or_direction": hook_line,
            "must_resolve_first": priority_label,
            "priority_debt_hint": priority_action,
            "blocking": blocking,
            "suggested_fix": blockers[0] if blockers else (priority_action or (warnings[0] if warnings else "")),
        },
    }


def build_analysis(project_dir: Path, target_chapter: int) -> dict[str, object]:
    memory_dir = project_dir / "00_memory"
    plan_text = read_text(memory_dir / "plan.md")
    state_text = read_text(memory_dir / "state.md")
    voice_text = read_text(memory_dir / "voice.md")
    style_text = read_text(memory_dir / "style.md")
    recent_text = read_text(memory_dir / "summaries" / "recent.md")
    next_context_text = read_text(memory_dir / "retrieval" / "next_context.md")
    runtime_context = load_runtime_context(project_dir, target_chapter)
    chapter_card_path = find_chapter_card_path(project_dir, target_chapter)
    chapter_card_text = read_text(chapter_card_path) if chapter_card_path else ""
    chapter_card = parse_chapter_card(chapter_card_text) if chapter_card_text else {}
    if not chapter_card_path:
        chapter_card_defaults = load_previous_card_defaults(project_dir, target_chapter)
        for key in ("chapter_tier", "target_word_count"):
            if not chapter_card.get(key, "") and chapter_card_defaults.get(key, ""):
                chapter_card[key] = chapter_card_defaults[key]

    active_volume = extract_present_line(state_text, "- 当前卷") or extract_state_value(state_text, "当前卷")
    active_arc = extract_present_line(state_text, "- 当前弧") or extract_state_value(state_text, "当前弧")
    absolute_time = extract_present_line(state_text, "- 当前绝对时间") or extract_state_value(state_text, "当前绝对时间")
    current_place = extract_present_line(state_text, "- 当前地点") or extract_state_value(state_text, "当前地点")
    next_goal = extract_next_goal(state_text) or str(runtime_context.get("next_goal", "")).strip()
    context_text = next_context_text or str(runtime_context.get("text", "")).strip()
    due_foreshadow_ids = load_due_foreshadow_ids(project_dir, target_chapter)
    milestones = parse_plan_milestones(plan_text)
    health_digest = load_health_digest(project_dir)
    priority_debt = derive_priority_debt(health_digest)

    overdue_milestones = [
        str(item["description"])
        for item in milestones
        if item["latest"] is not None
        and int(item["latest"]) < target_chapter
        and not is_done_status(str(item["status"]))
    ]
    due_milestones = [
        str(item["description"])
        for item in milestones
        if item["earliest"] is not None
        and item["latest"] is not None
        and int(item["earliest"]) <= target_chapter <= int(item["latest"])
        and not is_done_status(str(item["status"]))
    ]

    narrative_anchor = chapter_card.get("chapter_function", "") or next_goal or "\n".join(useful_lines(context_text, 4))
    combined_planning_text = "\n".join(
        part for part in (chapter_card_text, next_goal, context_text, recent_text) if part.strip()
    )
    upgrade_hits = detect_keyword_hits(combined_planning_text, UPGRADE_KEYWORDS)
    action_hits = detect_keyword_hits(combined_planning_text, ACTION_KEYWORDS)
    hook_hits = detect_keyword_hits(combined_planning_text, HOOK_KEYWORDS)

    blockers: list[str] = []
    warnings: list[str] = []

    if not useful_lines(plan_text, 4):
        blockers.append("缺少可用的 `plan.md` 主线计划，无法确认本章是否还在大纲轨道内。")
    if not next_goal and not chapter_card.get("chapter_goal", "") and not chapter_card.get("chapter_function", ""):
        blockers.append("缺少显式章卡或 `state.md` 下章预告，本章存在理由没有落到文字。")
    if not chapter_card.get("chapter_tier", ""):
        warnings.append("章卡缺少 `chapter_tier`，后续字数门禁无法判断这是常规章还是高潮章。")
    if not chapter_card.get("target_word_count", ""):
        warnings.append("章卡缺少 `target_word_count`，后续字数门禁无法校验目标字数。")
    if not active_arc:
        blockers.append("`state.md` 缺少“当前弧”，无法判断本章推进的是哪条弧线。")
    if not absolute_time:
        blockers.append("`state.md` 缺少“当前绝对时间”，章节因果锚点不稳。")
    if not current_place:
        blockers.append("`state.md` 缺少“当前地点”，起章站位不清。")
    if not useful_lines(voice_text or style_text, 5):
        blockers.append("缺少 `voice.md` / `style.md` 的单书声音约束，风格一致性无法预审。")
    if chapter_card_path and not chapter_card.get("result_change", ""):
        blockers.append("显式章卡存在，但缺少“本章结果变化”，正文容易写成无效推进。")
    if chapter_card_path and not chapter_card.get("hook_text", ""):
        blockers.append("显式章卡存在，但缺少“本章章尾钩子”，不允许带空钩子开写。")

    if not active_volume:
        warnings.append("`state.md` 未识别到“当前卷”，卷级节奏容易失焦。")
    if not useful_lines(recent_text, 3):
        warnings.append("缺少 recent 摘要，近章重复风险会升高。")
    if not context_text:
        warnings.append("尚未生成 `00_memory/retrieval/next_context.md`，建议先跑 context 再定稿本章规划。")
    if not chapter_card_path:
        warnings.append("未找到显式章卡，当前预审主要基于 `state.md` / planning context 推断。")
    if not upgrade_hits:
        warnings.append("未识别到明确结果升级词，本章可能只是延长旧冲突而没有产生新结果。")
    if not action_hits:
        warnings.append("未识别到下一章行动动词，章尾钩子可能只是更抓人，但没有改变下一章动作。")
    if not hook_hits:
        warnings.append("未识别到明显钩子信号，章尾可能缺少强制追读牵引。")
    if due_foreshadow_ids and not any(item in combined_planning_text for item in due_foreshadow_ids):
        suffix = " 等" if len(due_foreshadow_ids) > 6 else ""
        warnings.append(
            "存在到期伏笔但当前规划文字未提及："
            + "、".join(due_foreshadow_ids[:6])
            + suffix
        )
    if overdue_milestones:
        suffix = " 等" if len(overdue_milestones) > 4 else ""
        warnings.append(
            "存在已经超期但未完成的关键节点："
            + "、".join(overdue_milestones[:4])
            + suffix
        )

    status = "pass"
    if blockers:
        status = "fail"
    elif warnings:
        status = "warn"

    contract = build_planning_contract(
        target_chapter,
        chapter_card,
        next_goal,
        blockers,
        warnings,
        health_digest,
        priority_debt,
    )

    return {
        "target_chapter": target_chapter,
        "status": status,
        "planning_verdict": resolve_planning_verdict(blockers),
        "active_volume": active_volume or "未设定",
        "active_arc": active_arc or "未设定",
        "absolute_time": absolute_time or "未设定",
        "current_place": current_place or "未设定",
        "next_goal": next_goal or "未设定",
        "chapter_card_path": chapter_card_path.as_posix() if chapter_card_path else "",
        "chapter_card": chapter_card,
        "chapter_reason": narrative_anchor or "未识别，请人工补全本章存在理由。",
        "delete_loss": (
            "会损失当前弧推进 / 既有伏笔回收 / 关键节点窗口。"
            if due_foreshadow_ids or due_milestones or overdue_milestones
            else "当前未识别到硬性窗口，需人工确认本章删减损失。"
        ),
        "new_progress": chapter_card.get("result_change", "") or ("、".join(upgrade_hits[:4]) if upgrade_hits else "未识别到明确升级点"),
        "hook_upgrade": chapter_card.get("hook_text", "") or ("、".join(hook_hits[:4]) if hook_hits else "未识别到强钩子信号"),
        "action_shift": chapter_card.get("ending_focus", "") or ("、".join(action_hits[:4]) if action_hits else "未识别到下一章行动变化"),
        "due_foreshadow_ids": due_foreshadow_ids,
        "due_milestones": due_milestones,
        "overdue_milestones": overdue_milestones,
        "health_digest": health_digest,
        "priority_debt": priority_debt.get("label", ""),
        "priority_debt_key": priority_debt.get("key", ""),
        "priority_debt_reason": priority_debt.get("reason", ""),
        "priority_debt_hint": priority_debt.get("action", ""),
        "priority_debt_source": priority_debt.get("source", ""),
        "warnings": warnings,
        "warning_count": len(warnings),
        "blockers": blockers,
        "blocker_count": len(blockers),
        "blocking": contract["blocking"],
        "return_to": contract["return_to"],
        "rewrite_scope": contract["rewrite_scope"],
        "first_fix_priority": contract["first_fix_priority"],
        "recheck_order": contract["recheck_order"],
        "planner_contract": contract["planner_contract"],
        "hook_emotion_contract": contract["hook_emotion_contract"],
        "context_excerpt": useful_lines(context_text, 8),
        "voice_excerpt": useful_lines(voice_text or style_text, 8),
        "plan_excerpt": useful_lines(plan_text, 8),
        "chapter_card_excerpt": useful_lines(chapter_card_text, 12),
    }


def render_markdown(project_dir: Path, analysis: dict[str, object]) -> str:
    target_chapter = int(analysis["target_chapter"])
    lines = [
        f"# 第{target_chapter:03d}章章节规划预审",
        "",
        f"- 生成时间：`{datetime.now().isoformat(timespec='seconds')}`",
        f"- 项目：`{project_dir.as_posix()}`",
        f"- 预审结论：`{str(analysis['planning_verdict']).upper()}`",
        f"- 流水线状态：`{str(analysis['status']).upper()}`",
        f"- 显式章卡：`{analysis['chapter_card_path'] or '未找到'}`",
        "",
        "## 1. 本章存在理由",
        f"- `chapter_tier`：{analysis['chapter_card'].get('chapter_tier', '') or '未填写'}",
        f"- `target_word_count`：{analysis['chapter_card'].get('target_word_count', '') or '未填写'}",
        f"- 本章功能：{analysis['chapter_card'].get('chapter_function', '') or analysis['chapter_reason']}",
        f"- 如果删掉本章，会损失什么：{analysis['delete_loss']}",
        f"- 本章相较最近 3-5 章的新推进：{analysis['new_progress']}",
        "",
        "## 2. 结果升级",
        f"- 本章结果类型：{analysis['chapter_card'].get('result_type', '') or analysis['new_progress']}",
        f"- 为什么这次结果不重复上一章或最近几章：{analysis['action_shift']}",
        f"- 本章是否有明确升级点：{'是' if analysis['new_progress'] != '未识别到明确升级点' else '否'}",
        "",
        "## 3. 钩子与下一章行动",
        f"- 本章章尾钩子类型：{analysis['chapter_card'].get('hook_type', '') or analysis['hook_upgrade']}",
        f"- 这个钩子会如何改变下一章行动：{analysis['chapter_card'].get('hook_text', '') or analysis['action_shift']}",
        "",
        "## 4. 因果与连续性",
        f"- 当前卷 / 当前弧：{analysis['active_volume']} / {analysis['active_arc']}",
        f"- 当前绝对时间 / 当前地点：{analysis['absolute_time']} / {analysis['current_place']}",
        f"- 到期伏笔：{'、'.join(analysis['due_foreshadow_ids']) if analysis['due_foreshadow_ids'] else '无'}",
        f"- 本章窗口内关键节点：{'、'.join(analysis['due_milestones']) if analysis['due_milestones'] else '无'}",
        f"- 已超期关键节点：{'、'.join(analysis['overdue_milestones']) if analysis['overdue_milestones'] else '无'}",
        "",
        "## 5. 预审结论",
        f"- 结论：{analysis['planning_verdict']}",
        f"- 阻断项数：{analysis['blocker_count']}",
        f"- 预警项数：{analysis['warning_count']}",
        "",
        "### 阻断项",
        render_list(list(analysis["blockers"]), "无阻断项"),
        "",
        "### 预警项",
        render_list(list(analysis["warnings"]), "无预警项"),
        "",
        "### 计划摘录",
        render_list(list(analysis["plan_excerpt"]), "无可用计划摘录"),
        "",
        "### 章卡摘录",
        render_list(list(analysis["chapter_card_excerpt"]), "无显式章卡摘录"),
        "",
        "### 上下文摘录",
        render_list(list(analysis["context_excerpt"]), "无可用 planning context 摘录"),
        "",
        "### 书级声音摘录",
        render_list(list(analysis["voice_excerpt"]), "无可用声音摘录"),
        "",
    ]
    return "\n".join(lines)


def render_markdown_v2(project_dir: Path, analysis: dict[str, object]) -> str:
    target_chapter = int(analysis["target_chapter"])
    planner_contract = analysis.get("planner_contract", {})
    hook_contract = analysis.get("hook_emotion_contract", {})
    lines = [
        f"# Chapter {target_chapter:03d} Planning Review",
        "",
        f"- generated_at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- project: `{project_dir.as_posix()}`",
        f"- planning_verdict: `{str(analysis['planning_verdict']).upper()}`",
        f"- status: `{str(analysis['status']).upper()}`",
        f"- chapter_card_path: `{analysis['chapter_card_path'] or 'missing'}`",
        "",
        "## Planner Contract",
        f"- chapter_function: {planner_contract.get('chapter_function', '') or analysis['chapter_reason']}",
        f"- result_change: {planner_contract.get('result_change', '') or analysis['new_progress']}",
        f"- hook_type: {planner_contract.get('hook_type', '') or analysis['hook_upgrade']}",
        f"- chapter_tier: {planner_contract.get('chapter_tier', '') or 'missing'}",
        f"- target_word_count: {planner_contract.get('target_word_count', '') or 'missing'}",
        f"- time_anchor: {planner_contract.get('time_anchor', '') or analysis['absolute_time']}",
        f"- location_anchor: {planner_contract.get('location_anchor', '') or analysis['current_place']}",
        f"- present_characters: {planner_contract.get('present_characters', '') or 'missing'}",
        f"- knowledge_boundary: {planner_contract.get('knowledge_boundary', '') or 'missing'}",
        f"- resource_state: {planner_contract.get('resource_state', '') or 'missing'}",
        f"- open_threads: {planner_contract.get('open_threads', '') or 'missing'}",
        f"- priority_debt: {planner_contract.get('priority_debt', '') or analysis['priority_debt'] or 'none'}",
        f"- priority_debt_hint: {planner_contract.get('priority_debt_hint', '') or analysis['priority_debt_hint'] or 'none'}",
        f"- priority_debt_source: {planner_contract.get('priority_debt_source', '') or analysis['priority_debt_source'] or 'none'}",
        "",
        "## HookEmotion Contract",
        f"- entry_pressure: {hook_contract.get('entry_pressure', '') or 'missing'}",
        f"- midpoint_pressure: {hook_contract.get('midpoint_pressure', '') or 'missing'}",
        f"- peak_moment: {hook_contract.get('peak_moment', '') or 'missing'}",
        f"- aftershock: {hook_contract.get('aftershock', '') or 'missing'}",
        f"- hook_line_or_direction: {hook_contract.get('hook_line_or_direction', '') or 'missing'}",
        f"- must_resolve_first: {hook_contract.get('must_resolve_first', '') or analysis['priority_debt'] or 'none'}",
        f"- priority_debt_hint: {hook_contract.get('priority_debt_hint', '') or analysis['priority_debt_hint'] or 'none'}",
        "",
        "## Continuity Anchors",
        f"- active_volume: {analysis['active_volume']}",
        f"- active_arc: {analysis['active_arc']}",
        f"- absolute_time: {analysis['absolute_time']}",
        f"- current_place: {analysis['current_place']}",
        f"- due_foreshadow_ids: {', '.join(analysis['due_foreshadow_ids']) if analysis['due_foreshadow_ids'] else 'none'}",
        f"- due_milestones: {', '.join(analysis['due_milestones']) if analysis['due_milestones'] else 'none'}",
        f"- overdue_milestones: {', '.join(analysis['overdue_milestones']) if analysis['overdue_milestones'] else 'none'}",
        "",
        "## Contract Gate",
        f"- blocking: {analysis['blocking']}",
        f"- return_to: {analysis['return_to'] or 'n/a'}",
        f"- rewrite_scope: {analysis['rewrite_scope'] or 'n/a'}",
        f"- first_fix_priority: {analysis['first_fix_priority'] or 'n/a'}",
        f"- recheck_order: {analysis['recheck_order'] or 'n/a'}",
        f"- blocker_count: {analysis['blocker_count']}",
        f"- warning_count: {analysis['warning_count']}",
        "",
        "## Blockers",
        render_list(list(analysis["blockers"]), "none"),
        "",
        "## Warnings",
        render_list(list(analysis["warnings"]), "none"),
        "",
        "## Health Digest",
        render_list(list(analysis["health_digest"]), "none"),
        "",
        "## Plan Excerpt",
        render_list(list(analysis["plan_excerpt"]), "none"),
        "",
        "## Chapter Card Excerpt",
        render_list(list(analysis["chapter_card_excerpt"]), "none"),
        "",
        "## Context Excerpt",
        render_list(list(analysis["context_excerpt"]), "none"),
        "",
        "## Voice Excerpt",
        render_list(list(analysis["voice_excerpt"]), "none"),
        "",
    ]
    return "\n".join(lines)


def write_outputs(
    project_dir: Path,
    analysis: dict[str, object],
    output_path: Path | None,
    dry_run: bool,
) -> tuple[Path, Path]:
    target_chapter = int(analysis["target_chapter"])
    gate_dir = project_dir / "04_gate" / f"ch{target_chapter:03d}"
    report_path = output_path or gate_dir / "planning_review.md"
    result_path = gate_dir / "planning_review.json"
    if not dry_run:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render_markdown_v2(project_dir, analysis), encoding="utf-8")
        result_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_path, result_path


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    project_dir = Path(args.project).resolve()
    state_text = read_text(project_dir / "00_memory" / "state.md")
    target_chapter = detect_target_chapter(state_text, args.chapter, args.target_chapter)
    output_path = Path(args.output).resolve() if args.output else None
    analysis = build_analysis(project_dir, target_chapter)
    report_path, result_path = write_outputs(project_dir, analysis, output_path, args.dry_run)

    payload = {
        "project": project_dir.as_posix(),
        "target_chapter": target_chapter,
        "status": analysis["status"],
        "planning_verdict": analysis["planning_verdict"],
        "blocking": analysis["blocking"],
        "return_to": analysis["return_to"],
        "rewrite_scope": analysis["rewrite_scope"],
        "first_fix_priority": analysis["first_fix_priority"],
        "recheck_order": analysis["recheck_order"],
        "health_digest": analysis["health_digest"],
        "priority_debt": analysis["priority_debt"],
        "priority_debt_key": analysis["priority_debt_key"],
        "priority_debt_reason": analysis["priority_debt_reason"],
        "priority_debt_hint": analysis["priority_debt_hint"],
        "priority_debt_source": analysis["priority_debt_source"],
        "planner_contract": analysis["planner_contract"],
        "hook_emotion_contract": analysis["hook_emotion_contract"],
        "warnings": analysis["warnings"],
        "warning_count": analysis["warning_count"],
        "blockers": analysis["blockers"],
        "blocker_count": analysis["blocker_count"],
        "report_paths": {
            "markdown": report_path.as_posix(),
            "json": result_path.as_posix(),
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"target_chapter={target_chapter}")
        print(f"status={analysis['status']}")
        print(f"planning_verdict={analysis['planning_verdict']}")
        print(f"priority_debt={analysis['priority_debt'] or 'none'}")
        print(f"warning_count={analysis['warning_count']}")
        print(f"blocker_count={analysis['blocker_count']}")
        print(f"report={report_path.as_posix()}")
    return 1 if analysis["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

