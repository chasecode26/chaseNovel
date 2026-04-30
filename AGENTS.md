# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project overview

chaseNovel 是面向中文网文长篇连载的本地写作引擎。它关注连载长期稳定推进而非单章写出，核心能力包括节奏/阶段目标、设定连续性、人物推进、伏笔回收、文风治理、书级状态。

关键原则：
- 连载质量优先于单章漂亮
- `00_memory/schema/*.json` 是 runtime 真相源，markdown memory 是人工阅读层
- 文档与运行行为冲突时，以 `docs/core/runtime-design-baseline.md` 和 shipped runtime 代码为准
- 创作主链（正文生成）与校稿辅链（质量检查）分开，辅链只指出问题不替 Writer 决定怎么写

## Commands

### CLI (Node.js entry)

```bash
# 开书或准备下一章上下文
chase open --project <dir> [--chapter <n> | --target-chapter <n>]

# 质量门禁
chase quality --project <dir> [--chapter-no <n> | --from <n> --to <n>]

# 完整写作管线 open → runtime → quality → status
chase write --project <dir> [--chapter <n>] [--steps <csv>]

# 书级健康状态
chase status --project <dir> [--chapter <n>] [--focus <all|dashboard|foreshadow|arc|timeline|repeat>]

# dry-run 健康扫描（不进入正文生成）
chase check --project <dir> [--chapter <n>]
```

Chapter semantics: `--chapter <n>` 表示已写完的 reference chapter；`open` 默认准备 `target_chapter = n + 1`。

### Direct Python scripts

```bash
# 工作流编排（底层，chase write/check 都会调到）
python scripts/workflow_runner.py --project <dir> --chapter <n> [--steps open,runtime,quality,status]

# 各检查脚本可独立运行
python scripts/settings_consistency.py --project <dir> --from-chapter 1 --to-chapter 10 --json
python scripts/knowledge_boundary_check.py --project <dir> --from-chapter 1 --to-chapter 10
python scripts/resource_tracker.py --project <dir> --from-chapter 1 --to-chapter 10
python scripts/language_naturalness.py --project <dir> --chapter <n> --json
python scripts/volume_gate.py --project <dir> --chapter <n>

# Runtime 独立运行
python runtime/runtime_orchestrator.py  # 或从代码调用 LeadWriterRuntime().run()
```

### npm scripts

```bash
npm run check        # chase check --project .
npm run pack:dry-run # 打包预览
```

## Architecture

### 6-layer model

| Layer | 内容 | 职责 |
|-------|------|------|
| Entry | `README.md`, `SKILL.md`, `task-contracts.md` | 入口、路由、合同索引 |
| Runtime facts | `runtime-design-baseline.md` | 记录 shipped runtime 真实行为 |
| Capability docs | `docs/core/*.md`, `references/contracts/*.md` | 各子 skill 边界与合同 |
| Command surface | `scripts/*.py`, `bin/chase.js` | CLI 入口与聚合编排 |
| Runtime core | `runtime/`, `evaluators/`, `schemas/` | 正文生成、rewrite loop、裁决计算 |
| Memory/assets | `00_memory/`, `templates/` | 项目记忆、模板、参考资产 |

### Runtime pipeline (LeadWriterRuntime)

```
MemoryCompiler.build()  →  从 00_memory/schema/*.json + markdown 构建 ChapterContextPacket
    ↓
LeadWriterAgent.create_brief()  →  产出 ChapterBrief（目标、冲突、结果、钩子、短期待/长期待、题材承诺）
    ↓
DirectorAgent.direct()  →  产出 ChapterDirection（开场、第一冲突、中段反转、情绪曲线、期待线拍法）
    ↓
SceneBeatAgent.plan()  →  产出 SceneBeatPlan（场面目标、交锋、代价、next_pull、期待线、题材框架提示）
    ↓
WriterAgent.draft()  →  读取 agent prompt / handoff / SceneBeatPlan 生成正文与写作产物
    ↓
ReviewerAgent.review_with_report()  →  聚合 verdicts（含 prose_concreteness、market_fit、expectation_integrity、opening_diagnostics、genre_framework_fit）
    ↓
DecisionEngine.decide()  →  pass / revise / fail
    ↓
（若 revise: RewriterAgent.rewrite() 局部返工；必要时 LeadWriterAgent.revise_brief() 重做章卡，最多 2 轮）
    ↓
ReleasePolicy.evaluate()  →  最终放行门禁
    ↓
RuntimeMemorySync.summarize()  →  回写 schema patches + runtime summary
```

