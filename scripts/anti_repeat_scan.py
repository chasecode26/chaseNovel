#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from novel_utils import has_placeholder, list_chapter_files, read_text


HOOK_PATTERNS = {
    "结果未揭晓型": ("结果", "揭晓", "胜负", "到底成没成", "考核", "比试", "奖励", "到账", "名单", "名次"),
    "危机压顶型": ("危机", "危险", "杀", "追", "暴露", "出事", "围杀", "追杀", "搜查", "强敌", "失守"),
    "选择逼近型": ("二选一", "选择", "站队", "取舍", "代价", "该不该", "必须选", "要不要"),
    "信息反转型": ("真相", "发现", "原来", "身份", "秘密", "翻案", "不对", "死了", "旧案", "另一层"),
    "关系突变型": ("心乱", "沉默", "对视", "靠近", "分开", "决裂", "护短", "站队", "掉马", "翻脸"),
    "资源争夺型": ("突破", "升级", "收获", "机缘", "传承", "名额", "物资", "资格", "订单", "资源"),
    "欲望升级型": ("不够", "更大", "下一步", "野心", "赢", "翻身", "上位", "长期目标", "想要更多"),
}

CONFLICT_PATTERNS = {
    "confrontation": ("对峙", "交手", "围杀", "镇压", "逼迫", "追杀", "出手"),
    "misunderstanding": ("误会", "误判", "嘴硬", "错认", "曲解"),
    "escape": ("逃", "潜入", "撤离", "脱身", "追捕"),
    "negotiation": ("谈判", "交易", "交换", "讲条件", "试探口风", "试探"),
    "investigation": ("查", "线索", "盘问", "摸底", "追线"),
}

RESULT_PATTERNS = {
    "small_win": ("小胜", "压住", "拿下", "稳住", "占上风"),
    "turnaround": ("翻盘", "反杀", "逆转", "反制"),
    "interrupted": ("被打断", "未成", "差一点", "来不及", "中断"),
    "loss": ("吃亏", "受伤", "失手", "失守", "败退"),
    "gain": ("收获", "得到", "拿到", "到账", "突破"),
}

PAYOFF_PATTERNS = {
    "power_crush": ("碾压", "镇压", "横扫", "一招", "威慑"),
    "verbal_pressure": ("放话", "压服", "吓退", "震慑"),
    "system_reward": ("系统", "奖励", "到账", "提示"),
    "crowd_reaction": ("震惊", "哗然", "围观", "侧目"),
    "relationship_shift": ("靠近", "和解", "决裂", "心乱", "试探"),
}

RELATION_PATTERNS = {
    "暧昧拉扯": ("暧昧", "嘴硬", "靠近", "对视", "让步"),
    "误会升级": ("误会", "冷战", "曲解", "误判"),
    "信任推进": ("托付", "默契", "交底", "并肩"),
    "关系破裂": ("决裂", "翻脸", "背刺", "失望"),
}

SCENE_PATTERNS = {
    "铺垫": ("铺垫", "准备", "试探", "观察"),
    "收集信息": ("线索", "情报", "摸底", "盘问"),
    "谈情试探": ("试探", "靠近", "嘴硬", "拉扯"),
    "直接冲突": ("交手", "围杀", "对峙", "出手"),
}

RUNTIME_HOOK_MAP = {
    "pressure_kept": "危机压顶型",
    "cost_upgrade": "选择逼近型",
    "reveal": "信息反转型",
    "result_pending": "结果未揭晓型",
    "relationship_shift": "关系突变型",
}

