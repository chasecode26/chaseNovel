#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

from aggregation_utils import safe_write_text, validate_project_root
from novel_utils import read_text


DEFAULT_TARGETS = (
    "timeline.md",
    "foreshadowing.md",
    "payoff_board.md",
    "character_arcs.md",
)

RECOMMENDED_ORDER = {
    "timeline.md": 1,
    "foreshadowing.md": 2,
    "payoff_board.md": 3,
    "character_arcs.md": 4,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="应用 memory_update.py 生成并已确认的记忆同步 patch。"
    )
    parser.add_argument("--project", required=True, help="小说项目根目录")
    parser.add_argument(
        "--targets",
        help="指定要应用的目标，逗号分隔，如 timeline.md,foreshadowing.md；默认按可用 patch 全量处理。",
    )
    parser.add_argument("--all", action="store_true", help="应用当前全部可用 patch 目标")
    parser.add_argument("--interactive", action="store_true", help="每个目标应用前都进行交互确认")
    parser.add_argument(
        "--confirm-file",
        help="审批文件路径，每行一个允许应用的目标；写 all 表示全部批准。",
    )
    parser.add_argument("--json", action="store_true", help="输出 JSON 结果")
    parser.add_argument("--dry-run", action="store_true", help="只校验不写入文件")
    return parser.parse_args()


def sha256_text(text: str) -> str:
    normalized = text if text.endswith("\n") else text + "\n"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def load_patch_payload(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(read_text(path))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def parse_targets(args: argparse.Namespace, available: dict[str, dict[str, str]]) -> list[str]:
    if args.all or not args.targets:
        return sorted(available.keys(), key=lambda item: (RECOMMENDED_ORDER.get(item, 99), item))
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
        if line.lower() == "all":
            approved.add("all")
            continue
        approved.add(line)
    return approved


def apply_patch_target(target: str, item: dict[str, str], dry_run: bool, project_dir: Path) -> dict[str, object]:
    raw_path = str(item.get("path", "")).strip()
    before_sha = str(item.get("before_sha256", ""))
    after_content = str(item.get("after_content", ""))

    if not raw_path:
        return {"target": target, "status": "skip", "reason": "缺少目标文件路径"}

    file_path = Path(raw_path)
    try:
        resolved_root = validate_project_root(project_dir)
        candidate_path = file_path.resolve(strict=False) if file_path.is_absolute() else (resolved_root / file_path).resolve(strict=False)
        if candidate_path != resolved_root and resolved_root not in candidate_path.parents:
            return {"target": target, "status": "skip", "reason": "目标文件超出项目根目录", "path": raw_path}
    except ValueError as exc:
        return {"target": target, "status": "skip", "reason": str(exc), "path": raw_path}

    current = read_text(candidate_path)
    if not after_content:
        return {"target": target, "status": "skip", "reason": "缺少 after_content 内容"}
    if before_sha and sha256_text(current) != before_sha:
        return {
            "target": target,
            "status": "conflict",
            "reason": "patch 生成后文件已变化，请重新生成后再落表",
            "path": candidate_path.as_posix(),
        }
    if dry_run:
        return {"target": target, "status": "ready", "reason": "仅完成校验，尚未写入", "path": candidate_path.as_posix()}

    safe_write_text(candidate_path, after_content, root_dir=resolved_root)
    return {"target": target, "status": "applied", "path": candidate_path.as_posix()}


def confirm_target(target: str, item: dict[str, str], interactive: bool, approved_targets: set[str]) -> bool:
    if not interactive and not approved_targets:
        return True
    if "all" in approved_targets or target in approved_targets:
        return True
    if not interactive:
        return False

    summary = str(item.get("summary", target))
    print(f"[confirm] {target}: {summary}")
    answer = input("应用这个 patch？[y/N]: ").strip().lower()
    return answer in {"y", "yes"}


def build_payload(
    project_dir: Path,
    requested_targets: list[str],
    dry_run: bool,
    interactive: bool,
    approved_targets: set[str],
) -> dict[str, object]:
    patch_json_path = project_dir / "00_memory" / "retrieval" / "memory_sync_patches.json"
    patches = load_patch_payload(patch_json_path)
    results: list[dict[str, object]] = []
    warnings: list[str] = []

    if not patches:
        warnings.append("memory_sync_patches.json 不存在或为空，当前没有可确认落表的 patch。")
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
        item = patches.get(target)
        if not isinstance(item, dict):
            results.append({"target": target, "status": "skip", "reason": "未找到对应目标"})
            continue
        if not confirm_target(target, item, interactive, approved_targets):
            results.append({"target": target, "status": "skip", "reason": "未获确认，已跳过"})
            continue
        results.append(apply_patch_target(target, item, dry_run, project_dir))

    applied_count = sum(1 for item in results if item.get("status") == "applied")
    conflict_count = sum(1 for item in results if item.get("status") == "conflict")
    ready_count = sum(1 for item in results if item.get("status") == "ready")
    status = "warn" if conflict_count or warnings else "pass"
    if dry_run and not conflict_count:
        status = "warn"

    return {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "applied_count": applied_count,
        "ready_count": ready_count,
        "requested_targets": requested_targets,
        "recommended_order": [target for target in DEFAULT_TARGETS if target in patches],
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
    patch_json_path = project_dir / "00_memory" / "retrieval" / "memory_sync_patches.json"
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
        print(f"recommended_order={','.join(payload['recommended_order']) if payload['recommended_order'] else 'none'}")
        print(f"targets={','.join(targets) if targets else 'none'}")
        print(f"patch_json={payload['report_paths']['patch_json']}")
    return 1 if any(item.get("status") == "conflict" for item in payload["results"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