### Key types (runtime/contracts.py)

- `ChapterContextPacket`: 35 个字段携带跨章连续性状态，包括新增的卷边界字段 (`is_volume_start`, `is_volume_end`, `volume_name`, `volume_promises`, `volume_handoff`)
- `ChapterBrief`: 本章戏剧约束（功能、必须推进/不得重复、钩子目标、场景计划等）
- `ChapterDirection`: 导演级指令（戏剧问题、场景密度、情感曲线、结尾模式）
- `EvaluatorVerdict`: 统一裁决格式 `{dimension, status(pass|warn|fail), blocking, evidence, why_it_breaks, minimal_fix, rewrite_scope}`
- `RuntimeDecision`: 最终决策 `{decision(pass|revise|fail), rewrite_brief, blocking_dimensions, advisory_dimensions}`
- `MemoryPatch`: schema 变更 `{schema_file, before, after}`

### Evaluator pattern

每个评估维度遵循统一接口：
- `evaluators/*.py` 是适配器层，将领域脚本的输出转为 `EvaluatorVerdict`
- `runtime/quality_service.py` 是 runtime 侧唯一的 quality-facing facade，内部调用 `quality_gate.py`、`chapter_gate.py`、`language_audit.py` 等
- `runtime/runtime_orchestrator.py._evaluate_cycle()` 额外调用 pacing、causality、promise_payoff、chapter_progress、dialogue、character evaluator

### Memory system

- **真相源**: `00_memory/schema/*.json`（state.json, timeline.json, plan.json, characters.json, character_arcs.json, foreshadowing.json, payoff_board.json）
- **人工层**: `00_memory/*.md`（state.md, plan.md, characters.md 等）
- **回写**: `RuntimeMemorySync` 负责从 runtime payload 生成 schema patches 并写回 JSON
- **卷过渡**: `memory_sync.py._handle_volume_transition()` 在卷边界写入 `00_memory/volume_transitions/` 事件

### Quality check layers

| 层级 | 文件 | 维度 |
|------|------|------|
| 综合门禁 | `quality_gate.py` | continuity, pacing, style, dialogue, repeat, naturalness |
| 章级 | `chapter_gate.py` | chapter progress, arc |
| 草稿 | `draft_gate.py` | draft pacing, scene composition |
| 语言 | `language_audit.py`, `language_naturalness.py`, `genre_vocabulary_check.py` | style, Chinese naturalness, genre vocabulary |
| 连续性 | `timeline_check.py`, `arc_tracker.py`, `foreshadow_scheduler.py`, `anti_repeat_scan.py` | timeline, arc, foreshadow, repeat |
| 设定一致性 | `settings_consistency.py`, `knowledge_boundary_check.py`, `resource_tracker.py` | world setting, knowledge boundary, resource tracking |
| 卷级 | `volume_gate.py` | volume mapping, exit check, entry check, health report |

### Workflow step mapping

`workflow_runner.py` 的 `STEP_MAP` 定义了可编排步骤：
```python
"open": "open_book.py"
"runtime": None  # 调用 LeadWriterRuntime
"quality": "quality_gate.py"
"status": "book_health.py"
"settings": "settings_consistency.py"
"knowledge": "knowledge_boundary_check.py"
"resources": "resource_tracker.py"
```
