# 剩余优化待办清单（最终版）

## 使用说明

这份清单面向重构后的 `chaseNovel` 仓库，目标不是继续大拆大改，而是给后续维护留下一份**按优先级排序**的精修待办。

---

## 高优先级

### 1. 继续收 `references/` 重规则文档
当前仍保留但已降级的文档：
- `references/execution_workflow.md`
- `references/agent-collaboration.md`
- `references/revision-and-diagnostics.md`
- `references/craft-and-platform.md`

后续可做：
- 进一步把常用内容上提到 `docs/core/*`
- 对冷门长段落做归档或压缩
- 最终判断是否还需要整份保留

### 2. 决定根层核心模板 shim 是否长期保留
当前根层大部分核心模板已是 shim，真实内容已在 `templates/core/`。

后续可做：
- 继续保留 shim（稳定兼容）
- 或在合适版本彻底移除 shim，只保留 `templates/core/`

### 3. 决定根层 `technique-kb/` shim 是否最终移除
当前：
- 主内容已在 `assets/technique-kb/`
- 根层 `technique-kb/` 仅剩 shim README
- 脚本已优先读取资产层

后续可做：
- 保留 shim 一个周期
- 确认无兼容风险后移除根层 shim

---

## 中优先级

### 4. 压缩 README 与 SKILL 的兼容层描述
当前主结构已经稳定，但 README / SKILL 里仍保留不少“兼容说明”。

后续可做：
- 面向新用户进一步简化
- 把兼容层说明挪到单独迁移文档
- 保持 README 更像产品入口而不是迁移日志

### 5. 继续深化聚合脚本内部逻辑
当前已完成：
- 主入口收口
- 聚合脚本建立
- 聚合公共层抽取

后续可做：
- 继续减少旧单点脚本的存在感
- 让聚合脚本吸收更多共享业务逻辑
- 视情况把旧单点脚本降为纯兼容壳

### 6. 做一次 package / 分发面审查
当前 `package.json` 已包含：
- `docs`
- `assets`
- `templates`
- `technique-kb`
- `references`

后续可做：
- 确认哪些兼容层目录仍需要随包分发
- 评估未来是否减少分发冗余

---

## 低优先级 / 可选项

### 7. 为主入口补更产品化的命令文档
可选新增：
- `docs/core/cli-quickstart.md`
- `docs/core/migration-notes.md`

### 8. 给聚合入口补更多 smoke test / fixtures
尤其是：
- `open`
- `quality`
- `status`
- `write`

### 9. 清理 `.omx/` 中对旧路径的历史引用
这不会影响主运行链，但若追求仓库整洁，可后续慢慢处理。

---

## 当前建议停点

如果后续没有强需求继续重构，当前仓库已经可以作为**稳定使用版**停下：

- 主入口已收口
- 题材层已下沉
- 重复模板与重复目录已大量清除
- 兼容层边界已明确
- 关键重构总结文档已生成

也就是说，后续工作已经从“必须继续重构”变成“按需维护优化”。
