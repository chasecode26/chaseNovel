#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from novel_utils import (
    count_chapter_files,
    count_total_chapter_chars,
    detect_project_genre,
    detect_project_subgenre,
    extract_markdown_table_rows,
    extract_state_value,
    read_text,
    useful_lines,
)


GENRE_AUDIT_PROFILES = {
    "都市/系统流": {
        "promise_threshold": 2,
        "overdue_foreshadow_threshold": 2,
        "stalled_arc_threshold": 1,
        "repeat_warning_threshold": 3,
        "profile_note": "都市系统流强调快反馈与身份跃迁，兑现债务与套路重复都要更早敲钟。",
    },
    "历史/权谋": {
        "promise_threshold": 4,
        "overdue_foreshadow_threshold": 3,
        "stalled_arc_threshold": 2,
        "repeat_warning_threshold": 5,
        "profile_note": "历史权谋允许更长铺陈，但不能放任核心节点与关系账长期失焦。",
    },
    "末世": {
        "promise_threshold": 2,
        "overdue_foreshadow_threshold": 2,
        "stalled_arc_threshold": 2,
        "repeat_warning_threshold": 3,
        "profile_note": "末世题材最怕危机疲劳与囤货流水账，资源债务和同质化要提前拦。",
    },
    "玄幻/修仙": {
        "promise_threshold": 3,
        "overdue_foreshadow_threshold": 3,
        "stalled_arc_threshold": 2,
        "repeat_warning_threshold": 4,
        "profile_note": "玄幻修仙要防升级空转与设定堆积，节奏可略松但不能失去兑现感。",
    },
    "仙侠/苟道": {
        "promise_threshold": 3,
        "overdue_foreshadow_threshold": 2,
        "stalled_arc_threshold": 1,
        "repeat_warning_threshold": 4,
        "profile_note": "苟道最怕只剩观望不推进，人物与关系的停滞阈值应更严。",
    },
    "种田": {
        "promise_threshold": 3,
        "overdue_foreshadow_threshold": 2,
        "stalled_arc_threshold": 2,
        "repeat_warning_threshold": 3,
        "profile_note": "种田经营能慢，但不能把阶段目标与关系回报慢成流水账。",
    },
    "盗墓/民国": {
        "promise_threshold": 2,
        "overdue_foreshadow_threshold": 2,
        "stalled_arc_threshold": 2,
        "repeat_warning_threshold": 3,
        "profile_note": "盗墓民国重谜面与危机，拖谜不解和下墓重复都会迅速伤追读。",
    },
    "默认": {
        "promise_threshold": 3,
        "overdue_foreshadow_threshold": 3,
        "stalled_arc_threshold": 2,
        "repeat_warning_threshold": 4,
        "profile_note": "未识别题材时使用通用阈值。",
    },
}

SUBGENRE_AUDIT_OVERRIDES = {
    ("都市/系统流", "低位反压"): {
        "promise_threshold": 2,
        "overdue_foreshadow_threshold": 2,
        "stalled_arc_threshold": 1,
        "repeat_warning_threshold": 3,
        "profile_note": "低位反压卷要快翻身，不能连续拖反馈和人物站位变化。",
    },
    ("都市/系统流", "身份揭面"): {
        "promise_threshold": 2,
        "overdue_foreshadow_threshold": 2,
        "stalled_arc_threshold": 1,
        "repeat_warning_threshold": 3,
        "profile_note": "身份揭面卷要持续揭开层级与代价，不能只靠围观震惊。",
    },
    ("都市/系统流", "规则碾压"): {
        "promise_threshold": 3,
        "overdue_foreshadow_threshold": 2,
        "stalled_arc_threshold": 1,
        "repeat_warning_threshold": 4,
        "profile_note": "规则碾压卷允许铺更大的局，但必须有规则层结果而非只打一张脸。",
    },
    ("历史/权谋", "边关争霸"): {
        "promise_threshold": 4,
        "overdue_foreshadow_threshold": 3,
        "stalled_arc_threshold": 2,
        "repeat_warning_threshold": 4,
        "profile_note": "边关争霸要盯军权、军心、边情后账，重复军议与口号要更早拦。",
    },
    ("历史/权谋", "朝堂咬合"): {
        "promise_threshold": 4,
        "overdue_foreshadow_threshold": 4,
        "stalled_arc_threshold": 2,
        "repeat_warning_threshold": 5,
        "profile_note": "朝堂咬合允许更长铺陈，但门阀、站队、圣意节点不能一直悬空。",
    },
    ("末世", "囤货"): {
        "promise_threshold": 2,
        "overdue_foreshadow_threshold": 2,
        "stalled_arc_threshold": 2,
        "repeat_warning_threshold": 3,
        "profile_note": "囤货卷最怕仓库流水账，资源债务与重复危机要更早报警。",
    },
    ("末世", "安全屋成型"): {
        "promise_threshold": 3,
        "overdue_foreshadow_threshold": 2,
        "stalled_arc_threshold": 2,
        "repeat_warning_threshold": 3,
        "profile_note": "安全屋成型卷要盯防御、规则与邻里威胁，不能只写收集不写守住。",
    },
    ("末世", "秩序治理"): {
        "promise_threshold": 3,
        "overdue_foreshadow_threshold": 3,
        "stalled_arc_threshold": 2,
        "repeat_warning_threshold": 4,
        "profile_note": "秩序治理卷允许更长布局，但必须持续兑现规则、组织和势力后账。",
    },
}

