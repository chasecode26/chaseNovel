# 剩余优化待办清单

## 使用说明

这份清单面向当前已经完成主链收口的 `chaseNovel` 仓库。目标不是再做一次大拆大改，而是继续压薄兼容层、缩短默认入口、减少历史残影。

## 高优先级

### 1. 继续收紧 `references/` 的兼容边界
现状：
- 根层题材库、风格规则、开篇样本、语言审计、情绪检查等旧文，已基本降级为兼容 shim / 兼容摘要。
- 默认阅读路径已经迁到 `docs/core/*` 与 `docs/assets/*`。

后续方向：
- 禁止再把新的主规范写回 `references/` 根层。
- 继续把 `references/` 根层压成 one-screen shim，把真正仍有价值的资料继续下沉到 `docs/assets/` 或 `assets/`。

### 2. 评估根层模板 shim 的最终去留
当前仍有少量 shim：
- `templates/style-defaults.md`
- `templates/style_fingerprints.md`
- `templates/chapter-planning-review.md`
- `templates/rewrite-handoff.md`
- `templates/volume_blueprint.md`

后续要判断：
- 是继续保留一个兼容周期
- 还是在后续版本彻底迁走，只保留新位置

### 3. 决定根层 `technique-kb/` shim 是否最终移除
当前主内容已在 `assets/technique-kb/`。

## 中优先级

### 4. 继续压缩 README / SKILL 里的兼容叙述
当前入口说明已比早期版本收敛，但仍可继续把迁移说明集中到 `migration-notes.md`。

### 5. 继续强化聚合脚本
重点不是再加命令，而是：
- 继续减少旧单点脚本的存在感
- 让聚合脚本吸收更多共享业务逻辑
- 视情况把旧脚本进一步降为纯兼容壳

### 6. 继续做 package / 分发面审查
优先确认：
- `references/` 是否还需要全量随包分发
- 根层 shim 是否仍需随包存在
- 兼容目录继续缩薄后，能否同步缩包

## 低优先级 / 可选项

### 7. 给聚合入口补更多 smoke fixtures
尤其是：
- `open`
- `quality`
- `status`
- `write`
- `check`

### 8. 清理 `.omx/` 里对旧路径的历史引用
这不影响主运行链，但如果继续追求仓库整洁，可以后续慢慢处理。

## 当前建议停点

如果后续没有强需求继续重构，当前仓库已经可以作为稳定使用版继续维护：
- 主入口已收口
- 题材层已下沉
- `references/` 已明显压薄
- 关键默认文档已建立
- 后续工作已从“大重构”转成“按需压缩兼容层”
