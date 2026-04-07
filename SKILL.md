---
name: chaseNovel
description: 当用户要策划、起稿、续写、改写或管理中文网文平台连载，并且关注章节节奏、章尾钩子、伏笔回收、设定连续性、角色推进与追读留存时使用。
---

# 小说连载写作器

面向中文网文平台连载的写作技能。它不是“随手写一章”的轻量提示词，而是一套围绕**连载推进、文件化记忆、章节功能、伏笔回收、节奏控制、修章校准**构建的工作流。

## 快速入口

- 开书：先走 `/一键开书`，只看“核心原则”“任务路由”“资源导航”，再下钻到 `references/craft-and-platform.md`
- 写章 / 续写：先看“写前锚定包”“核心执行流程”“连载门禁”，再按需读 `references/execution_workflow.md`
- 改章：先看“任务路由”“复核冲突裁决顺序”“语言闭环”，再读 `references/revision-and-diagnostics.md`
- 项目体检：优先跑 `chase doctor --project <dir>`；要做整套干跑检查，跑 `chase check --project <dir> [--chapter <n>]`

默认不要求从头读完整份 `SKILL.md`。先按任务命中入口，再扩读相关专题。
跨任务规则与表达标准，统一看 `references/output-contracts.md` 和 `references/execution_workflow.md`。

## 核心原则

1. **连载优先于单章漂亮**：单章必须服务于追读动力、角色推进、冲突升级与后续可持续连载。
2. **文件即记忆**：重要状态写入项目文件，不依赖当前对话上下文，保证断更、换会话、跨天续写仍可恢复。
3. **先保结构，再修语言**：先确认章节功能、信息顺序、角色动机成立，再做润色与语言修正。
4. **默认说大白话**：默认把谁在做事、为什么做、结果变了什么写明白，不故作高深，不靠隐晦句子装气氛。
5. **按需读取，不机械全读**：默认只读当前任务需要的上下文；只有在长线伏笔、跨卷冲突、时间线校验明确相关时，才扩展读取范围。
6. **默认走显式多 Agent 编排**：开书可轻量，续写、写章、修章默认显式拆成“规划 / 正文 / 并行复核”三层执行，不允许只靠单线程感觉检查。
7. **先锚定事实，再动正文**：续写前必须先锚定当前时间、地点、在场人物、资源状态、未回收伏笔与上一章结果；缺锚点时先补记忆文件，不允许靠猜。
8. **防幻读高于行文流畅**：正文里出现任何“记忆文件未写、前文未落、当前章无依据”的信息，默认按幻读处理，必须回退。
9. **笔风稳定是硬指标**：语言不只看顺不顺，还要查是否机械过渡、概括腔、均质对白、作者代角色发言；AI 味压过题材口吻时直接阻断。
10. **悬疑只准局部留白**：只有悬疑、探案、反转前夜等需要保信息差的节点，才允许故意藏一截；平常章节不准整段说虚话。
11. **先过规划门槛，再写正文**：全书规划与章节规划都必须先过审；规划不过稿，不进正文。
12. **质量高于 token 与文件大小**：只要能明显提高成稿质量，允许扩读、扩审、扩写前规划，不因为流程变重而跳过关键检查。
13. **红线问题一票否决**：时间线错乱、人设硬崩、无依据新设定、应触发布置失忆、承诺拖欠成水文、AI 味压过题材口吻，任一命中都先返工。
14. **默认大白话直给**：先写事实，再写判断，再写后果；能直接说清的，不写成谜语句或术语句。
15. **章节长度受控**：常规章默认 `2300-3500` 字，高潮章可到 `4500`；字数不服务质量时，先改结构，不靠硬凑。


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

## 显式多 Agent 编排

默认不是“一个人脑内全包”，而是显式拆成多个角色协同；总审查由 `Reviewer` 收口，专项审查默认并行执行，而不是写完后凭印象口头自检。

### 默认 Agent

- `Planner`：卖点、路线、章卡、卷目标
- `Worldbuilder`：规则、术语、考据口径、世界边界
- `Character`：人物动机、关系变化、反工具人
- `HookEmotion`：情绪曲线、章尾钩子、爽点密度、收束换挡
- `StructureReviewer`：开头抓力、主角入场、冲突递进、章尾钩子是否真能带起下一章
- `RhythmReviewer`：哪里拖、哪里在讲不是在打、哪里该爆没爆、哪里重复同一种压法
- `StyleDialogue`：对话口吻、旁白硬度、角色说话区分、台词是否需要读者二次翻译
- `LanguageReviewer`：AI 味、机械过渡、解释味、信息搬运感、虚描述
- `StyleConsistencyReviewer`：单书 voice DNA、叙述节拍、角色声口、章节间风格漂移
- `ContinuityReviewer`：世界规则、时间线、伏笔、承诺、布置连续性
- `CausalityReviewer`：转折前提、人物决策、结果落地、后账合理性
- `ResearchMaterial`：资料抽读、考据压缩、本地语料转写、题材规则卡
- `Writer`：正文落地
- `Reviewer`：门禁、重复、连续性、承诺拖欠、回退决策

