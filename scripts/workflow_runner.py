#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from aggregation_utils import configure_utf8_stdio, run_script_json
from runtime.runtime_orchestrator import LeadWriterRuntime

# Shell role: orchestrates shipped workflow steps and normalizes aggregate output.
# Keep domain verdict rules in runtime/ and analyzer scripts, not in this entry layer.
STEP_MAP = {
    "open": "open_book.py",
    "runtime": None,
    "quality": "quality_gate.py",
    "status": "book_health.py",
    "settings": "settings_consistency.py",
    "knowledge": "knowledge_boundary_check.py",
    "resources": "resource_tracker.py",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a local chaseNovel workflow sequence with explicit reference/target chapter semantics."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument(
        "--chapter",
        type=int,
        help="Existing drafted reference chapter number. Open targets the next chapter by default.",
    )
    parser.add_argument("--target-chapter", type=int, help="Explicit target chapter number for open steps")
    parser.add_argument(
        "--steps",
        default="open,runtime,quality,status",
        help="Comma-separated workflow steps",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Pass dry-run to supported steps")
    return parser.parse_args()


def resolve_target_chapter(reference_chapter: int | None, explicit_target: int | None) -> int | None:
    if explicit_target is not None:
        return explicit_target
    if reference_chapter is not None:
        return reference_chapter + 1
    return None


def run_step(
    repo_root: Path,
    step: str,
    project: Path,
    reference_chapter: int | None,
    target_chapter: int | None,
    dry_run: bool,
) -> dict[str, object]:
    if step == "runtime":
        runtime_chapter = reference_chapter or 0
        runtime_payload = LeadWriterRuntime().run(project, runtime_chapter, dry_run=dry_run)
        return {
            "step": "runtime",
            "returncode": 0,
            "stderr": "",
            "status": runtime_payload.get("status", "pass"),
            "warning_count": len(runtime_payload.get("context", {}).get("warnings", [])),
            "warnings": runtime_payload.get("context", {}).get("warnings", []),
            "report_paths": runtime_payload.get("report_paths", {}),
            "reference_chapter": runtime_chapter,
            "summary": runtime_payload,
        }
    script_name = STEP_MAP[step]
    command = ["--project", project.as_posix()]
    if step == "open":
        if reference_chapter is not None:
            command.extend(["--chapter", str(reference_chapter)])
        if target_chapter is not None:
            command.extend(["--target-chapter", str(target_chapter)])
    elif step == "quality" and reference_chapter is not None:
        command.extend(["--chapter-no", str(reference_chapter)])
    elif step == "status" and reference_chapter is not None:
        command.extend(["--chapter", str(reference_chapter)])
    elif step in {"settings", "knowledge", "resources"}:
        if reference_chapter is not None:
            command.extend(["--from-chapter", "1", "--to-chapter", str(reference_chapter)])
    if dry_run:
        command.append("--dry-run")
    parsed = run_script_json(repo_root, script_name, command)
    payload: dict[str, object] = {
        "step": step,
        "returncode": int(parsed.get("returncode", 0)),
        "stderr": str(parsed.get("stderr", "")).strip(),
        "status": parsed.get("status", "pass"),
        "warning_count": parsed.get("warning_count", 0),
        "warnings": parsed.get("warnings", []),
        "report_paths": parsed.get("report_paths", {}),
    }
    if step == "open":
        payload["reference_chapter"] = reference_chapter
        payload["target_chapter"] = target_chapter
    elif step in {"runtime", "quality", "status", "settings", "knowledge", "resources"}:
        payload["reference_chapter"] = reference_chapter
    payload["summary"] = {
        key: value
        for key, value in parsed.items()
        if key not in {"script", "returncode", "stderr", "stdout", "warnings", "warning_count", "status", "report_paths"}
    }
    if "stdout" in parsed:
        payload["stdout"] = parsed["stdout"]
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


def find_step(steps: list[dict[str, object]], step_name: str) -> dict[str, object]:
    for item in steps:
        if str(item.get("step", "")).strip() == step_name:
            return item
    return {}


def to_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def has_meaningful_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, dict):
        return len(value) > 0
    return True


