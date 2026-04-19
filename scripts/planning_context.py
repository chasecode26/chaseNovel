#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from aggregation_utils import (
    build_aggregate_payload,
    configure_utf8_stdio,
    get_step_by_script,
    run_step_specs,
)


def enrich_planning_payload(payload: dict[str, object]) -> dict[str, object]:
    steps = payload.get("steps", [])
    if not isinstance(steps, list):
        return payload

    planning_step = get_step_by_script(steps, "chapter_planning_review.py")
    context_step = get_step_by_script(steps, "context_compiler.py")
    target_chapter = int(planning_step.get("target_chapter") or context_step.get("chapter") or 0)
    planning_status = str(planning_step.get("status", "missing")).strip()
    planning_verdict = str(planning_step.get("planning_verdict", "missing")).strip()
    planning_blockers = [str(item) for item in planning_step.get("blockers", []) if str(item).strip()]
    planning_warnings = [str(item) for item in planning_step.get("warnings", []) if str(item).strip()]
    context_warnings = [str(item) for item in context_step.get("warnings", []) if str(item).strip()]
    context_failed = str(context_step.get("status", "pass")).strip() == "fail"
    blocking = bool(planning_blockers) or planning_status == "fail" or context_failed
    write_ready = planning_verdict == "pass" and not blocking

    if blocking:
        readiness_summary = "不可写，需先清理 planning blockers。"
    elif str(payload.get("status", "pass")).strip() == "warn":
        readiness_summary = "可写，但建议先补强 planning/context 预警。"
    else:
        readiness_summary = "可写，可直接进入正文规划。"

    payload.update(
        {
            "target_chapter": target_chapter,
            "planning_status": planning_status,
            "planning_verdict": planning_verdict,
            "planning_blockers": planning_blockers,
            "planning_warnings": planning_warnings,
            "context_warnings": context_warnings,
            "blocking": "yes" if blocking else "no",
            "write_ready": "yes" if write_ready else "no",
            "readiness_summary": readiness_summary,
            "warning_sources": {
                "chapter_planning_review.py": len(planning_warnings),
                "context_compiler.py": len(context_warnings),
            },
        }
    )
    return payload

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run planning review plus next-context compilation as one step.")
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument(
        "--chapter",
        type=int,
        help="Existing drafted current chapter number. Planning/context targets the next chapter by default.",
    )
    parser.add_argument("--target-chapter", type=int, help="Explicit target chapter number")
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
    if args.target_chapter is not None:
        shared.extend(["--target-chapter", str(args.target_chapter)])
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
    payload = enrich_planning_payload(payload)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"target_chapter={payload['target_chapter']}")
        print(f"write_ready={payload['write_ready']}")
        print(f"warning_count={payload['warning_count']}")
    return 0 if payload["status"] != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
