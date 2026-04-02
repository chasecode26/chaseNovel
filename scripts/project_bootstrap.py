#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


DIRS = [
    "00_memory",
    "00_memory/retrieval",
    "00_memory/summaries",
    "01_outline",
    "02_knowledge",
    "03_chapters",
    "04_gate",
    "05_reports",
    "06_exports",
]

TEMPLATE_MAP = {
    "00_memory/plan.md": "plan.md",
    "00_memory/state.md": "state.md",
    "00_memory/arc_progress.md": "arc-progress.md",
    "00_memory/characters.md": "characters.md",
    "00_memory/character_arcs.md": "character-arcs.md",
    "00_memory/timeline.md": "timeline.md",
    "00_memory/foreshadowing.md": "foreshadowing.md",
    "00_memory/payoff_board.md": "payoff-board.md",
    "00_memory/style.md": "style.md",
    "00_memory/voice.md": "voice.md",
    "00_memory/scene_preferences.md": "scene_preferences.md",
    "00_memory/findings.md": "findings.md",
    "00_memory/summaries/recent.md": "summaries_recent.md",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap a chaseNovel project directory from templates."
    )
    parser.add_argument("--project", required=True, help="Path to the new or existing novel project root")
    parser.add_argument("--templates-root", help="Optional templates directory")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    return parser.parse_args()


def copy_template(src: Path, dst: Path, force: bool) -> None:
    if dst.exists() and not force:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    project_dir = Path(args.project).resolve()
    templates_root = Path(args.templates_root).resolve() if args.templates_root else (Path(__file__).resolve().parent.parent / "templates")
    project_dir.mkdir(parents=True, exist_ok=True)
    for rel_dir in DIRS:
        (project_dir / rel_dir).mkdir(parents=True, exist_ok=True)
    for rel_path, template_name in TEMPLATE_MAP.items():
        copy_template(templates_root / template_name, project_dir / rel_path, args.force)
    print(f"project={project_dir.as_posix()}")
    print("status=bootstrapped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
