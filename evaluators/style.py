from __future__ import annotations

from evaluators.contracts import build_verdict


def from_language_payload(payload: dict[str, object]) -> dict[str, object]:
    issues = payload.get("issues", [])
    evidence: list[str] = []
    if isinstance(issues, list):
        for item in issues[:8]:
            if isinstance(item, dict):
                reason = str(item.get("reason", "")).strip()
                position = str(item.get("position", "")).strip()
                evidence.append(f"{position} {reason}".strip())
            else:
                evidence.append(str(item))

    verdict = str(payload.get("verdict", "pass"))
    blocking = str(payload.get("blocking", "no")) == "yes" or verdict == "rewrite"
    status = "fail" if blocking else ("warn" if verdict == "warn" or evidence else "pass")
    return build_verdict(
        dimension="style",
        status=status,
        blocking=blocking,
        evidence=evidence,
        why_it_breaks="语言审计未通过当前书级 voice 与表达约束。",
        minimal_fix="压缩 AI 味与作者提炼腔，回到单书风格约束。",
        rewrite_scope=str(payload.get("rewrite_scope", "flagged_paragraphs")),
    )


def from_quality_payload(payload: dict[str, object]) -> dict[str, object]:
    return from_language_payload(payload)
