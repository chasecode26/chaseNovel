# chaseNovel（中文网文连载写作器）

面向中文长篇网文平台连载的写作技能与辅助工具集。
它不仅能写单章，还提供章卡、项目记忆、连续性门禁、语言审计、风格约束和题材技法知识库，用来支撑长期连载。

## ✨ 核心特性升级

- **🖋️ 风格约束与项目记忆**：支持以 `plan.md`、`state.md`、`style.md` 等文件维护长期连载状态，减少断更、跳设定和口吻漂移。
- **🛡️ 覆写优先级**：默认按【书级规则 / 题材规则】 > 【当前大纲目标】 > 【通用写法基线】处理冲突，避免不同规则互相打架。
- **📚 题材知识库**：提供按题材拆分的 profile、pattern、rewrite pair、scene recipe，当前已补到权谋、玄幻、种田、系统流、末世等方向。
- **⚙️ 长篇辅助资产**：
  - `power_economy_constraint.md`：力量体系防通胀
  - `antagonist_design.md`：反派与配角设计
  - `romance_arc.md`：感情线节奏管理
  - `ending_blueprint.md`：结局规划
  - `break_writers_block.md`：卡文诊断与急救
- **🔪 语言审计与门禁**：支持章节连续性检查、语言审计、建议改写与结果报告，不把“能写出来”直接当成“可发稿”。

## 🧭 资源分工

当前项目不是“所有规则都堆在一个提示词文件里”，而是拆成三层：

- `templates/`：给人看的模板、章卡骨架、题材写法提示、长期规划工具。
- `technique-kb/`：给脚本与人工共用的结构化技法库，包含题材 profile、坏模式、好模式、改写对照、场景配方。
- `scripts/`：自动执行层，负责 gate、语言审计、自检与报告生成。

简单理解：

- 想开书、搭章卡、定 `style.md`，先看 `templates/`
- 想让系统自动识别“这句为什么硬”“这种题材该怎么改”，靠 `technique-kb/`
- 想让知识库真正生效，走 `scripts/`

## 🤖 知识库是否自动调用

会，但不是 README/Skill 文本自己“自动读目录”，而是脚本层自动加载：

- `python scripts/language_audit.py ...`
  会自动读取：
  - `technique-kb/profiles/genre/*`
  - `technique-kb/profiles/book/*`
  - `technique-kb/patterns/negative/*`
  - `technique-kb/patterns/positive/*`
  - `technique-kb/patterns/rewrite_pairs/*`
  - `technique-kb/recipes/scene/*`
- `python scripts/chapter_gate.py ...`
  会继续调用 `language_audit.py`，因此也会自动吃完整 knowledge base。

反过来，`templates/*.md` 不会被上述脚本自动全文读取。模板默认只在人工写作、人工定风格、人工修章时按需补读。

## ✅ 当前已完成的闭环

当前这套能力链已经闭环，不再只是 prompt 集合：

- `SKILL.md`：定义写作工作流、读取策略、门禁规则
- `templates/`：提供人工写作和校风格时要用的骨架
- `technique-kb/`：提供题材 profile、场景 recipe、正反 pattern、rewrite pair
- `scripts/language_audit.py`：单章语言审计与建议改写
- `scripts/chapter_gate.py`：单章 continuity + language gate
- `scripts/batch_gate.py`：整本书批量回归与汇总报告

换言之，现在已经具备：

- 单章写作
- 单章语言质检
- 单章 continuity gate
- 书级/题材级知识库接入
- 整本书批量回归

## 🎯 基础操作

- `/一键开书`：生成包含核心卖点、冲突、阶段目标与卷节奏的开局方案。
- `/写`：根据章卡起草正文，严格遵守“先行动后信息”、“章尾必留悬念”铁律。
- `/修改` / `/续写`：定向修章、状态恢复、应对断更。
- `/防重复` / `/查承诺` / `/定风格`：随时调出辅助功能进行节奏干预。

### 常用脚本命令

```bash
python scripts/language_audit.py --project "novel_书名" --chapter-no 12
python scripts/language_audit.py --project "novel_书名" --chapter-no 12 --mode suggest
python scripts/chapter_gate.py --project "novel_书名" --chapter-no 12
python scripts/chapter_gate.py --project "novel_书名" --chapter-no 12 --rewrite-out "04_gate/ch012/rewrite.md"
python scripts/batch_gate.py --project "novel_书名"
python scripts/batch_gate.py --project "novel_书名" --from 1 --to 30 --json
```

对应产物：

- 单章语言审计：`04_gate/chXXX/language_report.md` / `language_report.json`
- 单章门禁：`04_gate/chXXX/continuity_report.md` / `result.json`
- 批量回归：`04_gate/batch_gate_summary.json` / `batch_gate_summary.md`

## ⚡ 5 分钟上手

如果你现在手上已经有一本书，最短路径如下：

1. 准备项目目录，至少包含：
   - `00_memory/plan.md`
   - `00_memory/state.md`
   - `00_memory/style.md`
   - `03_chapters/第001章_xxx.md`
2. 先补 `style.md`
   - 不知道怎么写时，先参考 `templates/style.md`
   - 若题材明确，优先把题材、禁句、慎用词、阈值写进去
3. 先跑单章语言审计：

```bash
python scripts/language_audit.py --project "novel_书名" --chapter-no 1 --mode suggest
```

4. 再跑单章门禁：

```bash
python scripts/chapter_gate.py --project "novel_书名" --chapter-no 1
```

5. 单章没问题后，再跑整本书回归：

```bash
python scripts/batch_gate.py --project "novel_书名"
```

6. 重点看三个位置：
   - `04_gate/chXXX/language_report.md`
   - `04_gate/chXXX/continuity_report.md`
   - `04_gate/batch_gate_summary.md`

如果你现在还没有项目文件，先用 `templates/` 把 `plan.md`、`state.md`、`style.md` 起出来，再开始写正文和跑 gate。

## 🚀 一键安装

最小推荐方式：

```bash
npx chase-novel-skill install
```

常用命令：

```bash
npx chase-novel-skill install
npx chase-novel-skill update
npx chase-novel-skill doctor
```

默认安装目录：

```text
~/.claude/skills/chaseNovel
```

若要安装到自定义目录：

```bash
npx chase-novel-skill install --target /custom/path/chaseNovel
```

## 📂 项目架构

- `SKILL.md`：引擎主控，定义路由、读取策略、门禁规则与资源职责。
- `references/`：长规则、诊断说明、输出契约、语言治理说明。
- `templates/`：模板、示例、题材写法资产，主要给人工工作流使用。
- `technique-kb/`：结构化技法知识库，主要给脚本与人工共用。
- `scripts/`：自动化执行层。
- `scripts/chapter_gate.py`：章节级 continuity + language gate，输出 `04_gate/chXXX/continuity_report.md` 与 `result.json`。
- `scripts/language_audit.py`：语言审计与建议改写入口，自动消费 `technique-kb/`。
- `scripts/batch_gate.py`：整本书批量回归入口，输出 `04_gate/batch_gate_summary.json` 与 `batch_gate_summary.md`。

## 适用场景

适合立志完成 **50 万字以上连载**、渴望跳出普通 AI 水文泥潭、需精准控制追读率与爽感节奏、追求**网文白金作家级文字质感**的文字创作者。
