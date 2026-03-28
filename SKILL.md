---
name: chaseNovel
description: 当用户要策划、起稿、续写、改写或管理中文网文平台连载，并且关注章节节奏、章尾钩子、伏笔回收、设定连续性与追读留存时使用。
---

# 小说连载写作器

面向中文网文平台连载的小说创作技能。它不是“随手写一章”的轻量提示词，而是一套围绕**连载推进、设定一致、爽点节奏、伏笔回收、章节功能、断点恢复**构建的写作工作流。

## 概述

核心原则只有两个：

1. **连载优先于单章漂亮**：单章必须服务于“追读动力、角色推进、冲突升级、后续可持续写下去”。
2. **文件即记忆**：重要状态写入项目文件，不依赖当前对话上下文，保证断更、换会话、跨天续写仍可恢复。

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

固定输出模板、命令预期与成功标准已迁到 `references/output-contracts.md`，逻辑不变，只是不再在入口文件里整块加载。

---

## 参考导航

以下参考文档承接了原 `SKILL.md` 中的长规则、长模板与诊断说明；**内容没有删除，只是拆分加载**。

- `references/craft-and-platform.md`
  适合在以下情况补读：
  - `/开书`、开篇规划、黄金三章、番茄风格、题材节奏
  - 判断一章是否有效、章尾钩子是否成立、信息释放是否过量
  - 角色轮转、题材基线、风格模板、写作技巧导航
- `references/revision-and-diagnostics.md`
  适合在以下情况补读：
  - 剧情跑偏、角色失真、承诺拖欠、节奏拖沓
  - 疑似重复、桥段同质、钩子重复
  - `/修`、卡文、写不下去、知道问题但不知道从哪里修
- `references/output-contracts.md`
  适合在以下情况补读：
  - 需要 `/开书`、`/写`、`/续`、`/修` 等固定输出格式
  - 需要回看常见错误、风险信号、运行原则、成功标准
  - 想校验输出是否仍符合原技能的交付约定

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
- 题材写法扩展与技法库：`templates/genre-writing-guide.md`、`templates/writing-techniques.md`、`templates/writing_playbook.md`

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

- `/开书` 完成后，优先先落 `plan.md` 与 `state.md`
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
- `/开书`、黄金三章、番茄向抓人、题材节奏判断 → 读 `references/craft-and-platform.md`
- 漂移、重复、卡文、修章诊断 → 读 `references/revision-and-diagnostics.md`
- 固定输出模板、风险信号、成功标准 → 读 `references/output-contracts.md`
- 需要更细的题材技法、桥段写法、多视角控制、节奏小工具 → 读 `templates/writing_playbook.md`

不要每次全量加载所有文件；只读取当前章节真正需要的上下文。

---

## 写前流程

开始写任何章节前，按顺序完成：

1. 读取 `plan.md`
2. 读取 `state.md`
3. 判断当前所处：
   - 哪一卷
   - 哪一阶段
   - 当前主冲突
   - 本章的首要功能
4. 若当前卷目标、阶段目标或下一次爆点位置不清，补读 `arc_progress.md`
5. 检查承诺兑现压力：
   - 当前卷必须兑现什么
   - 哪个承诺已经拖到高风险
   - 本章是推进、预热还是暂时不能兑现
6. 检查角色推进压力：
   - 本章轮到谁变化
   - 哪段关系该推进或该制造裂痕
   - 是否会让关键人物失真或停滞
7. 检查红线：
   - 是否会提前推进关键节点
   - 是否会让人物动机失真
   - 是否会破坏已建立规则
   - 是否会重复最近 3-5 章的桥段体验
8. 判断是否需要补读：
   - 卷进度 / 人物 / 人物弧 / 伏笔 / 承诺 / 时间线 / 最近摘要 / 对应参考文档
9. 输出本章简要章卡：
   - 本章目标
   - 本章冲突
   - 本章爽点/情绪点
   - 本章必须保留的信息
   - 本章要推进的角色/关系弧
   - 本章对应的承诺推进或延后说明
   - 本章章尾钩子

如果这一步无法说清本章功能，先不要写正文。

---

## 起草规则

正文生成默认遵循：

- 先场景、后解释
- 先行动、后信息
- 先冲突、后设定
- 句子节奏服从题材
- 每章至少有一个“结果变化”
- 每章结尾优先保留钩子或新压力
- 对白必须推动关系、冲突或信息，不只是填字数
- 描写必须服务于气氛、人物、动作或情绪，不做无效铺陈

### 默认字数策略

若用户没有单独指定，单章以**适合连载平台阅读**为目标控制篇幅。原有 `2500-3500` 可作为默认参考，不视为绝对铁律；当题材、平台、阶段目标不同，可按用户要求调整。

---

## 写后流程

完成初稿后，按顺序处理：

1. 提取本章事实与变化
2. 更新章节摘要
3. 检查当前卷/阶段是否推进，必要时更新 `arc_progress.md`
4. 检查人物状态是否变化
5. 检查角色弧与关系弧是否推进，必要时更新 `character_arcs.md`
6. 检查时间线是否新增节点
7. 检查伏笔是否新增、推进或回收
8. 检查读者承诺是否新增、推进、延迟或兑现，必要时更新 `payoff_board.md`
9. 扫描重复风险
10. 扫描风格偏移
11. 扫描是否提前越过 `plan.md` 的关键节点
12. 判定是否触发周期自检：
   - `chapter_no % 10 == 0` → 触发**大自检**
   - `chapter_no % 5 == 0` 且不命中 10 → 触发**小自检**
   - 触发后先落自检报告，再继续批量写或确认下一章