THRESHOLD_LABELS = {
    "promise_threshold": "承诺阈值",
    "overdue_foreshadow_threshold": "伏笔阈值",
    "stalled_arc_threshold": "停滞阈值",
    "repeat_warning_threshold": "重复阈值",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a volume-level health audit for a chaseNovel project."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Do not write report files")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(read_text(path))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def parse_active_promises(memory_dir: Path) -> list[dict[str, str]]:
    content = read_text(memory_dir / "payoff_board.md")
    rows: list[list[str]] = []
    for heading in ("活跃承诺", "娲昏穬鎵胯"):
        rows = extract_markdown_table_rows(content, heading)
        if len(rows) > 1:
            break
    items: list[dict[str, str]] = []
    for row in rows[1:]:
        if len(row) < 8 or not row[0].strip():
            continue
        items.append(
            {
                "id": row[0].strip(),
                "type": row[1].strip(),
                "content": row[2].strip(),
                "window": row[4].strip(),
                "status": row[5].strip(),
                "pressure": row[6].strip(),
            }
        )
    return items


def is_red_pressure_promise(item: dict[str, str]) -> bool:
    pressure = str(item.get("pressure", ""))
    status = str(item.get("status", ""))
    return any(marker in pressure for marker in ("🔴", "高", "馃敶")) or any(
        marker in status for marker in ("延迟", "逾期", "寤惰繜")
    )


def apply_adjustment(
    profile: dict[str, object],
    base_profile: dict[str, object],
    adjustments: dict[str, dict[str, object]],
    key: str,
    delta: int,
    reason: str,
    minimum: int = 1,
) -> None:
    if not delta:
        return
    current_value = int(profile[key])
    next_value = max(minimum, current_value + delta)
    actual_delta = next_value - current_value
    if not actual_delta:
        return
    profile[key] = next_value
    entry = adjustments.setdefault(
        key,
        {
            "base": int(base_profile[key]),
            "delta": 0,
            "effective": current_value,
            "reasons": [],
        },
    )
    entry["delta"] = int(entry["delta"]) + actual_delta
    entry["effective"] = next_value
    entry["reasons"].append(reason)