### Codex 子 Agent 映射

- `Planner` -> `planner`
- `Worldbuilder` -> `architect`
- `Character` -> `analyst`
- `HookEmotion` -> `writer`
- `StructureReviewer` -> `critic`
- `RhythmReviewer` -> `critic`
- `StyleDialogue` -> `writer`
- `LanguageReviewer` -> `code-reviewer`
- `StyleConsistencyReviewer` -> `critic`
- `ContinuityReviewer` -> `critic`
- `CausalityReviewer` -> `critic`
- `ResearchMaterial` -> `researcher`
- `Writer` -> `writer`
- `Reviewer` -> `critic`

默认要求：
- `/写`、`/续写`、`/修改` 若启用本技能，默认按上表显式拉起 Codex 子 agent
- 若运行环境无法显式拉起子 agent，必须按同一角色顺序手动执行，并在最终说明中标注“未实际拉起子 agent，只按同等检查项执行”

### 默认编排

- `/一键开书`：`Planner -> Character -> Worldbuilder -> Reviewer`
- `/写`：`Planner -> HookEmotion -> Writer -> [StructureReviewer || RhythmReviewer || StyleDialogue || LanguageReviewer || StyleConsistencyReviewer || ContinuityReviewer || CausalityReviewer || Reviewer] -> Writer/Planner 修正 -> Reviewer 收口`
- `/续写`：`Planner -> HookEmotion -> Writer -> [StructureReviewer || RhythmReviewer || StyleDialogue || LanguageReviewer || StyleConsistencyReviewer || ContinuityReviewer || CausalityReviewer || Reviewer] -> Writer/Planner 修正 -> Reviewer 收口`
- `/修改`：`Reviewer -> Planner -> HookEmotion -> Writer -> [StructureReviewer || RhythmReviewer || StyleDialogue || LanguageReviewer || StyleConsistencyReviewer || ContinuityReviewer || CausalityReviewer] -> Writer 修正 -> Reviewer 收口`

### 并行复核硬规则

- `/写`、`/续写`、`/修改` 默认必须显式拉起并行复核，不再把 `StyleDialogue`、`LanguageReviewer`、`StyleConsistencyReviewer`、`ContinuityReviewer`、`CausalityReviewer` 当可有可无的附加项
- `Planner` 默认必须给出 `chapter_tier` 与 `target_word_count`
- 开篇 `1-10` 章额外要求 `Reviewer` 参与并行复核，专门检查：
  - 章功能是否重复
  - 冲突类型是否重复
  - 结果类型是否重复
  - 钩子类型是否重复
- 若并行复核中有任一 reviewer 指出“同一节点重复推进”或“结果重复但无升级”，默认不得直接交稿，必须先修
- 若当前环境无法真正拉起子 agent，必须串行模拟全部 reviewer，并显式输出各 reviewer 结论，不得合并成一句混合评价
- 允许串行只限：
  - `/一键开书`
  - 极短的单段润色
  - 用户明确要求“只给草稿，不做复核”

### 并行复核固定输出

每个复核 agent 默认必须交回以下字段，缺一项视为复核不完整：

- `chapter_function`：本章章功能
- `conflict_type`：本章冲突类型
- `result_type`：本章结果类型
- `hook_type`：本章章尾钩子类型
- `findings`：本 agent 发现的问题
- `blocking`：是否阻断交稿，`yes/no`
- `suggested_fix`：若阻断，最小修法是什么

`Reviewer` 额外必须交：
- `repeat_window`：对照了哪几章
- `upgrade_point`：本章相较前章的升级点是什么；若答不出，默认阻断

### 写前锚定包

`Planner` 在 `/写`、`/续写`、`/修改` 开始前，必须先产出一个最小锚定包，再交给 `Writer`：

- `time_anchor`：当前绝对/相对时间，是否跨天，和上一章的间隔
- `location_anchor`：本章主要场景，人物移动边界
- `present_characters`：本章在场人物、旁听人物、缺席但会被提及的人物
- `knowledge_boundary`：每个核心人物此刻“知道 / 不知道 / 误以为”的事
- `resource_state`：钱、粮、地、水、工具、人手、伤病、债务等本章要动到的资源现状
- `open_threads`：本章允许触碰的伏笔、承诺、关系张力、后账
- `forbidden_inventions`：本章不允许凭空新增的设定、结果、情报

