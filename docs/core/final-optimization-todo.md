# 剩余优化待办清单

## 使用说明

这份清单面向当前 Phase 1.5 的 `chaseNovel` 仓库。  
目标不是再做一次大拆大改，而是继续把兼容层压薄、把默认入口做短。

---

## 高优先级

### 1. 继续压薄 `references/`
优先对象：
- `references/anti-repeat-rules.md`
- `references/writing-patterns.md`
- 题材路由类旧文档

方向：
- 把默认阅读路径继续迁到 `docs/core/*` 与 `docs/assets/*`
- `references/*` 逐步只保留“旧资料归档”价值

### 2. 评估根层模板 shim 的最终去留
当前根层已有多份 shim：
- `templates/style-defaults.md`
- `templates/style_fingerprints.md`
- `templates/chapter-planning-review.md`
- `templates/rewrite-handoff.md`
- `templates/volume_blueprint.md`

后续要判断：
- 是继续保留一个兼容周期
- 还是在后续版本彻底移除，只保留新位置

### 3. 决定根层 `technique-kb/` shim 是否最终移除
当前主内容已全部在 `assets/technique-kb/`。

---

## 中优先级

### 4. 继续压缩 README / SKILL 中的兼容叙述
当前已经比 Phase 1 更收敛，但仍可继续把迁移信息往 `migration-notes.md` 集中。

### 5. 继续深化聚合脚本
重点不是“再加命令”，而是：
- 继续减少旧单点脚本的存在感
- 让聚合脚本吸收更多共享业务逻辑
- 视情况把旧脚本降为纯兼容壳

### 6. 继续做 package / 分发面审查
优先确认：
- `references/` 是否需要全量随包分发
- 根层 shim 是否需要继续随包存在
- 兼容目录减少后是否可以进一步缩包

---

## 低优先级 / 可选项

### 7. 给聚合入口补更多 smoke test / fixtures
尤其是：
- `open`
- `quality`
- `status`
- `write`

### 8. 清理 `.omx/` 中对旧路径的历史引用
这不会影响主运行链，但若追求仓库整洁，可后续慢慢处理。

---

## 当前建议停点

如果后续没有强需求继续重构，当前仓库已经可以作为**稳定使用版**继续维护：

- 主入口已收口
- 题材层已下沉
- 兼容 shim 已经变薄
- 关键默认文档已建立
- 后续工作已从“继续大重构”转成“按需压缩兼容层”
