#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
SELF_CHECK_SCRIPT = SKILL_ROOT / "scripts" / "chapter_self_check.py"
CHAPTER_GATE_SCRIPT = SKILL_ROOT / "scripts" / "chapter_gate.py"


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


def run_json_script(script_path: Path, project_root: Path, extra_args: list[str] | None = None) -> dict | None:
    cmd = [sys.executable, str(script_path), "--project", str(project_root), "--json"]
    if extra_args:
        cmd.extend(extra_args)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        print(f"[chaseNovel hook] failed to execute {script_path.name}: {exc}", file=sys.stderr)
        return None

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        details = stderr or stdout or f"exit={result.returncode}"
        print(f"[chaseNovel hook] {script_path.name} failed: {details}", file=sys.stderr)
        return None

    try:
        return json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        print(f"[chaseNovel hook] {script_path.name} returned non-JSON output", file=sys.stderr)
        return None


def run_self_check(project_root: Path) -> None:
    payload = run_json_script(SELF_CHECK_SCRIPT, project_root, ["--force"])
    if not payload:
        return
    checkpoint = payload.get("checkpoint_due")
    report_path = payload.get("report_path")
    if checkpoint and report_path:
        print(
            f"[chaseNovel hook] {checkpoint} self-check triggered -> {report_path}",
            file=sys.stderr,
        )


def run_chapter_gate(project_root: Path) -> None:
    payload = run_json_script(CHAPTER_GATE_SCRIPT, project_root)
    if not payload:
        return

    verdict = payload.get("verdict")
    report_path = payload.get("report_path")
    if verdict and report_path:
        print(
            f"[chaseNovel hook] chapter gate {str(verdict).upper()} -> {report_path}",
            file=sys.stderr,
        )


def main() -> int:
    raw = sys.stdin.read()
    payload = load_input(raw)
    file_path = file_path_from_payload(payload)

    if file_path and is_chapter_markdown(file_path):
        project_root = project_root_from_chapter(file_path)
        run_self_check(project_root)
        run_chapter_gate(project_root)

    return emit_original(raw)


if __name__ == "__main__":
    raise SystemExit(main())
