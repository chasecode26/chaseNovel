#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


STEP_MAP = {
    "doctor": "project_doctor.py",
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
        default="doctor,context,memory,foreshadow,arc,timeline,repeat,dashboard",
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
    parsed: dict[str, object] | None = None
    stdout = completed.stdout.strip()
    if stdout:
        try:
            candidate = json.loads(stdout)
            if isinstance(candidate, dict):
                parsed = candidate
        except json.JSONDecodeError:
            parsed = None
    payload: dict[str, object] = {
        "step": step,
        "returncode": completed.returncode,
        "stderr": completed.stderr.strip(),
        "status": (parsed or {}).get("status", "pass" if completed.returncode == 0 else "fail"),
        "warning_count": (parsed or {}).get("warning_count", 0),
        "warnings": (parsed or {}).get("warnings", []),
        "report_paths": (parsed or {}).get("report_paths", {}),
    }
    if parsed is not None:
        payload["summary"] = {
            key: value
            for key, value in parsed.items()
            if key not in {"warnings", "warning_count", "status", "report_paths"}
        }
    elif stdout:
        payload["stdout"] = stdout
    return payload


def summarize_status(steps: list[dict[str, object]], failed_count: int) -> str:
    if failed_count:
        return "fail"
    if any(item.get("status") == "warn" for item in steps):
        return "warn"
    return "pass"


def collect_pipeline_warnings(steps: list[dict[str, object]]) -> list[str]:
    warnings: list[str] = []
    for item in steps:
        for warning in item.get("warnings", []):
            warnings.append(f"{item['step']}: {warning}")
    return warnings


def collect_report_paths(steps: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    report_paths: dict[str, dict[str, object]] = {}
    for item in steps:
        paths = item.get("report_paths")
        if isinstance(paths, dict):
            report_paths[str(item["step"])] = paths
    return report_paths


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# 流水线汇总报告",
        "",
        f"- 项目：`{payload['project']}`",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 总体状态：`{payload['status'].upper()}`",
        f"- 失败步骤数：`{payload['failed']}`",
        f"- 预警数：`{payload['warning_count']}`",
        "",
        "## 步骤结果",
    ]
    for item in payload["steps"]:
        lines.append(f"- `{item['step']}` -> rc={item['returncode']} / status={item['status']} / warnings={item['warning_count']}")
    lines.extend(["", "## 预警"])
    warnings = payload.get("warnings", [])
    if warnings:
        lines.extend([f"- {warning}" for warning in warnings])
    else:
        lines.append("- 无")
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    project_dir = Path(args.project).resolve()
    steps = [item.strip() for item in args.steps.split(",") if item.strip()]
    invalid_steps = [item for item in steps if item not in STEP_MAP]
    if invalid_steps:
        payload = {
            "project": project_dir.as_posix(),
            "steps": [],
            "failed": len(invalid_steps),
            "error": f"unknown steps: {', '.join(invalid_steps)}",
            "available_steps": list(STEP_MAP),
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(payload["error"])
            print("available=" + ",".join(payload["available_steps"]))
        return 1
    results = [run_step(repo_root, step, project_dir, args.chapter, args.dry_run) for step in steps]
    failed = [item for item in results if int(item["returncode"]) != 0]
    report_dir = project_dir / "05_reports"
    payload = {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "steps": results,
        "failed": len(failed),
        "status": summarize_status(results, len(failed)),
        "warnings": collect_pipeline_warnings(results),
        "warning_count": 0,
        "report_paths": {
            "markdown": (report_dir / "pipeline_report.md").as_posix(),
            "json": (report_dir / "pipeline_report.json").as_posix(),
        },
        "step_reports": collect_report_paths(results),
    }
    payload["warning_count"] = len(payload["warnings"])
    if not args.dry_run:
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / "pipeline_report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        (report_dir / "pipeline_report.md").write_text(render_markdown(payload), encoding="utf-8")
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"failed={len(failed)}")
        print(f"warning_count={payload['warning_count']}")
        for item in results:
            print(f"{item['step']}={item['returncode']}")
        print(f"report={payload['report_paths']['markdown']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
