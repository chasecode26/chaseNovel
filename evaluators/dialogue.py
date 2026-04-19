from __future__ import annotations

import re
from pathlib import Path

from evaluators.contracts import build_verdict

_DIALOGUE_PATTERN = re.compile(r"[“\"]([^”\"\n]{2,120})[”\"]")
_EXPLANATORY_MARKERS = ("因为", "其实", "就是", "等于", "你要知道", "意思是", "说明")
_PRESSURE_MARKERS = ("吗", "呢", "先", "别", "确认", "底牌", "代价", "局面", "主动权")


def _load_text(path_value: object) -> str:
    path = Path(str(path_value).strip())
    if not str(path).strip() or not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _length_band(text: str) -> str:
    length = len(text)
    if length <= 10:
        return "short"
    if length <= 22:
        return "mid"
    return "long"


def from_runtime_output(payload: dict[str, object]) -> dict[str, object]:
    manuscript_text = _load_text(payload.get("manuscript_path"))
    review_text = _load_text(payload.get("review_notes_path"))
    dialogue_lines = [match.group(1).strip() for match in _DIALOGUE_PATTERN.finditer(manuscript_text)]

    evidence: list[str] = []
    if not manuscript_text.strip():
        evidence.append("runtime manuscript 为空，无法校验对白承压与角色声线。")
    elif len(dialogue_lines) < 2:
        evidence.append("runtime manuscript 的有效对白不足 2 句，冲突交换层过薄。")
    else:
        normalized_lines = [re.sub(r"\s+", "", line) for line in dialogue_lines]
        unique_count = len(set(normalized_lines))
        if unique_count <= 1:
            evidence.append("多句对白几乎是同一模板回声，角色声线没有真正分开。")

        explanatory_count = sum(any(marker in line for marker in _EXPLANATORY_MARKERS) for line in dialogue_lines)
        if explanatory_count >= max(2, len(dialogue_lines) // 2 + 1):
            evidence.append("对白里的解释腔偏重，人物更像在替作者补信息，而不是在争位置。")

        pressure_count = sum(any(marker in line for marker in _PRESSURE_MARKERS) for line in dialogue_lines)
        if pressure_count == 0:
            evidence.append("对白没有把试探、施压或讨价还价落出来，冲突对话失去抓手。")

        length_bands = {_length_band(line) for line in dialogue_lines}
        if len(dialogue_lines) >= 3 and len(length_bands) == 1:
            evidence.append("多句对白长度过于整齐，节拍像同一模板裁出来，角色区分度不足。")

    if review_text and "## Voice Profiles" not in review_text:
        evidence.append("runtime review notes 缺少 Voice Profiles，无法回看对白差分是否落地。")

    status = "warn" if evidence else "pass"
    return build_verdict(
        dimension="dialogue",
        status=status,
        blocking=False,
        evidence=evidence,
        why_it_breaks="对白若缺少差分、施压和反应层，角色关系会被写平，章节读感只剩信息搬运。",
        minimal_fix="回到 dialogue turns，按角色目标、压力和身份差异重写问答与回击，不要让对白只做解释。",
        rewrite_scope="scene_beats + dialogue",
    )
