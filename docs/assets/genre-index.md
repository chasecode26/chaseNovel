# 题材资产索引

> 重构后，题材资料不再占核心主入口，而是作为资产层按需加载。

## 使用顺序

1. 先走核心主链：开书 / 写作 / 改写。
2. 只有在题材问题明确时，再补读题材资产包。
3. 一次只读 1-2 个最相关的包，避免题材资料反客为主。

## 当前资产包

- 玄幻 / 修仙：`assets/genres/xuanhuan-xiuxian/pack.md`
  - 默认资料入口：`docs/assets/xuanhuan-xiuxian-reference-map.md`
- 都市系统流：`assets/genres/dushi-system/pack.md`
  - 默认资料入口：`docs/assets/dushi-system-reference-map.md`
- 仙侠苟道：`assets/genres/goudao-xianxia/pack.md`
  - 默认资料入口：`docs/assets/goudao-xianxia-reference-map.md`
- 历史权谋：`assets/genres/historical-power/pack.md`
  - 默认资料入口：`docs/assets/historical-power-reference-map.md`
- 末世：`assets/genres/apocalypse/pack.md`
  - 默认资料入口：`docs/assets/apocalypse-reference-map.md`
- 种田文：`assets/genres/farming/pack.md`
  - 默认资料入口：`docs/assets/farming-reference-map.md`
- 盗墓 / 民国奇诡：`assets/genres/daomu-republic/pack.md`
  - 默认资料入口：`docs/assets/daomu-republic-reference-map.md`

## 其他资产

- 公共风格资产：`assets/common/`
- 结构化技法库：`assets/technique-kb/`
- 示例资产：`assets/examples/`

## 仍保留的题材旧资料

如果你维护的是老项目，以下旧资料还在 `references/`，但它们已不再是默认入口：

- 玄幻 / 修仙：统一从 `docs/assets/xuanhuan-xiuxian-reference-map.md` 进入，再按需下钻到 `assets/genres/01*.md` 与通用资料
- 都市：统一从 `docs/assets/dushi-system-reference-map.md` 进入，再按需下钻到 `references/dushi-*.md`
- 苟道：统一从 `docs/assets/goudao-xianxia-reference-map.md` 进入，再按需下钻到 `references/goudao-*.md`
- 历史：统一从 `docs/assets/historical-power-reference-map.md` 进入，再按需下钻到 `references/historical-*.md`
- 末世：统一从 `docs/assets/apocalypse-reference-map.md` 进入，再按需下钻到 `references/moshi-*.md`
- 种田 / 中天：统一从 `docs/assets/farming-reference-map.md` 进入，再按需下钻到 `references/zhongtian-*.md`
- 盗墓 / 民国：统一从 `docs/assets/daomu-republic-reference-map.md` 进入，再按需下钻到 `references/daomu-writing-notes.md`

默认策略仍然是：

- 新项目先看 `assets/genres/*/pack.md`
- 旧资料只在你明确需要兼容历史写法时再补读
