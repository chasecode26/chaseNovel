#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


CHAPTER_PATTERN = re.compile(r"(\d+)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update lightweight project memory after a chapter is drafted."
    )
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument("--chapter", type=int, help="Target chapter number; defaults to the latest chapter")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    return parser.parse_args()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").lstrip("\ufeff")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def detect_latest_chapter(project_dir: Path) -> tuple[int, Path | None]:
    chapters_dir = project_dir / "03_chapters"
    latest_no = 0
    latest_path: Path | None = None
    if not chapters_dir.exists():
        return latest_no, latest_path
    for path in chapters_dir.iterdir():
        if not path.is_file():
            continue
        match = CHAPTER_PATTERN.search(path.stem)
        if not match:
            continue
        chapter_no = int(match.group(1))
        if chapter_no > latest_no:
            latest_no = chapter_no
            latest_path = path
    return latest_no, latest_path


def replace_or_append_line(text: str, label: str, value: str) -> str:
    pattern = re.compile(rf"(^-?\s*{re.escape(label)}[:：]\s*).*$", re.MULTILINE)
    replacement = rf"\1{value}"
    if pattern.search(text):
        return pattern.sub(replacement, text, count=1)
    if text and not text.endswith("\n"):
        text += "\n"
    return text + f"- {label}：{value}\n"


def extract_title_and_summary(chapter_path: Path) -> tuple[str, list[str]]:
    content = read_text(chapter_path)
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    title = lines[0] if lines else f"第{chapter_path.stem}章"
    bullets: list[str] = []
    for line in lines[1:]:
        if line.startswith("#"):
            continue
        if len(line) >= 12:
            bullets.append(line[:60].rstrip("，。；、,."))
        if len(bullets) == 3:
            break
    return title, bullets


def append_recent_summary(recent_text: str, chapter_no: int, title: str, bullets: list[str]) -> str:
    if re.search(rf"##\s*第?0*{chapter_no}章", recent_text):
        return recent_text
    block = [f"## 第{chapter_no:03d}章：{title}"]
    if bullets:
        for bullet in bullets:
            block.append(f"- {bullet}")
    else:
        block.append("- 待补本章摘要")
    addition = "\n".join(block) + "\n"
    if recent_text and not recent_text.endswith("\n\n"):
        recent_text = recent_text.rstrip("\n") + "\n\n"
    return recent_text + addition


def build_memory_report(project_dir: Path, chapter_no: int, title: str) -> str:
    return "\n".join(
        [
            "# 记忆回写报告",
            "",
            f"- 章节：第{chapter_no:03d}章",
            f"- 标题：{title}",
            f"- 生成时间：{datetime.now().isoformat(timespec='seconds')}",
            "",
            "## 已自动完成",
            "- 更新 `state.md` 的当前章节与最后更新日期",
            "- 追加 `summaries/recent.md` 的本章摘要占位",
            "",
            "## 待人工确认",
            "- 若本章新增伏笔，补写 `foreshadowing.md`",
            "- 若本章改变人物阶段，补写 `character_arcs.md`",
            "- 若本章发生跳时或绝对时间锚点变化，补写 `timeline.md`",
            "- 若本章明确了承诺兑现或延后，补写 `payoff_board.md`",
            "",
        ]
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    project_dir = Path(args.project).resolve()
    chapter_no, chapter_path = detect_latest_chapter(project_dir)
    target_chapter = args.chapter or chapter_no
    if target_chapter <= 0:
        payload = {
            "project": project_dir.as_posix(),
            "updated": False,
            "reason": "no chapters found",
            "status": "warn",
            "warnings": ["当前未检测到章节文件，无法执行记忆回写。"],
            "warning_count": 1,
            "report_paths": {},
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print("status=warn")
            print("warning_count=1")
            print("updated=false")
            print("reason=no chapters found")
        return 0

    if chapter_path is None or (args.chapter and CHAPTER_PATTERN.search(chapter_path.stem) and int(CHAPTER_PATTERN.search(chapter_path.stem).group(1)) != target_chapter):
        target_path = None
        for path in (project_dir / "03_chapters").iterdir():
            match = CHAPTER_PATTERN.search(path.stem)
            if path.is_file() and match and int(match.group(1)) == target_chapter:
                target_path = path
                break
        chapter_path = target_path

    if chapter_path is None:
        raise SystemExit(f"chapter file not found for chapter {target_chapter}")

    memory_dir = project_dir / "00_memory"
    state_path = memory_dir / "state.md"
    recent_path = memory_dir / "summaries" / "recent.md"
    title, bullets = extract_title_and_summary(chapter_path)

    state_text = read_text(state_path)
    state_text = replace_or_append_line(state_text, "当前章节", f"第{target_chapter:03d}章")
    state_text = replace_or_append_line(state_text, "最后更新", datetime.now().strftime("%Y-%m-%d"))

    recent_text = append_recent_summary(read_text(recent_path), target_chapter, title, bullets)
    report_path = project_dir / "04_gate" / f"ch{target_chapter:03d}" / "memory_update.md"
    payload = {
        "project": project_dir.as_posix(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "pass",
        "updated": True,
        "chapter": target_chapter,
        "state_path": state_path.as_posix(),
        "recent_path": recent_path.as_posix(),
        "report_path": report_path.as_posix(),
        "warnings": [],
        "warning_count": 0,
        "report_paths": {
            "memory_report": report_path.as_posix(),
            "state": state_path.as_posix(),
            "recent": recent_path.as_posix(),
        },
    }
    if args.dry_run:
        payload["warnings"].append("dry-run 模式未实际写入 state.md、recent.md 与 memory_update.md。")
        payload["warning_count"] = len(payload["warnings"])
        payload["status"] = "warn"

    if not args.dry_run:
        write_text(state_path, state_text)
        write_text(recent_path, recent_text)
        write_text(report_path, build_memory_report(project_dir, target_chapter, title))

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"warning_count={payload['warning_count']}")
        print(f"updated=true")
        print(f"chapter={target_chapter}")
        print(f"report={payload['report_paths']['memory_report']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
