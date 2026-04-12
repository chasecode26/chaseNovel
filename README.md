# chaseNovel

`chaseNovel` 是一套面向中文长篇小说连载的本地技能与脚本工作台。

它不解决“给我一个 prompt 写一章”这种单点问题，解决的是长篇连载真正会失控的地方：

- 项目记忆
- 章节规划
- 正文推进
- 多 Agent 复审
- 质量门禁
- 脚本体检

核心目标只有一个：在几十章、几百章的推进过程中，尽量稳住节奏、设定、人物、伏笔、文风和追读动力。

## 当前版本重点

当前默认走质量优先的多 Agent 链路：

`Planner -> HookEmotion -> Writer -> (LanguageReviewer || StyleDialogue || ContinuityReviewer || CausalityReviewer) -> Reviewer`

这里的 `Reviewer` 指总审角色，不是普通 reviewer。

硬规则如下：

- 同一章同一时刻只允许一个 `Writer`
- 任一 reviewer 给出 `blocking=yes`，直接回退
- `Reviewer` 拥有最终放行权
- 脚本通过不等于可交稿
- 整章读感不过，默认返工

## 适用场景

- 开新书，做题材定位、卖点、黄金三章、卷纲、阶段目标
- 依赖 `plan.md`、`state.md`、时间线、人物弧、伏笔表推进后续章节
- 修复水章、重复章、AI 味重、人物失真、因果不稳的章节
- 做断更恢复、批量体检、伏笔排期、反重复扫描
- 管理书级 `voice` 与 `style`，而不是只润单章句子

## 不适用场景

- 只想临时要一句灵感文案
- 只想随手润一小段，不关心长线连续性
- 明确不要项目记忆、不要质量门禁、不要复审流程

## 仓库结构

- [SKILL.md](/D:/ai/chaseNovel/SKILL.md)
  技能主入口，定义默认流程、角色链路、质量门槛和资源导航
- [ARCHITECTURE.md](/D:/ai/chaseNovel/ARCHITECTURE.md)
  架构说明，描述分层、职责和边界
- [references/](/D:/ai/chaseNovel/references)
  执行规则、contracts、协作规范、诊断说明
- [templates/](/D:/ai/chaseNovel/templates)
  项目模板、记忆模板、文风模板、审查模板
- [technique-kb/](/D:/ai/chaseNovel/technique-kb)
  结构化写作规则库
- [scripts/](/D:/ai/chaseNovel/scripts)
  本地体检、审查、门禁、报告脚本
- [bin/chase.js](/D:/ai/chaseNovel/bin/chase.js)
  CLI 入口

## 默认工作流

### 开书

`Planner -> Character -> Worldbuilder -> Reviewer`

这里的 `Reviewer` 仍然是总审角色，但开书链不进入章节级四审。

### 写章 / 续写

`Planner -> HookEmotion -> Writer -> (LanguageReviewer || StyleDialogue || ContinuityReviewer || CausalityReviewer) -> Reviewer`

### 改章

`Reviewer -> Planner -> HookEmotion(如需要) -> Writer -> (LanguageReviewer || StyleDialogue || ContinuityReviewer || CausalityReviewer) -> Reviewer`

## 质量门禁

`chaseNovel` 默认不是先写完再说，而是边推进边过门。

当前脚本层与文档契约已经对齐，核心会显式输出：

- `blocking`
- `return_to`
- `rewrite_scope`
- `first_fix_priority`
- `recheck_order`
- `language_block`
- `causality_block`

脚本放行结论统一看“脚本放行结论”字段：

- 聚合层常见字段为 `final_release`
- `chapter_gate.py` 当前输出字段为 `script_final_release`

含义一致，都是“脚本层是否建议继续推进”。

## 本地脚本

核心脚本包括：

- `chapter_planning_review.py`
- `chapter_gate.py`
- `draft_gate.py`
- `language_audit.py`
- `timeline_check.py`
- `anti_repeat_scan.py`
- `foreshadow_scheduler.py`
- `arc_tracker.py`
- `dashboard_snapshot.py`
- `workflow_runner.py`

其中：

- `planning` 负责章节规划预审与回退契约
- `audit` 负责语言、AI 味、黑话简称、双闸题材检查
- `gate` 负责连续性、因果、语言门禁汇总
- `check` 负责整条 dry-run 体检

## 脚本给谁用

这些 `py` 不是只给 agent 用的内部脚本，而是一套“人和 agent 共用”的本地工具层。

