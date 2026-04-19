# Runtime Design Baseline

## Purpose

This note reconnects the shipped repository to the recovered LeadWriter runtime design baseline.

Primary references:
- [Recovered design spec](D:\git\chaseNovel\docs\superpowers\specs\2026-04-14-leadwriter-runtime-design.md)
- [Recovered implementation plan](D:\git\chaseNovel\docs\superpowers\plans\2026-04-14-leadwriter-runtime.md)

## Current Alignment

### Runtime ownership
- `LeadWriter` remains the only chapter decision owner.
- `WriterExecutor` remains the only prose execution path inside the runtime loop.
- `DecisionEngine` emits a single unified `RewriteBrief`.
- `EvaluatorVerdict` stays structured and blocking-oriented.

### Memory truth source
- `00_memory/schema/*.json` is the runtime truth source.
- Markdown memory stays as a human-readable layer and fallback input.
- `RuntimeMemorySync` writes normalized schema patches and runtime summaries.

### Workflow surface
- `write / run` default to `doctor,open,runtime,quality,status`.
- `check` default stays `doctor,open,quality,status` and keeps `dry-run`.
- `workflow_runner.py` exposes `reference_chapter`, `target_chapter`, `pipeline_summary`, and top-level `final_release`.

### Status and quality
- `quality` returns structured verdicts and `final_release`.
- `status` surfaces runtime-facing observation fields through `runtime_signals`.
- `dashboard_snapshot.py` reads runtime payloads and memory-sync outputs back into book-level observation.

## Recovered Baseline Decision

The design baseline was not relocated. The files below had been deleted from the working tree and are now restored as the repository baseline:
- [2026-04-14-leadwriter-runtime-design.md](D:\git\chaseNovel\docs\superpowers\specs\2026-04-14-leadwriter-runtime-design.md)
- [2026-04-14-leadwriter-runtime.md](D:\git\chaseNovel\docs\superpowers\plans\2026-04-14-leadwriter-runtime.md)

## Remaining Gaps

These are still acceptable as phase constraints, but they are not fully end-state:
- `quality` can consume persisted runtime verdicts, but some runtime-only evaluators are still strongest inside the runtime path itself.
- Compatibility shims still exist under `references/` and some root templates.
- The repository still carries migration residue that should not regain main-entry status.

## Rule Of Thumb

If a document conflicts with shipped behavior:
1. Trust the recovered design spec for target architecture.
2. Trust `workflow_runner.py`, `runtime/`, `quality_gate.py`, and `book_health.py` for current shipped behavior.
3. Update compatibility docs so they point back to the current mainline instead of becoming parallel specs.
