#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from novel_utils import clean_value, count_chapter_files, detect_current_chapter, extract_state_value, read_text


CHANGE_LABELS = {
    "promise_threshold": "承诺阈值",
    "overdue_foreshadow_threshold": "伏笔超期阈值",
    "stalled_arc_threshold": "弧线停滞阈值",
    "repeat_warning_threshold": "重复预警阈值",
    "checkpoint_words": "章节节点字数",
    "due_soon_window": "临近到期窗口",
}

KNOWN_PATCH_TARGETS = (
    "timeline.md",
    "foreshadowing.md",
    "payoff_board.md",
    "character_arcs.md",
)

HEALTH_DIGEST_LIMIT = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a lightweight book-level dashboard snapshot for a chaseNovel project."
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


def count_list_items(value: object) -> int:
    return len(value) if isinstance(value, list) else 0


def summarize_dynamic_changes(step: str, payload: dict[str, object]) -> list[str]:
    adjustments = payload.get("dynamic_adjustments", {})
    if not isinstance(adjustments, dict):
        return []

    genre = str(payload.get("genre", "") or "未识别")
    subgenre = str(payload.get("subgenre", "") or "未识别")
    lines: list[str] = []

    for key, value in adjustments.items():
        if not isinstance(value, dict):
            continue
        base = value.get("base")
        effective = value.get("effective")
        if base is None or effective is None:
            continue
        label = CHANGE_LABELS.get(str(key), str(key))
        lines.append(f"{step}: {genre}/{subgenre} {label} {base}->{effective}")
    return lines


def build_health_digest(
    pipeline_json: dict[str, object],
    volume_json: dict[str, object],
    milestone_json: dict[str, object],
    warnings: list[str],
) -> list[str]:
    pipeline_digest = pipeline_json.get("health_digest", [])
    if isinstance(pipeline_digest, list) and pipeline_digest:
        return [str(item) for item in pipeline_digest[:HEALTH_DIGEST_LIMIT]]

    digest = summarize_dynamic_changes("volume", volume_json)
    digest.extend(summarize_dynamic_changes("milestone", milestone_json))
    if digest:
        return digest[:HEALTH_DIGEST_LIMIT]
    return warnings[:HEALTH_DIGEST_LIMIT]


def render_health_digest_markdown(items: list[str]) -> str:
    lines = ["# 风险摘要", ""]
    if items:
        lines.extend(f"- {item}" for item in items)
    else:
        lines.append("- 暂无风险摘要。")
    return "\n".join(lines) + "\n"


def build_payload(project_dir: Path) -> dict[str, object]:
    memory_dir = project_dir / "00_memory"
    reports_dir = project_dir / "05_reports"
    retrieval_dir = memory_dir / "retrieval"
    state_text = read_text(memory_dir / "state.md")
    foreshadow_json = load_json(reports_dir / "foreshadow_heatmap.json")
    volume_json = load_json(reports_dir / "volume_audit.json")
    milestone_json = load_json(reports_dir / "milestone_audit.json")
    pipeline_json = load_json(reports_dir / "pipeline_report.json")
    memory_sync_json = load_json(retrieval_dir / "memory_sync_queue.json")
    memory_patch_json = load_json(retrieval_dir / "memory_sync_patches.json")

    active_volume = extract_state_value(state_text, "当前卷")
    active_arc = extract_state_value(state_text, "当前弧")
    warnings: list[str] = []
    chapter_count = count_chapter_files(project_dir)

    if chapter_count == 0:
        warnings.append("当前项目尚未检测到正文章节，dashboard 只能反映模板与记忆状态。")
    if not (retrieval_dir / "next_context.md").exists():
        warnings.append("缺少 next_context.md；建议先运行 context_compiler.py 或 chase context。")

    overdue_count = count_list_items(foreshadow_json.get("overdue"))
    if overdue_count:
        warnings.append(f"当前存在 {overdue_count} 条超期伏笔，建议优先安排回收。")

    volume_warning_count = int(volume_json.get("warning_count", 0) or 0)
    if volume_warning_count:
        warnings.append(f"卷级审计当前有 {volume_warning_count} 条预警。")

    milestone_warning_count = int(milestone_json.get("warning_count", 0) or 0)
    if milestone_warning_count:
        warnings.append(f"关键节点/十万字审计当前有 {milestone_warning_count} 条预警。")

    status = "warn" if warnings else "pass"
    health_digest = build_health_digest(pipeline_json, volume_json, milestone_json, warnings)
    memory_sync_targets = list(memory_sync_json.keys()) if isinstance(memory_sync_json, dict) else []
    memory_patch_targets = list(memory_patch_json.keys()) if isinstance(memory_patch_json, dict) else []
    apply_ready_targets = [target for target in KNOWN_PATCH_TARGETS if target in memory_patch_targets]

    return {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "current_chapter": detect_current_chapter(state_text) or chapter_count,
        "active_volume": clean_value(active_volume),
        "active_arc": clean_value(active_arc),
        "chapter_count": chapter_count,
        "pending_foreshadow_count": count_list_items(foreshadow_json.get("active")),
        "overdue_foreshadow_count": overdue_count,
        "volume_warning_count": volume_warning_count,
        "milestone_warning_count": milestone_warning_count,
        "health_digest": health_digest,
        "memory_sync_targets": memory_sync_targets,
        "memory_patch_targets": memory_patch_targets,
        "memory_patch_count": len(memory_patch_targets),
        "apply_ready_targets": apply_ready_targets,
        "warnings": warnings,
        "warning_count": len(warnings),
        "report_paths": {
            "next_context": (retrieval_dir / "next_context.md").as_posix(),
            "memory_sync_queue": (retrieval_dir / "memory_sync_queue.md").as_posix(),
            "memory_sync_patches": (retrieval_dir / "memory_sync_patches.md").as_posix(),
            "markdown": (reports_dir / "dashboard.md").as_posix(),
            "json": (reports_dir / "dashboard.json").as_posix(),
        },
    }


