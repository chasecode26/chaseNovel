from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_TEMPLATE_DIR = REPO_ROOT / "templates" / "core"


ASSET_FILENAMES = {
    "platform_profile": "platform-profile.md",
    "prose_examples": "prose-examples.md",
    "pre_publish_checklist": "pre-publish-checklist.md",
    "opening_diagnostics": "opening-diagnostics.md",
    "expectation_lines": "expectation-lines.md",
    "genre_framework": "genre-framework.md",
}


def _read_optional(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def load_market_asset(project_dir: Path, asset_name: str) -> str:
    """Load project-local market guidance, falling back to repo templates."""

    filename = ASSET_FILENAMES.get(asset_name, asset_name)
    project_asset = project_dir / "00_memory" / filename
    template_asset = CORE_TEMPLATE_DIR / filename
    return _read_optional(project_asset) or _read_optional(template_asset)


def load_market_assets(project_dir: Path) -> dict[str, str]:
    return {name: load_market_asset(project_dir, name) for name in ASSET_FILENAMES}


def compact_asset_lines(text: str, *, limit: int = 18) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        lines.append(line)
        if len(lines) >= limit:
            break
    return lines