def compute_dynamic_profile(
    base_profile: dict[str, object],
    repeat_report: dict[str, object],
    arc_report: dict[str, object],
    foreshadow_report: dict[str, object],
    red_pressure_count: int,
    chapter_count: int,
) -> tuple[dict[str, object], dict[str, dict[str, object]], dict[str, object]]:
    effective_profile = dict(base_profile)
    adjustments: dict[str, dict[str, object]] = {}

    repeat_warning_count = len(repeat_report.get("warnings", []))
    midgame_summary = repeat_report.get("midgame_fatigue", {}).get("summary", {})
    max_result_streak = int(midgame_summary.get("max_result_streak", 0) or 0)
    max_conflict_streak = int(midgame_summary.get("max_conflict_streak", 0) or 0)
    max_hook_streak = int(midgame_summary.get("max_hook_streak", 0) or 0)
    unique_results = int(midgame_summary.get("unique_results", 0) or 0)
    unique_conflicts = int(midgame_summary.get("unique_conflicts", 0) or 0)
    unique_hooks = int(midgame_summary.get("unique_hooks", 0) or 0)
    stalled_arc_count = int(arc_report.get("stalled_arc_count", 0) or 0)
    overdue_foreshadow_count = len(foreshadow_report.get("overdue", []))

    early_stage = chapter_count < 8
    streak_pressure = max(max_result_streak, max_conflict_streak, max_hook_streak)
    variety_pressure = sum(
        1
        for value in (unique_results, unique_conflicts, unique_hooks)
        if value and value <= 2
    )
    signals = {
        "chapter_count": chapter_count,
        "early_stage": early_stage,
        "repeat_warning_count": repeat_warning_count,
        "red_pressure_count": red_pressure_count,
        "stalled_arc_count": stalled_arc_count,
        "overdue_foreshadow_count": overdue_foreshadow_count,
        "midgame_fatigue": {
            "max_result_streak": max_result_streak,
            "max_conflict_streak": max_conflict_streak,
            "max_hook_streak": max_hook_streak,
            "unique_results": unique_results,
            "unique_conflicts": unique_conflicts,
            "unique_hooks": unique_hooks,
        },
    }

    if (
        early_stage
        and repeat_warning_count
        and repeat_warning_count < int(base_profile["repeat_warning_threshold"])
        and streak_pressure < 3
    ):
        apply_adjustment(
            effective_profile,
            base_profile,
            adjustments,
            "repeat_warning_threshold",
            1,
            "篇幅仍早，重复扫描暂时放宽一档，避免开局噪音。",
        )
        return effective_profile, adjustments, signals

    if chapter_count >= 8 and (
        streak_pressure >= 3
        or repeat_warning_count >= int(base_profile["repeat_warning_threshold"])
        or variety_pressure >= 2
    ):
        apply_adjustment(
            effective_profile,
            base_profile,
            adjustments,
            "repeat_warning_threshold",
            -1,
            "中盘疲劳或重复预警已成形，卷级重复阈值收紧一档。",
        )

    if chapter_count >= 8 and red_pressure_count >= int(base_profile["promise_threshold"]):
        apply_adjustment(
            effective_profile,
            base_profile,
            adjustments,
            "promise_threshold",
            -1,
            "高压承诺堆积，承诺债务阈值提前收紧。",
        )

    if chapter_count >= 10 and overdue_foreshadow_count >= max(
        1, int(base_profile["overdue_foreshadow_threshold"]) - 1
    ):
        apply_adjustment(
            effective_profile,
            base_profile,
            adjustments,
            "overdue_foreshadow_threshold",
            -1,
            "伏笔逾期开始累积，回收阈值提前收紧。",
        )

    if chapter_count >= 8 and stalled_arc_count >= max(1, int(base_profile["stalled_arc_threshold"]) - 1):
        apply_adjustment(
            effective_profile,
            base_profile,
            adjustments,
            "stalled_arc_threshold",
            -1,
            "弧线停滞已出现，停滞阈值收紧一档。",
        )

    return effective_profile, adjustments, signals


def build_payload(project_dir: Path) -> dict[str, object]:
    memory_dir = project_dir / "00_memory"
    reports_dir = project_dir / "05_reports"
    state_text = read_text(memory_dir / "state.md")
    blueprint_path = project_dir / "01_outline" / "volume_blueprint.md"
    genre = detect_project_genre(project_dir)
    subgenre = detect_project_subgenre(project_dir, genre)
    base_profile = dict(GENRE_AUDIT_PROFILES.get(genre, GENRE_AUDIT_PROFILES["默认"]))
    base_profile.update(SUBGENRE_AUDIT_OVERRIDES.get((genre, subgenre), {}))
    repeat_report = load_json(reports_dir / "repeat_report.json")
    arc_report = load_json(reports_dir / "arc_health.json")
    foreshadow_report = load_json(reports_dir / "foreshadow_heatmap.json")
    promises = parse_active_promises(memory_dir)
    chapter_count = count_chapter_files(project_dir)

    red_pressure = [item for item in promises if is_red_pressure_promise(item)]
    effective_profile, dynamic_adjustments, dynamic_signals = compute_dynamic_profile(
        base_profile,
        repeat_report,
        arc_report,
        foreshadow_report,
        len(red_pressure),
        chapter_count,
    )

    warnings: list[str] = []
    if not useful_lines(read_text(blueprint_path), 6):
        warnings.append("缺少有效的 volume_blueprint.md，本卷目标、四大节点与收束条件不清。")

    overdue_foreshadows = len(foreshadow_report.get("overdue", []))
    stalled_arc_count = int(arc_report.get("stalled_arc_count", 0) or 0)
    repeat_warning_count = len(repeat_report.get("warnings", []))

    if len(red_pressure) >= int(effective_profile["promise_threshold"]):
        warnings.append(
            f"{genre} 题材下，高压或延迟中的承诺达到 {len(red_pressure)} 条，已超过阈值 {effective_profile['promise_threshold']}。"
        )
    if overdue_foreshadows >= int(effective_profile["overdue_foreshadow_threshold"]):
        warnings.append(
            f"{genre} 题材下，超期伏笔达到 {overdue_foreshadows} 条，已超过阈值 {effective_profile['overdue_foreshadow_threshold']}。"
        )
    if stalled_arc_count >= int(effective_profile["stalled_arc_threshold"]):
        warnings.append(
            f"{genre} 题材下，停滞/重复/失真角色弧达到 {stalled_arc_count} 条，已超过阈值 {effective_profile['stalled_arc_threshold']}。"
        )
    if repeat_warning_count >= int(effective_profile["repeat_warning_threshold"]):
        warnings.append(
            f"{genre} 题材下，反重复扫描预警达到 {repeat_warning_count} 条，已超过阈值 {effective_profile['repeat_warning_threshold']}。"
        )

    return {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "warn" if warnings else "pass",
        "genre": genre,
        "subgenre": subgenre or "未识别",
        "genre_profile": base_profile,
        "effective_profile": effective_profile,
        "dynamic_adjustments": dynamic_adjustments,
        "dynamic_signals": dynamic_signals,
        "current_volume": extract_state_value(state_text, "当前卷") or "未识别",
        "current_arc": extract_state_value(state_text, "当前弧") or "未识别",
        "chapter_count": chapter_count,
        "total_effective_words": count_total_chapter_chars(project_dir),
        "blueprint_path": blueprint_path.as_posix(),
        "blueprint_lines": useful_lines(read_text(blueprint_path), 10),
        "red_pressure_promises": red_pressure[:8],
        "overdue_foreshadow_count": overdue_foreshadows,
        "stalled_arc_count": stalled_arc_count,
        "repeat_warning_count": repeat_warning_count,
        "warnings": warnings,
        "warning_count": len(warnings),
    }


