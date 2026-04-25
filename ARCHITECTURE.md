# chaseNovel Architecture

## Goal

`chaseNovel` 的目标，是为中文网文长篇连载提供一套质量优先的本地写作引擎。

它优先保证：
- 长线连载稳定性
- 项目记忆可持续使用
- 章节功能与结果变化清晰
- 伏笔、时间线、角色推进、文风治理可持续追踪
- 工具链真的改善稿件，而不是制造流程负担

## Current Runtime Facts

- `SKILL.md` 仍是主交互入口
- 当前 shipped 聚合编排入口是 `scripts/workflow_runner.py`
- `write / check` 都通过聚合层驱动
- `write` 默认链路是 `doctor -> open -> runtime -> quality -> status`
- `check` 默认链路是 `doctor -> open -> quality -> status`
- `check` 保持 dry-run，只做预审、quality 与状态回看，不进入 runtime 正文生成
- `open` 负责下一章 planning/context 准备
- `quality / runtime / status` handle the current `reference_chapter` checks, generation, and observation.
- `workflow_runner.py` 会同时输出 `pipeline_summary` 与顶层 `final_release`

## Design Baseline

- Current shipped alignment note: `docs/core/runtime-design-baseline.md`
- Historical archive documents have been removed from the shipped tree; use shipped runtime behavior as the source of truth.

## Design Principles

1. 主链优先，兼容层靠后
2. 章节语义必须明确，不能混用“当前章”和“目标章”
3. 聚合入口优先消费统一协议，而不是暴露越来越多的单点命令
4. 脚本只保留对稿件质量有明确价值的重复检查
5. 资产层、模板层、兼容资料层必须与主链分层

## Chapter Semantics

### Reference chapter
- `--chapter <n>` 表示已经写完、已经存在的章节号
- 聚合层把它视为 `reference_chapter`

### Target chapter
- `open` 会基于 `reference_chapter` 默认推导 `target_chapter = n + 1`
- 如需直接指定规划目标，使用 `--target-chapter <m>`

### Routing
- `doctor`：不消费章节号
- `open`：消费 `reference_chapter`，产出 `target_chapter`
- `runtime / quality / status`：消费 `reference_chapter`

## Aggregate Output Contract

- `write / check` 聚合输出至少应稳定包含：
- `reference_chapter`
- `target_chapter`
- `status`
- `warning_count`
- `steps`
- `report_paths`
- `pipeline_summary`
- `final_release`

其中：
- `pipeline_summary` 汇总 `open`、`runtime`、`quality`、`status` 的关键字段
- `pipeline_summary.final_release` 是流水线聚合后的发布决策
- 顶层 `final_release` 是给 CLI、烟测和上层编排方直接消费的稳定出口

## Layer Model

### Layer 1: Interaction
- `SKILL.md`
- `docs/core/open-book.md`
- `docs/core/write-workflow.md`
- `docs/core/status-workflow.md`
- `docs/core/revise-diagnostics.md`

### Layer 2: Aggregated Engines
- `project_bootstrap.py`
- `project_doctor.py`
- `planning_context.py`
- `quality_gate.py`
- `book_health.py`
- `workflow_runner.py`

### Layer 3: Runtime Core
- `runtime/`
- `evaluators/`
- `schemas/`

### Layer 4: Project Memory
- `00_memory/*.md`
- `00_memory/schema/*.json`

### Layer 5: Assets And References
- `docs/assets/`（默认先看 `genre-index` 与各题材 `*-reference-map.md`）
- `assets/`
- `templates/`
- `references/` keeps task contracts only.

## Command Surface

The public CLI keeps only current product commands:

- `bootstrap`
- `doctor`
- `open`
- `quality`
- `write`
- `status`
- `check`

Old aliases have been removed from `bin/chase.js`; use these commands directly.

## Repository Layout

```text
repo/
├── SKILL.md
├── README.md
├── ARCHITECTURE.md
├── bin/
├── docs/
│   ├── core/
│   └── assets/
├── assets/
- references/              # task contracts only
├── templates/
├── scripts/
├── runtime/
├── evaluators/
└── schemas/
```

## Why This Shape

因为真正决定长篇连载质量的，不是仓库里有多少散装命令，而是：
- 主链是否清晰
- 章节语义是否稳定
- 记忆是否可回写、可验证、可追踪
- 质量检查是否内联
- 状态观察是否能直接反哺下一轮 planning
