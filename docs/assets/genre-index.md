# 题材资产索引

> 重构后，题材资料不再占核心主入口，而是作为资产层按需加载。

## 使用顺序
1. 先走核心主链：开书 / 写作 / 改写
2. 只有在题材问题明确时，再补读题材资产包
3. 一次只读 1-2 个最相关的包，避免题材资料反客为主

## 当前资产包
- 都市系统流：`assets/genres/dushi-system/pack.md`
- 仙侠苟道：`assets/genres/goudao-xianxia/pack.md`
- 历史权谋：`assets/genres/historical-power/pack.md`
- 末世：`assets/genres/apocalypse/pack.md`
- 种田文：`assets/genres/farming/pack.md`
- 盗墓 / 民国奇诡：`assets/genres/daomu-republic/pack.md`

## 其他资产
- 公共风格资产：`assets/common/`
- 结构化技法库：`assets/technique-kb/`（Phase 1 先保留旧物理路径兼容）
- 示例资产：`assets/examples/`

## 仍保留的题材旧资料
如果你维护的是老项目，以下旧资料还在 `references/`，但它们已不再是默认入口：

- 都市：`references/dushi-volume-route-library.md`
- 苟道：`references/goudao-volume-route-library.md`
- 历史：`references/historical-volume-route-library.md`
- 末世：`references/moshi-volume-route-library.md`
- 种田 / 中田：`references/zhongtian-volume-route-library.md`
- 盗墓 / 民国：`references/daomu-writing-notes.md`

默认策略仍然是：
- 新项目先看 `assets/genres/*/pack.md`
- 旧资料只在你明确需要兼容历史写法时再补读
