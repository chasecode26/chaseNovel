# chaseNovel 架构说明

## 目标

`chaseNovel` 是一套面向中文长篇小说连载的 repo、本地技能与辅助脚本集合。

它的目标不是把流程做重，而是在故事质量优先的前提下，为能够持续连载数十章、数百章的项目提供稳定支撑。

当前架构服务的核心对象是：

- 本地单主笔创作
- 带项目记忆的持续连载
- 带质量门禁的章节推进
- 断更后的状态恢复
- 可审、可回退、可持续演进的写作流程

一句话概括：架构必须服从稿件质量，而不是反过来让稿件服从流程管理。

## 设计原则

1. `SKILL.md` 仍然是主入口。
2. 长期状态存放在项目文件中，不依赖瞬时会话上下文。
3. 脚本只保留那些对稿件仍有明确价值的重复检查。
4. 当更严格的 Agent 协作能提升章节质量时，允许流程变严。
5. 默认最小读取；一旦连续性、因果、承诺、资源状态或文风一致性有风险，立刻扩读。
6. 不引入 GUI 或管理层，除非它直接改善稿件质量或协作效率。

## 当前架构重点

当前版本的核心变化有三条：

1. 默认采用质量优先的多 Agent 生产链  
   `Planner -> HookEmotion -> Writer -> (LanguageReviewer || StyleDialogue || ContinuityReviewer || CausalityReviewer) -> Reviewer`
2. 默认把 `blocking=yes` 视为硬回退信号，而不是普通提醒。
3. 脚本层开始和文档契约对齐，显式产出：
   - `blocking`
   - `return_to`
   - `rewrite_scope`
   - `first_fix_priority`
   - `recheck_order`
   - `language_block`
   - `causality_block`

这里的 `Reviewer` 指总审角色，负责最终放行，不等于并行 reviewers。

## 运行分层

### 第一层：交互层

- `SKILL.md`
- 任务路由
- 章节级对话式写作
- `Planner / Writer / Reviewer` 角色分工

这一层负责把用户请求翻译成“该走哪条写作链”。

### 第二层：编排层

- `chase` CLI
- `workflow_runner.py`
- 各类子命令入口
- 干跑检查与报告聚合

这一层负责把单个能力串成可执行流水线。

### 第三层：书籍引擎层

- 项目记忆文件
- 伏笔排期
- 人物弧跟踪
- 时间线校验
- 反重复分析
- 书级 `voice` 与 `style` 治理

这一层负责“这本书本身”的长期稳定性。

### 第四层：分析与报告层

- `chapter_planning_review.py`
- `chapter_gate.py`
- `language_audit.py`
- `batch_gate.py`
- `project_doctor.py`
- `dashboard_snapshot.py`

这一层负责把问题显式化、结构化、可回退化。

## 仓库结构

```text
repo/
├─ ARCHITECTURE.md
├─ README.md
├─ SKILL.md
├─ bin/
│  └─ chase.js
├─ scripts/
│  ├─ chapter_planning_review.py
│  ├─ chapter_gate.py
│  ├─ batch_gate.py
│  ├─ draft_gate.py
│  ├─ language_audit.py
│  ├─ context_compiler.py
│  ├─ foreshadow_scheduler.py
│  ├─ arc_tracker.py
│  ├─ timeline_check.py
│  ├─ anti_repeat_scan.py
│  ├─ dashboard_snapshot.py
│  ├─ project_bootstrap.py
│  ├─ project_doctor.py
│  ├─ memory_update.py
│  └─ workflow_runner.py
├─ schemas/
├─ references/
├─ templates/
├─ technique-kb/
└─ skill.json
```

## 小说项目结构

```text
novel_{book}/
├─ 00_memory/
│  ├─ plan.md
│  ├─ state.md
│  ├─ arc_progress.md
│  ├─ characters.md
│  ├─ character_arcs.md
│  ├─ timeline.md
│  ├─ foreshadowing.md
│  ├─ payoff_board.md
│  ├─ style.md
│  ├─ voice.md
│  ├─ scene_preferences.md
│  ├─ findings.md
│  ├─ summaries/
│  │  └─ recent.md
│  └─ retrieval/
│     ├─ next_context.md
│     └─ dashboard_cache.json
├─ 01_outline/
├─ 02_knowledge/
├─ 03_chapters/
├─ 04_gate/
└─ 05_reports/
```

