# LeadWriter Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild chaseNovel around a strong-control LeadWriter runtime with structured memory, a single writer path, and blocking evaluator orchestration while keeping the public CLI surface stable.

**Architecture:** Add a new runtime core that compiles chapter context from structured schema memory, drives the write flow through a LeadWriter-owned orchestration path, and normalizes quality/status outputs around shared contracts. Keep `chase open|write|quality|status` stable, but demote old wrappers into thin façades or remove them when the runtime fully replaces them. Historical note: the shipped repo later kept `scripts/engine_runner.py` as a compatibility / rename placeholder rather than deleting it outright.

**Tech Stack:** Python 3 scripts, Node CLI wrapper, JSON schema files, Markdown templates, npm smoke validation

---

## File Structure

### New runtime core
- Create: `runtime/contracts.py` — shared dataclasses / typed dicts for context packet, brief, verdict, rewrite brief, memory patch
- Create: `runtime/memory_compiler.py` — build structured chapter context from schema + markdown fallback
- Create: `runtime/lead_writer.py` — generate chapter brief, orchestrate writer/evaluator loop, own decisions
- Create: `runtime/writer_executor.py` — single-writer execution shim for current phase
- Create: `runtime/decision_engine.py` — prioritize evaluator results and emit unified rewrite brief
- Create: `runtime/memory_sync.py` — write schema snapshots and runtime summary reports
- Create: `runtime/runtime_orchestrator.py` — entrypoint used by `write`
- Create: `runtime/__init__.py`

### New evaluator protocol layer
- Create: `evaluators/contracts.py` — evaluator output schema helpers
- Create: `evaluators/continuity.py` — adapt chapter gate into runtime verdict form
- Create: `evaluators/style.py` — adapt language audit into runtime verdict form
- Create: `evaluators/repeat.py` — adapt anti-repeat report into runtime verdict form
- Create: `evaluators/__init__.py`

### New schema files
- Create: `schemas/plan.schema.json`
- Create: `schemas/state.schema.json`
- Create: `schemas/timeline.schema.json`
- Create: `schemas/characters.schema.json`
- Create: `schemas/character_arcs.schema.json`
- Create: `schemas/payoff.schema.json`
- Modify: `schemas/project_state.schema.json`
- Modify: `schemas/arc.schema.json`
- Modify: `schemas/foreshadow.schema.json`

### Script integration points
- Modify: `scripts/project_bootstrap.py`
- Modify: `scripts/open_book.py`
- Modify: `scripts/workflow_runner.py`
- Historical option: keep `scripts/engine_runner.py` as a compatibility shim / rename placeholder
- Modify: `scripts/quality_gate.py`
- Modify: `scripts/book_health.py`
- Modify: `scripts/memory_update.py`
- Modify: `scripts/aggregation_utils.py`
- Modify: `scripts/project_doctor.py`
- Modify: `scripts/smoke_check.py`

### Docs and templates
- Modify: `ARCHITECTURE.md`
- Modify: `README.md`
- Modify: `docs/core/write-workflow.md`
- Modify: `docs/core/status-workflow.md`
- Modify: `docs/core/task-contracts.md`
- Modify: `templates/core/plan.md`
- Modify: `templates/core/state.md`
- Modify: `templates/core/timeline.md`
- Modify: `templates/core/characters.md`
- Modify: `templates/core/character-arcs.md`
- Modify: `templates/core/payoff-board.md`
- Modify: `templates/core/foreshadowing.md`
- Modify: `templates/core/style.md`
- Modify: `templates/core/voice.md`

### Removals / demotions
- Delete: `scripts/bootstrap.py`
- Delete: `scripts/doctor.py`
- Delete: `scripts/memory_sync.py`
- Demote only: `scripts/engine_runner.py` may remain as a compatibility shim / rename placeholder

---

### Task 1: Add shared runtime contracts

**Files:**
- Create: `runtime/contracts.py`
- Create: `evaluators/contracts.py`
- Test: `npm run smoke`

- [ ] **Step 1: Create shared runtime contracts**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Status = Literal["pass", "warn", "fail"]
Decision = Literal["pass", "revise", "fail"]

