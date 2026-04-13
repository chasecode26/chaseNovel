#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


def configure_utf8_stdio() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def run_script_json(repo_root: Path, script_name: str, extra_args: list[str]) -> dict[str, object]:
    script_path = repo_root / "scripts" / script_name
    completed = subprocess.run(
        [sys.executable, str(script_path), *extra_args, "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    payload: dict[str, object] = {
        "script": script_name,
        "returncode": completed.returncode,
        "status": "fail" if completed.returncode else "pass",
        "stderr": (completed.stderr or "").strip(),
    }
    stdout = (completed.stdout or "").strip()
    if stdout:
        try:
            parsed = json.loads(stdout)
            if isinstance(parsed, dict):
                payload.update(parsed)
        except json.JSONDecodeError:
            payload["stdout"] = stdout
    if payload["status"] == "fail":
        stderr = str(payload.get("stderr", "")).strip()
        if stderr and "Traceback" in stderr:
            lines = [line.strip() for line in stderr.splitlines() if line.strip()]
            last_line = lines[-1] if lines else stderr
            match = re.search(r"(?:ValueError|RuntimeError|Exception):\s*(.+)", last_line)
            payload["stderr"] = match.group(1) if match else last_line
    return payload


def summarize_statuses(statuses: list[str]) -> str:
    if any(item == "fail" for item in statuses):
        return "fail"
    if any(item == "warn" for item in statuses):
        return "warn"
    return "pass"


def collect_step_warnings(steps: list[dict[str, object]]) -> list[str]:
    warnings: list[str] = []
    for step in steps:
        warnings.extend(step.get("warnings", []) if isinstance(step.get("warnings"), list) else [])
    return warnings


def collect_step_report_paths(steps: list[dict[str, object]], key_field: str = "script") -> dict[str, object]:
    report_paths: dict[str, object] = {}
    for step in steps:
        if isinstance(step.get("report_paths"), dict):
            report_paths[str(step[key_field])] = step["report_paths"]
    return report_paths


def run_step_specs(
    repo_root: Path,
    step_specs: list[tuple[str, list[str]]],
) -> list[dict[str, object]]:
    return [run_script_json(repo_root, script_name, extra_args) for script_name, extra_args in step_specs]


def build_aggregate_payload(
    *,
    project: str,
    steps: list[dict[str, object]],
    extra_fields: dict[str, object] | None = None,
    key_field: str = "script",
) -> dict[str, object]:
    warnings = collect_step_warnings(steps)
    payload: dict[str, object] = {
        "project": project,
        "status": summarize_statuses([str(step.get("status", "pass")) for step in steps]),
        "warning_count": len(warnings),
        "warnings": warnings,
        "report_paths": collect_step_report_paths(steps, key_field=key_field),
        "steps": steps,
    }
    if extra_fields:
        payload.update(extra_fields)
    return payload
