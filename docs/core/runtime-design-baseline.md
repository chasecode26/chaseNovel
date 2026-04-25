# Runtime Design Baseline

## Purpose

This note defines the shipped LeadWriter runtime baseline.

Primary references:
- `workflow_runner.py`, `runtime/`, `quality_gate.py`, and `book_health.py` define shipped behavior.
- Historical archive and compatibility documents have been removed from the shipped tree.

## Current Alignment

### Runtime ownership
- `LeadWriter` remains the chapter decision owner.
- `WriterExecutor` remains the prose execution path inside the runtime loop.
- `DecisionEngine` emits one unified `RewriteBrief`.
- `EvaluatorVerdict` stays structured and blocking-oriented.

### Memory truth source
- `00_memory/schema/*.json` is the runtime truth source.
- Markdown memory stays as a human-readable layer and fallback input.
- `RuntimeMemorySync` writes normalized schema patches and runtime summaries.

### Workflow surface
- `write` defaults to `doctor,open,runtime,quality,status`.
- `check` defaults to `doctor,open,quality,status` and keeps `dry-run`.
- `workflow_runner.py` exposes `reference_chapter`, `target_chapter`, `pipeline_summary`, and top-level `final_release`.

### Status and quality
- `quality` returns structured verdicts and `final_release`.
- `status` surfaces runtime-facing observation fields through `runtime_signals`.
- `dashboard_snapshot.py` reads runtime payloads and memory-sync outputs back into book-level observation.

## Rule Of Thumb

If a document conflicts with shipped behavior:
1. Trust `workflow_runner.py`, `runtime/`, `quality_gate.py`, and `book_health.py`.
2. Update docs back to the current mainline instead of creating parallel specs.
