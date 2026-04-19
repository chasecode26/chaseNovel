# chaseNovel 重构总结

## 背景

本轮重构的目标不是单纯缩小仓库，而是把 `chaseNovel` 从“散命令 + 散脚本 + 散文档 + 散题材资料”的形态，收敛成：

- 通用长篇连载写作引擎
- 可插拔题材资产包

并且始终以小说写作质量第一为最高约束。

## 本轮重构完成了什么

### 1. 主入口收口

当前主入口已经收口为：

- `bootstrap`
- `doctor`
- `open`
- `quality`
- `write`
- `status`
- `check`

其中：
- `open`：开书与下一章 planning/context 预审入口
- `quality`：统一质量门；支持 `--check all|chapter|draft|language|batch`
- `write`：写作主链；默认走 `doctor,open,runtime,quality,status`
- `status`：统一书级健康入口；支持 `--focus all|dashboard|foreshadow|arc|timeline|repeat`
- `check`：dry-run 检查链；默认走 `doctor,open,quality,status`

旧命令 `planning/context/gate/draft/audit/batch/foreshadow/arc/timeline/repeat/dashboard/run` 仍保留，但已经降级为兼容别名。

### 2. 新文档主结构建立

当前默认文档入口已经迁到：

- `docs/core/open-book.md`
- `docs/core/write-workflow.md`
- `docs/core/status-workflow.md`
- `docs/core/revise-diagnostics.md`
- `docs/core/style-governance.md`
- `docs/core/task-contracts.md`
- `docs/core/cli-quickstart.md`
- `docs/assets/genre-index.md`

这些文档已经替代了原来大量散落在 `references/` 和根层模板中的主流程入口。

### 3. 新模板主结构建立

当前模板主层已经收口为：

- `templates/core/`
- `templates/launch/`
- `templates/review/`

其中：
- `templates/core/`：项目记忆核心模板
- `templates/launch/`：开书 / 起盘 / 结果与钩子 / 世界与设定工具包
- `templates/review/`：复核 / 诊断 / 回交模板

`project_bootstrap.py` 已经改成优先从 `templates/core/` 取模板，说明新项目已真正使用新结构。

### 4. 新资产层建立

题材与子风格已经从模板主层迁到资产层：

- `assets/genres/`
- `assets/substyles/`
- `assets/common/`
- `assets/examples/`
- `assets/technique-kb/`

这意味着题材资料不再和核心写作引擎混居主入口层。

### 5. 聚合脚本层建立

为了把主链路和旧散脚本收口，当前已建立并对齐：

- `scripts/open_book.py`
- `scripts/planning_context.py`
- `scripts/quality_gate.py`
- `scripts/book_health.py`
- `scripts/workflow_runner.py`
- `scripts/project_bootstrap.py`
- `scripts/project_doctor.py`

其中 `workflow_runner.py` 是当前 shipped 聚合编排入口，负责 `write / run / check` 的统一输出。

### 6. 聚合公共层建立

当前已抽出：

- `scripts/aggregation_utils.py`

用于统一处理：
- UTF-8 输出
- 子脚本 JSON 调用
- 聚合状态汇总
- warning 收集
- report_paths 收集
- traceback 压缩

### 7. 聚合语义补齐

当前聚合层已经补齐：

- `reference_chapter` / `target_chapter` 双语义
- `pipeline_summary`
- 顶层 `final_release`
- markdown `pipeline_report.md` 聚合报告

这意味着上层 CLI、烟测和外部调用方都能直接消费统一结果，而不必反复读各子脚本细节。

## 本轮已真实删除或降级的内容

### references
- obsolete reference index docs

### templates 根层旧模板
- deprecated review cards
- duplicated route cheatsheets
- duplicated root-level writing guides
- legacy continuity / language anti-AI / style consistency review templates merged into `templates/review/chapter-quality-review.md`

### 重复目录
- duplicated genre and substyle template directories

### 运行产物
- generated caches and build artifacts

## 仍保留但已降级为兼容层的内容

### 1. 旧 CLI 命令名
仍可用，但已不是主入口：

- `planning`
- `context`
- `gate`
- `draft`
- `audit`
- `batch`
- `dashboard`
- `foreshadow`
- `arc`
- `timeline`
- `repeat`
- `memory`
- `run`

### 2. `references/` 中的重规则文档
这些文档仍保留详细内容，但已不再作为默认主入口：

- `references/execution_workflow.md`
- `references/agent-collaboration.md`
- `references/revision-and-diagnostics.md`
- `references/craft-and-platform.md`

### 3. 根层少量 shim
这些 shim 仍可继续评估是否后续彻底移除：

- `templates/style-defaults.md`
- `templates/style_fingerprints.md`
- `templates/chapter-planning-review.md`
- `templates/rewrite-handoff.md`
- `templates/volume_blueprint.md`
- root `technique-kb/`

## 当前仓库结构

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

## 当前剩余风险

1. `references/` 中仍保留一些重规则文档，未来可能继续收敛或归档
2. 根层少量 shim 还没有完全移除
3. 某些历史计划文档和 `.omx/` 文件仍会提到旧路径，但不影响主运行链

## 后续建议

### 若继续重构
优先级建议：

1. 继续压薄 `references/`
2. 继续评估根层 shim 是否还有保留价值
3. 继续清理 `.omx/` 中对旧路径的历史引用

### 若准备稳定使用
现在已经可以把这套结构当作新的工作基线：

- 开书：`open`
- 写作：`write`
- 质量门：`quality`
- 状态检查：`status`
- dry-run 扫链：`check`
- 阅读入口：`docs/core/*` + `docs/assets/*`
- 模板入口：`templates/core/*` + `templates/launch/*` + `templates/review/*`
- 题材入口：`assets/genres/*`

## 一句话结论

这轮重构已经把 `chaseNovel` 从“功能很多但边界发散的技能仓库”，推进成了一套主入口清晰、资产层分明、兼容层可控、以小说质量为中心的长篇连载写作引擎。
