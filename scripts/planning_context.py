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

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run planning review plus next-context compilation as one step.")
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--chapter", type=int, help="Target chapter number")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    return parser.parse_args()

def main() -> int:
    configure_utf8_stdio()
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    shared = ["--project", args.project]
    if args.chapter is not None:
        shared.extend(["--chapter", str(args.chapter)])
    if args.dry_run:
        shared.append("--dry-run")

    steps = run_step_specs(
        repo_root,
        [
            ("chapter_planning_review.py", shared),
            ("context_compiler.py", shared),
        ],
    )
    payload = build_aggregate_payload(project=args.project, steps=steps)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"warning_count={payload['warning_count']}")
    return 0 if payload["status"] != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
