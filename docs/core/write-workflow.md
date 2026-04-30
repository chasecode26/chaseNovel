# writer：正文生成主链

`writer` 负责把 chapter-ready 的输入落成可读正文。当前实现不是单脚本生成，而是 Claude Code handoff 友好的 agent 闭环。

## 公开入口

```bash
chase write --project <dir>
chase write --project <dir> --chapter <n>
chase write --project <dir> --chapter <n> --target-chapter <m>
chase write --project <dir> --steps open,runtime,quality,status
```

默认 workflow：

```text
open -> runtime -> quality -> status
```

## runtime 写作闭环

```text
MemoryCompiler
-> LeadWriterAgent.create_brief()
-> DirectorAgent.direct()
-> SceneBeatAgent.plan()
-> WriterAgent.draft()
-> ReviewerAgent.review_with_report()
-> DecisionEngine.decide()
-> RewriterAgent.rewrite() if revise
-> ReleasePolicy.evaluate()
-> RuntimeMemorySync.summarize()
```

WriterAgent / ReviewerAgent / ReleasePolicy all load the same market assets before judging a chapter:

- `templates/core/platform-profile.md`: Fanqie/Qimao reader taste, retention rhythm, and hard red lines.
- `templates/core/prose-examples.md`: good prose patterns and bad AI-summary patterns.
- `templates/core/pre-publish-checklist.md`: final release checklist. A project can override any of these by placing a same-name file under `00_memory/`.
- `templates/core/opening-diagnostics.md`: golden first chapter / stage-opening diagnosis.
- `templates/core/expectation-lines.md`: short expectation, long expectation, payoff, new expectation, and expectation-gap risk.
- `templates/core/genre-framework.md`: genre promise calibration and micro-innovation boundaries.

最多重写 2 轮。连续 blocking 原因不变时升级为 `fail`，不无限磨稿。

## Agent 职责

### LeadWriterAgent

职责：

- 锁定本章目标、核心冲突、结果变化、章尾钩子。
- 检查设定、人物、时间线、伏笔/回收边界是否可写。
- 生成 `lead_writer_agent_report.md/json`。
- blocking 后负责生成 revise brief，但不写正文。

### DirectorAgent

职责：

- 把 brief 转成“怎么拍”的导演单。
- 锁定开场画面、第一冲突、中段反转、情绪曲线、对白压力、章尾落点。
- 生成 `director_agent_report.md/json`。

### SceneBeatAgent

职责：

- 把导演单拆成可写场面拍点。
- 每个 beat 必须含目标、冲突对象、第一交锋、反转、代价、信息释放、下一场牵引。
- 每个 beat 必须含人话规则、市场追读点、设定边界、时间线边界、伏笔/回收处理。
- 生成 `scene_beat_agent_report.md/json` 与 `scene_beat_plan.md/json`。

### WriterAgent

职责：

- 读取 `writer-agent.md`、brief、direction、SceneBeatPlan、voice/style。
- 生成 `writer_handoff.md/json`。
- 生成正文、writer prompt、review notes。
- 确保正文不是总结，而是场面。

硬规则：

- 每段至少两种场面信号：动作、物件、身体反应、对白压力、环境阻碍、局面变化。
- 不把 reviewer、runtime、scene card、beat、quality gate 等术语写进正文。
- 章尾必须有表层事件钩子和里层情感/代价钩子。

### ReviewerAgent

职责：

- 只审查，不改文。
- 输出结构化 `EvaluatorVerdict`。
- 生成 `reviewer_handoff.md/json` 和 `reviewer_agent_report.md/json`。

当前重点维度：

