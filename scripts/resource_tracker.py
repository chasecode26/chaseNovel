"""
跨章资源追踪 — 检测兵力/物资/财物/伤势/战力/道具的无因变化。

独立 CLI 使用：
    python scripts/resource_tracker.py --project <dir> --from-chapter N --to-chapter M
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# 资源关键词定义
# ---------------------------------------------------------------------------

# 兵力/人员
TROOP_KEYWORDS = (
    ("人", "个", "名"),
    ("兵", "个", "名"),
    ("哨骑", "骑", "人"),
    ("游骑", "骑", "人"),
    ("亲兵", "个", "名"),
    ("卫队", "支", "队"),
    ("队伍", "支", "队"),
    ("人马", "队", "批"),
)

# 物资/粮草
SUPPLY_KEYWORDS = (
    ("粮", "石", "车"),
    ("粮草", "车", "批"),
    ("箭", "支", "捆"),
    ("刀", "把", "柄"),
    ("甲", "副", "套"),
    ("马", "匹", "骑"),
    ("药", "副", "包"),
    ("金疮药", "瓶", "副"),
    ("银子", "两", "锭"),
    ("黄金", "两", "锭"),
    ("铜钱", "文", "贯"),
)

# 伤势/状态
INJURY_KEYWORDS = (
    "受伤", "重伤", "轻伤", "伤口", "骨折", "中毒",
    "失血", "昏迷", "卧床", "养伤", "痊愈", "包扎",
)

# 战力/消耗
POWER_KEYWORDS = (
    "灵气", "灵力", "真气", "魔力", "魂力", "精神力",
    "消耗", "耗尽", "恢复", "补充",
)

# 关键道具
ITEM_MARKERS = (
    "令牌", "玉佩", "钥匙", "地图", "丹", "剑", "刀",
    "符", "印", "卷轴", "戒指", "手镯",
)


def _read_chapter_text(project_dir: Path, chapter: int) -> str:
    candidates = [
        project_dir / "02_chapters" / f"ch{chapter:03d}.md",
        project_dir / "02_first_draft" / f"ch{chapter:03d}.md",
        project_dir / "02_first_draft" / f"ch{chapter}.md",
    ]
    draft_dir = project_dir / "02_first_draft"
    if draft_dir.exists():
        for f in draft_dir.glob(f"ch{chapter:03d}*.md"):
            candidates.append(f)
    for c in candidates:
        if c.exists():
            return c.read_text(encoding="utf-8")
    return ""


def _find_chapters(project_dir: Path) -> list[int]:
    chapters: set[int] = set()
    for base_dir in ["02_chapters", "02_first_draft"]:
        dir_path = project_dir / base_dir
        if dir_path.exists():
            for f in dir_path.glob("ch*.md"):
                m = re.search(r"ch(\d+)", f.name)
                if m:
                    chapters.add(int(m.group(1)))
    return sorted(chapters)


def _extract_numbers(text: str) -> list[tuple[int, str]]:
    """提取文本中的数字 + 上下文。"""
    results: list[tuple[int, str]] = []
    pattern = re.compile(r"(\d+)\s*([\u4e00-\u9fff]{1,3})")
    for m in pattern.finditer(text):
        num = int(m.group(1))
        unit = m.group(2)
        # 过滤无关数字（年份、章节号等）
        if unit in ("年", "月", "日", "章", "节", "页", "行", "岁", "点", "分", "秒"):
            continue
        # 取周围上下文
        start = max(0, m.start() - 15)
        end = min(len(text), m.end() + 15)
        context = text[start:end].replace("\n", " ")
        results.append((num, context))
    return results


def _extract_injuries(text: str) -> list[str]:
    """提取伤势状态。"""
    found: list[str] = []
    sentences = re.split(r"[。！？]", text)
    for s in sentences:
        for kw in INJURY_KEYWORDS:
            if kw in s:
                found.append(s.strip()[:80])
                break
    return found


def _extract_items(text: str) -> list[str]:
    """提取关键道具提及。"""
    found: list[str] = []
    for item in ITEM_MARKERS:
        if item in text and len(item) >= 2:
            idx = text.find(item)
            start = max(0, idx - 10)
            end = min(len(text), idx + len(item) + 10)
            found.append(text[start:end].replace("\n", " "))
    return found


# ---------------------------------------------------------------------------
# 检测
# ---------------------------------------------------------------------------

def _check_troop_continuity(chapter_texts: dict[int, str]) -> list[dict]:
    """兵力连续性检测。"""
    issues: list[dict] = []
    troop_history: dict[str, list[tuple[int, int]]] = defaultdict(list)

    for ch_no, text in sorted(chapter_texts.items()):
        numbers = _extract_numbers(text)
        for num, context in numbers:
            # 匹配兵力相关
            for troop_word, unit1, unit2 in TROOP_KEYWORDS:
                if troop_word in context:
                    key = troop_word
                    troop_history[key].append((ch_no, num))

    # 检测大幅变化
    for key, history in troop_history.items():
        if len(history) < 2:
            continue
        for i in range(1, len(history)):
            prev_ch, prev_num = history[i - 1]
            curr_ch, curr_num = history[i]
            if prev_num > 0 and curr_num > 0:
                ratio = curr_num / prev_num
                if ratio > 2.0:  # 翻倍
                    issues.append({
                        "type": "troop_explosive_growth",
                        "severity": "medium",
                        "reason": f"'{key}'数量在第{prev_ch}章→第{curr_ch}章"
                                   f"从 {prev_num} 增到 {curr_num}（x{ratio:.1f}），需确认原因",
                    })
                elif ratio < 0.3 and prev_num > 10:  # 骤减
                    issues.append({
                        "type": "troop_sharp_decline",
                        "severity": "medium",
                        "reason": f"'{key}'数量在第{prev_ch}章→第{curr_ch}章"
                                   f"从 {prev_num} 降到 {curr_num}（x{ratio:.1f}），需确认伤亡交代",
                    })

    return issues


def _check_supply_continuity(chapter_texts: dict[int, str]) -> list[dict]:
    """物资连续性检测。"""
    issues: list[dict] = []
    supply_history: dict[str, list[tuple[int, int]]] = defaultdict(list)

    for ch_no, text in sorted(chapter_texts.items()):
        numbers = _extract_numbers(text)
        for num, context in numbers:
            for supply_word, unit1, unit2 in SUPPLY_KEYWORDS:
                if supply_word in context and len(supply_word) >= 2:
                    key = supply_word
                    prev_count = supply_history[key][-1][1] if supply_history[key] else None
                    supply_history[key].append((ch_no, num))

                    if prev_count is not None and prev_count > 0 and num > 0:
                        ratio = num / prev_count
                        if ratio > 3.0 and num > 10:
                            issues.append({
                                "type": "supply_unexplained_increase",
                                "severity": "medium",
                                "reason": f"'{key}'在第{prev_count}→{num}章大幅增加（x{ratio:.1f}），"
                                           f"需确认补充来源",
                            })

    return issues


def _check_injury_progression(chapter_texts: dict[int, str]) -> list[dict]:
    """伤势进展检测。"""
    issues: list[dict] = []
    last_injury_state: dict[int, str] = {}

    for ch_no, text in sorted(chapter_texts.items()):
        injuries = _extract_injuries(text)
        injury_text = " | ".join(injuries)

        if ch_no - 1 in last_injury_state:
            prev = last_injury_state[ch_no - 1]
            # 检测：上章重伤 → 本章无伤交代
            if ("重伤" in prev or "受伤" in prev or "昏迷" in prev) and "重伤" not in injury_text and "受伤" not in injury_text:
                if "痊愈" not in injury_text and "恢复" not in injury_text and "养伤" not in injury_text:
                    issues.append({
                        "type": "injury_disappeared_without_explanation",
                        "severity": "medium",
                        "reason": f"第{ch_no - 1}章有伤势提及（'{prev[:50]}...'），"
                                   f"第{ch_no}章未交代恢复过程",
                    })

        last_injury_state[ch_no] = injury_text

    return issues


def _check_item_continuity(chapter_texts: dict[int, str]) -> list[dict]:
    """关键道具连续性检测。"""
    issues: list[dict] = []
    item_mentions: dict[str, list[int]] = defaultdict(list)

    for ch_no, text in sorted(chapter_texts.items()):
        items = _extract_items(text)
        for item in items:
            # 提取道具名（2-4字）
            name_match = re.search(r"[\u4e00-\u9fff]{2,4}(?:令|佩|匙|图|丹|剑|刀|符|印|轴|指|镯)", item)
            if name_match:
                item_name = name_match.group(0)
                item_mentions[item_name].append(ch_no)

    # 检测道具长时间未提及
    for item_name, chapters in item_mentions.items():
        if len(chapters) >= 2:
            gap = chapters[-1] - chapters[-2]
            if gap > 10:
                issues.append({
                    "type": "item_long_forgotten",
                    "severity": "low",
                    "reason": f"道具'{item_name}'上次在第{chapters[-2]}章出现，"
                               f"隔 {gap} 章后再提，读者可能已忘记",
                })

    return issues


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------

def analyze_resources(
    project_dir: Path,
    *,
    from_chapter: int | None = None,
    to_chapter: int | None = None,
    silence: bool = False,
) -> dict:
    """资源跨章追踪审计。"""
    all_issues: list[dict] = []

    if from_chapter and to_chapter:
        chapters = list(range(from_chapter, to_chapter + 1))
    else:
        chapters = _find_chapters(project_dir)

    chapter_texts = {ch: _read_chapter_text(project_dir, ch) for ch in chapters}
    chapter_texts = {k: v for k, v in chapter_texts.items() if v}

    all_issues.extend(_check_troop_continuity(chapter_texts))
    all_issues.extend(_check_supply_continuity(chapter_texts))
    all_issues.extend(_check_injury_progression(chapter_texts))
    all_issues.extend(_check_item_continuity(chapter_texts))

    high_count = sum(1 for i in all_issues if i["severity"] == "high")
    medium_count = sum(1 for i in all_issues if i["severity"] == "medium")
    low_count = sum(1 for i in all_issues if i["severity"] == "low")

    if high_count >= 1:
        verdict = "rewrite"
    elif medium_count >= 3:
        verdict = "warn"
    else:
        verdict = "pass"

    result = {
        "verdict": verdict,
        "chapters_scanned": len(chapter_texts),
        "issues": all_issues,
        "issue_count": len(all_issues),
        "high_issue_count": high_count,
        "medium_issue_count": medium_count,
        "low_issue_count": low_count,
        "scores": {
            "troop_continuity": max(0, 100 - sum(1 for i in all_issues if "troop" in i["type"]) * 25),
            "supply_continuity": max(0, 100 - sum(1 for i in all_issues if "supply" in i["type"]) * 25),
            "injury_tracking": max(0, 100 - sum(1 for i in all_issues if "injury" in i["type"]) * 20),
        },
    }

    if not silence:
        print(f"资源追踪审计 — 扫描 {len(chapter_texts)} 章 → {verdict}")
        for issue in all_issues:
            print(f"  [{issue['severity']}] {issue['reason'][:120]}")

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="跨章资源状态追踪")
    parser.add_argument("--project", type=str, required=True, help="项目根目录")
    parser.add_argument("--from-chapter", type=int, default=None, help="起始章节")
    parser.add_argument("--to-chapter", type=int, default=None, help="结束章节")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    project_dir = Path(args.project).resolve()
    if not project_dir.exists():
        print(f"项目目录不存在: {project_dir}")
        return

    result = analyze_resources(
        project_dir,
        from_chapter=args.from_chapter,
        to_chapter=args.to_chapter,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
