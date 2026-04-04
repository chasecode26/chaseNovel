### `/续写`
输出：
- Planner 结果
- HookEmotion 结果
- Writer 续写
- StyleDialogue 结果
- LanguageReviewer 结果
- Reviewer 结论

#### `/续写` 固定输出模板

```markdown
# 续写方案

## Agent 编排
- 默认顺序：`Planner -> HookEmotion -> Writer -> StyleDialogue -> LanguageReviewer -> Reviewer`

## 1. Planner 结果

### 1.1 恢复结论
- 当前位置：
- 当前卷 / 阶段：
- 当前主冲突：
- 最近关键结果：
- 本次续写最该接住什么：

### 1.2 当前状态摘要
- 主角当前状态：
- 关键配角状态：
- 当前有效布置：
- 当前承诺兑现压力：
- 当前伏笔触发压力：

### 1.3 下一章目标
- 本章功能：
- 本章最小推进：
- 本章结果变化：
- 本章章尾钩子方向：

## 2. HookEmotion 结果
- 本章情绪延续点：
- 断点钩子是否被接住：
- 本章高点应该落在哪：
- 本章章尾钩子建议：
- 情绪 / 节奏风险提示：

## 3. Writer 续写
[正文]

## 4. StyleDialogue 结果
- 是否延续既有口吻：
- 哪些段落容易显得像补作业：
- 哪些对白需要拉开角色区分：
- 语言层优先修订项：

## 5. LanguageReviewer 结果
- 哪些句段最像 AI 在补背景：
- 是否有过量书面过渡：
- 哪些段落解释重、动作轻：
- 去 AI 味优先修订项：

## 6. Reviewer 结论
- 是否接住了断点：是 / 否
- 是否延续既有口吻：是 / 否
- 是否存在状态错位：否 / 是（说明）
- 是否存在时间线风险：否 / 是（说明）
- 是否存在重复推进：否 / 是（说明）
- 是否存在 AI 味风险：否 / 是（说明）
- 是否建议直接进入下一章：是 / 否
- 若否，优先回修项：

## 7. 需更新的记忆点
- `state.md`：
- `summaries/recent.md`：
- `timeline.md`：
- `foreshadowing.md`：
- `character_arcs.md`：
- `payoff_board.md`：
- 其他：
```

补充约束：

- `/续写` 默认先读 `plan.md`、`state.md`，必要时补 `findings.md` 与 `summaries/recent.md`
- 若断点前存在强钩子，本章必须先接钩子，不要直接跳去新场面
- 先由 `HookEmotion` 判断断点情绪和钩子是否续上，再交给 `Writer`
- `StyleDialogue` 负责口吻延续，`LanguageReviewer` 负责压 AI 味和补作业感
- 默认由 `Reviewer` 执行续写后的门禁与自检
