# 显式多 Agent 协同协议

这不是形式化摆拍，也不是把 MOSS 整包搬进来。

它只做一件事：

**把 `chaseNovel` 的常用写作流程拆成几个稳定角色，并要求在 `/写`、`/续写`、`/修改` 时显式并行拉审查 agent，避免“写完凭感觉觉得没问题”。**

---

## 一、默认角色

### 1. Planner

负责：

- 题材定位
- 一句话卖点
- 开篇路线
- 黄金三章
- 卷纲 / 阶段目标

主要产物：

- `plan.md`
- `arc_progress.md`
- `/一键开书` 输出骨架

### 2. Worldbuilder

负责：

- 世界观边界
- 力量体系 / 规则体系
- 术语口径
- 考据词与虚构词的统一

主要产物：

- `worldbuilding-index.md`
- `findings.md`
- `plan.md` 中的世界规则部分

### 3. Character

负责：

- 主角反差
- 配角动机
- 关系变化
- 反工具人

主要产物：

- `characters.md`
- `character_arcs.md`
- `state.md` 的人物状态

### 4. Writer

负责：

- 把规划和记忆落成可读正文
- 输出章卡
- 起草章节

主要产物：

- 章节正文
- `summaries/recent.md`
- `state.md` 的推进结果

### 5. Reviewer

负责：

- 连续性
- 重复桥段
- 承诺拖欠
- 门禁回退

主要产物：

- 门禁结论
- 修订意见
- 必要时回写 `foreshadowing.md`、`timeline.md`、`payoff_board.md`

### 6. HookEmotion

负责：

- 情绪曲线
- 章尾钩子
- 爽点密度
- 高点前蓄压与高点后余波

主要产物：

- 本章情绪曲线判断
- 章尾钩子建议
- 爽点 / 情绪风险提示

### 7. StyleDialogue

负责：

- 对话口吻区分
- 旁白发硬
- 角色说话同质化

主要产物：

- 语言修订建议
- 对话分层建议
- 口吻与旁白风险提示
- `templates/character-voice-diff.md` 的角色说话差分表

### 8. LanguageReviewer

负责：

- AI 味过重
- 机械过渡
- 作者替读者总结
- 信息搬运感

主要产物：

- 语言去 AI 味审查结论
- 高风险句段定位
- `templates/language-anti-ai-review.md` 审查卡

### 8.1 StyleConsistencyReviewer

负责：
- 单书 voice DNA
- 叙述节拍
- 角色声口一致性
- 跨章节风格漂移

主要产物：
- 风格漂移定位
- 最小修法建议
- `templates/style-consistency-review.md` 审查卡
### 9. ContinuityReviewer

负责：

- 世界规则连续性
- 时间线连续性
- 伏笔 / 承诺连续性
- 已有效布置是否失忆

主要产物：

- 连续性风险定位
- 必修连续性问题
- `templates/continuity-review-card.md` 审查卡

### 10. CausalityReviewer

负责：

- 转折前提是否成立
- 人物决策是否合理
- 结果是否靠布置推出
- 后账是否接得住

主要产物：

- 因果硬伤定位
- 必修因果问题
- `templates/causality-review-card.md` 审查卡

### 11. ResearchMaterial

负责：

- 资料抽读
- 考据压缩
- 本地语料转写
- 现实资料转成可写规则

主要产物：

- 题材资料摘要
- 可直接落地的规则卡
- 术语 / 资料来源清单
- `references/contracts/07-research-material.md` 压缩卡

## 二、Codex 子 Agent 映射

为避免“写了角色名，但执行时没真拉 agent”，默认映射如下：

| 写作角色 | Codex 子 agent |
| --- | --- |
| `Planner` | `planner` |
| `Worldbuilder` | `architect` |
| `Character` | `analyst` |
| `HookEmotion` | `writer` |
| `StyleDialogue` | `writer` |
| `LanguageReviewer` | `code-reviewer` |
| `StyleConsistencyReviewer` | `critic` |
| `ContinuityReviewer` | `critic` |
| `CausalityReviewer` | `critic` |
| `ResearchMaterial` | `researcher` |
| `Writer` | `writer` |
| `Reviewer` | `critic` |

执行约束：

- `/写`、`/续写`、`/修改` 默认按此映射显式拉起 Codex 子 agent
- 若运行面当前无法显式拉起子 agent，必须按同一顺序手动执行检查项，并标注“未实际拉起子 agent”

---

## 三、默认编排模式

### 模式 A：开书编排

顺序：

