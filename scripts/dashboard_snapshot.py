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
RUNTIME_DIGEST_LIMIT = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a lightweight book-level dashboard snapshot for a chaseNovel project."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Do not write report files")
    return parser.parse_args()


def load_json(path: Path) -> object:
    if not path.exists():
        return {}
    try:
        payload = json.loads(read_text(path))
    except json.JSONDecodeError:
        return {}
    return payload


def count_list_items(value: object) -> int:
    return len(value) if isinstance(value, list) else 0


def normalize_list(value: object, *, limit: int | None = None) -> list[str]:
    if not isinstance(value, list):
        return []
    items = [str(item).strip() for item in value if str(item).strip()]
    return items if limit is None else items[:limit]


def build_runtime_digest(
    verdicts_payload: object,
    *,
    dimensions: list[str] | None = None,
    blocking: bool | None = None,
    limit: int = RUNTIME_DIGEST_LIMIT,
) -> list[str]:
    if not isinstance(verdicts_payload, list):
        return []

    verdicts = [item for item in verdicts_payload if isinstance(item, dict)]
    if not verdicts:
        return []

    ordered: list[dict[str, object]] = []
    if dimensions is not None:
        if not dimensions:
            return []
        seen_dimensions: set[str] = set()
        for dimension in dimensions:
            for verdict in verdicts:
                verdict_dimension = str(verdict.get("dimension", "")).strip()
                if verdict_dimension != dimension or verdict_dimension in seen_dimensions:
                    continue
                if blocking is not None and bool(verdict.get("blocking", False)) != blocking:
                    continue
                ordered.append(verdict)
                seen_dimensions.add(verdict_dimension)
                break
    else:
        for verdict in verdicts:
            if blocking is not None and bool(verdict.get("blocking", False)) != blocking:
                continue
            ordered.append(verdict)

    digest: list[str] = []
    for verdict in ordered[:limit]:
        dimension = str(verdict.get("dimension", "unknown")).strip() or "unknown"
        evidence = normalize_list(verdict.get("evidence", []), limit=1)
        minimal_fix = str(verdict.get("minimal_fix", "")).strip()
        rewrite_scope = str(verdict.get("rewrite_scope", "")).strip()
        detail = evidence[0] if evidence else (minimal_fix or str(verdict.get("status", "pass")).strip())
        digest.append(f"{dimension}: {detail}" + (f" [scope={rewrite_scope}]" if rewrite_scope else ""))
    return digest


def load_runtime_state(schema_dir: Path, retrieval_dir: Path) -> dict[str, object]:
    state_json = load_json(schema_dir / "state.json")
    runtime_payload = load_json(retrieval_dir / "leadwriter_runtime_payload.json")
    if not isinstance(state_json, dict):
        state_json = {}

    payload_decision = runtime_payload.get("decision", {}) if isinstance(runtime_payload, dict) else {}
    if not isinstance(payload_decision, dict):
        payload_decision = {}
    rewrite_brief = payload_decision.get("rewrite_brief", {})
    if not isinstance(rewrite_brief, dict):
        rewrite_brief = {}

    blocking_dimensions = payload_decision.get("blocking_dimensions", state_json.get("runtimeBlockingDimensions", []))
    advisory_dimensions = payload_decision.get("advisory_dimensions", state_json.get("runtimeAdvisoryDimensions", []))
    cycles_payload = runtime_payload.get("cycles", []) if isinstance(runtime_payload, dict) else []
    cycle_count = len(cycles_payload) if isinstance(cycles_payload, list) else 0
    last_cycle_decision = "unknown"
    if isinstance(cycles_payload, list) and cycles_payload:
        last_cycle = cycles_payload[-1]
        if isinstance(last_cycle, dict) and isinstance(last_cycle.get("decision"), dict):
            last_cycle_decision = str(last_cycle["decision"].get("decision", "unknown") or "unknown")

    return {
        "decision": str(payload_decision.get("decision", state_json.get("runtimeDecision", "unknown")) or "unknown"),
        "blocking_dimensions": normalize_list(blocking_dimensions),
        "advisory_dimensions": normalize_list(advisory_dimensions),
        "first_fix_priority": str(rewrite_brief.get("first_fix_priority", "")).strip(),
        "rewrite_scope": str(rewrite_brief.get("rewrite_scope", "")).strip(),
        "return_to": str(rewrite_brief.get("return_to", "")).strip(),
        "blocking_reasons": normalize_list(rewrite_brief.get("blocking_reasons", []), limit=RUNTIME_DIGEST_LIMIT),
        "must_change": normalize_list(rewrite_brief.get("must_change", []), limit=RUNTIME_DIGEST_LIMIT),
        "recheck_order": normalize_list(rewrite_brief.get("recheck_order", [])),
        "blocking_digest": build_runtime_digest(
            runtime_payload.get("verdicts", []) if isinstance(runtime_payload, dict) else [],
            dimensions=normalize_list(blocking_dimensions),
            blocking=True,
        ),
        "advisory_digest": build_runtime_digest(
            runtime_payload.get("verdicts", []) if isinstance(runtime_payload, dict) else [],
            dimensions=normalize_list(advisory_dimensions),
            blocking=False,
        ),
        "cycle_count": cycle_count,
        "last_cycle_decision": last_cycle_decision,
    }


