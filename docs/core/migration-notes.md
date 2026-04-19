# 兼容迁移说明

## 目标
这份说明只回答一件事：旧路径、旧命令、旧模板，现在各自应该迁到哪里。

## 命令迁移

### 新主入口
- `chase open`
- `chase quality`
- `chase write`
- `chase status`
- `chase check`

### 旧命令到新入口
- `planning` / `context` -> `open`
- `gate` / `draft` / `audit` / `batch` -> `quality`
- `dashboard` / `foreshadow` / `arc` / `timeline` / `repeat` -> `status`
- `run` -> `write`

## 当前默认链路
- `write` / `run` 默认步骤：`doctor,open,runtime,quality,status`
- `check` 默认步骤：`doctor,open,quality,status`
- `check` 保持 dry-run，不进入 `runtime`

## 文档迁移

### 核心主链
- `references/craft-and-platform.md` -> `docs/core/open-book.md`
- `references/execution_workflow.md` -> `docs/core/write-workflow.md`
- `references/revision-and-diagnostics.md` -> `docs/core/revise-diagnostics.md`
- `references/agent-collaboration.md` -> `docs/core/write-workflow.md`
- historical output contracts doc -> `docs/core/task-contracts.md`

### 资产层
- historical genre index docs -> `docs/assets/genre-index.md`
- root `technique-kb/` -> `assets/technique-kb/`
- root common style assets -> `assets/common/`

## 模板迁移
- `templates/style-defaults.md` -> `assets/common/style-defaults.md`
- `templates/style_fingerprints.md` -> `assets/common/style-fingerprints.md`
- `templates/chapter-planning-review.md` -> `templates/review/chapter-planning-review.md`
- `templates/rewrite-handoff.md` -> `templates/review/rewrite-handoff.md`
- `templates/volume_blueprint.md` -> `templates/launch/volume-blueprint.md`
- legacy continuity / language anti-AI / style consistency review templates
  -> merged into `templates/review/chapter-quality-review.md`

## 当前兼容策略
- 旧命令仍保留，但已经降级为兼容别名
- `references/` 继续承担兼容层职责，不再是默认阅读入口
- 根层模板只保留仍有兼容价值的 shim，未再使用的旧模板已移除

## 迁移建议
如果在维护旧项目，最实用的做法是：

1. 先把命令切到 `open / quality / write / status / check`
2. 再把阅读入口切到 `docs/core/*`
3. 最后逐步移除旧模板和旧 `references` 路径
