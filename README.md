# chaseNovel

`chaseNovel` 是一套面向中文网文长篇连载的写作引擎仓库。

它解决的不是“随手给我一个 prompt 写一章”，而是让项目在几十章、几百章、甚至百万字推进后，仍能稳住：
- 节奏
- 设定
- 人物
- 伏笔
- 章尾钩子
- 文风与对白差分
- 追读动力

## 当前重构方向

当前仓库正在从“大量平铺资料 + 多个平级命令”收敛为：

- **通用长篇连载写作引擎**
- **可插拔题材资产包**

第一优先级始终是：**保证小说写作质量**。

## 现在最重要的两条主链路

### 1. 开书
- 入口：`docs/core/open-book.md`
- 目标：题材定位、卖点、黄金三章、卷纲、阶段目标、书级风格与 voice

### 2. 写作
- 入口：`docs/core/write-workflow.md`
- 目标：LeadWriter 编译上下文 -> 下发 brief -> WriterExecutor 执行 -> Evaluators 放行/阻断 -> 回写记忆 -> 书级健康检查

### 3. 状态 / 健康
- 入口：`docs/core/status-workflow.md`
- 目标：统一查看 dashboard / 伏笔 / 角色弧 / 时间线 / 重复推进风险

## 核心文档
- `SKILL.md`：技能主入口
- `docs/core/cli-quickstart.md`：CLI 快速上手
- `docs/core/open-book.md`：开书主链路
- `docs/core/write-workflow.md`：写作主链路
- `docs/core/revise-diagnostics.md`：改写与诊断
- `docs/core/style-governance.md`：文风治理
- `docs/core/status-workflow.md`：状态与书级健康
- `docs/core/task-contracts.md`：任务输出契约
- `docs/core/migration-notes.md`：兼容迁移说明
- `docs/core/legacy-cleanup-candidates.md`：兼容层清理候选清单
- `docs/core/refactor-summary.md`：本轮重构总结
- `docs/core/final-optimization-todo.md`：剩余优化待办清单
- `docs/assets/genre-index.md`：题材资产入口

## 资产层
- `assets/genres/`：题材资产包
- `assets/substyles/`：子风格资产
- `assets/common/`：公共风格资产
- `assets/examples/`：示例资产
- `assets/technique-kb/`：结构化技法库主内容
- `technique-kb/`：兼容 shim

## 当前兼容说明

已完成：
- 新的核心文档结构已建立
- 新的资产层入口已建立
- 新的模板分层已建立
- 新增了聚合别名：`chase open`、`chase quality`、`chase write`、`chase status`
- 多份旧重规则文档已降级为 shim + legacy 归档

当前尚未做的：
- 旧命令仍然保留为兼容层
- `references/` 仍保留部分旧资料，后续继续下沉/合并
- 少量根层模板仍保留 shim，避免马上打断现有工作流

## 当前可用 CLI（兼容层）
```bash
chase bootstrap --project <dir>
chase doctor --project <dir>
chase open --project <dir> [--chapter <n>]
chase quality --project <dir> [--chapter-no <n> | --from <n> --to <n>]
chase write --project <dir> [--chapter <n>] [--steps <csv>]
chase status --project <dir> [--chapter <n>] [--focus <all|dashboard|foreshadow|arc|timeline|repeat>]
chase planning --project <dir> [--chapter <n> | --target-chapter <n>]
chase context --project <dir> [--chapter <n>]
chase foreshadow --project <dir> [--chapter <n>]
chase dashboard --project <dir>
chase arc --project <dir>
chase timeline --project <dir>
chase repeat --project <dir>
chase memory --project <dir> [--chapter <n>]
chase gate --project <dir> [--chapter-no <n>]
chase draft --project <dir> [--chapter-no <n>]
chase batch --project <dir> [--from <n> --to <n>]
chase audit --project <dir> [--chapter-no <n>]
chase check --project <dir> [--chapter <n>]
chase run --project <dir> [--chapter <n>] [--steps <csv>]
```

其中：
- `open` 是新的开书入口：默认做开书 readiness 扫描，传 `--chapter` 时兼容章节规划/上下文准备
- `quality` 是新的质量闸门聚合入口，当前先聚合 gate + draft + language
- `write` 是新的写作聚合入口，默认优先走 `doctor + open + runtime + status`
- `status` 是新的书级健康聚合别名，当前聚合 dashboard / foreshadow / arc / timeline / repeat，并返回 `runtime_signals`
- 旧 `planning/context/gate/draft/audit/batch/foreshadow/arc/timeline/repeat/dashboard` 现在都属于兼容别名，内部会转到新聚合入口
- `quality` 当前支持统一子检查协议：`--check all|chapter|draft|language|batch`
- `check` 现在也优先走 `doctor + open + status`

## 仓库维护校验
```bash
npm run smoke
```

它当前会做四件事：
- 检查 `chase --help`
- 编译全部 Python 脚本语法
- 跑一轮临时项目 fixture：`bootstrap -> doctor -> open -> status`
- 执行 `npm pack --dry-run`

## 当前维护状态

当前仓库已经进入“稳定维护版”阶段：
- 主入口已收口
- `docs/core/*` 已成为默认阅读路径
- `references/` 主要承担兼容层与题材资料层职责
- `references/legacy/` 仅保留源码仓库归档，不再进入 npm 分发包
- 根层若干模板只保留 shim，真实内容已下沉到分层目录

这意味着后续工作更偏向：
- 维护型优化
- fixture / smoke 校验增强
- 分发面继续瘦身
- 兼容层按需清理

## npm 分发策略

当前 npm 包默认分发：
- `docs/`
- `assets/`
- `templates/`
- `schemas/`
- `scripts/*.py`
- 仍有默认入口价值的 `references/*`
- `references/contracts/*`

当前 npm 包默认不分发：
- `references/legacy/*`
- 若干零引用、仅源码仓库保留的旧参考文档

如果你维护的是源码仓库，可以看到完整归档；如果你消费的是 npm 包，拿到的是更偏“当前可用主路径”的精简分发面。

## 推荐阅读顺序
1. `SKILL.md`
2. `docs/core/cli-quickstart.md`
3. `docs/core/open-book.md` 或 `docs/core/write-workflow.md`
4. `docs/core/status-workflow.md`
5. `docs/core/revise-diagnostics.md`
6. `docs/core/style-governance.md`
7. `docs/assets/genre-index.md`
8. 需要兼容旧项目时再看 `docs/core/migration-notes.md`

## 仓库结构（Phase 1 后）
```text
repo/
├─ SKILL.md
├─ README.md
├─ ARCHITECTURE.md
├─ bin/
├─ docs/
│  ├─ core/
│  └─ assets/
├─ assets/
│  ├─ genres/
│  ├─ substyles/
│  ├─ common/
│  ├─ examples/
│  └─ technique-kb/
├─ references/        # 兼容保留，后续继续下沉/合并
├─ templates/         # 当前主模板层：core/launch/review
├─ technique-kb/      # 兼容 shim
├─ scripts/
└─ schemas/
```

