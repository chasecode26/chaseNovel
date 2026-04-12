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
    "planning": "chapter_planning_review.py",
    "draft": "draft_gate.py",
    "memory": "memory_update.py",
    "foreshadow": "foreshadow_scheduler.py",
    "arc": "arc_tracker.py",
    "timeline": "timeline_check.py",
    "repeat": "anti_repeat_scan.py",
    "volume": "volume_audit.py",
    "milestone": "milestone_audit.py",
    "dashboard": "dashboard_snapshot.py",
}

CHANGE_LABELS = {
    "promise_threshold": "承诺阈值",
    "overdue_foreshadow_threshold": "伏笔阈值",
    "stalled_arc_threshold": "停滞阈值",
    "repeat_warning_threshold": "重复阈值",
    "checkpoint_words": "节点字数",
    "due_soon_window": "预警窗口",
}

DIGEST_PRIORITY = {
    "repeat_warning_threshold": 6,
    "stalled_arc_threshold": 5,
    "promise_threshold": 5,
    "overdue_foreshadow_threshold": 4,
    "checkpoint_words": 4,
    "due_soon_window": 3,
}

HEALTH_DIGEST_LIMIT = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a local chaseNovel workflow sequence. When --chapter is set, pass the number of an already existing drafted chapter, not the next chapter you plan to write."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument(
        "--chapter",
        type=int,
        help="Existing drafted chapter number for context/memory/foreshadow steps. Do not pass the next unwritten chapter here.",
    )
    parser.add_argument(
        "--steps",
        default="doctor,context,planning,draft,memory,foreshadow,arc,timeline,repeat,volume,milestone,dashboard",
        help="Comma-separated workflow steps",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Pass dry-run to supported steps")
    return parser.parse_args()


def run_step(repo_root: Path, step: str, project: Path, chapter: int | None, dry_run: bool) -> dict[str, object]:
    script_name = STEP_MAP[step]
    command = [sys.executable, str(repo_root / "scripts" / script_name), "--project", project.as_posix(), "--json"]
    if chapter is not None and step in {"draft", "context", "memory", "foreshadow"}:
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
        "blocking": (parsed or {}).get("blocking", "yes" if completed.returncode != 0 else "no"),
        "blocker_count": (parsed or {}).get("blocker_count", len((parsed or {}).get("blockers", []))),
        "return_to": (parsed or {}).get("return_to", ""),
        "recheck_order": (parsed or {}).get("recheck_order", ""),
        "final_release": (parsed or {}).get(
            "final_release",
            (parsed or {}).get("script_final_release", (parsed or {}).get("planning_verdict", "")),
        ),
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
    if failed_count or any(item.get("blocking") == "yes" for item in steps):
        return "fail"
    if any(item.get("status") == "warn" or item.get("final_release") == "revise" for item in steps):
        return "warn"
    return "pass"


def collect_pipeline_warnings(steps: list[dict[str, object]]) -> list[str]:
    warnings: list[str] = []
    for item in steps:
        for warning in item.get("warnings", []):
            warnings.append(f"{item['step']}: {warning}")
    return warnings


def collect_pipeline_blockers(steps: list[dict[str, object]]) -> list[str]:
    blockers: list[str] = []
    for item in steps:
        if item.get("blocking") == "yes":
            return_to = item.get("return_to") or "unknown"
            recheck_order = item.get("recheck_order") or "unknown"
            blockers.append(f"{item['step']}: blocking=yes -> return_to={return_to} -> recheck={recheck_order}")
    return blockers


def collect_report_paths(steps: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    report_paths: dict[str, dict[str, object]] = {}
    for item in steps:
        paths = item.get("report_paths")
        if isinstance(paths, dict):
            report_paths[str(item["step"])] = paths
    return report_paths


def collect_dynamic_thresholds(steps: list[dict[str, object]]) -> list[dict[str, object]]:
    digest: list[dict[str, object]] = []
    for item in steps:
        summary = item.get("summary")
        if not isinstance(summary, dict):
            continue
        adjustments = summary.get("dynamic_adjustments")
        if not isinstance(adjustments, dict) or not adjustments:
            continue

        changes: list[dict[str, object]] = []
        for key, value in adjustments.items():
            if not isinstance(value, dict):
                continue
            base = value.get("base")
            effective = value.get("effective")
            if base is None or effective is None:
                continue
            changes.append(
                {
                    "key": key,
                    "base": base,
                    "effective": effective,
                    "delta": int(value.get("delta", 0) or 0),
                    "reasons": value.get("reasons", []),
                }
            )

        if changes:
            changes.sort(key=lambda change: (DIGEST_PRIORITY.get(str(change["key"]), 1), abs(int(change["delta"]))), reverse=True)
            digest.append(
                {
                    "step": item["step"],
                    "genre": summary.get("genre", ""),
                    "subgenre": summary.get("subgenre", ""),
                    "changes": changes,
                }
            )
    return digest


def build_health_digest(dynamic_thresholds: list[dict[str, object]], warnings: list[str]) -> list[str]:
    ranked_groups: list[tuple[int, str]] = []
    for item in dynamic_thresholds:
        step = str(item.get("step", "unknown"))
        genre = str(item.get("genre", "") or "")
        subgenre = str(item.get("subgenre", "") or "未识别")
        merged_changes: list[str] = []
        score = 0
        for change in item.get("changes", []):
            key = str(change.get("key", ""))
            base = change.get("base")
            effective = change.get("effective")
            delta = int(change.get("delta", 0) or 0)
            if base is None or effective is None:
                continue
            merged_changes.append(f"{CHANGE_LABELS.get(key, key)} {base}->{effective}")
            score += DIGEST_PRIORITY.get(key, 1) + abs(delta)
        if merged_changes:
            ranked_groups.append((score, f"{step}: {genre}/{subgenre} " + "；".join(merged_changes)))

    ranked_groups.sort(key=lambda item: item[0], reverse=True)
    digest = [text for _, text in ranked_groups[:HEALTH_DIGEST_LIMIT]]
    if len(digest) >= HEALTH_DIGEST_LIMIT:
        return digest

    for warning in warnings:
        digest.append(warning)
        if len(digest) >= HEALTH_DIGEST_LIMIT:
            break
    return digest


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Pipeline Report",
        "",
        f"- project: `{payload['project']}`",
        f"- generated_at: `{payload['generated_at']}`",
        f"- overall_status: `{payload['status'].upper()}`",
        f"- failed_steps: `{payload['failed']}`",
        f"- blocking_steps: `{payload['blocking_count']}`",
        f"- warning_count: `{payload['warning_count']}`",
        "",
        "## Step Results",
    ]
    for item in payload["steps"]:
        lines.append(
            f"- `{item['step']}` -> rc={item['returncode']} / status={item['status']} / blocking={item['blocking']} / final={item.get('final_release', '') or 'n/a'} / warnings={item['warning_count']}"
        )

    lines.extend(["", "## Dynamic Thresholds"])
    dynamic_thresholds = payload.get("dynamic_thresholds", [])
    if dynamic_thresholds:
        for item in dynamic_thresholds:
            title = f"{item['step']} ({item.get('genre') or 'unknown'} / {item.get('subgenre') or '未识别'})"
            lines.append(f"- {title}")
            for change in item.get("changes", []):
                reasons = "；".join(change.get("reasons", [])) or "no reason"
                lines.append(
                    f"  - {change['key']}: {change['base']} -> {change['effective']} ({change.get('delta', 0):+}) / {reasons}"
                )
    else:
        lines.append("- none")

    lines.extend(["", "## Health Digest"])
    health_digest = payload.get("health_digest", [])
    if health_digest:
        lines.extend([f"- {item}" for item in health_digest])
    else:
        lines.append("- none")

    lines.extend(["", "## Warnings"])
    warnings = payload.get("warnings", [])
    if warnings:
        lines.extend([f"- {warning}" for warning in warnings])
    else:
        lines.append("- none")

    lines.extend(["", "## Blockers"])
    blockers = payload.get("blockers", [])
    if blockers:
        lines.extend([f"- {blocker}" for blocker in blockers])
    else:
        lines.append("- none")
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
    dynamic_thresholds = collect_dynamic_thresholds(results)
    payload = {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "steps": results,
        "failed": len(failed),
        "status": summarize_status(results, len(failed)),
        "blockers": collect_pipeline_blockers(results),
        "blocking_count": 0,
        "warnings": collect_pipeline_warnings(results),
        "warning_count": 0,
        "report_paths": {
            "markdown": (report_dir / "pipeline_report.md").as_posix(),
            "json": (report_dir / "pipeline_report.json").as_posix(),
        },
        "step_reports": collect_report_paths(results),
        "dynamic_thresholds": dynamic_thresholds,
        "health_digest": [],
    }
    payload["blocking_count"] = len(payload["blockers"])
    payload["warning_count"] = len(payload["warnings"])
    payload["health_digest"] = build_health_digest(dynamic_thresholds, payload["warnings"])

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
        for item in payload["dynamic_thresholds"]:
            changes = ",".join(
                f"{change['key']}:{change['base']}->{change['effective']}"
                for change in item.get("changes", [])
            )
            print(f"dynamic.{item['step']}={changes or 'none'}")
        for index, item in enumerate(payload["health_digest"], start=1):
            print(f"digest.{index}={item}")
        print(f"report={payload['report_paths']['markdown']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
