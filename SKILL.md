---
name: chaseNovel
description: 当用户要策划、起稿、续写、改写或管理中文网文平台连载，并且关注章节节奏、章尾钩子、伏笔回收、设定连续性、角色推进与追读留存时使用。
---

# 中文网文连载工作台

面向中文网文长篇连载的写作技能。

这不是“随手写一章”的轻提示词，而是一套围绕：

- 连载推进
- 项目记忆
- 章节功能
- 伏笔与回收
- 文风治理
- 质量闸门

建立的工作流。

## 快速入口

- 开书：先看“核心原则”“任务路由”“资源导航”，再按需读 [craft-and-platform.md](/D:/git/chaseNovel/references/craft-and-platform.md)
- 写章 / 续写：先看“写前锚定包”“默认流程”“连载门槛”，再按需读 [execution_workflow.md](/D:/git/chaseNovel/references/execution_workflow.md)
- 改章：先看“任务路由”“默认流程”“文风治理入口”，再按需读 [revision-and-diagnostics.md](/D:/git/chaseNovel/references/revision-and-diagnostics.md)
- 项目体检：优先跑 `chase doctor --project <dir>`；要做整套干跑检查，跑 `chase check --project <dir> [--chapter <n>]`

默认不要从头读完整份 `SKILL.md`。先命中任务入口，再按需下钻。

## 核心原则

1. 连载优先于单章漂亮。
2. 文件化记忆优先于当前会话记忆。
3. 先保章节功能，再修语言。
4. 默认清晰可判读，不默认口水化。
5. 默认第三人称限知，不乱跳视角。
6. 对白要承担真实功能，不只搬信息。
7. 只有悬疑等题材关键点才允许局部留白。
8. 默认不把所有题材压成统一番茄腔；只有平台或题材明确要求时才启用番茄向快反馈覆盖。
9. 规划不过，不进正文；硬红线命中，先返工。

## 适用场景

- 开一本中文网文平台连载
- 根据 `plan.md`、`state.md`、人物表、时间线继续写后续章节
- 修复剧情跑偏、人设失真、章节太水、伏笔遗忘、节奏拖沓、重复推进
- 规划黄金三章、卷纲、阶段目标、章尾钩子
- 做断更恢复、状态查看、批量推进、批量体检

## 不适用场景

- 只想写一句文案或一段灵感
- 只做单句润色，不关心长线设定
- 只做文学评论，不推进创作
- 明确不要项目记忆、不要质量门槛、不要连载约束

## 任务路由

任务路由回答的是“这是什么任务，最小执行路径是什么”，不是“要提示哪个 agent 名字”。

| 用户请求 | 任务类型 | 最小执行路径 |
| --- | --- | --- |
| 帮我开一本新书 | 立项开书 | 题材定位 -> 卖点/抓手 -> 主线目标 -> 角色结构 -> 卷纲/阶段目标 |
| 给我世界观 / 人设 / 大纲 | 设定规划 | 明确题材与受众 -> 建立核心冲突 -> 输出可执行设定与阶段推进 |
| 写第 X 章 / 继续写 | 单章推进 | 读取 `plan.md` + `state.md` -> 必要时补读相关记忆 -> 明确本章功能 -> 起草 -> 闸门 |
| 续写断更内容 | 状态恢复 | 读取 `plan.md` + `state.md` + `findings.md` + 最近摘要 -> 输出恢复结论 -> 再写 |
| 这章太水了 / 改一下 | 改写修复 | 识别保留项 -> 诊断问题类型 -> 选重写 / 压缩 / 补钩子 / 补冲突 |
| 人设崩了 / 剧情重复了 | 连载校准 | 扫描人物、摘要、伏笔、时间线 -> 找冲突点 -> 修正后续推进策略 |
| 看看现在写到哪了 | 状态查看 | 汇总当前卷、阶段、主冲突、有效布置、下章目标 |
| 批量推进几章 | 连载推进 | 先确认阶段目标与边界 -> 分章卡 -> 逐章执行门槛 |
| 帮我回收伏笔 | 伏笔管理 | 读取 `foreshadowing.md` + 最近摘要 -> 判断回收窗口 -> 设计兑现方式 |
| 改第 X 章但别动主线 | 定点修章 | 限定影响面 -> 仅修本章和必要记忆文件 -> 标记受影响后续章节 |

## 默认流程

### 开书

`Planner -> Character -> Worldbuilder -> Reviewer`

### 写章 / 续写

`Planner -> HookEmotion -> Writer -> Reviewers -> Writer/Planner 修正 -> Reviewer`

默认 `Reviewers` 至少包括：

- `StyleDialogue`
- `LanguageReviewer`
- `ContinuityReviewer`
- `CausalityReviewer`

如果环境不方便显式拉起子 agent，就按同等检查项串行执行。

### 改章

`Reviewer -> Planner -> Writer -> Reviewers -> Writer 修正 -> Reviewer`

## 写前锚定包

写章、续写、改章前，先锚定这些内容：

- `time_anchor`：当前绝对/相对时间，与上章间隔
- `location_anchor`：本章主场景与人物移动边界
- `present_characters`：在场、旁听、会被提及的人
- `scene_focal_character`：本场景默认跟随谁
- `knowledge_boundary`：谁知道 / 不知道 / 误以为
- `resource_state`：钱、粮、地、水、工具、人手、伤病、债务等本章会动到的资源
- `open_threads`：本章允许触碰的伏笔、承诺、关系张力、后账
- `forbidden_inventions`：本章不允许凭空新增的设定、结果、情报

缺任一关键项时，先补记忆文件，再进正文。

## 连载门槛