`Planner -> Character -> Worldbuilder -> Reviewer`

适用：

- `/一键开书`
- 新题材立项
- 开篇三章重做

最小交接：

- Planner 先定卖点、路线、卷目标
- Character 补主角反差、配角驱动、关系起手
- ResearchMaterial 如有必要，先把题材资料压成可写规则，再交给 Worldbuilder
- Worldbuilder 只补当前开篇必须用到的规则和术语
- Reviewer 检查卖点是否落得住、第一章是否真能抓人

### 模式 B：单章编排

顺序：

`Planner -> HookEmotion -> Writer -> [StyleDialogue || LanguageReviewer || StyleConsistencyReviewer || ContinuityReviewer || CausalityReviewer || Reviewer] -> Writer/Planner 修正 -> Reviewer`

适用：

- `/写`
- `/续写`
- 批量章节中的单章执行

最小交接：

- Planner 先定本章功能、结果变化、情绪点、钩子
- Planner 先补“写前锚定包”，明确时间、地点、在场人物、知情边界、资源状态、开放线程
- HookEmotion 先校正情绪曲线、高点位置和章尾钩子是否真的能决定下一章行动
- Writer 负责成稿
- `StyleDialogue` 在不改结构的前提下拉开对白口吻和旁白硬度，防止多人一个声口
- `LanguageReviewer` 单独盯 AI 味、机械过渡、解释感、概括腔
- `StyleConsistencyReviewer` 单独盯单书 voice DNA、章节节拍、角色声口、跨章漂移
- `ContinuityReviewer` 单独盯时间线、设定、伏笔、状态连续性和知情边界
- `CausalityReviewer` 单独盯人物决策、转折前提和结果落地
- `Reviewer` 专门盯章功能、冲突类型、结果类型、钩子类型是否与近 `3-5` 章重复
- 汇总后，若命中幻读、知情越界、时间漂移、资源漂移、重复推进或 AI 味过重，不通过，直接回退给 Writer / Planner 修

### 模式 C：重修编排

顺序：

`Reviewer -> Planner -> HookEmotion -> Writer -> [StyleDialogue || LanguageReviewer || StyleConsistencyReviewer || ContinuityReviewer || CausalityReviewer] -> Writer 修正 -> Reviewer`

适用：

- 太水
- 重复
- 人设崩
- 钩子弱
- AI 味重

最小交接：

- Reviewer 先指出问题类型和影响面
- Planner 重定保留项与修法
- HookEmotion 专门处理情绪跳、钩子弱、爽点不兑现这类问题
- Writer 重写
- StyleDialogue 只修对白和口吻层
- LanguageReviewer 单独压 AI 味和解释味
- StyleConsistencyReviewer 单独修风格漂移，不抢结构判断
- ContinuityReviewer 检查设定、时间线、伏笔、承诺是否被改崩
- CausalityReviewer 检查修订后的转折和决策是否站得住
- Reviewer 复核并决定是否再次回退

### 模式 D：复杂题材编排

顺序：

`Planner -> ResearchMaterial -> Worldbuilder -> Character -> HookEmotion -> Writer -> [StyleDialogue || LanguageReviewer || StyleConsistencyReviewer || ContinuityReviewer || CausalityReviewer || Reviewer] -> Writer/Planner 修正 -> Reviewer`

适用：

- 历史 / 权谋
- 盗墓 / 摸金
- 设定密度高的修仙
- 多势力并行的中长线题材

原则：

- ResearchMaterial 只压资料，不直接决定剧情
- Worldbuilder 不抢剧情推进权
- Character 不改世界规则
- Writer 不擅自扩设定
- StyleDialogue 不擅自改结构
- LanguageReviewer 不改剧情功能
- StyleConsistencyReviewer 不另造新风格，只负责把章节拉回本书既有 voice
- ContinuityReviewer 不重写正文，只抓硬伤
- CausalityReviewer 不重排大纲，只抓因果断点
- Reviewer 只做门禁和回退，不重新开大纲

---

## 三、并行复核硬规则

- `/写`、`/续写`、`/修改` 默认必须显式并行拉起：
  - `StyleDialogue`
  - `LanguageReviewer`
  - `StyleConsistencyReviewer`
  - `ContinuityReviewer`
  - `CausalityReviewer`
  - `Reviewer`
- 开篇 `1-10` 章里，`Reviewer` 额外必须检查：
  - 章功能是否重复
  - 冲突类型是否重复
  - 结果类型是否重复
  - 钩子类型是否重复
