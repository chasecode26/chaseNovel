# 状态与书级健康主链路

> `status` 是重构后的统一状态入口，用来回答“现在写到哪、哪里在积压、下一步该先看什么”。

## 目标
- 汇总 `dashboard / foreshadow / arc / timeline / repeat` 五类观察面
- 给出统一 `pass / warn / fail` 结论
- 输出下一步最值得优先处理的风险线索

## 主入口
- `chase status --project <dir>`
- `chase status --project <dir> --focus dashboard`
- `chase status --project <dir> --focus foreshadow`
- `chase status --project <dir> --focus arc`
- `chase status --project <dir> --focus timeline`
- `chase status --project <dir> --focus repeat`

## 统一协议
- `--focus all`
- `--focus dashboard`
- `--focus foreshadow`
- `--focus arc`
- `--focus timeline`
- `--focus repeat`

默认值是 `all`，会聚合整本书当前最关键的健康信号。

## 章节语义
- `status --chapter <n>` 里的 `n` 是 `reference_chapter`
- 这个编号表示“已经存在、拿来做状态检查的章节号”
- `status` 不会自动把 `--chapter` 推成下一章
- 如果目标是准备下一章，请走 `open`
- `open` 会把 `--chapter <n>` 解释为“当前已写章节”，默认规划 `target_chapter = n + 1`

## 什么时候用

### 写前
- 断更恢复时快速确认当前推进位置
- 先看全书是否有明显 overdue foreshadow、停滞角色弧或 timeline 风险
- 决定下一章前，先看哪条线最该优先处理
- 若准备起下一章，先结合 `state.md / timeline.md` 跑一遍“写章前硬核对清单”，确认时间承诺、人数、伤势、资源、知情边界没有错位

### 写后
- 检查本章是否抬高了伏笔压力
- 检查 `timeline / arc / repeat` 是否恶化
- 给后续 `open` 或 `quality` 提供状态依据

## 与 `check` 的边界
- `status` 是状态观察入口，不负责补做 quality 关卡
- `chase check` 当前默认链路是 `open,quality,status`
- `quality` 负责当前 `reference_chapter` 的质量放行判断
- `status` 负责书级健康回看
- `check` 保持 dry-run，不进入 `runtime`

## 兼容别名
以下旧命令已降级为兼容入口，内部统一汇入 `status`：
- `dashboard`
- `foreshadow`
- `arc`
- `timeline`
- `repeat`

推荐统一记忆为：
- `status --focus dashboard`
- `status --focus foreshadow`
- `status --focus arc`
- `status --focus timeline`
- `status --focus repeat`

## 输出关注点
- `dashboard`：全局健康面板与 runtime decision
- `foreshadow`：活跃伏笔、逾期伏笔、近期压力
- `arc`：角色弧 / 关系推进停滞与错位
- `timeline`：时间线先后关系与时距风险
- `repeat`：近章重复推进、重复钩子、重复节奏

## 当前 owner 关系
- `book_health.py` 是公开的 `status` 路由与聚合输出壳
- `dashboard_snapshot.py` 是 `dashboard` / `runtime_signals` 的主摘要构建器
- `book_health.py` 会读取 `dashboard_snapshot.py` 的 payload，再统一拼成 `status` 输出
- `dashboard_snapshot.py` 产出的 `runtime_signals`、`health_digest`、`report_paths` 应保持稳定
