from __future__ import annotations

import re
from pathlib import Path

from evaluators.contracts import build_verdict


ABSTRACT_MARKERS = (
    "意识到",
    "明白",
    "懂得",
    "真正的问题",
    "本质上",
    "这意味着",
    "换句话说",
    "归根结底",
    "关键在于",
    "他知道",
    "她知道",
    "终于知道",
    "终于明白",
    "不得不承认",
)

ACTION_MARKERS = (
    "走",
    "看",
    "抬",
    "低",
    "按",
    "握",
    "攥",
    "推",
    "拽",
    "退",
    "停",
    "站",
    "坐",
    "扔",
    "砸",
    "递",
    "咬",
    "盯",
    "敲",
    "摁",
    "撞",
    "躲",
    "抽",
    "扶",
    "扣",
)

BODY_MARKERS = (
    "手",
    "眼",
    "脚",
    "肩",
    "背",
    "喉",
    "牙",
    "指",
    "腕",
    "脸",
    "唇",
    "膝",
    "呼吸",
    "心口",
)

OBJECT_MARKERS = (
    "门",
    "窗",
    "桌",
    "椅",
    "墙",
    "地",
    "灯",
    "刀",
    "剑",
    "枪",
    "纸",
    "信",
    "手机",
    "衣",
    "袖",
    "杯",
    "车",
    "马",
    "钥匙",
)

SENSORY_MARKERS = (
    "雨",
    "风",
    "雪",
    "血",
    "火",
    "烟",
    "光",
    "声",
    "响",
    "冷",
    "热",
    "疼",
    "湿",
    "暗",
    "亮",
    "腥",
)

DIALOGUE_RE = re.compile(r"[“\"「『]([^”\"」』\n]{2,160})[”\"」』]")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+")


def _load_text(path_value: object) -> str:
    raw_path = str(path_value or "").strip()
    if not raw_path:
        return ""
    path = Path(raw_path)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _paragraphs(text: str) -> list[str]:
    paragraphs: list[str] = []
    for chunk in re.split(r"\n\s*\n", text):
        cleaned = " ".join(line.strip() for line in chunk.splitlines() if line.strip())
        if not cleaned or HEADING_RE.match(cleaned):
            continue
        paragraphs.append(cleaned)
    return paragraphs


def _has_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _scene_signal_count(paragraph: str) -> int:
    signals = 0
    if DIALOGUE_RE.search(paragraph):
        signals += 1
    if _has_any(paragraph, ACTION_MARKERS):
        signals += 1
    if _has_any(paragraph, BODY_MARKERS):
        signals += 1
    if _has_any(paragraph, OBJECT_MARKERS):
        signals += 1
    if _has_any(paragraph, SENSORY_MARKERS):
        signals += 1
    return signals


def _snippet(paragraph: str, limit: int = 70) -> str:
    normalized = re.sub(r"\s+", "", paragraph)
    return normalized if len(normalized) <= limit else normalized[:limit] + "..."


def _abstract_hits(paragraph: str) -> list[str]:
    return [marker for marker in ABSTRACT_MARKERS if marker in paragraph]


def from_runtime_output(payload: dict[str, object]) -> dict[str, object]:
    manuscript_text = _load_text(payload.get("manuscript_path"))
    paragraphs = _paragraphs(manuscript_text)

    blockers: list[str] = []
    warnings: list[str] = []

    if not manuscript_text.strip():
        blockers.append("正文为空，无法审查场面密度。")
    elif not paragraphs:
        blockers.append("正文没有可审查的自然段，Writer 没有落成有效场面。")

    weak_indexes: list[int] = []
    abstract_indexes: list[int] = []
    abstract_count = 0
    for index, paragraph in enumerate(paragraphs, start=1):
        signal_count = _scene_signal_count(paragraph)
        hits = _abstract_hits(paragraph)
        abstract_count += len(hits)
        if len(re.sub(r"\s+", "", paragraph)) >= 35 and signal_count < 2:
            weak_indexes.append(index)
            if len(warnings) < 4:
                warnings.append(f"第 {index} 段场面信号不足：{_snippet(paragraph)}")
        if hits:
            abstract_indexes.append(index)
            if len(warnings) < 6:
                warnings.append(f"第 {index} 段出现总结/抽象标记 {','.join(hits[:3])}：{_snippet(paragraph)}")

    consecutive_weak = any(
        current + 1 == following for current, following in zip(weak_indexes, weak_indexes[1:])
    )
    weak_ratio = (len(weak_indexes) / len(paragraphs)) if paragraphs else 0.0
    abstract_limit = max(3, len(paragraphs) // 3)

    if consecutive_weak:
        blockers.append("连续自然段缺少动作、物件、身体反应、对白压力或环境阻碍，正文滑向旁白总结。")
    if len(paragraphs) >= 4 and weak_ratio > 0.45:
        blockers.append(f"场面信号不足段落占比过高：{len(weak_indexes)}/{len(paragraphs)}。")
    if abstract_count >= abstract_limit:
        blockers.append(f"总结/抽象标记过密：{abstract_count} 处，超过本章容忍线 {abstract_limit}。")

    evidence = [*blockers, *warnings]
    return build_verdict(
        dimension="prose_concreteness",
        status="fail" if blockers else ("warn" if warnings else "pass"),
        blocking=bool(blockers),
        evidence=evidence[:8],
        why_it_breaks="正文一旦连续用总结和判断替代场面，读者看到的是作者解释，而不是人物在局里挣扎。",
        minimal_fix=(
            "按段落做局部重写：每段至少落入动作、物件、身体反应、对白压力、环境阻碍、局面变化中的两项；"
            "删掉意识到/明白/本质上/这意味着等总结句，改成角色当场做错、受阻、付代价或逼问。"
        ),
        rewrite_scope="flagged_paragraphs + scene_beats",
    )
