#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from aggregation_utils import configure_utf8_stdio, write_markdown_json_reports
from novel_utils import (
    count_total_chapter_chars,
    derive_plan_target_words,
    detect_current_chapter,
    detect_latest_chapter_file,
    detect_target_chapter,
    extract_markdown_table_rows,
    extract_next_goal,
    extract_state_value,
    extract_summary_field,
    find_chapter_card_path,
    has_placeholder,
    load_due_foreshadow_ids,
    load_health_digest,
    load_json,
    load_previous_card_defaults,
    parse_chapter_card,
    parse_plan_volumes,
    read_text,
    split_summary_entries,
    useful_lines,
)

# Shell-plus-readiness role: this file keeps the public open entry stable.
# When chapter targeting is requested it now builds planning review and next-context readiness directly; otherwise it runs launch-readiness checks.
REQUIRED_LAUNCH_FILES = [
    "00_memory/plan.md",
    "00_memory/state.md",
    "00_memory/style.md",
    "00_memory/voice.md",
    "00_memory/characters.md",
]
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
HIGH_RISK_PROGRESS_KEYWORDS = (
    "掉马",
    "结盟",
    "联盟",
    "确认",
    "揭露",
    "揭开",
    "公开站队",
    "摊牌",
    "彻底知道",
    "正式坐实",
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
        description="Open-book entry: launch-readiness scan by default, chapter planning/context when --chapter or --target-chapter is set."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument(
        "--chapter",
        type=int,
        help="Existing drafted current chapter number. Open-book planning/context targets the next chapter by default.",
    )
    parser.add_argument("--target-chapter", type=int, help="Explicit target chapter number")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    return parser.parse_args()


def parse_chapter_number(text: str) -> int | None:
    import re

    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else None


def detect_keyword_hits(text: str, keywords: tuple[str, ...]) -> list[str]:
    return [keyword for keyword in keywords if keyword in text]


def is_done_status(text: str) -> bool:
    return "已完成" in text or "✅" in text or "完成" == text.strip()


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
    rewrite_scope = "chapter_card" if chapter_card else "state.md + open readiness"
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
            "message_flow": chapter_card.get("message_flow", ""),
            "arrival_timing": chapter_card.get("arrival_timing", ""),
            "who_knows_now": chapter_card.get("who_knows_now", ""),
            "who_cannot_know_yet": chapter_card.get("who_cannot_know_yet", ""),
            "travel_time_floor": chapter_card.get("travel_time_floor", ""),
            "resource_state": chapter_card.get("resource_state", ""),
            "progress_floor": chapter_card.get("progress_floor", ""),
            "progress_ceiling": chapter_card.get("progress_ceiling", ""),
            "must_not_payoff_yet": chapter_card.get("must_not_payoff_yet", ""),
            "allowed_change_scope": chapter_card.get("allowed_change_scope", ""),
            "open_threads": chapter_card.get("open_threads", ""),
            "forbidden_inventions": chapter_card.get("forbidden_inventions", ""),
            "health_digest": health_digest,
            "priority_debt": priority_label,
            "priority_debt_hint": priority_action,
            "priority_debt_source": priority_source,
            "planning_verdict": "revise" if blockers else "pass",
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


def first_nonempty_lines(text: str, limit: int) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()][:limit]


def collect_latest_chapter_excerpt(project_dir: Path) -> str:
    _, latest_path = detect_latest_chapter_file(project_dir)
    if latest_path is None:
        return ""
    return "\n".join(first_nonempty_lines(read_text(latest_path), 16))


def derive_volume_blueprint_lines(volume_blueprint_text: str, plan_text: str) -> list[str]:
    lines = useful_lines(volume_blueprint_text, 10)
    if lines:
        return lines
    volumes = parse_plan_volumes(plan_text)
    if not volumes:
        return []
    return [
        f"- {str(item.get('label', '')).strip() or f'第{index + 1}卷'}：{str(item.get('name', '')).strip()}（第{int(item.get('chapterStart', 0) or 0)}~{int(item.get('chapterEnd', 0) or 0)}章）"
        for index, item in enumerate(volumes)
    ]


