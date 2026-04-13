# 协作与复核最小协议

> 兼容层提示：新的主入口已迁到 `docs/core/write-workflow.md`。
> 本文件继续保留详细协作细则，但不再作为默认主入口。

这份文档只回答两件事：
- 什么时候单人直写
- 什么时候必须加复核

它不是“多 Agent 仪式说明书”，只保留最小可执行规则。

## 1. 先判断要不要协作

### 可单人完成
- 开书前的轻量 brainstorming
- 极短润色
- 只改标题、简介、单段措辞
- 用户明确只要草稿，不要复核

### 默认要加复核
- `/写`
- `/续写`
- `/修改`
- 开篇前 `1-10` 章
- 牵涉伏笔、时间线、承诺兑现、资源状态的章节
- 已经出现 AI 味、重复推进、断点没接住、人物口吻漂移的稿子

一句话判断：
**只要这次产出会直接影响连载连续性，就不要只靠 Writer 一把过。**

## 2. 最小角色集

### `Planner`
- 负责：定本章功能、结果变化、章尾钩子；锚定时间、地点、在场人物、知情边界、资源状态；判断与近 `3-5` 章是否重复
- 必交：本章章卡、`chapter_tier`、`target_word_count`、本章最小推进、结果变化

### `Writer`
- 负责：按已确认章卡起草正文，把规划落成可读场面
- 不负责：擅自改卷纲、擅自新增重大设定、擅自跳过断点承接

- 写前自检：先看 `language-governance.md`，确保没有作者提炼句、概括句、抽象判断句直接顶场面
- 写前自检：同一件事先按人物身份、性格、当下压力拆声口，不准把武将、文臣、老兵、主母写成同一种“利落成熟腔”
- 写前自检：称谓先对身份、官职、场合，不确定身份时先用稳妥叫法，不准乱叫 `公公`
- 交稿前自检：脚本只负责帮忙扫雷，不算最终过关；Writer 自己要通读一遍，确认句子像人会说的话，不像作者在提炼总结
- 起稿纪律：不准先写省力句、提炼句、抽象收口句占位，再指望“后面再修”
- 起稿纪律：默认先保质量，再保速度；不能为了快先写一个劣质骨架版正文
### `Reviewer`
- 负责：最终门禁、汇总 reviewer 结论、判断能否交稿
- 必查：本章删掉后后文是否仍成立；本章相比近 `3-5` 章升级点是否成立；是否需要回写记忆文件

- 必查：不能把“脚本通过”当成“可交稿”；必须做人眼通读，专门抓脚本没报出来的别扭句、错口吻、错称谓、假通俗
- 必查：只要还像作者在提炼、讲道理、概括局势，哪怕句子更短了、脚本也没报，照样打回
- 必查：只要关键人物声口被压成一个模子，或称谓和身份打架，默认按硬错误处理，不当小瑕疵放过
- 必查：先整章读完，再回头逐类挑刺；不准只盯命中词句，不准只看单句，必须结合上下文判断逻辑、语气、信息承接和场面作用
- 必查：只要发现逻辑不通、表达不严谨、词语重复、说话人口气不对、作者视角发声、术语省略，就默认 `blocking=yes`
- 必查：复核不是“指出问题就算完”；命中硬伤后必须明确退回给 `Writer` 或对应 reviewer 重写，直到人眼读感过关
## 3. 按问题加的 reviewer

- `StyleDialogue`：对白口吻、角色区分、旁白发硬、故作含混
- `LanguageReviewer`：AI 味、机械过渡、解释感、抽象判断不落地
- `ContinuityReviewer`：时间线、设定、伏笔、承诺、资源状态、知情边界
- `CausalityReviewer`：转折前提、人物决策、结果落地、后账承接
- `HookEmotion`：断点承接、情绪高点、爽点密度、章尾钩子
- `ResearchMaterial`：资料压缩、术语统一、现实材料转可写规则

默认搭配：
- `/写`：`HookEmotion + StyleDialogue + LanguageReviewer + Reviewer`
- `/续写`：`HookEmotion + ContinuityReviewer + LanguageReviewer + Reviewer`
- `/修改`：`LanguageReviewer + ContinuityReviewer + CausalityReviewer + Reviewer`
- 复杂题材：再补 `ResearchMaterial`

