# 写作主链路

> 这是重构后的核心写作入口文档。它把原先分散在执行工作流、协作协议、部分写前模板里的内容收成一条主链。

## 核心目标
写作不是“先写完再说”，而是：
- 先锚定
- 再起稿
- 再复核
- 再回写记忆
- 再看书级健康

## 写前五步
1. 读取 `plan.md` 与 `state.md`
2. 锚定时间、地点、在场人物、知情边界、资源状态
3. 明确本章功能、结果变化、章尾钩子
4. 检查近 3-5 章是否重复推进
5. 明确本章不能擅自新增什么设定

## 默认执行链
`Planner -> Writer -> Reviewers -> Writer 修正 -> Reviewer`

### Reviewers 最少集
- 连续性
- 因果
- 语言 / AI 味
- 风格 / 对白差分

## 什么时候必须加复核
- 正式 `/写`
- `/续写`
- `/修改`
- 开篇前 1-10 章
- 牵涉伏笔、时间线、承诺兑现、资源状态的章节
- 已经出现 AI 味、重复推进、声口漂移的稿子

## 当前兼容执行面
当前阶段，旧命令仍可用：
- `chase planning`
- `chase context`
- `chase gate`
- `chase draft`
- `chase audit`
- `chase memory`
- `chase run`

但它们在产品层面都属于同一条“写作主链”。后续会收口到 `chase write`。

当前已经可用的新入口：
- `chase quality --project <dir> [--chapter-no <n> | --from <n> --to <n>]`
- `chase write --project <dir> [--chapter <n>] [--steps <csv>]`

其中：
- `quality` 聚合 `gate + draft + language`
- `quality` 支持统一子检查协议：`--check all|chapter|draft|language|batch`
- `write` 仍然作为整条写作流水线入口
- `write` 默认优先执行：`doctor -> open -> memory -> status`
- `check` 默认优先执行：`doctor -> open -> status`

## 相关旧资料
- 章节规划复核：`templates/review/chapter-planning-review.md`
- 章节质量复核：`templates/review/chapter-quality-review.md`
- 修章诊断：`docs/core/revise-diagnostics.md`
- 文风治理：`docs/core/style-governance.md`
- 输出要求：`docs/core/task-contracts.md`
- 章节结果/钩子：`templates/launch/chapter-outcome-kit.md`
