#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from novel_utils import detect_current_chapter, extract_pipe_table_rows, read_text


RELATIVE_TIME_MARKERS = ("后", "前", "同时", "随后", "之前", "之后", "期间", "当晚", "次日", "翌日")


def looks_relative_time(text: str) -> bool:
    normalized = text.strip()
    if not normalized:
        return False
    return any(marker in normalized for marker in RELATIVE_TIME_MARKERS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a lightweight timeline consistency report for a chaseNovel project."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    return parser.parse_args()


def parse_timeline_rows(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    table_rows = extract_pipe_table_rows(text)
    if not table_rows:
        return rows
    header_size = len(table_rows[0]) if table_rows else 0
    for cells in table_rows[1:]:
        if header_size >= 6:
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
            continue
        if header_size >= 3:
            if len(cells) < 3 or cells[0] in {"时间", "时间点"}:
                continue
            first_cell = cells[0]
            rows.append(
                {
                    "time_point": "" if looks_relative_time(first_cell) else first_cell,
                    "relative_time": first_cell if looks_relative_time(first_cell) else "",
                    "event": cells[1],
                    "characters": "",
                    "chapter": "",
                    "note": cells[2],
                }
            )
            continue
    return rows


def load_schema_rows(project_dir: Path) -> list[dict[str, str]]:
    schema_path = project_dir / "00_memory" / "schema" / "timeline.json"
    if not schema_path.exists():
        return []
    try:
        payload = json.loads(read_text(schema_path))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, dict):
        return []
    rows: list[dict[str, str]] = []
    recent_events = payload.get("recentEvents", [])
    if isinstance(recent_events, list):
        for event in recent_events:
            text = str(event).strip()
            if not text:
                continue
            chapter_match = re.search(r"chapter-(\d+)", text, re.IGNORECASE)
            rows.append(
                {
                    "time_point": str(payload.get("absoluteTime", "")).strip(),
                    "relative_time": str(payload.get("relativeTimeFromPrevChapter", "")).strip(),
                    "event": text,
                    "characters": "",
                    "chapter": chapter_match.group(1) if chapter_match else "",
                    "note": str(payload.get("currentLocation", "")).strip(),
                }
            )
    return rows


def detect_warnings(rows: list[dict[str, str]], current_chapter: int) -> list[str]:
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

    expected_min_events = min(3, max(current_chapter, 0))
    if current_chapter >= 1 and len(rows) < expected_min_events:
        warnings.append("时间线事件过少，长篇推进时缺乏足够锚点。")
    return warnings


def build_payload(project_dir: Path) -> dict[str, object]:
    timeline_path = project_dir / "00_memory" / "timeline.md"
    state_path = project_dir / "00_memory" / "state.md"
    current_chapter = detect_current_chapter(read_text(state_path))
    rows = parse_timeline_rows(read_text(timeline_path))
    if not rows:
        rows = load_schema_rows(project_dir)
    warnings = detect_warnings(rows, current_chapter)
    return {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "warn" if warnings else "pass",
        "current_chapter": current_chapter,
        "event_count": len(rows),
        "warnings": warnings,
        "warning_count": len(warnings),
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
    payload["report_paths"] = {
        "markdown": md_path.as_posix(),
        "json": json_path.as_posix(),
    }
    if not args.dry_run:
        reports_dir.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_markdown(payload), encoding="utf-8")
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"event_count={payload['event_count']}")
        print(f"warning_count={payload['warning_count']}")
        print(f"markdown={payload['report_paths']['markdown']}")
        print(f"json={payload['report_paths']['json']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
