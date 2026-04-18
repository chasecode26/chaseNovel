#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from pathlib import Path

from aggregation_utils import (
    build_aggregate_payload,
    configure_utf8_stdio,
    run_step_specs,
    write_aggregate_reports,
)


SCRIPT_BY_FOCUS = {
    "dashboard": "dashboard_snapshot.py",
    "foreshadow": "foreshadow_scheduler.py",
    "arc": "arc_tracker.py",
    "timeline": "timeline_check.py",
    "repeat": "anti_repeat_scan.py",
}


def build_runtime_signals(steps: list[dict[str, object]], focus: str) -> dict[str, object]:
    dashboard_step = next((item for item in steps if item.get("script") == "dashboard_snapshot.py"), None)
    dashboard_runtime = dashboard_step.get("runtime_signals", {}) if isinstance(dashboard_step, dict) else {}
    blocking_dimensions = dashboard_runtime.get("blocking_dimensions", [])
    advisory_dimensions = dashboard_runtime.get("advisory_dimensions", [])
    character_alignment_status = str(dashboard_runtime.get("character_alignment_status", "unknown"))
    character_alignment_evidence = dashboard_runtime.get("character_alignment_evidence", [])
    plan_status = str(dashboard_runtime.get("plan_status", "unknown"))
    foreshadow_overdue_count = int(dashboard_runtime.get("foreshadow_overdue_count", 0) or 0)
    arc_stalled_count = int(dashboard_runtime.get("arc_stalled_count", 0) or 0)
    applied_targets = dashboard_runtime.get("applied_targets", [])
    ready_targets = dashboard_runtime.get("ready_targets", [])
    skipped_targets = dashboard_runtime.get("skipped_targets", [])
    attention_queue: list[str] = []
    if isinstance(blocking_dimensions, list):
        attention_queue.extend(f"runtime blocking: {item}" for item in blocking_dimensions if str(item).strip())
    if isinstance(advisory_dimensions, list):
        attention_queue.extend(f"runtime advisory: {item}" for item in advisory_dimensions if str(item).strip())
    if character_alignment_status != "pass":
        if isinstance(character_alignment_evidence, list) and character_alignment_evidence:
            attention_queue.extend(f"character alignment: {item}" for item in character_alignment_evidence if str(item).strip())
        elif character_alignment_status != "unknown":
            attention_queue.append(f"character alignment: {character_alignment_status}")
    if plan_status == "warn":
        attention_queue.append("plan alignment: plan schema 仍有缺口")
    if foreshadow_overdue_count > 0:
        attention_queue.append(f"foreshadow overdue: {foreshadow_overdue_count}")
    if arc_stalled_count > 0:
        attention_queue.append(f"arc stalled: {arc_stalled_count}")
    for step in steps:
        warnings = step.get("warnings", [])
        if isinstance(warnings, list):
            attention_queue.extend(str(item) for item in warnings if str(item).strip())
    deduped_attention: list[str] = []
    seen: set[str] = set()
    for item in attention_queue:
        if item in seen:
            continue
        seen.add(item)
        deduped_attention.append(item)
    return {
        "decision": str(dashboard_runtime.get("decision", "unknown")),
        "blocking_dimensions": [str(item) for item in blocking_dimensions] if isinstance(blocking_dimensions, list) else [],
        "advisory_dimensions": [str(item) for item in advisory_dimensions] if isinstance(advisory_dimensions, list) else [],
        "character_alignment_status": character_alignment_status,
        "character_alignment_evidence": [str(item) for item in character_alignment_evidence] if isinstance(character_alignment_evidence, list) else [],
        "plan_status": plan_status,
        "foreshadow_overdue_count": foreshadow_overdue_count,
        "arc_stalled_count": arc_stalled_count,
        "applied_targets": [str(item) for item in applied_targets] if isinstance(applied_targets, list) else [],
        "ready_targets": [str(item) for item in ready_targets] if isinstance(ready_targets, list) else [],
        "skipped_targets": [str(item) for item in skipped_targets] if isinstance(skipped_targets, list) else [],
        "attention_queue": deduped_attention,
        "focus": focus,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate book-level health checks into one status command.")
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--chapter", type=int, help="Reference chapter number for foreshadow status")
    parser.add_argument(
        "--focus",
        choices=["all", "dashboard", "foreshadow", "arc", "timeline", "repeat"],
        default="all",
        help="Run all book-health checks or a single focus area",
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    return parser.parse_args()

def main() -> int:
    configure_utf8_stdio()
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    focuses = list(SCRIPT_BY_FOCUS) if args.focus == "all" else [args.focus]
    step_specs: list[tuple[str, list[str]]] = []
    for focus in focuses:
        extra_args = ["--project", args.project]
        if args.dry_run:
            extra_args.append("--dry-run")
        if focus == "foreshadow" and args.chapter is not None:
            extra_args.extend(["--chapter", str(args.chapter)])
        step_specs.append((SCRIPT_BY_FOCUS[focus], extra_args))
    steps = run_step_specs(repo_root, step_specs)

    payload = build_aggregate_payload(project=args.project, steps=steps, extra_fields={"focus": args.focus})
    payload["runtime_signals"] = build_runtime_signals(steps, args.focus)
    project_dir = Path(args.project).resolve()
    payload["report_paths"] = {
        **payload.get("report_paths", {}),
        **({} if args.dry_run else write_aggregate_reports(
            project_dir,
            payload,
            base_name="book_health_report",
            heading="书级健康汇总报告",
            mode_line=f"- 聚焦范围：`{args.focus}`",
        )),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"focus={payload['focus']}")
        print(f"warning_count={payload['warning_count']}")
        if isinstance(payload.get("report_paths"), dict) and payload["report_paths"].get("markdown"):
            print(f"report={payload['report_paths']['markdown']}")
    return 0 if payload["status"] != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
