# chaseNovel Architecture

## Goal

`chaseNovel` is a local writing engine for long-running Chinese web novels. The current architecture is optimized for Claude Code: local scripts build memory, handoff files, review reports, rewrite scopes, and release gates; Claude Code acts as the intelligent writing executor.

## Layer Model

### Layer 1: Entry

- `README.md`
- `SKILL.md`
- `docs/core/task-contracts.md`

Responsibilities:

- Public routing
- Task contracts
- Chapter semantics
- Human-facing explanation of the shipped workflow

### Layer 2: Runtime Facts

- `docs/core/runtime-design-baseline.md`

Responsibilities:

- Record the shipped runtime behavior
- Resolve conflicts between docs and implementation
- Describe the active agent loop

### Layer 3: Command Surface

- `bin/chase.js`
- `scripts/workflow_runner.py`
- `scripts/open_book.py`
- `scripts/quality_gate.py`
- `scripts/book_health.py`

Public commands:

- `chase open`
- `chase write`
- `chase quality`
- `chase status`
- `chase check`

Default `write` chain:

```text
open -> runtime -> quality -> status
```

Default `check` chain:

```text
open -> quality -> status
```

### Layer 4: Runtime Agent Core

- `runtime/runtime_orchestrator.py`
- `runtime/agents/`
- `runtime/decision_engine.py`
- `runtime/release_policy.py`
- `runtime/memory_sync.py`

Runtime writing loop:

```text
MemoryCompiler
-> LeadWriterAgent
-> DirectorAgent
-> SceneBeatAgent
-> WriterAgent
-> ReviewerAgent
-> DecisionEngine
-> RewriterAgent
-> ReleasePolicy
-> RuntimeMemorySync
```

Agent modules:

- `runtime/agents/writer.py`
- `runtime/agents/lead_writer.py`
- `runtime/agents/director.py`
- `runtime/agents/scene_beat.py`
- `runtime/agents/reviewer.py`
- `runtime/agents/rewriter.py`
- `runtime/agents/writer_executor.py`
- `runtime/agents/scene_beat_planner.py`
- `runtime/agents/handoff.py`
- `runtime/agents/local_rewrite.py`
- `runtime/agents/prompt_loader.py`
- `runtime/agents/model_gateway.py`

### Layer 5: Evaluators And Quality

- `evaluators/`
- `runtime/quality_service.py`
- `scripts/chapter_gate.py`
- `scripts/draft_gate.py`
- `scripts/language_audit.py`
- `scripts/anti_repeat_scan.py`

Responsibilities:

- Produce structured `EvaluatorVerdict`
- Diagnose, not directly rewrite
- Feed `DecisionEngine` and `ReleasePolicy`

### Layer 6: Memory And Templates

- `00_memory/schema/*.json`
- `00_memory/*.md`
- `templates/core/`
- `templates/launch/`
- `templates/agents/`

Rules:

- Schema JSON is the runtime truth source.
- Markdown memory is the human-readable layer and fallback input.
- Agent prompt and handoff templates live only in `templates/agents/`.

## Claude Code Handoff

The project does not require an embedded LLM provider. Runtime writes strong handoff files for Claude Code to consume.

Per-chapter outputs:

```text
04_gate/chXXX/agent_prompts/
04_gate/chXXX/handoffs/
04_gate/chXXX/scene_beat_plan.md
04_gate/chXXX/reviewer_agent_report.md
04_gate/chXXX/release_gate_report.md
04_gate/chXXX/agent_replay_report.md
```

These files are the primary collaboration surface between the local runtime and Claude Code.

## Chapter Semantics

- `--chapter <n>` means an existing reference chapter.
- `open` defaults to `target_chapter = n + 1`.
- `runtime / quality / status` consume the reference chapter.
- Use `--target-chapter <m>` for explicit skip, patch, or retarget operations.

## Cleanup Policy

- Do not keep duplicate old-path templates once an agent template exists.
- Do not keep CLI entries that point to missing directories.
- Do not keep a second runtime truth source.
- If docs conflict with runtime behavior, update docs to match shipped code.
