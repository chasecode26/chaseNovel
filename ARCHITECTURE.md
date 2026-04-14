# chaseNovel Architecture

## Goal

`chaseNovel` 的目标，是为中文网文长篇连载提供一个**质量优先**的本地写作引擎。

它优先保证：
- 长线连载稳定性
- 项目记忆持续可用
- 章节功能与结果变化清楚
- 伏笔、时间线、角色推进、文风治理可持续追踪
- 多 reviewer / 多 agent 协作真正改善稿件，而不是制造流程负担

## Design Principles

1. `SKILL.md` 仍然是主交互入口。
2. 核心主链只保：**开书**、**写作**。
3. 题材资料、样本、风格库、技法库都应下沉为资产层。
4. 脚本只保留对稿件有明确价值的重复检查。
5. 任何不能直接改善稿件质量的层，都不应该挡在主路径上。

## Phase 1 Status

当前架构处于重构过渡阶段（Phase 1.5）：
- 文档层与资产层已建立新分层
- 旧 `references/`、少量根层模板与根层 `technique-kb/` shim 仍保留兼容
- 旧 CLI 命令仍保留兼容
- 聚合脚本层已建立，但旧单点脚本仍在兼容面上暴露

## Target Layers

### Layer 1: Interaction
- `SKILL.md`
- 开书主链文档
- 写作主链文档
- 状态/健康主链文档
- 改写/诊断文档

### Layer 2: Runtime Core
- `LeadWriter`：唯一章节决策 owner
- `MemoryCompiler`：把 schema memory + markdown mirror 编译成 context
- `WriterExecutor`：唯一正文执行路径
- `DecisionEngine`：根据 evaluator verdict 生成 pass / revise / fail 决策
- `RuntimeMemorySync`：回写 runtime 摘要与记忆补丁

### Layer 3: Aggregated Engines
- bootstrap
- doctor
- open/planning-context engine
- quality gate engine
- book health engine
- run/check orchestration over aggregated layers

### Layer 4: Project Memory
- schema truth source：`00_memory/schema/*.json`
- markdown mirror：`plan.md` / `state.md` / `characters.md` / `timeline.md` / `foreshadowing.md` / `style.md` / `voice.md`

### Layer 5: Asset Packs
- genre packs
- substyle packs
- examples
- common reusable style assets
- technique-kb

## Repository Layout (Phase 1)

```text
repo/
├─ SKILL.md
├─ README.md
├─ ARCHITECTURE.md
├─ bin/
├─ docs/
│  ├─ core/
│  └─ assets/
├─ assets/
│  ├─ genres/
│  ├─ substyles/
│  ├─ common/
│  ├─ examples/
│  └─ technique-kb/
├─ references/      # legacy compatibility layer
├─ templates/       # current template layer: core / launch / review
├─ technique-kb/    # legacy shim path
├─ scripts/
└─ schemas/
```

## Current Command Surface

当前仍保留兼容命令：
- `bootstrap`
- `doctor`
- `open`
- `quality`
- `write`
- `status`
- `planning`
- `context`
- `foreshadow`
- `dashboard`
- `arc`
- `timeline`
- `repeat`
- `memory`
- `gate`
- `draft`
- `batch`
- `audit`
- `check`
- `run`

## Target Command Surface

后续阶段会收口到：
- `bootstrap`
- `doctor`
- `open`
- `quality`
- `write`
- `status`

其中旧命令 `planning/context/gate/draft/audit/batch/foreshadow/arc/timeline/repeat/dashboard`
已进入兼容别名阶段，不再是长期主入口。

## Current Optimization Direction

当前优化重点是：
1. 继续把 `references/` 的导航职责上提到 `docs/core/*` 与 `docs/assets/*`
2. 把根层模板尽量降为 shim，主内容只保留在分层后的真实位置
3. 让脚本层优先消费聚合入口，减少用户对旧单点命令的心智负担

## Why This Shape

因为真正决定长篇连载质量的，不是仓库里有多少散装命令，而是：
- 主链路是否短
- 记忆是否稳
- 质量检查是否内聚
- 题材资产是否按需加载
- 文风治理是否持续生效

## Runtime ownership rules
- LeadWriter 负责章节策略与边界裁定。
- WriterExecutor 只执行被允许的正文路径，不自行扩张世界设定。
- Evaluators 只负责放行、预警、阻断与给出最小修法。
- schema memory 是运行时真相源；markdown 模板负责人工可读、维护和回填镜像。

