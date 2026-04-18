# LeadWriter 强主控写作运行时设计

## 1. 目标
将 chaseNovel 从“流程型写作工具”升级为“强主控长篇写作运行时”，以长期连载稳定性为第一约束，重点保证：

- 章节不跑偏
- 文风不漂移
- 人设不失真
- 伏笔与承诺不丢失
- 审稿环节不越权改文
- 所有修改都走统一裁决链

系统核心原则：

1. LeadWriter 是唯一正文责任人。
2. WriterExecutor 是唯一正文执行器。
3. 结构化记忆 schema 是运行时真相源。
4. Evaluator 只能阻断和给出最小修法，不能直接改正文。
5. 所有 tools / skills / agents 都从属于 LeadWriter，不得分散正文主权。

## 2. 关键设计决策

### 2.1 强主控
采用强主控模式：LeadWriter 拥有唯一裁决权，其他 agent 或 evaluator 只能提供 verdict、风险和最小修法建议。

### 2.2 LeadWriter + 单一 Writer
LeadWriter 不直接写正文；它负责规划、裁决、生成 rewrite brief。正文永远交给同一个 WriterExecutor 完成，以保证 voice 和落笔方式稳定。

### 2.3 严格阻断型 evaluator loop
任一关键 evaluator 判定 blocking，当前稿件不得放行，必须返回 LeadWriter 生成新的 rewrite brief，再交给同一个 Writer 重写。

### 2.4 硬 schema 记忆
保留 Markdown 作为人工阅读层，但运行时以 schema 数据为准。任何进入主线的新事实都必须能映射到 schema 更新；无法落 schema 的新设定默认视为高风险信息。

## 3. 系统边界与非目标

### 3.1 系统边界
本设计覆盖：

- 章节级写作运行时
- 结构化记忆编译与回写
- 审稿 evaluator loop
- 现有 CLI 入口的内核重构方式

### 3.2 非目标
本设计不做以下事情：

- 不把多个 writer 并行产文作为默认机制
- 不让 advisory specialists 直接参与定稿
- 不把所有文学感受都强行结构化
- 不在本阶段重做所有现有 CLI 名称与用户入口
- 不要求一次性删除全部兼容层

## 4. 运行时核心模块

### 4.1 LeadWriter
唯一总控与唯一正文责任人。

职责：
- 读取并解释结构化记忆
- 生成 ChapterBrief
- 决定 Writer 起稿或重写任务
- 汇总 evaluator verdict
- 做唯一裁决：pass / revise / fail
- 决定哪些记忆需要回写

禁止：
- 不直接拼接 evaluator 建议成正文
- 不允许多个 writer 竞争正文
- 不允许 reviewer 越权定稿

### 4.2 WriterExecutor
唯一正文执行器。

职责：
- 严格依据 ChapterBrief 或 RewriteBrief 产出正文
- 保持书级 voice、节奏、叙述一致性
- 在不越权的前提下完成 draft 与 rewrite

禁止：
- 不得自行新增设定
- 不得自行改变章功能
- 不得绕过记忆约束
- 不得裁决 evaluator 冲突

### 4.3 MemoryCompiler
结构化记忆编译器。

职责：
- 读取 schema 层记忆
- 生成本章唯一可消费的 ChapterContextPacket
- 提供时间、地点、知情边界、资源状态、活跃伏笔、承诺压力、风格约束、forbidden inventions、近章重复对照信息

### 4.4 EvaluatorLoop
只审不写。

职责：
- 对当前稿件做专项检查
- 输出结构化 verdict
- 标注 blocking 与最小修法

禁止：
- 不直接重写正文
- 不给散文化大评论
- 不脱离 schema 和记忆约束发表评论

### 4.5 DecisionEngine
严格裁决器，由 LeadWriter 调用。

职责：
- 汇总 evaluator verdict
- 按固定优先级裁决冲突
- 输出统一 RewriteBrief

### 4.6 MemorySync
定稿后结构化回写器。

职责：
- 回写 schema 和记忆摘要
- 只更新发生变化的状态
- 记录“本章改变了什么”

## 5. 结构化记忆模型

建议在小说项目内采用双层记忆结构：

```text
00_memory/
  schema/
    plan.json
    state.json
    timeline.json
    characters.json
    character_arcs.json
    foreshadowing.json
    payoff_board.json
    style.json
    voice.json
  plan.md
  state.md
  timeline.md
  characters.md
  ...
```

