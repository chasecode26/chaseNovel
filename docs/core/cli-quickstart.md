# CLI 快速上手

## 主入口

当前默认只需要先记住 6 个命令：

```bash
chase bootstrap --project <dir>
chase doctor --project <dir>
chase open --project <dir> [--chapter <n>]
chase quality --project <dir> [--chapter-no <n> | --from <n> --to <n>]
chase write --project <dir> [--chapter <n>] [--steps <csv>]
chase status --project <dir> [--chapter <n>] [--focus <all|dashboard|foreshadow|arc|timeline|repeat>]
```

## 最常见用法

### 1. 初始化新项目
```bash
chase bootstrap --project my-book
chase doctor --project my-book
```

### 2. 开书
```bash
chase open --project my-book
```

### 3. 写某一章前先准备上下文
```bash
chase open --project my-book --chapter 12
```

### 4. 写前 / 写后做质量检查
```bash
chase quality --project my-book --chapter-no 12
```

### 5. 看整本书现在的健康状态
```bash
chase status --project my-book
```

### 6. 跑整条写作聚合链
```bash
chase write --project my-book --chapter 12
```

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

如果你是新用户，默认不要先记这些。

## 推荐阅读顺序
1. `SKILL.md`
2. `docs/core/open-book.md`
3. `docs/core/write-workflow.md`
4. `docs/core/status-workflow.md`
5. `docs/core/task-contracts.md`
