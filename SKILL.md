---
name: chaseNovel
description: 当用户要策划、起稿、续写、改写或管理中文网文长篇连载，并且关心章节节奏、章尾钩子、伏笔回收、设定连续性、角色推进与追读留存时使用。
---

# chaseNovel

面向中文网文长篇连载的写作技能。

它的核心不是“随手写一章”，而是两条主链：

- 开书
- 写作

一切规则、模板、脚本、复核和资产，都应服务这两条主链。

## 核心原则

1. 连载质量优先于单章漂亮。
2. 文件化记忆优先于临时会话记忆。
3. 写章先想“这章让读者经历什么”，再想“这章交代什么”。
4. 默认现代通俗白话，但不等于统一口水化。
5. 角色声口必须前置锁定，不准写完后才发现全员一个作者腔。
6. 伏笔、时间线、关系、承诺兑现必须能持续治理。
7. 题材资产按需加载，不能反客为主。
8. 对白必须答上问题，不能只靠冷话、狠话、断句顶过去。
9. 军政 / 权谋 / 敌情判断必须按“事实 -> 判断 -> 后果”写。
10. 命令发出后，1-3 句内必须跟上谁去做、先做什么、慢一步会怎样。
11. 一段最多只留一刀提炼；能靠场面让读者自己看懂，就不要旁白替读者做阅读理解。
12. `quality / anti-AI / style` 是校稿辅链，不是正文生成主链。

## 快速入口

- CLI 快速上手：`docs/core/cli-quickstart.md`
- 开书：`docs/core/open-book.md`
- 写章 / 续写：`docs/core/write-workflow.md`
- 改章 / 诊断：`docs/core/revise-diagnostics.md`
- 文风治理：`docs/core/style-governance.md`
- 状态 / 健康：`docs/core/status-workflow.md`
- 题材资产：`docs/assets/genre-index.md`

## 任务路由

| 用户请求 | 任务类型 | 最小路径 |
| --- | --- | --- |
| 帮我开一本新书 | 开书 | 题材定位 -> 卖点 -> 主线目标 -> 黄金三章 -> 卷纲/阶段目标 |
| 写第 X 章 / 继续写 | 写作 | 读记忆 -> 本章戏剧卡 -> 角色口条卡 -> 导演单 -> 起稿 -> 校稿 |
| 改这一章 | 改写 | 识别保留项 -> 找问题类型 -> 重写/压缩/补冲突/补钩子 |
| 人设崩了 / 剧情重复了 | 诊断 | 看阶段目标、人物、时间线、伏笔、重复推进 |
| 看看写到哪了 | 状态 | 汇总当前卷、当前弧、当前阻塞、下章目标 |

## 默认流程

### 开书

`Planner -> Character -> Worldbuilder -> Reviewer`

### 写作

`Memory -> Chapter Dramatic Card -> Character Voice Diff -> Writer Director Prompt -> Writer -> Reviewers -> Writer 修正`

### 两条链必须分开

#### 创作主链

- `chapter-dramatic-card.md`
- `character-voice-diff.md`
- `voice.md`
- `style.md`
- `writer-director-prompt.md`

创作主链只负责一件事：写出能读、能追、能记住的正文。

#### 校稿辅链

- Continuity
- Causality
- Language / Anti-AI
- Style / Dialogue

校稿辅链只负责指出问题，不负责替 Writer 决定句子怎么写。

## 写作硬校验

- 对白里一旦有人发问，下一轮必须答上。
- 术语第一次出现，要在同句或下一句解释清楚。
- 权谋戏优先写动作、座次、视线、军令、账册、后果，不先写“这很狠”。
- 任何一句删掉后只剩“味道”而不损失信息，默认删。
- 短答不等于有压迫感；如果读者还要补逻辑，默认重写。
- 一段最多只留一刀提炼；不能每推进一步都补一句作者总结。
- 主角被刺痛时，要落到一个极小但真实的生理反应，不能只写“想明白了”。
- 章尾要开下一步的门，不要做命运总结。

## 写章主输入

写章时默认只优先消化以下输入，不把全仓文档一股脑塞进正文生成：

1. `00_memory/state.md`
2. `00_memory/timeline.md`
3. `templates/core/chapter-dramatic-card.md`
4. `templates/core/character-voice-diff.md`
5. `templates/core/voice.md`
6. `templates/core/style.md`
7. 少量题材资产 / 风格样本

## 关键模板

- 长线计划：`templates/core/plan.md`
- 本章戏剧卡：`templates/core/chapter-dramatic-card.md`
- 导演单：`templates/core/writer-director-prompt.md`
- 单书声音：`templates/core/voice.md`
- 风格锚点：`templates/core/style.md`
- 风格护栏：`templates/core/style-guardrails.md`
- 角色说话差分：`templates/core/character-voice-diff.md`

## 不适用场景

- 只想写一句文案
- 只想润色单句，不关心长线连续性
- 只做文学评论，不推进创作
- 明确不要项目记忆、不要质量门禁、不要连载约束
