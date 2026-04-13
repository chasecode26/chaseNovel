---
name: chaseNovel
description: 当用户要策划、起稿、续写、改写或管理中文网文平台连载，并且关注章节节奏、章尾钩子、伏笔回收、设定连续性、角色推进与追读留存时使用。
---

# chaseNovel

面向中文网文长篇连载的写作技能。

它的核心不是“随手写一章”，而是两条主链路：
- **开书**
- **写作**

一切规则、模板、脚本、复核和资产，都应该服务这两条主链路。

## 核心原则
1. 连载质量优先于单章漂亮。
2. 文件化记忆优先于临时会话记忆。
3. 先保章节功能，再修语言。
4. 默认现代通俗大白话，但不等于统一口水化。
5. 角色声口必须有差分，不准全员一个作者腔。
6. 伏笔、时间线、关系、承诺兑现必须能持续治理。
7. 题材资产按需加载，不能反客为主。
8. 对白必须**答上问题**：问了就要正面答结论、答原因或答下一步动作，不能只靠冷话、狠话、断句顶过去。
9. 军政/权谋/敌情判断必须按 **事实 -> 判断 -> 后果** 写，不能直接抛结论，不准拿黑话和半截术语顶替解释。
10. 禁止提炼腔和装狠句：不写“这才是真刀”“真正要命的是”“不是……而是……”这类作者替读者总结的话。
11. 命令发出后，1-3句内必须跟上**谁去做、先做什么、慢一步会怎样**，不准只喊口号。

## 快速入口
- 开书：`docs/core/open-book.md`
- 写章 / 续写：`docs/core/write-workflow.md`
- 改章 / 诊断：`docs/core/revise-diagnostics.md`
- 文风治理：`docs/core/style-governance.md`
- 状态 / 健康：`docs/core/status-workflow.md`
- 清理候选：`docs/core/legacy-cleanup-candidates.md`
- 重构总结：`docs/core/refactor-summary.md`
- 剩余待办：`docs/core/final-optimization-todo.md`
- 题材资产：`docs/assets/genre-index.md`

## 任务路由
| 用户请求 | 任务类型 | 最小路径 |
| --- | --- | --- |
| 帮我开一本新书 | 开书 | 题材定位 -> 卖点 -> 主线目标 -> 黄金三章 -> 卷纲/阶段目标 |
| 写第 X 章 / 继续写 | 写作 | 读记忆 -> 锚定 -> 明确本章功能 -> 起稿 -> 复核 |
| 改这一章 | 改写 | 识别保留项 -> 找问题类型 -> 重写/压缩/补钩子/补冲突 |
| 人设崩了 / 剧情重复了 | 诊断 | 看阶段目标、人物、时间线、伏笔、重复推进 |
| 看看写到哪了 | 状态 | 汇总当前卷、当前弧、当前阻塞、下章目标 |

## 默认流程

### 开书
`Planner -> Character -> Worldbuilder -> Reviewer`

### 写作
`Planner -> Writer -> Reviewers -> Writer 修正 -> Reviewer`

最少 Reviewers：
- Continuity
- Causality
- Language / Anti-AI
- Style / Dialogue

### 写作硬校验（新增）
- 对白里一旦有人发问，下一轮必须答上，不能故作高深。
- 术语第一次出现，要在同句或下一句解释清楚它是什么、拿来干什么、影响谁。
- 权谋戏优先写动作、座次、称呼、军令、账册、后果，不写作者提炼句。
- 任何一句如果删掉后不影响读者理解事件，只剩“有味道”，默认删。
- 短答不等于有压迫感；若读者仍要补逻辑，默认重写。
- 普通章节先保清楚，再保狠，再保味；顺序不能倒。

### 本轮修文沉淀（避免重犯）
- 不要再写“前半截是赏，后半截才是真刀”这类提炼收口句。
- 不要再把“军令、调令、封账、断钱路”写成抽象压迫，必须写清谁受影响、什么时候死人、哪条线先断。
- 不要再让角色用半截短句互相顶来顶去，尤其是韩朔、谢知微、雍王、皇帝这几类高压角色。
- 不要再让“权谋感”压过“活人感”。人物先活，再谈压场。

## 当前兼容层

Phase 1 期间，旧命令和旧资料路径仍然保留；这样做是为了先完成分层，不先打断现有写作流。

当前仍可使用：
- `chase open`
- `chase quality`
- `chase write`
- `chase status`
- `chase planning`
- `chase context`
- `chase gate`
- `chase draft`
- `chase audit`
- `chase memory`
- `chase run`
- `templates/`

但从产品结构上，它们都已经被重新归类到：
- 开书主链
- 写作主链
- 资产层

阅读时优先：
- `docs/core/*`
- `docs/assets/*`
- `templates/core|launch|review`

不要再默认从 `references/` 平铺下钻；旧资料现在主要是兼容层。

其中：
- `chase open`：新的开书入口；默认做开书 readiness 扫描，传 `--chapter` 时兼容章节规划
- `chase quality`：新的质量闸门聚合入口
- `chase write`：新的写作聚合入口，默认优先走 `doctor + open + memory + status`
- `chase status`：新的书级健康聚合入口
- 旧 `planning/context/gate/draft/audit/batch/foreshadow/arc/timeline/repeat/dashboard` 已降级为兼容别名
- `quality` 已支持统一子检查协议：`all / chapter / draft / language / batch`

## 记忆文件（核心）
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

## 不适用场景
- 只想写一句文案
- 只想润色单句，不关心长线连续性
- 只做文学评论，不推进创作
- 明确不要项目记忆、不要质量闸门、不要连载约束
