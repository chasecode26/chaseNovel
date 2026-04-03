---
name: chaseNovel
description: 当用户要策划、起稿、续写、改写或管理中文网文平台连载，并且关注章节节奏、章尾钩子、伏笔回收、设定连续性、角色推进与追读留存时使用。
---

# 小说连载写作器

面向中文网文平台连载的写作技能。它不是“随手写一章”的轻量提示词，而是一套围绕**连载推进、文件化记忆、章节功能、伏笔回收、节奏控制、修章校准**构建的工作流。

## 核心原则

1. **连载优先于单章漂亮**：单章必须服务于追读动力、角色推进、冲突升级与后续可持续连载。
2. **文件即记忆**：重要状态写入项目文件，不依赖当前对话上下文，保证断更、换会话、跨天续写仍可恢复。
3. **先保结构，再修语言**：先确认章节功能、信息顺序、角色动机成立，再做润色与语言修正。
4. **按需读取，不机械全读**：默认只读当前任务需要的上下文；只有在长线伏笔、跨卷冲突、时间线校验明确相关时，才扩展读取范围。

## 适用场景

- 开一本中文网文平台连载
- 根据 `plan.md`、`state.md`、人物表、时间线继续写后续章节
- 修复剧情跑偏、人设失真、章节太水、伏笔遗忘、节奏拖沓、桥段重复
- 规划黄金三章、阶段目标、卷节奏、章尾钩子、读者承诺兑现
- 做断更恢复、状态汇总、章节改写、批量推进

## 不适用场景

- 只想写一小段灵感、广告文案、朋友圈文案
- 只需要单次润色一句话，不关心长线设定
- 只做文学评论、拆书分析或论文式分析，而不推进创作
- 明确要求不要文件化记忆、不要连载约束、只要即时自由发挥

## 任务路由

| 用户请求 | 任务类型 | 最小执行路径 |
| --- | --- | --- |
| 帮我开一本新书 | 立项开书 | 题材定位 -> 卖点/钩子 -> 主线目标 -> 角色结构 -> 卷纲/阶段目标 |
| 给我世界观/人设/大纲 | 设定规划 | 明确题材与受众 -> 建立核心冲突 -> 输出可执行设定与阶段推进 |
| 写第X章/继续写 | 单章推进 | 读取 `plan.md` + `state.md` -> 必要时补读相关记忆 -> 明确本章功能 -> 起草 -> 门禁 |
| 续写断更内容 | 状态恢复 | 读取 `plan.md` + `state.md` + `findings.md` + 最近摘要 -> 输出恢复结论 -> 再写 |
| 这章太水了/改一下 | 改写修复 | 识别保留项 -> 诊断问题类型 -> 选择重写/压缩/补钩子/补冲突 |
| 人设崩了/剧情重复了 | 连载校准 | 扫描人物、摘要、伏笔、时间线 -> 找冲突点 -> 修正后续推进策略 |
| 看看现在写到哪了 | 状态查看 | 汇总当前卷、当前阶段、核心冲突、下一章目标 |
| 我要批量推进几章 | 连载推进 | 先确认阶段目标与边界 -> 分章卡 -> 逐章执行门禁，不跨越大纲红线 |
| 帮我回收伏笔 | 伏笔管理 | 读取 `foreshadowing.md` + 最近摘要 -> 判断可回收窗口 -> 设计兑现方式 |
| 改第X章但别动主线 | 定点修章 | 限定影响面 -> 仅修改本章及必要记忆文件 -> 标记受影响的后续章节 |

## 资源导航

入口文件只保留核心流程；长规则、模板与诊断说明拆到 `references/`、`templates/` 与 `scripts/`。

- `references/craft-and-platform.md`
  - 开书、黄金三章、题材节奏、章尾钩子、平台追读逻辑
- `references/execution_workflow.md`
  - 写前准备、写中纪律、写后回填、章节门禁、周期自检
- `references/revision-and-diagnostics.md`
  - 卡文、修章、重复桥段、人物失真、节奏拖沓、承诺拖欠