### 5.1 Canonical Schema Layer
schema 层是运行时真相源，要求：
- 字段固定
- 可校验
- 可编译
- 可 diff
- 可精确回写

### 5.2 Human Readable Layer
Markdown 层用于：
- 人工阅读
- 人工修订
- 审阅报告
- 导出说明

若 Markdown 与 schema 冲突，以 schema 为准。

### 5.3 核心 schema 建议

#### state
- currentChapter
- currentVolume
- currentArc
- chapterGoal
- activeConflict
- nextPressure
- sceneAnchors
- openThreads
- forbiddenInventions
- pendingPayoffs

#### timeline
- absoluteTime
- relativeTimeFromPrevChapter
- currentLocation
- travelConstraints
- recentEvents
- injuryStatus
- resourceClock

#### characters
- id
- name
- role
- publicPersona
- privateMotive
- knownBySelf
- knownByOthers
- relationshipMap
- voiceTraits
- hardBoundaries

#### foreshadowing
- threadId
- setupChapter
- setupFact
- triggerCondition
- payoffWindow
- expiryRisk
- currentStatus

#### payoff_board
- promiseId
- promiseType
- readerExpectation
- openedAt
- expectedWindow
- overdueRisk
- status

#### style
- genreTone
- narrationRules
- prohibitedPhrases
- imageryRules
- expositionRules
- sceneDensity
- emotionDeliveryRules

#### voice
- bookVoiceDNA
- narratorDistance
- sentenceRhythm
- dialogueSharpness
- humorStyle
- forbiddenCadence
- commonFailurePatterns

## 6. 执行链设计

### Phase 0: Memory Compile
MemoryCompiler 基于 schema 和记忆资产生成 ChapterContextPacket，作为后续唯一共同输入底座。

### Phase 1: LeadWriter 生成 ChapterBrief
LeadWriter 输出：
- chapterFunction
- mustAdvance
- mustNotRepeat
- requiredPayoffOrPressure
- hookGoal
- allowedThreads
- disallowedMoves
- voiceConstraints
- scenePlan
- successCriteria

Writer 写的不是“想写的一章”，而是“LeadWriter 定义过的一章”。

### Phase 2: Writer 起稿
WriterExecutor 消费 ChapterContextPacket + ChapterBrief，输出 Draft v1。

### Phase 3: Evaluator 并行审稿
至少包含：
- ContinuityEvaluator
- CausalityEvaluator
- PromisePayoffEvaluator
- RepeatEvaluator
- PacingEvaluator
- StyleEvaluator
- DialogueEvaluator

统一 verdict 结构：
- dimension
- status(pass / revise / fail)
- blocking(yes / no)
- evidence
- why_it_breaks
- minimal_fix
- rewrite_scope

### Phase 4: DecisionEngine 裁决
固定优先级：
1. Continuity
2. Causality
3. PromisePayoff
4. Repeat
5. Pacing
6. Style
7. Dialogue

任一 blocking 即不放行。LeadWriter 只输出一个统一 RewriteBrief，不把多个 evaluator 原话直接丢给 Writer。

### Phase 5: Writer 重写
Writer 基于 RewriteBrief 输出 Draft v2。

### Phase 6: 循环直到通过
- 任一 blocking -> 必须返工
- 若连续多轮 blocking 原因未变化 -> LeadWriter 升级为 fail
- fail 后回退到章 brief 重定义、schema 校准或阶段目标纠偏

### Phase 7: Pass 后记忆回写
通过后由 MemorySync 更新：
- state
- timeline
- character_arcs
- foreshadowing
- payoff_board
- findings

并生成本章变化摘要、下一章风险和压力点。

## 7. 工具 / skill / agent 分层

### 7.1 Runtime Core
- LeadWriter
- MemoryCompiler
- WriterExecutor
- DecisionEngine
- MemorySync

### 7.2 Blocking Evaluators
- ContinuityEvaluator
- CausalityEvaluator
- PromisePayoffEvaluator
- RepeatEvaluator
- PacingEvaluator
- StyleEvaluator
- DialogueEvaluator

### 7.3 Operational Skills / Tools
保留为工具层：
- open
- status
- quality
- timeline_check
- anti_repeat_scan
- language_audit
- foreshadow_scheduler
- arc_tracker
- dashboard_snapshot
- book_health

