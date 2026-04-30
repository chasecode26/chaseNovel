# templates

Templates are organized by owner and runtime usage.

## Directory split

- `templates/core/`: shared book memory carriers and style/voice templates.
- `templates/launch/`: opening, volume, worldbuilding, and readiness templates.
- `templates/agents/`: Claude Code agent prompts and handoff templates.

## Agent templates

Prompt templates:

- `templates/agents/writer-agent.md`
- `templates/agents/lead-writer-agent.md`
- `templates/agents/director-agent.md`
- `templates/agents/scene-beat-agent.md`
- `templates/agents/reviewer-agent.md`
- `templates/agents/rewriter-agent.md`

Handoff templates:

- `templates/agents/writer-handoff.md`
- `templates/agents/reviewer-handoff.md`
- `templates/agents/rewriter-handoff.md`

These are consumed by `runtime/agents/` and copied into `04_gate/chXXX/agent_prompts/` or `04_gate/chXXX/handoffs/` during runtime.

## Core writer stack

- `templates/core/chapter-dramatic-card.md`
- `templates/core/writer-director-prompt.md`
- `templates/core/character-voice-diff.md`
- `templates/core/voice.md`
- `templates/core/style.md`
- `templates/core/style-guardrails.md`
- `templates/core/platform-profile.md`
- `templates/core/prose-examples.md`
- `templates/core/pre-publish-checklist.md`
- `templates/core/opening-diagnostics.md`
- `templates/core/expectation-lines.md`
- `templates/core/genre-framework.md`

## Notes

- Do not add a second review-template directory. Reviewer/Rewriter handoff now lives under `templates/agents/`.
- Keep paths stable; runtime report paths are designed for Claude Code to read directly.
- Platform, opening, expectation, genre, and prose assets may be copied into `00_memory/` for a specific book. If absent, runtime falls back to the repo templates targeting Fanqie/Qimao.