缺任一项时，不进入正文起草。

### 复核冲突裁决顺序

当不同复核 agent 意见冲突时，统一按以下优先级裁决：

1. `ContinuityReviewer` / `CausalityReviewer` 的硬伤
2. `Reviewer` 的重复推进 / 递进失效结论
3. `HookEmotion` 的节奏与钩子结论
4. `StyleDialogue` / `LanguageReviewer` 的语言与口吻建议

执行规则：
- 高优先级结论可以覆盖低优先级修法
- 低优先级修法若会破坏高优先级成立条件，默认丢弃
- 若 `ContinuityReviewer` 与 `CausalityReviewer` 同时阻断，先修因果与连续性，再回头修语言

### 开篇专用检查模板

开篇 `1-10` 章除常规复核外，默认再跑三张专用卡：

1. `黄金三章检查卡`
   - 第1章是否只负责抓死局与立问题
   - 第2章是否真正开始新行动
   - 第3章是否建立长期活路承诺
2. `递进防重复检查卡`
   - 相邻两章是否在推进同一节点
   - 相邻两章是否在拿同一结果
   - 相邻两章是否只是换说法，不换结构结果
3. `资源闭环检查卡`
   - 本章有没有把地 / 水 / 种 / 窑 / 换物中的至少一项推进成新结果
   - 本章有没有让“活路”比上一章更具体

### 什么时候加 Agent

- 设定密度高、术语多：加 `Worldbuilder`
- 群像、关系线、配角容易空：加 `Character`
- 钩子弱、情绪跳、爽点不足：加 `HookEmotion`
- 对话发空、旁白发硬、角色说话撞车：`StyleDialogue` 默认并行参与
- AI 味重、机械过渡多、解释味重：`LanguageReviewer` 默认并行参与
- 单书 voice 漂移、节拍飘、角色声口失真：`StyleConsistencyReviewer` 默认并行参与
- 世界观密、伏笔多、时间线容易打架：`ContinuityReviewer` 默认并行参与
- 转折多、博弈重、怕剧情硬推：`CausalityReviewer` 默认并行参与
- 历史、盗墓、权谋、修仙等资料依赖题材：加 `ResearchMaterial`
- 开篇三章、批量写作、大修：必须保留 `Reviewer`
- 开篇十章内续写：必须把 `Reviewer` 放入并行复核组，专查重复推进和递进失效

详细交接规则见：`references/agent-collaboration.md`

## 资源导航

入口文件只保留核心流程；长规则、模板与诊断说明拆到 `references/`、`templates/` 与 `scripts/`。

- `references/genre-asset-index.md`
  - 六条核心题材的一页式总索引，先判断该读哪份，再下钻到具体专项
- `references/craft-and-platform.md`
  - 开书、黄金三章、题材节奏、章尾钩子、平台追读逻辑
- `references/execution_workflow.md`
  - 写前准备、写中纪律、写后回填、章节门禁、阶段复盘
- `references/revision-and-diagnostics.md`
  - 卡文、修章、重复桥段、人物失真、节奏拖沓、承诺拖欠
- `references/language-governance.md`
  - 旁白治理、气氛落地、题材口吻、语言改写边界
- `references/chapter-emotion-and-ai-check.md`
  - 单章写作前后的情绪曲线与 AI 味自检，专门处理情绪跳跃、机械过渡、过度总结和对白发空
- `references/title-and-selling.md`
  - 书名、标题、一句话卖点与平台表达的压缩规则，专门处理“书名空、卖点虚、简介不抓人”
- `references/agent-collaboration.md`
  - 轻量真 agent 协同协议，固定 Planner / Worldbuilder / Character / HookEmotion / StyleDialogue / LanguageReviewer / ContinuityReviewer / CausalityReviewer / ResearchMaterial / Writer / Reviewer 的触发条件、交接顺序与回写要求
- `references/output-contracts.md`
  - `/一键开书`、`/写`、`/续写`、`/修改` 等固定输出骨架
- `references/contracts/07-research-material.md`
  - `ResearchMaterial` 的资料压缩卡，专门把抽读结果压成 Writer 可直接消费的规则、术语和场景材料
- `references/writing-patterns.md`
  - 章节落地手法、动作化表达、低 AI 味修法
- `references/opening-sample-library.md`
  - 高质量作品第一章样本库，用来校准开篇路线、信息顺序与卖点建立
