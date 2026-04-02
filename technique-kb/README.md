# technique-kb

最小可用的长篇小说语言技法知识库。

目标不是“收藏素材”，而是沉淀可以被人和脚本复用的结构化知识：

- 什么表达是高风险坏句
- 什么改写策略能保剧情不动地消掉僵硬感
- 什么场景该按什么顺序落地
- 什么题材允许什么口吻，不允许什么口吻

## 目录

```text
technique-kb/
├── README.md
├── schemas/
│   ├── pattern.schema.json
│   ├── recipe.schema.json
│   └── profile.schema.json
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

### pattern

用于记录单个表达模式，可分为：

- `negative`：坏句、坏段、坏旁白
- `positive`：自然表达、有效旁白、落地气氛
- `rewrite_pair`：原句到改句的对照

### recipe

用于记录场景写法配方，例如：

- 压迫
- 暧昧
- 危险
- 悬疑
- 打斗

### profile

用于记录口吻边界：

- `genre profile`：题材级通用规则
- `book profile`：单书级规则，优先级更高

## 使用规则

1. 新增条目优先写成结构化 JSON，不要直接堆长文摘录。
2. `bad_example` 和 `good_example` 保持短小，只用于说明模式，不做大段素材堆积。
3. 每个条目至少带一个可检索标签，例如：`authorial_narration`、`forced_atmosphere`、`romance_tension`。
4. `book profile` 高于 `genre profile`。
5. 同类条目优先补已有标签，不另造近义标签。

## 当前最小目标

先围绕这四类问题积累知识：

1. 作者式旁白
2. 强行气氛渲染
3. 抽象词堆叠
4. 局部改写对照

后续脚本接入时，优先消费：

- `patterns/negative/*.json`
- `patterns/rewrite_pairs/*.json`
- `recipes/scene/*.json`
- `profiles/genre/*.json`
- `profiles/book/*.json`

## book profile 使用约定

`profiles/book/` 用于维护“某一本书”的长期口吻真相源，优先级高于 `genre profile`。

建议命名：

- `book_<书名或代号>.json`

建议字段：

- `name`：书名或代号
- `genre`：基础题材
- `narration_rules`：这本书自己允许的旁白方式
- `forbidden_phrases` / `forbidden_words`
- `preferred_patterns`

接入顺序建议：

1. `genre profile` 先兜底
2. `book profile` 再覆盖
3. `00_memory/style.md` 最后补充临时或实验性约束
- `profiles/genre/*.json`
