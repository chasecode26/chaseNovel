from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_TEMPLATE_DIR = REPO_ROOT / "templates" / "agents"


def load_agent_prompt(name: str) -> str:
    path = AGENT_TEMPLATE_DIR / f"{name}.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def write_agent_prompt_snapshot(project_dir: Path, chapter: int, agent_name: str, prompt_text: str) -> str:
    if not prompt_text.strip():
        return ""
    prompt_dir = project_dir / "04_gate" / f"ch{chapter:03d}" / "agent_prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    path = prompt_dir / f"{agent_name}.md"
    path.write_text(prompt_text.strip() + "\n", encoding="utf-8")
    return path.as_posix()