- `references/opening-sample-specialties.md`
  - 历史权谋、末世囤货、仙侠苟道等偏好题材的开篇样本专题
- `references/local-corpus-learning.md`
  - 从本地下载小说语料中提炼出来的结构化学习笔记，补充历史权谋/边境战争、末世囤货、仙侠苟道的实战开篇打法
- `references/local-corpus-priority-map.md`
  - 本地下载语料的优先级地图，先判断该抽哪本、学哪段、提炼哪类结构
- `references/daomu-writing-notes.md`
  - 盗墓 / 摸金 / 民国奇诡题材的最小实战笔记，专门处理开篇入局、墓里危险、墓外后账和术语口径
- `references/historical-midgame-learning.md`
  - 历史权谋 / 边境战争的中盘推进专项，专门处理 10 章以后如何防塌、防水、防重复
- `references/historical-command-and-aftermath-library.md`
  - 历史权谋 / 边境战争的将领关系与战后后账专项，专门处理军令、军功、违令、封赏与清算
- `references/historical-relationship-card-deck.md`
  - 历史权谋 / 边境战争的人物关系卡组，快速处理皇帝、监军、宿将、先锋、粮官、地方官、台谏等关系变质
- `references/historical-military-political-chapter-card-library.md`
  - 历史权谋 / 边境战争的军政冲突章卡群，直接处理监军、粮官、地方官、朝使与军中体系互卡的场景
- `references/historical-character-learning.md`
  - 历史权谋 / 边境战争的人物弧与阵营关系专项，专门处理主角、部将、君臣、盟友的动态变化
- `references/historical-chapter-card-library.md`
  - 历史权谋 / 边境战争的章节卡样例库，直接给可落地的军议、朝堂、粮道、背刺、违令等章卡骨架
- `references/historical-volume-route-library.md`
  - 历史权谋 / 边境战争的卷级路线库，处理一卷该换什么、如何接下一卷、如何避免换皮重复
- `references/historical-negative-patterns.md`
  - 历史权谋 / 边境战争的反套路黑名单，专门识别空朝堂、假战争、死关系、单一爽点
- `references/hook-result-learning.md`
  - 末世囤货 / 仙侠苟道的结果路线与章尾钩子专项，用于中盘换挡和收束升级
- `references/moshi-bastion-and-order-library.md`
  - 末世囤货的据点升级与秩序治理专项，专门处理安全屋升级、规则建立、势力治理与秩序重建
- `references/moshi-bastion-governance-chapter-cards.md`
  - 末世囤货的据点治理章卡群，直接处理新人准入、资源分配、规则处罚、对外交易、扩张与闹营
- `references/moshi-volume-route-library.md`
  - 末世囤货的卷级路线库，处理囤货、守点、清算、势力碰撞、秩序重建的长期推进
- `references/moshi-character-learning.md`
  - 末世囤货的人物弧与团队关系专项，处理主角、队友、仇人、规则的动态变化
- `references/moshi-chapter-card-library.md`
  - 末世囤货的章节卡样例库，直接给抢购、安全屋、清算、团队裂痕、势力试探等章卡骨架
- `references/moshi-negative-patterns.md`
  - 末世囤货的反套路黑名单，专门识别囤货流水账、邻居反复送脸、团队假和谐
- `references/goudao-volume-route-library.md`
  - 仙侠苟道的卷级路线库，处理凡人入局、避险发育、伪装潜伏、机缘取舍与反噬升级
- `references/goudao-character-learning.md`
  - 仙侠苟道的人物弧与关系专项，处理风险判断、互防关系、因果与安全边界变化
- `references/goudao-chapter-card-library.md`
  - 仙侠苟道的章节卡样例库，直接给避险入局、小机缘、伪装潜伏、机缘取舍、安全区失效等章卡骨架
- `references/goudao-negative-patterns.md`
  - 仙侠苟道的反套路黑名单，专门识别假苟道、停剧情、空机缘、旧安全区不失效
- `references/dushi-volume-route-library.md`
  - 都市系统流的卷级路线库，处理低位反压、资源起势、身份揭面、规则碾压、上层碰撞
- `references/dushi-character-learning.md`
  - 都市系统流的人物弧与关系专项，处理主角升级、配角再估值、站队变化与关系后账
- `references/dushi-chapter-card-library.md`
  - 都市系统流的章节卡样例库，直接给会议打脸、身份揭面、规则反制、上层试探等章卡骨架
- `references/dushi-negative-patterns.md`
  - 都市系统流的反套路黑名单，专门识别重复装穷打脸、系统播报流水账、围观震惊式爽点
