# chaseNovel

面向中文网文平台连载写作的技能仓库。

目标不是“给一段 prompt 写一章”，而是把连载写作拆成可复用的规则、模板、记忆文件和质量门禁，一切以把小说写好为先。

## 三步上手

1. 先看 `SKILL.md` 顶部的“快速入口”，确认你现在是在开书、写章、续写还是改章。
2. 用 `chase bootstrap` 建项目，用 `chase doctor` / `chase check` 看结构和状态是否健康。
3. 真正落章时，先过规划，再跑门禁，不跳过 `planning -> gate/audit -> memory` 这条闭环。

说明：`chase check` 不是“宽松通过器”。如果项目还没补齐地点、目标、章卡、上下文锚点，它会直接失败，这是为了保住小说质量，而不是为了流程好看。
跨任务规则与表达标准，统一看 `references/output-contracts.md` 和 `references/execution_workflow.md`。

## 当前能力

- 写前规划预审：章节存在理由、结果升级、章尾钩子、到期伏笔、关键节点窗口。
- 写后质量门禁：连续性、因果、语言、风格一致性、对白区分、反重复。
- 项目级体检：目录结构、记忆文件、时间线、角色弧、伏笔热度、Dashboard 总览。
- 共享脚本工具层：章节识别、章节计数、最新章节定位、到期伏笔读取、表格解析、状态值清洗。

## 默认流程

### 开书

`Planner -> Character -> Worldbuilder -> Reviewer`

### 写章 / 续写

`Planner -> HookEmotion -> Writer -> [StyleDialogue || LanguageReviewer || StyleConsistencyReviewer || ContinuityReviewer || CausalityReviewer || Reviewer] -> Writer/Planner 修正 -> Reviewer`

### 改章

`Reviewer -> Planner -> HookEmotion -> Writer -> [StyleDialogue || LanguageReviewer || StyleConsistencyReviewer || ContinuityReviewer || CausalityReviewer] -> Writer 修正 -> Reviewer`

## 质量门禁

- 写前先跑 `chapter_planning_review.py`，规划不过不进正文。
- 写后先跑 `chapter_gate.py` 和 `language_audit.py`，再做人工或多 agent 收口。
- `workflow_runner.py` 默认流水线为：
  `doctor -> planning -> context -> memory -> foreshadow -> arc -> timeline -> repeat -> dashboard`
- 任一硬阻断项存在时，默认回修，不以“流程太重”为理由放行。

## 关键脚本

- `scripts/project_bootstrap.py`
  新建小说项目目录和基础记忆文件。
- `scripts/project_doctor.py`
  检查项目结构、关键文件和当前状态。
- `scripts/chapter_planning_review.py`
  写前章节规划预审。
- `scripts/context_compiler.py`
  生成下一章最小上下文包。
- `scripts/memory_update.py`
  写后回填 `state.md` 和 `summaries/recent.md`。
- `scripts/foreshadow_scheduler.py`
  识别到期伏笔、超期伏笔和活跃伏笔。
- `scripts/arc_tracker.py`
  扫描角色弧和关系弧的停滞风险。
- `scripts/timeline_check.py`
  检查时间线锚点和章节顺序。
- `scripts/anti_repeat_scan.py`
  扫描近章摘要和正文的重复推进风险。
- `scripts/chapter_gate.py`
  做单章节连续性与因果门禁。
- `scripts/language_audit.py`
  做语言、风格、一致性、对白区分审计。
- `scripts/dashboard_snapshot.py`
  生成项目级总览。
- `scripts/workflow_runner.py`
  串起整条质量流水线。

## 仓库结构

```text
repo/
├── SKILL.md
├── references/
├── templates/
├── technique-kb/
├── scripts/
├── schemas/
└── bin/
```

- `SKILL.md`
  入口说明、工作流、门禁与读写策略。
- `references/`
  规则、诊断、contracts、题材学习资产。
- `templates/`
  项目记忆模板、章卡模板、审查模板。
- `technique-kb/`
  给脚本和人工共用的结构化技法知识。
- `scripts/`
  bootstrap、doctor、planning、context、gate、dashboard 等工具。
- `bin/`
  `chase` CLI 入口。

## 常用命令

```bash
python scripts/project_bootstrap.py --project "novel_书名"
python scripts/project_doctor.py --project "novel_书名"
chase bootstrap --project "novel_书名"
chase doctor --project "novel_书名"
chase check --project "novel_书名" --chapter 12
python scripts/chapter_planning_review.py --project "novel_书名" --target-chapter 12
python scripts/context_compiler.py --project "novel_书名" --chapter 12
python scripts/workflow_runner.py --project "novel_书名" --chapter 12
python scripts/chapter_gate.py --project "novel_书名" --chapter-no 12
python scripts/language_audit.py --project "novel_书名" --chapter-no 12 --mode suggest
```

## 推荐阅读顺序

- 先看 `SKILL.md`
- 再看 `references/execution_workflow.md`
- 然后按任务进入 `references/` 对应专题
- 需要固定骨架时用 `templates/`
- 需要静态校验时用 `scripts/`

## 验证

```bash
python -m unittest discover -s tests -v
```
