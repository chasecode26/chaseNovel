# Task Contracts

This file indexes task contracts and maps them to the shipped CLI surface. Runtime behavior is defined by `docs/core/runtime-design-baseline.md` and current `runtime/` code.

## Skill Contract Index

| Skill | Contract | Responsibility |
| --- | --- | --- |
| `opening` | `references/contracts/01-launch.md` | 开书、黄金三章、卷纲、阶段目标、next-chapter readiness |
| `writer` | `references/contracts/02-write.md` | 正文生成主链、章卡到正文、runtime agent loop |
| `continue` | `references/contracts/03-continue.md` | 断点恢复、接上一章钩子、续写前状态恢复 |
| `revise` | `references/contracts/04-modify.md` | 诊断、修章、重写 handoff |
| `memory` | `references/contracts/05-state-and-rhythm.md` / `references/contracts/06-promises-and-repeat.md` | 书级状态、节奏体检、承诺重复观察、回写边界 |
| shared | `references/contracts/07-research-material.md` / `references/contracts/08-grounding-and-command.md` | 多个子 skill 共享的辅助约束 |

## CLI Mapping

- `chase open` -> `opening`
- `chase write` -> `writer`，并串联 `opening / style / memory`
- `chase quality` -> `revise` 与 shared quality gate
- `chase status` -> `memory` 与书级健康观察
- `chase check` -> dry-run 聚合链，不等于单独子 skill

公开命令保持：

```text
open / write / quality / status / check
```

写作 agent 在 `runtime/agents/` 内部实现，不新增公开 CLI 子命令。

## Default Chains

`chase write`:

```text
open -> runtime -> quality -> status
```

`chase check`:

```text
open -> quality -> status
```

`check` 必须保持 dry-run，不进入 runtime prose generation。

## Stable Aggregate Fields

`write / check` JSON should expose:

- `reference_chapter`
- `target_chapter`
- `status`
- `warning_count`
- `steps`
- `report_paths`
- `pipeline_summary`
- `final_release`

## Reading Order

1. `SKILL.md`
2. `docs/core/task-contracts.md`
3. The relevant contract under `references/contracts/`
4. `docs/core/runtime-design-baseline.md` for shipped runtime facts
