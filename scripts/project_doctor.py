#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from aggregation_utils import configure_utf8_stdio, write_markdown_json_reports
from novel_utils import count_chapter_files, detect_current_chapter, extract_state_value, read_text


REQUIRED_DIRS = [
    "00_memory",
    "00_memory/retrieval",
    "00_memory/summaries",
    "01_outline",
    "02_knowledge",
    "03_chapters",
    "04_gate",
]

REQUIRED_FILES = [
    "00_memory/plan.md",
    "00_memory/state.md",
    "00_memory/arc_progress.md",
    "00_memory/characters.md",
    "00_memory/character_arcs.md",
    "00_memory/timeline.md",
    "00_memory/foreshadowing.md",
    "00_memory/payoff_board.md",
    "00_memory/style.md",
    "00_memory/voice.md",
    "00_memory/scene_preferences.md",
    "00_memory/findings.md",
    "00_memory/summaries/recent.md",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run structural health checks for a chaseNovel project."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Do not write report files")
    return parser.parse_args()


def build_payload(project_dir: Path) -> dict[str, object]:
    missing_dirs = [item for item in REQUIRED_DIRS if not (project_dir / item).exists()]
    missing_files = [item for item in REQUIRED_FILES if not (project_dir / item).exists()]

    state_text = read_text(project_dir / "00_memory" / "state.md")
    current_chapter = detect_current_chapter(state_text) or None
    chapters = count_chapter_files(project_dir)
    current_place = extract_state_value(state_text, "当前地点")
    runtime_payload_exists = (project_dir / "00_memory" / "retrieval" / "leadwriter_runtime_payload.json").exists()

    warnings: list[str] = []
    if chapters == 0:
        warnings.append("当前项目还没有正文章节，无法做连续性与反重复回归。")
    if current_chapter is None:
        warnings.append("state.md 中未识别到“当前章节”，上下文编译会退回默认章节。")
    if not current_place:
        warnings.append("state.md 中缺少“当前地点”，章节起章站位与转场校验会偏弱。")
    elif chapters and current_chapter > chapters + 1:
        warnings.append(
            f"state.md 当前章节为第{current_chapter}章，但正文章节仅检测到 {chapters} 章，状态可能超前。"
        )
    if not (project_dir / "00_memory" / "retrieval" / "next_context.md").exists() and not runtime_payload_exists:
        warnings.append("缺少 next_context.md；建议优先运行 `chase open --project <dir> --chapter <n>` 生成章节上下文。")
    if not (project_dir / "00_memory" / "style_guardrails.md").exists():
        warnings.append("缺少 style_guardrails.md；建议补齐风格护栏，避免后续章节持续发虚或术语挡路。")
    if chapters >= 10 and not (project_dir / "00_memory" / "summaries" / "mid.md").exists():
        warnings.append("章节已达 10 章以上但缺少 summaries/mid.md，断更恢复会逐渐变慢。")
    if chapters >= 15 and not (project_dir / "01_outline" / "volume_blueprint.md").exists():
        warnings.append("章节已达 15 章以上但缺少 volume_blueprint.md，卷级节奏与收束风险会上升。")

    status = "pass"
    if missing_dirs or missing_files:
        status = "fail"
    elif warnings:
        status = "warn"

    return {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "missing_dirs": missing_dirs,
        "missing_files": missing_files,
        "chapter_count": chapters,
        "current_chapter": current_chapter,
        "warnings": warnings,
        "warning_count": len(warnings),
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# 项目体检报告",
        "",
        f"- 项目：`{payload['project']}`",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 体检结论：`{payload['status'].upper()}`",
        f"- 已识别章节数：`{payload['chapter_count']}`",
        f"- state 当前章节：`{payload['current_chapter'] if payload['current_chapter'] is not None else '未识别'}`",
        "",
        "## 缺失目录",
    ]
    if payload["missing_dirs"]:
        lines.extend([f"- {item}" for item in payload["missing_dirs"]])
    else:
        lines.append("- 无")

    lines.extend(["", "## 缺失文件"])
    if payload["missing_files"]:
        lines.extend([f"- {item}" for item in payload["missing_files"]])
    else:
        lines.append("- 无")

    lines.extend(["", "## 预警"])
    if payload["warnings"]:
        lines.extend([f"- {item}" for item in payload["warnings"]])
    else:
        lines.append("- 无")
    return "\n".join(lines) + "\n"


def main() -> int:
    configure_utf8_stdio()
    args = parse_args()
    project_dir = Path(args.project).resolve()
    payload = build_payload(project_dir)
    if not args.dry_run:
        payload["report_paths"] = write_markdown_json_reports(
            project_dir,
            payload,
            base_name="doctor",
            markdown_renderer=render_markdown,
        )
    else:
        report_dir = project_dir / "05_reports"
        payload["report_paths"] = {
            "markdown": (report_dir / "doctor.md").as_posix(),
            "json": (report_dir / "doctor.json").as_posix(),
        }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"warning_count={payload['warning_count']}")
        print(f"chapters={payload['chapter_count']}")
        print(f"report={payload['report_paths']['markdown']}")
    return 1 if payload["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
