#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


STEP_MAP = {
    "context": "context_compiler.py",
    "memory": "memory_update.py",
    "foreshadow": "foreshadow_scheduler.py",
    "arc": "arc_tracker.py",
    "timeline": "timeline_check.py",
    "repeat": "anti_repeat_scan.py",
    "dashboard": "dashboard_snapshot.py",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a local chaseNovel workflow sequence."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--chapter", type=int, help="Target chapter number")
    parser.add_argument(
        "--steps",
        default="context,memory,foreshadow,arc,timeline,repeat,dashboard",
        help="Comma-separated workflow steps",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Pass dry-run to supported steps")
    return parser.parse_args()


def run_step(repo_root: Path, step: str, project: Path, chapter: int | None, dry_run: bool) -> dict[str, object]:
    script_name = STEP_MAP[step]
    command = [sys.executable, str(repo_root / "scripts" / script_name), "--project", project.as_posix(), "--json"]
    if chapter is not None and step in {"context", "memory", "foreshadow"}:
        command.extend(["--chapter", str(chapter)])
    if dry_run:
        command.append("--dry-run")
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    payload: dict[str, object] = {
        "step": step,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }
    return payload


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    project_dir = Path(args.project).resolve()
    steps = [item.strip() for item in args.steps.split(",") if item.strip()]
    results = [run_step(repo_root, step, project_dir, args.chapter, args.dry_run) for step in steps]
    failed = [item for item in results if int(item["returncode"]) != 0]
    payload = {
        "project": project_dir.as_posix(),
        "steps": results,
        "failed": len(failed),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"failed={len(failed)}")
        for item in results:
            print(f"{item['step']}={item['returncode']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
