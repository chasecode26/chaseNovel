#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evaluators.continuity import from_gate_payload
from evaluators.draft import from_draft_payload
from evaluators.style import from_language_payload
from evaluators.contracts import build_verdict

from aggregation_utils import (
    build_aggregate_payload,
    configure_utf8_stdio,
    run_step_specs,
    write_aggregate_reports,
)


def load_optional_character_verdict(project_dir: Path) -> dict[str, object] | None:
    verdict_path = project_dir / "00_memory" / "retrieval" / "leadwriter_character_verdict.json"
    if not verdict_path.exists():
        return None
    try:
        payload = json.loads(verdict_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def build_schema_verdicts(project_dir: Path) -> list[dict[str, object]]:
    schema_dir = project_dir / "00_memory" / "schema"
    reports_dir = project_dir / "05_reports"
    plan_json = load_json(schema_dir / "plan.json")
    foreshadow_json = load_json(reports_dir / "foreshadow_heatmap.json")
    arc_json = load_json(reports_dir / "arc_health.json")
    verdicts: list[dict[str, object]] = []

    plan_evidence: list[str] = []
    if not str(plan_json.get("title", "")).strip():
        plan_evidence.append("plan schema 缺少书名。")
    if not str(plan_json.get("genre", "")).strip():
        plan_evidence.append("plan schema 缺少题材。")
    if not str(plan_json.get("hook", "")).strip():
        plan_evidence.append("plan schema 缺少核心 hook。")
    if int(plan_json.get("targetWords", 0) or 0) <= 0:
        plan_evidence.append("plan schema 还没有有效总字数目标。")
    verdicts.append(
        build_verdict(
            dimension="plan",
            status="warn" if plan_evidence else "pass",
            blocking=False,
            evidence=plan_evidence,
            why_it_breaks="卷级规划缺口会削弱章节目标与长线推进的一致性。",
            minimal_fix="补齐 plan schema 的书名、题材、hook 和总字数目标。",
            rewrite_scope="planning_memory",
        )
    )

    foreshadow_evidence: list[str] = []
    overdue = foreshadow_json.get("overdue", [])
    due = foreshadow_json.get("due", [])
    if isinstance(overdue, list) and overdue:
        foreshadow_evidence.append(f"存在 {len(overdue)} 条超期伏笔。")
    if isinstance(due, list) and due:
        foreshadow_evidence.append(f"当前章节有 {len(due)} 条到期伏笔待回收。")
    verdicts.append(
        build_verdict(
            dimension="foreshadow",
            status="warn" if foreshadow_evidence else "pass",
            blocking=False,
            evidence=foreshadow_evidence,
            why_it_breaks="伏笔到期但未调度时，会削弱回收节奏和读者记忆热度。",
            minimal_fix="安排到期/超期伏笔的回收窗口，或明确延后策略。",
            rewrite_scope="chapter_result_and_hook",
        )
    )

    arc_evidence: list[str] = []
    stalled_count = int(arc_json.get("stalled_arc_count", 0) or 0)
    if stalled_count > 0:
        arc_evidence.append(f"存在 {stalled_count} 个角色弧停滞风险。")
    if not arc_json.get("character_arcs"):
        arc_evidence.append("character arc schema/报告仍为空。")
    verdicts.append(
        build_verdict(
            dimension="arc",
            status="warn" if arc_evidence else "pass",
            blocking=False,
            evidence=arc_evidence,
            why_it_breaks="角色弧停滞或缺失时，章节推进会失去人物层结果变化。",
            minimal_fix="补齐角色弧状态，并把本章结果挂到角色阶段变化上。",
            rewrite_scope="character_arc_memory + chapter_result",
        )
    )
    return verdicts

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run draft / chapter / language gates as one quality step.")
    parser.add_argument("--project", required=True, help="Path to the novel project root")
    parser.add_argument(
        "--check",
        choices=["all", "chapter", "draft", "language", "batch"],
        default="all",
        help="Quality sub-check to run; defaults to all chapter-level checks",
    )
    parser.add_argument("--chapter-no", type=int, help="Target chapter number")
    parser.add_argument("--from", dest="chapter_from", type=int, help="Batch start chapter")
    parser.add_argument("--to", dest="chapter_to", type=int, help="Batch end chapter")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    return parser.parse_args()


def build_verdicts(steps: list[dict[str, object]]) -> list[dict[str, object]]:
    verdicts: list[dict[str, object]] = []
    for step in steps:
        script_name = str(step.get("script", ""))
        if script_name == "chapter_gate.py":
            verdicts.append(from_gate_payload(step))
        elif script_name == "draft_gate.py":
            verdicts.append(from_draft_payload(step))
        elif script_name == "language_audit.py":
            verdicts.append(from_language_payload(step))
    return verdicts

def main() -> int:
    configure_utf8_stdio()
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    shared = ["--project", args.project]
    if args.dry_run:
        shared.append("--dry-run")

    if args.check == "batch" or args.chapter_from is not None or args.chapter_to is not None:
        batch_args = shared[:]
        if args.chapter_from is not None:
            batch_args.extend(["--from", str(args.chapter_from)])
        if args.chapter_to is not None:
            batch_args.extend(["--to", str(args.chapter_to)])
        step_specs = [("batch_gate.py", batch_args)]
    else:
        if args.chapter_no is None:
            raise SystemExit("--chapter-no is required unless running batch mode")
        chapter_args = [*shared, "--chapter-no", str(args.chapter_no)]
        if args.check == "chapter":
            step_specs = [("chapter_gate.py", chapter_args)]
        elif args.check == "draft":
            step_specs = [("draft_gate.py", chapter_args)]
        elif args.check == "language":
            step_specs = [("language_audit.py", chapter_args)]
        else:
            step_specs = [
                ("chapter_gate.py", chapter_args),
                ("draft_gate.py", chapter_args),
                ("language_audit.py", chapter_args),
            ]
    steps = run_step_specs(repo_root, step_specs)

    payload = build_aggregate_payload(project=args.project, steps=steps, extra_fields={"check": args.check})
    verdicts = build_verdicts(steps)
    project_dir = Path(args.project).resolve()
    verdicts.extend(build_schema_verdicts(project_dir))
    character_verdict = load_optional_character_verdict(project_dir)
    if isinstance(character_verdict, dict) and str(character_verdict.get("dimension", "")).strip() == "character":
        verdicts.append(character_verdict)
    payload["verdicts"] = verdicts
    payload["final_release"] = "revise" if any(item.get("blocking") for item in verdicts) else payload["status"]
    payload["report_paths"] = {
        **payload.get("report_paths", {}),
        **({} if args.dry_run else write_aggregate_reports(
            project_dir,
            payload,
            base_name="quality_gate_report",
            heading="质量闸门汇总报告",
            mode_line=f"- 检查模式：`{args.check}`",
        )),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']}")
        print(f"check={payload['check']}")
        print(f"warning_count={payload['warning_count']}")
        if isinstance(payload.get("report_paths"), dict) and payload["report_paths"].get("markdown"):
            print(f"report={payload['report_paths']['markdown']}")
    return 0 if payload["status"] != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
