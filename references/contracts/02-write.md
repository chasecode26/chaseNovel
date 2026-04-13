### `/写`
输出：
- Planner 结果
- HookEmotion 结果
- 章节规划预审
- Writer 成稿
- StructureReviewer 结果
- RhythmReviewer 结果
- StyleDialogue 结果
- LanguageReviewer 结果
- ContinuityReviewer 结果
- CausalityReviewer 结果
- Reviewer 结论
- 需更新的记忆点

#### `/写` 固定输出模板

```markdown
# 第 X 章写作方案

## Agent 编排
- 默认顺序：`Planner -> HookEmotion -> Writer -> StructureReviewer -> RhythmReviewer -> StyleDialogue -> LanguageReviewer -> ContinuityReviewer -> CausalityReviewer -> Reviewer`

## 1. Planner 结果

### 1.1 本章章卡
- 本章时间：
- 距上章过去多久：
- 本章地点：
- `chapter_tier`：
- `target_word_count`：
- 本章功能：
- 本章目标：
- 本章冲突：
- 本章结果变化：
- 本章结果类型：
- 为什么这次不重复上一章结果：
- 本章爽点 / 情绪点：
- 本章应触发的既有布置 / 旧伏笔：
- 若未触发，失效或延后原因：
- 本章主要推进角色：
- 本章关系刷新点：
- 本章承诺推进 / 延后说明：
- 章尾钩子类型：
- 章尾钩子自动推荐依据：
- 为什么这一钩子适合本章：
- 本章章尾钩子：

### 1.2 规划说明
- 本章最不能丢的推进：
- 本章最需要控制的风险：
- 本章优先服务哪条长期线：

## 2. HookEmotion 结果
- 本章情绪主曲线：
- 高点前蓄压是否足够：
- 高点后余波怎么留：
- 本章钩子是否能决定下一章行动：
- 情绪 / 爽点风险提示：

## 2.1 章节规划预审
- 是否通过：pass / revise
- 本章功能是否与最近 `3-5` 章重复：否 / 是（说明）
- 本章结果是否有升级：是 / 否（说明）
- 本章钩子是否会改变下一章行动：是 / 否（说明）
- 本章关键转折前提是否成立：是 / 否（说明）
- 既有布局 / 资源 / 旧伏笔是否已确认：是 / 否（说明）

## 3. Writer 成稿
[正文]

写前补充硬要求：
- 不准先写省力句、提炼句、抽象收口句占位
- 不准靠“后面再修”放过第一轮正文质量
- 默认先保质量，再保速度

## 4. StructureReviewer 结果
- `chapter_function`：
- `conflict_type`：
- `result_type`：
- `hook_type`：
- `chapter_tier`：
- `target_word_count`：
- `findings`：
- `blocking`：yes / no
- `suggested_fix`：

## 4.1 RhythmReviewer 结果
- `chapter_function`：
- `conflict_type`：
- `result_type`：
- `hook_type`：
- `chapter_tier`：
- `target_word_count`：
- `findings`：
- `blocking`：yes / no
- `suggested_fix`：

## 5. StyleDialogue 结果
- 哪些段落 AI 味最重：
- 哪些对白口吻撞车：
- 哪些台词虽然更清楚，但已经不像这个人物会说的话：
- 哪些关键人物需要按身份 / 性格 / 压力状态重写声口：
- 哪些台词故作含混，读者难以判明真实作用：
- 哪些旁白过硬或解释味过重：
- 哪些地方该写得更清晰可判读，哪些地方可以保留题材余味：
- 语言层优先修订项：

## 6. LanguageReviewer 结果
- 是否已整章通读后再拆句审：是 / 否
- 通篇读完最重的 1-3 个问题：
- 哪些句段最像 AI 在解释：
- 机械过渡词是否过多：
- 哪些段落只有结论、没有动作承载：
- 哪些地方把“谁在做事 / 为什么做 / 结果变了什么”说清楚了，哪些地方还没说清：
- 哪些叙述只给抽象判断，没有落到具体事和具体后果：
- 哪些句子还在概括局势、提炼判断、讲道理，没有落到场面和实际后果：
- 哪些敌情、军报、推理句只剩“主口 / 主杀招 / 有鬼”这类黑话，没有把判断结论说透：
- 哪些地方逻辑不通或因果接不上：
- 哪些表达不够严谨，读者读完仍拿不准真实指向：
- 哪些关键词、判断、句式在反复重复：
- 哪些台词或口气不符合说话者身份、性格、场合和压力：
- 哪些地方作者站到台前替人物、替局势、替读者发声：
- 哪些地方写得太省，术语、关系、判断、后果需要读者自己补：
- 哪些称谓和人物身份、官职、场合不一致：
- 哪些留白属于题材必要留白，哪些只是故意吊着不说：
- 去 AI 味优先修订项：

## 6.1 ContinuityReviewer 结果
- `chapter_function`：
- `conflict_type`：
- `result_type`：
- `hook_type`：
- `findings`：
- `blocking`：yes / no
- `suggested_fix`：

## 6.2 CausalityReviewer 结果
- `chapter_function`：
- `conflict_type`：
- `result_type`：
- `hook_type`：
- `findings`：
- `blocking`：yes / no
- `suggested_fix`：

## 7. Reviewer 结论
- 是否已完整通篇复核：是 / 否
- 是否有明确推进：是 / 否
- 是否有结果变化：是 / 否
- 是否推进角色或关系：是 / 否
- 是否符合当前平台/子风格要求：是 / 否
- 是否存在时间线冲突：否 / 是（说明）
- 是否存在“应触发的布置未触发”问题：否 / 是（说明）
- 是否存在水章风险：
- 是否存在重复风险：
- 是否存在中盘疲劳风险：
- 是否存在 AI 味风险：
- 是否存在情绪跳跃风险：
- `word_count_verdict`：
- `repeat_window`：
- `upgrade_point`：
- 是否通过人眼读感复核：是 / 否
- 是否存在脚本未报、但人读仍明显别扭的问题：否 / 是（说明）
- 是否建议直接采用本稿：是 / 否
- 若否，必须交回给谁重写：`Writer / StyleDialogue / ContinuityReviewer / CausalityReviewer`
- 若否，优先回修项：

## 8. 需更新的记忆点
- `state.md`：
- `summaries/recent.md`：
- `timeline.md`：
- `foreshadowing.md`：
- `character_arcs.md`：
- `payoff_board.md`：
- 其他：
```

补充约束：

- `/写` 前若用户没有明确指定章尾钩子，先对照 `templates/launch/chapter-outcome-kit.md`
- `章尾钩子类型` 必须落到以下之一：`结果未揭晓型 / 危机压顶型 / 选择逼近型 / 信息反转型 / 关系突变型 / 资源争夺型 / 欲望升级型`
- `本章结果类型` 建议先对照 `templates/launch/chapter-outcome-kit.md`
- `本章结果类型` 至少落到以下之一：`小胜型 / 翻盘型 / 被打断型 / 失手受损型 / 资源到手型 / 赢局面丢关系型 / 保命失机型`
- `为什么这次不重复上一章结果` 必须回答：和近 1-3 章相比，本章换了什么反馈
- `章尾钩子自动推荐依据` 至少写清 2 项：`本章功能 / 当前压力源 / 题材惯性`
- `为什么这一钩子适合本章` 必须回答：它会如何改变下一章行动，不能只写“更抓人”
- 若章尾钩子与本章功能无关，或近 3 章重复同类钩子，默认记为重复风险
- 通用 reviewer 分工、阻断条件、冲突裁决与串行回退，统一见 `docs/core/write-workflow.md`
