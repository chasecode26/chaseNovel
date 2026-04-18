#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from novel_utils import read_text


DEFAULT_TARGETS = ("state.json", "timeline.json", "payoff_board.json")

RECOMMENDED_ORDER = {
    "state.json": 1,
    "timeline.json": 2,
    "payoff_board.json": 3,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply confirmed LeadWriter runtime memory patches.")
    parser.add_argument("--project", required=True, help="Novel project root")
    parser.add_argument("--targets", help="Comma-separated schema targets such as state.json,timeline.json")
    parser.add_argument("--all", action="store_true", help="Apply every available runtime patch target")
    parser.add_argument("--interactive", action="store_true", help="Confirm each target before applying")
    parser.add_argument(
        "--confirm-file",
        help="Approval file path. One approved target per line, or `all` to approve every target.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Validate only, do not write files")
    return parser.parse_args()


def load_patch_payload(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(read_text(path))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def patch_target_name(item: dict[str, object]) -> str:
    return Path(str(item.get("schema_file", ""))).name


def parse_targets(args: argparse.Namespace, available: list[dict[str, object]]) -> list[str]:
    available_targets = [patch_target_name(item) for item in available if patch_target_name(item)]
    if args.all or not args.targets:
        requested = available_targets or list(DEFAULT_TARGETS)
    else:
        requested = [item.strip() for item in args.targets.split(",") if item.strip()]
    return sorted(requested, key=lambda item: (RECOMMENDED_ORDER.get(item, 99), item))


def parse_confirm_file(path: Path | None) -> set[str]:
    if path is None or not path.exists():
        return set()
    approved = set()
    for raw_line in read_text(path).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        approved.add(line)
    return approved


def confirm_target(target: str, interactive: bool, approved_targets: set[str]) -> bool:
    if not interactive and not approved_targets:
        return True
    if "all" in approved_targets or target in approved_targets:
        return True
    if not interactive:
        return False
    answer = input(f"apply {target}? [y/N]: ").strip().lower()
    return answer in {"y", "yes"}


def apply_patch_target(item: dict[str, object], dry_run: bool) -> dict[str, object]:
    target = patch_target_name(item)
    schema_file = Path(str(item.get("schema_file", "")))
    if not target or not str(schema_file):
        return {"target": target or "unknown", "status": "skip", "reason": "missing schema_file"}

    before = item.get("before", {})
    after = item.get("after", {})
    if not isinstance(before, dict) or not isinstance(after, dict):
        return {"target": target, "status": "skip", "reason": "patch payload must include before/after objects"}

    current_text = read_text(schema_file)
    try:
        current_payload = json.loads(current_text) if current_text.strip() else {}
    except json.JSONDecodeError:
        return {"target": target, "status": "conflict", "reason": "current schema file is not valid JSON"}
    if not isinstance(current_payload, dict):
        current_payload = {}
    if current_payload != before:
        return {
            "target": target,
            "status": "conflict",
            "reason": "schema file changed after patch generation; regenerate runtime patches first",
            "path": schema_file.as_posix(),
        }

    if dry_run:
        return {"target": target, "status": "ready", "path": schema_file.as_posix()}

    schema_file.parent.mkdir(parents=True, exist_ok=True)
    schema_file.write_text(json.dumps(after, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"target": target, "status": "applied", "path": schema_file.as_posix()}


def build_payload(
    project_dir: Path,
    requested_targets: list[str],
    dry_run: bool,
    interactive: bool,
    approved_targets: set[str],
) -> dict[str, object]:
    patch_json_path = project_dir / "00_memory" / "retrieval" / "leadwriter_memory_patches.json"
    patches = load_patch_payload(patch_json_path)
    patch_map = {patch_target_name(item): item for item in patches if patch_target_name(item)}
    results: list[dict[str, object]] = []
    warnings: list[str] = []

    if not patch_map:
        warnings.append("leadwriter_memory_patches.json is missing or empty")
        return {
            "project": project_dir.as_posix(),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "status": "warn",
            "applied_count": 0,
            "ready_count": 0,
            "requested_targets": requested_targets,
            "recommended_order": [],
            "results": results,
            "warnings": warnings,
            "warning_count": len(warnings),
            "report_paths": {"patch_json": patch_json_path.as_posix()},
        }

    for target in requested_targets:
        patch = patch_map.get(target)
        if patch is None:
            results.append({"target": target, "status": "skip", "reason": "target not found in runtime patch set"})
            continue
        if not confirm_target(target, interactive, approved_targets):
            results.append({"target": target, "status": "skip", "reason": "not approved"})
            continue
        results.append(apply_patch_target(patch, dry_run))

    applied_count = sum(1 for item in results if item.get("status") == "applied")
    ready_count = sum(1 for item in results if item.get("status") == "ready")
    status = "warn" if dry_run or warnings else "pass"
    if any(item.get("status") == "conflict" for item in results):
        status = "warn"

    return {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "applied_count": applied_count,
        "ready_count": ready_count,
        "requested_targets": requested_targets,
        "recommended_order": [target for target in DEFAULT_TARGETS if target in patch_map],
        "results": results,
        "warnings": warnings,
        "warning_count": len(warnings),
        "report_paths": {"patch_json": patch_json_path.as_posix()},
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    project_dir = Path(args.project).resolve()
    patch_json_path = project_dir / "00_memory" / "retrieval" / "leadwriter_memory_patches.json"
    available = load_patch_payload(patch_json_path)
    targets = parse_targets(args, available)
    confirm_file_path = Path(args.confirm_file).resolve() if args.confirm_file else None
    approved_targets = parse_confirm_file(confirm_file_path)
    payload = build_payload(project_dir, targets, args.dry_run, args.interactive, approved_targets)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"applied_count={payload['applied_count']}")
        print(f"ready_count={payload['ready_count']}")
        print(
            "recommended_order="
            + (",".join(payload["recommended_order"]) if payload["recommended_order"] else "none")
        )
        print(f"targets={','.join(targets) if targets else 'none'}")
        print(f"patch_json={payload['report_paths']['patch_json']}")
    return 1 if any(item.get("status") == "conflict" for item in payload["results"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
