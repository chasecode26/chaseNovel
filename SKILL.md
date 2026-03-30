---
name: chaseNovel
description: 当用户要策划、起稿、续写、改写或管理中文网文平台连载，并且关注章节节奏、章尾钩子、伏笔回收、设定连续性与追读留存时使用。
---

# 小说连载写作器

面向中文网文平台连载的小说创作技能。它不是“随手写一章”的轻量提示词，而是一套围绕**连载推进、设定一致、爽点节奏、伏笔回收、章节功能、断点恢复**构建的写作工作流。

## 概述

核心原则有三个：

1. **连载优先于单章漂亮**：单章必须服务于“追读动力、角色推进、冲突升级、后续可持续写下去”。
2. **文件即记忆**：重要状态写入项目文件，不依赖当前对话上下文，保证断更、换会话、跨天续写仍可恢复。
3. **三级防冲突覆写协议 (Override Protocol)**：当各类设定出现矛盾时，绝对遵守：【第一级】作家指纹库与专有题材库（最高优先级） > 【第二级】本卷/本章核心大纲目标 > 【第三级】飞书通用爽文循环与大众润色基线。

---

## 适用场景

在以下场景使用本技能：

- 需要**开一本中文网文平台连载**
- 已有设定或已有章节，需要**继续推进平台连载的后续章节**
- 需要根据 `plan.md`、`state.md`、人物表、时间线等文件**恢复中文网文平台连载的写作状态**
- 需要处理**剧情跑偏、人物失真、章节太水、伏笔遗忘、节奏拖沓、重复桥段**
- 需要围绕**黄金三章、章尾钩子、爽点密度、追读保留**来优化平台连载写作
- 需要为玄幻/修仙、都市/系统流、种田、末世、甜宠、重生复仇等**中文网文常见题材**建立可持续推进的连载结构
- 需要在人工审核前，先做**一致性、重复度、节奏、风格、自检门禁**

## 不适用场景

以下情况不适合优先使用本技能：

- 只想写一段短篇灵感、诗歌、广告文案、朋友圈文案
- 只需要单次润色一句话，不关心长线设定
- 做文学评论、拆书分析、论文式分析，而不是推进创作
- 写作目标不是**中文网文平台连载**，而是传统出版小说、严肃文学、实验文本或一次性交付的短篇作品
- 用户明确要求“不要文件化记忆，不要连载约束，只要即时自由发挥”

---

## 任务路由

| 用户请求 | 任务类型 | 最小执行路径 |
|---|---|---|
| 帮我开一本新书 | 立项开书 | 题材定位 → 卖点/钩子 → 主线目标 → 角色结构 → 卷纲/阶段目标 |
| 给我世界观/人设/大纲 | 设定规划 | 明确题材与受众 → 建立核心冲突 → 输出可执行设定与阶段推进 |
| 写第X章/继续写 | 单章推进 | 读取 `plan.md` + `state.md` → 必要时补读相关记忆 → 明确本章功能 → 起草 → 门禁 |
| 续写断更内容 | 状态恢复 | 读取 `plan.md` + `state.md` + `findings.md` + 最近摘要 → 输出恢复结论 → 再写 |
| 这章太水了/改一下 | 改写修复 | 识别保留项 → 诊断问题类型 → 选择重写/压缩/补钩子/补冲突 |
| 人设崩了/剧情重复了 | 连载校准 | 扫描人物、摘要、伏笔、时间线 → 找冲突点 → 修正后续推进策略 |
| 看看现在写到哪了 | 状态查看 | 汇总当前卷、当前阶段、核心冲突、下一章目标 |
| 我要批量推进几章 | 连载推进 | 先确认阶段目标与边界 → 分章卡 → 逐章执行门禁，不跨越大纲红线 |
| 帮我回收伏笔 | 伏笔管理 | 读取 `foreshadowing.md` + 最近摘要 → 判断可回收窗口 → 设计兑现方式 |
| 改第X章但别动主线 | 定点修章 | 限定影响面 → 仅修改本章及必要记忆文件 → 标记受影响的后续章节 |

固定输出模板、命令预期与成功标准已迁到 `references/output-contracts.md` 与 `references/contracts/*.md`，逻辑不变，只是不再在入口文件里整块加载。