- `references/zhongtian-volume-route-library.md`
  - 种田文的卷级路线库，处理站稳脚跟、产业成形、村镇扩张、关系共建、外部冲击
- `references/zhongtian-character-learning.md`
  - 种田文的人物弧与关系专项，处理主角承担、合作关系、家族与共同体变化
- `references/zhongtian-chapter-card-library.md`
  - 种田文的章节卡样例库，直接给收成、合作、产业升级、天灾应对等章卡骨架
- `references/zhongtian-negative-patterns.md`
  - 种田文的反套路黑名单，专门识别电子账本推进、假平静、关系纸片化
- `references/anti-repeat-rules.md`
  - 重复桥段、重复反馈、重复钩子的专项排查与换法
- `references/advanced-template-map.md`
  - 反派、卷纲、长期转场、感情线、结局等高阶模板导航
- `templates/`
  - 项目记忆模板、章卡示例、题材写法、长期规划辅助模板
  - 其中 `templates/opening-route-cheatsheet.md` 用于 `/一键开书` 前快速选定第一章路线
  - 其中 `templates/golden-three-route-cheatsheet.md` 用于把开篇路线扩成黄金三章功能链
  - 其中 `templates/hook-route-cheatsheet.md` 用于 `/写` 前快速选定章尾钩子路线
  - 其中 `templates/result-route-cheatsheet.md` 用于 `/写` 前快速决定本章结果类型
  - 其中 `templates/midgame-fatigue-cheatsheet.md` 用于卷中段诊断疲劳并主动换挡
  - 其中 `templates/character-voice-diff.md` 用于 `StyleDialogue` 拉开角色说话差分，避免对白撞车
  - 其中 `templates/reviewer-stage-retro.md` 用于 `Reviewer` 做阶段复盘，只回写疲劳点、重复点、拖欠承诺和纠偏动作
  - 其中 `templates/language-anti-ai-review.md` 用于 `LanguageReviewer` 查机械过渡、解释味和信息搬运感
  - 其中 `templates/continuity-review-card.md` 用于 `ContinuityReviewer` 查世界观、时间线、伏笔、承诺和布置连续性
  - 其中 `templates/causality-review-card.md` 用于 `CausalityReviewer` 查转折前提、人物决策和结果合理性
  - 题材模板当前保留 6 条高频主战题材：玄幻/修仙、都市/系统流、种田文、末世、历史/权谋、盗墓/摸金
  - 子风格模板当前保留 3 条仍有明确入口的叠加风格：边关争霸男频、番茄快反馈、慢热共谋感情线
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

“最小读取”只是一条默认效率策略，不是质量豁免。只要出现以下任一情况，立刻扩读，不得继续靠猜：

- 章节规划预审答不清
- 连续性或因果 reviewer 命中阻断项
- 本章要动用旧伏笔、旧布局、资源链、身份链、关系后账
- 本章看似能写，但说不清为什么它必须存在

默认遵循“最小必要读取”。

### 必读

1. `00_memory/plan.md`
2. `00_memory/state.md`

### 续写硬性补读

涉及 `/写`、`/续写`、`/修改` 时，默认再强制读：

1. `00_memory/timeline.md`
2. `00_memory/character_arcs.md`

若当前章直接调用伏笔、资源账、本地术语或关系后账，再补读对应文件；不要凭“应该还记得”直接开写。

### 按需补读

