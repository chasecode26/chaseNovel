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
        description="Generate a lightweight arc tracking report for a chaseNovel project."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    return parser.parse_args()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").lstrip("\ufeff")


def parse_table_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "----" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        rows.append(cells)
    return rows


def parse_character_arcs(memory_dir: Path) -> list[dict[str, str]]:
    rows = parse_table_rows(read_text(memory_dir / "character_arcs.md"))
    results: list[dict[str, str]] = []
    for row in rows[1:]:
        if len(row) < 8 or not row[0]:
            continue
        results.append(
            {
                "character": row[0],
                "arc_type": row[1],
                "stage": row[2],
                "goal": row[3],
                "blocker": row[4],
                "latest_shift": row[5],
                "next_window": row[6],
                "risk": row[7],
            }
        )
    return results


def parse_relation_arcs(memory_dir: Path) -> list[dict[str, str]]:
    text = read_text(memory_dir / "character_arcs.md")
    matches = re.findall(
        r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|$",
        text,
        re.MULTILINE,
    )
    results: list[dict[str, str]] = []
    for row in matches:
        if row[0].strip() in {"关系对", "角色"}:
            continue
        if len(row) == 6 and "—" not in row[0]:
            continue
        if len(row) == 6:
            results.append(
                {
                    "pair": row[0].strip(),
                    "position": row[1].strip(),
                    "latest_shift": row[2].strip(),
                    "tension": row[3].strip(),
                    "next_mode": row[4].strip(),
                    "repeat_risk": row[5].strip(),
                }
            )
    return results


def build_payload(project_dir: Path) -> dict[str, object]:
    memory_dir = project_dir / "00_memory"
    state_text = read_text(memory_dir / "state.md")
    current_chapter_match = re.search(r"当前章节[:：]\s*第?(\d+)章", state_text)
    active_arc_match = re.search(r"当前弧[:：]\s*(.+)", state_text)
    characters = parse_character_arcs(memory_dir)
    stalled = [item for item in characters if any(flag in item["risk"] for flag in ("停滞", "重复", "失真"))]

    return {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "current_chapter": int(current_chapter_match.group(1)) if current_chapter_match else 0,
        "active_arc": active_arc_match.group(1).strip() if active_arc_match else "未识别",
        "character_arcs": characters,
        "relation_arcs": parse_relation_arcs(memory_dir),
        "stalled_arc_count": len(stalled),
        "stalled_characters": [item["character"] for item in stalled],
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# 角色弧线报告",
        "",
        f"- 项目：`{payload['project']}`",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 当前章节：`第{payload['current_chapter']:03d}章`",
        f"- 当前弧：`{payload['active_arc']}`",
        f"- 停滞风险角色数：`{payload['stalled_arc_count']}`",
        "",
        "## 风险角色",
    ]
    stalled = payload["stalled_characters"]
    if stalled:
        for name in stalled:
            lines.append(f"- {name}")
    else:
        lines.append("- 无")

    lines.extend(["", "## 角色弧线"])
    for item in payload["character_arcs"][:12]:
        lines.append(
            f"- `{item['character']}` 当前阶段 `{item['stage']}`，目标 `{item['goal']}`，下一窗口 `{item['next_window']}`，风险 `{item['risk']}`"
        )
    if not payload["character_arcs"]:
        lines.append("- 无")
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    project_dir = Path(args.project).resolve()
    payload = build_payload(project_dir)
    reports_dir = project_dir / "05_reports"
    md_path = reports_dir / "arc_health.md"
    json_path = reports_dir / "arc_health.json"
    if not args.dry_run:
        reports_dir.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_markdown(payload), encoding="utf-8")
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"stalled_arc_count={payload['stalled_arc_count']}")
        print(f"markdown={md_path.as_posix()}")
        print(f"json={json_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
