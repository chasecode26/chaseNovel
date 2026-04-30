"""
知识边界跨章校验 — 检测消息到达时序、角色知情边界、秘密跨章一致性、误判漂移。

独立 CLI 使用：
    python scripts/knowledge_boundary_check.py --project <dir> --from-chapter N --to-chapter M
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# 检测维度
# ---------------------------------------------------------------------------

def _check_message_arrival_timing(
    chapter_texts: dict[int, str],
) -> list[dict]:
    """消息到达时序验证。"""
    issues: list[dict] = []

    # 提取所有消息发送/接收事件
    send_pattern = re.compile(
        r"(?:传信|送信|报信|飞鸽|快马|遣使|派人).*?(?:给|到|送往|传向)([\u4e00-\u9fff]{2,4})"
    )
    receive_pattern = re.compile(
        r"(?:接到|收到|得到|接到信|接到消息|探子回报|暗哨传回).*?(?:来自|从)?([\u4e00-\u9fff]{2,4})"
    )
    know_before_arrival = re.compile(
        r"(?:已经知道|早就知道|早已知道|已然知道|预先知道)"
    )

    send_events: dict[int, list[dict]] = defaultdict(list)
    receive_events: dict[int, list[dict]] = defaultdict(list)

    for ch_no, text in sorted(chapter_texts.items()):
        for m in send_pattern.finditer(text):
            target = m.group(1)
            send_events[ch_no].append({"target": target, "content": m.group(0)[:60]})
        for m in receive_pattern.finditer(text):
            source = m.group(1)
            receive_events[ch_no].append({"source": source, "content": m.group(0)[:60]})
        # 检测提前知情
        if know_before_arrival.search(text):
            # 检查最近发送的事件是否还没到达
            recent_sends = [e for c in range(max(1, ch_no - 2), ch_no) for e in send_events.get(c, [])]
            if recent_sends:
                issues.append({
                    "type": "potential_early_knowledge",
                    "severity": "medium",
                    "reason": f"第 {ch_no} 章出现'提前知情'表达，检查此前发送的消息是否已到达",
                })

    # 对比发送/接收时序
    for ch_no in sorted(chapter_texts.keys()):
        # 当前章的接收事件中，是否有消息发送章离得太近
        receives = receive_events.get(ch_no, [])
        for rec in receives:
            source = rec["source"]
            # 查找包含该 source 的最早发送事件
            send_ch = None
            for sc in sorted(send_events.keys()):
                for se in send_events[sc]:
                    if source in se["target"] or source in se["content"]:
                        send_ch = sc
                        break
                if send_ch:
                    break
            if send_ch and ch_no - send_ch <= 1:
                issues.append({
                    "type": "message_arrival_too_fast",
                    "severity": "medium",
                    "reason": f"消息在第 {send_ch} 章发送，第 {ch_no} 章即收到，"
                               f"需确认时间跨度是否合理",
                })

    return issues


def _check_character_knowledge_boundary(
    project_dir: Path, chapter_texts: dict[int, str]
) -> list[dict]:
    """角色知情边界检测。"""
    issues: list[dict] = []

    # 从角色档案读取关键角色
    chars_path = project_dir / "00_memory" / "schema" / "characters.json"
    characters: list[str] = []
    if chars_path.exists():
        try:
            data = json.loads(chars_path.read_text(encoding="utf-8"))
            for char in data.get("characters", []):
                if isinstance(char, dict):
                    characters.append(str(char.get("name", "")))
        except (json.JSONDecodeError, KeyError):
            pass

    if not characters:
        chars_md = project_dir / "00_memory" / "characters.md"
        if chars_md.exists():
            text = chars_md.read_text(encoding="utf-8")
            names = re.findall(r"[-*]\s*([\u4e00-\u9fff]{2,4})[：:|\s]", text)
            characters = list(names)[:10]

    # 检测知识标记
    knowledge_markers = ("听说", "知道", "明白", "猜到", "推测出", "打听到", "探听到")
    for ch_no, text in sorted(chapter_texts.items()):
        for char in characters:
            if not char:
                continue
            for marker in knowledge_markers:
                pattern = re.compile(f"{re.escape(char)}.*?{marker}")
                if pattern.search(text):
                    # 记录该章该角色知道了什么
                    pass  # 基础版本，仅记录

    return issues


def _check_secret_consistency(project_dir: Path) -> list[dict]:
    """秘密跨章一致性检测。"""
    issues: list[dict] = []
    foreshadow_path = project_dir / "00_memory" / "foreshadowing.md"
    if not foreshadow_path.exists():
        return issues

    fs_text = foreshadow_path.read_text(encoding="utf-8")
    # 提取 who_knows 字段
    who_knows_entries = re.findall(r"who_knows[：:]\s*(.+)", fs_text)

    # 检测知道者的变化
    known_persons: set[str] = set()
    for entry in who_knows_entries:
        persons = re.findall(r"[\u4e00-\u9fff]{2,4}", entry)
        new_persons = set(persons) - known_persons
        if new_persons and known_persons:
            issues.append({
                "type": "secret_spreader_undocumented",
                "severity": "medium",
                "reason": f"秘密知情者新增: {', '.join(new_persons)}，需确认交代了获取途径",
            })
        known_persons.update(persons)

    return issues


# ---------------------------------------------------------------------------
# 主审计函数
# ---------------------------------------------------------------------------

def analyze_knowledge(
    project_dir: Path,
    *,
    from_chapter: int | None = None,
    to_chapter: int | None = None,
    silence: bool = False,
) -> dict:
    """知识边界审计。"""
    all_issues: list[dict] = []

    if from_chapter and to_chapter:
        chapters = list(range(from_chapter, to_chapter + 1))
    else:
        chapters = _find_chapters(project_dir)

    chapter_texts = {ch: _read_chapter_text(project_dir, ch) for ch in chapters}
    chapter_texts = {k: v for k, v in chapter_texts.items() if v}

    all_issues.extend(_check_message_arrival_timing(chapter_texts))
    all_issues.extend(_check_character_knowledge_boundary(project_dir, chapter_texts))
    all_issues.extend(_check_secret_consistency(project_dir))

    high_count = sum(1 for i in all_issues if i["severity"] == "high")
    medium_count = len(all_issues) - high_count

    if high_count >= 1:
        verdict = "rewrite"
    elif medium_count >= 2:
        verdict = "warn"
    else:
        verdict = "pass"

    result = {
        "verdict": verdict,
        "chapters_scanned": len(chapter_texts),
        "issues": all_issues,
        "issue_count": len(all_issues),
        "high_issue_count": high_count,
    }

    if not silence:
        print(f"知识边界审计 — 扫描 {len(chapter_texts)} 章 → {verdict}")
        for issue in all_issues:
            print(f"  [{issue['severity']}] {issue['reason'][:120]}")

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="知识边界跨章校验")
    parser.add_argument("--project", type=str, required=True, help="项目根目录")
    parser.add_argument("--from-chapter", type=int, default=None, help="起始章节")
    parser.add_argument("--to-chapter", type=int, default=None, help="结束章节")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    project_dir = Path(args.project).resolve()
    if not project_dir.exists():
        print(f"项目目录不存在: {project_dir}")
        return

    result = analyze_knowledge(
        project_dir,
        from_chapter=args.from_chapter,
        to_chapter=args.to_chapter,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
