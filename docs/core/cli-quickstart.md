# CLI 快速上手

## 主入口
当前默认先记住 7 个命令：

```bash
chase bootstrap --project <dir>
chase doctor --project <dir>
chase open --project <dir> [--chapter <n> | --target-chapter <n>]
chase quality --project <dir> [--chapter-no <n> | --from <n> --to <n>]
chase write --project <dir> [--chapter <n> | --target-chapter <n>] [--steps <csv>]
chase status --project <dir> [--chapter <n>] [--focus <all|dashboard|foreshadow|arc|timeline|repeat>]
chase check --project <dir> [--chapter <n> | --target-chapter <n>]
```

## 最常见用法

### 1. 初始化新项目
```bash
chase bootstrap --project my-book
chase doctor --project my-book
```

### 2. 开书 / 做 readiness 扫描
```bash
chase open --project my-book
```

### 3. 写某一章前先准备上下文
```bash
chase open --project my-book --chapter 12
```

### 4. 检查当前章节质量
```bash
chase quality --project my-book --chapter-no 12
```

### 5. 看整本书当前健康状态
```bash
chase status --project my-book
```

### 6. 跑完整写作聚合链
```bash
chase write --project my-book --chapter 12
```

### 7. 跑 dry-run 检查链
```bash
chase check --project my-book --chapter 12
```

## 默认链路

### `write`
- 默认步骤：`doctor,open,runtime,quality,status`
- 用于完整写作主链

### `check`
- 默认步骤：`doctor,open,quality,status`
- 用于 dry-run 健康扫链
- 会做 `quality` 放行确认
- 不会进入 `runtime`

## 章节语义
- `--chapter <n>` 在聚合命令里表示当前已写的 `reference_chapter`
- `open / planning / context` 会基于它默认准备 `target_chapter = n + 1`
- 需要跳章、补章、回头准备指定章节时，显式传 `--target-chapter <m>`
- `status / quality / runtime / memory` 都消费当前 `reference_chapter`

## 聚合输出
`chase write` / `chase run` / `chase check` 的聚合 JSON 当前可稳定关注：

- `reference_chapter`
- `target_chapter`
- `status`
- `warning_count`
- `steps`
- `report_paths`
- `pipeline_summary`
- `final_release`

其中：
- `pipeline_summary` 汇总 `open`、`runtime`、`quality`、`status` 的关键信号
- `final_release` 是给 CLI、烟测和上层工具直接消费的最终发布决策

## 兼容别名
以下旧命令仍能用，但现在都只是兼容入口：

- `planning`
- `context`
- `gate`
- `draft`
- `audit`
- `batch`
- `dashboard`
- `foreshadow`
- `arc`
- `timeline`
- `repeat`
- `memory`
- `run`

如果是新用户，默认不要先记这些。

## 推荐阅读顺序
1. `SKILL.md`
2. `docs/core/open-book.md`
3. `docs/core/write-workflow.md`
4. `docs/core/status-workflow.md`
5. `docs/core/task-contracts.md`

## 最小校验
维护仓库时，最小验尸命令是：

```bash
npm run smoke
```

若要在提交前快速看一眼“代码 / 文档 / 测试是否同拍”，再补一刀：

```bash
node ./scripts/change_analyzer.js --mode working --json
```

常用变体：
- `node ./scripts/change_analyzer.js --mode staged`
- `node ./scripts/change_analyzer.js --mode committed --json`
- `node ./scripts/change_analyzer.js --mode working --summary-only`
- `node ./scripts/change_analyzer.js --mode working --json --max-files 20`
- `node ./scripts/change_analyzer.js --mode working --category code`
- `node ./scripts/change_analyzer.js --mode working --category docs --summary-only`
- `node ./scripts/change_analyzer.js --mode working --module scripts --json`
- `node ./scripts/change_analyzer.js --mode working --module-prefix docs --json`
- `node ./scripts/change_analyzer.js --mode working --module templates/launch --json`
- `node ./scripts/change_analyzer.js --mode working --top-modules 5 --summary-only`

当前会覆盖：
- `chase --help`
- Python 脚本编译
- fixture 项目链路校验
- `check` 默认是否包含 `quality`
- `write` / `check` 聚合输出与 `final_release`
- `npm pack --dry-run`
