#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from novel_utils import derive_plan_target_words, has_placeholder, read_text


REQUIRED_LAUNCH_FILES = [
    "00_memory/plan.md",
    "00_memory/state.md",
    "00_memory/style.md",
    "00_memory/voice.md",
    "00_memory/characters.md",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Open-book entry: launch-readiness scan by default, chapter planning/context when --chapter or --target-chapter is set."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument(
        "--chapter",
        type=int,
        help="Existing drafted current chapter number. Open-book planning/context targets the next chapter by default.",
    )
    parser.add_argument("--target-chapter", type=int, help="Explicit target chapter number")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    return parser.parse_args()


def run_planning_context(args: argparse.Namespace) -> int:
    script_path = Path(__file__).with_name("planning_context.py")
    cmd = [sys.executable, str(script_path), "--project", args.project]
    if args.chapter is not None:
        cmd.extend(["--chapter", str(args.chapter)])
    if args.target_chapter is not None:
        cmd.extend(["--target-chapter", str(args.target_chapter)])
    if args.dry_run:
        cmd.append("--dry-run")
    if args.json:
        cmd.append("--json")
    completed = subprocess.run(cmd)
    return completed.returncode


def check_plan(plan_text: str, warnings: list[str], blockers: list[str]) -> None:
    required_labels = ["书名", "题材", "核心卖点"]
    for label in required_labels:
        if f"- {label}：" not in plan_text and f"- {label}:" not in plan_text:
            blockers.append(f"`plan.md` 缺少“{label}”，开书锚点不足。")
    if "预计总字数" not in plan_text:
        derived_target_words = derive_plan_target_words(plan_text)
        if derived_target_words <= 0:
            blockers.append("`plan.md` 缺少“预计总字数”，且无法从章节字数约束与卷范围推导总字数。")
        else:
            warnings.append(f"`plan.md` 未直写预计总字数，当前按卷范围推导约 `{derived_target_words}` 字。")
    if has_placeholder(plan_text):
        warnings.append("`plan.md` 仍含占位符，说明开书信息还没有填实。")


def check_state(state_text: str, warnings: list[str], blockers: list[str]) -> None:
    if "## 下章预告" not in state_text:
        warnings.append("`state.md` 缺少“下章预告”结构，后续章节承接会变弱。")
    if has_placeholder(state_text):
        warnings.append("`state.md` 仍含占位符，当前状态锚点还未填实。")
    if "- 当前卷：" not in state_text and "- 当前卷:" not in state_text:
        blockers.append("`state.md` 缺少“当前卷”，开书阶段缺卷级推进锚点。")


def check_style(style_text: str, warnings: list[str], blockers: list[str]) -> None:
    required_labels = ["题材", "主风格标签", "语言风格", "必须保住的声音"]
    for label in required_labels:
        if label not in style_text:
            warnings.append(f"`style.md` 可能缺少“{label}”相关内容，书级风格还不够具体。")
    if has_placeholder(style_text):
        warnings.append("`style.md` 仍含占位符，风格锚点未完成。")
    if "现代通俗大白话" not in style_text and "语言风格" in style_text:
        warnings.append("`style.md` 尚未明确默认表达基线，建议把“大白话/清晰可读”落成具体约束。")


def check_voice(voice_text: str, warnings: list[str], blockers: list[str]) -> None:
    if "角色说话差分总则" not in voice_text:
        blockers.append("`voice.md` 缺少角色声口差分总则，后续容易全员一个腔。")
    if has_placeholder(voice_text):
        warnings.append("`voice.md` 仍含占位符，书级声音尚未定实。")


def check_characters(char_text: str, warnings: list[str], blockers: list[str]) -> None:
    if "## 主角" not in char_text:
        blockers.append("`characters.md` 缺少主角档案，开书不能直接进入写作。")
    if "## 核心配角" not in char_text:
        warnings.append("`characters.md` 尚未补核心配角，关系推进空间可能不足。")
    if has_placeholder(char_text):
        warnings.append("`characters.md` 仍含占位符，人物资料未完成。")


def build_launch_payload(project_dir: Path) -> dict[str, object]:
    warnings: list[str] = []
    blockers: list[str] = []
    missing_files = [item for item in REQUIRED_LAUNCH_FILES if not (project_dir / item).exists()]
    if missing_files:
        blockers.extend([f"缺少 `{item}`，开书锚点不完整。" for item in missing_files])

    plan_text = read_text(project_dir / "00_memory" / "plan.md")
    state_text = read_text(project_dir / "00_memory" / "state.md")
    style_text = read_text(project_dir / "00_memory" / "style.md")
    voice_text = read_text(project_dir / "00_memory" / "voice.md")
    characters_text = read_text(project_dir / "00_memory" / "characters.md")

    if plan_text:
        check_plan(plan_text, warnings, blockers)
    if state_text:
        check_state(state_text, warnings, blockers)
    if style_text:
        check_style(style_text, warnings, blockers)
    if voice_text:
        check_voice(voice_text, warnings, blockers)
    if characters_text:
        check_characters(characters_text, warnings, blockers)

    status = "fail" if blockers else ("warn" if warnings else "pass")
    return {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "launch-readiness",
        "status": status,
        "missing_files": missing_files,
        "warnings": warnings,
        "warning_count": len(warnings),
        "blockers": blockers,
        "blocker_count": len(blockers),
        "recommended_next_steps": [
            "补齐 plan.md 的题材 / 卖点 / 总字数 / 卷目标",
            "补齐 state.md 的当前卷 / 当前阶段 / 下章预告",
            "补齐 style.md 与 voice.md，明确书级表达和角色声口差分",
            "补齐 characters.md 的主角与核心配角",
            "准备好后再进入写作主链或章节规划",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# 开书 readiness 报告",
        "",
        f"- 项目：`{payload['project']}`",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 模式：`{payload['mode']}`",
        f"- 状态：`{payload['status'].upper()}`",
        "",
        "## 阻断项",
    ]
    blockers = payload.get("blockers", [])
    if blockers:
        lines.extend([f"- {item}" for item in blockers])
    else:
        lines.append("- 无")
    lines.extend(["", "## 预警"])
    warnings = payload.get("warnings", [])
    if warnings:
        lines.extend([f"- {item}" for item in warnings])
    else:
        lines.append("- 无")
    lines.extend(["", "## 建议下一步"])
    lines.extend([f"- {item}" for item in payload.get("recommended_next_steps", [])])
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    if args.chapter is not None or args.target_chapter is not None:
        return run_planning_context(args)

    project_dir = Path(args.project).resolve()
    payload = build_launch_payload(project_dir)
    report_path = project_dir / "05_reports" / "open_book_readiness.md"
    json_path = project_dir / "05_reports" / "open_book_readiness.json"
    payload["report_paths"] = {
        "markdown": report_path.as_posix(),
        "json": json_path.as_posix(),
    }

    if not args.dry_run:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render_markdown(payload), encoding="utf-8")
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"blocker_count={payload['blocker_count']}")
        print(f"warning_count={payload['warning_count']}")
        print(f"report={payload['report_paths']['markdown']}")
    return 1 if payload["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
