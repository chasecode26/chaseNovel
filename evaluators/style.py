from __future__ import annotations

from evaluators.contracts import build_verdict


BLOCKING_KEYWORDS = ("AI", "机械", "同质", "概括腔")


def from_style_payload(payload: dict[str, object]) -> dict[str, object]:
    warnings = [str(item) for item in payload.get("warnings", [])]
    blocking = str(payload.get("blocking", "")).lower() == "yes"
    if not blocking:
        blocking = any(any(keyword in item for keyword in BLOCKING_KEYWORDS) for item in warnings)
    status = "fail" if blocking else ("warn" if warnings else "pass")
    return build_verdict(
        dimension="style",
        status=status,
        blocking=blocking,
        evidence=warnings,
        why_it_breaks="语言风格漂移或 AI 味过重，书级 voice 会失稳",
        minimal_fix="按书级 voice 约束重写对应段落与对白",
        rewrite_scope="language_layer",
    )
