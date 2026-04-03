#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def run(command: list[str], cwd: Path) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": (completed.stdout or "").strip(),
        "stderr": (completed.stderr or "").strip(),
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    repo_root = Path(__file__).resolve().parent.parent
    python = sys.executable
    node = "node"
    steps: list[dict[str, object]] = []
    tmp_root = repo_root / "tmp_toolchain_smoke"
    project_dir = tmp_root / "novel_smoke"
    shutil.rmtree(tmp_root, ignore_errors=True)

    try:
        steps.append(
            run(
                [python, "scripts/project_bootstrap.py", "--project", project_dir.as_posix()],
                repo_root,
            )
        )
        steps.append(
            run(
                [python, "scripts/project_doctor.py", "--project", project_dir.as_posix(), "--json"],
                repo_root,
            )
        )
        steps.append(
            run(
                [python, "scripts/workflow_runner.py", "--project", project_dir.as_posix(), "--dry-run", "--json"],
                repo_root,
            )
        )
        steps.append(
            run(
                [node, "bin/chase.js", "run", "--project", project_dir.as_posix(), "--dry-run"],
                repo_root,
            )
        )
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    failed = [step for step in steps if int(step["returncode"]) != 0]
    payload = {
        "repo": repo_root.as_posix(),
        "failed": len(failed),
        "steps": steps,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
