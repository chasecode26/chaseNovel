# 兼容迁移说明

## 目标

这份说明只回答一件事：  
**旧路径、旧命令、旧模板，现在各自应该迁到哪里。**

## 命令迁移

### 新主入口
- `chase open`
- `chase quality`
- `chase write`
- `chase status`

### 旧命令到新入口
- `planning` / `context` -> `open`
- `gate` / `draft` / `audit` / `batch` -> `quality`
- `dashboard` / `foreshadow` / `arc` / `timeline` / `repeat` -> `status`
- `run` -> `write`

## 文档迁移

### 核心主链
- `references/craft-and-platform.md` -> `docs/core/open-book.md`
- `references/execution_workflow.md` -> `docs/core/write-workflow.md`
- `references/revision-and-diagnostics.md` -> `docs/core/revise-diagnostics.md`
- `references/agent-collaboration.md` -> `docs/core/write-workflow.md`
- `references/output-contracts.md` -> `docs/core/task-contracts.md`

### 资产层
- 旧题材资料入口 -> `docs/assets/genre-index.md`
- 根层 `technique-kb/` -> `assets/technique-kb/`
- 根层风格公共资产 -> `assets/common/`

## 模板迁移

- `templates/style-defaults.md` -> `assets/common/style-defaults.md`
- `templates/style_fingerprints.md` -> `assets/common/style-fingerprints.md`
- `templates/chapter-planning-review.md` -> `templates/review/chapter-planning-review.md`
- `templates/rewrite-handoff.md` -> `templates/review/rewrite-handoff.md`
- `templates/volume_blueprint.md` -> `templates/launch/volume-blueprint.md`
- `templates/language-anti-ai-review.md` -> `templates/review/chapter-quality-review.md`
- `templates/style-consistency-review.md` -> `templates/review/chapter-quality-review.md`

## 当前兼容策略

- 旧命令：保留，但降级为兼容别名
- 旧 references 导航：尽量变成 shim 或 legacy
- 少量根层模板：保留 shim，避免打断旧项目

## 迁移建议

如果你在维护旧项目，最实用的做法是：
1. 先把命令切到 `open / quality / write / status`
2. 再把阅读入口切到 `docs/core/*`
3. 最后再逐步改掉旧模板和旧 references 路径