- `prose_concreteness`：抽象、总结、不说人话、AI 味。
- `story_logic`：场景目标、反转、代价、下一步牵引。
- `hook_integrity`：章尾双层钩子。
- `scene_density`：SceneBeatPlan 是否被正文承载。
- `continuity_guardrail`：设定、时间线、知情边界、伏笔/回收是否前置锁定。
- `market_fit`：平台追读牵引、胜利代价、场景末端小钩子是否成立。
- `pre_publish_checklist`：发稿前清单是否通过，重点卡开章入戏、目标/冲突/结果/代价、章尾 next_pull、故事内语言。
- `expectation_integrity`：短期待、长期待、兑现点、新挂期待和断期待风险是否连续。
- `opening_diagnostics`：黄金一章/阶段开篇是否完成吸睛、人设、卖点、危机和最小信息释放。
- `genre_framework_fit`：章节看点是否符合题材承诺，微创新是否过载。

## Long-term expectation memory

`RuntimeMemorySync` writes expectation tracking after each runtime run:

- `00_memory/schema/expectation_tracking.json`: structured history of short expectations, long expectations, payoffs, new expectations, expectation-gap risks, genre framework hints, and related watch dimensions.
- `00_memory/retrieval/expectation_tracking.md`: human-readable latest chapter tracking report.
- `00_memory/retrieval/expectation_tracking.latest.json`: latest chapter tracking payload for Claude Code handoff.

This does not replace `state.json` or `payoff_board.json`; it adds a dedicated long-term trail for reader-expectation continuity.
- 其他 runtime evaluator：pacing、causality、promise_payoff、chapter_progress、dialogue、character。

### RewriterAgent

职责：

- 只按 `RewriteBrief` 返工。
- 生成 `rewriter_handoff.md/json`。
- 保存 `reader_manuscript.before_rewrite.md`。
- 输出 `rewrite_operation.json`。

局部手术规则：

- `chapter_tail`：只替换章尾段。
- `dialogue`：只替换对白段。
- `flagged_paragraphs`：只替换抽象/总结问题段。
- `scene_beat_plan`：先修场面结构，再动正文。

## Claude Code handoff 文件

每章产物位于：

```text
04_gate/chXXX/
```

关键文件：

- `agent_prompts/writer-agent.md`
- `agent_prompts/lead-writer-agent.md`
- `agent_prompts/director-agent.md`
- `agent_prompts/scene-beat-agent.md`
- `agent_prompts/reviewer-agent.md`
- `agent_prompts/rewriter-agent.md`
- `handoffs/writer_handoff.md`
- `handoffs/reviewer_handoff.md`
- `handoffs/rewriter_handoff.md`
- `scene_beat_plan.md`
- `lead_writer_agent_report.md`
- `director_agent_report.md`
- `scene_beat_agent_report.md`
- `writer_prompt.md`
- `reader_manuscript.md`
- `runtime_review_notes.md`
- `reviewer_agent_report.md`
- `release_gate_report.md`
- `agent_replay_report.md`

Claude Code 作为智能执行者时，应读取 handoff 文件执行写、审、改；runtime 负责留痕、判定和回写。

## Rewrite contract

- evaluator / ReviewerAgent 只能指出问题，不能直接改正文。
- `DecisionEngine` 必须输出唯一 `RewriteBrief`。
- `RewriterAgent` 只能修 `rewrite_scope` 指定范围。
- 已经有效的场面、对白压力、人物动作和章尾钩子必须尽量保留。
- 回炉后必须重新经过 ReviewerAgent 和 ReleasePolicy。

## Quality boundary

`quality` 是公开质量门，但不是 runtime writer loop 的替身。

runtime 内部优先使用 agent/evaluator verdict；外层 `quality` 继续作为统一门禁聚合，面向 CLI 和报告层。

## 章节语义

- `--chapter <n>` 是已存在章节，即 `reference_chapter`。
- `open` 默认准备 `target_chapter = n + 1`。
- `runtime / quality / status` 消费 `reference_chapter`。

## 相关文档

- `docs/core/runtime-design-baseline.md`
- `docs/core/open-book.md`
- `docs/core/revise-diagnostics.md`
- `docs/core/status-workflow.md`
- `references/contracts/02-write.md`
