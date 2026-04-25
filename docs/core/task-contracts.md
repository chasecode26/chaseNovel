# Task Contracts

## Contract index

- Launch: `references/contracts/01-launch.md`
- Write: `references/contracts/02-write.md`
- Continue: `references/contracts/03-continue.md`
- Revise: `references/contracts/04-modify.md`
- State / rhythm: `references/contracts/05-state-and-rhythm.md`
- Promise / repeat: `references/contracts/06-promises-and-repeat.md`
- Research material: `references/contracts/07-research-material.md`

## Current entry points

- Launch and next-chapter readiness: `chase open`
- Main writing pipeline: `chase write`
- Quality gate: `chase quality`
- Book health: `chase status`
- Dry-run sweep: `chase check`

## Chapter semantics

- `open` treats `--chapter <n>` as the current drafted `reference_chapter` and prepares `target_chapter = n + 1` by default.
- `quality`, `status`, and runtime steps consume the current `reference_chapter`.
- `write` and `check` aggregate both `reference_chapter` and `target_chapter`.

## Default chains

- `chase write`: `doctor,open,runtime,quality,status`
- `chase check`: `doctor,open,quality,status`
- `check` must remain dry-run and must not enter runtime prose generation.

## Aggregate output contract

`write` and `check` JSON should stably expose:

- `reference_chapter`
- `target_chapter`
- `status`
- `warning_count`
- `steps`
- `report_paths`
- `pipeline_summary`
- `final_release`

`quality` should distinguish:

- `runtime_only_dimensions`
- `loaded_runtime_dimensions`
- `fallback_runtime_dimensions`
- `missing_runtime_dimensions`
- `runtime_verdict_source`

`final_release` is the top-level publish decision for CLI, smoke tests, and upper orchestration.