- 任一 reviewer 命中以下问题，默认不能直接交稿：
  - 同一节点重复推进
  - 同一结果重复拿到但无升级
  - 相邻章节只是换说法，不换结果
  - 解释重复压过新进展
- 允许不并行的情况只限：
  - `/一键开书`
  - 极短润色
  - 用户明确要求只给草稿

### 并行复核固定输出

每个复核 agent 默认必须交：

- `chapter_function`
- `conflict_type`
- `result_type`
- `hook_type`
- `findings`
- `blocking`
- `suggested_fix`

`Reviewer` 额外必须交：

- `repeat_window`
- `upgrade_point`

缺字段的复核，默认视为不完整，不得直接收口。

### 复核冲突裁决顺序

当多个 reviewer 结论互相冲突时，统一按以下顺序裁决：

1. `ContinuityReviewer` / `CausalityReviewer`
2. `Reviewer`
3. `HookEmotion`
4. `StyleDialogue` / `LanguageReviewer`
5. `StyleConsistencyReviewer`

规则：

- 高优先级可覆盖低优先级修法
- 低优先级建议若破坏高优先级成立条件，直接丢弃
- 连续性 / 因果未过时，不进入纯语言收尾

### 开篇专用检查模板

开篇 `1-10` 章默认额外跑三张检查卡：

1. `黄金三章检查卡`
2. `递进防重复检查卡`
3. `资源闭环检查卡`

三张卡至少由 `Reviewer` 明确给结论，不允许省略。

## 四、什么情况需要拉额外 Agent

### 必拉 Worldbuilder

- 新题材设定多
- 术语多且容易写混
- 有真实考据词
- 题材依赖规矩、门派、制度、机关、组织口径

### 必拉 Character

- 群像开书
- 配角开始工具人化
- 关系推动是本章主要看点
- 感情线 / 君臣 / 师徒 / 队友裂痕是核心推进器

### 必拉 Reviewer

- 批量写作
- 开篇三章
- 大改重修
- 用户明确要求控节奏、重复

### 必拉 HookEmotion

- 章尾钩子弱
- 情绪起伏不顺
- 爽点密度不足
- 连续几章收尾同质
- 用户明确要求控节奏、抓追读

### 必拉 StyleDialogue

- 对话发空
- 旁白发硬
- 角色说话区分不出来

### 必拉 LanguageReviewer

- AI 味重
- 机械过渡太多
- 作者替读者总结
- 场景像信息搬运

### 必拉 ContinuityReviewer

- 世界观开始写混
- 时间线容易打架
- 伏笔、承诺、布置容易失忆
- 用户明确要求“别崩设定”

### 必拉 CausalityReviewer

- 转折靠硬推
- 人物决策像作者安排
- 结果落地过快
- 用户明确要求“剧情走向合理”

### 必拉 ResearchMaterial

- 历史 / 盗墓 / 权谋 / 修仙等资料依赖题材
- 需要吸收本地下载小说样本
- 真实资料很多，但还没转成可写规则
- 新题材需要先做资料压缩

---

## 五、每个 Agent 的输入边界

### Planner 输入

- 题材
- 平台倾向
- 当前阶段
- 已有记忆文件

不负责：

- 直接出长正文

### Worldbuilder 输入

- 当前章节需要的规则
- 当前卷需要的势力 / 术语 / 机制

不负责：

- 为了显得完整而扩写一整本百科

### Character 输入

- 当前章要推谁
- 当前关系要怎么变

不负责：

- 替 Writer 直接写完整正文

### Writer 输入

- 已确认的章卡
- 已确认的“写前锚定包”
- 已确认的规则边界
- 已确认的人物状态
- 已确认的情绪曲线与钩子方向

不负责：

- 擅自新增重大设定
- 擅自改卷纲
- 擅自写出锚定包之外的新知情、新资源、新时间跳跃

### Reviewer 输入

- 成稿
- 当前 plan / state / timeline / foreshadowing / character_arcs

不负责：

- 重写整章
- 重开整套世界观

必须额外检查：

- 近 `3-5` 章章功能是否重复
- 近 `3-5` 章结果类型是否重复
- 开篇 `1-10` 章是否有递进失效
- 本章删掉后后文是否仍基本成立
- 开篇 `1-10` 章是否通过三张专用检查卡
- 人物知情边界是否越线
- 资源状态是否无依据跳变
- 记忆文件之间、记忆文件与正文之间是否冲突

默认补件：

- 命中阶段复盘时，优先套 `templates/reviewer-stage-retro.md`

### HookEmotion 输入

