#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from novel_utils import clean_value, count_chapter_files, detect_current_chapter, extract_state_value, read_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a lightweight book-level dashboard snapshot for a chaseNovel project."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Do not write report files")
    return parser.parse_args()

def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(read_text(path))


def build_payload(project_dir: Path) -> dict[str, object]:
    memory_dir = project_dir / "00_memory"
    reports_dir = project_dir / "05_reports"
    state_text = read_text(memory_dir / "state.md")
    foreshadow_json = load_json(reports_dir / "foreshadow_heatmap.json")

    active_volume = extract_state_value(state_text, "当前卷")
    active_arc = extract_state_value(state_text, "当前弧")
    warnings: list[str] = []
    chapter_count = count_chapter_files(project_dir)
    if chapter_count == 0:
        warnings.append("当前项目还没有正文章节，dashboard 仅反映模板与记忆状态。")
    if not (memory_dir / "retrieval" / "next_context.md").exists():
        warnings.append("缺少 next_context.md；建议先运行 context_compiler.py 或 chase context。")
    overdue_count = len(foreshadow_json.get("overdue", []))
    if overdue_count:
        warnings.append(f"当前存在 {overdue_count} 条超期伏笔，建议优先安排回收。")
    status = "warn" if warnings else "pass"

    return {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "current_chapter": detect_current_chapter(state_text) or chapter_count,
        "active_volume": clean_value(active_volume),
        "active_arc": clean_value(active_arc),
        "chapter_count": chapter_count,
        "pending_foreshadow_count": len(foreshadow_json.get("active", [])),
        "overdue_foreshadow_count": overdue_count,
        "warnings": warnings,
        "warning_count": len(warnings),
        "report_paths": {
            "next_context": (memory_dir / "retrieval" / "next_context.md").as_posix(),
            "markdown": (reports_dir / "dashboard.md").as_posix(),
            "json": (reports_dir / "dashboard.json").as_posix(),
        },
    }


def render_markdown(payload: dict[str, object]) -> str:
    return "\n".join(
        [
            "# 项目总览",
            "",
            f"- 项目：`{payload['project']}`",
            f"- 生成时间：`{payload['generated_at']}`",
            f"- 当前章节：`第{payload['current_chapter']:03d}章`",
            f"- 当前卷：`{payload['active_volume']}`",
            f"- 当前弧：`{payload['active_arc']}`",
            f"- 已有章节数：`{payload['chapter_count']}`",
            f"- 活跃伏笔数：`{payload['pending_foreshadow_count']}`",
            f"- 超期伏笔数：`{payload['overdue_foreshadow_count']}`",
            "",
            "## 关键产物",
            f"- 下一章上下文：`{payload['report_paths']['next_context']}`",
            f"- Dashboard JSON：`{payload['report_paths']['json']}`",
        ]
    ) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    project_dir = Path(args.project).resolve()
    reports_dir = project_dir / "05_reports"
    payload = build_payload(project_dir)

    if not args.dry_run:
        reports_dir.mkdir(parents=True, exist_ok=True)
        (reports_dir / "dashboard.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        (reports_dir / "dashboard.md").write_text(render_markdown(payload), encoding="utf-8")
        retrieval_dir = project_dir / "00_memory" / "retrieval"
        retrieval_dir.mkdir(parents=True, exist_ok=True)
        (retrieval_dir / "dashboard_cache.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"warning_count={payload['warning_count']}")
        print(f"chapter={payload['current_chapter']}")
        print(f"active_volume={payload['active_volume']}")
        print(f"active_arc={payload['active_arc']}")
        print(f"dashboard={payload['report_paths']['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