- `references/language-governance.md`
  - 旁白治理、气氛落地、题材口吻、语言改写边界
- `references/output-contracts.md`
  - `/一键开书`、`/写`、`/续写`、`/修改` 等固定输出骨架
- `references/writing-patterns.md`
  - 章节落地手法、动作化表达、低 AI 味修法
- `references/anti-repeat-rules.md`
  - 重复桥段、重复反馈、重复钩子的专项排查与换法
- `references/advanced-template-map.md`
  - 反派、卷纲、长期转场、感情线、结局等高阶模板导航
- `templates/`
  - 项目记忆模板、章卡示例、题材写法、长期规划辅助模板
- `technique-kb/`
  - 给脚本和人工共用的结构化技法库，用于语言审计、反重复和改写建议
- `scripts/`
  - 自动化能力入口，负责 gate、language audit、自检与记忆回填

## 资源分工

- `SKILL.md`：触发后必须立刻知道的工作流、读取策略、门禁与导航
- `references/`：长规则、诊断逻辑、固定输出契约
- `templates/`：模板、示例、题材写法资产
- `technique-kb/`：可检索、可累积、可供脚本消费的技法知识
- `scripts/`：自动化执行逻辑，以脚本结果为准

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
│   ├── self_checks/
│   └── summaries/
├── 01_outline/
├── 02_knowledge/
├── 03_chapters/
└── 04_gate/
```

### 核心文件职责

- `plan.md`：全书主线、卷纲、红线规则、阶段目标
- `state.md`：当前推进位置、角色状态、当前冲突、有效布置、下一章目标
- `findings.md`：临时发现、潜在线索、后续待跟进问题
- `arc_progress.md`：当前卷、当前阶段、阶段目标、兑现压力
- `characters.md`：角色资料、关系、秘密、动机、变化轨迹
- `character_arcs.md`：角色弧与关系弧推进位置
- `timeline.md`：时间顺序、关键事件、绝对/相对时间锚点
- `foreshadowing.md`：伏笔、触发条件、失效条件、回收窗口
- `payoff_board.md`：读者承诺、兑现窗口、超期风险
- `style.md`：文风、句式、节奏、题材口吻、禁忌表达

## 最小读取策略

默认遵循“最小必要读取”。

### 必读

1. `00_memory/plan.md`
2. `00_memory/state.md`

### 按需补读

- 进入新卷、阶段切换、中盘发散：读 `arc_progress.md`
- 关键人物或关系推进：读 `characters.md`、`character_arcs.md`
- 涉及世界规则、力量体系：优先补写或扩展 `00_memory/plan.md`、`00_memory/findings.md`，必要时自建世界观文件
- 涉及伏笔兑现：读 `foreshadowing.md`
- 涉及读者承诺兑现：读 `payoff_board.md`
- 涉及前后事件对齐、回忆、跳时：强制读 `timeline.md`
- 断更恢复：读 `findings.md` + `summaries/recent.md`
- 怀疑桥段重复：读最近摘要与最近 `repeat_report.md`
- 开书、黄金三章、平台节奏：读 `references/craft-and-platform.md`
- 修章、卡文、人物失真、重复：读 `references/revision-and-diagnostics.md`
- 想把结构写得更抓人、更自然：读 `references/writing-patterns.md`
- 怀疑桥段、反馈、钩子重复：读 `references/anti-repeat-rules.md`
- 语言发硬、AI味重、气氛空泛：读 `references/language-governance.md`
- 需要固定输出格式：读 `references/output-contracts.md`
- 命中卷纲、反派、长期转场、感情线、结局等复杂场景：读 `references/advanced-template-map.md`

不要每次全量加载所有文件；只读取当前章节真正需要的上下文。

## 核心执行流程

### `/一键开书`

1. 明确题材、受众、平台倾向
2. 确定一句话卖点、主角反差、主线目标
3. 给出卷纲、阶段目标、黄金三章抓手
4. 初始化 `plan.md`、`state.md`，必要时补 `characters.md`

### `/写` 或 `/续写`

1. 读取 `plan.md` + `state.md`
2. 判断是否需要补读人物、时间线、伏笔、承诺文件
3. 先定义本章功能：推进主线 / 制造阻力 / 兑现爽点 / 埋设伏笔 / 回收伏笔 / 推进关系
4. 按章卡起草正文
5. 执行门禁检查，确认本章不是水章、重复章、断层章
6. 回填必要记忆文件

### `/修改` 或 `/改章`

1. 先标记必须保留的事实、伏笔、结果
2. 诊断问题归类：太水 / 爽点不足 / 人设不稳 / 节奏拖 / 信息过量 / 钩子弱 / 重复
3. 优先修最影响追读的问题，不先做表面润色
4. 修改后重新检查角色、时间线、伏笔状态和章尾钩子

## 连载门禁

### 必过项

- 没有违反 `plan.md` 红线
- 没有明显时间线冲突
- 角色动机与行为仍成立
- 当前卷或当前阶段在推进，而不是原地打转
- 本章有明确功能
- 本章有可感知的局面变化、结果反馈或新压力
- 本章至少推进了角色弧、关系弧、伏笔或承诺中的一项
- 章尾有继续阅读动力

### 阻断项

- 提前跳到下一卷或下一阶段关键节点
- 角色行为与既有人设严重冲突且无铺垫
- 连续多章拖欠同一核心承诺
- 关键关系连续停滞，没有新变化
- 近几章重复使用同一类桥段、爽点或钩子
- 解释性文字压过当前冲突
- 删掉本章后对后文几乎没有影响

## 语言闭环

涉及 `/写`、`/续写`、`/修改` 时，默认执行：

1. **Draft**：先写成立的剧情稿，只保证章节功能、角色行为、信息顺序正确。
2. **Audit**：检查作者式旁白、抽象堆词、强行气氛、重复句式、无效抒情。
3. **Rewrite**：只改语言，不改剧情功能；优先删空话、补感知、压重复、稳口吻。
4. **Recheck**：确认改写后，本章功能、伏笔、冲突、章尾钩子未受损。

若用户明确要求只给初稿，也要说明“未经过语言审计闭环”。

## 自动化脚本

```bash
python scripts/project_bootstrap.py --project "novel_书名"
python scripts/project_doctor.py --project "novel_书名"
python scripts/context_compiler.py --project "novel_书名" --chapter 12
python scripts/workflow_runner.py --project "novel_书名" --chapter 12
python scripts/toolchain_smoke.py
python scripts/chapter_gate.py --project "novel_书名" --chapter-no 12
python scripts/language_audit.py --project "novel_书名" --chapter-no 12 --mode suggest
python scripts/batch_gate.py --project "novel_书名" --from 1 --to 30 --json
python scripts/chapter_self_check.py --project "novel_书名" --chapter-no 10
```

默认理解：

- `templates/` 主要给人工阅读与使用
- `technique-kb/` 会被 `language_audit.py`、`chapter_gate.py` 等脚本自动消费
- `scripts/` 产出的报告优先于口头印象
- `toolchain_smoke.py` 用于校验技能仓库自身的工程链路，运行后不会留下测试目录
- `workflow_runner.py` 会额外生成 `05_reports/pipeline_report.{md,json}` 作为流水线总报告

## 对话侧常用指令

- `/一键开书`
- `/写`
- `/修改`
- `/续写`
- `/批量写 N`
- `/状态`
- `/卷节奏`
- `/弧进度`
- `/角色弧`
- `/人物 [名字]`
- `/伏笔`
- `/承诺`
- `/兑现`
- `/防重复`
- `/时间线`
- `/改章 第X章`
- `/重建大纲`
- `/定风格`
- `/校风格`

## 成功标准

- 新会话也能恢复写作状态
- 每章都能说清“这章在推进什么”
- 长线设定不轻易丢失
- 重复桥段能被及时识别
- 章尾普遍具备追读动力
- 爽点、情绪点、悬念点能周期性兑现
- 修章时能先定位故障，再动刀修改