- 本章功能
- 当前压力源
- 本章结果类型
- 近 1-3 章钩子与情绪走势

不负责：

- 擅自改主线
- 单独定义世界规则

### StyleDialogue 输入

- 已成稿正文
- 当前题材口吻
- 角色说话边界

不负责：

- 改主线结论
- 改章节功能

默认补件：

- 角色说话开始撞车时，先补 `templates/character-voice-diff.md`

### LanguageReviewer 输入

- 已成稿正文
- 已做过 StyleDialogue 的版本
- 当前题材口吻
- 写前锚定包中的场景目标与情绪目标

不负责：

- 改主线结论
- 直接重排剧情

默认补件：

- 先套 `templates/language-anti-ai-review.md`
- 再额外检查：机械连接词、总结腔、均质对白、作者代角色发言

### ContinuityReviewer 输入

- 成稿
- `plan.md` / `state.md` / `timeline.md` / `foreshadowing.md` / `payoff_board.md` / `character_arcs.md`
- 写前锚定包

不负责：

- 代替 Worldbuilder 重建设定
- 代替 Reviewer 做总审结论

默认补件：

- 先套 `templates/continuity-review-card.md`
- 再额外检查：人物知情边界、时间跨度、资源账、场景移动是否与锚定包一致

### CausalityReviewer 输入

- 成稿
- 本章章卡
- 近章关键结果与布置

不负责：

- 直接改文风
- 重开全书大纲

默认补件：

- 先套 `templates/causality-review-card.md`

### ResearchMaterial 输入

- 当前题材
- 当前要解决的问题
- 资料来源或本地样本范围

不负责：

- 直接起草正文
- 把资料原样堆进设定

默认补件：

- 先按 `references/contracts/07-research-material.md` 压成规则卡，再交下游

---

## 六、回写原则

编排不是开会，必须落文件。

### 开书后至少回写

- `plan.md`
- `characters.md`
- `state.md`

### 单章完成后至少回写

- `summaries/recent.md`
- `state.md`

### 命中复杂规则时追加回写

- 伏笔变动：`foreshadowing.md`
- 时间变化：`timeline.md`
- 关系推进：`character_arcs.md`
- 术语新增：`worldbuilding-index.md`
- 承诺兑现压力变化：`payoff_board.md`
- 资料转写：`findings.md` / `worldbuilding-index.md`
- 阶段复盘：`state.md` / `findings.md`

### 复核后强制回写

- 重复推进 / 递进失效 -> `findings.md`
- 阶段节奏风险 / 下一章警告 -> `state.md`
- 长线目标、阶段目标受影响 -> `plan.md`
- 伏笔窗口改变 -> `foreshadowing.md`
- 时间顺序调整 -> `timeline.md`
- 人物关系、分工变化 -> `character_arcs.md`
- 人物知情边界调整、误会建立或解除 -> `character_arcs.md` 或单独记入 `findings.md`
- 资源状态被正文推进过 -> `state.md`，必要时同步 `timeline.md`

语言层纯润色可不回写；结构性问题默认必须回写。

---

## 七、最短执行口令

如果不显式说明，默认这样理解：

- `/一键开书`：走 `Planner -> Character -> Worldbuilder -> Reviewer`
- `/写`：走 `Planner -> HookEmotion -> Writer -> [StyleDialogue || LanguageReviewer || StyleConsistencyReviewer || ContinuityReviewer || CausalityReviewer || Reviewer] -> 修正 -> Reviewer`
- `/续写`：走 `Planner -> HookEmotion -> Writer -> [StyleDialogue || LanguageReviewer || StyleConsistencyReviewer || ContinuityReviewer || CausalityReviewer || Reviewer] -> 修正 -> Reviewer`
- `/修改`：走 `Reviewer -> Planner -> HookEmotion -> Writer -> [StyleDialogue || LanguageReviewer || StyleConsistencyReviewer || ContinuityReviewer || CausalityReviewer] -> 修正 -> Reviewer`
- 高风险单章 / 世界观密集章：并行复核不减配，只增配
- 复杂题材开书 / 复杂题材中盘：可扩成 `Planner -> ResearchMaterial -> Worldbuilder -> Character -> HookEmotion -> Writer -> [StyleDialogue || LanguageReviewer || StyleConsistencyReviewer || ContinuityReviewer || CausalityReviewer || Reviewer] -> 修正 -> Reviewer`

---

## 八、一句话原则

**显式多 Agent 协同不是多几个人设，而是把“谁先写、谁并行挑错、什么情况下必须回退”固定下来。**
