#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path


HOOK_PATTERNS = {
    "结果未揭晓型": ("结果", "揭晓", "胜负", "到底成没成", "考核", "比试", "奖励", "到账", "名单", "名次"),
    "危机压顶型": ("危机", "危险", "杀", "追", "暴露", "出事", "围杀", "追杀", "搜查", "强敌", "失守"),
    "选择逼近型": ("二选一", "选择", "站队", "取舍", "代价", "该不该", "必须选", "要不要"),
    "信息反转型": ("真相", "发现", "原来", "身份", "秘密", "翻案", "不对", "死了", "旧案", "另一层"),
    "关系突变型": ("心乱", "沉默", "对视", "靠近", "分开", "决裂", "护短", "站队", "掉马", "翻脸"),
    "资源争夺型": ("突破", "升级", "收获", "机缘", "传承", "名额", "物资", "资格", "订单", "资源"),
    "欲望升级型": ("不够", "更大", "下一步", "野心", "争", "翻身", "上位", "长期目标", "想要更多"),
}

CONFLICT_PATTERNS = {
    "confrontation": ("对峙", "交手", "围杀", "镇压", "逼迫", "追杀", "出手"),
    "misunderstanding": ("误会", "误判", "嘴硬", "错认", "曲解"),
    "escape": ("逃", "潜入", "撤离", "脱身", "追捕"),
    "negotiation": ("谈判", "交易", "交换", "讲条件", "试探口风"),
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

PLACEHOLDER_PATTERNS = (
    re.compile(r"\{[A-Z0-9_]+\}"),
    re.compile(r"第_{2,}章"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan recent chapter summaries for repeated hook and story-pattern risks."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    return parser.parse_args()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").lstrip("\ufeff")


def has_placeholder(text: str) -> bool:
    normalized = text.strip()
    if not normalized:
        return False
    return any(pattern.search(normalized) for pattern in PLACEHOLDER_PATTERNS)


def split_summary_entries(text: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    blocks = re.split(r"\n(?=##\s*第?\d+章)", text)
    for block in blocks:
        stripped = block.strip()
        if not stripped:
            continue
        heading_match = re.search(r"##\s*第?(\d+)章[:：]?\s*(.*)", stripped)
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


def analyze_golden_three(entries: list[dict[str, str]]) -> dict[str, object]:
    relevant = []
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
    expected = [no for no in (1, 2, 3) if no in chapter_map]

    for chapter_no in expected:
        entry = chapter_map[chapter_no]
        core_event = extract_summary_field(entry["body"], "核心事件")
        carry_out = extract_summary_field(entry["body"], "启下")
        character_change = extract_summary_field(entry["body"], "人物变化")
        hook = classify_hook(" ".join((carry_out, entry["body"])))
        summary.append({
            "chapter": str(chapter_no),
            "core_event": core_event,
            "carry_out": carry_out,
            "character_change": character_change,
            "hook": hook,
        })

    if 1 in chapter_map:
        chapter1 = chapter_map[1]
        first_event = extract_summary_field(chapter1["body"], "核心事件")
        if not first_event:
            warnings.append("第1章摘要缺少“核心事件”，无法确认开篇抓手是否落地。")

    if 2 in chapter_map:
        chapter2 = chapter_map[2]
        second_event = extract_summary_field(chapter2["body"], "核心事件")
        second_change = extract_summary_field(chapter2["body"], "人物变化")
        second_carry = extract_summary_field(chapter2["body"], "启下")
        if not any((second_event, second_change, second_carry)):
            warnings.append("第2章摘要过空，无法确认主角是否已经开始行动。")
        elif not second_event and not second_change:
            warnings.append("第2章未明显体现“行动推进”或“局面显形”，黄金三章中段偏虚。")

    if 3 in chapter_map:
        chapter3 = chapter_map[3]
        third_carry = extract_summary_field(chapter3["body"], "启下")
        third_event = extract_summary_field(chapter3["body"], "核心事件")
        third_hook = classify_hook(" ".join((third_carry, chapter3["body"])))
        if not third_carry:
            warnings.append("第3章摘要缺少“启下”，无法确认长期承诺是否已挂到第4章。")
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
            warnings.append("第2-3章“启下”重复，第三章没有把承诺再往上抬。")

    return {"summary": summary, "warnings": warnings}


def normalize_tag(text: str) -> str:
    normalized = text.strip()
    if not normalized or has_placeholder(normalized):
        return ""
    return normalized


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


def detect_repeat_risks(entries: list[dict[str, str]]) -> dict[str, object]:
    hook_counter: Counter[str] = Counter()
    conflict_counter: Counter[str] = Counter()
    result_counter: Counter[str] = Counter()
    payoff_counter: Counter[str] = Counter()
    relationship_counter: Counter[str] = Counter()
    scene_counter: Counter[str] = Counter()
    pair_counter: Counter[str] = Counter()
    opener_counter: Counter[str] = Counter()
    chapter_dimensions: list[dict[str, str]] = []

    for entry in entries:
        body = entry["body"]
        dimensions = analyze_entry_dimensions(entry)
        chapter_dimensions.append({"chapter": entry["chapter"], **dimensions})
        hook_counter[dimensions["hook"]] += 1
        conflict_counter[dimensions["conflict"]] += 1
        result_counter[dimensions["result"]] += 1
        payoff_counter[dimensions["payoff"]] += 1
        relationship_counter[dimensions["relationship"]] += 1
        scene_counter[dimensions["scene"]] += 1
        if dimensions["main_pair"]:
            pair_counter[dimensions["main_pair"]] += 1
        first_line = next((line.strip() for line in body.splitlines() if line.strip().startswith("-")), "")
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
            warnings.append(f"近章 `{label}` 型爽点路径出现 {count} 次，反馈贬值风险升高。")
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
        suggestions.append("把下一章主冲突从误判/嘴硬，换成摊牌、交易、设局或直接对抗。")
    if result_counter.get("small_win", 0) >= 3:
        suggestions.append("不要再给小胜，改成险胜、失手、被打断，或胜局面但丢资源/名声。")
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
    if hook_counter.get("关系突变型", 0) >= 3:
        suggestions.append("关系钩子别连刷，改用资源争夺型、信息反转型或结果未揭晓型打断节奏。")
    if any(count >= 3 for count in pair_counter.values()):
        suggestions.append("换主要人物组合，让边缘角色、对手或新搭档进入场景，打断固定互动模板。")

    golden_three = payload.get("golden_three", {})
    golden_three_warnings = golden_three.get("warnings", []) if isinstance(golden_three, dict) else []
    if golden_three_warnings:
        suggestions.append("开篇前三章未完全拉开层级，回看黄金三章：第1章抓入场，第2章推动行动，第3章挂长期承诺。")

    if not suggestions:
        suggestions.append("当前未发现高强度重复，可继续写，但仍需盯住下一章的结果类型和钩子换法。")
    return suggestions


def collect_chapter_files(project_dir: Path) -> list[Path]:
    chapters_dir = project_dir / "03_chapters"
    items: list[tuple[int, Path]] = []
    if not chapters_dir.exists():
        return []
    for path in chapters_dir.iterdir():
        if not path.is_file():
            continue
        match = re.search(r"(\d+)", path.stem)
        if not match:
            continue
        items.append((int(match.group(1)), path))
    items.sort(key=lambda item: item[0])
    return [path for _, path in items[-12:]]


def detect_body_patterns(project_dir: Path) -> dict[str, object]:
    opening_counter: Counter[str] = Counter()
    hook_counter: Counter[str] = Counter()
    for path in collect_chapter_files(project_dir):
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
    return {
        "body_openers": dict(opening_counter.most_common(10)),
        "body_hooks": dict(hook_counter),
        "warnings": warnings,
    }


def build_payload(project_dir: Path) -> dict[str, object]:
    recent_path = project_dir / "00_memory" / "summaries" / "recent.md"
    entries = split_summary_entries(read_text(recent_path))
    analysis = detect_repeat_risks(entries)
    body_analysis = detect_body_patterns(project_dir)
    golden_three = analyze_golden_three(entries)
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
        "warnings": analysis["warnings"] + body_analysis["warnings"] + list(golden_three["warnings"]),
    }
    payload["suggestions"] = suggest_actions(payload)
    payload["warning_count"] = len(payload["warnings"])
    payload["status"] = "warn" if payload["warnings"] else "pass"
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
    golden_three = payload.get("golden_three", {})
    golden_three_summary = golden_three.get("summary", []) if isinstance(golden_three, dict) else []
    if golden_three_summary:
        for item in golden_three_summary:
            lines.append(
                f"- 第{item['chapter']}章：核心事件={item['core_event'] or '未写'} / "
                f"启下={item['carry_out'] or '未写'} / 钩子={item['hook']}"
            )
    else:
        lines.append("- 无")

    lines.extend([
        "",
        "## 六维快照",
    ])
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
        lines.extend([f"- {item}" for item in payload["warnings"]])
    else:
        lines.append("- 无")
    lines.extend(["", "## 替代建议"])
    lines.extend([f"- {item}" for item in payload.get("suggestions", [])])
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    project_dir = Path(args.project).resolve()
    payload = build_payload(project_dir)
    reports_dir = project_dir / "05_reports"
    md_path = reports_dir / "anti_repeat.md"
    json_path = reports_dir / "anti_repeat.json"
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
        print(f"entry_count={payload['entry_count']}")
        print(f"warning_count={payload['warning_count']}")
        print(f"markdown={payload['report_paths']['markdown']}")
        print(f"json={payload['report_paths']['json']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
