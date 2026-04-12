# 输出契约与运行校验参考

这份文档负责两件事：

- 给 `chaseNovel` 的核心角色定义统一输出格式
- 给多 Agent 流程定义统一的 `blocking / revise / pass` 裁决约定

按命令拆开的详细模板仍在 `references/contracts/`。
这里只保留跨任务通用的输出骨架、运行原则和成功标准。

## 目录

- 分命令输出契约索引
- 角色输出契约
- 回退与裁决契约
- 常见错误
- 风险信号
- 默认运行原则
- 成功标准

---

## 分命令输出契约索引

- `/一键开书`：详见 `references/contracts/01-launch.md`
- `/写`：详见 `references/contracts/02-write.md`
- `/继续`：详见 `references/contracts/03-continue.md`
- `/修改`：详见 `references/contracts/04-modify.md`
- `/状态`、`/卷节奏`：详见 `references/contracts/05-state-and-rhythm.md`
- `/角色弧`、`/承诺`、`/兑现`、`/防重复`：详见 `references/contracts/06-promises-and-repeat.md`
- `ResearchMaterial`：详见 `references/contracts/07-research-material.md`

使用方式：

- 先在本文确认当前任务是否需要固定输出骨架
- 再只补读对应命令的 contract 文件
- 若要校验 reviewer、回退、门禁、成功标准，以本文为准

---

## 角色输出契约

以下契约默认适用于长篇连载的多 Agent 主链：

`Planner -> HookEmotion -> Writer -> (LanguageReviewer || StyleDialogue || ContinuityReviewer || CausalityReviewer) -> Reviewer`

说明：
- 这里的 `Reviewer` 指总审角色，负责最终放行
- `LanguageReviewer / StyleDialogue / ContinuityReviewer / CausalityReviewer` 属于并行 reviewer，不等于总审

### `Planner`

最少必须输出：

- `chapter_function`
- `result_change`
- `hook_type`
- `chapter_tier`
- `target_word_count`
- `time_anchor`
- `location_anchor`
- `present_characters`
- `knowledge_boundary`
- `resource_state`
- `open_threads`
- `forbidden_inventions`
- `planning_verdict`

其中：

- `chapter_function` 必须回答“本章为什么必须存在”
- `result_change` 必须是可感知的变化，不能只写“气氛更紧”
- `planning_verdict` 只能是 `pass` 或 `revise`

### `HookEmotion`

最少必须输出：

- `entry_pressure`
- `midpoint_pressure`
- `peak_moment`
- `aftershock`
- `hook_type`
- `hook_line_or_direction`
- `blocking`
- `suggested_fix`

要求：

- 只负责情绪曲线和断点承接
- 不改主线结论

### `Writer`

最少必须输出：

- `draft_scope`
- `chapter_text`
- `self_check`
- `result_change`
- `memory_writeback_needed`
- `known_risks`

其中：

- `draft_scope` 要写清本次覆盖哪些场景
- `self_check` 至少覆盖：提炼句、黑话简称、角色声口、场景密度、结果变化
- `memory_writeback_needed` 需列出是否要回写 `state.md`、`timeline.md`、`foreshadowing.md` 等

### `LanguageReviewer`

最少必须输出：

- `findings`
- `blocking`
- `suggested_fix`
- `ai_tone_source`
- `needs_full_rewrite`

`findings` 默认重点覆盖：

- 提炼句
- 概括句
- 黑话简称
- 半截推理
- 机械过渡
- 假氛围
- 抽象收口句

### `StyleDialogue`

最少必须输出：

- `findings`
- `blocking`
- `suggested_fix`
- `voice_conflict`
- `naming_conflict`

### `ContinuityReviewer`

最少必须输出：

- `findings`
- `blocking`
- `suggested_fix`
- `continuity_conflict`
- `memory_files_affected`

### `CausalityReviewer`

最少必须输出：

- `findings`
- `blocking`
- `suggested_fix`
- `causality_gap`
- `fact_judgment_consequence_clear`

### `Reviewer`

最少必须输出：

- `blocking`
- `human_read_verdict`
- `repeat_window`
- `upgrade_point`
- `script_missed_issue`
- `full_chapter_read`
- `rewrite_handoff`
- `final_release`

约束：

- `full_chapter_read` 只能是 `yes` 或 `no`
- `final_release` 只能是 `pass` 或 `revise`
- 没有 `full_chapter_read: yes`，不得放行
- `final_release` 表示总审放行结论；若脚本层使用 `script_final_release`，仅字段名不同，含义一致

---

## 回退与裁决契约

### reviewer 通用输出格式

除 `Planner`、`Writer` 外，其余 reviewer 默认都至少输出：