| 类型 | 谁在用 | 常见入口 | 主要作用 |
|------|--------|----------|----------|
| 人直接使用 | 作者 / 操作人 | `chase check`、`chase context`、`chase volume` | 手动体检、生成报告、排查问题 |
| Agent 直接使用 | Codex / 其他 agent | `python scripts/*.py --project ... --json` | 读取状态、跑审计、生成上下文 |
| 编排器内部使用 | `workflow_runner.py` | `chase run`、`chase check` | 串起多步脚本，形成完整工作流 |
| 报告与检索层消费 | `dashboard_snapshot.py`、`context_compiler.py`、retrieval | 继续消费 `05_reports/*.json` 与 `00_memory/retrieval/*.json` |

更准确地说：
- `scripts/*.py` 是能力层
- `bin/chase.js` 是统一 CLI 入口
- `workflow_runner.py` 是编排层
- `05_reports` 与 `00_memory/retrieval` 是产物消费层

## 脚本分工速查

### 直接给人和 agent 跑的能力脚本

| 脚本 | 入口 | 主要作用 |
|------|------|----------|
| `project_bootstrap.py` | `chase bootstrap` | 初始化项目骨架 |
| `project_doctor.py` | `chase doctor` | 检查项目能否继续工作 |
| `context_compiler.py` | `chase context` | 生成 `next_context` |
| `chapter_planning_review.py` | `chase planning` | 做章节规划预审 |
| `draft_gate.py` | `chase draft` | 检查草稿级问题 |
| `chapter_gate.py` | `chase gate` | 做章节门禁汇总 |
| `language_audit.py` | `chase audit` | 查语言、AI 味与风格问题 |
| `anti_repeat_scan.py` | `chase repeat` | 查重复与中盘疲劳 |
| `timeline_check.py` | `chase timeline` | 查时间线冲突 |
| `foreshadow_scheduler.py` | `chase foreshadow` | 排期伏笔与回收窗口 |
| `arc_tracker.py` | `chase arc` | 跟踪角色弧/主线弧推进 |
| `memory_update.py` | `chase memory` | 更新 `recent.md`、`mid.md`、同步队列 |
| `volume_audit.py` | `chase volume` | 做卷级健康审计 |
| `milestone_audit.py` | `chase milestone` | 做节点/字数审计 |
| `dashboard_snapshot.py` | `chase dashboard` | 生成 dashboard 与风险摘要 |

### 主要给编排器调用的脚本

| 脚本 | 谁调用它 | 作用 |
|------|----------|------|
| `workflow_runner.py` | `chase run` / `chase check` / agent | 串起多步脚本并输出统一 pipeline 报告 |
| `batch_gate.py` | 人 / agent / 批处理 | 批量检查多章 |

### 主要给其他脚本导入的辅助脚本

| 脚本 | 谁用它 | 作用 |
|------|--------|------|
| `novel_utils.py` | 几乎所有 `scripts/*.py` | 提供项目读写、章节识别、题材识别、Markdown 表格解析等基础函数 |

## 推荐使用方式

- 人手动使用：优先走 `chase <command>`
- Agent 自动化：优先走 `python scripts/*.py --json` 或 `chase run/check`
- 需要整链体检：走 `chase check`
- 需要自定义步骤：走 `chase run --steps ...`
- 需要给后续写作喂状态：看 `00_memory/retrieval/next_context.*` 与 `health_digest.*`

## CLI

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
chase planning --project "novel_书名" --target-chapter 12
chase check --project "novel_书名" --chapter 12
chase gate --project "novel_书名" --chapter-no 12
chase audit --project "novel_书名" --chapter-no 12
```

## 记忆文件

这套技能的核心假设是：长篇连载不能只靠当前会话上下文。

所以状态默认落在项目文件里，而不是只活在聊天里。常用文件包括：

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

最关键的 4 个文件：

- `plan.md`
- `state.md`
- `style.md`
- `voice.md`

## 推荐阅读顺序

1. [SKILL.md](/D:/ai/chaseNovel/SKILL.md)
2. [references/execution_workflow.md](/D:/ai/chaseNovel/references/execution_workflow.md)
3. [references/output-contracts.md](/D:/ai/chaseNovel/references/output-contracts.md)
4. [references/agent-collaboration.md](/D:/ai/chaseNovel/references/agent-collaboration.md)
5. 再按任务类型进入对应 `references/`

## 一句话总结

`chaseNovel` 不是“网文 prompt 集”，而是一套把长篇连载写作文件化、可恢复、可复审、可校验、可持续推进的本地技能工作台。
