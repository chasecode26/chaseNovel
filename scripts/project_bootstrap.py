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
    "00_memory/plan.md": "core/plan.md",
    "00_memory/state.md": "core/state.md",
    "00_memory/arc_progress.md": "core/arc-progress.md",
    "00_memory/characters.md": "core/characters.md",
    "00_memory/character_arcs.md": "core/character-arcs.md",
    "00_memory/character-voice-diff.md": "core/character-voice-diff.md",
    "00_memory/timeline.md": "core/timeline.md",
    "00_memory/foreshadowing.md": "core/foreshadowing.md",
    "00_memory/payoff_board.md": "core/payoff-board.md",
    "00_memory/style.md": "core/style.md",
    "00_memory/style_guardrails.md": "core/style-guardrails.md",
    "00_memory/voice.md": "core/voice.md",
    "00_memory/scene_preferences.md": "core/scene_preferences.md",
    "00_memory/findings.md": "core/findings.md",
    "00_memory/summaries/recent.md": "core/summaries_recent.md",
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


def resolve_template(templates_root: Path, template_name: str) -> Path:
    direct = templates_root / template_name
    if direct.exists():
        return direct
    legacy = templates_root / Path(template_name).name
    if legacy.exists():
        return legacy
    raise FileNotFoundError(f"template not found: {template_name}")


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
        copy_template(resolve_template(templates_root, template_name), project_dir / rel_path, args.force)
    print(f"project={project_dir.as_posix()}")
    print("status=bootstrapped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
