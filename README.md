# chaseNovel

优先导航：

- `references/genre-asset-index.md`
  用来先判断这次该读哪份题材资产，再下钻到历史权谋、末世囤货、仙侠苟道、都市系统流、种田文的专项文档

面向中文网文平台连载的写作技能与辅助工具集，现已收口为“技能入口 + 模板资产 + 技法知识库 + 工程脚本”的工程化仓库。

当前主战题材：

- 历史权谋 / 边境战争
- 末世囤货
- 仙侠苟道
- 都市系统流
- 种田文

这套仓库现在回到一个更清晰的结构：

- `SKILL.md` 只保留核心工作流、读取策略、门禁与资源导航
- `references/` 存放长规则、诊断说明、固定输出契约
- `templates/` 提供项目记忆模板、章卡示例、题材写法资产
- `technique-kb/` 提供脚本和人工共用的结构化技法知识
- `hooks/` 只保留可执行的自动自检 hook，供 Claude 本地安装态接入
- `scripts/` 负责 chapter gate、language audit、自检和记忆回填
- `bin/` 提供 `chase` / `chase-novel-skill` CLI 入口

高阶模板已经单独收束到导航：

- `references/advanced-template-map.md`
  用来定位卷纲、反派、长期转场、感情线、结局等进阶模板
- `references/opening-sample-library.md`
  用来对照高质量作品的第一章路线，学习开篇抓人、信息顺序与卖点建立
- `references/opening-sample-specialties.md`
  用来对照偏好题材的开篇路线专题，优先覆盖历史权谋、末世囤货、仙侠苟道
- `references/local-corpus-learning.md`
  用来沉淀本地下载小说语料的结构化学习结果，重点提炼历史权谋/边境战争、末世囤货、仙侠苟道三类高频路线，并为都市系统流、种田文扩展提供对照底稿
- `references/local-corpus-priority-map.md`
  用来先判断本地下载目录里哪本更值得先读、分别适合提炼什么结构，避免盲目整本平推
- 题材专项资产统一按同一套结构组织：
  - `*-volume-route-library.md`：整卷路线
  - `*-character-learning.md`：人物与关系
  - `*-chapter-card-library.md`：章节卡实战骨架
  - `*-negative-patterns.md`：高频反套路与负面清单
  - 当前已覆盖 `historical`、`moshi`、`goudao`、`dushi`、`zhongtian`
- `references/historical-midgame-learning.md`
  用来专门补强历史权谋 / 边境战争在 10 章以后如何持续推进、换挡与提压
- `references/historical-command-and-aftermath-library.md`
  用来专门补强将领关系、军令分配、违令有功、分功定责、封赏清算与战后后账
- `references/historical-relationship-card-deck.md`
  用来速查皇帝、监军、宿将、先锋、粮官、地方官、台谏、盟友、亲兵等高频关系的变质路线
- `references/historical-military-political-chapter-card-library.md`
  用来直接套用监军夺令、粮官卡脖、地方官逼军、战后分功、封赏藏刀、抚恤闹营等军政冲突章卡
- `references/hook-result-learning.md`
  用来专门补强末世囤货 / 仙侠苟道的章节结果换挡与章尾钩子设计
- `references/moshi-bastion-and-order-library.md`
  用来专门补强末世囤货中后期的据点升级、规则建立、势力治理与秩序重建
- `references/moshi-bastion-governance-chapter-cards.md`
  用来直接套用新人准入、资源分配、规则处罚、对外交易、外点扩张、闹营治理等据点治理章卡
- `templates/opening-route-cheatsheet.md`
  用来在 `/一键开书` 前快速选择第一章路线，而不是直接闷头写
- `templates/golden-three-route-cheatsheet.md`
  用来把开篇主路线扩成黄金三章功能链，避免只会抓第一章，不会接第二第三章
- `templates/hook-route-cheatsheet.md`
  用来在 `/写` 前快速选择章尾钩子路线，避免连续几章用同一种断尾
- `templates/result-route-cheatsheet.md`
  用来在 `/写` 前快速给本章换结果类型，避免连续几章都是同一种反馈
