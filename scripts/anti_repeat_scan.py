#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path


HOOK_PATTERNS = {
    "threat": ("危机", "危险", "杀", "追", "出事", "暴露"),
    "reveal": ("真相", "发现", "原来", "身份", "秘密"),
    "emotion": ("心乱", "沉默", "对视", "靠近", "分开"),
    "reward": ("突破", "到账", "升级", "奖励", "收获"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan recent chapter summaries for repeated hook and conflict patterns."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    return parser.parse_args()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").lstrip("\ufeff")


def split_summary_entries(text: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    blocks = re.split(r"\n(?=##\s*第?\d+章)", text)
    for block in blocks:
        stripped = block.strip()
        if not stripped:
            continue
        heading_match = re.search(r"##\s*第?(\d+)章[:：]?\s*(.*)", stripped)
        if not heading_match:
            continue
        entries.append(
            {
                "chapter": heading_match.group(1),
                "title": heading_match.group(2).strip(),
                "body": stripped,
            }
        )
    return entries


def classify_hook(text: str) -> str:
    for label, patterns in HOOK_PATTERNS.items():
        if any(pattern in text for pattern in patterns):
            return label
    return "unknown"


def detect_repeat_risks(entries: list[dict[str, str]]) -> dict[str, object]:
    hook_counter: Counter[str] = Counter()
    opener_counter: Counter[str] = Counter()
    for entry in entries:
        body = entry["body"]
        hook_counter[classify_hook(body)] += 1
        first_line = next((line.strip() for line in body.splitlines() if line.strip().startswith("-")), "")
        if first_line:
            opener_counter[first_line[:18]] += 1

    warnings: list[str] = []
    for label, count in hook_counter.items():
        if label != "unknown" and count >= 3:
            warnings.append(f"近章 `{label}` 型钩子出现 {count} 次，存在重复风险。")
    for opener, count in opener_counter.items():
        if count >= 3:
            warnings.append(f"近章摘要开头模式重复 {count} 次：{opener}")

    return {
        "hook_counter": dict(hook_counter),
        "opener_counter": dict(opener_counter.most_common(10)),
        "warnings": warnings,
    }


def collect_chapter_files(project_dir: Path) -> list[Path]:
    chapters_dir = project_dir / "03_chapters"
    items: list[tuple[int, Path]] = []
    if not chapters_dir.exists():
        return []
    for path in chapters_dir.iterdir():
        if not path.is_file():
            continue
        match = re.search(r"(\d+)", path.stem)
        if not match:
            continue
        items.append((int(match.group(1)), path))
    items.sort(key=lambda item: item[0])
    return [path for _, path in items[-12:]]


def detect_body_patterns(project_dir: Path) -> dict[str, object]:
    opening_counter: Counter[str] = Counter()
    hook_counter: Counter[str] = Counter()
    for path in collect_chapter_files(project_dir):
        content = read_text(path)
        lines = [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith("#")]
        if lines:
            opening_counter[lines[0][:24]] += 1
            tail = "\n".join(lines[-5:])
            hook_counter[classify_hook(tail)] += 1
    warnings: list[str] = []
    for opener, count in opening_counter.items():
        if count >= 3:
            warnings.append(f"近章正文开头模式重复 {count} 次：{opener}")
    for label, count in hook_counter.items():
        if label != "unknown" and count >= 3:
            warnings.append(f"近章正文结尾 `{label}` 型钩子重复 {count} 次。")
    return {
        "body_openers": dict(opening_counter.most_common(10)),
        "body_hooks": dict(hook_counter),
        "warnings": warnings,
    }


def build_payload(project_dir: Path) -> dict[str, object]:
    recent_path = project_dir / "00_memory" / "summaries" / "recent.md"
    entries = split_summary_entries(read_text(recent_path))
    analysis = detect_repeat_risks(entries)
    body_analysis = detect_body_patterns(project_dir)
    return {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "entry_count": len(entries),
        "hook_counter": analysis["hook_counter"],
        "opener_counter": analysis["opener_counter"],
        "body_openers": body_analysis["body_openers"],
        "body_hooks": body_analysis["body_hooks"],
        "warnings": analysis["warnings"] + body_analysis["warnings"],
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# 反重复扫描报告",
        "",
        f"- 项目：`{payload['project']}`",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 近章条目数：`{payload['entry_count']}`",
        f"- 钩子分布：`{json.dumps(payload['hook_counter'], ensure_ascii=False)}`",
        f"- 正文结尾钩子：`{json.dumps(payload['body_hooks'], ensure_ascii=False)}`",
        "",
        "## 预警",
    ]
    if payload["warnings"]:
        lines.extend([f"- {item}" for item in payload["warnings"]])
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
    md_path = reports_dir / "anti_repeat.md"
    json_path = reports_dir / "anti_repeat.json"
    if not args.dry_run:
        reports_dir.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_markdown(payload), encoding="utf-8")
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"entry_count={payload['entry_count']}")
        print(f"warning_count={len(payload['warnings'])}")
        print(f"markdown={md_path.as_posix()}")
        print(f"json={json_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
