#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from chapter_gate import (
    chapter_number_from_name,
    build_gate_analysis,
    write_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run chapter gate in batch mode and emit summary reports."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--templates-root", help="Path to templates directory; defaults to ../templates")
    parser.add_argument("--style", help="Path to a specific style.md file")
    parser.add_argument("--skip-language", action="store_true", help="Skip language audit integration")
    parser.add_argument("--from", dest="chapter_from", type=int, help="Start chapter number")
    parser.add_argument("--to", dest="chapter_to", type=int, help="End chapter number")
    parser.add_argument("--dry-run", action="store_true", help="Do not write per-chapter outputs or summary files")
    parser.add_argument("--json", action="store_true", help="Print summary JSON to stdout")
    return parser.parse_args()


def detect_chapters(project_dir: Path, chapter_from: int | None, chapter_to: int | None) -> list[tuple[int, Path]]:
    chapters_dir = project_dir / "03_chapters"
    items: list[tuple[int, Path]] = []
    if not chapters_dir.exists():
        return items

    for path in chapters_dir.iterdir():
        if not path.is_file():
            continue
        chapter_no = chapter_number_from_name(path.name)
        if chapter_no is None:
            continue
        if chapter_from is not None and chapter_no < chapter_from:
            continue
        if chapter_to is not None and chapter_no > chapter_to:
            continue
        items.append((chapter_no, path))
    return sorted(items, key=lambda item: item[0])


def summarize_issue_text(messages: list[str]) -> str:
    if not messages:
        return "无"
    return " | ".join(messages[:3])


def render_summary_markdown(summary: dict[str, object]) -> str:
    rows = [
        "| 章节 | 总判定 | 连续性 | 语言 | 主要问题 |",
        "|---|---|---|---|---|",
    ]
    for item in summary["chapters"]:
        rows.append(
            "| 第{chapter_no:03d}章 | {verdict} | {continuity_verdict} | {language_verdict} | {issues} |".format(
                chapter_no=item["chapter_no"],
                verdict=item["verdict"],
                continuity_verdict=item["continuity_verdict"],
                language_verdict=item["language_verdict"],
                issues=item["top_issues"] or "无",
            )
        )

    verdict_counter = summary["stats"]["verdict_counter"]
    continuity_counter = summary["stats"]["continuity_counter"]
    language_counter = summary["stats"]["language_counter"]
    issue_counter = summary["stats"]["issue_counter"]
    top_issue_lines = (
        ["- 无"]
        if not issue_counter
        else [f"- {name} x{count}" for name, count in issue_counter.items()]
    )

    lines = [
        "# 批量门禁汇总",
        "",
        f"- 项目：`{summary['project']}`",
        f"- 章节范围：`{summary['chapter_range']}`",
        f"- 总章节数：`{summary['stats']['chapter_count']}`",
        f"- 总判定分布：`{json.dumps(verdict_counter, ensure_ascii=False)}`",
        f"- 连续性分布：`{json.dumps(continuity_counter, ensure_ascii=False)}`",
        f"- 语言分布：`{json.dumps(language_counter, ensure_ascii=False)}`",
        "",
        "## 高频问题",
        *top_issue_lines,
        "",
        "## 章节明细",
        *rows,
    ]
    return "\n".join(lines)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    project_dir = Path(args.project).resolve()
    templates_root = (
        Path(args.templates_root).resolve()
        if args.templates_root
        else (Path(__file__).resolve().parent.parent / "templates")
    )
    style_path = Path(args.style).resolve() if args.style else (project_dir / "00_memory" / "style.md")
    chapters = detect_chapters(project_dir, args.chapter_from, args.chapter_to)
    if not chapters:
        print("未找到可处理的章节。")
        return 1

    verdict_counter: Counter[str] = Counter()
    continuity_counter: Counter[str] = Counter()
    language_counter: Counter[str] = Counter()
    issue_counter: Counter[str] = Counter()
    chapter_items: list[dict[str, object]] = []

    for chapter_no, chapter_path in chapters:
        analysis = build_gate_analysis(project_dir, chapter_no, chapter_path, style_path, args.skip_language)
        write_outputs(project_dir, templates_root, analysis, args.dry_run, None)

        verdict_counter[str(analysis["verdict"])] += 1
        continuity_counter[str(analysis["continuity_verdict"])] += 1
        language_counter[str(analysis["language_verdict"])] += 1

        issues = list(analysis["blockers"]) + list(analysis["warnings"]) + list(analysis["language_blockers"]) + list(analysis["language_warnings"])
        for issue in issues:
            issue_counter[str(issue)] += 1

        chapter_items.append({
            "chapter_no": chapter_no,
            "chapter_path": chapter_path.as_posix(),
            "verdict": analysis["verdict"],
            "continuity_verdict": analysis["continuity_verdict"],
            "language_verdict": analysis["language_verdict"],
            "top_issues": summarize_issue_text(issues),
        })

    summary = {
        "project": project_dir.as_posix(),
        "chapter_range": f"{chapters[0][0]:03d}-{chapters[-1][0]:03d}",
        "chapters": chapter_items,
        "stats": {
            "chapter_count": len(chapter_items),
            "verdict_counter": dict(sorted(verdict_counter.items())),
            "continuity_counter": dict(sorted(continuity_counter.items())),
            "language_counter": dict(sorted(language_counter.items())),
            "issue_counter": dict(issue_counter.most_common(10)),
        },
    }

    gate_dir = project_dir / "04_gate"
    summary_json_path = gate_dir / "batch_gate_summary.json"
    summary_md_path = gate_dir / "batch_gate_summary.md"
    if not args.dry_run:
        gate_dir.mkdir(parents=True, exist_ok=True)
        summary_json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        summary_md_path.write_text(render_summary_markdown(summary), encoding="utf-8")

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"chapter_count={summary['stats']['chapter_count']}")
        print(f"chapter_range={summary['chapter_range']}")
        print(f"summary_json={summary_json_path.as_posix()}")
        print(f"summary_md={summary_md_path.as_posix()}")
        print(f"verdicts={json.dumps(summary['stats']['verdict_counter'], ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
