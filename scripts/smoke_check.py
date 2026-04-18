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
from runtime.runtime_orchestrator import LeadWriterRuntime


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


def prepare_fixture(project_dir: Path) -> None:
    memory_dir = project_dir / "00_memory"
    (memory_dir / "plan.md").write_text(
        "# 主线计划\n\n"
        "## 核心设定（不可偏离）\n"
        "- 书名：测试书\n"
        "- 题材：都市系统\n"
        "- 核心卖点：普通人靠系统翻身\n"
        "- 预计总字数：1200000\n",
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
    chapter_body = "主角稳住呼吸，盯着走廊尽头的脚步声，确认自己终于拿回了一点主动。\n" * 88
    (memory_dir / "plan.md").write_text(
        "# 主线计划\n\n"
        "- 书名：测试书\n"
        "- 题材：都市系统\n"
        "- 核心卖点：普通人靠系统翻身\n",
        encoding="utf-8",
    )
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

    write_payload = run_capture_json(
        ["python", "./scripts/workflow_runner.py", "--project", str(project_dir), "--chapter", "1", "--json", "--dry-run"],
        cwd=repo_root,
    )
    runtime_steps = [step for step in write_payload.get("steps", []) if step.get("step") == "runtime"]
    if not runtime_steps:
        raise SystemExit("fixture write flow did not include runtime step")
    runtime_summary = runtime_steps[0].get("summary", {})
    runtime_decision = runtime_summary.get("decision", {})
    if runtime_decision.get("decision") != "revise":
        raise SystemExit("fixture runtime dry-run did not emit revise decision")
    runtime_draft = runtime_summary.get("draft", {})
    if runtime_draft.get("status") != "pending-human-rewrite":
        raise SystemExit("fixture runtime dry-run did not emit rewrite handoff status")
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
    require_targets(
        list(dashboard_runtime.get("ready_targets", [])),
        {"plan.json", "state.json", "timeline.json", "characters.json", "foreshadowing.json"},
        "fixture dashboard did not expose expected ready runtime targets",
    )

    memory_apply_dry_payload = run_capture_json(
        ["python", "./scripts/memory_sync_apply.py", "--project", str(project_dir), "--json", "--dry-run"],
        cwd=repo_root,
    )
    ready_results = [item for item in memory_apply_dry_payload.get("results", []) if item.get("status") == "ready"]
    require_targets(
        [str(item.get("target", "")).strip() for item in ready_results],
        {"plan.json", "state.json", "timeline.json", "characters.json", "foreshadowing.json"},
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
    if applied_runtime.get("decision") != "revise":
        raise SystemExit("fixture dashboard did not persist runtime decision after apply")
    require_targets(
        list(applied_runtime.get("applied_targets", [])),
        {"plan.json", "state.json", "timeline.json", "characters.json", "foreshadowing.json"},
        "fixture dashboard did not expose applied runtime targets after apply",
    )

    state_schema = read_json_file(state_schema_path)
    if state_schema.get("currentChapter") != 1:
        raise SystemExit("fixture runtime apply did not update state schema chapter")
    if state_schema.get("runtimeDecision") != "revise":
        raise SystemExit("fixture runtime apply did not persist runtime decision into state schema")
    if state_schema.get("runtimeAdvisoryDimensions") != ["plan", "arc"]:
        raise SystemExit("fixture runtime apply did not persist advisory dimensions into state schema")

    status_runtime_payload = run_capture_json(
        ["python", "./scripts/book_health.py", "--project", str(project_dir), "--json", "--dry-run"],
        cwd=repo_root,
    )
    if "runtime_signals" not in status_runtime_payload:
        raise SystemExit("fixture status output did not expose runtime signals")
    blocking_dimensions = status_runtime_payload.get("runtime_signals", {}).get("blocking_dimensions", [])
    if blocking_dimensions != ["continuity", "pacing"]:
        raise SystemExit("fixture status output did not expose expected blocking dimensions")


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
    if runtime_decision.get("decision") != "pass":
        raise SystemExit("pass fixture runtime did not emit pass decision")
    runtime_draft = runtime_summary.get("draft", {})
    if runtime_draft.get("status") != "ready-human-review":
        raise SystemExit("pass fixture runtime did not emit draft review status")
    if not runtime_draft.get("draft_path"):
        raise SystemExit("pass fixture runtime did not expose draft path")
    if runtime_draft.get("scene_count") != 4:
        raise SystemExit("pass fixture runtime did not expose expected scene count")
    if int(runtime_draft.get("word_count", 0) or 0) < 400:
        raise SystemExit("pass fixture runtime draft is still too thin")

    runtime_apply_payload = run_capture_json(
        ["python", "./scripts/workflow_runner.py", "--project", str(project_dir), "--chapter", "1", "--steps", "runtime", "--json"],
        cwd=repo_root,
    )
    runtime_apply_steps = [step for step in runtime_apply_payload.get("steps", []) if step.get("step") == "runtime"]
    if not runtime_apply_steps:
        raise SystemExit("pass fixture runtime apply flow did not include runtime step")
    runtime_apply_draft = runtime_apply_steps[0].get("summary", {}).get("draft", {})
    postdraft_verdicts = runtime_apply_steps[0].get("summary", {}).get("postdraft_verdicts", [])
    character_constraints = runtime_apply_draft.get("character_constraints", {})
    scene_cards = runtime_apply_draft.get("scene_cards", [])
    outcome_signature = runtime_apply_draft.get("outcome_signature", {})
    blueprint_path = Path(str(runtime_apply_draft.get("blueprint_path", "")))
    editorial_summary_path = Path(str(runtime_apply_draft.get("editorial_summary_path", "")))
    manuscript_path = Path(str(runtime_apply_draft.get("manuscript_path", "")))
    draft_path = Path(str(runtime_apply_draft.get("draft_path", "")))
    review_notes_path = Path(str(runtime_apply_draft.get("review_notes_path", "")))
    if not draft_path.exists():
        raise SystemExit("pass fixture runtime apply did not write runtime draft artifact")
    if not review_notes_path.exists():
        raise SystemExit("pass fixture runtime apply did not write runtime review notes")
    if not blueprint_path.exists():
        raise SystemExit("pass fixture runtime apply did not write chapter blueprint")
    if not editorial_summary_path.exists():
        raise SystemExit("pass fixture runtime apply did not write editorial summary")
    if not manuscript_path.exists():
        raise SystemExit("pass fixture runtime apply did not write reader manuscript")
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
    blueprint_text = blueprint_path.read_text(encoding="utf-8")
    editorial_summary_text = editorial_summary_path.read_text(encoding="utf-8")
    manuscript_text = manuscript_path.read_text(encoding="utf-8")
    if "## Scene 1 开场压迫" not in draft_text or "## Scene 4 代价揭示" not in draft_text:
        raise SystemExit("pass fixture runtime draft did not expose expected scene structure")
    if "### Beats" not in draft_text or "### Draft" not in draft_text:
        raise SystemExit("pass fixture runtime draft did not expose scene beat structure")
    if "林砚" not in draft_text or "苏晚" not in draft_text:
        raise SystemExit("pass fixture runtime draft did not inject character-driven dialogue")
    if "“" not in draft_text:
        raise SystemExit("pass fixture runtime draft still lacks dialogue lines")
    if "拿回主动权" not in draft_text or "不把命交给运气" not in draft_text or "局面彻底失控" not in draft_text:
        raise SystemExit("pass fixture runtime draft did not consume goal/fear/taboo fields in正文")
    if "- protagonist_goal: 拿回主动权" not in draft_text or "- counterpart_fear: 局面彻底失控" not in draft_text:
        raise SystemExit("pass fixture runtime notes did not expose structured character constraints")
    if "信任已经开始绷紧" not in draft_text or "系统给出的不是白拿的筹码" not in draft_text or "价码" not in manuscript_text:
        raise SystemExit("pass fixture runtime scenes did not preserve differentiated mid-scene and end-hook rhythm")
    if "## Voice Profiles" not in review_text or "句长=" not in review_text:
        raise SystemExit("pass fixture runtime review notes did not expose voice profiles")
    if "当前诉求=拿回主动权" not in review_text or "决策风格=谨慎" not in review_text:
        raise SystemExit("pass fixture runtime review notes did not consume structured character fields")
    behavior_snapshot = character_constraints.get("behavior_snapshot", {})
    if not behavior_snapshot.get("protagonist_cautious_markers") or not behavior_snapshot.get("counterpart_pressure_markers"):
        raise SystemExit("pass fixture runtime behavior snapshot did not capture expected action markers")
    if not any(str(item.get("result_type")) == "partial_win" for item in scene_cards):
        raise SystemExit("pass fixture runtime scene cards did not expose expected result signatures")
    if "## Scene Cards" not in blueprint_text or "result_type: partial_win_with_pressure_kept" not in blueprint_text:
        raise SystemExit("pass fixture chapter blueprint did not expose expected chapter signature")
    if "主动权" not in blueprint_text or "价码" not in draft_text:
        raise SystemExit("pass fixture runtime structure did not apply urban-system genre profile")
    if "结算" not in draft_text:
        raise SystemExit("pass fixture runtime paragraphs did not apply urban-system action profile")
    if "# Editorial Summary" not in editorial_summary_text or "counterpart_pressure_markers:" not in editorial_summary_text:
        raise SystemExit("pass fixture editorial summary did not expose expected editorial trace")
    if "### Beats" in manuscript_text or "## Runtime Notes" in manuscript_text:
        raise SystemExit("pass fixture reader manuscript still contains runtime scaffolding")
    if "拿回主动权" not in manuscript_text or "局面彻底失控" not in manuscript_text:
        raise SystemExit("pass fixture reader manuscript did not preserve core chapter outcome")
    if "价码" not in manuscript_text:
        raise SystemExit("pass fixture reader manuscript did not apply urban-system genre wording")
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

    quality_after_runtime = run_capture_json(
        ["python", "./scripts/quality_gate.py", "--project", str(project_dir), "--chapter-no", "1", "--json", "--dry-run"],
        cwd=repo_root,
    )
    character_verdicts = [item for item in quality_after_runtime.get("verdicts", []) if item.get("dimension") == "character"]
    if not character_verdicts or character_verdicts[0].get("status") != "pass":
        raise SystemExit("pass fixture quality gate did not expose passing character verdict")
    verdict_dimensions = {str(item.get("dimension")) for item in quality_after_runtime.get("verdicts", [])}
    if not {"plan", "foreshadow", "arc", "character"}.issubset(verdict_dimensions):
        raise SystemExit("pass fixture quality gate did not expose schema-aware verdict dimensions")

    status_after_runtime = run_capture_json(
        ["python", "./scripts/book_health.py", "--project", str(project_dir), "--json", "--dry-run"],
        cwd=repo_root,
    )
    runtime_signals_after = status_after_runtime.get("runtime_signals", {})
    if "plan_status" not in runtime_signals_after or "foreshadow_overdue_count" not in runtime_signals_after or "arc_stalled_count" not in runtime_signals_after:
        raise SystemExit("pass fixture status did not expose schema-aware runtime signals")
    if runtime_signals_after.get("advisory_dimensions") != ["plan", "arc"]:
        raise SystemExit("pass fixture status did not expose expected advisory dimensions")


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    npm = shutil.which("npm") or shutil.which("npm.cmd") or "npm"

    print("[smoke] checking CLI help")
    run(["node", "./bin/chase.js", "--help"], cwd=repo_root)

    print("[smoke] compiling python scripts")
    compile_python_scripts(repo_root)

    print("[smoke] checking runtime decision policy")
    run_runtime_policy_checks()

    print("[smoke] running bootstrap/doctor/open fixture")
    run_fixture_flow(repo_root)

    print("[smoke] running pass fixture")
    run_pass_fixture_flow(repo_root)

    print("[smoke] dry-run package build")
    npm_env = dict(os.environ)
    npm_env["npm_config_cache"] = str((repo_root / ".tmp-npm-cache").resolve())
    run([npm, "pack", "--dry-run"], cwd=repo_root, env=npm_env)

    print("[smoke] ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