def build_normalized_step_fields(step: dict[str, object]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    summary = step.get("summary", {})
    if not isinstance(summary, dict):
        return normalized

    step_name = str(step.get("step", "")).strip()
    if step_name == "open":
        normalized.update(
            {
                "target_chapter": summary.get("target_chapter"),
                "planning_status": str(summary.get("planning_status", "")).strip(),
                "planning_verdict": str(summary.get("planning_verdict", "")).strip(),
                "planning_blockers": to_string_list(summary.get("planning_blockers", [])),
                "planning_warnings": to_string_list(summary.get("planning_warnings", [])),
                "context_warnings": to_string_list(summary.get("context_warnings", [])),
                "blocking": str(summary.get("blocking", "")).strip(),
                "write_ready": str(summary.get("write_ready", "")).strip(),
                "readiness_summary": str(summary.get("readiness_summary", "")).strip(),
            }
        )
    elif step_name == "quality":
        normalized.update(
            {
                "final_release": str(summary.get("final_release", "")).strip(),
                "blocking_dimensions": to_string_list(summary.get("blocking_dimensions", [])),
                "advisory_dimensions": to_string_list(summary.get("advisory_dimensions", [])),
                "runtime_verdict_source": str(summary.get("runtime_verdict_source", "")).strip(),
                "loaded_runtime_dimensions": to_string_list(summary.get("loaded_runtime_dimensions", [])),
                "fallback_runtime_dimensions": to_string_list(summary.get("fallback_runtime_dimensions", [])),
                "missing_runtime_dimensions": to_string_list(summary.get("missing_runtime_dimensions", [])),
                "verdicts": summary.get("verdicts", []),
            }
        )
    elif step_name == "runtime":
        decision = summary.get("decision", {})
        draft = summary.get("draft", {})
        if isinstance(decision, dict):
            normalized.update(
                {
                    "runtime_decision": str(decision.get("decision", "")).strip(),
                    "blocking_dimensions": to_string_list(decision.get("blocking_dimensions", [])),
                    "advisory_dimensions": to_string_list(decision.get("advisory_dimensions", [])),
                }
            )
        if isinstance(draft, dict):
            normalized["draft_status"] = str(draft.get("status", "")).strip()
    elif step_name == "status":
        runtime_signals = summary.get("runtime_signals", {})
        if isinstance(runtime_signals, dict):
            normalized.update(
                {
                    "runtime_decision": str(runtime_signals.get("decision", "")).strip(),
                    "blocking_dimensions": to_string_list(runtime_signals.get("blocking_dimensions", [])),
                    "advisory_dimensions": to_string_list(runtime_signals.get("advisory_dimensions", [])),
                    "attention_queue": to_string_list(runtime_signals.get("attention_queue", [])),
                }
            )
    elif step_name == "settings":
        normalized.update(
            {
                "settings_verdict": str(summary.get("verdict", "")).strip(),
                "settings_issue_count": int(summary.get("issue_count", 0)),
                "settings_chapters_scanned": int(summary.get("chapters_scanned", 0)),
            }
        )
    elif step_name == "knowledge":
        normalized.update(
            {
                "knowledge_verdict": str(summary.get("verdict", "")).strip(),
                "knowledge_issue_count": int(summary.get("issue_count", 0)),
                "knowledge_chapters_scanned": int(summary.get("chapters_scanned", 0)),
            }
        )
    elif step_name == "resources":
        normalized.update(
            {
                "resources_verdict": str(summary.get("verdict", "")).strip(),
                "resources_issue_count": int(summary.get("issue_count", 0)),
                "resources_chapters_scanned": int(summary.get("chapters_scanned", 0)),
            }
        )
    return {key: value for key, value in normalized.items() if has_meaningful_value(value)}


def enrich_steps_with_normalized_fields(steps: list[dict[str, object]]) -> list[dict[str, object]]:
    enriched: list[dict[str, object]] = []
    for item in steps:
        merged = dict(item)
        merged.update(build_normalized_step_fields(item))
        enriched.append(merged)
    return enriched


def build_pipeline_summary(results: list[dict[str, object]]) -> dict[str, object]:
    open_step = find_step(results, "open")
    quality_step = find_step(results, "quality")
    runtime_step = find_step(results, "runtime")
    status_step = find_step(results, "status")
    settings_step = find_step(results, "settings")
    knowledge_step = find_step(results, "knowledge")
    resources_step = find_step(results, "resources")

    summary: dict[str, object] = {
        "write_ready": str(open_step.get("write_ready", "")).strip(),
        "open_blocking": str(open_step.get("blocking", "")).strip(),
        "planning_verdict": str(open_step.get("planning_verdict", "")).strip(),
        "planning_status": str(open_step.get("planning_status", "")).strip(),
        "quality_final_release": str(quality_step.get("final_release", "")).strip(),
        "quality_runtime_verdict_source": str(quality_step.get("runtime_verdict_source", "")).strip(),
        "quality_loaded_runtime_dimensions": to_string_list(quality_step.get("loaded_runtime_dimensions", [])),
        "quality_fallback_runtime_dimensions": to_string_list(quality_step.get("fallback_runtime_dimensions", [])),
        "quality_missing_runtime_dimensions": to_string_list(quality_step.get("missing_runtime_dimensions", [])),
        "runtime_decision": str(runtime_step.get("runtime_decision", "")).strip(),
        "draft_status": str(runtime_step.get("draft_status", "")).strip(),
        "status_runtime_decision": str(status_step.get("runtime_decision", "")).strip(),
        "attention_queue": to_string_list(status_step.get("attention_queue", [])),
        "settings_verdict": str(settings_step.get("settings_verdict", "")).strip(),
        "settings_issue_count": settings_step.get("settings_issue_count", 0),
        "knowledge_verdict": str(knowledge_step.get("knowledge_verdict", "")).strip(),
        "knowledge_issue_count": knowledge_step.get("knowledge_issue_count", 0),
        "resources_verdict": str(resources_step.get("resources_verdict", "")).strip(),
        "resources_issue_count": resources_step.get("resources_issue_count", 0),
    }

    blocking_dimensions: list[str] = []
    advisory_dimensions: list[str] = []
    for step in results:
        blocking_dimensions.extend(to_string_list(step.get("blocking_dimensions", [])))
        advisory_dimensions.extend(to_string_list(step.get("advisory_dimensions", [])))

    dedup_blocking: list[str] = []
    seen_blocking: set[str] = set()
    for item in blocking_dimensions:
        if item in seen_blocking:
            continue
        seen_blocking.add(item)
        dedup_blocking.append(item)

    dedup_advisory: list[str] = []
    seen_advisory: set[str] = set()
    for item in advisory_dimensions:
        if item in seen_advisory:
            continue
        seen_advisory.add(item)
        dedup_advisory.append(item)

    summary["blocking_dimensions"] = dedup_blocking
    summary["advisory_dimensions"] = dedup_advisory
    summary["final_release"] = derive_pipeline_final_release(summary)
    return {key: value for key, value in summary.items() if has_meaningful_value(value)}


def derive_pipeline_final_release(summary: dict[str, object]) -> str:
    open_blocking = str(summary.get("open_blocking", "")).strip().lower()
    planning_verdict = str(summary.get("planning_verdict", "")).strip().lower()
    runtime_decision = str(summary.get("runtime_decision", "")).strip().lower()
    quality_final_release = str(summary.get("quality_final_release", "")).strip().lower()
    status_runtime_decision = str(summary.get("status_runtime_decision", "")).strip().lower()
    settings_verdict = str(summary.get("settings_verdict", "")).strip().lower()
    knowledge_verdict = str(summary.get("knowledge_verdict", "")).strip().lower()
    resources_verdict = str(summary.get("resources_verdict", "")).strip().lower()
    blocking_dimensions = to_string_list(summary.get("blocking_dimensions", []))

    if open_blocking == "yes":
        return "revise"
    if planning_verdict == "fail":
        return "revise"
    if runtime_decision in {"fail", "revise"}:
        return "revise"
    if quality_final_release == "revise":
        return "revise"
    if status_runtime_decision in {"fail", "revise"}:
        return "revise"
    for v in [settings_verdict, knowledge_verdict, resources_verdict]:
        if v == "rewrite":
            return "revise"
    if blocking_dimensions:
        return "revise"
    return "pass"


def render_markdown(payload: dict[str, object]) -> str:
    pipeline_summary = payload.get("pipeline_summary", {})
    if not isinstance(pipeline_summary, dict):
        pipeline_summary = {}

    lines = [
        "# Pipeline Report",
        "",
        f"- project: `{payload['project']}`",
        f"- generated_at: `{payload['generated_at']}`",
        f"- status: `{payload['status'].upper()}`",
        f"- final_release: `{payload.get('final_release', '') or 'n/a'}`",
        f"- failed_steps: `{payload['failed']}`",
        f"- warning_count: `{payload['warning_count']}`",
        "",
        "## Aggregate Summary",
    ]
    if pipeline_summary:
        if str(pipeline_summary.get("write_ready", "")).strip():
            lines.append(f"- write_ready=`{pipeline_summary['write_ready']}`")
        if str(pipeline_summary.get("open_blocking", "")).strip():
            lines.append(f"- open_blocking=`{pipeline_summary['open_blocking']}`")
        if str(pipeline_summary.get("planning_verdict", "")).strip():
            lines.append(f"- planning_verdict=`{pipeline_summary['planning_verdict']}`")
        if str(pipeline_summary.get("planning_status", "")).strip():
            lines.append(f"- planning_status=`{pipeline_summary['planning_status']}`")
        if str(pipeline_summary.get("runtime_decision", "")).strip():
            lines.append(f"- runtime_decision=`{pipeline_summary['runtime_decision']}`")
        if str(pipeline_summary.get("quality_final_release", "")).strip():
            lines.append(f"- quality_final_release=`{pipeline_summary['quality_final_release']}`")
        if str(pipeline_summary.get("quality_runtime_verdict_source", "")).strip():
            lines.append(
                f"- quality_runtime_verdict_source=`{pipeline_summary['quality_runtime_verdict_source']}`"
            )
        if str(pipeline_summary.get("final_release", "")).strip():
            lines.append(f"- final_release=`{pipeline_summary['final_release']}`")
        if str(pipeline_summary.get("status_runtime_decision", "")).strip():
            lines.append(f"- status_runtime_decision=`{pipeline_summary['status_runtime_decision']}`")
        if str(pipeline_summary.get("draft_status", "")).strip():
            lines.append(f"- draft_status=`{pipeline_summary['draft_status']}`")
        if str(pipeline_summary.get("settings_verdict", "")).strip():
            lines.append(f"- settings_verdict=`{pipeline_summary['settings_verdict']}` (issues={pipeline_summary.get('settings_issue_count', 0)})")
        if str(pipeline_summary.get("knowledge_verdict", "")).strip():
            lines.append(f"- knowledge_verdict=`{pipeline_summary['knowledge_verdict']}` (issues={pipeline_summary.get('knowledge_issue_count', 0)})")
        if str(pipeline_summary.get("resources_verdict", "")).strip():
            lines.append(f"- resources_verdict=`{pipeline_summary['resources_verdict']}` (issues={pipeline_summary.get('resources_issue_count', 0)})")

        blocking_dimensions = to_string_list(pipeline_summary.get("blocking_dimensions", []))
        advisory_dimensions = to_string_list(pipeline_summary.get("advisory_dimensions", []))
        attention_queue = to_string_list(pipeline_summary.get("attention_queue", []))
        if blocking_dimensions:
            lines.append(f"- blocking_dimensions=`{', '.join(blocking_dimensions)}`")
        if advisory_dimensions:
            lines.append(f"- advisory_dimensions=`{', '.join(advisory_dimensions)}`")
        quality_loaded_runtime_dimensions = to_string_list(pipeline_summary.get("quality_loaded_runtime_dimensions", []))
        quality_fallback_runtime_dimensions = to_string_list(
            pipeline_summary.get("quality_fallback_runtime_dimensions", [])
        )
        quality_missing_runtime_dimensions = to_string_list(pipeline_summary.get("quality_missing_runtime_dimensions", []))
        if quality_loaded_runtime_dimensions:
            lines.append(f"- quality_loaded_runtime_dimensions=`{', '.join(quality_loaded_runtime_dimensions)}`")
        if quality_fallback_runtime_dimensions:
            lines.append(
                f"- quality_fallback_runtime_dimensions=`{', '.join(quality_fallback_runtime_dimensions)}`"
            )
        if quality_missing_runtime_dimensions:
            lines.append(
                f"- quality_missing_runtime_dimensions=`{', '.join(quality_missing_runtime_dimensions)}`"
            )
        if attention_queue:
            lines.append("- attention_queue:")
            lines.extend([f"  - {item}" for item in attention_queue])
    else:
        lines.append("- none")

    lines.extend(["", "## Step Results"])
    for item in payload["steps"]:
        lines.append(f"- `{item['step']}` -> rc={item['returncode']} / status={item['status']} / warnings={item['warning_count']}")

    lines.extend(["", "## Warnings"])
    warnings = payload.get("warnings", [])
    if warnings:
        lines.extend([f"- {warning}" for warning in warnings])
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main() -> int:
    configure_utf8_stdio()
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    project_dir = Path(args.project).resolve()
    target_chapter = resolve_target_chapter(args.chapter, args.target_chapter)
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
    results = [run_step(repo_root, step, project_dir, args.chapter, target_chapter, args.dry_run) for step in steps]
    results = enrich_steps_with_normalized_fields(results)
    failed = [item for item in results if int(item["returncode"]) != 0]
    report_dir = project_dir / "05_reports"
    payload = {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "reference_chapter": args.chapter,
        "target_chapter": target_chapter,
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
    payload["pipeline_summary"] = build_pipeline_summary(results)
    payload["final_release"] = str(payload["pipeline_summary"].get("final_release", "")).strip() or "pass"
    if failed and payload["final_release"] == "pass":
        payload["final_release"] = "revise"
        if isinstance(payload["pipeline_summary"], dict):
            payload["pipeline_summary"]["final_release"] = "revise"
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
