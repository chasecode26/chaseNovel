# 任务输出契约

## 目标
把开书、写作、续写、改写、状态体检这些主任务的最低输出要求收束到一处，避免聚合脚本升级后仍沿用旧口径。

## 契约索引
- 开书：`references/contracts/01-launch.md`
- 写作：`references/contracts/02-write.md`
- 续写：`references/contracts/03-continue.md`
- 改写：`references/contracts/04-modify.md`
- 状态 / 节奏：`references/contracts/05-state-and-rhythm.md`
- 承诺 / 防重复：`references/contracts/06-promises-and-repeat.md`
- 研究材料：`references/contracts/07-research-material.md`

## 当前主入口
- 开书：[docs/core/open-book.md](D:\git\chaseNovel\docs\core\open-book.md)
- 写作：[docs/core/write-workflow.md](D:\git\chaseNovel\docs\core\write-workflow.md)
- 状态：[docs/core/status-workflow.md](D:\git\chaseNovel\docs\core\status-workflow.md)
- 改写与诊断：[docs/core/revise-diagnostics.md](D:\git\chaseNovel\docs\core\revise-diagnostics.md)

## Runtime Ownership
- `LeadWriter` 负责章节目标解释、brief 生成、blocking 裁决、rewrite brief 统一输出。
- `WriterExecutor` 负责唯一正文执行，不得越权新增设定或改章功能。
- evaluator 负责阻断与举证，不负责定稿与代写。
- `MemorySync` 只在定稿后回写 schema 和记忆摘要，不在审稿阶段篡改正文结论。

## 开书最小输出
- 题材与主卖点
- 主线目标与阶段目标
- 黄金三章功能链
- 角色结构
- 书级 `style.md` / `voice.md`

## 写作 / 续写最小输出
- 本章时间、地点、在场人物、知情边界、资源状态
- 本章功能
- 结果变化
- 章尾钩子
- 需要兑现 / 预热 / 延后的旧布局

## 改写最小输出
- 保留项
- 问题类型
- 改法选择
- 影响面
- 是否需要同步更新记忆文件

## 状态 / 书级体检最小输出
- 当前章节 / 当前卷 / 当前弧
- 活跃伏笔 / 逾期伏笔
- 时间线风险
- 重复推进风险
- 下一章目标或当前阻塞点

## 章节编号语义
- `open` / `planning` / `context`
- `--chapter <n>` = 当前已写的 `reference_chapter`
- 默认规划 `target_chapter = n + 1`
- 需要跳章、补章、回头重做时，显式传 `--target-chapter <m>`
- `status` / `memory` / `quality` / `runtime`
- 只消费当前要检查、生成或回写的 `reference_chapter`
- 不自动把章节号加一
- `workflow_runner` / `chase write` / `chase run` / `chase check`
- 聚合输出应同时暴露 `reference_chapter` 与 `target_chapter`
- 调用 `open/planning/context` 时传目标章节语义
- 调用 `status/memory/runtime/quality` 时传参考章节语义

## 聚合链默认契约
- `chase write` / `chase run` 默认步骤：`doctor,open,runtime,quality,status`
- `chase check` 默认步骤：`doctor,open,quality,status`
- `check` 必须保持 `dry-run`
- `check` 可以做 `quality` 关卡确认，但不得进入 `runtime` 正文生成
- `open` 负责下一章 `target_chapter` 预审
- `quality` / `status` 负责当前 `reference_chapter` 的质检与健康回看

## 聚合输出契约
- `write / run / check` 聚合 JSON 至少应稳定包含：
- `reference_chapter`
- `target_chapter`
- `status`
- `warning_count`
- `steps`
- `report_paths`
- `pipeline_summary`
- `final_release`

`quality` 侧还应明确区分：
- `runtime_only_dimensions`
- `loaded_runtime_dimensions`
- `fallback_runtime_dimensions`
- `missing_runtime_dimensions`
- `runtime_verdict_source`

其中：
- `pipeline_summary.final_release` 是聚合后的发布决策
- 顶层 `final_release` 是对 `pipeline_summary.final_release` 的直接提升，方便 CLI、烟测和上层调用方直接消费
- `final_release` 当前只使用 `pass / revise`
- 若满足以下任一条件，聚合结果必须映射为 `final_release = revise`
- `open_blocking = yes`
- `planning_verdict = fail`
- `runtime_decision in {fail, revise}`
- `quality_final_release = revise`
- `status_runtime_decision in {fail, revise}`
- 存在 `blocking_dimensions`

补充说明：
- `character / causality / promise_payoff / pacing / dialogue` 当前属于 runtime-first verdict 维度。
- `quality` 若要展示这些维度，默认来自已落盘的 runtime payload，而不是独立重跑一整套 runtime writer loop。
- 若没有 runtime payload，`quality` 可以对其中可轻量推断的维度做 fallback，并写入 `fallback_runtime_dimensions`。
- 若 `missing_runtime_dimensions` 非空，不表示这些维度已经通过，只表示本次 `quality` 没拿到对应 runtime verdict。

## 跨任务共通规则
- 统一结论只用 `pass / warn / fail`，必要时再映射到 `revise`
- 若判退，必须补齐 `return_to / rewrite_scope / first_fix_priority / recheck_order`
- reviewer 没有完整读完对应范围，不得直接放行
- 语言、风格、连续性、因果四类问题，默认先修承载方式，再动主线结果
- 任何会影响 `state.md / timeline.md / foreshadowing.md / payoff_board.md / character_arcs.md` 的修改，都必须显式说明是否回写

## Rewrite Escalation Rules
- 任一 `blocking_dimensions` 出现，聚合结果必须能追溯到对应 `RewriteBrief`。
- `runtime_decision in {revise, fail}` 时，`final_release` 不得仍为 `pass`。
- `check` 允许补做 quality/status 判断，但不得偷偷进入 runtime 正文生成。
- 若 reviewer 或脚本建议与 `LeadWriter` 裁决冲突，最终以统一 `RewriteBrief` 为准，而不是并列给 writer 多份口径。

## 成功标准
- 读者能说清这一章发生了什么、为什么发生、结果变了什么
- 章节功能、结果变化、章尾钩子三者一致
- 关键风险落到具体人物、动作、资源或后果，而不是停留在抽象判断
- 需要复核的地方已经过 reviewer 或 gate，而不是只靠作者自检

## Runtime Fallback Notes
- `quality` 暴露 `fallback_runtime_dimensions` 时，表示这些 runtime-first 维度是由轻量 fallback 兜底得出，而不是重跑了一整套 runtime writer loop。
- `missing_runtime_dimensions` 非空时，语义仍然是“本轮没拿到对应 runtime verdict”，不能解释成“这些维度已经 pass”。
- `pacing` fallback 现已覆盖段落重复与 progression density；`promise_payoff` fallback 现已覆盖短兑现落地与章尾 long-tail pressure 是否继续抬升。
- `character / causality / dialogue` fallback 现已覆盖 relationship shift 与 information transfer 一类轻量信号，可揭示“已经试出信息，但关系、站位、压制没有继续变化”的断层。
- 对 `promise_payoff` 而言，fallback 只能校验短兑现和章尾抬高是否可见；真正的承诺债务排序、回收节奏与升级强度，仍以 runtime verdict 为准。
- 上述 fallback 能力仍然只是 quality gate 的兜底补光，不替代 `LeadWriter -> RewriteBrief -> WriterExecutor` 的完整 runtime 裁决。
