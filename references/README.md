# references

`references/` 当前定位为兼容层与资料层，不再是默认主入口。

这里保留两类内容：

- `shim`：把旧路径读者导向新的默认入口
- 仍有业务价值、但尚未完全下沉的题材与技法资料

另有一层历史兼容隔离区：

- `references/legacy/`：只保留旧路径，不再承载任何默认流程说明

## 当前默认入口

默认阅读与使用入口已经迁到：

- `docs/core/`
- `docs/assets/`
- `templates/core/`
- `templates/launch/`
- `templates/review/`

对外主命令面已经收口为：

- `chase open`
- `chase quality`
- `chase write`
- `chase status`
- `chase check`

其中：

- `write / run` 默认链路是 `doctor,open,runtime,quality,status`
- `check` 默认链路是 `doctor,open,quality,status`
- `check` 保持 dry-run，不进入 `runtime`

## 当前保留策略

### shim

用于把旧路径读者导向新的默认入口，例如：

- `execution_workflow.md`
- `agent-collaboration.md`
- `revision-and-diagnostics.md`
- `craft-and-platform.md`
- `legacy/*`

### domain references

仍保留部分题材、样本、写法与负面模式资料，供资产层迁移与兼容期使用。

## 已经完成的迁移方向

- 历史流程入口已迁到 `docs/core/*`
- 题材索引已迁到 `docs/assets/genre-index.md`
- 模板主入口已迁到 `templates/core/*`、`templates/launch/*`、`templates/review/*`
- `technique-kb/` 主内容已迁到 `assets/technique-kb/`

## 使用建议

除非需要兼容旧项目、追溯历史资料或做存量对照，否则不要再从 `references/` 平铺下钻。

优先阅读：

1. `docs/core/open-book.md`
2. `docs/core/write-workflow.md`
3. `docs/core/status-workflow.md`
4. `docs/core/task-contracts.md`
5. `docs/core/cli-quickstart.md`
