# templates

当前模板层已经按用途分层：

- `templates/core/`：项目记忆核心模板
- `templates/launch/`：开书 / 起盘 / 章节结果工具包
- `templates/review/`：复核 / 诊断 / 回交模板

仓库根层当前只保留少量仍有兼容价值或脚本依赖的模板文件。
核心模板主内容已经统一收口到 `templates/core/`。

题材与子风格模板已迁移到：
- `docs/assets/` 作为题材资料默认入口
- `assets/genres/` 作为题材资产包
- `assets/substyles/` 作为子风格资产包

新的默认使用顺序：
1. 先看 `templates/core/`
2. 开书时补 `templates/launch/`
3. 复核时补 `templates/review/`
4. 题材先从 `docs/assets/genre-index.md` 进入，再按需读取对应 `docs/assets/*-reference-map.md`
5. 子风格按需去 `assets/substyles/`

根层仍保留的少量文件，大多只是兼容 shim：
- `templates/style-defaults.md` -> `assets/common/style-defaults.md`
- `templates/style_fingerprints.md` -> `assets/common/style-fingerprints.md`
- `templates/chapter-planning-review.md` -> `templates/review/chapter-planning-review.md`
- `templates/rewrite-handoff.md` -> `templates/review/rewrite-handoff.md`
- `templates/volume_blueprint.md` -> `templates/launch/volume-blueprint.md`
- legacy continuity / language anti-AI / style consistency review templates
  -> merged into `templates/review/chapter-quality-review.md`