## 4. 推荐顺序

- `/写`：`Planner -> HookEmotion -> Writer -> reviewer 复核 -> Reviewer`
- `/续写`：`Planner -> HookEmotion -> Writer -> reviewer 复核 -> Reviewer`
  额外要求：先接上上一章断点，再决定要不要开新场面
- `/修改`：`Reviewer 初检 -> Planner -> HookEmotion（如需要）-> Writer -> reviewer 复核 -> Reviewer`
  额外要求：先诊断故障，再决定是小修还是重写

## 5. 每个 reviewer 至少交什么

除 `Planner`、`Writer` 外，其余 reviewer 默认至少交：
- `findings`
- `blocking`
- `suggested_fix`

结构类 reviewer 可额外带：
- `chapter_function`
- `result_type`
- `hook_type`

`Reviewer` 额外必须交：
- `repeat_window`
- `upgrade_point`
- `word_count_verdict`
- `human_read_verdict`
- `script_missed_issue`
- `full_chapter_read`
- `rewrite_handoff`

默认 `rewrite_handoff` 可直接套：

- `templates/rewrite-handoff.md`

## 6. 什么算阻断

出现以下任一项，`blocking` 默认记为 `yes`：
- 断点没接住，却硬开新戏
- 本章没有结果变化
- 时间线、设定、知情边界冲突
- 关键转折没有前提，像作者硬推
- 对白故作含混，读者判不明真实作用
- 叙述只给抽象判断，不落到具体事和具体后果
- 与近 `3-5` 章重复同一种推进或钩子
- 只是补解释、补背景，删掉也不影响后文

- 命中作者提炼句黑名单，或仍在用“真正的问题是 / 关键在于 / 像极了”这类句子替场面下结论
- 角色声口被压平，同一类压力下谁都像一个人在说话
- 称谓和身份、官职、场合打架，属于人眼一读就出戏的硬错误
- 脚本虽通过，但 Reviewer 人眼通读仍觉得不像人话、像作者提炼总结
- Writer 起稿阶段已经在用省力句、抽象句、占位句糊段落
- 术语、判断、军报、推理只写半截，读者需要自己补关键逻辑
- 表达不严谨，前后说法打架，或一句话落不稳真实指向
- 关键词、句式、判断重复堆叠，读起来像在原地复读
- 说话人口气不符合身份、性格、场合和当前压力
- 旁白替人物总结，作者站到台前替读者下结论
## 7. 冲突裁决顺序

当 reviewer 意见打架时，按这个顺序裁决：
1. `ContinuityReviewer` / `CausalityReviewer`
2. `Reviewer`
3. `HookEmotion`
4. `StyleDialogue` / `LanguageReviewer`

原则：
- 连续性和因果没过，不进入纯语言收尾
- 语言建议不能破坏既有设定、时间线和因果

## 8. 串行回退方案

如果当前环境不能真的拉起多个子 agent，也不能省掉检查。

串行顺序：
1. `Planner`
2. `HookEmotion`（若本章需要）
3. `Writer`
4. `StyleDialogue`
5. `LanguageReviewer`
6. `ContinuityReviewer`
7. `CausalityReviewer`
8. `Reviewer`

要求：
- 每个角色单独给结论，不要合成一段模糊总评
- 命中阻断项就回退，不继续硬收尾

- 脚本结果只能当辅助证据，不能替代 `LanguageReviewer` 和 `Reviewer` 的人眼判断
- `Reviewer` 必须先完整读一遍，再按“逻辑 / 严谨 / 重复 / 声口 / 作者发声 / 术语省略”六类回头拆
- `Reviewer` 一旦判定 `blocking=yes`，必须明确写出交回给谁重写、重写后优先复查什么
## 9. 什么时候不用拉满

- 只做句子润色：`StyleDialogue -> LanguageReviewer`
- 只补断点承接：`Planner -> HookEmotion -> Writer -> Reviewer`
- 只查连续性：`Planner -> ContinuityReviewer -> Reviewer`

但只要涉及整章交付，`Reviewer` 不建议省。

## 10. 一句话总纲

**协作不是多几个人设，而是把“谁先定、谁来写、谁挑硬伤、谁拍板回退”固定下来。**
