"""Settings evaluator — 设定一致性评估器适配器。

把 settings_consistency.py 的输出转为标准 evaluator verdict 格式。
"""

from __future__ import annotations

from evaluators.contracts import build_verdict


def from_settings_payload(payload: dict[str, object]) -> dict[str, object]:
    """将设定一致性审计结果转为标准 verdict。

    Args:
        payload: settings_consistency.analyze_settings() 的返回值

    Returns:
        { dimension, status, blocking, evidence, why_it_breaks, minimal_fix, rewrite_scope }
    """
    issues = payload.get("issues", [])
    if not isinstance(issues, list):
        issues = []

    verdict = str(payload.get("verdict", "pass"))
    blocking = verdict == "rewrite"

    evidence: list[str] = []
    for issue in issues[:8]:
        reason = str(issue.get("reason", "")).strip()
        if reason:
            severity = str(issue.get("severity", ""))
            evidence.append(f"[{severity}] {reason}")

    return build_verdict(
        dimension="settings",
        status="fail" if blocking else ("warn" if issues else "pass"),
        blocking=blocking,
        evidence=evidence,
        why_it_breaks=(
            "世界设定、力量体系、资源状态或术语定义存在跨章不一致"
            if blocking or issues
            else ""
        ),
        minimal_fix=(
            "对齐跨章设定，补充资源变化的原因，修正术语定义漂移"
            if blocking or issues
            else ""
        ),
        rewrite_scope="affected_paragraphs",
    )