### 7.4 Advisory Specialists
按需调用：
- WorldbuildingAdvisor
- GenreAdvisor
- HookAdvisor
- EmotionAdvisor
- ResearchAdvisor
- RelationshipAdvisor
- CombatAdvisor
- PoliticsAdvisor

制度性约束：所有 skill、agent、工具、脚本默认只能增强 LeadWriter 的判断，不得分散正文主权。

## 8. 当前仓库的落地策略

### 8.1 外部入口保持稳定
继续保留：
- chase open
- chase write
- chase quality
- chase status

内部重新定义：
- open -> 准备 / 校验 ChapterContextPacket
- write -> 驱动 LeadWriterRuntime
- quality -> 独立运行 evaluator 集合
- status -> 书级 schema 健康与推进压力分析

### 8.2 新增 Runtime Core 目录
建议新增：

```text
runtime/
  lead_writer.py
  memory_compiler.py
  writer_executor.py
  evaluator_loop.py
  decision_engine.py
  memory_sync.py
  contracts.py
```

### 8.3 schema 与校验层
在仓库中补：

```text
schemas/
  plan.schema.json
  state.schema.json
  timeline.schema.json
  characters.schema.json
  ...
```

### 8.4 evaluator 协议层
建议新增：

```text
evaluators/
  continuity.py
  causality.py
  promise_payoff.py
  repeat.py
  pacing.py
  style.py
  dialogue.py
```

### 8.5 现有脚本迁移方式

保留为工具层：
- scripts/timeline_check.py
- scripts/anti_repeat_scan.py
- scripts/language_audit.py
- scripts/foreshadow_scheduler.py
- scripts/arc_tracker.py
- scripts/book_health.py
- scripts/dashboard_snapshot.py

降级为兼容 façade：
- scripts/workflow_runner.py
- scripts/engine_runner.py
- scripts/quality_gate.py
- scripts/planning_context.py
- scripts/memory_sync.py

新建/重构核心对象：
- LeadWriterRuntime
- ChapterContextPacket
- ChapterBrief
- EvaluatorVerdict
- RewriteBrief
- MemoryPatch
- schema validator
- runtime orchestrator

## 9. 风险与反模式

### 9.1 LeadWriter 变成超级 prompt
防法：LeadWriter 只保留主控和裁决权，不吞掉 Writer、Evaluator、MemorySync 的职责。

### 9.2 Writer 偷回主权
防法：Writer 只能消费 ChapterBrief / RewriteBrief；任何超出 brief 的新增都视为违规。

### 9.3 Evaluator 越审越写
防法：evaluator 只输出结构化 verdict，最多给 minimal_fix，不给成稿替换文本。

### 9.4 schema 过重
防法：schema 只覆盖运行时必需事实，不把全部文学感受强行结构化。

### 9.5 write / quality / status 三套标准
防法：三者共享同一 schema 真相源、同一 verdict 协议、同一 pass / revise / fail 语义。

### 9.6 工具过多导致主控失焦
防法：blocking evaluator 固定最小集；advisory specialists 按需调用；所有输出必须能被 LeadWriter 消化。

### 9.7 过度审稿拖慢推进
防法：blocking 只针对真正破坏连载稳定性的项；rewrite brief 必须限制返工范围，避免无限磨稿。

## 10. 推荐实施顺序

### Phase 1: 先立 contract
定义：
- schema
- ChapterContextPacket
- ChapterBrief
- EvaluatorVerdict
- RewriteBrief
- MemoryPatch

### Phase 2: 再立 LeadWriterRuntime
把 write 主链收口到 LeadWriter。

### Phase 3: 接 evaluator loop
让 quality 和 write 共享 evaluator contract。

### Phase 4: 接 memory sync 与 status
让 status 成为真正的运行时观测面板。

## 11. 最终结论
推荐采用以下目标架构：

- 以 LeadWriter 为唯一正文责任人
- 以硬 schema 记忆为真相源
- 以单一 Writer 为唯一正文执行器
- 以严格阻断型 evaluator loop 为质量门禁
- 以多 tool / skill / agent 作为 LeadWriter 的能力插件

这是比当前“流程型多角色协作”更稳定的升级方向，更适合中文网文长篇连载对声口统一、递进稳定、长期连续性的要求。
