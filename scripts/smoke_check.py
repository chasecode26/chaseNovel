#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import subprocess
import sys
import shutil
from pathlib import Path


def run(command: list[str], cwd: Path) -> None:
    completed = subprocess.run(command, cwd=cwd)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def compile_python_scripts(repo_root: Path) -> None:
    for path in (repo_root / "scripts").glob("*.py"):
        py_compile.compile(str(path), doraise=True)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    npm = shutil.which("npm") or shutil.which("npm.cmd") or "npm"

    print("[smoke] checking CLI help")
    run(["node", "./bin/chase.js", "--help"], cwd=repo_root)

    print("[smoke] compiling python scripts")
    compile_python_scripts(repo_root)

    print("[smoke] dry-run package build")
    run([npm, "pack", "--dry-run"], cwd=repo_root)

    print("[smoke] ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
