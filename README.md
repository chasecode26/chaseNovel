# chaseNovel

面向中文网文平台连载的写作技能仓库。  
目标不是“给一段 prompt 写一章”，而是把连载写作拆成可复用的工作流、模板、知识资产和校验脚本，长期解决这几类问题：

- 开书时卖点不立、黄金三章发散
- 连载中剧情重复、节奏拖沓、伏笔失忆
- 世界观写崩、时间线打架、人物行为失真
- 文本 AI 味重、对白撞车、旁白发硬

## 一眼看懂

- 主入口：`SKILL.md`
- 题材导航：`references/genre-asset-index.md`
- 默认模式：轻量多 agent 协同，不走重型编排系统
- 自检方式：`Reviewer` 收总口，专项问题拆给独立 reviewer

## 默认编排

### 开书

`Planner -> Character -> Worldbuilder -> Reviewer`

资料依赖题材可扩成：

`Planner -> ResearchMaterial -> Character -> Worldbuilder -> Reviewer`

### 写 / 续写

`Planner -> HookEmotion -> Writer -> StyleDialogue -> LanguageReviewer -> Reviewer`

### 修改

`Reviewer -> Planner -> HookEmotion -> Writer -> StyleDialogue -> LanguageReviewer -> ContinuityReviewer -> CausalityReviewer -> Reviewer`

## Agent 分工

- `Planner`：卖点、路线、章卡、卷目标
- `Worldbuilder`：世界规则、术语、考据口径
- `Character`：人物动机、关系变化、反工具人
- `HookEmotion`：情绪曲线、章尾钩子、爽点换挡
- `StyleDialogue`：对白口吻、旁白硬度、角色说话区分
- `LanguageReviewer`：AI 味、机械过渡、解释味、信息搬运感
- `ContinuityReviewer`：世界规则、时间线、伏笔、承诺、布置连续性
- `CausalityReviewer`：转折前提、人物决策、结果落地、后账合理性
- `ResearchMaterial`：资料抽读、考据压缩、本地语料转写
- `Writer`：正文落地
- `Reviewer`：总门禁、重复、回退决策、阶段复盘

## 当前重点题材

- 历史权谋 / 边境战争
- 末世囤货
- 仙侠苟道
- 都市系统流
- 种田文
- 盗墓 / 摸金 / 民国奇诡

## 仓库结构

```text
repo/
├─ SKILL.md
├─ references/
├─ templates/
│  ├─ genres/
│  └─ substyles/
├─ technique-kb/
├─ scripts/
├─ schemas/
└─ bin/
```

- `SKILL.md`：最小工作流、读取策略、门禁与导航
- `references/`：规则、诊断、contracts、题材学习资产
- `templates/`：项目记忆模板、章卡模板、题材模板、审查卡
- `technique-kb/`：给脚本和人工共用的结构化技法知识
- `scripts/`：bootstrap、doctor、context、gate、batch、dashboard 等工具
- `bin/`：`chase` CLI 入口

## 先读什么

### 开书

- `references/craft-and-platform.md`
- `templates/opening-route-cheatsheet.md`
- `templates/golden-three-route-cheatsheet.md`
- `references/title-and-selling.md`

### 单章推进

- `templates/hook-route-cheatsheet.md`
- `templates/result-route-cheatsheet.md`
- `references/chapter-emotion-and-ai-check.md`

### 修章 / 诊断

- `references/revision-and-diagnostics.md`
- `references/anti-repeat-rules.md`
- `references/language-governance.md`

### 题材学习

- `references/genre-asset-index.md`
- `references/local-corpus-learning.md`
- `references/local-corpus-priority-map.md`

### Agent 协同

- `references/agent-collaboration.md`
- `references/output-contracts.md`
- `references/contracts/07-research-material.md`

## 审查模板

- `templates/character-voice-diff.md`
  给 `StyleDialogue` 拉开角色说话差分
- `templates/language-anti-ai-review.md`
  给 `LanguageReviewer` 专查 AI 味、机械过渡、解释味
- `templates/continuity-review-card.md`
  给 `ContinuityReviewer` 专查规则、时间线、伏笔、承诺
- `templates/causality-review-card.md`
  给 `CausalityReviewer` 专查转折前提、人物决策、结果合理性
- `templates/reviewer-stage-retro.md`
  给 `Reviewer` 做阶段复盘

## 常用命令

```bash
python scripts/project_bootstrap.py --project "novel_书名"
python scripts/project_doctor.py --project "novel_书名"
python scripts/context_compiler.py --project "novel_书名" --chapter 12
python scripts/workflow_runner.py --project "novel_书名" --chapter 12
python scripts/chapter_gate.py --project "novel_书名" --chapter-no 12
python scripts/language_audit.py --project "novel_书名" --chapter-no 12 --mode suggest
python scripts/batch_gate.py --project "novel_书名" --from 1 --to 30 --json
```

### 命令说明

- `project_bootstrap.py`
  新建小说项目目录和基础记忆文件
- `project_doctor.py`
  检查项目结构、关键文件、当前状态
- `context_compiler.py`
  生成下一章最小上下文包
- `workflow_runner.py`
  串起 `doctor -> context -> memory -> foreshadow -> arc -> timeline -> repeat -> dashboard`
- `chapter_gate.py`
  做单章门禁与连续性校验
- `batch_gate.py`
  做多章汇总门禁

### 关于 `workflow_runner --chapter`

`workflow_runner.py --chapter N` 里的 `N` 指“已经写完并已落盘的当前章”。  
因为流水线里的 `memory` 步骤会回填这一章。

如果你只是要准备下一章上下文，不要把“下一章号”直接传给 `workflow_runner`，而是单独用：

```bash
python scripts/context_compiler.py --project "novel_书名" --chapter 下一章
```

## 使用建议

1. 先看 `SKILL.md`
2. 再按任务去 `references/` 找对应规则
3. 需要固定骨架时用 `templates/`
4. 需要静态校验时跑 `scripts/`

## 原则

- 从本地小说学习结构，不搬运原文
- 先保结构，再修语言
- 先保连续性，再追求文气
- 先让下一章有人想看，再追求段落精致
- 不把所有规则堆进一个超长 prompt，而是拆成入口、规则、模板、知识和脚本
