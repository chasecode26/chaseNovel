# chaseNovel Architecture

## Goal

`chaseNovel` is a repo-local writing skill plus a small set of helper scripts for long-form Chinese web novels. The goal is stable support for projects that run for hundreds of chapters without turning the repo into a heavy product.

The system is designed for a single primary author working locally. It prioritizes:

- low-friction chat-driven writing
- durable project memory
- chapter and book level validation
- recovery after breaks
- controlled evolution instead of a heavy product rebuild

## Design Principles

1. `SKILL.md` remains the primary interaction entry.
2. Long-term state lives in project files, not transient chat context.
3. Scripts only keep the repetitive checks that still have clear value.
4. Lightweight agent orchestration handles planning, drafting, language cleanup, and review.
5. No GUI or heavy orchestration layer unless the local workflow proves it is needed.

## Runtime Layers

### Layer 1: Interaction

- Codex skill
- slash-command style prompts
- planner / writer / reviewer conversation workflow

### Layer 2: Orchestration

- `chase` CLI
- local workflow runner
- context compilation entrypoints
- minimal report generation commands

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
- project doctor checks

## Repository Layout

```text
repo/
├─ ARCHITECTURE.md
├─ SKILL.md
├─ bin/
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
│  └─ workflow_runner.py
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
│  ├─ summaries/
│  │  └─ recent.md
│  └─ retrieval/
│     ├─ next_context.md
│     └─ dashboard_cache.json
├─ 01_outline/
├─ 02_knowledge/
├─ 03_chapters/
├─ 04_gate/
└─ 05_reports/
```

## Core Workflows

1. Chapter planning uses `context_compiler.py` to build the minimum next-chapter context package.
2. Chapter drafting stays skill-driven and follows the lightweight agent sequence.
3. Revision uses `language_audit.py` plus style and memory files.
4. Chapter governance uses `chapter_gate.py` and `dashboard_snapshot.py`.
5. Book health review uses `batch_gate.py`, `foreshadow_scheduler.py`, and in-workflow reviewer retrospectives.

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

- Chat remains the fastest writing surface.
- Python scripts remain the cheapest automation layer.
- Markdown memory remains the most transparent storage format.
- Lightweight agent roles improve quality without introducing a heavy orchestration system.
