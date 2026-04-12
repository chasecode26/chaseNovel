# 协作与复核最小协议

这份文档定义 `chaseNovel` 在长篇连载中的默认多 Agent 协作方式。

目标只有一个：
在不牺牲连续性和文风统一的前提下，把章节生产固定为
`规划 -> 写作 -> 并行复审 -> 总审裁决 -> 不过即回退`

## 1. 什么时候必须启用多 Agent

以下场景默认进入多 Agent 流程：

- `/写`
- `/继续`
- `/修改`
- 开篇前 `1-10` 章
- 涉及伏笔兑现、时间线、身份暴露、资源调度、关系升级的章节
- 已经出现 AI 味、重复推进、断点失手、角色声口漂移的稿子

以下场景可不拉满整套阵型：

- 轻量 brainstorming
- 只改标题、简介、单段摘句
- 用户明确只要草稿，不要复审

一句话判断：
只要这次产出会直接影响连载连续性，就不要只让 `Writer` 一把写完。

## 2. 默认阵型

### `Lead`

- 负责调度、文件锁、顺序裁决、回退决策
- 不直接产正文
- 不让两个 `Writer` 同时写同一章

### `Planner`

- 负责章卡
- 锁定 `time_anchor`、`location_anchor`、`present_characters`、`knowledge_boundary`
- 明确本章功能、结果变化、章尾钩子、`chapter_tier`、`target_word_count`
- 先回答“本章为何必须存在”

### `HookEmotion`

- 负责断点承接、情绪曲线、高潮前蓄压、高潮后余波、章尾钩子
- 不改主线目标

### `Writer`

- 只按章卡写正文
- 不擅改卷纲
- 不擅加重大设定
- 不跳过已知断点与既有后手

### `LanguageReviewer`

- 专抓 AI 味、提炼句、抽象判断、黑话简称、机械过渡

### `StyleDialogue`

- 专抓对白声口、角色区分、称谓、身份口气、对白是否只在搬信息

### `ContinuityReviewer`

- 专抓时间线、设定、伏笔、知情边界、资源状态、人物位置

### `CausalityReviewer`

- 专抓“事实 -> 判断 -> 后果”链
- 专查关键转折、人物决策、结果落地、敌我条件是否同时成立

### `Reviewer`

- 最终门禁
- 必须整章顺读后再拆检
- 拥有一票否决权
- 这里的 `Reviewer` 指总审角色，不等于并行 reviewers

## 3. 默认顺序

### 开书

`Planner -> Character -> Worldbuilder -> Reviewer`

### 写章 / 续写

`Planner -> HookEmotion -> Writer -> (LanguageReviewer || StyleDialogue || ContinuityReviewer || CausalityReviewer) -> Reviewer`

### 改章

`Reviewer -> Planner -> HookEmotion(如需要) -> Writer -> (LanguageReviewer || StyleDialogue || ContinuityReviewer || CausalityReviewer) -> Reviewer`

## 4. 文件与职责铁律

- 同一章同一时刻只允许一个 `Writer`
- reviewer 默认只审，不直接替 `Writer` 重写整章
- 命中阻断项后，不允许“先往下写，后面再修”
- `Reviewer` 不能因为脚本通过就放行
- 语言建议不能破坏既有设定、时间线和因果链

## 5. 每个角色至少交什么

### `Planner`

- `chapter_function`
- `result_change`
- `hook_type`
- `chapter_tier`
- `target_word_count`
- `anchors`

### `Writer`

- 正文草稿
- 自检结论
- 需要回写的 memory 项

### 其他 reviewer

- `findings`
- `blocking`
- `suggested_fix`

### `Reviewer`

- `blocking`
- `human_read_verdict`
- `repeat_window`
- `upgrade_point`
- `script_missed_issue`
- `rewrite_handoff`
- `final_release`

## 6. 什么算阻断

出现以下任一项，`blocking=yes`：

- 本章说不清为何必须存在
- 本章没有结果变化
- 时间线、设定、知情边界、资源状态冲突
- 关键转折没有前提，像作者硬推
- 对白故作含混，读者判不明真实作用
- 叙述只有判断，没有具体动作、依据、后果
- 与近 `3-5` 章重复同一种推进或钩子
- 关键信息靠黑话、简称、半截推理支撑
- 角色声口被压平
- 称谓、身份、官职、场合打架
- 脚本虽过，但人眼仍觉得像作者在提炼和讲道理

## 7. 冲突裁决顺序

当 reviewer 意见打架时，按以下优先级裁决：

1. `ContinuityReviewer` / `CausalityReviewer`
2. `Reviewer`
3. `HookEmotion`
4. `StyleDialogue` / `LanguageReviewer`

原则：

- 连续性和因果没过，不进入纯语言收尾
- 语言建议不能破坏设定和逻辑

## 8. 回退规则

### 退回给 `Writer`

- AI 味重
- 抽象判断太多
- 场景太薄
- 氛围过载但没推进

### 退回给 `Planner + Writer`

- 本章功能不成立
- 结果变化不足
- 关键转折缺前提
- 章尾钩子不改变下章行动

### 退回给 `Writer + StyleDialogue`

- 声口压平
- 对白搬信息
- 称谓与身份不稳

### 退回给 `Planner + Writer + CausalityReviewer`

- 军报、敌情、权谋、推理链不闭合
- 事实、判断、后果顺序失真

## 9. 无法真拉多 Agent 时

如果当前环境不能显式拉起多个子 agent，也不能省掉检查。

串行顺序如下：

1. `Planner`
2. `HookEmotion`
3. `Writer`
4. `StyleDialogue`
5. `LanguageReviewer`
6. `ContinuityReviewer`
7. `CausalityReviewer`
8. `Reviewer`

要求：

- 每个角色单独给结论
- 命中阻断项立刻回退
- 不准合成一句模糊总评后硬放行

## 10. 一句话总纲

协作不是多几个人一起写，而是把“谁先定、谁来写、谁抓硬伤、谁拍板回退”固定下来。
