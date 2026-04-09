### `/修改`
输出：
- Reviewer 初检
- Planner 修复策略
- HookEmotion 结果
- Writer 修订稿
- StructureReviewer 结果
- RhythmReviewer 结果
- StyleDialogue 结果
- LanguageReviewer 结果
- ContinuityReviewer 结果
- CausalityReviewer 结果
- Reviewer 复核

#### `/修改` 固定输出模板

```markdown
# 修章方案

## Agent 编排
- 默认顺序：`Reviewer -> Planner -> HookEmotion -> Writer -> StructureReviewer -> RhythmReviewer -> StyleDialogue -> LanguageReviewer -> ContinuityReviewer -> CausalityReviewer -> Reviewer`

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
- `chapter_tier` 与 `target_word_count` 是否已重新确认：是 / 否
- 若以上任一为否：先补齐，再改稿

## 3. HookEmotion 结果
- 是否存在情绪跳跃：
- 是否存在钩子失效：
- 爽点 / 压力该怎么重排：
- 本轮优先修哪一个情绪问题：

## 4. Writer 修订稿
[修订后正文]

## 5. StructureReviewer 结果
- `chapter_function`：
- `conflict_type`：
- `result_type`：
- `hook_type`：
- `chapter_tier`：
- `target_word_count`：
- `findings`：
- `blocking`：yes / no
- `suggested_fix`：

## 5.1 RhythmReviewer 结果
- `chapter_function`：
- `conflict_type`：
- `result_type`：
- `hook_type`：
- `chapter_tier`：
- `target_word_count`：
- `findings`：
- `blocking`：yes / no
- `suggested_fix`：

## 6. StyleDialogue 结果
- 哪些句段最像 AI 在解释：
- 哪些对白需要重写口吻：
- 哪些台词的问题不只是发硬，而是已经不像这个人会说的话：
- 哪些台词故作含混，读者难以判明真实作用：
- 哪些旁白需要降硬度：
- 哪些地方该改得更清晰可判读，哪些地方应保留原有题材余味：
- 语言层是否建议只做小修：是 / 否

## 7. LanguageReviewer 结果
- 是否已整章通读后再拆句审：是 / 否
- 通篇读完最重的 1-3 个问题：
- 最重的 AI 味来源：
- 机械过渡是否压下去：
- 是否还有作者替人物总结：
- 哪些“那个人 / 那件事 / 某种真相”式写法还没改掉：
- 哪些叙述只给抽象判断，没有落到具体事和具体后果：
- 哪些句子还在概括局势、提炼判断、讲道理，没有改成场面和实际后果：
- 哪些敌情、军报、推理句还在用“主口 / 主杀招 / 有鬼”这类黑话顶关键信息：
- 哪些地方逻辑不通或因果接不上：
- 哪些表达不够严谨，读者读完仍拿不准真实指向：
- 哪些关键词、判断、句式在反复重复：
- 哪些台词或口气不符合说话者身份、性格、场合和压力：
- 哪些地方作者站到台前替人物、替局势、替读者发声：
- 哪些地方写得太省，术语、关系、判断、后果需要读者自己补：
- 哪些称谓和人物身份、官职、场合不一致：
- 哪些留白保留得合理，哪些留白只是装深沉：
- 语言层是否已可用：是 / 否

## 8. ContinuityReviewer 结果
- 是否仍有世界规则冲突：否 / 是（说明）
- 是否仍有时间线冲突：否 / 是（说明）
- 是否仍有伏笔 / 承诺失忆：否 / 是（说明）
- 是否仍有既有布置失效未解释：否 / 是（说明）

## 9. CausalityReviewer 结果
- 转折前提是否成立：是 / 否
- 人物决策是否站得住：是 / 否
- 结果是否仍有硬推感：否 / 是（说明）
- 后账是否接得住：是 / 否

## 10. Reviewer 复核
- 是否已完整通篇复核：是 / 否
- 主故障是否已修掉：是 / 否
- 是否仍有水章风险：否 / 是（说明）
- 是否仍有人设风险：否 / 是（说明）
- 是否仍有时间线风险：否 / 是（说明）
- 是否仍有重复风险：否 / 是（说明）
- 是否仍有 AI 味风险：否 / 是（说明）
- `word_count_verdict`：
- 章尾钩子是否比原稿更有效：是 / 否
- 是否通过人眼读感复核：是 / 否
- 是否存在脚本未报、但人读仍明显别扭的问题：否 / 是（说明）
- 是否建议采用：是 / 否
- 若否，必须交回给谁重写：`Writer / StyleDialogue / ContinuityReviewer / CausalityReviewer`
- 若否，下一轮只修什么：

## 11. 需更新的记忆点
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
- `HookEmotion` 先处理情绪跳、钩子弱、爽点失焦，再进入正文重写
- 若只是语言发硬，优先小修；若已影响结构、人物或承诺，再扩大到重写
- 若修改会影响后续章节，必须显式写出影响面
- 通用 reviewer 分工、阻断条件、冲突裁决与串行回退，统一见 `references/agent-collaboration.md`
