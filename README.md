# chaseNovel

`chaseNovel` 是一套面向中文网文长篇连载的本地写作引擎仓库。
它关注的不是“随手写一章”，而是让项目在几十章、几百章后仍能稳住节奏、设定、人物、伏笔、章尾钩子与书级状态。

## 主入口

默认只看四条主链：
1. 开书：`docs/core/open-book.md`
2. 写作：`docs/core/write-workflow.md`
3. 质量：`docs/core/revise-diagnostics.md` / `docs/core/task-contracts.md`
4. 状态：`docs/core/status-workflow.md`

CLI 主入口：

```bash
chase open --project <dir> [--chapter <n> | --target-chapter <n>]
chase quality --project <dir> [--chapter-no <n> | --from <n> --to <n>]
chase write --project <dir> [--chapter <n> | --target-chapter <n>] [--steps <csv>]
chase status --project <dir> [--chapter <n>] [--focus <all|dashboard|foreshadow|arc|timeline|repeat>]
chase check --project <dir> [--chapter <n> | --target-chapter <n>]
```

兼容命令仍可用，但不再作为默认心智入口。

## 当前运行事实

- `scripts/workflow_runner.py` 是现行 shipped 聚合编排入口。
- `write / run / check` 都走聚合链。
- `check` 当前默认链路是 `doctor,open,quality,status`，保持 dry-run，但会显式补做 quality 关卡。
- `open / planning / context` 负责下一章准备。
- `status / memory / runtime / quality` 负责当前参考章检查或回写。
- `engine_runner` 只是未来可选重命名方向，不是当前主链入口。

## 章节语义

- `--chapter <n>` 在聚合链中表示当前已经写完的 reference chapter。
- `open / planning / context` 会把它视为“当前已写章节”，默认准备 `target_chapter = n + 1`。
- 需要跳章、补章、回头指定目标章时，显式传 `--target-chapter <m>`。
- `status / runtime / memory / quality` 不会自动把 `--chapter` 加一。

## 核心文档

- `SKILL.md`
- `docs/core/cli-quickstart.md`
- `docs/core/runtime-design-baseline.md`
- `docs/core/open-book.md`
- `docs/core/write-workflow.md`
- `docs/core/revise-diagnostics.md`
- `docs/core/style-governance.md`
- `docs/core/status-workflow.md`
- `docs/core/task-contracts.md`
- `docs/assets/genre-index.md`
- `docs/assets/xuanhuan-xiuxian-reference-map.md`
- `docs/assets/dushi-system-reference-map.md`
- `docs/assets/goudao-xianxia-reference-map.md`
- `docs/assets/historical-power-reference-map.md`
- `docs/assets/apocalypse-reference-map.md`
- `docs/assets/farming-reference-map.md`
- `docs/assets/daomu-republic-reference-map.md`

## Design Baseline

- Recovered design spec: `docs/superpowers/specs/2026-04-14-leadwriter-runtime-design.md`
- Recovered implementation plan: `docs/superpowers/plans/2026-04-14-leadwriter-runtime.md`
- Runtime alignment note: `docs/core/runtime-design-baseline.md`

## 仓库校验

```bash
npm run smoke
node ./scripts/change_analyzer.js --mode working --json
```

当前会做：
- 检查 `chase --help`
- 编译全部 Python 脚本语法
- 跑一轮 fixture 主链
- 执行 `npm pack --dry-run`

`change_analyzer` 用于提交前验更，支持：
- `--mode working`：检查当前工作区全部变更
- `--mode staged`：只检查暂存区
- `--mode committed`：只检查最近一次提交
- `--json`：输出机器可消费的分类、模块、告警与建议
- `--summary-only`：只保留摘要、模块、告警，不回传逐文件列表
- `--max-files <n>`：在保留摘要的同时，只返回前 `n` 个文件明细，并显式标记省略数量
- `--category <code|docs|tests|config|other>`：只看单一类别变更，适合重构期快速切到代码视角或文档视角
- `--module <name>`：只看单一模块桶，例如 `scripts`、`references`、`docs/core`
- `--module-prefix <prefix>`：只看一整组模块家族，例如 `docs`、`references`，但仍保留细分模块统计
- `--top-modules <n>`：模块很多时只保留前 `n` 个模块摘要，便于先抓主战场
- 当使用 `--category` / `--module` / `--module-prefix` 时，输出仍会保留 `global_warnings` 与 `global_recommendations`，避免局部筛选掩盖全局风险
- 如果本轮存在删除文件，输出会附带 `deleted_reference_hits` / `global_deleted_reference_hits`，把仍在引用旧路径的位置直接列出来

## 当前状态

仓库已进入聚合主链稳定维护阶段：
- `docs/core/*` 是默认阅读面
- 聚合层章节语义已统一为 `reference_chapter / target_chapter`
- `references/` 主要承担兼容层与资料层职责
- 根层只保留少量仍有兼容价值的 shim

## 仓库结构

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
├─ references/
├─ templates/
│  ├─ core/
│  ├─ launch/
│  └─ review/
├─ scripts/
├─ runtime/
├─ evaluators/
└─ schemas/
```
