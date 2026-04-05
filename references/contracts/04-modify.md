### `/修改`
输出：
- Reviewer 初检
- Planner 修复策略
- HookEmotion 结果
- Writer 修订稿
- StyleDialogue 结果
- LanguageReviewer 结果
- ContinuityReviewer 结果
- CausalityReviewer 结果
- Reviewer 复核

#### `/修改` 固定输出模板

```markdown
# 修章方案

## Agent 编排
- 默认顺序：`Reviewer -> Planner -> HookEmotion -> Writer -> StyleDialogue -> LanguageReviewer -> ContinuityReviewer -> CausalityReviewer -> Reviewer`

## 1. Reviewer 初检

### 1.1 问题诊断
- 本次问题类型：
- 最主要故障：
- 次级故障：
- 当前最影响追读的问题：

### 1.2 影响面判断
- 是否允许只改本章：是 / 否
- 会影响哪些人物状态：
- 会影响哪些伏笔 / 承诺：
- 会影响哪些后续章节：

### 1.3 必须保留项
- 必留事实：
- 必留结果：
- 必留伏笔：
- 必留人物关系：

## 2. Planner 修复策略
- 修法类型：压缩 / 重写 / 重排信息 / 补结果 / 补钩子 / 修动机 / 换反馈
- 优先修哪一层：
- 本章修改后必须成立什么：
- 本章绝不能再出现什么：
- 是否需要补读：`characters.md` / `timeline.md` / `foreshadowing.md` / `payoff_board.md`

### 2.1 修改前复审闸门
- 写前锚定包是否已补齐：是 / 否
- 允许改动的事实边界是否明确：是 / 否
- 最近 `3-5` 章的重复窗口是否已对照：是 / 否
- 旧伏笔 / 旧布局 / 资源状态是否已回查：是 / 否
- 若以上任一为否：先补齐，再改稿

## 3. HookEmotion 结果
- 是否存在情绪跳跃：
- 是否存在钩子失效：
- 爽点 / 压力该怎么重排：
- 本轮优先修哪一个情绪问题：

## 4. Writer 修订稿
[修订后正文]

## 5. StyleDialogue 结果
- 哪些句段最像 AI 在解释：
- 哪些对白需要重写口吻：
- 哪些旁白需要降硬度：
- 语言层是否建议只做小修：是 / 否

## 6. LanguageReviewer 结果
- 最重的 AI 味来源：
- 机械过渡是否压下去：
- 是否还有作者替人物总结：
- 语言层是否已可用：是 / 否

## 7. ContinuityReviewer 结果
- 是否仍有世界规则冲突：否 / 是（说明）
- 是否仍有时间线冲突：否 / 是（说明）
- 是否仍有伏笔 / 承诺失忆：否 / 是（说明）
- 是否仍有既有布置失效未解释：否 / 是（说明）

## 8. CausalityReviewer 结果
- 转折前提是否成立：是 / 否
- 人物决策是否站得住：是 / 否
- 结果是否仍有硬推感：否 / 是（说明）
- 后账是否接得住：是 / 否

## 9. Reviewer 复核
- 主故障是否已修掉：是 / 否
- 是否仍有水章风险：否 / 是（说明）
- 是否仍有人设风险：否 / 是（说明）
- 是否仍有时间线风险：否 / 是（说明）
- 是否仍有重复风险：否 / 是（说明）
- 是否仍有 AI 味风险：否 / 是（说明）
- 章尾钩子是否比原稿更有效：是 / 否
- 是否建议采用：是 / 否
- 若否，下一轮只修什么：

## 10. 需更新的记忆点
- `state.md`：
- `summaries/recent.md`：
- `timeline.md`：
- `foreshadowing.md`：
- `character_arcs.md`：
- `payoff_board.md`：
- 其他：
```

补充约束：

- `/修改` 先诊断，不要一上来整章重写
- 默认由 `Reviewer` 负责前后两次检查，不再依赖本地 hook
- `HookEmotion` 先处理情绪跳、钩子弱、爽点失焦，再进入正文重写
- `StyleDialogue` 只处理对白、口吻、旁白层，不改主线结论
- `LanguageReviewer` 单独负责压 AI 味和机械解释
- `ContinuityReviewer` 单独负责设定、时间线、伏笔、承诺和布置连续性
- `CausalityReviewer` 单独负责转折、决策和结果合理性
- 若只是语言发硬，优先小修；若已影响结构、人物或承诺，再扩大到重写
- 若修改会影响后续章节，必须显式写出影响面
