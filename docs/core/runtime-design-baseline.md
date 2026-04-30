# Runtime design baseline

这是 shipped runtime 的事实基线。文档、合同或 skill 说明与实际运行冲突时，以本文件和当前 `runtime/` 代码为准。

## Primary references

- `scripts/workflow_runner.py`
- `runtime/runtime_orchestrator.py`
- `runtime/agents/`
- `runtime/release_policy.py`
- `runtime/quality_service.py`
- `scripts/quality_gate.py`
- `scripts/book_health.py`

## Workflow surface

`write` 默认链路：

```text
open -> runtime -> quality -> status
```

`check` 默认链路：

```text
open -> quality -> status
```

`check` 保持 dry-run，不进入 runtime 正文生成。

## Runtime ownership

- `LeadWriterAgent` 是章节决策 owner，负责 brief 与 revise brief。
- `DirectorAgent` 把 brief 转为导演单。
- `SceneBeatAgent` 在正文前生成 SceneBeatPlan。
- `WriterAgent` 负责写作 handoff 与初稿生成。
- `ReviewerAgent` 负责结构化复核，只判病不改文。
- `DecisionEngine` 输出唯一 `RuntimeDecision / RewriteBrief`。
- `RewriterAgent` 按 `RewriteBrief` 局部返工。
- `ReleasePolicy` 负责最终放行门禁。
- `RuntimeMemorySync` 负责 runtime summary 与 schema patch 回写。

## Agent files

Agent 代码集中在：

```text
runtime/agents/
```

主要模块：

- `writer.py`
- `lead_writer.py`
- `director.py`
- `scene_beat.py`
- `reviewer.py`
- `rewriter.py`
- `writer_executor.py`
- `scene_beat_planner.py`
- `handoff.py`
- `local_rewrite.py`
- `prompt_loader.py`
- `model_gateway.py`

说明：

- `writer_executor.py` 是 Writer/Rewriter 共用的底层正文执行器，已经归入 agent 文件夹。
- 项目不要求内置真实 LLM provider；`model_gateway.py` 当前主要承担 trace / abstraction / future adapter 角色。
- Claude Code 是外部智能执行者，runtime 生成 handoff 与质量门。

## Prompt and handoff

Prompt 模板：

```text
templates/agents/writer-agent.md
templates/agents/lead-writer-agent.md
templates/agents/director-agent.md
templates/agents/scene-beat-agent.md
templates/agents/reviewer-agent.md
templates/agents/rewriter-agent.md
```

Handoff 模板：

```text
templates/agents/writer-handoff.md
templates/agents/reviewer-handoff.md
templates/agents/rewriter-handoff.md
```

每章运行后，runtime 会在 `04_gate/chXXX/` 下生成：

- `agent_prompts/*.md`
- `handoffs/*.md`
- `scene_beat_plan.md/json`
- `lead_writer_agent_report.md/json`
- `director_agent_report.md/json`
- `scene_beat_agent_report.md/json`
- `reviewer_agent_report.md/json`
- `release_gate_report.md/json`
- `agent_replay_report.md/json`

## Verdict and release

`EvaluatorVerdict` 保持统一结构：

```text
dimension
status: pass | warn | fail
blocking
evidence
why_it_breaks
minimal_fix
rewrite_scope
```

关键 blocking 会回到：

```text
LeadWriter + RewriterAgent
```

`ReleasePolicy` 输出：

- `final_release`: `pass | warn | revise | fail`
- `release_allowed`
- `must_rewrite`
- `blocking_dimensions`
- `advisory_dimensions`
- `reasons`

## Memory truth source

- `00_memory/schema/*.json` 是 runtime 真相源。
- Markdown memory 是人工阅读层与 fallback 输入层。
- `RuntimeMemorySync` 负责 schema patch、apply report 和 runtime summary。
- `00_memory/schema/expectation_tracking.json` 专门追踪短期待、长期待、兑现点、新挂期待、断期待风险和题材承诺，用于长期观察追读链是否断档。

## Rule of thumb

如果文档和 shipped 行为冲突：

1. 优先相信 `runtime/` 与 `scripts/workflow_runner.py`。
2. 再看 `quality_gate.py` 与 `book_health.py`。
3. 修改文档回到当前主线，不另起平行 runtime 规范。
