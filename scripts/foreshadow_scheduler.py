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
        description="Build foreshadow due reports for a chaseNovel project."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--chapter", type=int, help="Reference chapter number")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    return parser.parse_args()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").lstrip("\ufeff")


def detect_current_chapter(state_text: str) -> int:
    match = re.search(r"当前章节[:：]\s*第?(\d+)章", state_text)
    return int(match.group(1)) if match else 0


def parse_priority(raw: str) -> str:
    if "高" in raw:
        return "high"
    if "中" in raw:
        return "medium"
    if "低" in raw:
        return "low"
    return "unknown"


def parse_status(raw: str) -> str:
    mapping = {"待回收": "active", "已激活": "triggered", "已回收": "resolved", "已延后": "delayed", "已废弃": "abandoned"}
    for key, value in mapping.items():
        if key in raw:
            return value
    return "active"


def parse_rows(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in read_text(path).splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "----" in stripped or "ID" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 9:
            continue
        item_id = cells[0]
        if not item_id:
            continue
        seed_match = re.search(r"(\d+)", cells[1])
        due_match = re.search(r"(\d+)", cells[6])
        rows.append(
            {
                "id": item_id,
                "seed_chapter": int(seed_match.group(1)) if seed_match else 0,
                "content": cells[2],
                "who_knows": cells[3],
                "trigger_condition": cells[4],
                "invalid_condition": cells[5],
                "due_chapter": int(due_match.group(1)) if due_match else None,
                "priority": parse_priority(cells[7]),
                "status": parse_status(cells[8]),
            }
        )
    return rows


def compute_heat(target_chapter: int, seed_chapter: int) -> str:
    if seed_chapter <= 0:
        return "unknown"
    distance = target_chapter - seed_chapter
    if distance <= 8:
        return "high"
    if distance <= 20:
        return "medium"
    return "low"


def classify_items(rows: list[dict[str, object]], target_chapter: int) -> dict[str, list[dict[str, object]]]:
    due: list[dict[str, object]] = []
    overdue: list[dict[str, object]] = []
    active: list[dict[str, object]] = []

    for row in rows:
        if row["status"] in {"resolved", "abandoned"}:
            continue
        row["reader_memory_heat"] = compute_heat(target_chapter, int(row["seed_chapter"]))
        due_chapter = row["due_chapter"]
        if due_chapter is not None and due_chapter < target_chapter:
            overdue.append(row)
        elif due_chapter is not None and due_chapter == target_chapter:
            due.append(row)
        else:
            active.append(row)

    return {"due": due, "overdue": overdue, "active": active}


def render_markdown(project_dir: Path, target_chapter: int, groups: dict[str, list[dict[str, object]]]) -> str:
    lines = [
        "# 伏笔调度报告",
        "",
        f"- 项目：`{project_dir.as_posix()}`",
        f"- 参考章节：`第{target_chapter:03d}章`",
        f"- 生成时间：`{datetime.now().isoformat(timespec='seconds')}`",
        "",
        "## 到期伏笔",
    ]
    if groups["due"]:
        for item in groups["due"]:
            lines.append(f"- `{item['id']}` 第{item['seed_chapter']}章埋设，当前应回收；热度 `{item['reader_memory_heat']}`；内容：{item['content']}")
    else:
        lines.append("- 无")

    lines.extend(["", "## 超期伏笔"])
    if groups["overdue"]:
        for item in groups["overdue"]:
            lines.append(f"- `{item['id']}` 已超期；计划回收章：{item['due_chapter']}；当前状态：{item['status']}；内容：{item['content']}")
    else:
        lines.append("- 无")

    lines.extend(["", "## 活跃伏笔"])
    if groups["active"]:
        for item in groups["active"][:12]:
            due_text = f"第{item['due_chapter']}章" if item["due_chapter"] is not None else "未指定"
            lines.append(f"- `{item['id']}` 计划回收：{due_text}；热度 `{item['reader_memory_heat']}`；内容：{item['content']}")
    else:
        lines.append("- 无")

    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    project_dir = Path(args.project).resolve()
    state_text = read_text(project_dir / "00_memory" / "state.md")
    target_chapter = args.chapter or detect_current_chapter(state_text)
    foreshadow_path = project_dir / "00_memory" / "foreshadowing.md"
    rows = parse_rows(foreshadow_path) if foreshadow_path.exists() else []
    groups = classify_items(rows, target_chapter)

    reports_dir = project_dir / "05_reports"
    md_path = reports_dir / "foreshadow_heatmap.md"
    json_path = reports_dir / "foreshadow_heatmap.json"
    payload = {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "chapter": target_chapter,
        "due": groups["due"],
        "overdue": groups["overdue"],
        "active": groups["active"][:50],
        "warnings": [],
        "warning_count": 0,
    }
    if not rows:
        payload["warnings"].append("伏笔表为空，当前没有可调度条目。")
    if groups["overdue"]:
        payload["warnings"].append(f"存在 {len(groups['overdue'])} 条超期伏笔，应优先处理。")
    payload["warning_count"] = len(payload["warnings"])
    payload["status"] = "warn" if payload["warnings"] else "pass"
    payload["report_paths"] = {
        "markdown": md_path.as_posix(),
        "json": json_path.as_posix(),
    }

    if not args.dry_run:
        reports_dir.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_markdown(project_dir, target_chapter, groups), encoding="utf-8")
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"warning_count={payload['warning_count']}")
        print(f"chapter={target_chapter}")
        print(f"due={len(groups['due'])}")
        print(f"overdue={len(groups['overdue'])}")
        print(f"markdown={payload['report_paths']['markdown']}")
        print(f"json={payload['report_paths']['json']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