- 进入新卷、阶段切换、中盘发散：读 `arc_progress.md`
- 关键人物或关系推进：读 `characters.md`、`character_arcs.md`
- 涉及世界规则、力量体系：优先补写或扩展 `00_memory/plan.md`、`00_memory/findings.md`，必要时自建世界观文件
- 涉及大量术语、世界观模块多、真实考据词容易写混：新建或补读 `worldbuilding-index.md`
- 涉及伏笔兑现：读 `foreshadowing.md`
- 涉及读者承诺兑现：读 `payoff_board.md`
- 涉及前后事件对齐、回忆、跳时：强制读 `timeline.md`
- 断更恢复：读 `findings.md` + `summaries/recent.md`
- 怀疑桥段重复：读最近摘要与最近 `repeat_report.md`
- 开书、黄金三章、平台节奏：读 `references/craft-and-platform.md`
- 开篇总是平、第一章卖点不立、想参考成熟作品入口：读 `references/opening-sample-library.md`
- 开篇题材很明确，且偏历史权谋、末世囤货、仙侠苟道：补读 `references/opening-sample-specialties.md`
- 用户明确要求“按本地下载小说学习”或需要吸收外部样本但不落原文：读 `references/local-corpus-learning.md`
- 书名起不住、卖点太虚、简介像空话：读 `references/title-and-selling.md`
- 用户手头有一批本地下载小说，但不知道先读哪本最值：读 `references/local-corpus-priority-map.md`
- 盗墓、摸金、民国奇诡题材要开书，或已经写成重复副本：读 `references/daomu-writing-notes.md`
- 历史权谋、边境战争写到中段开始发散、重复、空转：读 `references/historical-midgame-learning.md`
- 历史权谋、边境战争的人物关系开始僵、部将只会听令、君臣线没有试探：读 `references/historical-character-learning.md`
- 历史权谋、边境战争知道要推人物关系，但一到具体角色对就不知道怎么变质：读 `references/historical-relationship-card-deck.md`
- 历史权谋、边境战争开始只会“军议 -> 出兵 -> 大胜”，不会写军令、军功、违令、封赏后账：读 `references/historical-command-and-aftermath-library.md`
- 历史权谋、边境战争已经知道方向，但不会把一章真正落成可写章卡：读 `references/historical-chapter-card-library.md`
- 历史权谋、边境战争会写大战，不会写监军、粮官、地方官、朝使与边军互卡的一章：读 `references/historical-military-political-chapter-card-library.md`
- 历史权谋、边境战争已经能写单章，但整卷开始换皮重复：读 `references/historical-volume-route-library.md`
- 历史权谋、边境战争总像老三样，朝堂假、战争空、爽点单一：读 `references/historical-negative-patterns.md`
- 末世囤货、仙侠苟道不知道本章该怎么收、怎么换结果、怎么挂钩子：读 `references/hook-result-learning.md`
- 末世囤货已经能写开篇，但整卷只会囤货、守屋、打邻居循环：读 `references/moshi-volume-route-library.md`
- 末世囤货已经有据点和团队，但不会继续写规则、治理、势力和秩序升级：读 `references/moshi-bastion-and-order-library.md`
- 末世囤货团队像工具人、仇人只会送脸：读 `references/moshi-character-learning.md` 与 `references/moshi-negative-patterns.md`
- 末世囤货知道方向，但不会落成可写章卡：读 `references/moshi-chapter-card-library.md`
- 末世囤货会写生存危机，但不会把准入、分配、处罚、交易、扩张、闹营真正落成一章：读 `references/moshi-bastion-governance-chapter-cards.md`
- 仙侠苟道写着写着变成拖节奏、假苟道、白捡机缘：读 `references/goudao-volume-route-library.md` 与 `references/goudao-negative-patterns.md`
- 仙侠苟道知道原则，但不会落成具体章节推进：读 `references/goudao-chapter-card-library.md`
- 仙侠苟道人物关系只有远离和信任两档，不会写互防、借力、因果：读 `references/goudao-character-learning.md`
- 都市系统流已经能写开篇，但整卷只会装弱打脸循环：读 `references/dushi-volume-route-library.md`
- 都市系统流配角只会送脸、围观、震惊：读 `references/dushi-character-learning.md` 与 `references/dushi-negative-patterns.md`
- 都市系统流知道方向，但不会落成可写章卡：读 `references/dushi-chapter-card-library.md`
- 种田文已经能写积累感，但整卷只会种、卖、赚、扩：读 `references/zhongtian-volume-route-library.md`
- 种田文人物关系太平、合作线太纸：读 `references/zhongtian-character-learning.md` 与 `references/zhongtian-negative-patterns.md`
- 种田文知道方向，但不会落成可写章卡：读 `references/zhongtian-chapter-card-library.md`
- 第一章能抓人，但第二三章容易发散：读 `templates/golden-three-route-cheatsheet.md`
- 不知道本章怎么收尾、章尾总平、钩子连续重复：读 `templates/hook-route-cheatsheet.md`
- 不知道本章该给哪种结果、总像上一章那套：读 `templates/result-route-cheatsheet.md`
- 进入 10 章以后开始同质化：读 `templates/midgame-fatigue-cheatsheet.md`
- 修章、卡文、人物失真、重复：读 `references/revision-and-diagnostics.md`
- 想把结构写得更抓人、更自然：读 `references/writing-patterns.md`
- 怀疑桥段、反馈、钩子重复：读 `references/anti-repeat-rules.md`
- 语言发硬、AI味重、气氛空泛：读 `references/language-governance.md`
- 章节情绪跳跃、高点不成立、写完像信息搬运：读 `references/chapter-emotion-and-ai-check.md`
- 书名、标题、一句话卖点总发空：读 `references/title-and-selling.md`
- 需要固定输出格式：读 `references/output-contracts.md`
- 命中卷纲、反派、长期转场、感情线、结局等复杂场景：读 `references/advanced-template-map.md`