- 章节必须有功能
- 章节必须有结果变化、压力变化或关系变化
- 钩子必须具体，不靠空泛断尾
- 不能重复上一章同一类推进
- 不能靠作者总结代替场面
- 不能靠对白搬运信息
- 不能新增无依据设定
- 不能把应兑现的布置长期拖欠成水文

## 文风治理入口

当前文风治理重点抓这些问题：

- 作者替角色下结论
- 抽象氛围词堆叠
- 提纲扩写感
- 对白信息搬运感
- 多角色同声
- 书级 voice 漂移
- 故意写虚、硬装悬念
- 战争文术语黑话、绕弯判断、问答没对位

对应入口：

- [style-runtime-core.md](/D:/git/chaseNovel/references/style-runtime-core.md)
- [language-governance.md](/D:/git/chaseNovel/references/language-governance.md)
- [language-anti-ai-review.md](/D:/git/chaseNovel/templates/language-anti-ai-review.md)
- [character-voice-diff.md](/D:/git/chaseNovel/templates/character-voice-diff.md)
- [language_audit.py](/D:/git/chaseNovel/scripts/language_audit.py)

## 资源导航

只保留最常用的入口。更细的题材资料、子风格和专题规则都下沉到 `references/` 与 `templates/`。

### 总入口

- [execution_workflow.md](/D:/git/chaseNovel/references/execution_workflow.md)
  写前准备、写中纪律、写后回填、章节门槛、阶段复盘
- [output-contracts.md](/D:/git/chaseNovel/references/output-contracts.md)
  `/一键开书`、`/写`、`/继续`、`/修改` 的固定输出骨架
- [agent-collaboration.md](/D:/git/chaseNovel/references/agent-collaboration.md)
  什么时候单人直写、什么时候拉复核、拉哪些 reviewer
- [revision-and-diagnostics.md](/D:/git/chaseNovel/references/revision-and-diagnostics.md)
  水章、改章、重复推进、人设失真、承诺拖欠的诊断与修法
- [craft-and-platform.md](/D:/git/chaseNovel/references/craft-and-platform.md)
  开书、黄金三章、题材节奏、平台策略、章尾钩子

### 文风与对白

- [style-runtime-core.md](/D:/git/chaseNovel/references/style-runtime-core.md)
- [language-governance.md](/D:/git/chaseNovel/references/language-governance.md)
- [voice.md](/D:/git/chaseNovel/templates/voice.md)
- [character-voice-diff.md](/D:/git/chaseNovel/templates/character-voice-diff.md)

### 记忆与长期线

- [templates/plan.md](/D:/git/chaseNovel/templates/plan.md)
- [templates/state.md](/D:/git/chaseNovel/templates/state.md)
- [templates/foreshadowing.md](/D:/git/chaseNovel/templates/foreshadowing.md)
- [templates/payoff-board.md](/D:/git/chaseNovel/templates/payoff-board.md)
- [templates/timeline.md](/D:/git/chaseNovel/templates/timeline.md)
- [templates/arc-progress.md](/D:/git/chaseNovel/templates/arc-progress.md)

### 题材与专题

- [genre-asset-index.md](/D:/git/chaseNovel/references/genre-asset-index.md)
  先看这一页，再决定下钻哪份题材资料
- `templates/genres/`
  常用题材模板
- `templates/substyles/`
  子风格覆盖模板

## 记忆模型

默认采用文件型记忆，不依赖单次会话上下文。

```text
novel_{书名}/
├── 00_memory/
│   ├── plan.md
│   ├── state.md
│   ├── findings.md
│   ├── arc_progress.md
│   ├── characters.md
│   ├── character_arcs.md
│   ├── timeline.md
│   ├── foreshadowing.md
│   ├── payoff_board.md
│   ├── style.md
│   ├── voice.md
│   └── summaries/
├── 01_outline/
├── 02_knowledge/
├── 03_chapters/
└── 04_gate/
```

最关键的 4 个文件：

- `plan.md`：全书主线、卷纲、阶段目标
- `state.md`：当前推进位置、主冲突、有效布置、下章目标
- `style.md`：书级语言基线、禁写表达、慎用表达
- `voice.md`：这一本书怎么说话

## 常用命令

```bash
chase bootstrap --project "novel_书名"
chase doctor --project "novel_书名"
chase check --project "novel_书名" --chapter 12
chase planning --project "novel_书名" --target-chapter 12
chase context --project "novel_书名" --chapter 12
chase gate --project "novel_书名" --chapter-no 12
chase draft --project "novel_书名" --chapter-no 12
chase audit --project "novel_书名" --chapter-no 12
```

补充：

- `planning` 默认看下一章
- `run --chapter N` 传的是已经写出来的第 `N` 章，不是下一章
- `check` 是严格体检，不是宽松绿灯

## 什么时候再往下读

- 要做开书和平台节奏：读 [craft-and-platform.md](/D:/git/chaseNovel/references/craft-and-platform.md)
- 要写章和续写：读 [execution_workflow.md](/D:/git/chaseNovel/references/execution_workflow.md)
- 要改章和诊断：读 [revision-and-diagnostics.md](/D:/git/chaseNovel/references/revision-and-diagnostics.md)
- 要管文风和对白：读 [style-runtime-core.md](/D:/git/chaseNovel/references/style-runtime-core.md) 和 [language-governance.md](/D:/git/chaseNovel/references/language-governance.md)
- 要看固定输出骨架：读 [output-contracts.md](/D:/git/chaseNovel/references/output-contracts.md)
- 要决定单人还是多轮复核：读 [agent-collaboration.md](/D:/git/chaseNovel/references/agent-collaboration.md)