- `templates/midgame-fatigue-cheatsheet.md`
  用来在卷中段快速诊断疲劳，决定该换结果、换冲突还是换人物组合

当前 `/一键开书` 固定产物已经要求显式输出：

- 开篇主路线
- 第一章最先立住什么
- 第一章绝不能先写什么
- 黄金三章草案
- 黄金三章自动推荐依据
- 第三章长期承诺
- 第三章章尾钩子类型

当前 `/写` 章卡也应显式输出：

- 章尾钩子类型
- 章尾钩子自动推荐依据
- 为什么这一钩子适合本章
- 本章章尾钩子

## 核心能力

- 开书：题材定位、卖点、主线目标、黄金三章
- 续写：基于 `plan.md`、`state.md` 等记忆文件恢复状态并推进章节
- 修章：处理太水、重复、人设失真、钩子弱、节奏拖沓
- 门禁：对单章或批量章节做 continuity、重复度、语言质量检查
- 长线维护：伏笔、承诺、角色弧、时间线、卷节奏
- 题材补强：当前重点深挖 5 条常用主线，分别是历史权谋 / 边境战争、末世囤货、仙侠苟道、都市系统流、种田文；其余模板按需调用

当前工程脚本已同步支持：

- 黄金三章递进检查：第 1 章抓入场、第 2 章推行动、第 3 章挂长期承诺
- 章尾钩子七型识别：结果未揭晓 / 危机压顶 / 选择逼近 / 信息反转 / 关系突变 / 资源争夺 / 欲望升级
- 开篇期轻量预警：`chapter_gate.py` 会对第 1-3 章给出抓手、推进、承诺类 warning

学习原则：

- 从本地下载小说中学习结构，不直接搬运原文入库
- 仓库只沉淀可复用的路线、章卡、关系、反套路与门禁规则
- 先按 `genre-asset-index.md` 选入口，再按题材下钻，不做整包加载

## 推荐使用顺序

1. 先看 `SKILL.md`
2. 需要长规则时再读 `references/`
3. 需要模板时读 `templates/`
4. 需要自动化检查时运行 `scripts/`

## 常用命令

```bash
python scripts/project_bootstrap.py --project "novel_书名"
python scripts/project_doctor.py --project "novel_书名"
python scripts/context_compiler.py --project "novel_书名" --chapter 12
python scripts/workflow_runner.py --project "novel_书名" --chapter 12
python scripts/toolchain_smoke.py
npm run verify:toolchain
python scripts/chapter_gate.py --project "novel_书名" --chapter-no 12
python scripts/language_audit.py --project "novel_书名" --chapter-no 12 --mode suggest
python scripts/batch_gate.py --project "novel_书名" --from 1 --to 30 --json
python scripts/chapter_self_check.py --project "novel_书名" --chapter-no 10
```

其中：

- `project_doctor.py` 用于检查单个小说项目目录是否完整、状态是否异常
- `workflow_runner.py` 用于按默认顺序串起 `doctor -> context -> memory -> foreshadow -> arc -> timeline -> repeat -> dashboard`，并生成 `05_reports/pipeline_report.{md,json}`
- `chapter_gate.py` 除常规 continuity gate 外，也会对第 1-3 章做黄金三章轻量校验
- `anti_repeat_scan.py` 会扫描近章钩子分布，并额外输出 `golden_three` 开篇三章递进快照
- `toolchain_smoke.py` 用于验证当前技能仓库的工程链路是否可用；脚本会创建临时项目并在退出时自动清理，不保留测试内容
- `npm run verify:toolchain` 是 `toolchain_smoke.py` 的 npm 包装入口

## 仓库结构

```text
repo/
├─ SKILL.md
├─ references/
├─ templates/
│  ├─ genres/        # 5 条常用主战题材模板
│  └─ substyles/     # 3 类子风格模板
├─ technique-kb/
├─ hooks/
├─ scripts/
├─ schemas/
└─ bin/
```

这不是“把所有规则堆进一个超长 prompt”的仓库，而是把入口、规则、模板、知识库和脚本拆开，让技能本体保持清晰，长期连载能力留给文件与脚本承接。
