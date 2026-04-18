from __future__ import annotations

from evaluators.contracts import build_verdict


def from_repeat_payload(payload: dict[str, object]) -> dict[str, object]:
    warnings = [str(item) for item in payload.get("warnings", [])]
    return build_verdict(
        dimension="repeat",
        status="warn" if warnings else "pass",
        blocking=False,
        evidence=warnings,
        why_it_breaks="近章推进存在重复风险",
        minimal_fix="调整本章结果类型、冲突类型或钩子类型",
        rewrite_scope="chapter_result_and_hook",
    )
