from __future__ import annotations


def build_verdict(
    *,
    dimension: str,
    status: str,
    blocking: bool,
    evidence: list[str],
    why_it_breaks: str,
    minimal_fix: str,
    rewrite_scope: str,
) -> dict[str, object]:
    return {
        "dimension": dimension,
        "status": status,
        "blocking": blocking,
        "evidence": evidence,
        "why_it_breaks": why_it_breaks,
        "minimal_fix": minimal_fix,
        "rewrite_scope": rewrite_scope,
    }
