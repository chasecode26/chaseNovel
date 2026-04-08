# technique-kb

`technique-kb` 是 `chaseNovel` 的结构化技法库。

它不收藏素材，不堆长文摘录，只沉淀能被人和脚本复用的最小知识单元：

- 哪类表达有高风险
- 同一句子怎么改得更落地
- 某类场景通常按什么顺序推进
- 某个题材默认允许什么口吻、限制什么口吻

## 目录

```text
technique-kb/
├── schemas/
├── patterns/
│   ├── negative/
│   ├── positive/
│   └── rewrite_pairs/
├── recipes/
│   └── scene/
└── profiles/
    ├── genre/
    └── book/
```

## 条目类型

- `pattern`
  - `negative`：坏句、坏段、坏旁白
  - `positive`：自然表达、有效推进、落地气氛
  - `rewrite_pair`：原句到改句的对照
- `recipe`
  - 场景写法配方，例如压迫、暧昧、危险、悬疑、开篇抓手、黄金三章递进、章尾钩子
- `profile`
  - `genre profile`：题材级兜底规则
  - `book profile`：单书级覆盖规则，优先级更高

## 使用规则

1. 新增条目优先写成结构化 JSON，不要直接堆长文。
2. `bad_example` 和 `good_example` 保持短小，只说明模式，不做素材仓库。
3. 每个条目至少带一个可检索标签。
4. 同类条目优先补已有标签，不另造近义标签。
5. 覆盖顺序默认是：`genre profile -> book profile -> 00_memory/style.md`。

## 维护边界

- 这里保存“可复用的最小规则”，不保存整篇教程。
- 若一句 `notes` 只是把 `goal`、`problem` 或 `scene` 换句话说，直接删。
- 若某条目已经被上层模板完整覆盖，不再在这里重复展开。
