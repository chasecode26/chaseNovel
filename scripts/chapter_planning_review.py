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
        "open_threads": parse_heading_value(card_text, ["open_threads", "开放线程"]),
        "forbidden_inventions": parse_heading_value(card_text, ["forbidden_inventions", "禁止发明"]),
        "chapter_function": parse_heading_value(card_text, ["本章功能"]),
        "chapter_goal": parse_heading_value(card_text, ["本章目标"]),
        "conflict_type": parse_heading_value(card_text, ["本章冲突"]),
        "result_change": parse_heading_value(card_text, ["本章结果变化"]),
        "result_type": parse_heading_value(card_text, ["本章结果类型"]),
        "emotion_point": parse_heading_value(card_text, ["本章爽点 / 情绪点", "本章爽点/情绪点"]),
        "relationship_shift": parse_heading_value(card_text, ["本章关系刷新点"]),
        "promise_progress": parse_heading_value(
            card_text,
            ["本章承诺推进 / 延后说明", "本章承诺推进/延后说明"],
        ),
        "hook_type": parse_heading_value(card_text, ["章尾钩子类型"]),
        "hook_text": parse_heading_value(card_text, ["本章章尾钩子"]),
        "opening_focus": parse_heading_value(card_text, ["开头先落什么"]),
        "mid_focus": parse_heading_value(card_text, ["中段必须推进什么"]),
        "ending_focus": parse_heading_value(card_text, ["结尾必须留下什么"]),
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


def is_done_status(text: str) -> bool:
    return "已完成" in text or "✅" in text or "完成" == text.strip()


def build_analysis(project_dir: Path, target_chapter: int) -> dict[str, object]:
    memory_dir = project_dir / "00_memory"
    plan_text = read_text(memory_dir / "plan.md")
    state_text = read_text(memory_dir / "state.md")
    voice_text = read_text(memory_dir / "voice.md")
    style_text = read_text(memory_dir / "style.md")
    recent_text = read_text(memory_dir / "summaries" / "recent.md")
    next_context_text = read_text(memory_dir / "retrieval" / "next_context.md")
    chapter_card_path = find_chapter_card_path(project_dir, target_chapter)
    chapter_card_text = read_text(chapter_card_path) if chapter_card_path else ""
    chapter_card = parse_chapter_card(chapter_card_text) if chapter_card_text else {}

    active_volume = extract_present_line(state_text, "- 当前卷") or extract_state_value(state_text, "当前卷")
    active_arc = extract_present_line(state_text, "- 当前弧") or extract_state_value(state_text, "当前弧")
    absolute_time = extract_present_line(state_text, "- 当前绝对时间") or extract_state_value(state_text, "当前绝对时间")
    current_place = extract_present_line(state_text, "- 当前地点") or extract_state_value(state_text, "当前地点")
    next_goal = extract_next_goal(state_text)
    due_foreshadow_ids = load_due_foreshadow_ids(project_dir, target_chapter)
    milestones = parse_plan_milestones(plan_text)

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

    narrative_anchor = chapter_card.get("chapter_function", "") or next_goal or "\n".join(useful_lines(next_context_text, 4))
    combined_planning_text = "\n".join(
        part for part in (chapter_card_text, next_goal, next_context_text, recent_text) if part.strip()
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
    if not next_context_text:
        warnings.append("尚未生成 `00_memory/retrieval/next_context.md`，建议先跑 context 再定稿本章规划。")
    if not chapter_card_path:
        warnings.append("未找到显式章卡，当前预审主要基于 `state.md` / `next_context.md` 推断。")
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

    return {
        "target_chapter": target_chapter,
        "status": status,
        "planning_verdict": "pass" if status == "pass" else "revise",
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
        "warnings": warnings,
        "warning_count": len(warnings),
        "blockers": blockers,
        "blocker_count": len(blockers),
        "context_excerpt": useful_lines(next_context_text, 8),
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
        render_list(list(analysis["context_excerpt"]), "无可用 next_context 摘录"),
        "",
        "### 书级声音摘录",
        render_list(list(analysis["voice_excerpt"]), "无可用声音摘录"),
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
        report_path.write_text(render_markdown(project_dir, analysis), encoding="utf-8")
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
        print(f"warning_count={analysis['warning_count']}")
        print(f"blocker_count={analysis['blocker_count']}")
        print(f"report={report_path.as_posix()}")
    return 1 if analysis["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
