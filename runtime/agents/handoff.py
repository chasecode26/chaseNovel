from __future__ import annotations

import json
from pathlib import Path

from runtime.agents.prompt_loader import load_agent_prompt


def _chapter_dir(project_dir: Path, chapter: int) -> Path:
    path = project_dir / "04_gate" / f"ch{chapter:03d}" / "handoffs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_handoff(project_dir: Path, chapter: int, name: str, payload: dict[str, object], markdown: str) -> dict[str, str]:
    handoff_dir = _chapter_dir(project_dir, chapter)
    json_path = handoff_dir / f"{name}.json"
    md_path = handoff_dir / f"{name}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(markdown.strip() + "\n", encoding="utf-8")
    return {f"{name}_json": json_path.as_posix(), f"{name}_markdown": md_path.as_posix()}


def write_writer_handoff(
    project_dir: Path,
    chapter: int,
    *,
    brief: dict[str, object],
    direction: dict[str, object],
    scene_beat_plan: dict[str, object],
    paths: dict[str, str],
    market_assets: dict[str, str] | None = None,
) -> dict[str, str]:
    template = load_agent_prompt("writer-handoff")
    market_assets = market_assets or {}
    payload = {
        "agent": "WriterAgent",
        "chapter": chapter,
        "brief": brief,
        "direction": direction,
        "scene_beat_plan": scene_beat_plan,
        "market_assets": market_assets,
        "paths": paths,
        "completion_checklist": [
            "正文只写小说内容，不写解释。",
            "每段至少两种场面信号。",
            "chapter_result 与 next_pull 都落在正文中。",
            "章尾有表层事件钩子和里层代价钩子。",
            "符合番茄/七猫平台画像，不用抽象总结替代现场。",
        ],
    }
    markdown = "\n\n".join(
        [
            template,
            "## Runtime Inputs",
            f"- chapter: {chapter}",
            f"- writer_prompt: {paths.get('writer_prompt_path', '') or 'missing'}",
            f"- scene_beat_plan: {paths.get('scene_beat_plan_markdown', '') or 'missing'}",
            f"- manuscript_output: {paths.get('manuscript_path', '') or 'missing'}",
            "",
            "## Chapter Result Target",
            f"- {brief.get('result_change', '') or brief.get('chapter_function', '') or 'missing'}",
            "",
            "## Ending Pull Target",
            f"- {brief.get('closing_hook', '') or brief.get('hook_goal', '') or 'missing'}",
            "",
            "## Market Assets",
            f"- platform_profile: {'loaded' if market_assets.get('platform_profile') else 'missing'}",
            f"- prose_examples: {'loaded' if market_assets.get('prose_examples') else 'missing'}",
            f"- pre_publish_checklist: {'loaded' if market_assets.get('pre_publish_checklist') else 'missing'}",
            f"- opening_diagnostics: {'loaded' if market_assets.get('opening_diagnostics') else 'missing'}",
            f"- expectation_lines: {'loaded' if market_assets.get('expectation_lines') else 'missing'}",
            f"- genre_framework: {'loaded' if market_assets.get('genre_framework') else 'missing'}",
        ]
    )
    return _write_handoff(project_dir, chapter, "writer_handoff", payload, markdown)


def write_reviewer_handoff(
    project_dir: Path,
    chapter: int,
    *,
    draft_payload: dict[str, object],
    verdicts: list[dict[str, object]],
    paths: dict[str, str],
) -> dict[str, str]:
    template = load_agent_prompt("reviewer-handoff")
    blocking = [item for item in verdicts if item.get("blocking")]
    payload = {
        "agent": "ReviewerAgent",
        "chapter": chapter,
        "draft": draft_payload,
        "verdicts": verdicts,
        "blocking_dimensions": [str(item.get("dimension", "")) for item in blocking],
        "paths": paths,
    }
    markdown = "\n\n".join(
        [
            template,
            "## Runtime Inputs",
            f"- manuscript: {draft_payload.get('manuscript_path', '') or 'missing'}",
            f"- scene_beat_plan: {draft_payload.get('scene_beat_plan_markdown', '') or paths.get('scene_beat_plan_markdown', '') or 'missing'}",
            f"- reviewer_report: {paths.get('reviewer_agent_report_markdown', '') or 'missing'}",
            "",
            "## Blocking Dimensions",
            "\n".join(f"- {item.get('dimension')}: {item.get('minimal_fix')}" for item in blocking) or "- none",
        ]
    )
    return _write_handoff(project_dir, chapter, "reviewer_handoff", payload, markdown)


def write_rewriter_handoff(
    project_dir: Path,
    chapter: int,
    *,
    rewrite_brief: dict[str, object],
    draft_payload: dict[str, object],
    paths: dict[str, str],
) -> dict[str, str]:
    template = load_agent_prompt("rewriter-handoff")
    payload = {
        "agent": "RewriterAgent",
        "chapter": chapter,
        "rewrite_brief": rewrite_brief,
        "draft": draft_payload,
        "paths": paths,
        "local_surgery": {
            "scope": rewrite_brief.get("rewrite_scope", ""),
            "first_fix_priority": rewrite_brief.get("first_fix_priority", ""),
            "must_change": rewrite_brief.get("must_change", []),
            "must_preserve": rewrite_brief.get("must_preserve", []),
        },
    }
    markdown = "\n\n".join(
        [
            template,
            "## Runtime Inputs",
            f"- original_snapshot: {draft_payload.get('original_manuscript_snapshot_path', '') or paths.get('original_manuscript_snapshot_path', '') or 'missing'}",
            f"- reviewer_report: {paths.get('reviewer_agent_report_markdown', '') or 'missing'}",
            f"- rewrite_operation: {draft_payload.get('rewrite_operation_path', '') or paths.get('rewrite_operation_path', '') or 'pending'}",
            "",
            "## RewriteBrief",
            f"- first_fix_priority: {rewrite_brief.get('first_fix_priority', '') or 'missing'}",
            f"- rewrite_scope: {rewrite_brief.get('rewrite_scope', '') or 'missing'}",
            "- must_change:",
            "\n".join(f"  - {item}" for item in rewrite_brief.get("must_change", []) or ["missing"]),
        ]
    )
    return _write_handoff(project_dir, chapter, "rewriter_handoff", payload, markdown)