## 核心工作流

### 1. 章节规划

由 `chapter_planning_review.py` 负责。

它当前不只做传统预审，还会补出规划契约层：

- `planner_contract`
- `hook_emotion_contract`
- `blocking`
- `return_to`
- `rewrite_scope`
- `first_fix_priority`
- `recheck_order`

### 2. 正文写作

正文仍由技能主流程驱动，不直接交给脚本生成。

脚本不负责写文，只负责：

- 减少重复检查
- 暴露连续性问题
- 暴露语言问题
- 把回退路径写清楚

### 3. 语言审查

由 `language_audit.py` 负责。

它当前的职责包括：

- AI 味识别
- 提炼句、概括句、抽象氛围堆叠识别
- 黑话简称与半截判断识别
- 对白问答错位、声口问题辅助识别
- 双闸题材检查

当前会显式产出：

- `findings`
- `blocking`
- `suggested_fix`
- `ai_tone_source`
- `needs_full_rewrite`
- `language_block`
- `causality_block`

### 4. 连续性门禁

由 `chapter_gate.py` 负责。

它负责把以下信息汇总到一处：

- 规划预审结果
- 连续性与时间线状态
- 语言审查结果
- 最终脚本级回退契约

当前会显式产出：

- `blocking`
- `return_to`
- `rewrite_scope`
- `first_fix_priority`
- `recheck_order`
- `script_final_release`

这里的 `script_final_release` 是脚本放行结论字段，与聚合层看到的 `final_release` 含义一致。

### 5. 整链体检

由 `workflow_runner.py` 与 `chase check` 负责。

它当前不再只看 `returncode`，还会汇总：

- 每步 `blocking`
- 每步脚本放行结论
- 全局 `blockers`
- `blocking_steps`

这意味着 `check` 已经开始从“脚本是否跑完”转向“流程是否可继续推进”。

## 命令面

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

关键约束：

- `planning` 默认看“下一章”
- `run --chapter N` 传的是已经写出的第 `N` 章
- `check` 是干跑体检，不是宽松绿灯

## 脚本使用对象

仓库里的 `scripts/*.py` 不是单纯给 agent 用的隐藏内部接口，而是一个共享工具层：

1. 给人直接使用
   通过 `bin/chase.js` 暴露成 `chase planning / check / context / dashboard ...`

2. 给 agent 直接调用
   agent 可以直接跑 `python scripts/<name>.py --project ... --json`

3. 给编排层调用
   `workflow_runner.py` 会把多个单点脚本串成一条完整工作流

4. 给产物消费层调用
   `dashboard_snapshot.py`、`context_compiler.py`、retrieval 缓存会继续读取前面脚本产出的 `json/md`

因此更准确的分层是：
- `scripts/*.py` = 能力层
- `workflow_runner.py` = 编排层
- `bin/chase.js` = 交互入口层
- `05_reports` + `00_memory/retrieval` = 产物消费层

## 谁应该直接碰什么

| 对象 | 推荐入口 | 不推荐 |
|------|----------|--------|
| 人 | `chase <command>` | 手记所有 `python scripts/*.py` 参数 |
| Agent | `python scripts/*.py --json` 或 `chase run/check` | 手写重复解析逻辑 |
| 下游脚本 | 读取 `05_reports/*.json` / `00_memory/retrieval/*.json` | 反复重跑无关脚本 |

## 为什么采用这种形态

- 对长篇连载来说，聊天依然是最快的写作表面
- Python 脚本依然是成本最低的自动化层
- Markdown 记忆依然是最透明、最可维护的状态格式
- Agent 角色存在的目的只有一个：提高章节质量

任何不能改善稿件质量的层，都不应该长期留在主路径里。

## 当前边界

这套架构当前明确不做的事：

- 不把正文写作完全脚本化
- 不把项目管理做成独立系统
- 不把所有题材压成统一口水文腔
- 不把脚本结果等同于最终审稿结论

## 一句话总结

`chaseNovel` 的架构不是“写作管理平台”，而是一套围绕长篇连载质量构建的：`技能入口 + 项目记忆 + 多 Agent 复审 + 脚本门禁 + 可回退报告` 的本地工作架构。