- `findings`
- `blocking`
- `suggested_fix`

其中：

- `findings` 不是空泛总评，必须指出具体问题层
- `blocking` 只能是 `yes` 或 `no`
- `suggested_fix` 必须是可执行修法，不能只写“再润一润”

### `blocking` 解释

- `blocking=yes`
  本轮不得继续进入下一个主流程环节，必须回退
- `blocking=no`
  只代表该 reviewer 本轮不阻断，不代表整章自动放行

### 回退输出格式

只要 `blocking=yes`，必须补齐：

- `return_to`
- `rewrite_scope`
- `first_fix_priority`
- `recheck_order`

解释：

- `return_to`
  只能指向明确角色，如 `Writer`、`Planner + Writer`
- `rewrite_scope`
  说明是整句、整段、整场还是整章
- `first_fix_priority`
  说明先修逻辑、连续性、声口还是语言承载
- `recheck_order`
  说明修完后先回哪个 reviewer

### 推荐回退映射

- AI 味、抽象判断、假氛围、场景太薄
  - `return_to: Writer`
- 声口压平、对白搬信息、称谓错位
  - `return_to: Writer + StyleDialogue`
- 时间线、设定、知情边界、资源状态冲突
  - `return_to: Planner + Writer + ContinuityReviewer`
- 转折无前提、推理链不闭合、结果落不实
  - `return_to: Planner + Writer + CausalityReviewer`

### 双闸题材补充契约

若章节涉及军报、敌情、权谋、推理，再补：

#### `language_block`

- `plain_language_pass: yes | no`
- `term_explained_on_first_use: yes | no`
- `qa_matched: yes | no`
- `order_can_execute: yes | no`

#### `causality_block`

- `fact_judgment_consequence_clear: yes | no`
- `protagonist_reasoning_clear: yes | no`
- `shared_conditions_checked: yes | no`
- `reader_inference_gap: yes | no`

任一字段为 `no`，默认整章 `revise`。

---

## 常见错误

### 1. 把“能写很多”误当成“适合连载”

长篇连载最怕无效字数。能扩写不代表能持续追读。

### 2. reviewer 只给感受，不给回退路径

“不太对”“有点 AI 味”“再润一下”都不算有效审稿。

### 3. 只审语言，不审章节功能

很多“文不顺”其实是本章功能不成立、结果变化不足、冲突过弱。

### 4. 把脚本通过当成交稿通过

脚本只负责扫雷，不负责人眼读感。

### 5. 回退时只说重写，不说先修哪一层

不先定优先级，`Writer` 很容易先修文气，后修逻辑，最后返工更重。

### 6. 忘记要求 `full_chapter_read`

没有整章顺读，很多 AI 味和节奏塌陷根本抓不出来。

### 7. 章节通过了却不标记 memory 回写需求

这会让下一章连续性失真。

---

## 风险信号

出现以下信号时，应暂停继续堆正文，先回到章卡、memory 文件与 reviewer 契约：

- “这章好像也不是不能删”
- “先多写点过渡再说”
- “先把字数补够”
- “先别说太清楚，显得高级”
- “脚本没报，应该能过”
- “这段虽然不太像人话，但先放过去”
- “后面一起补 state”
- “这段就先用‘刀’‘主口’这种说法，读者应该懂”

这些通常意味着：
章节功能失焦、信息承载失控、文风发虚或连载记忆开始失真。

---

## 默认运行原则

- 默认长篇连载使用多 Agent 主链
- 默认同一章同一时刻只允许一个 `Writer`
- 默认 reviewer 并行，但最终裁决统一收束到 `Reviewer`
- 默认先过规划预审，再进正文
- 默认 `Reviewer` 先整章顺读，再分类拆检
- 默认命中 `blocking=yes` 就回退，不往下硬推
- 默认脚本、黑名单、审卡是辅助证据，不替代人眼
- 默认场景承载信息，不能靠提炼句、黑话、抽象判断代替
- 默认普通章 `2300-3500` 字，高点章可放宽到 `4500`
- 默认先保证“下一章有人想看”，再谈局部辞藻精细度

---

## 成功标准

这套输出契约被正确执行时，应达到这些结果：

- 每个角色知道自己必须交什么
- reviewer 不会只给模糊感受
- `blocking` 有统一含义，不会被随意解释
- 回退后能直接进入明确重写路径
- 章节不会在没过总审时偷偷流入下一章
- AI 味、黑话简称、半截推理、假氛围能被稳定拦住
- 场景薄、声口压平、逻辑断裂能在复审阶段被抓出
- memory 回写需求能被及时显式化
- 新会话也能恢复当前章节生产状态
