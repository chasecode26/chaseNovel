"""Naturalness evaluator — 中文自然度评估器适配器。

把 language_naturalness.py 的输出转为标准 evaluator verdict 格式。
"""

from __future__ import annotations

from evaluators.contracts import build_verdict


def from_naturalness_payload(payload: dict[str, object]) -> dict[str, object]:
    """将自然度审计结果转为标准 verdict。

    Args:
        payload: language_naturalness.analyze_naturalness() 的返回值

    Returns:
        { dimension, status, blocking, evidence, why_it_breaks, minimal_fix, rewrite_scope }
    """
    issues = payload.get("issues", [])
    if not isinstance(issues, list):
        issues = []

    verdict = str(payload.get("verdict", "pass"))
    scores = payload.get("scores", {})
    if isinstance(scores, dict):
        # 找出最低分的维度作为证据
        sorted_scores = sorted(scores.items(), key=lambda x: x[1])
        low_dims = [f"{k}={v}" for k, v in sorted_scores[:3] if v < 60]
    else:
        low_dims = []

    blocking = verdict == "rewrite"

    evidence: list[str] = []
    for issue in issues[:6]:
        reason = str(issue.get("reason", "")).strip()
        if reason:
            severity = str(issue.get("severity", ""))
            evidence.append(f"[{severity}] {reason}")

    if low_dims:
        evidence.append(f"低分维度: {', '.join(low_dims)}")

    return build_verdict(
        dimension="naturalness",
        status="fail" if blocking else ("warn" if issues else "pass"),
        blocking=blocking,
        evidence=evidence,
        why_it_breaks=(
            "章节语言质感存在机械感：句长节奏、节拍覆盖、展示/告知比偏离自然写作习惯"
            if blocking or issues
            else ""
        ),
        minimal_fix=(
            "调整句长节奏分布，增加视觉节拍覆盖，降低过渡词密度"
            if blocking or issues
            else ""
        ),
        rewrite_scope="flagged_paragraphs",
    )
