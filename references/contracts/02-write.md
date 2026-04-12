### `/写`

输出：

- `Planner` 结果
- `HookEmotion` 结果
- 章节规划预审
- `Writer` 成稿
- `LanguageReviewer` 结果
- `StyleDialogue` 结果
- `ContinuityReviewer` 结果
- `CausalityReviewer` 结果
- `Reviewer` 结论
- 需要更新的记忆点

#### `/写` 固定输出模板

```markdown
# 第 X 章写作方案

## Agent 编排
- 默认顺序：`Planner -> HookEmotion -> Writer -> (LanguageReviewer || StyleDialogue || ContinuityReviewer || CausalityReviewer) -> Reviewer`

## 1. Planner 结果

### 1.1 本章章卡
- `chapter_function`：
- `result_change`：
- `hook_type`：
- `chapter_tier`：
- `target_word_count`：
- `time_anchor`：
- `location_anchor`：
- `present_characters`：
- `scene_focal_character`：
- `knowledge_boundary`：
- `resource_state`：
- `open_threads`：
- `forbidden_inventions`：

### 1.2 规划说明
- 本章为什么必须存在：
- 本章最不能丢的推进：
- 本章最需要控制的风险：
- 本章与近 `3-5` 章相比，变化在哪里：

## 2. HookEmotion 结果
- `entry_pressure`：
- `midpoint_pressure`：
- `peak_moment`：
- `aftershock`：
- `hook_type`：
- `hook_line_or_direction`：
- `blocking`：yes / no
- `suggested_fix`：

## 2.1 章节规划预审
- `planning_verdict`：pass / revise
- 本章功能是否重复近 `3-5` 章：
- 本章结果变化是否成立：
- 本章钩子是否改变下章行动：
- 关键转折前提是否成立：
- 既有布置 / 资源 / 旧伏笔是否已确认：

## 3. Writer 成稿
- `draft_scope`：
- `self_check`：
- `known_risks`：
- `memory_writeback_needed`：

[正文]

## 4. LanguageReviewer 结果
- `findings`：
- `blocking`：yes / no
- `suggested_fix`：
- `ai_tone_source`：
- `needs_full_rewrite`：yes / no
- `return_to`：
- `rewrite_scope`：
- `first_fix_priority`：
- `recheck_order`：

## 5. StyleDialogue 结果
- `findings`：
- `blocking`：yes / no
- `suggested_fix`：
- `voice_conflict`：
- `naming_conflict`：
- `return_to`：
- `rewrite_scope`：
- `first_fix_priority`：
- `recheck_order`：

## 6. ContinuityReviewer 结果
- `findings`：
- `blocking`：yes / no
- `suggested_fix`：
- `continuity_conflict`：
- `memory_files_affected`：
- `return_to`：
- `rewrite_scope`：
- `first_fix_priority`：
- `recheck_order`：

## 7. CausalityReviewer 结果
- `findings`：
- `blocking`：yes / no
- `suggested_fix`：
- `causality_gap`：
- `fact_judgment_consequence_clear`：yes / no
- `return_to`：
- `rewrite_scope`：
- `first_fix_priority`：
- `recheck_order`：

## 8. Reviewer 结论
- `full_chapter_read`：yes / no
- `blocking`：yes / no
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

## 9. 需要更新的记忆点
- `state.md`：
- `summaries/recent.md`：
- `timeline.md`：
- `foreshadowing.md`：
- `character_arcs.md`：
- `payoff_board.md`：
- 其他：
```

补充约束：

- `/写` 默认先过规划预审，未过不准进正文
- 若任一 reviewer `blocking=yes`，必须补齐 `return_to / rewrite_scope / first_fix_priority / recheck_order`
- `Writer` 不准用省力句、提炼句、抽象收口句占位
- `Reviewer` 没有 `full_chapter_read: yes` 不得放行
- 通用 reviewer 分工、阻断条件、冲突裁决与串行回退，统一见 `references/agent-collaboration.md`
