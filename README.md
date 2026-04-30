# chaseNovel

## Platform Assets

默认平台口味面向番茄和七猫。正文生成、审稿和放行门会共同读取：

- `templates/core/platform-profile.md`
- `templates/core/prose-examples.md`
- `templates/core/pre-publish-checklist.md`
- `templates/core/opening-diagnostics.md`
- `templates/core/expectation-lines.md`
- `templates/core/genre-framework.md`

如果某本书需要更具体的平台策略，把同名文件复制到项目 `00_memory/` 下即可覆盖默认模板。

`chaseNovel` 是面向中文网文长篇连载的本地写作引擎，当前定位为 **Claude Code 原生智能写作 agent 工作台**。

它不追求单次生成一章就结束，而是围绕长篇连载的稳定推进建立闭环：

- 章节目标、阶段节奏与追读钩子
- 设定连续性、时间线、知情边界与资源状态
- 人物弧光、关系推进与声口差分
- 伏笔、承诺、兑现与防重复
- 正文场面密度、去总结腔、去抽象腔、低 AI 味
- 写作、复核、返工、放行、记忆回写

## 当前写作架构

外层命令仍然是稳定 workflow：

```text
open -> runtime -> quality -> status
```

`runtime` 内部已经升级为 agent 写作闭环：

```text
LeadWriterAgent
-> DirectorAgent
-> SceneBeatAgent
-> WriterAgent
-> ReviewerAgent
-> DecisionEngine
-> RewriterAgent
-> ReleasePolicy
-> Agent Replay Report
-> RuntimeMemorySync
```

说明：

- `LeadWriterAgent` 负责章节目标、核心冲突、结果变化、章尾钩子和边界。
- `DirectorAgent` 负责节奏、开场画面、中段反转、对白压力和章尾落点。
- `SceneBeatAgent` 在正文前生成场面拍点，锁定人话表达、设定边界、时间线、伏笔与市场追读牵引。
- `WriterAgent` 读取 prompt / handoff / SceneBeatPlan 写正文。
- `ReviewerAgent` 只审查，不改文，输出结构化 verdict。
- `DecisionEngine` 统一决定 `pass / revise / fail`。
- `RewriterAgent` 按 `RewriteBrief` 做局部返工，不重开章节。
- `ReleasePolicy` 输出最终放行门禁。

## Claude Code Handoff 模式

项目不内置外部 LLM provider。Claude Code 本身就是智能执行者；本地 runtime 负责生成任务卡、上下文、审查报告和质量门。

每章主要产物位于：

```text
04_gate/chXXX/
```

关键文件：

- `agent_prompts/*.md`：每个 agent 实际使用的 prompt 快照。
- `handoffs/writer_handoff.md`：给 Claude Code / WriterAgent 的写作交接卡。
- `handoffs/reviewer_handoff.md`：审查交接卡。
- `handoffs/rewriter_handoff.md`：返工交接卡。
- `scene_beat_plan.md/json`：章卡到正文之间的场面拍点。
- `lead_writer_agent_report.md/json`：章节目标、冲突、结果、钩子和边界检查。
- `director_agent_report.md/json`：节奏、情绪曲线、对白压力和落点检查。
- `scene_beat_agent_report.md/json`：场面拍点、人话规则、设定/时间线/伏笔边界检查。
- `reviewer_agent_report.md/json`：多维审查报告。
- `release_gate_report.md/json`：最终放行门禁。
- `agent_replay_report.md/json`：每轮 agent 执行复盘。

## 命令

```bash
chase open --project <dir> [--chapter <n> | --target-chapter <n>]
chase quality --project <dir> [--chapter-no <n> | --from <n> --to <n>]
chase write --project <dir> [--chapter <n> | --target-chapter <n>] [--steps <csv>]
chase status --project <dir> [--chapter <n>] [--focus <all|dashboard|foreshadow|arc|timeline|repeat>]
chase check --project <dir> [--chapter <n> | --target-chapter <n>]
```

默认：

- `chase write`：`open,runtime,quality,status`
- `chase check`：`open,quality,status`，dry-run，不进入正文生成

## 章节语义

- `--chapter <n>` 表示已经存在的参考章节，即 `reference_chapter`。
- `open` 默认准备 `target_chapter = reference_chapter + 1`。
- `runtime / quality / status` 继续消费 `reference_chapter`。
- 跳章、补章、回头重做目标章节时，显式传 `--target-chapter <m>`。

## 入口文档

- 路由入口：[SKILL.md](SKILL.md)
- 架构说明：[ARCHITECTURE.md](ARCHITECTURE.md)
- 写作主链：[docs/core/write-workflow.md](docs/core/write-workflow.md)
- runtime 事实基线：[docs/core/runtime-design-baseline.md](docs/core/runtime-design-baseline.md)
- 合同索引：[docs/core/task-contracts.md](docs/core/task-contracts.md)

当文档与 shipped runtime 行为冲突时，以 `docs/core/runtime-design-baseline.md` 和当前 `runtime/` 代码为准。