---

## 参考导航

以下参考文档承接了原 `SKILL.md` 中的长规则、长模板与诊断说明；**内容没有删除，只是拆分加载**。

- `references/craft-and-platform.md`
  适合在以下情况补读：
  - `/一键开书`、开篇规划、黄金三章、番茄风格、题材节奏
  - 判断一章是否有效、章尾钩子是否成立、信息释放是否过量
  - 角色轮转、题材基线、风格模板、写作技巧导航
- `references/revision-and-diagnostics.md`
  适合在以下情况补读：
  - 剧情跑偏、角色失真、承诺拖欠、节奏拖沓
  - 疑似重复、桥段同质、钩子重复
  - `/修改`、卡文、写不下去、知道问题但不知道从哪里修
- `references/output-contracts.md`
  适合在以下情况补读：
  - 需要 `/一键开书`、`/写`、`/续写`、`/修改` 等固定输出格式
  - 需要回看常见错误、风险信号、运行原则、成功标准
  - 想校验输出是否仍符合原技能的交付约定
  - 先看索引页，再按命令补读 `references/contracts/*.md`
- **新增：飞书强力打法专区**
  - `references/feishu_knowledge_summary.md`：需要了解长篇爽点循环法、开篇三幕式。
  - `references/tropes_library.md`：需要20个言情虐点公式或72个人设爆发点。
  - `references/suspense_techniques.md`：悬念怎么设，爽点怎么抛。

现有模板与辅助资源继续保留在 `templates/`、`scripts/`、`hooks/` 中，不做语义删减。

## 资源职责分工

为避免后续继续膨胀或出现双写冲突，默认按以下分工维护：

- `SKILL.md`：只保留触发后必须立刻知道的核心工作流、路由、门禁、自检与导航
- `references/`：保留长规则、长说明、长模板契约、诊断逻辑；按需补读，不在入口里重复展开
- `templates/`：保留实际产物模板、示例与题材化写法资产；当某项内容已经有模板或示例时，`references/` 只负责指路，不重复抄正文
- `scripts/`：保留自动化逻辑与可执行能力；流程里提到“自动判定 / 自动生成 / 自动回写”时，以脚本行为为准
- `hooks/`：保留宿主集成层；只负责把外部事件接进 `scripts/`，不承载业务规则本体

当前默认的唯一真相源如下：

- 周期自检规则与生成行为：`scripts/chapter_self_check.py`
- Claude 自动触发接线：`hooks/posttooluse_chapter_self_check.py` + `hooks/claude-settings.local.json`
- 记忆文件结构与字段骨架：`templates/plan.md`、`templates/state.md`、`templates/characters.md`、`templates/foreshadowing.md`、`templates/payoff-board.md` 等
- 章卡示例与长写法示例：`templates/chapter-card-examples.md`、`templates/writing-examples.md`
- 题材写法扩展与技法库：`templates/genre-writing-guide.md`、`templates/genres/*.md`、`templates/substyles/*.md`、`templates/writing-techniques.md`、`templates/writing_playbook.md`

---

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
│   ├── world.md
│   ├── timeline.md
│   ├── foreshadowing.md
│   ├── payoff_board.md
│   ├── style.md
│   ├── self_checks/
│   │   ├── ch005_minor_self_check.md
│   │   └── ch010_major_self_check.md
│   └── summaries/
│       ├── recent.md
│       ├── mid.md
│       └── archive/
├── 00_memory/retrieval/
│   ├── story_index.json
│   ├── entity_map.json
│   ├── next_context.md
│   └── retrieval_index.sqlite
├── 01_outline/
│   ├── seed.md
│   ├── blueprint.md
│   └── sprint/
├── 02_knowledge/
│   ├── worldbuilding.md
│   ├── power_system.md
│   ├── characters.md
│   ├── names.md
│   └── writing_playbook.md
├── 03_chapters/
│   ├── 第001章_XXXX.md
│   └── ...
└── 04_gate/
    └── ch{NNN}/
        ├── memory_update.md
        ├── consistency_report.md
        ├── repeat_report.md
        ├── style_report.md
        ├── proof_report.md
        ├── edit_report.md
        └── result.json