def parse_due_foreshadow_details(memory_dir: Path, target_chapter: int) -> list[dict[str, str]]:
    import re

    foreshadow_text = read_text(memory_dir / "foreshadowing.md")
    rows = extract_markdown_table_rows(foreshadow_text, "活跃伏笔")
    if len(rows) <= 1:
        rows = extract_markdown_table_rows(foreshadow_text, "📌 未回收伏笔(Pending)")

    details: list[dict[str, str]] = []
    for row in rows[1:]:
        if len(row) < 9:
            continue
        due_text = row[6].strip()
        chapter_match = re.search(r"(\d+)", due_text)
        if not chapter_match or int(chapter_match.group(1)) > target_chapter:
            continue
        status = row[8].strip()
        if any(flag in status for flag in ("已回收", "已废弃", "宸插洖鏀?", "宸插簾寮?")):
            continue
        details.append(
            {
                "id": row[0].strip(),
                "content": row[2].strip(),
                "who_knows": row[3].strip(),
                "trigger": row[4].strip(),
                "due_chapter": due_text,
                "status": status or "待回收",
            }
        )
    return details


def parse_schema_due_foreshadows(project_dir: Path, target_chapter: int) -> list[dict[str, str]]:
    payload = load_json(project_dir / "00_memory" / "schema" / "foreshadowing.json")
    threads = payload.get("threads", [])
    if not isinstance(threads, list):
        return []

    details: list[dict[str, str]] = []
    for item in threads:
        if not isinstance(item, dict):
            continue
        due_chapter = item.get("due_chapter")
        if not isinstance(due_chapter, int) or due_chapter > target_chapter:
            continue
        status = str(item.get("status", "")).strip().lower()
        if status in {"resolved", "closed", "已回收", "废弃"}:
            continue
        details.append(
            {
                "id": str(item.get("id", "")).strip(),
                "content": str(item.get("content", "")).strip(),
                "who_knows": str(item.get("who_knows", "")).strip(),
                "trigger": str(item.get("trigger_condition", "")).strip(),
                "due_chapter": f"第{due_chapter}章",
                "status": str(item.get("status", "")).strip() or "active",
            }
        )
    return details


def parse_active_promises(memory_dir: Path, target_chapter: int) -> list[dict[str, str]]:
    import re

    payoff_text = read_text(memory_dir / "payoff_board.md")
    rows = extract_markdown_table_rows(payoff_text, "活跃承诺")
    if len(rows) <= 1:
        rows = extract_markdown_table_rows(payoff_text, "娲昏穬鎵胯")

    active: list[dict[str, str]] = []
    for row in rows[1:]:
        if len(row) < 8 or not row[0].strip():
            continue
        expected_window = row[4].strip()
        window_match = re.search(r"(\d+)", expected_window)
        due_soon = bool(window_match and int(window_match.group(1)) <= target_chapter + 3)
        pressure = row[6].strip()
        status = row[5].strip()
        if any(flag in status for flag in ("已兑现", "已废弃", "宸插厬鐜?", "宸插簾寮?")):
            continue
        if due_soon or "🔴" in pressure or "馃敶" in pressure or "延迟" in status or "寤惰繜" in status or "待兑现" in status:
            active.append(
                {
                    "id": row[0].strip(),
                    "type": row[1].strip(),
                    "content": row[2].strip(),
                    "window": expected_window or "未填写",
                    "status": status or "待兑现",
                    "pressure": pressure or "未填写",
                }
            )
    return active


def parse_character_hotspots(memory_dir: Path, target_chapter: int) -> list[dict[str, str]]:
    import re

    arc_text = read_text(memory_dir / "character_arcs.md")
    rows = extract_markdown_table_rows(arc_text, "核心角色弧表")
    hotspots: list[dict[str, str]] = []
    for row in rows[1:]:
        if len(row) < 8:
            continue
        next_window = row[6].strip()
        risk = row[7].strip()
        chapter_numbers = [int(match) for match in re.findall(r"(\d+)", next_window)]
        due_now = any(abs(number - target_chapter) <= 3 for number in chapter_numbers)
        if risk or due_now:
            hotspots.append(
                {
                    "character": row[0].strip(),
                    "stage": row[2].strip(),
                    "goal": row[3].strip(),
                    "next_window": next_window or "未填写",
                    "risk": risk or "无显式风险",
                }
            )
    if hotspots:
        return hotspots[:6]

    fallback: list[dict[str, str]] = []
    for row in rows[1:4]:
        if len(row) < 8 or not row[0].strip():
            continue
        fallback.append(
            {
                "character": row[0].strip(),
                "stage": row[2].strip(),
                "goal": row[3].strip(),
                "next_window": row[6].strip() or "未填写",
                "risk": row[7].strip() or "未填写",
            }
        )
    return fallback