def render_dynamic_adjustments(payload: dict[str, object]) -> list[str]:
    adjustments = payload.get("dynamic_adjustments", {})
    if not adjustments:
        return ["- 动态修正：无"]
    lines: list[str] = []
    for key, value in adjustments.items():
        label = THRESHOLD_LABELS.get(key, key)
        reasons = "；".join(value.get("reasons", []))
        lines.append(
            f"- {label}：{value['base']} → {value['effective']} ({value['delta']:+d}) / {reasons}"
        )
    return lines


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# 卷级审计报告",
        "",
        f"- 项目：`{payload['project']}`",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 题材：`{payload['genre']}`",
        f"- 子类型：`{payload['subgenre']}`",
        f"- 当前卷 / 当前弧：`{payload['current_volume']}` / `{payload['current_arc']}`",
        f"- 已有章节数：`{payload['chapter_count']}`",
        f"- 有效总字数：`{payload['total_effective_words']}`",
        f"- 高压承诺数：`{len(payload['red_pressure_promises'])}`",
        f"- 超期伏笔数：`{payload['overdue_foreshadow_count']}`",
        f"- 弧线停滞数：`{payload['stalled_arc_count']}`",
        "",
        "## 题材阈值",
        f"- 说明：{payload['genre_profile']['profile_note']}",
        f"- 承诺阈值：{payload['genre_profile']['promise_threshold']}",
        f"- 伏笔阈值：{payload['genre_profile']['overdue_foreshadow_threshold']}",
        f"- 停滞阈值：{payload['genre_profile']['stalled_arc_threshold']}",
        f"- 重复阈值：{payload['genre_profile']['repeat_warning_threshold']}",
        "",
        "## 动态阈值",
        f"- 生效承诺阈值：{payload['effective_profile']['promise_threshold']}",
        f"- 生效伏笔阈值：{payload['effective_profile']['overdue_foreshadow_threshold']}",
        f"- 生效停滞阈值：{payload['effective_profile']['stalled_arc_threshold']}",
        f"- 生效重复阈值：{payload['effective_profile']['repeat_warning_threshold']}",
    ]
    lines.extend(render_dynamic_adjustments(payload))
    lines.extend(["", "## 卷纲摘录"])
    if payload["blueprint_lines"]:
        lines.extend(f"- {item}" for item in payload["blueprint_lines"])
    else:
        lines.append("- 无有效卷纲内容")
    lines.extend(["", "## 高压承诺"])
    if payload["red_pressure_promises"]:
        for item in payload["red_pressure_promises"]:
            lines.append(
                f"- `{item['id']}` [{item['type']}] {item['content']} / 状态={item['status']} / 压力={item['pressure']} / 窗口={item['window'] or '未写'}"
            )
    else:
        lines.append("- 无")
    lines.extend(["", "## 预警"])
    if payload["warnings"]:
        lines.extend(f"- {item}" for item in payload["warnings"])
    else:
        lines.append("- 无")
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    project_dir = Path(args.project).resolve()
    reports_dir = project_dir / "05_reports"
    payload = build_payload(project_dir)
    md_path = reports_dir / "volume_audit.md"
    json_path = reports_dir / "volume_audit.json"
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
        print(f"markdown={payload['report_paths']['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
