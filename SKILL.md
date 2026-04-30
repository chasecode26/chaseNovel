---
name: chaseNovel
description: 当用户要策划、起稿、续写、改写或管理中文网文长篇连载，并关心章节节奏、章尾钩子、伏笔回收、设定连续性、角色推进与追读留存时使用。
---

# chaseNovel

`chaseNovel` 是中文长篇网文连载的主 skill，当前面向 **Claude Code 原生智能写作 agent 工作流**。

它负责判断用户处于哪个创作阶段，并路由到正确能力面；真正的章节写作由 shipped CLI 与 runtime agent 闭环执行。

## 路由

| 场景 | 优先进入 | 文档 / 合同 |
| --- | --- | --- |
| 开书、黄金三章、卷纲、阶段目标 | `opening` | `docs/core/open-book.md` / `references/contracts/01-launch.md` |
| 写第 X 章、把章卡落成正文 | `writer` | `docs/core/write-workflow.md` / `references/contracts/02-write.md` |
| 接上上一章钩子继续写 | `continue` | `references/contracts/03-continue.md` |
| 改章、诊断、返工 | `revise` | `docs/core/revise-diagnostics.md` / `references/contracts/04-modify.md` |
| 校正文风、去 AI 味、拉开角色声口 | `style` | `docs/core/style-governance.md` |
| 查看当前状态、节奏、承诺、重复风险 | `memory` | `references/contracts/05-state-and-rhythm.md` / `references/contracts/06-promises-and-repeat.md` |

## 当前写作主链

公开入口不新增子命令，仍使用：

```bash
chase write --project <dir> [--chapter <n> | --target-chapter <n>] [--steps <csv>]
```

默认链路：

```text
open -> runtime -> quality -> status
```

`runtime` 内部链路：

```text
LeadWriterAgent -> DirectorAgent -> SceneBeatAgent -> WriterAgent -> ReviewerAgent -> DecisionEngine -> RewriterAgent -> ReleasePolicy -> MemorySync
```

## Agent 边界

- `LeadWriterAgent`：锁定目标、冲突、结果、钩子、设定边界、人物压力。
- `DirectorAgent`：锁定节奏、开场画面、中段反转、对白压力、情绪曲线。
- `SceneBeatAgent`：锁定每场目标、交锋、代价、伏笔/回收、时间线和人话规则。
- `WriterAgent`：按 `writer-agent.md`、章卡、导演单、SceneBeatPlan 写正文。
- `ReviewerAgent`：只复核，不改文；输出 `prose_concreteness / story_logic / hook_integrity / scene_density / continuity_guardrail / market_fit` 等 verdict。
- `RewriterAgent`：只按 `RewriteBrief` 和 `rewrite_scope` 做局部返工。
- `DecisionEngine`：统一决定 `pass / revise / fail`。
- `ReleasePolicy`：最终放行门禁。

## Claude Code Handoff

本项目不要求内置 LLM provider。Claude Code 是外部智能执行者；runtime 负责生成强 handoff 与质量门。

每章会生成：

- `04_gate/chXXX/handoffs/writer_handoff.md`
- `04_gate/chXXX/handoffs/reviewer_handoff.md`
- `04_gate/chXXX/handoffs/rewriter_handoff.md`
- `04_gate/chXXX/agent_prompts/*.md`
- `04_gate/chXXX/lead_writer_agent_report.md`
- `04_gate/chXXX/director_agent_report.md`
- `04_gate/chXXX/scene_beat_agent_report.md`
- `04_gate/chXXX/scene_beat_plan.md`
- `04_gate/chXXX/reviewer_agent_report.md`
- `04_gate/chXXX/release_gate_report.md`
- `04_gate/chXXX/agent_replay_report.md`

Claude Code 写作时应优先读取这些 handoff 文件，而不是绕开 runtime 自由发挥。

## 章节语义

- `--chapter <n>` 表示已经写完、已经存在的 `reference_chapter`。
- `open` 默认准备 `target_chapter = n + 1`。
- `runtime / quality / status` 消费 `reference_chapter`。
- 跳章、补章、回头重做目标章节时，显式传 `--target-chapter <m>`。

## 判断准则

如果文档和实际行为冲突：

1. 优先相信 `runtime/`、`scripts/workflow_runner.py`、`quality_gate.py`、`book_health.py`。
2. 再看 `docs/core/runtime-design-baseline.md`。
3. 不另起一套平行流程；把文档改回当前 shipped runtime 事实。
