from __future__ import annotations

from evaluators.contracts import build_verdict


def from_draft_payload(payload: dict[str, object]) -> dict[str, object]:
    warnings = [str(item) for item in payload.get("warnings", [])]
    blockers = [str(item) for item in payload.get("blockers", [])]
    evidence = [*blockers, *warnings]
    blocking = bool(blockers)
    status = "fail" if blocking else ("warn" if evidence else "pass")
    return build_verdict(
        dimension="draft",
        status=status,
        blocking=blocking,
        evidence=evidence,
        why_it_breaks="章卡契约或正文篇幅未达标，当前稿件还不能进入稳定交付。",
        minimal_fix="先补齐章卡约束，再把正文调整到目标字数与章节档位范围内。",
        rewrite_scope="chapter_card_and_draft_length",
    )