def parse_schema_character_hotspots(project_dir: Path, target_chapter: int) -> list[dict[str, str]]:
    import re

    payload = load_json(project_dir / "00_memory" / "schema" / "character_arcs.json")
    arcs = payload.get("arcs", [])
    if not isinstance(arcs, list):
        return []

    hotspots: list[dict[str, str]] = []
    for item in arcs:
        if not isinstance(item, dict):
            continue
        next_window = str(item.get("nextWindow", "")).strip()
        risk = str(item.get("risk", "")).strip()
        chapter_numbers = [int(match) for match in re.findall(r"(\d+)", next_window)]
        due_now = any(abs(number - target_chapter) <= 3 for number in chapter_numbers)
        if risk or due_now:
            hotspots.append(
                {
                    "character": str(item.get("character", "")).strip(),
                    "stage": str(item.get("stage", "")).strip(),
                    "goal": str(item.get("goal", "")).strip(),
                    "next_window": next_window or "未填写",
                    "risk": risk or "无显式风险",
                }
            )
    if hotspots:
        return hotspots[:6]

    fallback: list[dict[str, str]] = []
    for item in arcs[:4]:
        if not isinstance(item, dict):
            continue
        fallback.append(
            {
                "character": str(item.get("character", "")).strip(),
                "stage": str(item.get("stage", "")).strip(),
                "goal": str(item.get("goal", "")).strip(),
                "next_window": str(item.get("nextWindow", "")).strip() or "未填写",
                "risk": str(item.get("risk", "")).strip() or "未填写",
            }
        )
    return fallback


def render_summary_snapshot(entries: list[dict[str, str]], limit: int) -> list[str]:
    lines: list[str] = []
    for entry in entries[-limit:]:
        chapter = entry.get("chapter", "") or "?"
        title = entry.get("title", "") or "未命名"
        core_event = extract_summary_field(entry["body"], "核心事件") or title
        hook = extract_summary_field(entry["body"], "启下") or extract_summary_field(entry["body"], "伏笔")
        try:
            chapter_label = f"第{int(chapter):03d}章"
        except ValueError:
            chapter_label = f"第{chapter}章"
        lines.append(f"{chapter_label}《{title}》：{core_event}")
        if hook:
            lines.append(f"  启下：{hook}")
    return lines


def parse_mid_archive(memory_dir: Path) -> list[str]:
    mid_path = memory_dir / "summaries" / "mid.md"
    if not mid_path.exists():
        return []
    return useful_lines(read_text(mid_path), 8)


def load_runtime_payload(project_dir: Path) -> dict[str, object]:
    payload = load_json(project_dir / "00_memory" / "retrieval" / "leadwriter_runtime_payload.json")
    return payload if payload else {}


def extract_runtime_context(runtime_payload: dict[str, object]) -> dict[str, object]:
    context = runtime_payload.get("context", {})
    return context if isinstance(context, dict) else {}


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


