# chaseNovel

`chaseNovel` 是一套面向中文网文长篇连载的写作技能仓库。

它解决的不是“给我一个 prompt 写一章”，而是把连载写作拆成可复用的：

- 规则
- 记忆文件
- 审查模板
- 质量门槛
- 本地脚本工具

目标很明确：让项目在几十章、几百章之后，仍然能稳住节奏、设定、人物和追读动力。

## 它适合什么

- 开新书，做题材定位、卖点、黄金三章、卷纲和阶段目标
- 继续写已有项目，依赖 `plan.md`、`state.md`、时间线、人物弧和伏笔表推进
- 修改烂章、水章、重复章、AI 味重的章
- 做断更恢复、阶段体检、伏笔回收排期、反重复扫描
- 管理“书级 voice”而不是只管某一章顺不顺

## 它不适合什么

- 只想要一句灵感文案
- 只想随手润色一小段，不关心长线连续性
- 只做文学评论，不推进创作
- 明确不要项目记忆、不要质量门槛、不要连载约束

## 现在这套版本的核心变化

这版 `chaseNovel` 不再把所有书默认压成统一“番茄腔”或“口水化大白话”。

当前默认基线是：

- 清晰可判读
- 章节功能优先
- 结果变化要落地
- 对白要有真实功能
- 文风要服从题材、角色和项目自己的 `voice.md`

只有在用户明确指定平台，或题材天然要求高密度快反馈时，才启用番茄向覆盖策略。

换句话说：

- 默认不是“统一短句快推”
- 默认不是“所有对白都直给”
- 默认不是“写清楚 = 扁平化”

## 仓库里有什么

- [SKILL.md](/D:/git/chaseNovel/SKILL.md)
  主入口。定义工作流、任务路由、默认 Agent 编排、门槛和引用导航。
- [references/](/D:/git/chaseNovel/references)
  规则、contracts、诊断文档、题材资料、平台策略和执行说明。
- [templates/](/D:/git/chaseNovel/templates)
  记忆模板、章卡模板、审查模板、风格模板。
- [technique-kb/](/D:/git/chaseNovel/technique-kb)
  供脚本和人工共用的结构化技法知识库。
- [scripts/](/D:/git/chaseNovel/scripts)
  本地质量工具：planning、context、timeline、repeat、gate、audit、dashboard 等。
- [bin/chase.js](/D:/git/chaseNovel/bin/chase.js)
  CLI 入口。
- [ARCHITECTURE.md](/D:/git/chaseNovel/ARCHITECTURE.md)
  设计目标、分层和项目布局说明。

## 快速上手

1. 先看 [SKILL.md](/D:/git/chaseNovel/SKILL.md) 顶部“快速入口”。
2. 用 `chase bootstrap --project "novel_书名"` 初始化项目。
3. 用 `chase doctor --project "novel_书名"` 检查结构是否完整。
4. 写下一章前，先跑 `chase planning` 或 `chase check`，把规划和上下文锚点补齐。
5. 草稿完成后，再跑 `gate`、`draft`、`audit` 一类脚本做闸门。

说明：

- `check` 不是宽松绿灯，它是严格体检。
- 一个刚 bootstrap、但还没补齐规划和记忆文件的项目，`check` 失败是正常的。
- 这不是流程设计失误，而是为了阻止“没锚点硬写”。

## 默认工作流

### 开书

`Planner -> Character -> Worldbuilder -> Reviewer`

### 写章 / 续写

`Planner -> HookEmotion -> Writer -> [StyleDialogue || LanguageReviewer || StyleConsistencyReviewer || ContinuityReviewer || CausalityReviewer || Reviewer] -> Writer/Planner 修正 -> Reviewer`

### 改章

`Reviewer -> Planner -> HookEmotion -> Writer -> [StyleDialogue || LanguageReviewer || StyleConsistencyReviewer || ContinuityReviewer || CausalityReviewer] -> Writer 修正 -> Reviewer`

## 质量门槛

写作不是“先写完再说”，而是默认带门槛推进：

- 写前先做章节规划预审
- 写后先过连续性和因果闸门
- 语言层再过 AI 味、对白差分、风格漂移审计
- 项目级持续检查时间线、伏笔、人物弧和重复风险

关键脚本：

- `chapter_planning_review.py`
- `chapter_gate.py`
- `draft_gate.py`
- `language_audit.py`
- `timeline_check.py`
- `anti_repeat_scan.py`
- `foreshadow_scheduler.py`
- `arc_tracker.py`
- `dashboard_snapshot.py`