不要每次全量加载所有文件；只读取当前章节真正需要的上下文。

## 核心执行流程

### `/一键开书`

默认编排：`Planner -> Character -> Worldbuilder -> Reviewer`

资料依赖题材可扩展为：`Planner -> ResearchMaterial -> Character -> Worldbuilder -> Reviewer`

1. 明确题材、受众、平台倾向
2. 先用 `templates/opening-route-cheatsheet.md` 选第一章路线；若用户未指定，按题材 > 卖点 > 当前压力源自动推荐
3. 再用 `templates/golden-three-route-cheatsheet.md` 把第一章路线扩成前三章功能链；若用户未指定，按开篇主路线 > 核心卖点 > 平台节奏自动推荐
4. 确定一句话卖点、主角反差、主线目标
5. 给出卷纲、阶段目标、黄金三章抓手
6. 初始化 `plan.md`、`state.md`，必要时补 `characters.md`

### `/写` 或 `/续写`

默认编排：`Planner -> HookEmotion -> Writer -> 并行复核组 -> Writer/Planner 修正 -> Reviewer 收口`

并行复核组默认包含：
- `StyleDialogue`
- `LanguageReviewer`
- `ContinuityReviewer`
- `CausalityReviewer`
- `Reviewer`

1. 读取 `plan.md` + `state.md`
2. 强制读取 `timeline.md` + `character_arcs.md`，再按需补读人物、伏笔、承诺、术语文件
3. 先输出“写前锚定包”，确认当前时间、地点、在场人物、知情边界、资源状态、开放线程
4. 若记忆文件之间互相冲突，先修记忆文件或先做校准说明，不允许带冲突直接起草
5. 先定义本章功能：推进主线 / 制造阻力 / 兑现爽点 / 埋设伏笔 / 回收伏笔 / 推进关系
6. 若用户未指定章尾钩子，先按 `templates/hook-route-cheatsheet.md` 基于本章功能 > 当前压力源 > 题材惯性自动推荐
7. 按章卡起草正文；正文不得写出锚定包之外的新知情、新资源、新时间跳跃
8. 显式并行分发复核：
   - `StyleDialogue`：只查对白口吻、旁白硬度、角色说话差分
   - `LanguageReviewer`：只查 AI 味、机械过渡、解释味、概括腔、同质句法
   - `ContinuityReviewer`：只查时间线、伏笔、设定、状态连续性、知情边界是否越线
   - `CausalityReviewer`：只查转折前提、行为动机、结果落地
   - `Reviewer`：专查章功能、冲突类型、结果类型、钩子类型是否与近 `3-5` 章重复
9. 汇总并行复核结论，若命中重复推进、断层、知情越界、时间漂移、资源漂移、AI 味过重，先修正再收口
10. 回填必要记忆文件

### `/修改` 或 `/改章`

默认编排：`Reviewer -> Planner -> HookEmotion -> Writer -> 并行复核组 -> Writer 修正 -> Reviewer 收口`

1. 先标记必须保留的事实、伏笔、结果
2. 先补齐“写前锚定包”，明确哪些事实能改、哪些事实只能顺接不能重写
3. 诊断问题归类：太水 / 爽点不足 / 人设不稳 / 节奏拖 / 信息过量 / 钩子弱 / 重复 / 幻读 / 时间线漂移 / AI 味重
4. 优先修最影响追读和连续性的问题，不先做表面润色
5. 修改后必须再次并行检查角色、时间线、伏笔状态、章尾钩子、知情边界和重复推进

### 复核后回写闭环

复核不是口头建议，默认要写回项目记忆：

- 重复推进 / 递进失效 -> `findings.md`
- 当前阶段节奏风险 / 下一章提醒 -> `state.md`
- 长线承诺或阶段目标受影响 -> `plan.md`
- 伏笔窗口变化 -> `foreshadowing.md`
- 时间顺序变化 -> `timeline.md`
- 人物关系或分工变化 -> `character_arcs.md`

若只是语言层问题，可不强制回写记忆文件；其余结构问题默认必须回写。

## 连载门禁

### 必过项

- 没有违反 `plan.md` 红线
- 没有明显时间线冲突
- 角色动机与行为仍成立
- 人物知道什么、不知道什么、误以为什么，都和前文与记忆文件对得上
- 本章涉及的关键资源状态与前文、记忆文件对得上
- 当前卷或当前阶段在推进，而不是原地打转
- 本章有明确功能
- 本章有可感知的局面变化、结果反馈或新压力
- 本章至少推进了角色弧、关系弧、伏笔或承诺中的一项
- 章尾有继续阅读动力
- 语言口吻贴合题材，未被概括腔、解释腔、均质对白压平
- 台词意思当场能懂，不需要读者自己先翻译一遍
- 叙述落得到具体事和具体后果，不写“已经在流血了”“气息一下紧了”这类虚描述

