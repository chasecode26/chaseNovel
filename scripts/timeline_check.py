#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a lightweight timeline consistency report for a chaseNovel project."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    return parser.parse_args()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").lstrip("\ufeff")


def parse_timeline_rows(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "----" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 6 or cells[0] in {"时间点", "角色"}:
            continue
        rows.append(
            {
                "time_point": cells[0],
                "relative_time": cells[1],
                "event": cells[2],
                "characters": cells[3],
                "chapter": cells[4],
                "note": cells[5],
            }
        )
    return rows


def detect_warnings(rows: list[dict[str, str]]) -> list[str]:
    warnings: list[str] = []
    chapter_numbers: list[int] = []
    for row in rows:
        match = re.search(r"(\d+)", row["chapter"])
        if match:
            chapter_numbers.append(int(match.group(1)))

    if chapter_numbers and chapter_numbers != sorted(chapter_numbers):
        warnings.append("时间线表中的章节顺序不是单调递增，可能存在回填或错位。")

    relative_count = sum(1 for row in rows if row["relative_time"])
    if rows and relative_count < max(1, len(rows) // 2):
        warnings.append("时间线相对时间锚点不足，后续容易发生跳时错位。")

    if len(rows) < 3:
        warnings.append("时间线事件过少，长篇推进时缺乏足够锚点。")
    return warnings


def build_payload(project_dir: Path) -> dict[str, object]:
    timeline_path = project_dir / "00_memory" / "timeline.md"
    rows = parse_timeline_rows(read_text(timeline_path))
    warnings = detect_warnings(rows)
    return {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "event_count": len(rows),
        "warnings": warnings,
        "events": rows[:50],
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# 时间线校验报告",
        "",
        f"- 项目：`{payload['project']}`",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 事件数：`{payload['event_count']}`",
        "",
        "## 预警",
    ]
    if payload["warnings"]:
        lines.extend([f"- {item}" for item in payload["warnings"]])
    else:
        lines.append("- 无")
    lines.extend(["", "## 最近事件"])
    if payload["events"]:
        for item in payload["events"][:12]:
            lines.append(f"- `{item['chapter']}` {item['time_point']} / {item['relative_time']} -> {item['event']}")
    else:
        lines.append("- 无")
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    project_dir = Path(args.project).resolve()
    payload = build_payload(project_dir)
    reports_dir = project_dir / "05_reports"
    md_path = reports_dir / "timeline_check.md"
    json_path = reports_dir / "timeline_check.json"
    if not args.dry_run:
        reports_dir.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_markdown(payload), encoding="utf-8")
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"event_count={payload['event_count']}")
        print(f"warning_count={len(payload['warnings'])}")
        print(f"markdown={md_path.as_posix()}")
        print(f"json={json_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
