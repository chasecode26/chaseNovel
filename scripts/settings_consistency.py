"""
设定一致性自动校验 — 检测世界设定、力量体系、地点、人物关系、资源、术语的一致性。

独立 CLI 使用：
    python scripts/settings_consistency.py --project <dir> [--all] [--from-chapter N --to-chapter M]
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _char_count(text: str) -> int:
    return sum(1 for c in text if "\u4e00" <= c <= "\u9fff")


def _read_chapter_text(project_dir: Path, chapter: int) -> str:
    """读取章节正文。"""
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


def _read_chapter_cards(project_dir: Path) -> dict[int, dict]:
    """读取所有章卡信息。"""
    cards: dict[int, dict] = {}
    cards_dir = project_dir / "03_chapter_cards"
    if not cards_dir.exists():
        return cards
    for card_file in sorted(cards_dir.glob("ch*.md")):
        ch_match = re.search(r"ch(\d+)", card_file.name)
        if ch_match:
            ch_no = int(ch_match.group(1))
            cards[ch_no] = {"path": card_file, "text": card_file.read_text(encoding="utf-8")}
    return cards


def _find_chapters(project_dir: Path) -> list[int]:
    """扫描项目中所有已写章节号。"""
    chapters: set[int] = set()
    for base_dir in ["02_chapters", "02_first_draft"]:
        dir_path = project_dir / base_dir
        if dir_path.exists():
            for f in dir_path.glob("ch*.md"):
                m = re.search(r"ch(\d+)", f.name)
                if m:
                    chapters.add(int(m.group(1)))
    return sorted(chapters)


# ---------------------------------------------------------------------------
# 检测维度
# ---------------------------------------------------------------------------

def _check_power_progression(
    chapter_texts: dict[int, str], power_milestones: list[dict] | None = None
) -> list[dict]:
    """力量体系阶梯检测 — 是否越级升级。"""
    issues: list[dict] = []

    if not power_milestones:
        # 从文本中自动提取力量等级关键词
        power_levels = [
            ("练气", 1), ("筑基", 2), ("金丹", 3), ("元婴", 4),
            ("化神", 5), ("炼虚", 6), ("合体", 7), ("大乘", 8), ("渡劫", 9),
            ("一阶", 1), ("二阶", 2), ("三阶", 3), ("四阶", 4), ("五阶", 5),
            ("六阶", 6), ("七阶", 7), ("八阶", 8), ("九阶", 9),
            ("一品", 1), ("二品", 2), ("三品", 3), ("四品", 4), ("五品", 5),
            ("一级", 1), ("二级", 2), ("三级", 3), ("四级", 4), ("五级", 5),
            ("第一层", 1), ("第二层", 2), ("第三层", 3), ("第四层", 4),
        ]
        detected_levels: dict[int, int] = {}  # chapter → max_level
        current_max = 0

        for ch_no in sorted(chapter_texts.keys()):
            text = chapter_texts[ch_no]
            chapter_max = 0
            for term, level in power_levels:
                if term in text:
                    chapter_max = max(chapter_max, level)
            if chapter_max > 0:
                detected_levels[ch_no] = chapter_max
                # 跳级检测
                if chapter_max > current_max + 1:
                    issues.append({
                        "type": "power_level_skip",
                        "severity": "medium",
                        "reason": f"第 {ch_no} 章出现力量等级 {chapter_max}，"
                                   f"上一最高等级为 {current_max}，存在跳级风险",
                    })
                current_max = max(current_max, chapter_max)

    return issues


def _check_location_continuity(project_dir: Path, chapter_texts: dict[int, str]) -> list[dict]:
    """地点连续性检测。"""
    issues: list[dict] = []
    state_path = project_dir / "00_memory" / "state.md"
    if not state_path.exists():
        return issues

    state_text = state_path.read_text(encoding="utf-8")

    # 提取"空间与位置"部分
    location_section = re.search(r"空间与位置[\s\S]*?(?=##|\Z)", state_text)
    if not location_section:
        return issues

    # 提取地点信息
    location_entries = re.findall(
        r"[-*]\s*(.+?)[：:]\s*([\u4e00-\u9fff\w]+)",
        location_section.group(0),
    )

    places_seen: set[str] = set()
    for entity, place in location_entries:
        if entity in places_seen:
            issues.append({
                "type": "duplicate_entity_location",
                "severity": "medium",
                "reason": f"'{entity}' 的位置声明了多次，可能冲突",
            })
        places_seen.add(entity)

    return issues


def _check_relationship_consistency(
    project_dir: Path, chapter_cards: dict[int, dict]
) -> list[dict]:
    """人物关系变化一致性 — 检测无记录的关系突变。"""
    issues: list[dict] = []
    chars_path = project_dir / "00_memory" / "characters.md"
    if not chars_path.exists():
        return issues

    chars_text = chars_path.read_text(encoding="utf-8")
    # 提取关系变化标记
    relation_changes = re.findall(
        r"(?:关系|relation).*?(?:升|降|变|转变|冲突|破裂|合作|联盟|信任|不信任)",
        chars_text, re.IGNORECASE,
    )

    # 跟踪关系变化 → 检查章卡是否有对应记录
    ch_card_texts = " ".join(c.get("text", "") for c in chapter_cards.values())
    for change in relation_changes:
        # 简单检查：关系变化关键词是否在章卡中出现
        if change[:10] not in ch_card_texts:
            issues.append({
                "type": "relationship_change_untracked",
                "severity": "medium",
                "reason": f"人物关系变化'{change[:50]}'在章卡中无对应记录",
            })

    return issues


def _check_term_consistency(chapter_texts: dict[int, str]) -> list[dict]:
    """设定术语一致性 — 同词不同义检测。"""
    issues: list[dict] = []

    # 提取所有专有名词（连续 2-4 字的大写或特殊词）
    term_pattern = re.compile(r"[「【](.+?)[」】]")
    terms: dict[str, dict[int, str]] = defaultdict(dict)

    for ch_no, text in sorted(chapter_texts.items()):
        for m in term_pattern.finditer(text):
            term = m.group(1).strip()
            # 取术语出现的上下文
            start = max(0, m.start() - 20)
            end = min(len(text), m.end() + 40)
            context = text[start:end].replace("\n", " ")
            if ch_no not in terms[term]:
                terms[term][ch_no] = context

    # 检测定义漂移
    for term, occurrences in terms.items():
        if len(occurrences) < 2:
            continue
        # 简单检查：取首尾章的上下文，比较关键词
        chapters_sorted = sorted(occurrences.keys())
        first_context = occurrences[chapters_sorted[0]]
        last_context = occurrences[chapters_sorted[-1]]

        # 提取定义性描述（"是/即/指" 后的内容）
        first_def = re.search(rf"{re.escape(term)}[是为即指](.+?)[，。]", first_context)
        last_def = re.search(rf"{re.escape(term)}[是为即指](.+?)[，。]", last_context)

        if first_def and last_def:
            f_def = first_def.group(1).strip()
            l_def = last_def.group(1).strip()
            if f_def != l_def and len(f_def) > 2 and len(l_def) > 2:
                issues.append({
                    "type": "term_definition_drift",
                    "severity": "medium",
                    "reason": f"术语'{term}'的定义漂移: "
                               f"第{chapters_sorted[0]}章→'{f_def}'，"
                               f"第{chapters_sorted[-1]}章→'{l_def}'",
                })

    return issues


# ---------------------------------------------------------------------------
# 主审计函数
# ---------------------------------------------------------------------------

def analyze_settings(
    project_dir: Path,
    *,
    from_chapter: int | None = None,
    to_chapter: int | None = None,
    all_chapters: bool = False,
    silence: bool = False,
) -> dict:
    """
    设定一致性审计。

    Args:
        project_dir: 项目根目录
        from_chapter: 起始章节（含）
        to_chapter: 结束章节（含）
        all_chapters: 是否扫描全部章节
        silence: 是否抑制输出

    Returns:
        { "verdict": "pass"|"warn"|"rewrite", "issues": [...], "scores": {...} }
    """
    all_issues: list[dict] = []

    if all_chapters:
        chapters = _find_chapters(project_dir)
    elif from_chapter and to_chapter:
        chapters = list(range(from_chapter, to_chapter + 1))
    else:
        chapters = _find_chapters(project_dir)

    chapter_texts = {ch: _read_chapter_text(project_dir, ch) for ch in chapters}
    chapter_texts = {k: v for k, v in chapter_texts.items() if v}  # 去空
    chapter_cards = _read_chapter_cards(project_dir)

    # 逐维度检测
    all_issues.extend(_check_power_progression(chapter_texts))
    all_issues.extend(_check_location_continuity(project_dir, chapter_texts))
    all_issues.extend(_check_relationship_consistency(project_dir, chapter_cards))
    all_issues.extend(_check_term_consistency(chapter_texts))

    # 综合裁决
    high_count = sum(1 for i in all_issues if i["severity"] == "high")
    medium_count = len(all_issues) - high_count

    if high_count >= 1:
        verdict = "rewrite"
    elif medium_count >= 3:
        verdict = "warn"
    else:
        verdict = "pass"

    result = {
        "verdict": verdict,
        "chapters_scanned": len(chapter_texts),
        "chapter_range": [min(chapters) if chapters else 0, max(chapters) if chapters else 0],
        "issues": all_issues,
        "issue_count": len(all_issues),
        "high_issue_count": high_count,
        "scores": {
            "power_progression": max(0, 100 - sum(1 for i in all_issues if i["type"] == "power_level_skip") * 30),
            "location_continuity": max(0, 100 - sum(1 for i in all_issues if "location" in i["type"]) * 20),
            "term_consistency": max(0, 100 - sum(1 for i in all_issues if "term" in i["type"]) * 20),
        },
    }

    if not silence:
        print(f"设定一致性审计 — 扫描 {len(chapter_texts)} 章 (ch{min(chapters) if chapters else 0}-ch{max(chapters) if chapters else 0}) → {verdict}")
        for issue in all_issues:
            print(f"  [{issue['severity']}] {issue['reason'][:120]}")

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="设定一致性自动校验")
    parser.add_argument("--project", type=str, required=True, help="项目根目录")
    parser.add_argument("--from-chapter", type=int, default=None, help="起始章节")
    parser.add_argument("--to-chapter", type=int, default=None, help="结束章节")
    parser.add_argument("--all", dest="all_chapters", action="store_true",
                        help="扫描全部章节")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    project_dir = Path(args.project).resolve()
    if not project_dir.exists():
        print(f"项目目录不存在: {project_dir}")
        return

    result = analyze_settings(
        project_dir,
        from_chapter=args.from_chapter,
        to_chapter=args.to_chapter,
        all_chapters=args.all_chapters,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
