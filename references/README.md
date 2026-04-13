# references

`references/` 当前处于**兼容层**定位。

这里仍保留旧版规则文档、题材资料、拆散的执行说明，目的是：
- 不立刻打断旧项目
- 允许渐进迁移
- 为后续归档与清理留缓冲

其中一部分导航型旧文档已经完成 shim 阶段并可删除，当前仓库已先移除：
- `advanced-template-map.md`
- `genre-asset-index.md`
- `output-contracts.md`

另外一部分已进一步处理为“根层 shim + legacy 归档”的结构，例如：
- `execution_workflow.md` -> `references/legacy/execution_workflow.md`
- `agent-collaboration.md` -> `references/legacy/agent-collaboration.md`
- `revision-and-diagnostics.md` -> `references/legacy/revision-and-diagnostics.md`
- `craft-and-platform.md` -> `references/legacy/craft-and-platform.md`

新的默认入口已经迁到：
- `docs/core/`
- `docs/assets/`
- `templates/core/`
- `templates/launch/`
- `templates/review/`

除非需要查兼容旧资料，否则不要再默认从 `references/` 平铺下钻。
