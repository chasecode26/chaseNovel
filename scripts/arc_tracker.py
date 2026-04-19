#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from novel_utils import clean_value, detect_current_chapter, extract_pipe_table_rows, extract_state_value, read_text


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a lightweight arc tracking report for a chaseNovel project."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    return parser.parse_args()


def parse_character_arcs(memory_dir: Path) -> list[dict[str, str]]:
    schema_payload = load_json(memory_dir / "schema" / "character_arcs.json")
    schema_arcs = schema_payload.get("arcs", [])
    if isinstance(schema_arcs, list) and schema_arcs:
        results: list[dict[str, str]] = []
        for item in schema_arcs:
            if not isinstance(item, dict):
                continue
            character = str(item.get("character", "")).strip()
            if not character:
                continue
            results.append(
                {
                    "character": character,
                    "arc_type": str(item.get("arcType", "")).strip(),
                    "stage": str(item.get("stage", "")).strip(),
                    "goal": str(item.get("goal", "")).strip(),
                    "blocker": str(item.get("blocker", "")).strip(),
                    "latest_shift": str(item.get("recentChange", "")).strip(),
                    "next_window": str(item.get("nextWindow", "")).strip(),
                    "risk": str(item.get("risk", "")).strip(),
                }
            )
        if results:
            return results

    rows = extract_pipe_table_rows(read_text(memory_dir / "character_arcs.md"))
    results: list[dict[str, str]] = []
    for row in rows[1:]:
        if len(row) < 8 or not row[0] or row[0] in {"角色", "关系对"}:
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
    rows = extract_pipe_table_rows(read_text(memory_dir / "character_arcs.md"))
    results: list[dict[str, str]] = []
    for row in rows[1:]:
        if len(row) != 6 or not row[0] or row[0] in {"关系对", "角色"}:
            continue
        results.append(
            {
                "pair": row[0],
                "position": row[1],
                "latest_shift": row[2],
                "tension": row[3],
                "next_mode": row[4],
                "repeat_risk": row[5],
            }
        )
    return results


def build_payload(project_dir: Path) -> dict[str, object]:
    memory_dir = project_dir / "00_memory"
    state_text = read_text(memory_dir / "state.md")
    characters = parse_character_arcs(memory_dir)
    stalled = [
        item for item in characters if any(flag in item["risk"] for flag in ("停滞", "重复", "失真"))
    ]
    warnings: list[str] = []
    if not characters:
        warnings.append("角色弧表为空，当前只能做轻量结构检查。")
    if stalled:
        warnings.append(f"检测到 {len(stalled)} 个角色弧存在停滞/重复/失真风险。")
    status = "warn" if warnings else "pass"

    return {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "current_chapter": detect_current_chapter(state_text),
        "active_arc": clean_value(extract_state_value(state_text, "当前弧")),
        "character_arcs": characters,
        "relation_arcs": parse_relation_arcs(memory_dir),
        "stalled_arc_count": len(stalled),
        "stalled_characters": [item["character"] for item in stalled],
        "warnings": warnings,
        "warning_count": len(warnings),
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
        lines.extend(f"- {name}" for name in stalled)
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
        print(f"warning_count={payload['warning_count']}")
        print(f"stalled_arc_count={payload['stalled_arc_count']}")
        print(f"markdown={payload['report_paths']['markdown']}")
        print(f"json={payload['report_paths']['json']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
