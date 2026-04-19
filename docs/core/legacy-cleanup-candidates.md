# Legacy Cleanup Candidates

## Completed

The phase-1 migration residue below has already been removed from the live tree:

- generated caches and build artifacts
- obsolete reference index docs
- deprecated root-level review cards and route cheatsheets
- duplicated genre and substyle template directories
- root-level genre route docs downgraded to compatibility shims
- root-level style, opening, hook, language, and audit rule docs downgraded to compatibility summaries
- legacy continuity / language anti-AI / style consistency review templates merged into `templates/review/chapter-quality-review.md`

## Remaining merge targets

### Keep for now: root shim templates

- `templates/style-defaults.md`
- `templates/style_fingerprints.md`
- `templates/chapter-planning-review.md`
- `templates/rewrite-handoff.md`
- `templates/volume_blueprint.md`

### Keep for now: references compatibility layer

- `references/anti-repeat-rules.md` -> compatibility summary to `docs/core/revise-diagnostics.md`
- `references/writing-patterns.md` -> compatibility summary to `docs/core/write-workflow.md` / `docs/core/style-governance.md`
- genre routing notes -> compatibility shims to `docs/assets/genre-index.md`
- style / opening / hook / language notes -> compatibility summaries to `docs/core/*`

## Keep for now: script dependent

- `templates/core/plan.md`
- `templates/core/state.md`
- `templates/core/style.md`
- `templates/core/style-guardrails.md`
- `templates/core/voice.md`
- `templates/core/characters.md`
- `templates/core/character-arcs.md`
- `templates/core/foreshadowing.md`
- `templates/core/payoff-board.md`
- `templates/core/timeline.md`
- `templates/core/findings.md`
- `templates/core/scene_preferences.md`
- `templates/core/summaries_recent.md`
- `templates/core/character-voice-diff.md`
- `templates/summaries_mid.md`

## Keep for now: compatibility layer

- `references/`

## Keep for now: heavy rule docs now downgraded by compatibility headers

- `references/execution_workflow.md`
- `references/agent-collaboration.md`
- `references/revision-and-diagnostics.md`
- `references/craft-and-platform.md`
