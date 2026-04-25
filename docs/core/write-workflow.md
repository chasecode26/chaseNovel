# 写作主链路

> `write` 是重构后统一的写作流水线入口。它不再只是“跑几个脚本”，而是把开写前检查、规划、runtime、状态回看收束成一条主链。

## 核心目标
- 开写前先确认本章是否值得写。
- 先把“本章让读者经历什么”想透，再把“本章交代什么”写清。
- 把 planning/context 与 runtime 连接成连续流水线。
- 让章节、状态、质量、记忆回写使用同一套章节语义。

## Runtime Ownership
- `LeadWriter` 是唯一章节决策者，负责 brief、裁决、rewrite brief。
- `WriterExecutor` 是唯一正文执行路径，负责 draft 与 rewrite。
- evaluator 只能 `pass / warn / fail`，并给出 `minimal_fix`，不能直接改正文。
- schema memory 是运行时真相源；Markdown memory 是阅读层与补充输入层。
- 任一 blocking verdict 都必须先回到 `LeadWriter -> RewriteBrief -> WriterExecutor`，不能绕开主链直接修文。
- `quality / anti-AI / style` 是校稿辅链，不是正文生成主链。

## 主入口
- `chase write --project <dir>`
- `chase write --project <dir> --chapter <n>`
- `chase write --project <dir> --chapter <n> --target-chapter <m>`
- `chase write --project <dir> --steps doctor,open,runtime,quality,status`
- `chase check --project <dir> --chapter <n>`

## 默认流水线

### `write`
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

## 创作主链与校稿辅链

### 创作主链

正文生成前，优先把输入压到这四类：

1. `state.md / timeline.md` 中与本章直接相关的信息
2. `chapter-dramatic-card.md`
3. `character-voice-diff.md`
4. `voice.md / style.md`

创作主链要回答的是：

- 这章最值钱的戏是什么
- 谁在拦谁
- 读者最该被哪一下打中
- 本章结束后，局面具体变了什么

### 校稿辅链

校稿辅链负责：

- continuity
- causality
- anti-repeat
- style drift
- dialogue QA
- promise / payoff

它只能指出问题，不能把 reviewer 腔直接塞回正文。

## 章节编号语义

### reference chapter
- `--chapter <n>` 表示当前已经写完、已经存在的章节号。
- 它是聚合流水线里的 reference chapter。

### target chapter
- `open` 会把 `--chapter <n>` 当作“当前已写章节”。
- 如果没有额外指定，它们默认准备 `target_chapter = n + 1`。
- 如需跳章、补章、回头重做指定章，显式传 `--target-chapter <m>`。

### 分流规则
- `doctor`: 不消费章节号
- `open`: 消费 `reference_chapter`，产出 `target_chapter`
- `runtime/status/quality`: 消费 `reference_chapter`

## 写前最小检查
- `doctor` 确认项目骨架、章节、基础目录是否完整。
- `open` 汇总 planning review 与 next context，判断下一章是否 `write_ready`。
- 若 `open` 仍有 `blocking = yes`，不应直接推进正文链。
- 起稿前必须先把卷纲 / 章功能转译为“本章戏剧卡”，再过一遍“写章前硬核对清单”。
- 若硬核对里任何一项答不清，先修 `state.md / timeline.md / 章卡`，再进 `runtime`。
- 若连“这章最值钱的一下是什么”都答不清，默认不进入正文生成。

## 写章前硬核对清单
1. 时间有没有对上上一章结尾的承诺。
2. 当前在场人数、离场人物、援手人数有没有说清。
3. 伤势、体力、兵器、资源有没有无因变化。
4. 消息是谁带来的，谁现在能知道，谁现在还不该知道。
5. 上章发出的命令、做出的承诺，这章有没有接上。
6. 人和物现在分别在哪，是否来得及到场，位置变化有没有交代。
7. 上一章留下的疲惫、伤势、翻脸、断粮、暴露等后果，这章是否还在生效。
8. 本章最多能推进到哪一步，哪些结果不能提前兑现。

## Runtime 位置
- `runtime` 是写作中段，不是开书入口。
- 它基于当前 reference chapter 的 runtime 状态、brief、角色约束与 pressure/payoff 信号生成中间产物。
- 产物通常落在 `04_gate/chNNN/` 与 `00_memory/retrieval/`。

## 正文生成最小输入

进入 `runtime` 前，默认只给 Writer 这些：

- 本章戏剧卡
- 角色说话差分表
- 单书 voice / style
- 必要的 state / timeline 钉死信息
- 少量题材资产

默认不把整仓 reviewer 术语、质量指标、长串禁令一起塞进正文 prompt。

## Writer 最小导演原则

正文生成时默认遵守：

1. 先写场面，再让读者自己看懂局。
2. 先写人物在做什么，再写为什么，再写结果变了什么。
3. 对话必须承担利益冲突 / 压制 / 试探 / 自保 / 传情中的至少一种功能。
4. 一段最多只留一刀提炼，不准每推进一步都补一句作者总结。
5. 主角被刺中时，要落到一个极小但真实的生理反应。
6. 章尾不要总结命运，要把读者推向下一步。

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

## 写后最小回写
- 一章写完后，必须先回写本章新钉死的信息，再看下一章。
- 默认只强制回写 `state.md / timeline.md`；若涉及伏笔、兑现、人物变化，再同步回写对应记忆文件。
- 若本章已经明确了新的时间承诺、位置变化、在场人数、伤势变化、资源变化、消息送达、命令结果、遗留后果，这些都不能只留在正文里，必须写进记忆。
- 没回写就不要直接开下一章，否则默认容易出现“上一章写过，但下一章忘了”的连续性错误。
- 若出现位置瞬移、到达时间不合理、上章后果无因消失、`state.md / timeline.md` 缺回写，统一视为 blocking，先修再继续。

## 写后必须回写的钉死信息
1. 本章结尾的时间与地点。
2. 本章结尾时谁在场，谁离场，谁在路上。
3. 本章结尾时伤势、体力、兵器、资源变成了什么状态。
4. 哪条消息已经送到，哪条消息还没送到。
5. 哪条命令已经执行到哪一步，哪条承诺已经兑现或卡住。
6. 哪些后果还在持续，哪些后果已经缓解，代价现在落在谁身上。
7. 下一章不能改口的内容是什么。

## 写后回写模板
```markdown
# 本章写后回写

- 本章结尾时间：
- 本章结尾地点：
- 在场人物：
- 已离场人物：
- 在路上人物 / 援手 / 信使：
- 当前伤势 / 体力：
- 当前兵器 / 资源：
- 已送达消息：
- 未送达消息：
- 已执行命令：
- 未执行完命令：
- 已兑现承诺：
- 未兑现承诺：
- 持续中的后果：
- 已缓解的后果：
- 下一章不能改口的点：
```

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
5. `status`

若只想确认是否可开写：
1. `check`

## 什么时候该停下
出现以下任一情况，应先修再跑全链：
- `open` 返回 `blocking = yes`
- `planning_verdict = fail`
- `quality` 出现 blocking verdict
- `status` 暴露 overdue foreshadow / stalled arc / timeline break，但正文仍试图继续硬推

## 聚合输出约定
`write/check` 的聚合 JSON 应至少稳定包含：
- `reference_chapter`
- `target_chapter`
- `status`
- `warning_count`
- `steps`
- `report_paths`

其中：
- `open` step 应显式回传 `target_chapter`
- `runtime/status/quality` step 应显式回传 `reference_chapter`

## 兼容命令
以下旧命令仍可用，但已不再是产品层主入口：

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