@dataclass(frozen=True)
class ChapterContextPacket:
    project: str
    chapter: int
    active_volume: str
    active_arc: str
    current_place: str
    next_goal: str
    open_threads: list[str]
    forbidden_inventions: list[str]
    voice_rules: list[str]
    warnings: list[str] = field(default_factory=list)

@dataclass(frozen=True)
class ChapterBrief:
    chapter: int
    chapter_function: str
    must_advance: list[str]
    must_not_repeat: list[str]
    hook_goal: str
    allowed_threads: list[str]
    disallowed_moves: list[str]
    voice_constraints: list[str]

@dataclass(frozen=True)
class EvaluatorVerdict:
    dimension: str
    status: Status
    blocking: bool
    evidence: list[str]
    why_it_breaks: str
    minimal_fix: str
    rewrite_scope: str

@dataclass(frozen=True)
class RewriteBrief:
    return_to: str
    blocking_reasons: list[str]
    first_fix_priority: str
    rewrite_scope: str
    must_preserve: list[str]
    must_change: list[str]
    recheck_order: list[str]

@dataclass(frozen=True)
class RuntimeDecision:
    decision: Decision
    rewrite_brief: RewriteBrief | None
    blocking_dimensions: list[str]

@dataclass(frozen=True)
class MemoryPatch:
    schema_file: str
    before: dict[str, object]
    after: dict[str, object]
