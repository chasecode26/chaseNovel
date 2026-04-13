#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import subprocess
import sys
import shutil
import tempfile
import json
from pathlib import Path


def run(command: list[str], cwd: Path) -> None:
    completed = subprocess.run(command, cwd=cwd)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def run_capture_json(command: list[str], cwd: Path) -> dict[str, object]:
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if completed.returncode != 0 and not completed.stdout.strip():
        raise SystemExit(completed.returncode)
    return json.loads(completed.stdout)


def compile_python_scripts(repo_root: Path) -> None:
    for path in (repo_root / "scripts").glob("*.py"):
        py_compile.compile(str(path), doraise=True)


def prepare_open_fixture(project_dir: Path) -> None:
    memory_dir = project_dir / "00_memory"
    (memory_dir / "plan.md").write_text(
        "# 主线计划\n\n## 核心设定（不可偏离）\n"
        "- 书名：测试书\n"
        "- 题材：都市系统\n"
        "- 核心卖点：普通人靠系统翻身\n"
        "- 预计总字数：1200000\n",
        encoding="utf-8",
    )
    (memory_dir / "state.md").write_text(
        "# 当前状态\n\n## 进度\n"
        "- 当前章节：1\n"
        "- 当前卷：第一卷\n"
        "- 总字数：0\n\n"
        "## 当前阶段\n"
        "- 当前弧：起盘\n\n"
        "## 下章预告\n"
        "- 章节号：1\n"
        "- 计划内容：建立主角处境\n",
        encoding="utf-8",
    )
    (memory_dir / "style.md").write_text(
        "# 风格锚点\n\n"
        "- 题材：都市系统\n"
        "- 主风格标签：快反馈\n"
        "- 语言风格：现代通俗大白话\n"
        "- 必须保住的声音：利落、直接、有结果感\n",
        encoding="utf-8",
    )
    (memory_dir / "voice.md").write_text(
        "# 书级 Voice DNA\n\n"
        "角色说话差分总则：身份不同、性格不同、压力不同，说法就必须不同。\n",
        encoding="utf-8",
    )
    (memory_dir / "characters.md").write_text(
        "# 角色档案\n\n"
        "## 主角\n- 姓名：林砚\n\n"
        "## 核心配角\n- 苏晚：盟友\n",
        encoding="utf-8",
    )


def run_fixture_flow(repo_root: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="chase-smoke-") as temp_dir:
        project_dir = Path(temp_dir) / "fixture-book"

        run(["node", "./bin/chase.js", "bootstrap", "--project", str(project_dir)], cwd=repo_root)
        prepare_open_fixture(project_dir)

        doctor_payload = run_capture_json(
            ["python", "./scripts/doctor.py", "--project", str(project_dir), "--json"],
            cwd=repo_root,
        )
        if doctor_payload.get("status") == "fail":
            raise SystemExit("fixture doctor failed after bootstrap")

        open_payload = run_capture_json(
            ["python", "./scripts/open_book.py", "--project", str(project_dir), "--json"],
            cwd=repo_root,
        )
        if open_payload.get("status") == "fail":
            raise SystemExit("fixture open-book readiness failed after bootstrap")

        status_payload = run_capture_json(
            ["python", "./scripts/book_health.py", "--project", str(project_dir), "--json"],
            cwd=repo_root,
        )
        if status_payload.get("status") == "fail":
            raise SystemExit("fixture status health check failed after bootstrap")


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    npm = shutil.which("npm") or shutil.which("npm.cmd") or "npm"

    print("[smoke] checking CLI help")
    run(["node", "./bin/chase.js", "--help"], cwd=repo_root)

    print("[smoke] compiling python scripts")
    compile_python_scripts(repo_root)

    print("[smoke] running bootstrap/doctor/open fixture")
    run_fixture_flow(repo_root)

    print("[smoke] dry-run package build")
    run([npm, "pack", "--dry-run"], cwd=repo_root)

    print("[smoke] ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
