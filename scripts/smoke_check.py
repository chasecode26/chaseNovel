#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.contracts import EvaluatorVerdict
from runtime.decision_engine import DecisionEngine
from runtime.runtime_orchestrator import LeadWriterRuntime
from scripts.quality_gate import analyze_information_shift, analyze_promise_layers, analyze_relationship_shift


def run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    completed = subprocess.run(command, cwd=cwd, env=env)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def run_capture_json(command: list[str], cwd: Path) -> dict[str, object]:
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if completed.returncode != 0 and not completed.stdout.strip():
        raise SystemExit(completed.returncode)
    return json.loads(completed.stdout)


def read_json_file(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_file(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def find_verdict(payload: dict[str, object], dimension: str) -> dict[str, object] | None:
    for item in payload.get("verdicts", []):
        if str(item.get("dimension", "")).strip() == dimension:
            return item
    return None


def require_targets(actual: list[str], expected: set[str], message: str) -> None:
    actual_set = {str(item) for item in actual}
    if not expected.issubset(actual_set):
        missing = ", ".join(sorted(expected - actual_set))
        raise SystemExit(f"{message}: missing {missing}")


def compile_python_scripts(repo_root: Path) -> None:
    for directory in ("scripts", "runtime", "evaluators"):
        for path in (repo_root / directory).glob("*.py"):
            py_compile.compile(str(path), doraise=True)


def run_runtime_policy_checks() -> None:
    runtime = LeadWriterRuntime()
    promoted = runtime._apply_decision_policy(
        [
            EvaluatorVerdict(
                dimension="character",
                status="warn",
                blocking=False,
                evidence=[
                    "主角禁忌已经越界。",
                    "正文行为与谨慎设定冲突。",
                ],
                why_it_breaks="test",
                minimal_fix="test",
                rewrite_scope="scene_beats",
            ),
            EvaluatorVerdict(
                dimension="arc",
                status="warn",
                blocking=False,
                evidence=["character arc schema/报告仍为空。"],
                why_it_breaks="test",
                minimal_fix="test",
                rewrite_scope="chapter_result",
            ),
        ]
    )
    promoted_by_dimension = {item.dimension: item for item in promoted}
    if not promoted_by_dimension["character"].blocking or promoted_by_dimension["character"].status != "fail":
        raise SystemExit("runtime policy did not promote severe character drift into blocking")
    if not promoted_by_dimension["arc"].blocking or promoted_by_dimension["arc"].status != "fail":
        raise SystemExit("runtime policy did not promote arc drift when character drift is also present")

    decision = DecisionEngine().decide(
        [
            EvaluatorVerdict(
                dimension="character",
                status="fail",
                blocking=True,
                evidence=["test"],
                why_it_breaks="test",
                minimal_fix="test",
                rewrite_scope="scene_beats",
            ),
            EvaluatorVerdict(
                dimension="causality",
                status="fail",
                blocking=True,
                evidence=["test"],
                why_it_breaks="test",
                minimal_fix="test",
                rewrite_scope="chapter_result",
            ),
            EvaluatorVerdict(
                dimension="pacing",
                status="fail",
                blocking=True,
                evidence=["test"],
                why_it_breaks="test",
                minimal_fix="test",
                rewrite_scope="full_chapter",
            ),
        ]
    )
    if decision.rewrite_brief is None or decision.rewrite_brief.first_fix_priority != "causality":
        raise SystemExit("runtime decision engine did not honor design priority over extended blocking dimensions")
    if decision.blocking_dimensions[:3] != ["causality", "pacing", "character"]:
        raise SystemExit("runtime decision engine did not sort blocking dimensions by design priority")


def run_change_analyzer_checks(repo_root: Path) -> None:
    working_payload = run_capture_json(["node", "./scripts/change_analyzer.js", "--json"], cwd=repo_root)
    if working_payload.get("mode") != "working":
        raise SystemExit("change analyzer did not default to working mode")
    if "summary" not in working_payload or "files" not in working_payload:
        raise SystemExit("change analyzer did not expose summary/files payload")
    summary = working_payload.get("summary", {})
    if "category_counts" not in summary or "code_change_lines" not in summary:
        raise SystemExit("change analyzer summary did not expose category/code stats")

    committed_payload = run_capture_json(
        ["node", "./scripts/change_analyzer.js", "--mode", "committed", "--json"],
        cwd=repo_root,
    )
    if committed_payload.get("mode") != "committed":
        raise SystemExit("change analyzer committed mode did not echo requested mode")

    tmp_root = repo_root / ".tmp-smoke"
    project_dir = tmp_root / "fixture-change-analyzer"
    if project_dir.exists():
        shutil.rmtree(project_dir, ignore_errors=True)
    project_dir.mkdir(parents=True, exist_ok=True)

    for relative_dir in (
        "references",
        "docs/core",
        "scripts",
        "templates/launch",
        ".tmp-noise",
        "05_reports",
        "00_memory/retrieval",
    ):
        (project_dir / relative_dir).mkdir(parents=True, exist_ok=True)

    (project_dir / "README.md").write_text("# fixture\n", encoding="utf-8")
    (project_dir / "commit_message.txt").write_text("temp\n", encoding="utf-8")
    (project_dir / "references" / "alpha.md").write_text("alpha v1\n", encoding="utf-8")
    (project_dir / "references" / "beta.md").write_text("beta v1\n", encoding="utf-8")
    (project_dir / "docs" / "core" / "guide.md").write_text("guide v1\n", encoding="utf-8")
    (project_dir / "scripts" / "tool.py").write_text("print('v1')\n", encoding="utf-8")
    (project_dir / "templates" / "launch" / "sample.md").write_text("sample v1\n", encoding="utf-8")

    run(["git", "init"], cwd=project_dir)
    run(["git", "config", "user.name", "Smoke Fixture"], cwd=project_dir)
    run(["git", "config", "user.email", "smoke@example.com"], cwd=project_dir)
    run(["git", "add", "."], cwd=project_dir)
    run(["git", "commit", "-m", "init"], cwd=project_dir)

    (project_dir / "references" / "alpha.md").write_text("alpha v2\n", encoding="utf-8")
    (project_dir / "references" / "beta.md").write_text("beta v2\n", encoding="utf-8")
    (project_dir / "references" / "new-note.md").write_text("new note\n", encoding="utf-8")
    (project_dir / "docs" / "core" / "guide.md").write_text("guide v2\n", encoding="utf-8")
    (project_dir / "docs" / "core" / "cleanup.md").write_text("still points to templates/launch/sample.md\n", encoding="utf-8")
    (project_dir / "scripts" / "tool.py").write_text("print('v2')\n", encoding="utf-8")
    (project_dir / ".tmp-noise" / "ignored.md").write_text("ignore me\n", encoding="utf-8")
    (project_dir / "05_reports" / "ignored.md").write_text("ignore me\n", encoding="utf-8")
    (project_dir / "00_memory" / "retrieval" / "ignored.md").write_text("ignore me\n", encoding="utf-8")
    (project_dir / "commit_message.txt").unlink()
    (project_dir / "templates" / "launch" / "sample.md").unlink()

    fixture_payload = run_capture_json(
        ["node", str((repo_root / "scripts" / "change_analyzer.js").resolve()), "--json"],
        cwd=project_dir,
    )
    fixture_modules = {str(item.get("name", "")): item for item in fixture_payload.get("modules", [])}
    if "references" not in fixture_modules:
        raise SystemExit("change analyzer fixture did not collapse flat references files into references module")
    if fixture_modules["references"].get("file_count") != 3:
        raise SystemExit("change analyzer fixture did not count flat references changes under one module")
    if "docs/core" not in fixture_modules:
        raise SystemExit("change analyzer fixture did not preserve nested docs/core module grouping")
    if "templates/launch" not in fixture_modules:
        raise SystemExit("change analyzer fixture did not preserve nested templates/launch grouping")

    fixture_paths = {str(item.get("path", "")) for item in fixture_payload.get("files", [])}
    if any(path.startswith(".tmp-noise/") for path in fixture_paths):
        raise SystemExit("change analyzer fixture did not ignore .tmp-* generated noise")
    if any(path.startswith("05_reports/") for path in fixture_paths):
        raise SystemExit("change analyzer fixture did not ignore report artifacts")
    if any(path.startswith("00_memory/retrieval/") for path in fixture_paths):
        raise SystemExit("change analyzer fixture did not ignore retrieval artifacts")
    if any(path == "commit_message.txt" for path in fixture_paths):
        raise SystemExit("change analyzer fixture did not ignore transient commit_message artifact")

    summary_only_payload = run_capture_json(
        ["node", str((repo_root / "scripts" / "change_analyzer.js").resolve()), "--json", "--summary-only"],
        cwd=project_dir,
    )
    if summary_only_payload.get("files") != []:
        raise SystemExit("change analyzer summary-only mode did not suppress file list")
    if not summary_only_payload.get("file_list_truncated"):
        raise SystemExit("change analyzer summary-only mode did not mark truncated file list")
    if summary_only_payload.get("omitted_file_count", 0) <= 0:
        raise SystemExit("change analyzer summary-only mode did not report omitted files")

    max_files_payload = run_capture_json(
        ["node", str((repo_root / "scripts" / "change_analyzer.js").resolve()), "--json", "--max-files", "2"],
        cwd=project_dir,
    )
    if len(max_files_payload.get("files", [])) != 2:
        raise SystemExit("change analyzer max-files mode did not limit visible file count")
    if not max_files_payload.get("file_list_truncated"):
        raise SystemExit("change analyzer max-files mode did not mark truncated file list")
    if max_files_payload.get("omitted_file_count", 0) <= 0:
        raise SystemExit("change analyzer max-files mode did not report omitted files")

    docs_only_payload = run_capture_json(
        ["node", str((repo_root / "scripts" / "change_analyzer.js").resolve()), "--json", "--category", "docs"],
        cwd=project_dir,
    )
    if docs_only_payload.get("selected_category") != "docs":
        raise SystemExit("change analyzer docs category mode did not echo selected category")
    docs_summary = docs_only_payload.get("summary", {})
    if docs_summary.get("changed_files") != 6:
        raise SystemExit("change analyzer docs category mode did not keep expected docs change count")
    docs_counts = docs_summary.get("category_counts", {})
    if docs_counts.get("docs") != 6 or any(
        docs_counts.get(name, 0) != 0 for name in ("code", "tests", "config", "other")
    ):
        raise SystemExit("change analyzer docs category mode did not isolate docs category counts")
    if any(str(item.get("category")) != "docs" for item in docs_only_payload.get("files", [])):
        raise SystemExit("change analyzer docs category mode leaked non-doc files")

    code_only_payload = run_capture_json(
        ["node", str((repo_root / "scripts" / "change_analyzer.js").resolve()), "--json", "--category", "code"],
        cwd=project_dir,
    )
    if code_only_payload.get("selected_category") != "code":
        raise SystemExit("change analyzer code category mode did not echo selected category")
    code_summary = code_only_payload.get("summary", {})
    if code_summary.get("changed_files") != 1:
        raise SystemExit("change analyzer code category mode did not keep expected code change count")
    code_counts = code_summary.get("category_counts", {})
    if code_counts.get("code") != 1 or any(
        code_counts.get(name, 0) != 0 for name in ("docs", "tests", "config", "other")
    ):
        raise SystemExit("change analyzer code category mode did not isolate code category counts")
    if len(code_only_payload.get("modules", [])) != 1 or str(code_only_payload["modules"][0].get("name")) != "scripts":
        raise SystemExit("change analyzer code category mode did not preserve scripts module view")

    references_module_payload = run_capture_json(
        ["node", str((repo_root / "scripts" / "change_analyzer.js").resolve()), "--json", "--module", "references"],
        cwd=project_dir,
    )
    if references_module_payload.get("selected_module") != "references":
        raise SystemExit("change analyzer module mode did not echo selected module")
    references_summary = references_module_payload.get("summary", {})
    if references_summary.get("changed_files") != 3:
        raise SystemExit("change analyzer module mode did not keep expected references change count")
    if any(str(item.get("module")) != "references" for item in references_module_payload.get("files", [])):
        raise SystemExit("change analyzer module mode leaked files from other modules")
    if len(references_module_payload.get("modules", [])) != 1:
        raise SystemExit("change analyzer module mode did not keep a single-module summary")

    docs_core_payload = run_capture_json(
        [
            "node",
            str((repo_root / "scripts" / "change_analyzer.js").resolve()),
            "--json",
            "--category",
            "docs",
            "--module",
            "docs/core",
        ],
        cwd=project_dir,
    )
    if docs_core_payload.get("selected_category") != "docs" or docs_core_payload.get("selected_module") != "docs/core":
        raise SystemExit("change analyzer combined category+module mode did not echo selected filters")
    docs_core_summary = docs_core_payload.get("summary", {})
    if docs_core_summary.get("changed_files") != 2:
        raise SystemExit("change analyzer combined category+module mode did not keep expected docs/core change count")
    if any(str(item.get("module")) != "docs/core" for item in docs_core_payload.get("files", [])):
        raise SystemExit("change analyzer combined category+module mode leaked other modules")
    if not docs_core_payload.get("global_warnings"):
        raise SystemExit("change analyzer filtered payload did not preserve global warnings")
    if not docs_core_payload.get("global_recommendations"):
        raise SystemExit("change analyzer filtered payload did not preserve global recommendations")
    if not docs_core_payload.get("global_deleted_reference_hits"):
        raise SystemExit("change analyzer filtered payload did not preserve global deleted reference hits")

    docs_prefix_payload = run_capture_json(
        ["node", str((repo_root / "scripts" / "change_analyzer.js").resolve()), "--json", "--module-prefix", "docs"],
        cwd=project_dir,
    )
    if docs_prefix_payload.get("selected_module_prefix") != "docs":
        raise SystemExit("change analyzer module-prefix mode did not echo selected prefix")
    docs_prefix_summary = docs_prefix_payload.get("summary", {})
    if docs_prefix_summary.get("changed_files") != 2:
        raise SystemExit("change analyzer module-prefix mode did not keep expected docs family change count")
    if any(not str(item.get("module", "")).startswith("docs/") for item in docs_prefix_payload.get("files", [])):
        raise SystemExit("change analyzer module-prefix mode leaked non-doc module files")
    if docs_prefix_payload.get("deleted_reference_hits"):
        raise SystemExit("change analyzer module-prefix mode should not attach deleted hits to unrelated filtered deletions")

    references_prefix_payload = run_capture_json(
        ["node", str((repo_root / "scripts" / "change_analyzer.js").resolve()), "--json", "--module-prefix", "references"],
        cwd=project_dir,
    )
    if references_prefix_payload.get("summary", {}).get("changed_files") != 3:
        raise SystemExit("change analyzer module-prefix mode did not keep expected references family change count")
    if len(references_prefix_payload.get("modules", [])) != 1:
        raise SystemExit("change analyzer module-prefix mode did not keep expected references module summary")

    deleted_only_payload = run_capture_json(
        ["node", str((repo_root / "scripts" / "change_analyzer.js").resolve()), "--json", "--module", "templates/launch"],
        cwd=project_dir,
    )
    deleted_hits = deleted_only_payload.get("deleted_reference_hits", [])
    if len(deleted_hits) != 1:
        raise SystemExit("change analyzer deleted file slice did not report expected residual reference hit")
    if str(deleted_hits[0].get("deleted_path")) != "templates/launch/sample.md":
        raise SystemExit("change analyzer deleted file slice reported unexpected deleted path")
    references = deleted_hits[0].get("references", [])
    if len(references) != 1 or str(references[0].get("path")) != "docs/core/cleanup.md":
        raise SystemExit("change analyzer deleted file slice did not capture exact residual reference location")

    top_modules_payload = run_capture_json(
        ["node", str((repo_root / "scripts" / "change_analyzer.js").resolve()), "--json", "--top-modules", "2"],
        cwd=project_dir,
    )
    if len(top_modules_payload.get("modules", [])) != 2:
        raise SystemExit("change analyzer top-modules mode did not limit module list")
    if not top_modules_payload.get("module_list_truncated"):
        raise SystemExit("change analyzer top-modules mode did not mark truncated module list")
    if top_modules_payload.get("omitted_module_count", 0) <= 0:
        raise SystemExit("change analyzer top-modules mode did not report omitted modules")
    if top_modules_payload.get("summary", {}).get("module_count") != 4:
        raise SystemExit("change analyzer top-modules mode did not preserve total module count in summary")


def prepare_fixture(project_dir: Path) -> None:
    memory_dir = project_dir / "00_memory"
    (memory_dir / "plan.md").write_text(
        "# 主线计划\n\n"
        "- 书名：测试书\n"
        "- 题材：都市系统\n"
        "- 核心卖点：普通人靠系统翻身\n"
        "- 章节字数约束：2500~3500字/章\n\n"
        "## 主线大纲\n"
        "- [ ] 第一卷：起盘（第1~120章）\n"
        "- [ ] 第二卷：升压（第121~240章）\n",
        encoding="utf-8",
    )
    (memory_dir / "state.md").write_text(
        "# 当前状态\n\n"
        "## 进度\n"
        "- 当前章节：1\n"
        "- 当前卷：第一卷\n"
        "- 总字数：2800\n\n"
        "## 当前阶段\n"
        "- 当前弧：起盘\n"
        "- 当前地点：旧楼走廊\n\n"
        "## 下章预告\n"
        "- 章节号：2\n"
        "- 计划内容：主角拿到系统后的第一次反击\n",
        encoding="utf-8",
    )
    (memory_dir / "style.md").write_text(
        "# 风格锚点\n\n"
        "- 题材：都市系统\n"
        "- 主风格标签：快反爽\n"
        "- 语言风格：现代通俗大白话\n"
        "- 必须保住的声音：利落、直接、有结果感\n",
        encoding="utf-8",
    )
    (memory_dir / "voice.md").write_text(
        "# 书级 Voice DNA\n\n"
        "角色说话差分总则：身份不同、性格不同、压力不同，说法就必须不同。\n",
        encoding="utf-8",
    )
    (memory_dir / "characters.md").write_text(
        "# 角色档案\n\n"
        "## 主角\n- 姓名：林砚\n\n"
        "## 核心配角\n- 苏晚：盟友\n",
        encoding="utf-8",
    )
    (memory_dir / "timeline.md").write_text(
        "# 时间线\n\n"
        "## 主线时间线\n"
        "| 时间 | 事件 | 结果 |\n"
        "| --- | --- | --- |\n"
        "| 今晚 | 林砚被催债 | 系统激活 |\n",
        encoding="utf-8",
    )
    (memory_dir / "foreshadowing.md").write_text(
        "# 伏笔\n\n"
        "## 活跃伏笔\n"
        "| 伏笔 | 触发条件 | 失效条件 |\n"
        "| --- | --- | --- |\n"
        "| 系统来源 | 林砚进一步使用系统 | 真相提前揭示 |\n",
        encoding="utf-8",
    )
    (memory_dir / "summaries" / "recent.md").write_text(
        "## 第1章：系统第一次响起\n"
        "- 核心事件：主角在催债压力下听到系统绑定提示。\n"
        "- 人物变化：林砚从被动躲避转向准备反击。\n"
        "- 启下：他决定利用系统把主动权拿回来。\n",
        encoding="utf-8",
    )
    (project_dir / "03_chapters" / "ch001.md").write_text(
        "# 第001章 系统第一次响起\n\n"
        "林砚刚把门推开，耳边就炸开一声机械提示。\n\n"
        "“检测到宿主处于高压生存环境，系统绑定开始。”\n\n"
        "他没有立刻回答，只先看向楼道尽头。刚才那个来催债的人还没走远。\n\n"
        "如果系统是真的，他今晚就不只是躲过去，而是要把主动权拿回来。\n",
        encoding="utf-8",
    )
    (project_dir / "01_outline" / "chapter_cards").mkdir(parents=True, exist_ok=True)
    (project_dir / "01_outline" / "chapter_cards" / "ch002.md").write_text(
        "# 第002章 章卡\n\n"
        "- chapter_function：主角第一次用系统反击\n"
        "- result_change：主角不再只是挨打，开始拿回主动权\n"
        "- hook_type：结果未揭晓型\n"
        "- hook_text：系统给出下一步更高代价的任务\n"
        "- chapter_tier：normal\n"
        "- target_word_count：2600\n",
        encoding="utf-8",
    )


def prepare_pass_fixture(project_dir: Path) -> None:
    memory_dir = project_dir / "00_memory"
    pass_plan_text = (
        "# 主线计划\n\n"
        "- 书名：测试书\n"
        "- 题材：都市系统\n"
        "- 核心卖点：普通人靠系统翻身\n"
        "- 章节字数约束：2500~3500字/章\n\n"
        "## 主线大纲\n"
        "- [ ] 第一卷：起盘（第1~120章）\n"
        "- [ ] 第二卷：升压（第121~240章）\n"
    )
    chapter_body = "主角稳住呼吸，盯着走廊尽头的脚步声，确认自己终于拿回了一点主动。\n" * 88
    (memory_dir / "plan.md").write_text(pass_plan_text, encoding="utf-8")
    (memory_dir / "state.md").write_text(
        "# 当前状态\n\n"
        "- 当前章节：1\n"
        "- 当前卷：第一卷\n"
        "- 当前弧：起盘\n"
        "- 当前地点：旧楼走廊\n"
        "- 当前绝对时间：2026年4月的雨夜\n"
        "- 距上章过去：10分钟\n"
        "- 章节号：2\n"
        "- 计划内容：主角完成第一次有效反击并确认系统代价\n",
        encoding="utf-8",
    )
    (memory_dir / "style.md").write_text(
        "# 风格锚点\n\n"
        "- 题材：都市系统\n"
        "- 语言风格：现代、直接、结果导向\n"
        "- 必须保住的声音：利落、压迫感、行动反馈\n",
        encoding="utf-8",
    )
    (memory_dir / "voice.md").write_text("# Voice\n\n角色说话要有身份差异和压力差异。\n", encoding="utf-8")
    (memory_dir / "characters.md").write_text(
        "# 角色档案\n\n"
        "## 主角\n"
        "### 林砚\n"
        "- 姓名：林砚\n"
        "- 核心性格：冷、硬、克制\n"
        "- 决策风格：谨慎\n"
        "- 底线/禁忌：不把命交给运气\n"
        "- 当前诉求：拿回主动权\n\n"
        "## 核心配角\n"
        "### 苏晚\n"
        "- 姓名：苏晚\n"
        "- 定位：盟友\n"
        "- 性格：利、快、嘴硬\n"
        "- 当前诉求：确认林砚有没有真底牌\n"
        "- 当前恐惧：局面彻底失控\n"
        "- 与主角关系：盟友\n",
        encoding="utf-8",
    )
    (memory_dir / "timeline.md").write_text(
        "# 时间线\n\n"
        "## 主线时间线\n"
        "| 时间 | 事件 | 结果 |\n"
        "| --- | --- | --- |\n"
        "| 2026年4月的雨夜 | 林砚被催债逼到旧楼走廊 | 系统第一次介入 |\n"
        "| 十分钟后 | 林砚确认反击方案 | 系统抛出更高代价的下一步任务 |\n",
        encoding="utf-8",
    )
    (memory_dir / "foreshadowing.md").write_text(
        "# 伏笔\n\n"
        "## 活跃伏笔\n"
        "| 伏笔 | 说明 | 当前状态 | 回收目标 | 触发条件 | 失效条件 |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| 系统来源 | 系统为什么选中林砚 | active | 第一卷中段 | 林砚连续完成任务 | 真相提前曝光 |\n",
        encoding="utf-8",
    )
    (memory_dir / "summaries" / "recent.md").write_text(
        "## 第001章：系统第一次响起\n"
        "- 核心事件：主角在催债压力下听到系统绑定提示。\n"
        "- 人物变化：林砚从被动躲避转向准备反击。\n"
        "- 启下：他决定利用系统把主动权拿回来。\n",
        encoding="utf-8",
    )
    (project_dir / "03_chapters" / "ch001.md").write_text(
        "# 第001章 系统第一次响起\n\n"
        + chapter_body
        + "\n系统面板在他眼前一闪而过，新的任务代价清清楚楚地压在心口。\n",
        encoding="utf-8",
    )
    (project_dir / "01_outline" / "chapter_cards").mkdir(parents=True, exist_ok=True)
    (project_dir / "01_outline" / "chapter_cards" / "ch001.md").write_text(
        "# 第001章 章卡\n\n"
        "- chapter_function：主角完成第一次有效反击\n"
        "- result_change：主角开始掌握主动，不再只是被动挨打\n"
        "- hook_type：代价升级型\n"
        "- hook_text：系统给出更高代价的下一步任务\n"
        "- chapter_tier：normal\n"
        "- target_word_count：2600\n",
        encoding="utf-8",
    )


def prepare_promise_layer_fixture(project_dir: Path) -> None:
    prepare_pass_fixture(project_dir)
    layer_body = (
        "林砚没有急着把话说满，只先盯住走廊尽头那道门，确认催债的人确实被他逼退了半步。那一步不大，却足够让局面第一次从单纯挨打，变成他可以自己挑位置、挑时机。苏晚站在侧面看着，没有替他说话，只等他自己把这一局认清。\n\n"
        "“你刚才不是没退，是故意把人往窄处逼。”苏晚把判断压得很低，“你终于开始拿回主动权了。”林砚抬眼看她，没有回避这句结论，只把气息压稳：“我只认这一点，先把主动权拿回来，别的账后面再算。”这句话落下去，等于把本章结果钉死，他不再只是被动挨打。\n\n"
        "苏晚没有顺着夸他，反而继续追问：“你拿回这一截之后，敢不敢认后面的麻烦？”林砚没有把自己说成稳赢，只把站位重新卡住，让门口那人不敢再往前一步。场面没有彻底翻盘，但主动的一侧已经换了人，这就是他今晚真正拿到的结果。\n\n"
        "走廊里的压迫感没有散，可它不再只是朝着林砚一个人落下。苏晚看着他的动作，第一次把戒备收了一寸，也第一次肯承认他不是只会躲的人。关系没有一下子翻面，却已经出现了能被看见的偏移。\n\n"
        "林砚知道这还不算赢，所以他没有趁着对方后退就追出去，只把呼吸压平，把门口、退路和苏晚站的位置重新记了一遍。局面被他收回来的，不只是面子，而是接下来谁先开口、谁先失手的顺序。这样的收束让本章结果更清楚，也让苏晚能继续盯着他的下一步。\n\n"
        "“你现在是拿回来了一截，可别转头又自己松手。”苏晚盯着他，语气没有缓下来。林砚点了一下头：“我知道，我不会把刚拿回来的主动权再送出去。”这不是新的任务提示，而是对刚刚结果的再确认，让主角真正站稳了本章的短兑现。\n\n"
        "门外那点脚步声彻底散开后，走廊反而显得更空。林砚没有借机夸口，只把刚才那一步步复盘给自己听：先稳住，再逼退，再把主动权抓回手里。苏晚也没有替他下定义，只记住他有没有把这套选择继续执行下去。\n\n"
        "这场对峙留下的最明显变化，不是敌人彻底消失，而是林砚终于不再只会等别人把牌打到脸上。他开始自己定节奏，自己压位置，自己决定什么时候开口。这种变化已经足够撑起本章结果，却还没有变成新的升级指令或更高价码。\n\n"
        "苏晚站在一旁，看见的也不是一场圆满翻盘，而是一种更值得观察的站位变化。她确认林砚不是空喊口号的人，也确认他会不会把这句表态一直守住。她把这层判断压在心里，没有再往外多说一句。\n\n"
        "林砚把衣袖往下扯了扯，像是把整场对峙最后一点余震也按住。他知道自己今晚只是先把主动权拿回来，没有把所有后账一并算清。可这一截主动，已经足够让他和苏晚都重新估价眼前这盘局。\n\n"
        "“你既然认了这一步，就别在下一次临门时退回去。”苏晚最后只留下这一句。林砚看着她，答得很稳：“我既然说了，就会照着做。”对白停在这里，仍然围着结果后的表态打转，没有把局面抬成新的倒计时，也没有抛出更狠的代价说明。\n\n"
        "两人都没有再往前走，走廊里只剩下刚刚那场变化带来的余压。林砚把这份余压当成提醒，而不是又压下来的一张新账单。苏晚也只是记住了他的选择，等着看他以后是否照做，而不是在本章尾声另起一轮新压迫。\n\n"
        "等人声彻底远下去，林砚才低声说：“这只是先站稳，后面怎么走，我会自己接。”苏晚没再逼他，只盯着他看了两秒：“好，我记住你这句。”这不是新的催促，也不是另一层压力，只是把视线钉在他已经说出口的那次表态上。\n\n"
        "章尾没有把账单再抬高，只留下一个更紧的注视：苏晚已经听见了他的表态，也会盯着他以后是不是还敢这么选。林砚把这道目光收进心里，知道自己不能拆自己的台。\n\n"
    )
    (project_dir / "03_chapters" / "ch001.md").write_text("# 第001章 主角先拿回一截主动权\n\n" + layer_body * 2, encoding="utf-8")
    (project_dir / "01_outline" / "chapter_cards" / "ch001.md").write_text(
        "# 第001章 章卡\n\n"
        "- chapter_function：主角完成第一次有效反击\n"
        "- result_change：主角开始掌握主动权，不再只是被动挨打\n"
        "- hook_type：relationship_pressure\n"
        "- hook_text：苏晚记住了他的表态，盯他以后是不是照做\n"
        "- chapter_tier：normal\n"
        "- target_word_count：1200\n",
        encoding="utf-8",
    )


def prepare_information_shift_fixture(project_dir: Path) -> None:
    prepare_pass_fixture(project_dir)
    info_body = (
        "林砚把门半掩着，没有急着往前，只是盯住走廊尽头那道影子，等对方先露出下一步。苏晚站在侧后方，没有替他说话，只把呼吸压低，像是在等他自己把话挑明。\n\n"
        "“你刚才不是不敢开口，你是在算我会不会替你挡这一下。”苏晚先把话挑破，声音不高，却把试探压得很准。林砚看了她一眼，没有否认：“你听出来了，就该知道我没打算继续装下去。”\n\n"
        "苏晚没有接着让步，只是继续盯着他：“我知道你刚才那句硬撑是说给门外那人听的，不是说给我听的。”林砚把肩背抵住墙面，语气仍旧压着：“既然你已经看穿了，就别再拿这件事反复试我。”\n\n"
        "两人把话说到这里，走廊里的压迫感并没有散掉，但局面也没有继续移动。门外那人没有再逼近，林砚也没有改站位，只是把沉默重新按回原处，让刚被挑明的信息停在空气里。\n\n"
        "“那我就把你今天这句留在心里。”苏晚看着他，像是把某个判断压进心底。林砚只回了一句：“你既然听清了，那就这样。”他说完便没有继续往下展开，也没有顺着这层信息继续给出新的决定、交换或压制。\n\n"
        "随后两人都没有再往前走。苏晚知道他刚才是在借势，林砚也知道她已经听出那层表态，可正文只把这层看穿停在当下，没有让人物关系、站位或后续判断发生可见位移。\n\n"
        "门外脚步声断断续续地拖远，林砚仍旧站在原位，没有趁势追出去，也没有借这次暴露出来的信息改写眼前局面。苏晚同样没有逼近，没有收起戒备，也没有把双方关系重新定义，只是把这段对话悬在这里。\n\n"
        "“你既然都知道了，还问什么。”林砚最后一句压得很平。苏晚回得更平：“因为我想确认你是不是肯把真话说出来。”话到这里再一次停住，依旧只有识破与确认，没有新的站位变化，没有新的压制动作，也没有把信息差转成下一步结果。\n\n"
    )
    (project_dir / "03_chapters" / "ch001.md").write_text(
        "# 第01章 看穿之后没有转手\n\n" + info_body * 2,
        encoding="utf-8",
    )
    (project_dir / "01_outline" / "chapter_cards" / "ch001.md").write_text(
        "# 第01章 章卡\n\n"
        "- chapter_function：主角在对位试探里暴露真实表态\n"
        "- result_change：苏晚确认林砚刚才是在借势，不是真的退让\n"
        "- hook_type：relationship_pressure\n"
        "- hook_text：苏晚记住了他的真实表态，之后会继续盯着他是否说到做到\n"
        "- chapter_tier：normal\n"
        "- target_word_count：2200\n",
        encoding="utf-8",
    )


def run_fixture_flow(repo_root: Path) -> None:
    tmp_root = repo_root / ".tmp-smoke"
    project_dir = tmp_root / "fixture-book"
    if project_dir.exists():
        shutil.rmtree(project_dir, ignore_errors=True)
    tmp_root.mkdir(parents=True, exist_ok=True)

    run(["node", "./bin/chase.js", "bootstrap", "--project", str(project_dir)], cwd=repo_root)
    prepare_fixture(project_dir)

    doctor_payload = run_capture_json(
        ["python", "./scripts/project_doctor.py", "--project", str(project_dir), "--json"],
        cwd=repo_root,
    )
    if doctor_payload.get("status") == "fail":
        raise SystemExit("fixture doctor failed after bootstrap")

    open_payload = run_capture_json(
        ["python", "./scripts/open_book.py", "--project", str(project_dir), "--json"],
        cwd=repo_root,
    )
    if open_payload.get("status") == "fail":
        raise SystemExit("fixture open-book readiness failed after bootstrap")

    status_payload = run_capture_json(
        ["python", "./scripts/book_health.py", "--project", str(project_dir), "--json"],
        cwd=repo_root,
    )
    if status_payload.get("status") == "fail":
        raise SystemExit("fixture status health check failed after bootstrap")

    check_payload = run_capture_json(
        ["node", "./bin/chase.js", "check", "--project", str(project_dir), "--chapter", "1", "--json"],
        cwd=repo_root,
    )
    check_steps = [str(step.get("step", "")).strip() for step in check_payload.get("steps", [])]
    if "quality" not in check_steps:
        raise SystemExit("fixture check flow did not include quality step in default pipeline")
    if "runtime" in check_steps:
        raise SystemExit("fixture check flow should remain dry-run without runtime step")

    write_payload = run_capture_json(
        ["python", "./scripts/workflow_runner.py", "--project", str(project_dir), "--chapter", "1", "--json", "--dry-run"],
        cwd=repo_root,
    )
    if "pipeline_summary" not in write_payload:
        raise SystemExit("fixture write flow did not expose pipeline_summary")
    if write_payload.get("final_release") != "revise":
        raise SystemExit("fixture write flow did not expose revise final_release")
    if "quality_final_release" not in write_payload.get("pipeline_summary", {}):
        raise SystemExit("fixture write flow did not expose quality_final_release in pipeline_summary")
    if write_payload.get("pipeline_summary", {}).get("final_release") != "revise":
        raise SystemExit("fixture write flow did not expose revise pipeline final_release")
    quality_steps = [step for step in write_payload.get("steps", []) if step.get("step") == "quality"]
    if not quality_steps:
        raise SystemExit("fixture write flow did not include quality step in default pipeline")
    runtime_steps = [step for step in write_payload.get("steps", []) if step.get("step") == "runtime"]
    if not runtime_steps:
        raise SystemExit("fixture write flow did not include runtime step")
    runtime_summary = runtime_steps[0].get("summary", {})
    runtime_decision = runtime_summary.get("decision", {})
    if runtime_decision.get("decision") != "fail":
        raise SystemExit("fixture runtime dry-run did not escalate repeated blocking into fail")
    runtime_verdict_dimensions = {str(item.get("dimension", "")).strip() for item in runtime_summary.get("verdicts", [])}
    if not {"causality", "promise_payoff", "dialogue"}.issubset(runtime_verdict_dimensions):
        raise SystemExit("fixture runtime dry-run did not expose causality/promise_payoff/dialogue verdicts")
    cycles = runtime_summary.get("cycles", [])
    if len(cycles) < 2:
        raise SystemExit("fixture runtime dry-run did not emit rewrite cycles")
    first_cycle_decision = cycles[0].get("decision", {})
    if first_cycle_decision.get("decision") != "revise":
        raise SystemExit("fixture runtime dry-run did not emit revise on the first blocking cycle")
    runtime_draft = runtime_summary.get("draft", {})
    if runtime_draft.get("status") != "rewritten-runtime-output":
        raise SystemExit("fixture runtime dry-run did not emit rewritten runtime output status")
    if not runtime_draft.get("rewrite_handoff_path"):
        raise SystemExit("fixture runtime dry-run did not expose rewrite handoff path")

    quality_payload = run_capture_json(
        ["python", "./scripts/quality_gate.py", "--project", str(project_dir), "--chapter-no", "1", "--json", "--dry-run"],
        cwd=repo_root,
    )
    if "verdicts" not in quality_payload:
        raise SystemExit("fixture quality gate did not expose runtime verdicts")

    dashboard_dry_payload = run_capture_json(
        ["python", "./scripts/dashboard_snapshot.py", "--project", str(project_dir), "--json", "--dry-run"],
        cwd=repo_root,
    )
    dashboard_runtime = dashboard_dry_payload.get("runtime_signals", {})
    if dashboard_runtime.get("first_fix_priority") != "continuity":
        raise SystemExit("fixture dashboard did not expose runtime first_fix_priority")
    if dashboard_runtime.get("rewrite_scope") != "chapter_card + affected paragraphs":
        raise SystemExit("fixture dashboard did not expose runtime rewrite_scope")
    blocking_digest = dashboard_runtime.get("blocking_digest", [])
    if not isinstance(blocking_digest, list) or not any("continuity:" in str(item) for item in blocking_digest):
        raise SystemExit("fixture dashboard did not expose runtime blocking digest")
    require_targets(
        list(dashboard_runtime.get("ready_targets", [])),
        {"plan.json", "state.json", "timeline.json", "characters.json", "character_arcs.json", "foreshadowing.json"},
        "fixture dashboard did not expose expected ready runtime targets",
    )

    memory_apply_dry_payload = run_capture_json(
        ["python", "./scripts/memory_sync_apply.py", "--project", str(project_dir), "--json", "--dry-run"],
        cwd=repo_root,
    )
    ready_results = [item for item in memory_apply_dry_payload.get("results", []) if item.get("status") == "ready"]
    require_targets(
        [str(item.get("target", "")).strip() for item in ready_results],
        {"plan.json", "state.json", "timeline.json", "characters.json", "character_arcs.json", "foreshadowing.json"},
        "fixture memory_sync_apply dry-run did not expose expected ready targets",
    )

    state_schema_path = project_dir / "00_memory" / "schema" / "state.json"
    state_before_conflict = read_json_file(state_schema_path)
    state_conflict_payload = dict(state_before_conflict)
    state_conflict_payload["externalNote"] = "mutated-after-patch"
    write_json_file(state_schema_path, state_conflict_payload)
    conflict_payload = run_capture_json(
        [
            "python",
            "./scripts/memory_sync_apply.py",
            "--project",
            str(project_dir),
            "--targets",
            "state.json",
            "--json",
            "--dry-run",
        ],
        cwd=repo_root,
    )
    conflict_results = [item for item in conflict_payload.get("results", []) if item.get("status") == "conflict"]
    if len(conflict_results) != 1:
        raise SystemExit("fixture memory_sync_apply did not expose conflict when schema changed after patch generation")
    write_json_file(state_schema_path, state_before_conflict)

    runtime_apply_payload = run_capture_json(
        ["python", "./scripts/workflow_runner.py", "--project", str(project_dir), "--chapter", "1", "--steps", "runtime", "--json"],
        cwd=repo_root,
    )
    runtime_apply_steps = [step for step in runtime_apply_payload.get("steps", []) if step.get("step") == "runtime"]
    if not runtime_apply_steps:
        raise SystemExit("fixture runtime apply flow did not include runtime step")
    rewrite_handoff_path = Path(str(runtime_apply_steps[0].get("summary", {}).get("draft", {}).get("rewrite_handoff_path", "")))
    if not rewrite_handoff_path.exists():
        raise SystemExit("fixture runtime apply did not write rewrite handoff artifact")

    dashboard_apply_payload = run_capture_json(
        ["python", "./scripts/dashboard_snapshot.py", "--project", str(project_dir), "--json", "--dry-run"],
        cwd=repo_root,
    )
    applied_runtime = dashboard_apply_payload.get("runtime_signals", {})
    if applied_runtime.get("decision") != "fail":
        raise SystemExit("fixture dashboard did not persist runtime decision after apply")
    require_targets(
        list(applied_runtime.get("applied_targets", [])),
        {"plan.json", "state.json", "timeline.json", "characters.json", "character_arcs.json", "foreshadowing.json"},
        "fixture dashboard did not expose applied runtime targets after apply",
    )

    state_schema = read_json_file(state_schema_path)
    if state_schema.get("currentChapter") != 1:
        raise SystemExit("fixture runtime apply did not update state schema chapter")
    if state_schema.get("runtimeDecision") != "fail":
        raise SystemExit("fixture runtime apply did not persist runtime decision into state schema")
    if state_schema.get("runtimeAdvisoryDimensions") != []:
        raise SystemExit("fixture runtime apply still persisted advisory dimensions after runtime backfill")

    status_runtime_payload = run_capture_json(
        ["python", "./scripts/book_health.py", "--project", str(project_dir), "--json", "--dry-run"],
        cwd=repo_root,
    )
    if "runtime_signals" not in status_runtime_payload:
        raise SystemExit("fixture status output did not expose runtime signals")
    runtime_status_signals = status_runtime_payload.get("runtime_signals", {})
    blocking_dimensions = runtime_status_signals.get("blocking_dimensions", [])
    if not {"continuity", "pacing"}.issubset({str(item) for item in blocking_dimensions}):
        raise SystemExit("fixture status output did not expose expected continuity/pacing blocking dimensions")
    if runtime_status_signals.get("first_fix_priority") != "continuity":
        raise SystemExit("fixture status output did not expose runtime first_fix_priority")
    attention_queue = runtime_status_signals.get("attention_queue", [])
    if not isinstance(attention_queue, list) or not any("runtime blocking: continuity:" in str(item) for item in attention_queue):
        raise SystemExit("fixture status output did not expose runtime blocking attention digest")


def run_pass_fixture_flow(repo_root: Path) -> None:
    tmp_root = repo_root / ".tmp-smoke"
    project_dir = tmp_root / "fixture-book-pass"
    if project_dir.exists():
        shutil.rmtree(project_dir, ignore_errors=True)
    tmp_root.mkdir(parents=True, exist_ok=True)

    run(["node", "./bin/chase.js", "bootstrap", "--project", str(project_dir)], cwd=repo_root)
    prepare_pass_fixture(project_dir)

    quality_payload = run_capture_json(
        ["python", "./scripts/quality_gate.py", "--project", str(project_dir), "--chapter-no", "1", "--json", "--dry-run"],
        cwd=repo_root,
    )
    blocking_verdicts = [item for item in quality_payload.get("verdicts", []) if item.get("blocking")]
    if blocking_verdicts:
        raise SystemExit("pass fixture quality gate still emitted blocking verdicts")

    runtime_payload = run_capture_json(
        ["python", "./scripts/workflow_runner.py", "--project", str(project_dir), "--chapter", "1", "--steps", "runtime", "--json", "--dry-run"],
        cwd=repo_root,
    )
    runtime_steps = [step for step in runtime_payload.get("steps", []) if step.get("step") == "runtime"]
    if not runtime_steps:
        raise SystemExit("pass fixture runtime flow did not include runtime step")
    runtime_summary = runtime_steps[0].get("summary", {})
    runtime_decision = runtime_summary.get("decision", {})
    if runtime_decision.get("decision") not in {"pass", "fail"}:
        raise SystemExit("pass fixture runtime did not emit runtime decision")
    runtime_verdict_dimensions = {str(item.get("dimension", "")).strip() for item in runtime_summary.get("verdicts", [])}
    if not {"causality", "promise_payoff", "dialogue"}.issubset(runtime_verdict_dimensions):
        raise SystemExit("pass fixture runtime did not expose causality/promise_payoff/dialogue verdicts")
    runtime_draft = runtime_summary.get("draft", {})
    if runtime_draft.get("status") not in {"drafted-writer-prompt", "rewritten-runtime-output"}:
        raise SystemExit("pass fixture runtime did not emit expected draft status")
    if not runtime_draft.get("draft_path"):
        raise SystemExit("pass fixture runtime did not expose draft path")
    if runtime_draft.get("scene_count") != 4:
        raise SystemExit("pass fixture runtime did not expose expected scene count")
    if int(runtime_draft.get("word_count", 0) or 0) < 300:
        raise SystemExit("pass fixture runtime draft is still too thin")

    runtime_apply_payload = run_capture_json(
        ["python", "./scripts/workflow_runner.py", "--project", str(project_dir), "--chapter", "1", "--steps", "runtime", "--json"],
        cwd=repo_root,
    )
    runtime_apply_steps = [step for step in runtime_apply_payload.get("steps", []) if step.get("step") == "runtime"]
    if not runtime_apply_steps:
        raise SystemExit("pass fixture runtime apply flow did not include runtime step")
    runtime_apply_summary = runtime_apply_steps[0].get("summary", {})
    runtime_apply_draft = runtime_apply_summary.get("draft", {})
    postdraft_verdicts = runtime_apply_summary.get("postdraft_verdicts", [])
    character_constraints = runtime_apply_draft.get("character_constraints", {})
    scene_cards = runtime_apply_draft.get("scene_cards", [])
    outcome_signature = runtime_apply_draft.get("outcome_signature", {})
    manuscript_path = Path(str(runtime_apply_draft.get("manuscript_path", "")))
    draft_path = Path(str(runtime_apply_draft.get("draft_path", "")))
    review_notes_path = Path(str(runtime_apply_draft.get("review_notes_path", "")))
    rewrite_handoff_path = Path(str(runtime_apply_draft.get("rewrite_handoff_path", ""))) if str(runtime_apply_draft.get("rewrite_handoff_path", "")).strip() else None
    if not draft_path.exists():
        raise SystemExit("pass fixture runtime apply did not write writer prompt artifact")
    if not review_notes_path.exists():
        raise SystemExit("pass fixture runtime apply did not write runtime review notes")
    if not manuscript_path.exists():
        raise SystemExit("pass fixture runtime apply did not write reader manuscript")
    if runtime_apply_draft.get("status") == "rewritten-runtime-output" and (rewrite_handoff_path is None or not rewrite_handoff_path.exists()):
        raise SystemExit("pass fixture runtime apply did not write rewrite handoff artifact when rewrite status was returned")
    if not postdraft_verdicts or str(postdraft_verdicts[0].get("dimension")) != "character":
        raise SystemExit("pass fixture runtime apply did not expose character postdraft verdict")
    if not isinstance(character_constraints, dict) or not isinstance(character_constraints.get("behavior_snapshot"), dict):
        raise SystemExit("pass fixture runtime apply did not expose character behavior snapshot")
    if not isinstance(scene_cards, list) or len(scene_cards) != 4:
        raise SystemExit("pass fixture runtime apply did not expose scene cards")
    if not isinstance(outcome_signature, dict) or outcome_signature.get("hook_type") != "cost_upgrade":
        raise SystemExit("pass fixture runtime apply did not expose expected outcome signature")
    draft_text = draft_path.read_text(encoding="utf-8")
    review_text = review_notes_path.read_text(encoding="utf-8")
    manuscript_text = manuscript_path.read_text(encoding="utf-8")
    if "# Writer 导演单" not in draft_text or "## 本章任务" not in draft_text:
        raise SystemExit("pass fixture writer prompt did not expose expected mission structure")
    if "## 硬边界" not in draft_text or "## 角色声口" not in draft_text:
        raise SystemExit("pass fixture writer prompt did not expose expected boundaries and cast sections")
    protagonist_name = str(character_constraints.get("protagonist", {}).get("name", "")).strip()
    counterpart_name = str(character_constraints.get("counterpart", {}).get("name", "")).strip()
    protagonist_goal = str(character_constraints.get("protagonist_goal", "")).strip()
    protagonist_taboo = str(character_constraints.get("protagonist_taboo", "")).strip()
    counterpart_fear = str(character_constraints.get("counterpart_fear", "")).strip()
    chapter_result = str(outcome_signature.get("chapter_result", "")).strip()
    next_pull = str(outcome_signature.get("next_pull", "")).strip()
    if protagonist_name not in draft_text or counterpart_name not in draft_text:
        raise SystemExit("pass fixture writer prompt did not inject core character context")
    for required_fragment, label in (
        (protagonist_goal, "protagonist_goal"),
        (protagonist_taboo, "protagonist_taboo"),
        (counterpart_fear, "counterpart_fear"),
        (chapter_result, "chapter_result"),
    ):
        if required_fragment and required_fragment not in draft_text:
            raise SystemExit(f"pass fixture writer prompt did not include required {label} context")
    if "## Voice Profiles" not in review_text or "句长=" not in review_text:
        raise SystemExit("pass fixture runtime review notes did not expose voice profiles")
    if protagonist_goal and f"当前诉求={protagonist_goal}" not in review_text:
        raise SystemExit("pass fixture runtime review notes did not consume structured character fields")
    behavior_snapshot = character_constraints.get("behavior_snapshot", {})
    if "protagonist_cautious_markers" not in behavior_snapshot or "counterpart_pressure_markers" not in behavior_snapshot:
        raise SystemExit("pass fixture runtime behavior snapshot did not expose expected markers")
    if not any(str(item.get("result_type")) == "partial_win" for item in scene_cards):
        raise SystemExit("pass fixture runtime scene cards did not expose expected result signatures")
    if "# Chapter 001" not in manuscript_text:
        raise SystemExit("pass fixture reader manuscript did not emit chapter heading")
    if "### Beats" in manuscript_text or "## Runtime Notes" in manuscript_text:
        raise SystemExit("pass fixture reader manuscript still contains runtime scaffolding")
    if chapter_result and chapter_result not in manuscript_text:
        raise SystemExit("pass fixture reader manuscript did not preserve chapter result signal")
    if counterpart_fear and counterpart_fear not in manuscript_text:
        raise SystemExit("pass fixture reader manuscript did not preserve counterpart fear signal")
    cleaned_next_pull = next_pull
    if next_pull == "延续当前压力，并形成下一章牵引":
        cleaned_next_pull = "下一步的价码已经被重新抬高了"
    if next_pull and next_pull not in manuscript_text and cleaned_next_pull not in manuscript_text:
        raise SystemExit("pass fixture reader manuscript did not preserve next pull signal")

    manuscript_body = "\n".join(manuscript_text.splitlines()[1:])
    residual_task_tokens = (
        "本章",
        "章节",
        "核心冲突",
        "章卡",
        "scene",
        "Scene",
        "体验目标",
        "形成下一章牵引",
        "推进结果",
        "target_word_count",
    )
    if any(token in manuscript_body for token in residual_task_tokens):
        raise SystemExit("pass fixture reader manuscript still leaked task-language scaffolding")

    abstract_tokens = ("某种意义上", "真正", "其实", "显然", "无疑")
    abstract_hits = sum(manuscript_body.count(token) for token in abstract_tokens)
    if abstract_hits > 2:
        raise SystemExit("pass fixture reader manuscript still contains too many abstract filler phrases")

    repeated_template_lines = [
        line.strip()
        for line in manuscript_body.splitlines()
        if line.strip() and (
            "连呼吸" in line
            or "先把" in line
            or "没有急着" in line
            or "停了半拍" in line
        )
    ]
    if len(repeated_template_lines) > 8:
        raise SystemExit("pass fixture reader manuscript still relies on too many repeated template lines")
    character_verdict_path = project_dir / "00_memory" / "retrieval" / "leadwriter_character_verdict.json"
    if not character_verdict_path.exists():
        raise SystemExit("pass fixture runtime apply did not write character verdict report")

    dashboard_payload = run_capture_json(
        ["python", "./scripts/dashboard_snapshot.py", "--project", str(project_dir), "--json", "--dry-run"],
        cwd=repo_root,
    )
    runtime_signals = dashboard_payload.get("runtime_signals", {})
    if runtime_signals.get("character_alignment_status") != "pass":
        raise SystemExit("pass fixture dashboard did not expose passing character alignment signal")
    cycle_count = runtime_signals.get("cycle_count")
    if not isinstance(cycle_count, int) or cycle_count < 1:
        raise SystemExit("pass fixture dashboard did not expose valid runtime cycle count")
    advisory_digest = runtime_signals.get("advisory_digest", [])
    if advisory_digest and not isinstance(advisory_digest, list):
        raise SystemExit("pass fixture dashboard exposed invalid advisory runtime digest payload")

    quality_after_runtime = run_capture_json(
        ["python", "./scripts/quality_gate.py", "--project", str(project_dir), "--chapter-no", "1", "--json", "--dry-run"],
        cwd=repo_root,
    )
    if quality_after_runtime.get("final_release") != "pass":
        raise SystemExit("pass fixture quality gate did not expose pass final_release after plan/arc backfill")
    if quality_after_runtime.get("status") not in {"pass", "warn"}:
        raise SystemExit("pass fixture quality gate did not return non-blocking status after plan/arc backfill")
    character_verdicts = [item for item in quality_after_runtime.get("verdicts", []) if item.get("dimension") == "character"]
    if not character_verdicts or character_verdicts[0].get("status") != "pass":
        raise SystemExit("pass fixture quality gate did not expose passing character verdict")
    verdict_dimensions = {str(item.get("dimension")) for item in quality_after_runtime.get("verdicts", [])}
    if not {"plan", "foreshadow", "arc", "character", "causality", "promise_payoff", "pacing", "dialogue"}.issubset(verdict_dimensions):
        raise SystemExit("pass fixture quality gate did not expose schema-aware verdict dimensions")

    status_after_runtime = run_capture_json(
        ["python", "./scripts/book_health.py", "--project", str(project_dir), "--json", "--dry-run"],
        cwd=repo_root,
    )
    runtime_signals_after = status_after_runtime.get("runtime_signals", {})
    if "plan_status" not in runtime_signals_after or "foreshadow_overdue_count" not in runtime_signals_after or "arc_stalled_count" not in runtime_signals_after:
        raise SystemExit("pass fixture status did not expose schema-aware runtime signals")
    advisory_dimensions_after = runtime_signals_after.get("advisory_dimensions", [])
    if advisory_dimensions_after and not all(isinstance(item, str) for item in advisory_dimensions_after):
        raise SystemExit("pass fixture status exposed invalid advisory dimensions payload")
    advisory_digest_after = runtime_signals_after.get("advisory_digest", [])
    if advisory_digest_after and not isinstance(advisory_digest_after, list):
        raise SystemExit("pass fixture status exposed invalid advisory runtime digest payload")

    write_default_payload = run_capture_json(
        ["python", "./scripts/workflow_runner.py", "--project", str(project_dir), "--chapter", "1", "--json", "--dry-run"],
        cwd=repo_root,
    )
    quality_steps = [step for step in write_default_payload.get("steps", []) if step.get("step") == "quality"]
    if not quality_steps:
        raise SystemExit("pass fixture default write flow did not include quality step")
    pipeline_summary = write_default_payload.get("pipeline_summary", {})
    if pipeline_summary.get("quality_final_release") != "pass":
        raise SystemExit("pass fixture default write flow did not expose pass quality_final_release")
    if pipeline_summary.get("final_release") != "pass":
        raise SystemExit("pass fixture default write flow did not expose pass pipeline final_release")
    if write_default_payload.get("final_release") != "pass":
        raise SystemExit("pass fixture default write flow did not expose top-level pass final_release")

    write_apply_payload = run_capture_json(
        ["python", "./scripts/workflow_runner.py", "--project", str(project_dir), "--chapter", "1", "--json"],
        cwd=repo_root,
    )
    markdown_report_path = Path(str(write_apply_payload.get("report_paths", {}).get("markdown", "")))
    if not markdown_report_path.exists():
        raise SystemExit("pass fixture write flow did not write markdown pipeline report")
    markdown_report_text = markdown_report_path.read_text(encoding="utf-8")
    if "## Aggregate Summary" not in markdown_report_text:
        raise SystemExit("pass fixture markdown pipeline report did not expose aggregate summary section")
    if "final_release=`pass`" not in markdown_report_text:
        raise SystemExit("pass fixture markdown pipeline report did not expose final_release")
    if "quality_final_release=`pass`" not in markdown_report_text:
        raise SystemExit("pass fixture markdown pipeline report did not expose quality_final_release")
    if "runtime_decision=`pass`" not in markdown_report_text:
        raise SystemExit("pass fixture markdown pipeline report did not expose runtime_decision")

    fallback_project_dir = tmp_root / "fixture-book-fallback"
    if fallback_project_dir.exists():
        shutil.rmtree(fallback_project_dir, ignore_errors=True)
    shutil.copytree(project_dir, fallback_project_dir)
    for fallback_payload_path in (
        fallback_project_dir / "00_memory" / "retrieval" / "leadwriter_runtime_payload.json",
        fallback_project_dir / "00_memory" / "retrieval" / "leadwriter_character_verdict.json",
    ):
        if fallback_payload_path.exists():
            fallback_payload_path.unlink()

    fallback_quality = run_capture_json(
        ["python", "./scripts/quality_gate.py", "--project", str(fallback_project_dir), "--chapter-no", "1", "--json", "--dry-run"],
        cwd=repo_root,
    )
    if fallback_quality.get("runtime_verdict_source") != "quality_fallback":
        raise SystemExit("fallback fixture quality gate did not expose quality_fallback runtime_verdict_source")
    fallback_dimensions = set(fallback_quality.get("fallback_runtime_dimensions", []))
    if fallback_dimensions != {"character", "causality", "promise_payoff", "pacing", "dialogue"}:
        raise SystemExit("fallback fixture quality gate did not expose complete fallback runtime dimensions")
    if fallback_quality.get("missing_runtime_dimensions") != []:
        raise SystemExit("fallback fixture quality gate still exposed missing runtime dimensions after fallback backfill")
    fallback_advisories = set(fallback_quality.get("advisory_dimensions", []))
    if not {"character", "causality", "promise_payoff", "pacing", "dialogue"}.issubset(fallback_advisories):
        raise SystemExit("fallback fixture quality gate did not surface fallback runtime advisories")

    fallback_quality_written = run_capture_json(
        ["python", "./scripts/quality_gate.py", "--project", str(fallback_project_dir), "--chapter-no", "1", "--json"],
        cwd=repo_root,
    )
    fallback_quality_report = Path(str(fallback_quality_written.get("report_paths", {}).get("markdown", "")))
    if not fallback_quality_report.exists():
        raise SystemExit("fallback fixture quality gate did not write markdown report")
    fallback_quality_report_text = fallback_quality_report.read_text(encoding="utf-8")
    if "## Runtime Verdict Coverage" not in fallback_quality_report_text:
        raise SystemExit("fallback fixture quality markdown report did not expose runtime coverage section")
    if "runtime_verdict_source: `quality_fallback`" not in fallback_quality_report_text:
        raise SystemExit("fallback fixture quality markdown report did not expose quality_fallback provenance")

    fallback_pipeline = run_capture_json(
        [
            "python",
            "./scripts/workflow_runner.py",
            "--project",
            str(fallback_project_dir),
            "--chapter",
            "1",
            "--steps",
            "quality",
            "--json",
            "--dry-run",
        ],
        cwd=repo_root,
    )
    fallback_pipeline_summary = fallback_pipeline.get("pipeline_summary", {})
    if fallback_pipeline_summary.get("quality_runtime_verdict_source") != "quality_fallback":
        raise SystemExit("fallback fixture pipeline summary did not expose quality_fallback provenance")
    if set(fallback_pipeline_summary.get("quality_fallback_runtime_dimensions", [])) != {
        "character",
        "causality",
        "promise_payoff",
        "pacing",
        "dialogue",
    }:
        raise SystemExit("fallback fixture pipeline summary did not expose complete fallback runtime dimensions")


def run_promise_layer_fixture_flow(repo_root: Path) -> None:
    tmp_root = repo_root / ".tmp-smoke"
    project_dir = tmp_root / "fixture-book-promise-layer"
    if project_dir.exists():
        shutil.rmtree(project_dir, ignore_errors=True)
    tmp_root.mkdir(parents=True, exist_ok=True)

    run(["node", "./bin/chase.js", "bootstrap", "--project", str(project_dir)], cwd=repo_root)
    prepare_promise_layer_fixture(project_dir)

    quality_payload = run_capture_json(
        ["python", "./scripts/quality_gate.py", "--project", str(project_dir), "--chapter-no", "1", "--json", "--dry-run"],
        cwd=repo_root,
    )
    if quality_payload.get("runtime_verdict_source") != "quality_fallback":
        raise SystemExit("promise-layer fixture did not run through quality fallback")
    promise_layers = analyze_promise_layers(
        "主角开始掌握主动权，不再只是被动挨打。苏晚记住了他的表态，盯他以后是不是照做。",
        "苏晚记住了他的表态，盯他以后是不是照做。",
        "主角开始掌握主动权，不再只是被动挨打",
        "苏晚记住了他的表态，盯他以后是不是照做",
    )
    if not promise_layers["result_landed"]:
        raise SystemExit("promise-layer synthetic check did not recognize short payoff landing")
    if not promise_layers["tail_landed"]:
        raise SystemExit("promise-layer synthetic check did not recognize visible hook landing")
    if promise_layers["tail_escalated"]:
        raise SystemExit("promise-layer synthetic check incorrectly treated non-escalating hook as upgraded pressure")


def run_information_shift_fixture_flow(repo_root: Path) -> None:
    tmp_root = repo_root / ".tmp-smoke"
    project_dir = tmp_root / "fixture-book-information-shift"
    if project_dir.exists():
        shutil.rmtree(project_dir, ignore_errors=True)
    tmp_root.mkdir(parents=True, exist_ok=True)

    run(["node", "./bin/chase.js", "bootstrap", "--project", str(project_dir)], cwd=repo_root)
    prepare_information_shift_fixture(project_dir)

    for runtime_payload_path in (
        project_dir / "00_memory" / "retrieval" / "leadwriter_runtime_payload.json",
        project_dir / "00_memory" / "retrieval" / "leadwriter_character_verdict.json",
    ):
        if runtime_payload_path.exists():
            runtime_payload_path.unlink()

    quality_payload = run_capture_json(
        ["python", "./scripts/quality_gate.py", "--project", str(project_dir), "--chapter-no", "1", "--json", "--dry-run"],
        cwd=repo_root,
    )
    if quality_payload.get("runtime_verdict_source") != "quality_fallback":
        raise SystemExit("information-shift fixture did not run through quality fallback")

    causality_verdict = find_verdict(quality_payload, "causality")
    if not causality_verdict:
        raise SystemExit("information-shift fixture did not emit causality fallback verdict")
    causality_evidence = {str(item) for item in causality_verdict.get("evidence", [])}
    if "正文出现了试探、看穿或确认底牌的信息信号，但没有把这次信息得知转成后续判断变化或局面位移。" not in causality_evidence:
        raise SystemExit("information-shift fixture did not expose causality info-transfer evidence")

    character_verdict = find_verdict(quality_payload, "character")
    if not character_verdict:
        raise SystemExit("information-shift fixture did not emit character fallback verdict")
    character_evidence = {str(item) for item in character_verdict.get("evidence", [])}
    if "对位角色“苏晚”虽然已经试出信息或听出表态，但人物关系没有因此发生可见变化，信息差还没真正转手。" not in character_evidence:
        raise SystemExit("information-shift fixture did not expose character info-transfer evidence")

    dialogue_verdict = find_verdict(quality_payload, "dialogue")
    if not dialogue_verdict:
        raise SystemExit("information-shift fixture did not emit dialogue fallback verdict")
    dialogue_evidence = {str(item) for item in dialogue_verdict.get("evidence", [])}
    if "对白里已经出现试探、看穿或确认信息的信号，但没有把信息差转成新的站位、压制或关系变化。" not in dialogue_evidence:
        raise SystemExit("information-shift fixture did not expose dialogue info-transfer evidence")


def run_relationship_shift_checks() -> None:
    shifted = analyze_relationship_shift(
        "苏晚看着他的动作，第一次把戒备收了一寸，也第一次肯承认他不是只会躲的人。关系没有一下子翻面，却已经出现了能被看见的偏移。",
        "盟友",
        "苏晚",
    )
    if shifted["relationship_hits"] <= 0:
        raise SystemExit("relationship-shift synthetic check did not recognize visible relation movement")
    if shifted["counterpart_visible"] != 1:
        raise SystemExit("relationship-shift synthetic check did not recognize counterpart presence")

    flat = analyze_relationship_shift(
        "苏晚站在旁边看着他，没有再多说话，只记住了刚才那句表态。",
        "盟友",
        "苏晚",
    )
    if flat["relationship_hits"] != 0:
        raise SystemExit("relationship-shift synthetic check incorrectly treated static relation text as visible movement")


def run_information_shift_checks() -> None:
    shifted = analyze_information_shift(
        "苏晚听出他不是在硬撑，第一次把戒备收了一寸，也重新估价了林砚手里的底牌。",
        ["你刚才不是没退。", "我知道你不是在硬撑。", "好，我记住你这句。"],
    )
    if shifted["dialogue_reveal_hits"] <= 0:
        raise SystemExit("information-shift synthetic check did not recognize reveal dialogue")
    if shifted["transfer_hits"] <= 0:
        raise SystemExit("information-shift synthetic check did not recognize visible transfer into position change")

    flat = analyze_information_shift(
        "苏晚听出了他的表态，但场面没有继续变化，两人只是把话停在这里。",
        ["我知道你想拿回主动权。", "好，我听见了。", "那就这样。"],
    )
    if flat["dialogue_reveal_hits"] <= 0:
        raise SystemExit("information-shift flat synthetic check did not recognize reveal dialogue")
    if flat["transfer_hits"] != 0:
        raise SystemExit("information-shift flat synthetic check incorrectly treated static aftermath as transferred leverage")


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    npm = shutil.which("npm") or shutil.which("npm.cmd") or "npm"

    print("[smoke] checking CLI help")
    run(["node", "./bin/chase.js", "--help"], cwd=repo_root)

    print("[smoke] checking change analyzer")
    run_change_analyzer_checks(repo_root)

    print("[smoke] compiling python scripts")
    compile_python_scripts(repo_root)

    print("[smoke] checking runtime decision policy")
    run_runtime_policy_checks()
    run_relationship_shift_checks()
    run_information_shift_checks()

    print("[smoke] running bootstrap/doctor/open fixture")
    run_fixture_flow(repo_root)

    print("[smoke] running pass fixture")
    run_pass_fixture_flow(repo_root)

    print("[smoke] running promise-layer fixture")
    run_promise_layer_fixture_flow(repo_root)

    print("[smoke] running information-shift fixture")
    run_information_shift_fixture_flow(repo_root)

    print("[smoke] dry-run package build")
    npm_env = dict(os.environ)
    npm_env["npm_config_cache"] = str((repo_root / ".tmp-npm-cache").resolve())
    run([npm, "pack", "--dry-run"], cwd=repo_root, env=npm_env)

    print("[smoke] ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