RUNTIME_RESULT_MAP = {
    "partial_win": "small_win",
    "partial_win_with_pressure_kept": "small_win",
    "pressure_stabilized": "small_win",
    "turnaround": "turnaround",
    "interrupted": "interrupted",
    "loss": "loss",
    "gain": "gain",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan recent chapter summaries for repeated hook and story-pattern risks."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    return parser.parse_args()


def split_summary_entries(text: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    blocks = re.split(r"\n(?=##\s*第?\d+章)", text)
    for block in blocks:
        stripped = block.strip()
        if not stripped:
            continue
        heading_match = re.search(r"##\s*第?(\d+)章[：:]\s*(.*)", stripped)
        if not heading_match:
            continue
        entries.append(
            {
                "chapter": heading_match.group(1),
                "title": heading_match.group(2).strip(),
                "body": stripped,
            }
        )
    return entries


def extract_summary_field(body: str, label: str) -> str:
    match = re.search(rf"-\s*{re.escape(label)}[:：]\s*(.+)", body)
    return match.group(1).strip() if match else ""


def classify_dimension(text: str, pattern_map: dict[str, tuple[str, ...]], fallback: str = "unknown") -> str:
    for label, patterns in pattern_map.items():
        if any(pattern in text for pattern in patterns):
            return label
    return fallback


def classify_hook(text: str) -> str:
    return classify_dimension(text, HOOK_PATTERNS)


def normalize_tag(text: str) -> str:
    normalized = text.strip()
    if not normalized or has_placeholder(normalized):
        return ""
    return normalized


def extract_md_value(text: str, label: str) -> str:
    match = re.search(rf"(?mi)^\s*-\s*{re.escape(label)}\s*[:：]\s*(.+)$", text)
    if not match:
        return ""
    value = match.group(1).strip()
    return "" if has_placeholder(value) else value


def extract_md_values(text: str, labels: tuple[str, ...]) -> list[str]:
    values: list[str] = []
    for label in labels:
        values.extend(
            match.group(1).strip()
            for match in re.finditer(rf"(?mi)^\s*-\s*{re.escape(label)}\s*[:：]\s*(.+)$", text)
            if match.group(1).strip() and not has_placeholder(match.group(1).strip())
        )
    return values


def load_runtime_dimension_map(project_dir: Path) -> dict[str, dict[str, str]]:
    dimensions_by_chapter: dict[str, dict[str, str]] = {}
    for gate_dir in sorted((project_dir / "04_gate").glob("ch*")):
        if not gate_dir.is_dir():
            continue
        chapter_match = re.search(r"ch(\d+)", gate_dir.name, re.IGNORECASE)
        if not chapter_match:
            continue
        chapter_key = chapter_match.group(1)
        blueprint_text = read_text(gate_dir / "chapter_blueprint.md")
        runtime_draft_text = read_text(gate_dir / "runtime_draft.md")
        editorial_text = read_text(gate_dir / "editorial_summary.md")
        combined_text = "\n".join(part for part in (blueprint_text, runtime_draft_text, editorial_text) if part.strip())
        if not combined_text:
            continue

        runtime_hook = extract_md_value(blueprint_text, "hook_type")
        runtime_result = extract_md_value(blueprint_text, "result_type")
        chapter_result = extract_md_value(blueprint_text, "chapter_result")
        main_pair = ""
        protagonist = extract_md_value(editorial_text, "protagonist")
        counterpart = extract_md_value(editorial_text, "counterpart")
        if protagonist and counterpart:
            main_pair = f"{protagonist} / {counterpart}"

        dimensions_by_chapter[chapter_key] = {
            "hook": RUNTIME_HOOK_MAP.get(runtime_hook, classify_hook(combined_text)),
            "conflict": classify_dimension(combined_text, CONFLICT_PATTERNS),
            "result": RUNTIME_RESULT_MAP.get(runtime_result, classify_dimension(f"{chapter_result} {combined_text}", RESULT_PATTERNS)),
            "payoff": classify_dimension(combined_text, PAYOFF_PATTERNS),
            "relationship": classify_dimension(combined_text, RELATION_PATTERNS),
            "scene": classify_dimension(" ".join(extract_md_values(blueprint_text, ("summary", "scene_plan_focus"))), SCENE_PATTERNS),
            "main_pair": normalize_tag(main_pair),
        }
    return dimensions_by_chapter


def merge_dimensions(base: dict[str, str], runtime_meta: dict[str, str]) -> dict[str, str]:
    merged = dict(base)
    for key in ("hook", "conflict", "result", "payoff", "relationship", "scene"):
        if merged.get(key, "unknown") == "unknown" and runtime_meta.get(key, "unknown") != "unknown":
            merged[key] = runtime_meta[key]
    if not merged.get("main_pair") and runtime_meta.get("main_pair"):
        merged["main_pair"] = runtime_meta["main_pair"]
    return merged


def analyze_entry_dimensions(entry: dict[str, str]) -> dict[str, str]:
    body = entry["body"]
    title = entry["title"]
    core_event = extract_summary_field(body, "核心事件")
    character_change = extract_summary_field(body, "人物变化")
    emotion = extract_summary_field(body, "情感基调")
    carry_out = extract_summary_field(body, "启下")
    combined = " ".join(part for part in (title, core_event, character_change, emotion, carry_out) if part)
    return {
        "hook": classify_hook(" ".join((carry_out, body))),
        "conflict": classify_dimension(combined, CONFLICT_PATTERNS),
        "result": classify_dimension(" ".join((core_event, carry_out)), RESULT_PATTERNS),
        "payoff": classify_dimension(" ".join((core_event, emotion, carry_out)), PAYOFF_PATTERNS),
        "relationship": classify_dimension(" ".join((character_change, emotion)), RELATION_PATTERNS),
        "scene": classify_dimension(combined, SCENE_PATTERNS),
        "main_pair": normalize_tag(character_change or extract_summary_field(body, "承上")),
    }


def analyze_golden_three(
    entries: list[dict[str, str]],
    runtime_dimensions: dict[str, dict[str, str]] | None = None,
) -> dict[str, object]:
    relevant = []
    runtime_dimensions = runtime_dimensions or {}
    for entry in entries:
        try:
            chapter_no = int(entry["chapter"])
        except (TypeError, ValueError):
            continue
        if 1 <= chapter_no <= 3:
            relevant.append((chapter_no, entry))
    relevant.sort(key=lambda item: item[0])

    warnings: list[str] = []
    summary: list[dict[str, str]] = []
    if not relevant:
        return {"summary": summary, "warnings": warnings}

    chapter_map = {chapter_no: entry for chapter_no, entry in relevant}
    for chapter_no in [no for no in (1, 2, 3) if no in chapter_map]:
        entry = chapter_map[chapter_no]
        core_event = extract_summary_field(entry["body"], "核心事件")
        carry_out = extract_summary_field(entry["body"], "启下")
        character_change = extract_summary_field(entry["body"], "人物变化")
        summary.append(
            {
                "chapter": str(chapter_no),
                "core_event": core_event,
                "carry_out": carry_out,
                "character_change": character_change,
                "hook": merge_dimensions(
                    {"hook": classify_hook(" ".join((carry_out, entry["body"])))},
                    runtime_dimensions.get(str(chapter_no).zfill(3), {}),
                ).get("hook", "unknown"),
            }
        )

    if 1 in chapter_map and not extract_summary_field(chapter_map[1]["body"], "核心事件"):
        warnings.append("第1章摘要缺少“核心事件”，无法确认开篇抓手是否落地。")
    if 2 in chapter_map:
        second_event = extract_summary_field(chapter_map[2]["body"], "核心事件")
        second_change = extract_summary_field(chapter_map[2]["body"], "人物变化")
        second_carry = extract_summary_field(chapter_map[2]["body"], "启下")
        if not any((second_event, second_change, second_carry)):
            warnings.append("第2章摘要过空，无法确认主角是否已经开始行动。")
        elif not second_event and not second_change:
            warnings.append("第2章未明显体现行动推进或局面显影，黄金三章中段偏虚。")
    if 3 in chapter_map:
        third_event = extract_summary_field(chapter_map[3]["body"], "核心事件")
        third_carry = extract_summary_field(chapter_map[3]["body"], "启下")
        third_hook = merge_dimensions(
            {"hook": classify_hook(" ".join((third_carry, chapter_map[3]["body"])))},
            runtime_dimensions.get("003", {}),
        ).get("hook", "unknown")
        if not third_carry:
            warnings.append("第3章摘要缺少“启下”，无法确认长期承诺是否挂到第4章。")
        if third_hook == "unknown":
            warnings.append("第3章未识别到明确章尾钩子类型，黄金三章收束偏弱。")
        if not third_event:
            warnings.append("第3章摘要缺少“核心事件”，长期承诺可能没有落到局面变化。")
    if 1 in chapter_map and 2 in chapter_map:
        first_event = extract_summary_field(chapter_map[1]["body"], "核心事件")
        second_event = extract_summary_field(chapter_map[2]["body"], "核心事件")
        if first_event and second_event and first_event == second_event:
            warnings.append("第1-2章“核心事件”文本完全重复，开篇推进可能停在同一层。")
    if 2 in chapter_map and 3 in chapter_map:
        second_carry = extract_summary_field(chapter_map[2]["body"], "启下")
        third_carry = extract_summary_field(chapter_map[3]["body"], "启下")
        if second_carry and third_carry and second_carry == third_carry:
            warnings.append("第2-3章“启下”重复，第3章没有把承诺再往上抬。")

    return {"summary": summary, "warnings": warnings}


def analyze_midgame_fatigue(chapter_dimensions: list[dict[str, str]]) -> dict[str, object]:
    recent = chapter_dimensions[-5:]
    warnings: list[str] = []
    summary = {
        "window_size": len(recent),
        "recent_chapters": [item["chapter"] for item in recent],
        "unique_results": len({item["result"] for item in recent if item["result"] != "unknown"}),
        "unique_conflicts": len({item["conflict"] for item in recent if item["conflict"] != "unknown"}),
        "unique_hooks": len({item["hook"] for item in recent if item["hook"] != "unknown"}),
        "unique_pairs": len({item["main_pair"] for item in recent if item["main_pair"]}),
    }
    if len(recent) < 5:
        return {"summary": summary, "warnings": warnings}

    if summary["unique_results"] <= 2:
        warnings.append("近5章结果类型过少，中盘反馈可能开始同质化。")
    if summary["unique_conflicts"] <= 2:
        warnings.append("近5章冲突路径过少，中盘冲突形态可能重复。")
    if summary["unique_hooks"] <= 2:
        warnings.append("近5章钩子类型过少，章尾驱动力可能进入模板循环。")
    if summary["unique_pairs"] <= 2:
        warnings.append("近5章主要人物组合过少，互动关系可能发僵。")

    def max_streak(key: str) -> int:
        best = 1
        current = 1
        for previous, item in zip(recent, recent[1:]):
            if item[key] != "unknown" and item[key] == previous[key]:
                current += 1
                best = max(best, current)
            else:
                current = 1
        return best

    summary["max_result_streak"] = max_streak("result")
    summary["max_hook_streak"] = max_streak("hook")
    summary["max_conflict_streak"] = max_streak("conflict")

    if summary["max_result_streak"] >= 3:
        warnings.append(f"近章结果类型连续 {summary['max_result_streak']} 章未换挡，建议先换结果。")
    if summary["max_hook_streak"] >= 3:
        warnings.append(f"近章钩子类型连续 {summary['max_hook_streak']} 章未换挡，建议换章尾路线。")
    if summary["max_conflict_streak"] >= 3:
        warnings.append(f"近章冲突路径连续 {summary['max_conflict_streak']} 章未换挡，建议换冲突形态。")

    return {"summary": summary, "warnings": warnings}


def detect_repeat_risks(entries: list[dict[str, str]], runtime_dimensions: dict[str, dict[str, str]] | None = None) -> dict[str, object]:
    hook_counter: Counter[str] = Counter()
    conflict_counter: Counter[str] = Counter()
    result_counter: Counter[str] = Counter()
    payoff_counter: Counter[str] = Counter()
    relationship_counter: Counter[str] = Counter()
    scene_counter: Counter[str] = Counter()
    pair_counter: Counter[str] = Counter()
    opener_counter: Counter[str] = Counter()
    chapter_dimensions: list[dict[str, str]] = []
    runtime_dimensions = runtime_dimensions or {}

    for entry in entries:
        dimensions = analyze_entry_dimensions(entry)
        dimensions = merge_dimensions(dimensions, runtime_dimensions.get(str(entry["chapter"]).zfill(3), {}))
        chapter_dimensions.append({"chapter": entry["chapter"], **dimensions})
        hook_counter[dimensions["hook"]] += 1
        conflict_counter[dimensions["conflict"]] += 1
        result_counter[dimensions["result"]] += 1
        payoff_counter[dimensions["payoff"]] += 1
        relationship_counter[dimensions["relationship"]] += 1
        scene_counter[dimensions["scene"]] += 1
        if dimensions["main_pair"]:
            pair_counter[dimensions["main_pair"]] += 1
        first_line = next((line.strip() for line in entry["body"].splitlines() if line.strip().startswith("-")), "")
        if first_line:
            opener_counter[first_line[:18]] += 1

    warnings: list[str] = []
    for label, count in hook_counter.items():
        if label != "unknown" and count >= 3:
            warnings.append(f"近章 `{label}` 型钩子出现 {count} 次，存在重复风险。")
    for label, count in conflict_counter.items():
        if label != "unknown" and count >= 3:
            warnings.append(f"近章 `{label}` 型冲突出现 {count} 次，冲突路径有同质化风险。")
    for label, count in result_counter.items():
        if label != "unknown" and count >= 3:
            warnings.append(f"近章 `{label}` 型结果出现 {count} 次，结果反馈过于单一。")
    for label, count in payoff_counter.items():
        if label != "unknown" and count >= 3:
            warnings.append(f"近章 `{label}` 型爽点路径出现 {count} 次，反馈价值风险升高。")
    for label, count in relationship_counter.items():
        if label != "unknown" and count >= 3:
            warnings.append(f"近章 `{label}` 型关系推进出现 {count} 次，关系线可能原地打转。")
    for label, count in scene_counter.items():
        if label != "unknown" and count >= 4:
            warnings.append(f"近章 `{label}` 型场景功能出现 {count} 次，章节职责可能重复。")
    for opener, count in opener_counter.items():
        if count >= 3:
            warnings.append(f"近章摘要开头模式重复 {count} 次：{opener}")
    for pair, count in pair_counter.items():
        if count >= 3:
            warnings.append(f"近章主要人物组合重复 {count} 次：{pair}")

    return {
        "chapter_dimensions": chapter_dimensions,
        "hook_counter": dict(hook_counter),
        "conflict_counter": dict(conflict_counter),
        "result_counter": dict(result_counter),
        "payoff_counter": dict(payoff_counter),
        "relationship_counter": dict(relationship_counter),
        "scene_counter": dict(scene_counter),
        "pair_counter": dict(pair_counter.most_common(10)),
        "opener_counter": dict(opener_counter.most_common(10)),
        "warnings": warnings,
    }


def detect_body_patterns(project_dir: Path) -> dict[str, object]:
    opening_counter: Counter[str] = Counter()
    hook_counter: Counter[str] = Counter()
    chapter_files = list_chapter_files(project_dir)[-12:]
    for _, path in chapter_files:
        content = read_text(path)
        lines = [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith("#")]
        if lines:
            opening_counter[lines[0][:24]] += 1
            tail = "\n".join(lines[-5:])
            hook_counter[classify_hook(tail)] += 1

    warnings: list[str] = []
    for opener, count in opening_counter.items():
        if count >= 3:
            warnings.append(f"近章正文开头模式重复 {count} 次：{opener}")
    for label, count in hook_counter.items():
        if label != "unknown" and count >= 3:
            warnings.append(f"近章正文结尾 `{label}` 型钩子重复 {count} 次。")
    if not chapter_files:
        warnings.append("当前没有正文章节，无法判断正文开头和章尾钩子是否重复。")
    return {
        "body_openers": dict(opening_counter.most_common(10)),
        "body_hooks": dict(hook_counter),
        "warnings": warnings,
    }


def suggest_actions(payload: dict[str, object]) -> list[str]:
    suggestions: list[str] = []
    hook_counter = payload.get("hook_counter", {})
    conflict_counter = payload.get("conflict_counter", {})
    result_counter = payload.get("result_counter", {})
    payoff_counter = payload.get("payoff_counter", {})
    relationship_counter = payload.get("relationship_counter", {})
    scene_counter = payload.get("scene_counter", {})
    pair_counter = payload.get("pair_counter", {})

    if conflict_counter.get("misunderstanding", 0) >= 3:
        suggestions.append("把下一章主冲突从误会/嘴硬，换成摊牌、交易、设局或直接对抗。")
    if result_counter.get("small_win", 0) >= 3:
        suggestions.append("不要再给小胜，改成险胜、失手、被打断，或赢局面但丢资源/名声。")
    if payoff_counter.get("power_crush", 0) >= 3 or payoff_counter.get("verbal_pressure", 0) >= 3:
        suggestions.append("减少碾压和嘴上压服，补真实代价、关系变化或信息反转。")
    if relationship_counter.get("暧昧拉扯", 0) >= 3:
        suggestions.append("关系线不要继续嘴硬拉扯，改成信任推进、误会炸裂或利益绑定。")
    if scene_counter.get("铺垫", 0) >= 4:
        suggestions.append("下一章不要再铺垫，必须给局面变化、资源结果或明确摊牌。")
    if hook_counter.get("危机压顶型", 0) >= 3:
        suggestions.append("章尾钩子别再只写危险逼近，改成结果未揭晓型、关系突变型或选择逼近型。")
    if hook_counter.get("结果未揭晓型", 0) >= 3:
        suggestions.append("别连续卡结果揭晓，下一章改用危机压顶型、关系突变型或信息反转型。")
    if any(count >= 3 for count in pair_counter.values()):
        suggestions.append("换主要人物组合，让边缘角色、对手或新搭档进场，打断固定互动模板。")

    golden_three = payload.get("golden_three", {})
    if isinstance(golden_three, dict) and golden_three.get("warnings"):
        suggestions.append("开篇前三章未完全拉开层级，回看黄金三章：第1章抓入场，第2章推行动，第3章挂长期承诺。")
    midgame = payload.get("midgame_fatigue", {})
    if isinstance(midgame, dict) and midgame.get("warnings"):
        suggestions.append("进入中盘换挡点：先换结果类型，再换冲突路径，再换人物组合，最后才换句子。")
    if not suggestions:
        suggestions.append("当前未发现高强度重复，可继续写，但仍需盯住下一章的结果类型和钩子换法。")
    return suggestions


def build_payload(project_dir: Path) -> dict[str, object]:
    entries = split_summary_entries(read_text(project_dir / "00_memory" / "summaries" / "recent.md"))
    runtime_dimensions = load_runtime_dimension_map(project_dir)
    analysis = detect_repeat_risks(entries, runtime_dimensions)
    body_analysis = detect_body_patterns(project_dir)
    golden_three = analyze_golden_three(entries, runtime_dimensions)
    midgame_fatigue = analyze_midgame_fatigue(analysis["chapter_dimensions"])
    warnings = (
        analysis["warnings"]
        + body_analysis["warnings"]
        + list(golden_three["warnings"])
        + list(midgame_fatigue["warnings"])
    )
    if not entries:
        warnings.append("recent 摘要为空，无法判断近章推进是否重复。")
    payload = {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "entry_count": len(entries),
        "chapter_dimensions": analysis["chapter_dimensions"],
        "hook_counter": analysis["hook_counter"],
        "conflict_counter": analysis["conflict_counter"],
        "result_counter": analysis["result_counter"],
        "payoff_counter": analysis["payoff_counter"],
        "relationship_counter": analysis["relationship_counter"],
        "scene_counter": analysis["scene_counter"],
        "pair_counter": analysis["pair_counter"],
        "opener_counter": analysis["opener_counter"],
        "body_openers": body_analysis["body_openers"],
        "body_hooks": body_analysis["body_hooks"],
        "golden_three": golden_three,
        "midgame_fatigue": midgame_fatigue,
        "warnings": warnings,
        "warning_count": len(warnings),
        "status": "warn" if warnings else "pass",
    }
    payload["suggestions"] = suggest_actions(payload)
    return payload


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# 反重复扫描报告",
        "",
        f"- 项目：`{payload['project']}`",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 近章条目数：`{payload['entry_count']}`",
        f"- 钩子分布：`{json.dumps(payload['hook_counter'], ensure_ascii=False)}`",
        f"- 冲突分布：`{json.dumps(payload['conflict_counter'], ensure_ascii=False)}`",
        f"- 结果分布：`{json.dumps(payload['result_counter'], ensure_ascii=False)}`",
        f"- 爽点路径：`{json.dumps(payload['payoff_counter'], ensure_ascii=False)}`",
        f"- 关系推进：`{json.dumps(payload['relationship_counter'], ensure_ascii=False)}`",
        f"- 场景功能：`{json.dumps(payload['scene_counter'], ensure_ascii=False)}`",
        f"- 正文结尾钩子：`{json.dumps(payload['body_hooks'], ensure_ascii=False)}`",
        "",
        "## 开篇三章快照",
    ]
    golden_three_summary = payload.get("golden_three", {}).get("summary", [])
    if golden_three_summary:
        for item in golden_three_summary:
            lines.append(
                f"- 第{item['chapter']}章：核心事件={item['core_event'] or '未写'} / 启下={item['carry_out'] or '未写'} / 钩子={item['hook']}"
            )
    else:
        lines.append("- 无")

    lines.extend(["", "## 中盘疲劳快照"])
    midgame_summary = payload.get("midgame_fatigue", {}).get("summary", {})
    if midgame_summary:
        lines.append(
            f"- 近窗章节：`{', '.join(midgame_summary.get('recent_chapters', [])) or '无'}` / "
            f"结果去重={midgame_summary.get('unique_results', 0)} / "
            f"冲突去重={midgame_summary.get('unique_conflicts', 0)} / "
            f"钩子去重={midgame_summary.get('unique_hooks', 0)} / "
            f"人物组合去重={midgame_summary.get('unique_pairs', 0)}"
        )
        lines.append(
            f"- 连续重复：结果={midgame_summary.get('max_result_streak', 0)} / "
            f"冲突={midgame_summary.get('max_conflict_streak', 0)} / "
            f"钩子={midgame_summary.get('max_hook_streak', 0)}"
        )
    else:
        lines.append("- 无")

    lines.extend(["", "## 六维快照"])
    chapter_dimensions = payload.get("chapter_dimensions", [])
    if chapter_dimensions:
        for item in chapter_dimensions[-5:]:
            lines.append(
                f"- 第{item['chapter']}章：冲突={item['conflict']} / 结果={item['result']} / 爽点={item['payoff']} / "
                f"关系={item['relationship']} / 钩子={item['hook']} / 场景={item['scene']}"
            )
    else:
        lines.append("- 无")

    lines.extend(["", "## 预警"])
    if payload["warnings"]:
        lines.extend(f"- {item}" for item in payload["warnings"])
    else:
        lines.append("- 无")

    lines.extend(["", "## 建议动作"])
    lines.extend(f"- {item}" for item in payload["suggestions"])
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    project_dir = Path(args.project).resolve()
    payload = build_payload(project_dir)
    reports_dir = project_dir / "05_reports"
    md_path = reports_dir / "repeat_report.md"
    json_path = reports_dir / "repeat_report.json"
    payload["report_paths"] = {
        "markdown": md_path.as_posix(),
        "json": json_path.as_posix(),
    }

    if not args.dry_run:
        reports_dir.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_markdown(payload), encoding="utf-8")
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"warning_count={payload['warning_count']}")
        print(f"entry_count={payload['entry_count']}")
        print(f"markdown={payload['report_paths']['markdown']}")
        print(f"json={payload['report_paths']['json']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