def format_targets(targets: list[str]) -> str:
    return ", ".join(targets) if targets else "none"


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# 项目 Dashboard",
        "",
        f"- 项目：`{payload['project']}`",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 状态：`{payload['status']}`",
        f"- 当前章节：`第{int(payload['current_chapter']):03d}章`",
        f"- 当前卷 / 当前弧：`{payload['active_volume']}` / `{payload['active_arc']}`",
        f"- 已有章节数：`{payload['chapter_count']}`",
        f"- 活跃伏笔数：`{payload['pending_foreshadow_count']}`",
        f"- 超期伏笔数：`{payload['overdue_foreshadow_count']}`",
        f"- 卷级预警数：`{payload['volume_warning_count']}`",
        f"- 关键节点预警数：`{payload['milestone_warning_count']}`",
        f"- 记忆同步目标数：`{len(payload['memory_sync_targets'])}`",
        f"- 可确认 patch 数：`{payload['memory_patch_count']}`",
        "",
        "## 风险摘要",
    ]

    if payload["health_digest"]:
        lines.extend(f"- {item}" for item in payload["health_digest"])
    else:
        lines.append("- 暂无。")

    lines.extend(
        [
            "",
            "## 记忆同步",
            f"- 队列目标：`{format_targets(payload['memory_sync_targets'])}`",
            f"- patch 目标：`{format_targets(payload['memory_patch_targets'])}`",
            f"- 推荐应用目标：`{format_targets(payload['apply_ready_targets'])}`",
            f"- next_context：`{payload['report_paths']['next_context']}`",
            f"- memory_sync_queue：`{payload['report_paths']['memory_sync_queue']}`",
            f"- memory_sync_patches：`{payload['report_paths']['memory_sync_patches']}`",
            f"- dashboard.json：`{payload['report_paths']['json']}`",
        ]
    )

    if payload["warnings"]:
        lines.extend(["", "## 警告"])
        lines.extend(f"- {item}" for item in payload["warnings"])

    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    project_dir = Path(args.project).resolve()
    reports_dir = project_dir / "05_reports"
    payload = build_payload(project_dir)

    if not args.dry_run:
        reports_dir.mkdir(parents=True, exist_ok=True)
        (reports_dir / "dashboard.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        (reports_dir / "dashboard.md").write_text(render_markdown(payload), encoding="utf-8")

        retrieval_dir = project_dir / "00_memory" / "retrieval"
        retrieval_dir.mkdir(parents=True, exist_ok=True)
        (retrieval_dir / "dashboard_cache.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        (retrieval_dir / "health_digest.json").write_text(
            json.dumps(
                {
                    "project": payload["project"],
                    "generated_at": payload["generated_at"],
                    "health_digest": payload["health_digest"],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        (retrieval_dir / "health_digest.md").write_text(
            render_health_digest_markdown(payload["health_digest"]),
            encoding="utf-8",
        )

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"warning_count={payload['warning_count']}")
        print(f"digest_count={len(payload['health_digest'])}")
        print(f"chapter={payload['current_chapter']}")
        print(f"active_volume={payload['active_volume']}")
        print(f"active_arc={payload['active_arc']}")
        print(f"dashboard={payload['report_paths']['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
