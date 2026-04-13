# chaseNovel 重构总结

## 背景

本轮重构的目标不是单纯缩小仓库，而是把 `chaseNovel` 从“散命令 + 散脚本 + 散文档 + 散题材资料”的形态，收敛成：

- **通用长篇连载写作引擎**
- **可插拔题材资产包**

并且始终以 **小说写作质量第一** 为最高约束。

---

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
- `open`：开书入口；默认做开书 readiness 扫描，传 `--chapter` 时兼容章节规划
- `quality`：统一质量门；支持 `--check all|chapter|draft|language|batch`
- `write`：写作主链；默认优先走 `doctor + open + memory + status`
- `status`：统一书级健康入口；支持 `--focus all|dashboard|foreshadow|arc|timeline|repeat`

旧命令 `planning/context/gate/draft/audit/batch/foreshadow/arc/timeline/repeat/dashboard` 仍保留，但已经降级为兼容别名。

---

### 2. 新文档主结构建立

当前默认文档入口已经迁到：

- `docs/core/open-book.md`
- `docs/core/write-workflow.md`
- `docs/core/status-workflow.md`
- `docs/core/revise-diagnostics.md`
- `docs/core/style-governance.md`
- `docs/core/task-contracts.md`
- `docs/assets/genre-index.md`

这些文档已经替代了原来大量散落在 `references/` 和根层模板中的主流程入口。

---

### 3. 新模板主结构建立

当前模板主层已经收口为：

- `templates/core/`
- `templates/launch/`
- `templates/review/`

其中：
- `templates/core/`：项目记忆核心模板
- `templates/launch/`：开书 / 起盘 / 结果与钩子 / 世界与设定工具包
- `templates/review/`：复核 / 诊断 / 回交模板

`project_bootstrap.py` 已经改成优先从 `templates/core/` 取模板，说明新项目已经开始真正使用新结构。

---

### 4. 新资产层建立

题材与子风格已经从模板主层彻底迁到资产层：

- `assets/genres/`
- `assets/substyles/`
- `assets/common/`
- `assets/examples/`
- `assets/technique-kb/`

这意味着题材资料不再和核心写作引擎混居主入口层。

---

### 5. 聚合脚本层建立

为了把主链路和旧散脚本收口，当前已建立：

- `scripts/open_book.py`
- `scripts/planning_context.py`
- `scripts/quality_gate.py`
- `scripts/book_health.py`
- `scripts/engine_runner.py`
- `scripts/memory_sync.py`
- `scripts/bootstrap.py`
- `scripts/doctor.py`

它们和新的主入口一一对应。

---

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

这意味着聚合脚本已经不再是简单复制粘贴式包装器，而开始共享真正的基础编排逻辑。

---

## 本轮已真实删除的内容

### references
- `references/advanced-template-map.md`
- `references/genre-asset-index.md`
- `references/output-contracts.md`

### templates 根层旧模板
- `templates/causality-review-card.md`
- `templates/continuity-review-card.md`
- `templates/style-consistency-review.md`
- `templates/reviewer-stage-retro.md`
- `templates/language-anti-ai-review.md`
- `templates/opening-route-cheatsheet.md`
- `templates/golden-three-route-cheatsheet.md`
- `templates/genre-writing-guide.md`
- `templates/result-route-cheatsheet.md`
- `templates/hook-route-cheatsheet.md`
- `templates/opening-setup-checklist.md`
- `templates/worldbuilding-index.md`
- `templates/midgame-fatigue-cheatsheet.md`

### 重复目录
- `templates/genres/`
- `templates/substyles/`

### 运行产物
- `scripts/__pycache__/`

---

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
这些文档仍保留详细内容，但已经加了兼容层提示头，不再作为默认主入口：
- `references/execution_workflow.md`
- `references/agent-collaboration.md`
- `references/revision-and-diagnostics.md`
- `references/craft-and-platform.md`

### 3. 根层仍保留的少量模板
这些模板中的大部分已经被改成兼容 shim，主内容实际收口到 `templates/core/`：
- `templates/core/plan.md`
- `templates/core/state.md`
- `templates/core/style.md`
- `templates/core/voice.md`
- `templates/core/characters.md`
- `templates/core/character-arcs.md`
- `templates/core/foreshadowing.md`
- `templates/core/payoff-board.md`
- `templates/core/timeline.md`
- `templates/core/findings.md`
- `templates/core/scene_preferences.md`
- `templates/core/summaries_recent.md`
- `templates/core/character-voice-diff.md`

当前仍真正保留主内容的根层模板，主要剩：
- `templates/continuity-report.md`

未来可继续评估是否连 shim 也进一步收掉，只保留 `templates/core/`。

---

## 当前仓库结构（收敛后）

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
├─ references/      # 兼容层，保留重规则文档
├─ templates/
│  ├─ core/
│  ├─ launch/
│  └─ review/
├─ technique-kb/    # 旧路径 shim
├─ scripts/
└─ schemas/
```

---

## 为什么这轮重构是有效的

因为它不是“为了整洁而整洁”，而是实质上做了这几件事：

1. **减少了主入口数量**：从大量平级命令收敛成少数主入口
2. **减少了主入口歧义**：现在更容易判断“开书 / 写作 / 状态 / 质量”分别该去哪
3. **把题材资料与核心引擎分开**：防止题材资产继续污染主链路
4. **减少了重复模板维护**：很多旧模板已被 shim 或删除
5. **给后续维护留下了可持续结构**：新入口、新模板层、新资产层、新聚合脚本层都已经建好

---

## 当前剩余风险

1. `references/` 里仍保留一些重规则文档，未来可能继续收敛或归档
2. 根层少量核心模板还没有完全切换为只保留 `templates/core/`
3. `technique-kb/` 主内容已迁到 `assets/technique-kb/`；根层仅保留 shim 说明
4. 某些历史计划文档和 `.omx/` 文件仍会提到旧路径，但不影响主运行链

---

## 后续建议

### 若继续重构
优先级建议：

1. 评估 `references/` 中哪些重规则文档还能继续拆分、归档或彻底让位给 `docs/core/*`
2. 评估根层核心模板是否可完全切换到 `templates/core/`
3. 评估未来是否彻底移除根层 `technique-kb/` shim

### 若准备稳定使用
现在已经可以把这套结构当作新的工作基线：

- 开书：`open`
- 写作：`write`
- 质量门：`quality`
- 状态检查：`status`
- 阅读入口：`docs/core/*` + `docs/assets/*`
- 模板入口：`templates/core/*` + `templates/launch/*` + `templates/review/*`
- 题材入口：`assets/genres/*`

---

## 一句话结论

这轮重构已经把 `chaseNovel` 从“功能很多但边界发散的技能仓库”，推进成了一套 **主入口清晰、资产层分明、兼容层可控、以小说质量为中心的长篇连载写作引擎**。