def build_context_payload(project_dir: Path, target_chapter: int) -> dict[str, object]:
    memory_dir = project_dir / "00_memory"
    reports_dir = project_dir / "05_reports"
    plan_text = read_text(memory_dir / "plan.md")
    state_text = read_text(memory_dir / "state.md")
    arc_text = read_text(memory_dir / "arc_progress.md")
    findings_text = read_text(memory_dir / "findings.md")
    recent_text = read_text(memory_dir / "summaries" / "recent.md")
    voice_text = read_text(memory_dir / "voice.md")
    style_text = read_text(memory_dir / "style.md")
    volume_blueprint_text = read_text(project_dir / "01_outline" / "volume_blueprint.md")
    runtime_payload = load_runtime_payload(project_dir)
    runtime_context = extract_runtime_context(runtime_payload)

    active_volume = extract_state_value(state_text, "当前卷")
    active_arc = extract_state_value(state_text, "当前弧")
    current_place = extract_state_value(state_text, "当前地点")
    next_goal = extract_next_goal(state_text)
    active_volume = active_volume or str(runtime_context.get("active_volume", "")).strip()
    active_arc = active_arc or str(runtime_context.get("active_arc", "")).strip()
    current_place = current_place or str(runtime_context.get("current_place", "")).strip()
    next_goal = next_goal or str(runtime_context.get("next_goal", "")).strip()
    due_ids = load_due_foreshadow_ids(project_dir, target_chapter)
    due_foreshadows = parse_due_foreshadow_details(memory_dir, target_chapter)
    if not due_foreshadows:
        due_foreshadows = parse_schema_due_foreshadows(project_dir, target_chapter)
    if not due_ids and due_foreshadows:
        due_ids = [str(item.get("id", "")).strip() for item in due_foreshadows if str(item.get("id", "")).strip()]
    active_promises = parse_active_promises(memory_dir, target_chapter)
    character_hotspots = parse_character_hotspots(memory_dir, target_chapter)
    if not character_hotspots:
        character_hotspots = parse_schema_character_hotspots(project_dir, target_chapter)
    repeat_report = load_json(reports_dir / "repeat_report.json")
    recent_entries = split_summary_entries(recent_text)
    health_digest = load_health_digest(project_dir)
    output_path = project_dir / "00_memory" / "retrieval" / "next_context.md"

    payload = {
        "script": "open_book.py#context",
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "chapter": target_chapter,
        "output": output_path.as_posix(),
        "output_json": output_path.with_suffix(".json").as_posix(),
        "active_volume": active_volume or "未识别",
        "active_arc": active_arc or "未识别",
        "current_place": current_place or "未识别",
        "next_goal": next_goal or "待明确",
        "total_effective_words": count_total_chapter_chars(project_dir),
        "plan_lines": useful_lines(plan_text, 8),
        "volume_blueprint_lines": derive_volume_blueprint_lines(volume_blueprint_text, plan_text),
        "state_lines": useful_lines(state_text, 12),
        "arc_lines": useful_lines(arc_text, 10),
        "finding_lines": useful_lines(findings_text, 8),
        "recent_snapshot": render_summary_snapshot(recent_entries, 3),
        "mid_snapshot": parse_mid_archive(memory_dir),
        "voice_lines": useful_lines(voice_text or style_text, 10),
        "due_foreshadow_ids": due_ids,
        "due_foreshadows": due_foreshadows,
        "active_promises": active_promises,
        "character_hotspots": character_hotspots,
        "repeat_warnings": [str(item) for item in repeat_report.get("warnings", [])[:4]],
        "health_digest": health_digest,
        "latest_excerpt": collect_latest_chapter_excerpt(project_dir),
        "warnings": [],
    }

    warnings = payload["warnings"]
    if not payload["plan_lines"]:
        warnings.append("缺少 plan.md 主线摘要，深记忆检索将失去全书主线锚。")
    if not payload["volume_blueprint_lines"]:
        warnings.append("缺少 volume_blueprint.md，卷级目标和收束节点无法前置压入上下文。")
    if not payload["character_hotspots"]:
        warnings.append("未识别到角色弧热点，人物推进提醒会偏弱。")
    if not payload["active_promises"] and target_chapter >= 10:
        warnings.append("当前未识别到高压承诺，可能是 payoff_board 没同步，而不是真的没有债务。")
    if not payload["latest_excerpt"]:
        warnings.append("当前没有正文章节，上一章摘录将为空。")
    if due_ids and not due_foreshadows:
        warnings.append("当前未识别到到期伏笔详情。")
    if not payload["health_digest"] and not runtime_payload and not payload["repeat_warnings"]:
        warnings.append("当前未收到风险摘要，建议先运行 chase check 或 dashboard 生成总控摘要。")
    payload["warning_count"] = len(warnings)
    payload["status"] = "warn" if warnings else "pass"
    payload["report_paths"] = {
        "markdown": output_path.as_posix(),
        "json": output_path.with_suffix(".json").as_posix(),
    }
    payload["returncode"] = 0
    return payload