def load_character_verdict(retrieval_dir: Path) -> dict[str, object]:
    payload = load_json(retrieval_dir / "leadwriter_character_verdict.json")
    if not isinstance(payload, dict):
        return {"status": "unknown", "evidence": []}
    evidence = payload.get("evidence", [])
    return {
        "status": str(payload.get("status", "unknown") or "unknown"),
        "evidence": [str(item) for item in evidence if str(item).strip()] if isinstance(evidence, list) else [],
    }


def summarize_apply_results(payload: object) -> dict[str, object]:
    if not isinstance(payload, list):
        return {"applied_targets": [], "ready_targets": [], "skipped_targets": []}
    applied_targets: list[str] = []
    ready_targets: list[str] = []
    skipped_targets: list[str] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        target = Path(str(item.get("schema_file", ""))).name
        if not target:
            continue
        status = str(item.get("status", "unknown"))
        if status == "applied":
            applied_targets.append(target)
        elif status == "ready":
            ready_targets.append(target)
        elif status == "skipped":
            skipped_targets.append(target)
    return {
        "applied_targets": applied_targets,
        "ready_targets": ready_targets,
        "skipped_targets": skipped_targets,
    }


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
    warnings: list[str],
) -> list[str]:
    pipeline_digest = pipeline_json.get("health_digest", [])
    if isinstance(pipeline_digest, list) and pipeline_digest:
        return [str(item) for item in pipeline_digest[:HEALTH_DIGEST_LIMIT]]
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
    schema_dir = memory_dir / "schema"
    state_text = read_text(memory_dir / "state.md")
    foreshadow_json = load_json(reports_dir / "foreshadow_heatmap.json")
    pipeline_json = load_json(reports_dir / "pipeline_report.json")
    plan_json = load_json(schema_dir / "plan.json")
    memory_sync_json = load_json(retrieval_dir / "memory_sync_queue.json")
    memory_patch_json = load_json(retrieval_dir / "leadwriter_memory_patches.json")
    memory_apply_json = load_json(retrieval_dir / "leadwriter_memory_apply.json")
    runtime_state = load_runtime_state(schema_dir, retrieval_dir)
    character_verdict = load_character_verdict(retrieval_dir)
    apply_summary = summarize_apply_results(memory_apply_json)
    runtime_payload_exists = (retrieval_dir / "leadwriter_runtime_payload.json").exists()

    active_volume = extract_state_value(state_text, "当前卷")
    active_arc = extract_state_value(state_text, "当前弧")
    warnings: list[str] = []
    chapter_count = count_chapter_files(project_dir)

    if chapter_count == 0:
        warnings.append("当前项目尚未检测到正文章节，dashboard 只能反映模板与记忆状态。")
    if not (retrieval_dir / "next_context.md").exists() and not runtime_payload_exists:
        warnings.append("?? next_context.md?????? `chase open --project <dir> --chapter <n>` ????????")

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
    if isinstance(memory_patch_json, list):
        memory_patch_targets = [
            Path(str(item.get("schema_file", ""))).name
            for item in memory_patch_json
            if isinstance(item, dict) and str(item.get("schema_file", "")).strip()
        ]
    elif isinstance(memory_patch_json, dict):
        memory_patch_targets = list(memory_patch_json.keys())
    else:
        memory_patch_targets = []
    if isinstance(memory_apply_json, list):
        apply_ready_targets = [
            Path(str(item.get("schema_file", ""))).name
            for item in memory_apply_json
            if isinstance(item, dict) and str(item.get("status")) in {"ready", "applied"}
        ]
    else:
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
        "runtime_signals": {
            "decision": runtime_state["decision"],
            "blocking_dimensions": runtime_state["blocking_dimensions"],
            "advisory_dimensions": runtime_state["advisory_dimensions"],
            "first_fix_priority": runtime_state["first_fix_priority"],
            "rewrite_scope": runtime_state["rewrite_scope"],
            "return_to": runtime_state["return_to"],
            "blocking_reasons": runtime_state["blocking_reasons"],
            "must_change": runtime_state["must_change"],
            "recheck_order": runtime_state["recheck_order"],
            "blocking_digest": runtime_state["blocking_digest"],
            "advisory_digest": runtime_state["advisory_digest"],
            "cycle_count": runtime_state["cycle_count"],
            "last_cycle_decision": runtime_state["last_cycle_decision"],
            "character_alignment_status": character_verdict["status"],
            "character_alignment_evidence": character_verdict["evidence"],
            "plan_status": "pass" if str(plan_json.get("hook", "")).strip() and int(plan_json.get("targetWords", 0) or 0) > 0 else "warn",
            "foreshadow_overdue_count": overdue_count,
            "arc_stalled_count": int(load_json(reports_dir / "arc_health.json").get("stalled_arc_count", 0) or 0),
            "applied_targets": apply_summary["applied_targets"],
            "ready_targets": apply_summary["ready_targets"],
            "skipped_targets": apply_summary["skipped_targets"],
        },
        "warnings": warnings,
        "warning_count": len(warnings),
        "report_paths": {
            "next_context": (retrieval_dir / "next_context.md").as_posix(),
            "memory_sync_queue": (retrieval_dir / "memory_sync_queue.md").as_posix(),
            "memory_sync_patches": (retrieval_dir / "leadwriter_memory_patches.md").as_posix(),
            "memory_sync_apply": (retrieval_dir / "leadwriter_memory_apply.md").as_posix(),
            "markdown": (reports_dir / "dashboard.md").as_posix(),
            "json": (reports_dir / "dashboard.json").as_posix(),
        },
    }


