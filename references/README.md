# references

`references/` 当前处于**兼容层**定位。

这里仍保留旧版规则文档、题材资料、拆散的执行说明，目的是：
- 不立刻打断旧项目
- 允许渐进迁移
- 为后续归档与清理留缓冲

其中一部分导航型旧文档已经完成合并并已删除：
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

建议把 `references/` 理解为三类内容：
- **shim**：只负责把人导向新入口
- **legacy**：旧长文归档，不再默认阅读
- **仍有业务价值的题材/技法资料**：后续继续按需下沉或合并

当前对 `references/legacy/*` 的定位已经基本稳定：
- 可以继续保留为归档
- 但不再承担默认阅读职责
- 未来除非出现新的高频使用证据，否则不再继续拆散成更多平级入口

除非需要查兼容旧资料，否则不要再默认从 `references/` 平铺下钻。
