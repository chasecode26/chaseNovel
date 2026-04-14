# 任务输出契约

## 目标
把“开书 / 写作 / 续写 / 修改 / 状态”几类任务的最低输出要求收在一处，避免命令一多就把契约拆散。

## 契约索引
- 开书：`references/contracts/01-launch.md`
- 写作：`references/contracts/02-write.md`
- 续写：`references/contracts/03-continue.md`
- 修改：`references/contracts/04-modify.md`
- 状态 / 节奏：`references/contracts/05-state-and-rhythm.md`
- 承诺 / 防重复：`references/contracts/06-promises-and-repeat.md`
- 研究材料：`references/contracts/07-research-material.md`

## 开书最小输出
- 题材与主卖点
- 主线目标与阶段目标
- 黄金三章功能链
- 角色结构
- 书级 `style.md` / `voice.md`

## 写作 / 续写最小输出
- 本章时间、地点、在场人物、知情边界、资源状态
- 本章功能
- 结果变化
- 章尾钩子
- 需要兑现 / 预热 / 延后的旧布置

## 修改最小输出
- 保留项
- 问题类型
- 改法选择
- 影响面
- 是否需要同步更新记忆文件

## 状态 / 书级体检最小输出
- 当前章节 / 当前卷 / 当前弧
- 活跃伏笔 / 超期伏笔
- 时间线风险
- 重复推进风险
- 下章目标或当前阻塞点

## 当前主入口
- 开书：`docs/core/open-book.md`
- 写作：`docs/core/write-workflow.md`
- 状态：`docs/core/status-workflow.md`
- 改写与诊断：`docs/core/revise-diagnostics.md`

## 跨任务共通裁决
- 结论只用：`pass / revise / fail`
- 若判退，必须补：`return_to / rewrite_scope / first_fix_priority / recheck_order`
- reviewer 没有整章读完，不得直接放行
- 语言、风格、连续性、因果四类问题，默认先修承载方式，再动主线结果
- 凡是会影响 `state.md / timeline.md / foreshadowing.md / payoff_board.md / character_arcs.md` 的修改，必须显式说明是否回写

## Runtime contract fields
- `context`：由 LeadWriter runtime 编译出的章节上下文
- `brief`：LeadWriter 下发给 WriterExecutor 的章级 brief
- `verdicts`：统一 evaluator 输出
- `final_release`：quality 聚合的最终放行结论
- `runtime_signals`：status 聚合返回的观察信号
- `decision`：runtime 的 pass / revise / fail 决策与 rewrite brief

## 成功标准
- 读者能说清这一章发生了什么、为什么发生、结果变了什么
- 章节功能、结果变化、章尾钩子三者一致
- 关键风险已落到具体人物、动作、资源或后果，不停留在抽象判断
- 需要复核的地方已经过 reviewer，而不是只靠作者自检
