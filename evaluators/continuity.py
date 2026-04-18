from __future__ import annotations

from evaluators.contracts import build_verdict


def from_gate_payload(payload: dict[str, object]) -> dict[str, object]:
    raw_status = str(payload.get("status", "pass"))
    blockers = [str(item) for item in payload.get("blockers", [])]
    blocking = bool(blockers) or raw_status == "fail"
    status = "fail" if blocking else ("warn" if raw_status == "warn" else "pass")
    return build_verdict(
        dimension="continuity",
        status=status,
        blocking=blocking,
        evidence=blockers,
        why_it_breaks="章节连续性或记忆锚点未对齐",
        minimal_fix="回到 LeadWriter 重新对齐章节 brief 与 memory anchors",
        rewrite_scope="chapter_card + affected paragraphs",
    )