13. 生成门禁产物（分级）：
   - **每章必做（轻量）**：更新 `state.md`、更新 `summaries/recent.md`、输出本章结果变化一句话总结
   - **仅当出现问题时才生成**：`consistency_report.md`、`repeat_report.md`、`style_report.md`
   - **仅在周期自检或用户要求时生成**：`proof_report.md`、`edit_report.md`、`result.json`
14. 若无问题：
   - 输出审核稿
   - 说明下一章方向
15. 若发现问题：
   - 明确失败原因
   - 指出需修项
   - 等待 `/修`

需要更细的漂移、重复、修章诊断时，补读 `references/revision-and-diagnostics.md`。

---

## 周期自检机制

### 触发规则

- 第 5 / 15 / 25 / 35 ... 章：执行一次**小自检**
- 第 10 / 20 / 30 / 40 ... 章：执行一次**大自检**
- 若同时命中 5 和 10，只做**大自检**，不重复跑两次
- `/批量写 N` 若跨过触发章，必须在触发章停住，先完成自检，再继续后续章节

### 小自检

适用于最近 5 章的轻量体检，重点看“有没有开始拖”“有没有开始重复”“有没有该还不还”。

必读：

- `plan.md`
- `state.md`
- `arc_progress.md`
- `payoff_board.md`
- `summaries/recent.md`
- 最近 5 章正文

必须回答：

- 最近 5 章是否都具备明确章节功能
- 最近 5 章是否至少有 2 次可感知小兑现或局面变化
- 是否出现连续 2 章以上弱反馈、平收或同类钩子
- 哪条角色弧 / 关系弧已经停滞
- 哪个承诺已进入高风险拖欠
- 下一章必须换哪种反馈路径

输出位置：

- `00_memory/self_checks/ch{NNN}_minor_self_check.md`

### 大自检

适用于最近 10 章的阶段体检，重点看“当前卷是不是还在往前走”“人物与承诺有没有集体失衡”。

必读：

- `plan.md`
- `state.md`
- `arc_progress.md`
- `character_arcs.md`
- `foreshadowing.md`
- `payoff_board.md`
- `timeline.md`
- `summaries/recent.md`
- 最近 10 章正文

必须回答：

- 当前卷 / 当前阶段是否仍在推进
- 最近 10 章的高低潮分布是否失衡
- 是否存在连续 3 章以上同质体验
- 哪些角色弧、关系弧已经停滞或失真
- 设定同步、伏笔状态、时间线是否仍然稳定
- 下个 10 章窗口必须兑现什么，否则会明显伤追读

输出位置：

- `00_memory/self_checks/ch{NNN}_major_self_check.md`

### 自动触发方式

优先使用本地脚本判定自检节点：

```bash
python scripts/chapter_self_check.py --project "novel_书名"
python scripts/chapter_self_check.py --project "novel_书名" --chapter-no 10 --json
```

执行要求：

- 正文确认写入后立刻运行一次
- 脚本若回报 `checkpoint_due=minor|major`，必须同步生成并填写对应自检报告
- 脚本会顺手刷新 `state.md` 中的“周期自检”状态块
- 若宿主支持 post-write / post-confirm hooks，可把此脚本直接挂上；不依赖特定 hook 平台

### Claude hooks 落点

- Hook 包装器：`hooks/posttooluse_chapter_self_check.py`
- Claude 配置片段：`hooks/claude-settings.local.json`
- 推荐接到 Claude 的 `PostToolUse`，匹配 `Edit|Write|MultiEdit`
- Hook 只在命中 `03_chapters/*.md` 时触发；改记忆文件、模板文件、普通文档不会误触
- 命中后由包装器反调 `scripts/chapter_self_check.py`，并传入 `--project <小说项目根目录>`

---

## 门禁检查

### 必过项

- 没有违反 `plan.md` 红线
- 没有明显时间线冲突
- 人物动机与行为仍成立
- 当前卷/当前阶段仍在推进，而不是原地打转
- 没有重复近章核心桥段或同类阅读体验
- 本章有明确功能
- 本章存在可感知推进
- 本章至少推进了一个角色弧、关系弧、伏笔或承诺中的一项
- 章尾具备继续阅读动力，或至少形成新问题/新压力

### 阻断项

出现以下任一情况，默认阻断：

- 提前进入下一卷/下一阶段关键节点
- 主要人物行为与既有人设严重不符，且无过渡
- 当前卷核心承诺长期拖欠，且本章既未兑现也未预热
- 关键角色或关键关系连续多章停滞，没有新的变化
- 同一爽点、桥段、钩子或关系拉扯路径在近几章重复使用
- 解释性内容过量，压过当前冲突
- 本章删掉后对后续几乎没有影响
- 章尾平收，没有结果、没有悬念、没有新压力

门禁之外的深度漂移 / 重复 / 修复策略，详见 `references/revision-and-diagnostics.md`。

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

- `/开书`
- `/写`
- `/修`
- `/续`
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

- 固定输出模板：详见 `references/output-contracts.md`
- 常见错误与风险信号：详见 `references/output-contracts.md`
- 默认运行原则与成功标准：详见 `references/output-contracts.md`

需要严格按旧版输出骨架工作时，直接补读该文件即可；原始模板与检查项全部保留。