## CLI 命令面

实际可用命令如下：

```bash
chase planning --project <dir> [--chapter <n> | --target-chapter <n>]
chase context --project <dir> [--chapter <n>]
chase foreshadow --project <dir> [--chapter <n>]
chase dashboard --project <dir>
chase arc --project <dir>
chase timeline --project <dir>
chase repeat --project <dir>
chase memory --project <dir> [--chapter <n>]
chase gate --project <dir> [--chapter-no <n>]
chase draft --project <dir> [--chapter-no <n>]
chase batch --project <dir> [--from <n> --to <n>]
chase audit --project <dir> [--chapter-no <n>]
chase bootstrap --project <dir> [--force]
chase doctor --project <dir> [--json]
chase check --project <dir> [--chapter <n>]
chase run --project <dir> [--chapter <n>] [--steps <csv>]
```

常见用法：

```bash
chase bootstrap --project "novel_书名"
chase doctor --project "novel_书名"
chase check --project "novel_书名" --chapter 12
chase planning --project "novel_书名" --target-chapter 12
chase context --project "novel_书名" --chapter 12
chase gate --project "novel_书名" --chapter-no 12
chase draft --project "novel_书名" --chapter-no 12
chase audit --project "novel_书名" --chapter-no 12
chase run --project "novel_书名" --chapter 12
```

补充规则：

- `planning` 默认看“下一章”；`--chapter` 表示当前已存在草稿章。
- `run --chapter N` 传的是“已经写出来的第 N 章”，不是下一章。
- `check` 是一次 dry-run 健康扫描：`doctor + planning + context + foreshadow + arc + timeline + repeat + dashboard`。

## 推荐阅读顺序

1. [SKILL.md](/D:/git/chaseNovel/SKILL.md)
2. [references/execution_workflow.md](/D:/git/chaseNovel/references/execution_workflow.md)
3. [references/output-contracts.md](/D:/git/chaseNovel/references/output-contracts.md)
4. [references/agent-collaboration.md](/D:/git/chaseNovel/references/agent-collaboration.md)
5. 再按任务类型进入对应 `references/`
6. 需要固定骨架时看 `templates/`
7. 需要做批量校验时看 `scripts/`

## 记忆文件为什么重要

`chaseNovel` 的核心假设是：

长篇连载不能只靠当前聊天上下文。

所以项目状态默认落在 Markdown 文件里，而不是只活在会话里。常见记忆文件包括：

- `plan.md`
- `state.md`
- `characters.md`
- `character_arcs.md`
- `timeline.md`
- `foreshadowing.md`
- `payoff_board.md`
- `style.md`
- `voice.md`
- `scene_preferences.md`
- `summaries/recent.md`

其中：

- `style.md` 负责书级语言基线、禁写表达、慎用表达
- `voice.md` 负责“这一本书怎么说话”
- `character-voice-diff.md` 负责角色台词差分，不让所有人说成一个声口

## 目录结构

```text
repo/
├── SKILL.md
├── README.md
├── ARCHITECTURE.md
├── bin/
├── references/
├── templates/
├── technique-kb/
├── scripts/
├── schemas/
└── skill.json
```

典型小说项目结构：

```text
novel_{book}/
├── 00_memory/
├── 01_outline/
├── 02_knowledge/
├── 03_chapters/
├── 04_gate/
└── 05_reports/
```

## 文风治理现在会抓什么

当前语言治理不只是查“句子顺不顺”，还会查这些问题：

- 作者替角色下结论
- 抽象氛围词堆叠
- 故意写虚、强行吊着不说
- 提纲扩写感
- 对白像在搬运信息
- 多角色同声
- 书级 voice 漂移

对应入口：

- [references/language-governance.md](/D:/git/chaseNovel/references/language-governance.md)
- [references/style-runtime-core.md](/D:/git/chaseNovel/references/style-runtime-core.md)
- [templates/language-anti-ai-review.md](/D:/git/chaseNovel/templates/language-anti-ai-review.md)
- [templates/character-voice-diff.md](/D:/git/chaseNovel/templates/character-voice-diff.md)
- [scripts/language_audit.py](/D:/git/chaseNovel/scripts/language_audit.py)

## 一句话总结

`chaseNovel` 不是“网文 prompt 集”，而是一套把长篇连载写作文件化、可恢复、可审查、可持续推进的本地工作台。