def build_planning_payload(project_dir: Path, target_chapter: int) -> dict[str, object]:
    state_text = read_text(project_dir / "00_memory" / "state.md")
    plan_text = read_text(project_dir / "00_memory" / "plan.md")
    voice_text = read_text(project_dir / "00_memory" / "voice.md")
    style_text = read_text(project_dir / "00_memory" / "style.md")
    recent_text = read_text(project_dir / "00_memory" / "summaries" / "recent.md")
    next_context_text = read_text(project_dir / "00_memory" / "retrieval" / "next_context.md")
    runtime_context = load_runtime_context(project_dir, target_chapter)
    chapter_card_path = find_chapter_card_path(project_dir, target_chapter)
    chapter_card_text = read_text(chapter_card_path) if chapter_card_path else ""
    chapter_card = parse_chapter_card(chapter_card_text) if chapter_card_text else {}
    if not chapter_card_path:
        chapter_card_defaults = load_previous_card_defaults(project_dir, target_chapter)
        for key in ("chapter_tier", "target_word_count"):
            if not chapter_card.get(key, "") and chapter_card_defaults.get(key, ""):
                chapter_card[key] = chapter_card_defaults[key]

    active_volume = extract_state_value(state_text, "当前卷")
    active_arc = extract_state_value(state_text, "当前弧")
    absolute_time = extract_state_value(state_text, "当前绝对时间")
    current_place = extract_state_value(state_text, "当前地点")
    next_goal = extract_next_goal(state_text) or str(runtime_context.get("next_goal", "")).strip()
    context_text = next_context_text or str(runtime_context.get("text", "")).strip()
    due_foreshadow_ids = load_due_foreshadow_ids(project_dir, target_chapter)
    milestones = parse_plan_milestones(plan_text)
    health_digest = load_health_digest(project_dir)
    priority_debt = derive_priority_debt(health_digest)

    overdue_milestones = [
        str(item["description"])
        for item in milestones
        if item["latest"] is not None and int(item["latest"]) < target_chapter and not is_done_status(str(item["status"]))
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
    combined_planning_text = "\n".join(part for part in (chapter_card_text, next_goal, context_text, recent_text) if part.strip())
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
    if chapter_card_path and not chapter_card.get("message_flow", ""):
        blockers.append("显式章卡存在，但缺少“消息传播链”，无法判断消息是谁发出、经谁送、如何扩散。")
    if chapter_card_path and not chapter_card.get("arrival_timing", ""):
        blockers.append("显式章卡存在，但缺少“最早送达时间”，无法预审消息先后与时序压缩。")
    if chapter_card_path and not chapter_card.get("who_knows_now", ""):
        blockers.append("显式章卡存在，但缺少“谁现在能知道”，知情边界仍然是空的。")
    if chapter_card_path and not chapter_card.get("who_cannot_know_yet", ""):
        blockers.append("显式章卡存在，但缺少“谁按理还不能知道”，无法拦住越界知情。")
    if chapter_card_path and not chapter_card.get("travel_time_floor", ""):
        warnings.append("显式章卡存在，但缺少“路程至少多久”，跨地行动仍可能被一句话压缩。")

    progress_text = " ".join(
        [
            chapter_card.get("result_change", ""),
            chapter_card.get("hook_text", ""),
            chapter_card.get("promise_progress", ""),
            chapter_card.get("chapter_goal", ""),
        ]
    )
    high_risk_progress = any(keyword in progress_text for keyword in HIGH_RISK_PROGRESS_KEYWORDS)
    if chapter_card_path and not chapter_card.get("progress_ceiling", ""):
        if high_risk_progress:
            blockers.append("显式章卡存在，且本章存在高风险推进，但缺少“本章推进上限”，无法拦住提前兑现或推进过线。")
        else:
            warnings.append("显式章卡存在，但缺少“本章推进上限”，本章容易把试探写成坐实、把半推进写成全兑现。")
    if chapter_card_path and not chapter_card.get("must_not_payoff_yet", ""):
        warnings.append("显式章卡存在，但缺少“本章不能提前兑现”，后续章的重要结果仍可能被本章提前写穿。")
    if chapter_card_path and not chapter_card.get("allowed_change_scope", ""):
        warnings.append("显式章卡存在，但缺少“本章允许变化范围”，关系/局面/认知变化层级容易写过线。")
    if chapter_card.get("progress_ceiling", "") and chapter_card.get("result_change", ""):
        contradiction_pairs = (
            ("不能确认", "确认"),
            ("不能坐实", "坐实"),
            ("不能结盟", "结盟"),
            ("不能掉马", "掉马"),
            ("不能揭露", "揭露"),
            ("不能摊牌", "摊牌"),
        )
        ceiling = chapter_card.get("progress_ceiling", "")
        result_change = chapter_card.get("result_change", "")
        for ceiling_token, result_token in contradiction_pairs:
            if ceiling_token in ceiling and result_token in result_change:
                blockers.append(f"章卡“本章推进上限”写着{ceiling_token}，但“本章结果变化”已经写成{result_token}，推进边界自相矛盾。")
                break

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
        warnings.append("存在到期伏笔但当前规划文字未提及：" + "、".join(due_foreshadow_ids[:6]) + suffix)
    if overdue_milestones:
        suffix = " 等" if len(overdue_milestones) > 4 else ""
        warnings.append("存在已经超期但未完成的关键节点：" + "、".join(overdue_milestones[:4]) + suffix)

    status = "fail" if blockers else ("warn" if warnings else "pass")
    contract = build_planning_contract(
        target_chapter,
        chapter_card,
        next_goal,
        blockers,
        warnings,
        health_digest,
        priority_debt,
    )
    report_path = project_dir / "04_gate" / f"ch{target_chapter:03d}" / "planning_review.md"
    result_path = project_dir / "04_gate" / f"ch{target_chapter:03d}" / "planning_review.json"
    return {
        "script": "open_book.py#planning",
        "project": project_dir.as_posix(),
        "target_chapter": target_chapter,
        "status": status,
        "planning_verdict": "revise" if blockers else "pass",
        "active_volume": active_volume or "未设定",
        "active_arc": active_arc or "未设定",
        "absolute_time": absolute_time or "未设定",
        "current_place": current_place or "未设定",
        "next_goal": next_goal or "未设定",
        "chapter_card_path": chapter_card_path.as_posix() if chapter_card_path else "",
        "chapter_card": chapter_card,
        "chapter_reason": narrative_anchor or "未识别，请人工补全本章存在理由。",
        "delete_loss": "会损失当前弧推进 / 既有伏笔回收 / 关键节点窗口。" if due_foreshadow_ids or due_milestones or overdue_milestones else "当前未识别到硬性窗口，需人工确认本章删减损失。",
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
        "report_paths": {"markdown": report_path.as_posix(), "json": result_path.as_posix()},
        "returncode": 1 if blockers else 0,
    }


def enrich_planning_payload(payload: dict[str, object]) -> dict[str, object]:
    steps = payload.get("steps", [])
    if not isinstance(steps, list):
        return payload

    planning_step = next((step for step in steps if str(step.get("script", "")).strip() == "open_book.py#planning"), {})
    context_step = next((step for step in steps if str(step.get("script", "")).strip() == "open_book.py#context"), {})
    target_chapter = int(planning_step.get("target_chapter") or context_step.get("chapter") or 0)
    planning_status = str(planning_step.get("status", "missing")).strip()
    planning_verdict = str(planning_step.get("planning_verdict", "missing")).strip()
    planning_blockers = [str(item) for item in planning_step.get("blockers", []) if str(item).strip()]
    planning_warnings = [str(item) for item in planning_step.get("warnings", []) if str(item).strip()]
    context_warnings = [str(item) for item in context_step.get("warnings", []) if str(item).strip()]
    context_failed = str(context_step.get("status", "pass")).strip() == "fail"
    blocking = bool(planning_blockers) or planning_status == "fail" or context_failed
    write_ready = planning_verdict == "pass" and not blocking

    if blocking:
        readiness_summary = "不可写，需先清理 planning blockers。"
    elif str(payload.get("status", "pass")).strip() == "warn":
        readiness_summary = "可写，但建议先补强 planning/context 预警。"
    else:
        readiness_summary = "可写，可直接进入正文规划。"

    payload.update(
        {
            "target_chapter": target_chapter,
            "planning_status": planning_status,
            "planning_verdict": planning_verdict,
            "planning_blockers": planning_blockers,
            "planning_warnings": planning_warnings,
            "context_warnings": context_warnings,
            "blocking": "yes" if blocking else "no",
            "write_ready": "yes" if write_ready else "no",
            "readiness_summary": readiness_summary,
            "warning_sources": {
                "open_book.py#planning": len(planning_warnings),
                "open_book.py#context": len(context_warnings),
            },
        }
    )
    return payload


def build_open_payload(project_dir: Path, target_chapter: int) -> dict[str, object]:
    planning_step = build_planning_payload(project_dir, target_chapter)
    context_step = build_context_payload(project_dir, target_chapter)
    steps = [planning_step, context_step]
    warnings: list[str] = []
    for step in steps:
        warnings.extend(step.get("warnings", []) if isinstance(step.get("warnings"), list) else [])
    payload = {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "fail" if any(str(step.get("status", "pass")) == "fail" for step in steps) else ("warn" if any(str(step.get("status", "pass")) == "warn" for step in steps) else "pass"),
        "warning_count": len(warnings),
        "warnings": warnings,
        "report_paths": {
            str(step.get("script", "step")): step.get("report_paths", {})
            for step in steps
            if isinstance(step.get("report_paths"), dict)
        },
        "steps": steps,
    }
    return enrich_planning_payload(payload)


def check_plan(plan_text: str, warnings: list[str], blockers: list[str]) -> None:
    required_labels = ["书名", "题材", "核心卖点"]
    for label in required_labels:
        if f"- {label}：" not in plan_text and f"- {label}:" not in plan_text:
            blockers.append(f"`plan.md` 缺少“{label}”，开书锚点不足。")
    if "预计总字数" not in plan_text:
        derived_target_words = derive_plan_target_words(plan_text)
        if derived_target_words <= 0:
            blockers.append("`plan.md` 缺少“预计总字数”，且无法从章节字数约束与卷范围推导总字数。")
        else:
            warnings.append(f"`plan.md` 未直写预计总字数，当前按卷范围推导约 `{derived_target_words}` 字。")
    if has_placeholder(plan_text):
        warnings.append("`plan.md` 仍含占位符，说明开书信息还没有填实。")


def check_state(state_text: str, warnings: list[str], blockers: list[str]) -> None:
    if "## 下章预告" not in state_text:
        warnings.append("`state.md` 缺少“下章预告”结构，后续章节承接会变弱。")
    if has_placeholder(state_text):
        warnings.append("`state.md` 仍含占位符，当前状态锚点还未填实。")
    if "- 当前卷：" not in state_text and "- 当前卷:" not in state_text:
        blockers.append("`state.md` 缺少“当前卷”，开书阶段缺卷级推进锚点。")


def check_style(style_text: str, warnings: list[str], blockers: list[str]) -> None:
    required_labels = ["题材", "主风格标签", "语言风格", "必须保住的声音"]
    for label in required_labels:
        if label not in style_text:
            warnings.append(f"`style.md` 可能缺少“{label}”相关内容，书级风格还不够具体。")
    if has_placeholder(style_text):
        warnings.append("`style.md` 仍含占位符，风格锚点未完成。")
    if "现代通俗大白话" not in style_text and "语言风格" in style_text:
        warnings.append("`style.md` 尚未明确默认表达基线，建议把“大白话/清晰可读”落成具体约束。")


def check_voice(voice_text: str, warnings: list[str], blockers: list[str]) -> None:
    if "角色说话差分总则" not in voice_text:
        blockers.append("`voice.md` 缺少角色声口差分总则，后续容易全员一个腔。")
    if has_placeholder(voice_text):
        warnings.append("`voice.md` 仍含占位符，书级声音尚未定实。")


def check_characters(char_text: str, warnings: list[str], blockers: list[str]) -> None:
    if "## 主角" not in char_text:
        blockers.append("`characters.md` 缺少主角档案，开书不能直接进入写作。")
    if "## 核心配角" not in char_text:
        warnings.append("`characters.md` 尚未补核心配角，关系推进空间可能不足。")
    if has_placeholder(char_text):
        warnings.append("`characters.md` 仍含占位符，人物资料未完成。")


def build_launch_payload(project_dir: Path) -> dict[str, object]:
    warnings: list[str] = []
    blockers: list[str] = []
    missing_files = [item for item in REQUIRED_LAUNCH_FILES if not (project_dir / item).exists()]
    if missing_files:
        blockers.extend([f"缺少 `{item}`，开书锚点不完整。" for item in missing_files])

    plan_text = read_text(project_dir / "00_memory" / "plan.md")
    state_text = read_text(project_dir / "00_memory" / "state.md")
    style_text = read_text(project_dir / "00_memory" / "style.md")
    voice_text = read_text(project_dir / "00_memory" / "voice.md")
    characters_text = read_text(project_dir / "00_memory" / "characters.md")

    if plan_text:
        check_plan(plan_text, warnings, blockers)
    if state_text:
        check_state(state_text, warnings, blockers)
    if style_text:
        check_style(style_text, warnings, blockers)
    if voice_text:
        check_voice(voice_text, warnings, blockers)
    if characters_text:
        check_characters(characters_text, warnings, blockers)

    status = "fail" if blockers else ("warn" if warnings else "pass")
    return {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "launch-readiness",
        "status": status,
        "missing_files": missing_files,
        "warnings": warnings,
        "warning_count": len(warnings),
        "blockers": blockers,
        "blocker_count": len(blockers),
        "recommended_next_steps": [
            "补齐 plan.md 的题材 / 卖点 / 总字数 / 卷目标",
            "补齐 state.md 的当前卷 / 当前阶段 / 下章预告",
            "补齐 style.md 与 voice.md，明确书级表达和角色声口差分",
            "补齐 characters.md 的主角与核心配角",
            "准备好后再进入写作主链或章节规划",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# 开书 readiness 报告",
        "",
        f"- 项目：`{payload['project']}`",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 模式：`{payload['mode']}`",
        f"- 状态：`{payload['status'].upper()}`",
        "",
        "## 阻断项",
    ]
    blockers = payload.get("blockers", [])
    if blockers:
        lines.extend([f"- {item}" for item in blockers])
    else:
        lines.append("- 无")
    lines.extend(["", "## 预警"])
    warnings = payload.get("warnings", [])
    if warnings:
        lines.extend([f"- {item}" for item in warnings])
    else:
        lines.append("- 无")
    lines.extend(["", "## 建议下一步"])
    lines.extend([f"- {item}" for item in payload.get("recommended_next_steps", [])])
    return "\n".join(lines) + "\n"


def main() -> int:
    configure_utf8_stdio()
    args = parse_args()
    project_dir = Path(args.project).resolve()
    if args.chapter is not None or args.target_chapter is not None:
        state_text = read_text(project_dir / "00_memory" / "state.md")
        target_chapter = detect_target_chapter(state_text, args.chapter, args.target_chapter)
        payload = build_open_payload(project_dir, target_chapter)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"status={payload['status']}")
            print(f"target_chapter={payload['target_chapter']}")
            print(f"write_ready={payload['write_ready']}")
            print(f"warning_count={payload['warning_count']}")
        return 0 if payload["status"] != "fail" else 1

    payload = build_launch_payload(project_dir)
    if not args.dry_run:
        payload["report_paths"] = write_markdown_json_reports(
            project_dir,
            payload,
            base_name="open_book_readiness",
            markdown_renderer=render_markdown,
        )
    else:
        report_dir = project_dir / "05_reports"
        payload["report_paths"] = {
            "markdown": (report_dir / "open_book_readiness.md").as_posix(),
            "json": (report_dir / "open_book_readiness.json").as_posix(),
        }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"blocker_count={payload['blocker_count']}")
        print(f"warning_count={payload['warning_count']}")
        print(f"report={payload['report_paths']['markdown']}")
    return 1 if payload["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
