#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from pathlib import Path

from aggregation_utils import (
    build_aggregate_payload,
    configure_utf8_stdio,
    run_step_specs,
)


SCRIPT_BY_FOCUS = {
    "dashboard": "dashboard_snapshot.py",
    "foreshadow": "foreshadow_scheduler.py",
    "arc": "arc_tracker.py",
    "timeline": "timeline_check.py",
    "repeat": "anti_repeat_scan.py",
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
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"focus={payload['focus']}")
        print(f"warning_count={payload['warning_count']}")
    return 0 if payload["status"] != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
