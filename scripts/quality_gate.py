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
    parser = argparse.ArgumentParser(description="Run draft / chapter / language gates as one quality step.")
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument(
        "--check",
        choices=["all", "chapter", "draft", "language", "batch"],
        default="all",
        help="Quality sub-check to run; defaults to all chapter-level checks",
    )
    parser.add_argument("--chapter-no", type=int, help="Target chapter number")
    parser.add_argument("--from", dest="chapter_from", type=int, help="Batch start chapter")
    parser.add_argument("--to", dest="chapter_to", type=int, help="Batch end chapter")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    return parser.parse_args()

def main() -> int:
    configure_utf8_stdio()
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    shared = ["--project", args.project]
    if args.dry_run:
        shared.append("--dry-run")

    if args.check == "batch" or args.chapter_from is not None or args.chapter_to is not None:
        batch_args = shared[:]
        if args.chapter_from is not None:
            batch_args.extend(["--from", str(args.chapter_from)])
        if args.chapter_to is not None:
            batch_args.extend(["--to", str(args.chapter_to)])
        step_specs = [("batch_gate.py", batch_args)]
    else:
        if args.chapter_no is None:
            raise SystemExit("--chapter-no is required unless running batch mode")
        chapter_args = [*shared, "--chapter-no", str(args.chapter_no)]
        if args.check == "chapter":
            step_specs = [("chapter_gate.py", chapter_args)]
        elif args.check == "draft":
            step_specs = [("draft_gate.py", chapter_args)]
        elif args.check == "language":
            step_specs = [("language_audit.py", chapter_args)]
        else:
            step_specs = [
                ("chapter_gate.py", chapter_args),
                ("draft_gate.py", chapter_args),
                ("language_audit.py", chapter_args),
            ]
    steps = run_step_specs(repo_root, step_specs)

    payload = build_aggregate_payload(project=args.project, steps=steps, extra_fields={"check": args.check})
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"warning_count={payload['warning_count']}")
    return 0 if payload["status"] != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
