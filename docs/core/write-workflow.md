# 写作主链路

> `write` 是重构后统一的写作流水线入口。它不再只是“跑几个脚本”，而是把开写前检查、规划、runtime、状态回看收束成一条主链。

## 核心目标
- 开写前先确认本章是否值得写。
- 把 planning/context 与 runtime 连接成连续流水线。
- 让章节、状态、质量、记忆回写使用同一套章节语义。

## Runtime Ownership
- `LeadWriter` 是唯一章节决策者，负责 brief、裁决、rewrite brief。
- `WriterExecutor` 是唯一正文执行路径，负责 draft 与 rewrite。
- evaluator 只能 `pass / warn / fail`，并给出 `minimal_fix`，不能直接改正文。
- schema memory 是运行时真相源；Markdown memory 是阅读层与补充输入层。
- 任一 blocking verdict 都必须先回到 `LeadWriter -> RewriteBrief -> WriterExecutor`，不能绕开主链直接修文。

## 主入口
- `chase write --project <dir>`
- `chase write --project <dir> --chapter <n>`
- `chase write --project <dir> --chapter <n> --target-chapter <m>`
- `chase write --project <dir> --steps doctor,open,runtime,quality,status`
- `chase check --project <dir> --chapter <n>`
- `chase run --project <dir> --chapter <n>`

## 默认流水线

### `write` / `run`
默认 steps：
- `doctor`
- `open`
- `runtime`
- `quality`
- `status`

### `check`
默认 steps：
- `doctor`
- `open`
- `quality`
- `status`

`check` 默认是 dry-run 健康扫链，会补做 quality 关卡确认，但仍不进入 runtime 正文生成。

## 章节编号语义

### reference chapter
- `--chapter <n>` 表示当前已经写完、已经存在的章节号。
- 它是聚合流水线里的 reference chapter。

### target chapter
- `open` / `planning` / `context` 会把 `--chapter <n>` 当作“当前已写章节”。
- 如果没有额外指定，它们默认准备 `target_chapter = n + 1`。
- 如需跳章、补章、回头重做指定章，显式传 `--target-chapter <m>`。

### 分流规则
- `doctor`: 不消费章节号
- `open/planning/context`: 消费 `reference_chapter`，产出 `target_chapter`
- `runtime/status/memory/quality`: 消费 `reference_chapter`

## 写前最小检查
- `doctor` 确认项目骨架、章节、基础目录是否完整。
- `open` 汇总 planning review 与 next context，判断下一章是否 `write_ready`。
- 若 `open` 仍有 `blocking = yes`，不应直接推进正文链。

## Runtime 位置
- `runtime` 是写作中段，不是开书入口。
- 它基于当前 reference chapter 的 runtime 状态、brief、角色约束与 pressure/payoff 信号生成中间产物。
- 产物通常落在 `04_gate/chNNN/` 与 `00_memory/retrieval/`。

## Rewrite Contract
- `runtime` 内部若出现 blocking verdict，当前稿件不得直接放行。
- `DecisionEngine` 必须输出唯一统一的 `RewriteBrief`，不能把多个 evaluator 原话直接拼给 writer。
- `WriterExecutor` 重写时必须保留 `must_preserve`，只修 `must_change` 与 `rewrite_scope` 指定范围。
- 连续多轮 blocking 原因不变时，应升级为 `fail`，回退到 brief 或 memory 校准，而不是无穷磨稿。

## Quality Boundary
- `quality` 是统一质量门，但不是完整 runtime writer loop 的替身。
- `continuity / style / draft/schema` 可独立运行；`character / causality / promise_payoff / pacing / dialogue` 当前默认优先来自 runtime 已产出的 verdict。
- 若 runtime payload 不存在，`quality` 会对 `character / causality / promise_payoff / pacing / dialogue` 中可轻量推断的部分维度做 fallback，并显式回报 `fallback_runtime_dimensions`。
- 因此 `quality` 输出里若出现 `missing_runtime_dimensions`，语义是“本轮未拿到对应 runtime verdict”，不是“对应维度无问题”。

## Status 位置
- `status` 是写后回看，不负责下一章规划。
- 它聚合：
  - `dashboard`
  - `foreshadow`
  - `arc`
  - `timeline`
  - `repeat`
- 它回答的是“当前书级健康如何”，不是“下一章要怎么写”。

## 最小执行顺序
推荐顺序：
1. `doctor`
2. `open`
3. `runtime`
4. `quality` 或 reviewer
5. `memory`
6. `status`

若只想确认是否可开写：
1. `check`

## 什么时候该停下
出现以下任一情况，应先修再跑全链：
- `open` 返回 `blocking = yes`
- `planning_verdict = fail`
- `quality` 出现 blocking verdict
- `status` 暴露 overdue foreshadow / stalled arc / timeline break，但正文仍试图继续硬推

## 聚合输出约定
`write/run/check` 的聚合 JSON 应至少稳定包含：
- `reference_chapter`
- `target_chapter`
- `status`
- `warning_count`
- `steps`
- `report_paths`

其中：
- `open` step 应显式回传 `target_chapter`
- `runtime/status/memory/quality` step 应显式回传 `reference_chapter`

## 兼容命令
以下旧命令仍可用，但已不再是产品层主入口：
- `chase planning`
- `chase context`
- `chase gate`
- `chase draft`
- `chase audit`
- `chase memory`
- `chase run`

建议对外统一记忆为：
- 开写前：`chase open`
- 跑主链：`chase write`
- 做健康扫链：`chase check`
- 看书级状态：`chase status`

## 相关文档
- `docs/core/open-book.md`
- `docs/core/status-workflow.md`
- `docs/core/task-contracts.md`
- `docs/core/revise-diagnostics.md`

## Runtime Fallback Notes
- `quality` fallback 只负责兜底暴露明显缺口，不会复刻 `LeadWriter -> RewriteBrief -> WriterExecutor` 的完整 runtime 决策链。
- `character / causality / promise_payoff / pacing / dialogue` 这些 runtime-first 维度一旦缺少 persisted runtime payload，fallback 只能提供轻量证据，不应被视作完整放行依据。
- `pacing` fallback 当前会补看段落重复与 progression density；`promise_payoff` fallback 会补看短兑现是否落地，以及章尾有没有继续抬高 long-tail pressure。
- `character / causality / dialogue` fallback 当前还能补抓 relationship shift 与 information transfer 缺口，例如“已经试出信息，但关系、站位或压制没有继续转手”这类空转。
- `promise_payoff` 的 fallback 只检查“短兑现是否落地”与“章尾是否继续抬高 long-tail pressure”，不能替代 runtime 对整章承诺债务、回收顺序和升级强度的全链路裁决。
- 即使 fallback 命中了上述新信号，它仍然只是质量闸门的轻量代偿，不等于重新跑过完整 `LeadWriter` 决策与 rewrite loop。
