"""
卷级质量门禁 — 填补跨卷连续性检测的架构空白。

四大功能：
1. 卷映射：解析 plan.md 建立 chapter→volume 映射
2. 卷退出检查：卷末章时验证承诺兑现/伏笔回收/弧线阶段
3. 卷进入初始化：新卷首章时检查跨卷记忆交接
4. 卷级健康报告：按卷分段的聚合统计

独立 CLI 使用：
    python scripts/volume_gate.py --project <dir> --chapter <N>
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# 卷映射
# ---------------------------------------------------------------------------

def _parse_volume_outline_from_plan(plan_text: str) -> list[dict]:
    """从 plan.md 解析卷纲，提取每卷的章节范围。"""
    volumes: list[dict] = []
    volume_pattern = re.compile(
        r"[-*]\s*第([一二三四五六七八九十\d]+)卷[：:]\s*\n"
        r"(?:\s*[-*]\s*阶段目标[：:]\s*(.*?)\n)?"
        r"(?:\s*[-*]\s*卷尾必须兑现什么[：:]\s*(.*?)\n)?"
        r"(?:\s*[-*]\s*卷尾必须抬起什么[：:]\s*(.*?)\n)?",
        re.MULTILINE,
    )

    # 也尝试更宽松的匹配
    loose_pattern = re.compile(
        r"第([一二三四五六七八九十\d]+)卷[\s\S]*?"
        r"(?=第[一二三四五六七八九十\d]+卷|$)",
        re.MULTILINE,
    )

    # 从 plan.json schema 读取更精准的卷信息
    # 此处先用 plan.md 文本解析作为回退

    for m in volume_pattern.finditer(plan_text):
        vol_num_raw = m.group(1)
        vol_name = f"第{vol_num_raw}卷"
        stage_goal = (m.group(2) or "").strip()
        must_deliver = (m.group(3) or "").strip()
        must_raise = (m.group(4) or "").strip()
        volumes.append({
            "volume": vol_name,
            "stage_goal": stage_goal,
            "must_deliver": must_deliver,
            "must_raise": must_raise,
        })

    # 如果上面没匹配到，尝试从 schema/plan.json 读取
    return volumes


def _build_volume_map(project_dir: Path, plan_text: str) -> dict[int, dict]:
    """
    建立 chapter → volume 映射表。
    优先从 schema/plan.json 的 volumes 数组，回退到 plan.md 文本解析。
    """
    schema_path = project_dir / "00_memory" / "schema" / "plan.json"
    volume_map: dict[int, dict] = {}

    # 方案 A：JSON Schema
    if schema_path.exists():
        try:
            plan_data = json.loads(schema_path.read_text(encoding="utf-8"))
            volumes = plan_data.get("volumes", [])
            if isinstance(volumes, list) and volumes:
                for i, vol in enumerate(volumes):
                    if not isinstance(vol, dict):
                        continue
                    vol_name = str(vol.get("name", vol.get("volumeName", f"第{i + 1}卷")))
                    start = vol.get("start", vol.get("startChapter"))
                    end = vol.get("end", vol.get("endChapter"))
                    if isinstance(start, (int, float)) and isinstance(end, (int, float)):
                        start_ch = int(start)
                        end_ch = int(end)
                        for ch in range(start_ch, end_ch + 1):
                            volume_map[ch] = {
                                "volume": vol_name,
                                "start_chapter": start_ch,
                                "end_chapter": end_ch,
                                "stage_goal": str(vol.get("stageGoal", vol.get("stage_goal", ""))),
                                "must_deliver": str(vol.get("mustDeliver", vol.get("must_deliver", ""))),
                                "must_raise": str(vol.get("mustRaise", vol.get("must_raise", ""))),
                            }
                if volume_map:
                    return volume_map
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    # 方案 B：plan.md 文本解析
    _CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    volumes_parsed = _parse_volume_outline_from_plan(plan_text)

    # 从 plan.md 中找章节数线索（如果有卷级章节数信息）
    # plan.md 卷纲通常没有明确的 start/end 章号，需要从 schema/plan.json 补
    # 如果都拿不到，返回空映射
    if not volume_map:
        # 尝试从 volume-blueprint.md 获取更多信息
        blueprint_dir = project_dir / "00_memory" / "volumes"
        if blueprint_dir.exists():
            for md_file in sorted(blueprint_dir.glob("*.md")):
                content = md_file.read_text(encoding="utf-8")
                # 匹配 "章节跨度" 或 "chapterRange"
                range_match = re.search(r"(?:章节跨度|chapterRange)[：:\s]*(\d+)\s*[-–—]\s*(\d+)", content)
                if range_match:
                    start = int(range_match.group(1))
                    end = int(range_match.group(2))
                    vol_name_match = re.search(r"(?:本卷名称|volumeName)[：:\s]*(.+)", content)
                    vol_name = vol_name_match.group(1).strip() if vol_name_match else md_file.stem
                    for ch in range(start, end + 1):
                        volume_map[ch] = {
                            "volume": vol_name,
                            "start_chapter": start,
                            "end_chapter": end,
                            "stage_goal": "",
                            "must_deliver": "",
                            "must_raise": "",
                        }

    return volume_map


def _get_volume_info(volume_map: dict[int, dict], chapter: int) -> dict | None:
    """获取指定章节所在的卷信息。"""
    return volume_map.get(chapter)


def _is_volume_start(volume_map: dict[int, dict], chapter: int) -> bool:
    info = volume_map.get(chapter)
    return info is not None and info["start_chapter"] == chapter


def _is_volume_end(volume_map: dict[int, dict], chapter: int) -> bool:
    info = volume_map.get(chapter)
    return info is not None and info["end_chapter"] == chapter


# ---------------------------------------------------------------------------
# 卷退出检查
# ---------------------------------------------------------------------------

def _check_volume_promises(project_dir: Path, vol_info: dict) -> list[dict]:
    """检查卷级承诺是否兑现。"""
    issues: list[dict] = []
    payoff_path = project_dir / "00_memory" / "payoff-board.md"
    if not payoff_path.exists():
        return issues

    payoff_text = payoff_path.read_text(encoding="utf-8")
    # 查找"当前卷重点盯防"表格
    focus_section = re.search(r"当前卷重点盯防[\s\S]*?(?=##|$)", payoff_text)
    if focus_section:
        # 解析表格中的 status 列
        for line in focus_section.group(0).split("\n"):
            if "|" in line and "未兑现" in line:
                issues.append({
                    "type": "volume_promise_unfulfilled",
                    "severity": "high",
                    "reason": f"卷级承诺未兑现: {line.strip()[:100]}",
                })

    return issues


def _check_volume_foreshadowing(project_dir: Path, vol_info: dict) -> list[dict]:
    """检查本卷活跃伏笔的回收率。"""
    issues: list[dict] = []
    foreshadow_path = project_dir / "00_memory" / "foreshadowing.md"
    if not foreshadow_path.exists():
        return issues

    fs_text = foreshadow_path.read_text(encoding="utf-8")
    start_ch = vol_info.get("start_chapter", 0)
    end_ch = vol_info.get("end_chapter", 0)

    # 解析活跃伏笔表
    total_in_volume = 0
    resolved_in_volume = 0
    overdue_count = 0

    table_lines = re.findall(r"\|.*?\|.*?\|.*?\|.*?\|", fs_text)
    for line in table_lines:
        fields = [f.strip() for f in line.split("|") if f.strip()]
        if len(fields) < 3:
            continue
        # 尝试提取章节号
        for field in fields:
            ch_match = re.search(r"(\d+)", field)
            if ch_match and start_ch <= int(ch_match.group(1)) <= end_ch:
                total_in_volume += 1
                if "已回收" in line or "resolved" in line:
                    resolved_in_volume += 1
                elif "超期" in line or "overdue" in line or "abandoned" in line:
                    overdue_count += 1
                break

    if total_in_volume > 0:
        recovery_rate = resolved_in_volume / total_in_volume
        if recovery_rate < 0.5:
            issues.append({
                "type": "volume_foreshadow_low_recovery",
                "severity": "high",
                "reason": f"本卷伏笔回收率={recovery_rate:.0%}（{resolved_in_volume}/{total_in_volume}），"
                           f"超期 {overdue_count} 条，跨卷烂尾风险高",
            })
        elif recovery_rate < 0.7:
            issues.append({
                "type": "volume_foreshadow_moderate_recovery",
                "severity": "medium",
                "reason": f"本卷伏笔回收率={recovery_rate:.0%}（{resolved_in_volume}/{total_in_volume}），"
                           f"建议在卷末加速回收",
            })

    return issues


def _check_volume_arc_progression(project_dir: Path, vol_info: dict) -> list[dict]:
    """检查本卷角色弧阶段是否到达预期。"""
    issues: list[dict] = []
    arcs_path = project_dir / "00_memory" / "character_arcs.md"
    if not arcs_path.exists():
        return issues

    arcs_text = arcs_path.read_text(encoding="utf-8")
    stalled_keywords = ("停滞", "重复", "倒退", "失真")
    for keyword in stalled_keywords:
        if keyword in arcs_text:
            # 定位上下文
            for line in arcs_text.split("\n"):
                if keyword in line and "|" in line:
                    issues.append({
                        "type": "volume_arc_stalled",
                        "severity": "medium",
                        "reason": f"角色弧出现'{keyword}'信号: {line.strip()[:100]}",
                    })

    return issues


def _check_volume_exit(project_dir: Path, volume_map: dict[int, dict], chapter: int) -> dict:
    """卷退出综合检查。"""
    vol_info = _get_volume_info(volume_map, chapter)
    if not vol_info or not _is_volume_end(volume_map, chapter):
        return {"is_volume_end": False, "issues": [], "verdict": "pass"}

    issues: list[dict] = []
    issues.extend(_check_volume_promises(project_dir, vol_info))
    issues.extend(_check_volume_foreshadowing(project_dir, vol_info))
    issues.extend(_check_volume_arc_progression(project_dir, vol_info))

    # 检查 volume-blueprint 核心任务是否在章卡中有对应
    blueprint_dir = project_dir / "00_memory" / "volumes"
    if blueprint_dir.exists():
        for md_file in sorted(blueprint_dir.glob("*.md")):
            bp_text = md_file.read_text(encoding="utf-8")
            core_task = re.search(r"(?:卷核心任务|coreTask)[\s\S]*?(?=##|\Z)", bp_text)
            if core_task:
                task_content = core_task.group(0)
                # 检查是否有主角诉求 + 核心阻碍都写了
                has_protag_goal = bool(re.search(r"主角.*?(?:诉求|想做|目标)", task_content))
                has_obstacle = bool(re.search(r"(?:阻碍|妨碍|反派|BOSS)", task_content))
                if not has_protag_goal or not has_obstacle:
                    issues.append({
                        "type": "volume_blueprint_incomplete",
                        "severity": "medium",
                        "reason": f"卷蓝图 {md_file.name} 核心任务未完整填写（缺{'主角诉求' if not has_protag_goal else '核心阻碍'}）",
                    })

    high_count = sum(1 for i in issues if i["severity"] == "high")
    verdict = "fail" if high_count >= 1 else ("warn" if issues else "pass")

    return {
        "is_volume_end": True,
        "volume": vol_info["volume"],
        "start_chapter": vol_info["start_chapter"],
        "end_chapter": vol_info["end_chapter"],
        "issues": issues,
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# 卷进入初始化
# ---------------------------------------------------------------------------

def _check_volume_entry(project_dir: Path, volume_map: dict[int, dict], chapter: int) -> dict:
    """卷进入检查。"""
    vol_info = _get_volume_info(volume_map, chapter)
    if not vol_info or not _is_volume_start(volume_map, chapter):
        return {"is_volume_start": False, "issues": [], "verdict": "pass"}

    issues: list[dict] = []

    # 检查上一卷的跨卷记忆交接
    start_ch = vol_info["start_chapter"]
    prev_vol = None
    for ch, info in volume_map.items():
        if info["end_chapter"] == start_ch - 1:
            prev_vol = info
            break

    state_path = project_dir / "00_memory" / "state.md"
    state_text = ""
    if state_path.exists():
        state_text = state_path.read_text(encoding="utf-8")

    # 1. 检查 state.md 是否更新了当前卷
    current_vol_in_state = re.search(r"当前卷[：:]\s*(.+)", state_text)
    if current_vol_in_state:
        state_vol = current_vol_in_state.group(1).strip()
        if state_vol != vol_info["volume"]:
            issues.append({
                "type": "volume_state_not_updated",
                "severity": "high",
                "reason": f"state.md 当前卷为'{state_vol}'，但已进入'{vol_info['volume']}'",
            })

    # 2. 检查 volume-blueprint 是否存在
    blueprint_dir = project_dir / "00_memory" / "volumes"
    if not blueprint_dir.exists() or not list(blueprint_dir.glob("*.md")):
        issues.append({
            "type": "volume_blueprint_missing",
            "severity": "medium",
            "reason": f"未找到卷蓝图文件。建议在 00_memory/volumes/ 下创建新卷的卷纲",
        })

    # 3. 生成跨卷记忆交接提示
    handoff_hint = ""
    if prev_vol:
        prev_blueprint = project_dir / "00_memory" / "volumes" / f"{prev_vol['volume']}.md"
        if prev_blueprint.exists():
            bp_text = prev_blueprint.read_text(encoding="utf-8")
            handoff_match = re.search(r"跨卷记忆交接[\s\S]*?(?=##|\Z)", bp_text)
            if handoff_match:
                handoff_hint = handoff_match.group(0).strip()

    verdict = "fail" if any(i["severity"] == "high" for i in issues) else ("warn" if issues else "pass")

    return {
        "is_volume_start": True,
        "volume": vol_info["volume"],
        "start_chapter": vol_info["start_chapter"],
        "issues": issues,
        "verdict": verdict,
        "handoff_hint": handoff_hint,
    }


# ---------------------------------------------------------------------------
# 卷级健康报告
# ---------------------------------------------------------------------------

def _generate_volume_health_report(project_dir: Path, volume_map: dict[int, dict]) -> dict:
    """生成按卷分段的聚合健康报告。"""
    # 收集已有的质检报告
    aggregation_path = project_dir / "05_reports"
    reports: dict[str, dict] = {}

    # 按卷分组统计
    vol_stats: dict[str, dict] = {}
    for ch, vol_info in sorted(volume_map.items()):
        vol_name = vol_info["volume"]
        if vol_name not in vol_stats:
            vol_stats[vol_name] = {
                "volume": vol_name,
                "chapter_range": [vol_info["start_chapter"], vol_info["end_chapter"]],
                "chapter_count": 0,
                "blocking_count": 0,
                "warning_count": 0,
                "issues": [],
            }
        vol_stats[vol_name]["chapter_count"] += 1

    # 汇总各卷章节数 → 构造输出
    summary = {
        "total_volumes": len(vol_stats),
        "volumes": list(vol_stats.values()),
        "volume_map_key": {
            str(ch): info["volume"]
            for ch, info in sorted(volume_map.items())
        },
    }

    return summary


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------

def analyze_volume(
    project_dir: Path,
    chapter: int,
    *,
    plan_text: str | None = None,
    silence: bool = False,
) -> dict:
    """
    卷级质量审计。

    Returns:
        {
            "verdict": "pass"|"warn"|"fail",
            "volume_map": {chapter: volume_info},
            "current_volume": dict,
            "exit_check": dict,
            "entry_check": dict,
            "health_report": dict,
            "issues": [...],
        }
    """
    if plan_text is None:
        plan_path = project_dir / "00_memory" / "plan.md"
        plan_text = plan_path.read_text(encoding="utf-8") if plan_path.exists() else ""

    volume_map = _build_volume_map(project_dir, plan_text)
    vol_info = _get_volume_info(volume_map, chapter)

    all_issues: list[dict] = []
    exit_result = _check_volume_exit(project_dir, volume_map, chapter)
    entry_result = _check_volume_entry(project_dir, volume_map, chapter)
    health_report = _generate_volume_health_report(project_dir, volume_map)

    all_issues.extend(exit_result.get("issues", []))
    all_issues.extend(entry_result.get("issues", []))

    # 综合裁决
    if exit_result["verdict"] == "fail" or entry_result["verdict"] == "fail":
        verdict = "fail"
    elif exit_result["verdict"] == "warn" or entry_result["verdict"] == "warn":
        verdict = "warn"
    else:
        verdict = "pass"

    result = {
        "verdict": verdict,
        "chapter": chapter,
        "volume_map": {
            str(k): v for k, v in volume_map.items()
        } if volume_map else {},
        "current_volume": vol_info,
        "is_volume_start": entry_result.get("is_volume_start", False),
        "is_volume_end": exit_result.get("is_volume_end", False),
        "exit_check": exit_result,
        "entry_check": entry_result,
        "health_report": health_report,
        "issues": all_issues,
        "issue_count": len(all_issues),
    }

    if not silence:
        vol_name = vol_info["volume"] if vol_info else "未知卷"
        print(f"卷级质量门禁 — 第 {chapter} 章 ({vol_name}) → {verdict}")
        if exit_result.get("is_volume_end"):
            print(f"  ⚠ 卷末检查: {exit_result['verdict']} ({len(exit_result.get('issues', []))} 个问题)")
        if entry_result.get("is_volume_start"):
            print(f"  ⚠ 卷首检查: {entry_result['verdict']} ({len(entry_result.get('issues', []))} 个问题)")
            if entry_result.get("handoff_hint"):
                print(f"  📋 跨卷交接提示:\n{entry_result['handoff_hint'][:200]}")
        for issue in all_issues:
            print(f"  [{issue['severity']}] {issue['reason'][:120]}")

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="卷级质量门禁 — 跨卷连续性检测")
    parser.add_argument("--project", type=str, required=True, help="项目根目录")
    parser.add_argument("--chapter", type=int, required=True, help="章节号")
    parser.add_argument("--plan-text", type=str, default=None, help="直接传入 plan.md 内容")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    project_dir = Path(args.project).resolve()
    if not project_dir.exists():
        print(f"项目目录不存在: {project_dir}")
        return

    result = analyze_volume(
        project_dir,
        args.chapter,
        plan_text=args.plan_text,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
