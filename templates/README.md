# templates

当前模板层已经按用途分层：

- `templates/core/`：项目记忆核心模板
- `templates/launch/`：开书 / 起盘 / 章节结果工具包
- `templates/review/`：复核 / 诊断 / 回交模板

仓库根层当前只保留少量仍有兼容价值或脚本依赖的模板文件。
核心模板主内容已经统一收口到 `templates/core/`。

题材与子风格模板已迁移到：
- `assets/genres/`
- `assets/substyles/`

新的默认使用顺序：
1. 先看 `templates/core/`
2. 开书时补 `templates/launch/`
3. 复核时补 `templates/review/`
4. 题材 / 子风格按需去 `assets/genres/` 与 `assets/substyles/`