def format_targets(targets: list[str]) -> str:
    return ", ".join(targets) if targets else "none"


def render_markdown(payload: dict[str, object]) -> str:
    runtime_signals = payload.get("runtime_signals", {})
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
            f"- memory_sync_apply：`{payload['report_paths']['memory_sync_apply']}`",
            f"- dashboard.json：`{payload['report_paths']['json']}`",
        ]
    )

    if isinstance(runtime_signals, dict):
        lines.extend(
            [
                "",
                "## Runtime Signals",
                f"- decision：`{runtime_signals.get('decision', 'unknown')}`",
                f"- blocking_dimensions：`{format_targets(list(runtime_signals.get('blocking_dimensions', [])) if isinstance(runtime_signals.get('blocking_dimensions'), list) else [])}`",
                f"- advisory_dimensions：`{format_targets(list(runtime_signals.get('advisory_dimensions', [])) if isinstance(runtime_signals.get('advisory_dimensions'), list) else [])}`",
                f"- first_fix_priority：`{runtime_signals.get('first_fix_priority', '') or 'none'}`",
                f"- rewrite_scope：`{runtime_signals.get('rewrite_scope', '') or 'none'}`",
                f"- return_to：`{runtime_signals.get('return_to', '') or 'none'}`",
                f"- cycle_count：`{runtime_signals.get('cycle_count', 0)}`",
                f"- last_cycle_decision：`{runtime_signals.get('last_cycle_decision', 'unknown')}`",
                f"- blocking_digest：`{format_targets(list(runtime_signals.get('blocking_digest', [])) if isinstance(runtime_signals.get('blocking_digest'), list) else [])}`",
                f"- advisory_digest：`{format_targets(list(runtime_signals.get('advisory_digest', [])) if isinstance(runtime_signals.get('advisory_digest'), list) else [])}`",
                f"- must_change：`{format_targets(list(runtime_signals.get('must_change', [])) if isinstance(runtime_signals.get('must_change'), list) else [])}`",
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
