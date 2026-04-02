# chaseNovel Architecture

## Goal

`chaseNovel` is evolving from a pure writing skill into a local writing operating system for long-form Chinese web novels. The target is stable support for projects that run for hundreds of chapters and approach or exceed one million Chinese characters.

The system is designed for a single primary author working locally. It prioritizes:

- low-friction chat-driven writing
- durable project memory
- chapter and book level validation
- recovery after breaks
- controlled evolution instead of a heavy product rebuild

## Design Principles

1. `skill` remains the primary interaction entry.
2. Long-term state lives in project files, not transient chat context.
3. Repetitive governance work moves into scripts and reports.
4. Chapter drafting and book governance are separate concerns.
5. GUI is optional and deferred until the local workflow is proven.

## Runtime Layers

### Layer 1: Interaction

- Codex or Claude skill
- slash-command style prompts
- planner / drafter / reviser conversation workflow

### Layer 2: Orchestration

- `chase` CLI
- local workflow runner
- context compilation entrypoints
- report generation commands

### Layer 3: Book Engine

- project memory files
- foreshadow scheduling
- arc tracking
- timeline validation
- anti-repeat analysis
- voice and style governance

### Layer 4: Analysis and Reporting

- `chapter_gate.py`
- `language_audit.py`
- `batch_gate.py`
- dashboard snapshots
- future regression reports

## Repository Layout

```text
repo/
├─ ARCHITECTURE.md
├─ SKILL.md
├─ bin/
│  ├─ chase-novel-skill.js
│  └─ chase.js
├─ scripts/
│  ├─ chapter_gate.py
│  ├─ batch_gate.py
│  ├─ language_audit.py
│  ├─ context_compiler.py
│  ├─ foreshadow_scheduler.py
│  ├─ arc_tracker.py
│  ├─ timeline_check.py
│  ├─ anti_repeat_scan.py
│  ├─ dashboard_snapshot.py
│  ├─ project_bootstrap.py
│  ├─ memory_update.py
│  ├─ workflow_runner.py
│  └─ install-skill.js
├─ schemas/
│  ├─ project_state.schema.json
│  ├─ foreshadow.schema.json
│  └─ arc.schema.json
├─ references/
├─ templates/
└─ technique-kb/
```

## Novel Project Layout

```text
novel_{book}/
├─ 00_memory/
│  ├─ plan.md
│  ├─ state.md
│  ├─ arc_progress.md
│  ├─ characters.md
│  ├─ character_arcs.md
│  ├─ timeline.md
│  ├─ foreshadowing.md
│  ├─ payoff_board.md
│  ├─ style.md
│  ├─ voice.md
│  ├─ scene_preferences.md
│  └─ retrieval/
│     ├─ next_context.md
│     └─ dashboard_cache.json
├─ 01_outline/
├─ 02_knowledge/
├─ 03_chapters/
├─ 04_gate/
├─ 05_reports/
└─ 06_exports/
```

## Core Workflows

1. Chapter planning uses `context_compiler.py` to build the minimum next-chapter context package.
2. Chapter drafting remains skill-driven and focuses on functional story advancement.
3. Revision uses style and voice constraints plus `language_audit.py`.
4. Chapter governance uses `chapter_gate.py` and `dashboard_snapshot.py`.
5. Book health review uses `batch_gate.py`, `foreshadow_scheduler.py`, and `dashboard_snapshot.py`.

## Phase 1 Deliverables

- unified `chase` CLI wrapper
- context compiler
- foreshadow scheduler
- dashboard snapshot generator
- voice and scene preference templates
- JSON schemas for future automation

## Phase 2 Deliverables

- arc health tracker
- timeline consistency check
- anti-repeat scan for recent summaries
- project bootstrap command for new books
- memory update helper after chapter drafting
- workflow runner that chains local governance steps

## Command Surface

```bash
chase context --project novel_x --chapter 128
chase foreshadow --project novel_x --chapter 128
chase dashboard --project novel_x
chase arc --project novel_x
chase timeline --project novel_x
chase repeat --project novel_x
chase memory --project novel_x --chapter 128
chase gate --project novel_x --chapter 128
chase batch --project novel_x --from 101 --to 130
chase bootstrap --project novel_x
chase run --project novel_x --chapter 128
```

## Why This Shape

This architecture is intentionally hybrid:

- chat remains the fastest writing surface
- Python scripts remain the cheapest automation layer
- markdown memory remains the most transparent storage format

That combination is strong enough for a single-author million-character workflow without the cost of building a full writing platform too early.
