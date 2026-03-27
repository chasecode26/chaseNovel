#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
SELF_CHECK_SCRIPT = SKILL_ROOT / "scripts" / "chapter_self_check.py"


def emit_original(payload: str) -> int:
    sys.stdout.write(payload)
    return 0


def load_input(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[chaseNovel hook] invalid JSON payload: {exc}", file=sys.stderr)
        return {}


def file_path_from_payload(payload: dict) -> Path | None:
    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path")
    if not file_path:
        return None
    return Path(file_path).resolve()


def is_chapter_markdown(path: Path) -> bool:
    parent_name = path.parent.name
    if parent_name != "03_chapters":
        return False
    if path.suffix.lower() != ".md":
        return False
    return True


def project_root_from_chapter(path: Path) -> Path:
    return path.parent.parent


def run_self_check(project_root: Path) -> None:
    try:
        result = subprocess.run(
            [sys.executable, str(SELF_CHECK_SCRIPT), "--project", str(project_root), "--json"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        print(f"[chaseNovel hook] failed to execute self-check: {exc}", file=sys.stderr)
        return

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        details = stderr or stdout or f"exit={result.returncode}"
        print(f"[chaseNovel hook] self-check failed: {details}", file=sys.stderr)
        return

    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        print("[chaseNovel hook] self-check returned non-JSON output", file=sys.stderr)
        return

    checkpoint = payload.get("checkpoint_due")
    report_path = payload.get("report_path")
    if checkpoint and report_path:
        print(
            f"[chaseNovel hook] {checkpoint} self-check triggered -> {report_path}",
            file=sys.stderr,
        )


def main() -> int:
    raw = sys.stdin.read()
    payload = load_input(raw)
    file_path = file_path_from_payload(payload)

    if file_path and is_chapter_markdown(file_path):
        run_self_check(project_root_from_chapter(file_path))

    return emit_original(raw)


if __name__ == "__main__":
    raise SystemExit(main())
