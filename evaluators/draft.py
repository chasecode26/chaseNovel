from __future__ import annotations

from evaluators.contracts import build_verdict


def from_draft_payload(payload: dict[str, object]) -> dict[str, object]:
    blockers = [str(item) for item in payload.get("blockers", []) if str(item).strip()]
    warnings = [str(item) for item in payload.get("warnings", []) if str(item).strip()]
    evidence = blockers or warnings
    blocking = bool(blockers)
    status = "fail" if blockers else ("warn" if warnings else "pass")
    return build_verdict(
        dimension="pacing",
        status=status,
        blocking=blocking,
        evidence=evidence,
        why_it_breaks="章节字数与篇幅控制未通过当前章节节奏门。",
        minimal_fix="回到 Writer 调整正文长度与结果密度，避免章节失衡。",
        rewrite_scope="full_chapter" if blocking else "flagged_paragraphs",
    )
