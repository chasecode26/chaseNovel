# 状态与书级健康主链路

> 这是重构后的核心状态入口文档。它负责把书级健康检查收敛成一个统一入口，而不是让用户在很多散装命令之间来回切换。

## 目标
`status` 负责回答这几个问题：
- 现在写到哪了
- 哪些伏笔到期了
- 角色弧有没有停滞
- 时间线是否开始错位
- 最近几章有没有重复推进
- 下一章前最值得优先关注的风险是什么

## 当前主入口
- `chase status --project <dir>`
- `chase status --project <dir> --focus dashboard`
- `chase status --project <dir> --focus foreshadow`
- `chase status --project <dir> --focus arc`
- `chase status --project <dir> --focus timeline`
- `chase status --project <dir> --focus repeat`

## 统一协议
`status` 当前支持：
- `--focus all`
- `--focus dashboard`
- `--focus foreshadow`
- `--focus arc`
- `--focus timeline`
- `--focus repeat`

默认是 `all`，会把整本书最关键的健康信号一次性汇总出来。

## 什么时候用 status

### 写前
- 断更恢复
- 不确定当前主线推进到哪
- 想先看本书有没有明显风险，再决定下一章怎么写

### 写后
- 想看这章有没有拉高伏笔压力
- 想看时间线、角色弧、重复推进是否恶化
- 想知道下一章应该优先处理什么

## 当前兼容别名
以下旧命令都已降级为兼容别名，内部转向 `status`：
- `dashboard`
- `foreshadow`
- `arc`
- `timeline`
- `repeat`

建议默认不再直接记这些旧名字，而是记：
- `status --focus dashboard`
- `status --focus foreshadow`
- `status --focus arc`
- `status --focus timeline`
- `status --focus repeat`

## 典型理解方式
- `dashboard`：总体面板
- `foreshadow`：伏笔兑现压力
- `arc`：角色/关系推进压力
- `timeline`：时间与先后关系风险
- `repeat`：近章套路与钩子重复风险

它们现在不再是五个平级主入口，而是 `status` 的五个观察视角。
