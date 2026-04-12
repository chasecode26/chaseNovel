### `/修改`

输出：

- `Reviewer` 初检
- `Planner` 修复策略
- `HookEmotion` 结果
- `Writer` 修订稿
- `LanguageReviewer` 结果
- `StyleDialogue` 结果
- `ContinuityReviewer` 结果
- `CausalityReviewer` 结果
- `Reviewer` 复核
- 需要更新的记忆点

#### `/修改` 固定输出模板

```markdown
# 修章方案

## Agent 编排
- 默认顺序：`Reviewer -> Planner -> HookEmotion -> Writer -> (LanguageReviewer || StyleDialogue || ContinuityReviewer || CausalityReviewer) -> Reviewer`

## 1. Reviewer 初检

### 1.1 问题诊断
- 当前问题类型：
- 最主要故障：
- 次级故障：
- 当前最影响追读的问题：
- `blocking`：yes / no

### 1.2 影响面判断
- 是否允许只改本章：
- 会影响哪些人物状态：
- 会影响哪些伏笔 / 承诺：
- 会影响哪些后续章节：

### 1.3 必须保留项
- 必留事实：
- 必留结果：
- 必留伏笔：
- 必留人物关系：
- `rewrite_handoff`：

## 2. Planner 修复策略
- 修法类型：压缩 / 重写 / 重排信息 / 补结果 / 补钩子 / 修动机 / 换反应
- `chapter_function`：
- `result_change`：
- `hook_type`：
- `chapter_tier`：
- `target_word_count`：
- 优先修哪一层：
- 本章修后必须成立什么：
- 本章绝不能再出现什么：
- 需要补读哪些 memory 文件：
- `planning_verdict`：pass / revise

## 3. HookEmotion 结果
- `entry_pressure`：
- `midpoint_pressure`：
- `peak_moment`：
- `aftershock`：
- 情绪跳跃是否存在：
- 钩子失效是否存在：
- `blocking`：yes / no
- `suggested_fix`：

## 4. Writer 修订稿
- `draft_scope`：
- `self_check`：
- `known_risks`：
- `memory_writeback_needed`：

[修订后正文]

## 5. LanguageReviewer 结果
- `findings`：
- `blocking`：yes / no
- `suggested_fix`：
- `ai_tone_source`：
- `needs_full_rewrite`：yes / no
- `return_to`：
- `rewrite_scope`：
- `first_fix_priority`：
- `recheck_order`：

## 6. StyleDialogue 结果
- `findings`：
- `blocking`：yes / no
- `suggested_fix`：
- `voice_conflict`：
- `naming_conflict`：
- `return_to`：
- `rewrite_scope`：
- `first_fix_priority`：
- `recheck_order`：

## 7. ContinuityReviewer 结果
- `findings`：
- `blocking`：yes / no
- `suggested_fix`：
- `continuity_conflict`：
- `memory_files_affected`：
- `return_to`：
- `rewrite_scope`：
- `first_fix_priority`：
- `recheck_order`：

## 8. CausalityReviewer 结果
- `findings`：
- `blocking`：yes / no
- `suggested_fix`：
- `causality_gap`：
- `fact_judgment_consequence_clear`：yes / no
- `return_to`：
- `rewrite_scope`：
- `first_fix_priority`：
- `recheck_order`：

## 9. Reviewer 复核
- `full_chapter_read`：yes / no
- `blocking`：yes / no
- 主故障是否已修掉：
- 是否仍有水章风险：
- 是否仍有人设风险：
- 是否仍有时间线风险：
- 是否仍有重复风险：
- 是否仍有 AI 味风险：
- `human_read_verdict`：
- `repeat_window`：
- `upgrade_point`：
- `script_missed_issue`：
- `rewrite_handoff`：
- `final_release`：pass / revise
- `final_release` 表示总审放行结论
- 若 `final_release=revise`，交回给谁：
- 若 `final_release=revise`，先修哪一层：
- 若 `final_release=revise`，修完先复查什么：

## 10. 需要更新的记忆点
- `state.md`：
- `summaries/recent.md`：
- `timeline.md`：
- `foreshadowing.md`：
- `character_arcs.md`：
- `payoff_board.md`：
- 其他：
```

补充约束：

- `/修改` 先诊断，再决定小修还是重写
- 若只是语言发硬，优先小修；若已伤结构、人物、承诺，再扩大到重写
- `HookEmotion` 先处理情绪跳、钩子弱、爽点失焦，再进入正文修订
- 若修改会影响后续章节，必须显式写出影响面
- 若任一 reviewer `blocking=yes`，必须补齐回退四字段
- 通用 reviewer 分工、阻断条件、冲突裁决与串行回退，统一见 `references/agent-collaboration.md`
