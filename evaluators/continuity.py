from __future__ import annotations

from evaluators.contracts import build_verdict


BLOCKING_KEYWORDS = ("冲突", "失配", "越界", "断裂")


def from_continuity_payload(payload: dict[str, object]) -> dict[str, object]:
    warnings = [str(item) for item in payload.get("warnings", [])]
    blockers = [str(item) for item in payload.get("blockers", [])]
    evidence = [*blockers, *warnings]
    blocking = str(payload.get("blocking", "")).lower() == "yes" or bool(blockers)
    if not blocking:
        blocking = any(any(keyword in item for keyword in BLOCKING_KEYWORDS) for item in evidence)
    status = "fail" if blocking else ("warn" if evidence else "pass")
    return build_verdict(
        dimension="continuity",
        status=status,
        blocking=blocking,
        evidence=evidence,
        why_it_breaks="时间线、状态锚点或知情边界出现问题",
        minimal_fix="回退到记忆锚点并修正冲突事实",
        rewrite_scope="chapter_fact_layer",
    )