```

### 核心文件职责

- `plan.md`：全书主线、卷纲、红线规则、阶段目标
- `state.md`：当前推进位置、当前角色状态、当前冲突、下一章目标
- `findings.md`：临时发现、潜在线索、后续要跟进的问题
- `arc_progress.md`：当前卷、当前阶段、阶段目标、节奏压力、卷内兑现压力
- `characters.md`：角色资料、关系、秘密、动机、变化轨迹
- `character_arcs.md`：角色弧线推进、关系弧位置、下一次角色变化窗口
- `timeline.md`：时间顺序、关键事件、前后逻辑
- `foreshadowing.md`：伏笔埋设、状态、回收窗口
- `payoff_board.md`：读者承诺、兑现窗口、超期风险、卷内兑现优先级
- `style.md`：文风、句式、节奏、禁忌表达、题材偏好
- `self_checks/`：每 5 章 / 10 章的周期体检报告，记录节奏、重复、角色、承诺与纠偏动作
- `recent.md`：近章摘要，防重复、防错位、防遗忘

### 核心记忆文件最小模板

初始化项目时，不必从零空想，直接以模板起步：

- `plan.md` 最小模板：详见 `templates/plan.md`
- `state.md` 最小模板：详见 `templates/state.md`
- `characters.md` 最小模板：详见 `templates/characters.md`
- `foreshadowing.md` 最小模板：详见 `templates/foreshadowing.md`
- `payoff_board.md` 最小模板：详见 `templates/payoff-board.md`
- 长期风格模板：详见 `templates/style.md` 与 `templates/style-defaults.md`
- 周期自检模板：详见 `templates/self-check-small.md` 与 `templates/self-check-large.md`

### 初始化建议

- `/一键开书` 完成后，优先先落 `plan.md` 与 `state.md`
- 第 1 卷正式推进前，补 `characters.md`
- 开始埋线后，立即启用 `foreshadowing.md`
- 一旦出现“这书后面一定会写到”的期待，就记入 `payoff_board.md`
- 若风格开始漂，先回 `style.md` 校准，不要只改单章文字

---

## 最小读取策略

默认遵循“最小必要读取”。

### 必读

1. `00_memory/plan.md`
2. `00_memory/state.md`

### 按需补读

出现以下情况时再扩展读取范围：

- 进入新卷、阶段切换、觉得中盘发散 → 读 `arc_progress.md`
- 写到关键人物或关系推进 → 读 `characters.md`
- 判断角色是否该变化、关系是否该推进 → 读 `character_arcs.md`
- 写到世界规则/力量体系 → 读 `world.md` / `power_system.md`
- 涉及伏笔兑现 → 读 `foreshadowing.md`
- 涉及读者承诺兑现、怕爽点/情绪点拖欠 → 读 `payoff_board.md`
- 涉及前后事件对齐 → 读 `timeline.md`
- 觉得可能重复 → 读 `summaries/recent.md` + 最近 `repeat_report.md`
- 断更恢复/会话恢复 → 读 `findings.md` + `recent.md` + `next_context.md`
- 触发 5 章 / 10 章周期自检 → 读最近 `self_checks/` 与对应窗口内章节正文
- `/一键开书`、黄金三章、番茄向抓人、题材节奏判断 → 读 `references/craft-and-platform.md`
- 漂移、重复、卡文、修章诊断 → 读 `references/revision-and-diagnostics.md`
- 固定输出模板、风险信号、成功标准 → 先读 `references/output-contracts.md`，再按命令补读 `references/contracts/*.md`
- 需要具体题材的写法重点、失误清单与短对照范文 → 先读 `templates/genre-writing-guide.md`，再按题材补读 `templates/genres/*.md`
- 若是古代权谋里偏边关争霸、养兵夺权、黄袍加身的男频路线 → 补读 `templates/substyles/bianguan-zhengba-nanpin.md`
- 若平台目标偏番茄、需要每章更强的结果反馈和章尾钩子 → 补读 `templates/substyles/fanqie-kuai-fankui-shuangdian.md`
- 若主线里有克制、慢热、互相递刀的关系推进 → 补读 `templates/substyles/manre-gongmou-ganqingxian.md`
- 需要更细的题材技法、桥段写法、多视角控制、节奏小工具 → 读 `templates/writing_playbook.md`
- **面临极其复杂的高潮章、大型战斗、权谋局** → 强行挂载读 `templates/writing_playbook_multi_expert.md` (六大师专家模式)
- **初稿完成后需要润色，或被警告AI味太重** → 强行读取 `templates/vibe_check_prompt.md` 挨个排查
- **写到50万字以上感觉通货膨胀/战力崩坏时** → 警告：强制读取 `templates/power_economy_constraint.md`（锚点设计法、中期通胀手术、每卷健康检查）
- **面临大型换地图/更换大境界导致配角闲置时** → 强行读取 `templates/long_term_transition.md` 把不带走的人归档，设立遗留悬念
- **想要构建贯穿百万字的悬念或大反派** → 读取 `templates/shadow_rival_design.md` 设计一个伴随式的镜像宿主或倒计时压迫法则
- **设计/调整反派或感觉反派开始降智时** → 读取 `templates/antagonist_design.md`（反镜像法则、BOSS保鲜三条、配角四分类）
- **感情线停滞超过5章 / 写CP感提不起来 / 虐点/甜点节拍不对** → 读取 `templates/romance_arc.md`（六阶段节奏、三路线节拍、CP感写法铁律）
- **完全卡文写不下去，超过20分钟没有任何产出** → 读取 `references/break_writers_block.md`，先做症状自诊（A/B/C/D/E型），再对症取急救动作
- **全书完成度达到60%以上，准备规划结局** → 强制读取 `templates/ending_blueprint.md`（四种结局模型、章节结构规划、最后一句话设计法、结局前清单）

不要每次全量加载所有文件；只读取当前章节真正需要的上下文。

---

## 核心写作工作流 (Execution Workflow)

为保证整个控制中枢的极致精简，所有单章推进的底层机制（也就是你在实际执行写文时必须遵守的纪律）已经被全部打包到了专属外存。

在执行 `/写`、`/续写`、`/改章` 时，如果遇到流程卡壳，或不清楚怎么检查自己写的章节过不过关，强行补读：
👉 `references/execution_workflow.md`

此文件完整包含了以下五大机制：
1. **写前流程**：大纲对照、角色核验、章卡倒推。
2. **起草规则**：先动作后解释、潜台词占比、防AI味。
3. **写后流程**：记忆库自动刷新、伏笔勾销原则。
4. **门禁检查 (Gatekeeping)**：包含判定这章是不是“水文”、“太同质化”的阻断项。
5. **周期自检机制**：5章一小检防注水拖节奏，10章一大检防主线人物崩盘的硬性规则。

---

## 快速参考

### 常用命令

```bash
python novel-writor/scripts/novel_writor.py init --title "书名" --genre "玄幻/修仙"
python novel-writor/scripts/novel_writor.py gate --project "novel_书名" --chapter "draft.md" --chapter-no 1
python novel-writor/scripts/novel_writor.py confirm --project "novel_书名" --chapter-no 1
python novel-writor/scripts/novel_writor.py index --project "novel_书名"
python novel-writor/scripts/novel_writor.py context --project "novel_书名" --chapter "draft.md" --chapter-no 2
python novel-writor/scripts/novel_writor.py search --project "novel_书名" --q "某个角色名"
python novel-writor/scripts/novel_writor.py resume --project "novel_书名"
python novel-writor/scripts/novel_writor.py pack --project "novel_书名" --chapter-no 2 --extra "本章节奏：升；重点回收一个伏笔"
python scripts/chapter_self_check.py --project "novel_书名" --chapter-no 5
python scripts/chapter_self_check.py --project "novel_书名" --json
python hooks/posttooluse_chapter_self_check.py
```

### 对话侧常用指令

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
- `/拆书`
- `/定风格`
- `/校风格`

---

## 输出与校验约定

- 固定输出模板：先读 `references/output-contracts.md`，再按命令补读 `references/contracts/*.md`
- 常见错误与风险信号：详见 `references/output-contracts.md`
- 默认运行原则与成功标准：详见 `references/output-contracts.md`

需要严格按旧版输出骨架工作时，先读索引页，再只补读当前命令对应的 contract 文件；原始模板与检查项全部保留。