```

- [ ] **Step 2: Run smoke to confirm imports don’t break repository packaging**

Run: `npm run smoke`
Expected: PASS, with `[smoke] ok`

- [ ] **Step 3: Commit contracts skeleton**

```bash
git add runtime/contracts.py evaluators/contracts.py
git commit -m "feat: add leadwriter runtime contracts"
```

### Task 2: Bootstrap schema memory skeleton

**Files:**
- Modify: `scripts/project_bootstrap.py`
- Create: `schemas/plan.schema.json`
- Create: `schemas/state.schema.json`
- Create: `schemas/timeline.schema.json`
- Create: `schemas/characters.schema.json`
- Create: `schemas/character_arcs.schema.json`
- Create: `schemas/payoff.schema.json`
- Modify: `schemas/project_state.schema.json`
- Modify: `schemas/arc.schema.json`
- Modify: `schemas/foreshadow.schema.json`
- Test: `npm run smoke`

- [ ] **Step 1: Extend bootstrap directories and seed schema paths**

```python
DIRS = [
    "00_memory",
    "00_memory/schema",
    "00_memory/retrieval",
    "00_memory/summaries",
    "01_outline",
    "02_knowledge",
    "03_chapters",
    "04_gate",
    "05_reports",
    "06_exports",
]
```

Add a `SCHEMA_SEEDS` map in `scripts/project_bootstrap.py`:

```python
SCHEMA_SEEDS = {
    "00_memory/schema/plan.json": {"title": "", "genre": "", "hook": "", "target_words": 0, "volumes": []},
    "00_memory/schema/state.json": {"currentChapter": 0, "currentVolume": "", "currentArc": "", "chapterGoal": "", "openThreads": [], "forbiddenInventions": []},
    "00_memory/schema/timeline.json": {"absoluteTime": "", "relativeTimeFromPrevChapter": "", "currentLocation": "", "recentEvents": []},
    "00_memory/schema/characters.json": {"characters": []},
    "00_memory/schema/character_arcs.json": {"arcs": []},
    "00_memory/schema/foreshadowing.json": {"threads": []},
    "00_memory/schema/payoff_board.json": {"promises": []},
    "00_memory/schema/style.json": {"genreTone": "", "narrationRules": [], "prohibitedPhrases": []},
    "00_memory/schema/voice.json": {"bookVoiceDNA": "", "sentenceRhythm": "", "forbiddenCadence": []},
}
```

- [ ] **Step 2: Write schema files used by runtime validation**

Example `schemas/state.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "LeadWriter Runtime State",
  "type": "object",
  "required": ["currentChapter", "currentVolume", "currentArc", "chapterGoal", "openThreads", "forbiddenInventions"],
  "properties": {
    "currentChapter": { "type": "integer", "minimum": 0 },
    "currentVolume": { "type": "string" },
    "currentArc": { "type": "string" },
    "chapterGoal": { "type": "string" },
    "activeConflict": { "type": "string" },
    "nextPressure": { "type": "string" },
    "sceneAnchors": {
      "type": "object",
      "properties": {
        "absoluteTime": { "type": "string" },
        "relativeTime": { "type": "string" },
        "location": { "type": "string" }
      },
      "additionalProperties": false
    },
    "openThreads": {
      "type": "array",
      "items": { "type": "string" }
    },
    "forbiddenInventions": {
      "type": "array",
      "items": { "type": "string" }
    },
    "pendingPayoffs": {
      "type": "array",
      "items": { "type": "string" }
    }
  },
  "additionalProperties": true
}
```

- [ ] **Step 3: Run smoke to verify bootstrap still works with fixture project**

Run: `npm run smoke`
Expected: PASS, fixture project contains `00_memory/schema/*.json`

- [ ] **Step 4: Commit schema bootstrap changes**

```bash
git add scripts/project_bootstrap.py schemas/*.json
git commit -m "feat: bootstrap structured memory schema"
```

### Task 3: Implement memory compiler and LeadWriter runtime shell

**Files:**
- Create: `runtime/memory_compiler.py`
- Create: `runtime/lead_writer.py`
- Create: `runtime/runtime_orchestrator.py`
- Create: `runtime/writer_executor.py`
- Create: `runtime/decision_engine.py`
- Create: `runtime/memory_sync.py`
- Create: `runtime/__init__.py`
- Test: `python ./scripts/workflow_runner.py --project <fixture> --json --dry-run`

- [ ] **Step 1: Build `MemoryCompiler` around existing context extraction**

```python
from __future__ import annotations

import json
from pathlib import Path

from runtime.contracts import ChapterContextPacket
from scripts.novel_utils import read_text

class MemoryCompiler:
    def build(self, project_dir: Path, chapter: int) -> ChapterContextPacket:
        state = json.loads((project_dir / "00_memory/schema/state.json").read_text(encoding="utf-8"))
        voice = json.loads((project_dir / "00_memory/schema/voice.json").read_text(encoding="utf-8"))
        return ChapterContextPacket(
            project=project_dir.as_posix(),
            chapter=chapter,
            active_volume=str(state.get("currentVolume", "未识别")),
            active_arc=str(state.get("currentArc", "未识别")),
            current_place=str(state.get("sceneAnchors", {}).get("location", "未识别")),
            next_goal=str(state.get("chapterGoal", "待明确")),
            open_threads=[str(item) for item in state.get("openThreads", [])],
            forbidden_inventions=[str(item) for item in state.get("forbiddenInventions", [])],
            voice_rules=[str(item) for item in voice.get("forbiddenCadence", [])],
        )
```

- [ ] **Step 2: Build LeadWriter brief generator and default writer executor**

```python
from runtime.contracts import ChapterBrief, ChapterContextPacket

class LeadWriter:
    def create_brief(self, packet: ChapterContextPacket) -> ChapterBrief:
        return ChapterBrief(
            chapter=packet.chapter,
            chapter_function=packet.next_goal or "推进当前章节目标",
            must_advance=packet.open_threads[:3],
            must_not_repeat=[],
            hook_goal="延续当前压力并形成下一章牵引",
            allowed_threads=packet.open_threads,
            disallowed_moves=packet.forbidden_inventions,
            voice_constraints=packet.voice_rules,
        )
```

```python
class WriterExecutor:
    def draft(self, brief: ChapterBrief) -> dict[str, object]:
        return {
            "chapter": brief.chapter,
            "mode": "runtime-single-writer",
            "chapter_function": brief.chapter_function,
            "status": "pending-human-draft"
        }
```

- [ ] **Step 3: Build a thin runtime orchestrator for phase-one `write`**

```python
from runtime.memory_compiler import MemoryCompiler
from runtime.lead_writer import LeadWriter
from runtime.writer_executor import WriterExecutor

class LeadWriterRuntime:
    def run(self, project_dir: Path, chapter: int) -> dict[str, object]:
        packet = MemoryCompiler().build(project_dir, chapter)
        brief = LeadWriter().create_brief(packet)
        draft = WriterExecutor().draft(brief)
        return {
            "status": "pass",
            "chapter": chapter,
            "context": packet.__dict__,
            "brief": brief.__dict__,
            "draft": draft,
        }
```

- [ ] **Step 4: Verify orchestrator dry-run output**

Run: `python ./scripts/workflow_runner.py --project . --json --dry-run`
Expected: JSON output includes `runtime`-backed write summary without tracebacks

- [ ] **Step 5: Commit runtime shell**

```bash
git add runtime
git commit -m "feat: add leadwriter runtime shell"
```

### Task 4: Route `write` through runtime and remove redundant wrappers

**Files:**
- Modify: `scripts/workflow_runner.py`
- Modify: `bin/chase.js`
- Optional demotion only: `scripts/engine_runner.py`
- Delete: `scripts/bootstrap.py`
- Delete: `scripts/doctor.py`
- Delete: `scripts/memory_sync.py`
- Test: `node ./bin/chase.js write --project . --dry-run --json`
- Test: `npm run smoke`

- [ ] **Step 1: Replace workflow runner step engine with runtime-aware execution**

Update `scripts/workflow_runner.py` so `write` flow becomes:

```python
DEFAULT_STEPS = ["doctor", "open", "runtime", "status"]

STEP_MAP = {
    "doctor": "project_doctor.py",
    "open": "planning_context.py",
    "runtime": None,
    "status": "book_health.py",
    "quality": "quality_gate.py",
}
```

And add:

```python
from runtime.runtime_orchestrator import LeadWriterRuntime

if step == "runtime":
    runtime_payload = LeadWriterRuntime().run(project, chapter or 0)
    return {
        "step": "runtime",
        "returncode": 0,
        "stderr": "",
        "status": runtime_payload.get("status", "pass"),
        "warning_count": 0,
        "warnings": [],
        "report_paths": {},
        "summary": runtime_payload,
    }
```

- [ ] **Step 2: Point Node CLI directly at real scripts, not throwaway wrappers**

In `bin/chase.js`, change:

```javascript
bootstrap: { script: "project_bootstrap.py" },
doctor: { script: "project_doctor.py" },
write: { script: "workflow_runner.py" },
memory: { script: "memory_update.py" },
run: { script: "workflow_runner.py" },
check: {
  script: "workflow_runner.py",
  injectArgs: ["--dry-run", "--steps", "doctor,open,status"],
},
```

- [ ] **Step 3: Delete obsolete one-line wrappers and demote rename placeholders**

Delete files:

```text
scripts/bootstrap.py
scripts/doctor.py
scripts/memory_sync.py
```

Keep as compatibility shim if still present:

```text
scripts/engine_runner.py
```

- [ ] **Step 4: Run CLI checks for write path and smoke suite**

Run: `node ./bin/chase.js write --project . --dry-run --json`
Expected: JSON payload returned, includes `runtime` step

Run: `npm run smoke`
Expected: PASS, `[smoke] ok`

- [ ] **Step 5: Commit runtime routing and deletions**

```bash
git add bin/chase.js scripts/workflow_runner.py
git add -u scripts
git commit -m "refactor: route write flow through runtime core"
```

### Task 5: Normalize quality and status around shared verdicts

**Files:**
- Create: `evaluators/continuity.py`
- Create: `evaluators/style.py`
- Create: `evaluators/repeat.py`
- Modify: `scripts/quality_gate.py`
- Modify: `scripts/book_health.py`
- Modify: `scripts/aggregation_utils.py`
- Test: `python ./scripts/quality_gate.py --project . --chapter-no 1 --json --dry-run`
- Test: `python ./scripts/book_health.py --project . --json --dry-run`

- [ ] **Step 1: Add evaluator adapters that convert current reports to verdict objects**

Example `evaluators/continuity.py`:

```python
from __future__ import annotations

from evaluators.contracts import build_verdict
from scripts.chapter_gate import map_overall_verdict

def from_gate_payload(payload: dict[str, object]) -> dict[str, object]:
    verdict = str(payload.get("continuity_verdict", payload.get("status", "pass")))
    return build_verdict(
        dimension="continuity",
        status="fail" if verdict == "block" else verdict,
        blocking=verdict == "block",
        evidence=[str(item) for item in payload.get("blockers", [])],
        why_it_breaks="章节连续性或记忆锚点未对齐",
        minimal_fix="回到 LeadWriter 重新对齐章节 brief 与 memory anchors",
        rewrite_scope="chapter_card + affected paragraphs",
    )
```

- [ ] **Step 2: Make quality gate return `verdicts` and `final_release`**

In `scripts/quality_gate.py`, after building aggregate payload, append:

```python
payload["verdicts"] = verdicts
payload["final_release"] = "revise" if any(item["blocking"] for item in verdicts) else "pass"
```

- [ ] **Step 3: Make status output runtime-facing observation fields**

In `scripts/book_health.py`, add:

```python
payload["runtime_signals"] = {
    "blocking_dimensions": [],
    "attention_queue": payload.get("warnings", []),
    "focus": args.focus,
}
```

- [ ] **Step 4: Verify JSON output contracts**

Run: `python ./scripts/quality_gate.py --project . --chapter-no 1 --json --dry-run`
Expected: JSON includes `verdicts` and `final_release`

Run: `python ./scripts/book_health.py --project . --json --dry-run`
Expected: JSON includes `runtime_signals`

- [ ] **Step 5: Commit shared verdict integration**

```bash
git add evaluators scripts/quality_gate.py scripts/book_health.py scripts/aggregation_utils.py
git commit -m "feat: unify runtime verdicts for quality and status"
```

### Task 6: Sync markdown templates and docs to runtime-first model

**Files:**
- Modify: `ARCHITECTURE.md`
- Modify: `README.md`
- Modify: `docs/core/write-workflow.md`
- Modify: `docs/core/status-workflow.md`
- Modify: `docs/core/task-contracts.md`
- Modify: `templates/core/plan.md`
- Modify: `templates/core/state.md`
- Modify: `templates/core/timeline.md`
- Modify: `templates/core/characters.md`
- Modify: `templates/core/character-arcs.md`
- Modify: `templates/core/payoff-board.md`
- Modify: `templates/core/foreshadowing.md`
- Modify: `templates/core/style.md`
- Modify: `templates/core/voice.md`
- Test: `npm run smoke`

- [ ] **Step 1: Rewrite docs to describe runtime ownership**

Key wording to add to `docs/core/write-workflow.md`:

```md
## Runtime ownership
- LeadWriter is the only chapter decision owner.
- WriterExecutor is the only prose execution path.
- Evaluators block or pass; they do not rewrite final prose.
- Schema memory is the runtime truth source.
```

- [ ] **Step 2: Update templates so markdown mirrors schema fields**

Example `templates/core/state.md` additions:

```md
## Runtime Schema Mirror
- forbiddenInventions：
- openThreads：
- pendingPayoffs：
- sceneAnchors.absoluteTime：
- sceneAnchors.location：
```

- [ ] **Step 3: Run smoke to ensure fixture still renders and package still builds**

Run: `npm run smoke`
Expected: PASS, `[smoke] ok`

- [ ] **Step 4: Commit docs and templates refresh**

```bash
git add ARCHITECTURE.md README.md docs/core templates/core
git commit -m "docs: align workflow docs with leadwriter runtime"
```

### Task 7: Final verification and branch-ready cleanup

**Files:**
- Modify: any touched files from Tasks 1-6
- Test: `npm run smoke`
- Test: `node ./bin/chase.js write --project . --dry-run --json`
- Test: `node ./bin/chase.js quality --project . --chapter-no 1 --json --dry-run`
- Test: `node ./bin/chase.js status --project . --json --dry-run`

- [ ] **Step 1: Run full smoke suite**

Run: `npm run smoke`
Expected: PASS, `[smoke] ok`

- [ ] **Step 2: Run key CLI dry-runs**

Run: `node ./bin/chase.js write --project . --dry-run --json`
Expected: JSON contains `runtime` step

Run: `node ./bin/chase.js quality --project . --chapter-no 1 --json --dry-run`
Expected: JSON contains `verdicts`

Run: `node ./bin/chase.js status --project . --json --dry-run`
Expected: JSON contains `runtime_signals`

- [ ] **Step 3: Commit final verification adjustments**

```bash
git add -u
git add runtime evaluators schemas docs/core templates/core

git commit -m "refactor: establish leadwriter runtime as write core"
```