### 阻断项

- 提前跳到下一卷或下一阶段关键节点
- 角色行为与既有人设严重冲突且无铺垫
- 连续多章拖欠同一核心承诺
- 关键关系连续停滞，没有新变化
- 近几章重复使用同一类桥段、爽点或钩子
- 同一节点在相邻两章或近三章里被完整推进两次
- 同一结果在相邻两章里重复拿到，却没有升级
- 人物知道了他此时不该知道的信息
- 时间、天气、路程、伤势、库存、地块、钱粮、人手在无依据情况下跳变
- 记忆文件彼此冲突，或记忆文件与正文冲突
- 正文出现“好像读过但其实没写过”的桥段、设定或关系进度
- 解释性文字压过当前冲突
- 台词看着有劲，但读者还得自己翻译意思
- 叙述只给抽象判断，不落具体事和具体后果
- 机械连接词、总结腔、空泛感慨过密，AI 味压过题材口吻
- 删掉本章后对后文几乎没有影响

## 语言闭环

涉及 `/写`、`/续写`、`/修改` 时，默认执行：

1. **Draft**：先写成立的剧情稿，只保证章节功能、角色行为、信息顺序正确。
2. **Audit**：检查作者式旁白、抽象堆词、强行气氛、重复句式、无效抒情、机械连接词、概括腔、同声对白。
3. **Rewrite**：只改语言，不改剧情功能；优先删空话、补感知、压重复、拆机械过渡、让对白各有主人。
4. **Recheck**：确认改写后，本章功能、伏笔、冲突、章尾钩子未受损，且题材口吻仍稳。

若用户明确要求只给初稿，也要说明“未经过语言审计闭环”。

### 语言硬性审计项

- 禁止连续使用“很快 / 随后 / 很显然 / 不多时 / 可以说 / 某种意义上”等机械转场顶剧情
- 禁止用总结句替代场景句，能让人物做出来的，不让旁白替人物概括
- 禁止多人对白一个腔调；人物年龄、身份、利害不同，语气和词路也要不同
- 禁止为了显得有质感而堆抽象判断，优先落到动作、物件、气味、触感、账目、工序
- 禁止把本来一句能说清的台词写成读者需要二次翻译的“硬句”；有劲不等于含混，必须让读者当场听懂
- 禁止用“已经在流血了”“气息一下紧了”“局势更坏了”这类抽象判断代替场景事实；必须补到具体发生了什么、具体坏到哪一步
- 种田文默认优先“家计感、劳作感、积累感、微小得失感”，不写成空泛励志或万能经营学

## 默认字数策略

涉及 `/写`、`/续写`、`/修改` 时，若用户没有单独指定章节篇幅，默认按**单章 2200-3500 字**控制。

- `2200-3500` 是默认参考区间，不是绝对铁律
- 默认优先避免章节字数过少；低于 `2200` 时，除非用户明确要求短章、该章功能天然偏短、或平台策略明确要求短更，否则视为风险
- 字数服从章节功能、题材节奏、平台阅读体验，不允许为了凑字数灌水
- 若章节天然属于过渡、钩子、插叙、短冲突回合，允许低于默认区间，但必须保证本章仍有明确推进、结果变化或新压力

## 自动化脚本

```bash
python scripts/project_bootstrap.py --project "novel_书名"
python scripts/project_doctor.py --project "novel_书名"
python scripts/context_compiler.py --project "novel_书名" --chapter 12
python scripts/workflow_runner.py --project "novel_书名" --chapter 12
python scripts/chapter_gate.py --project "novel_书名" --chapter-no 12
python scripts/language_audit.py --project "novel_书名" --chapter-no 12 --mode suggest
python scripts/batch_gate.py --project "novel_书名" --from 1 --to 30 --json
```

默认理解：

- `templates/` 主要给人工阅读与使用
- `technique-kb/` 会被 `language_audit.py`、`chapter_gate.py` 等脚本自动消费
- `scripts/` 产出的报告优先于口头印象
- `workflow_runner.py` 会额外生成 `05_reports/pipeline_report.{md,json}` 作为流水线总报告
- `workflow_runner.py --chapter N` 的 `N` 默认指“已存在的当前章”，适合写完一章后做回填和汇总；若只是要准备下一章上下文，用 `context_compiler.py --chapter 下一章`

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
