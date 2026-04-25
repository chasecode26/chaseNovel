#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from language_audit import analyze_text, parse_style_file  # noqa: E402


SAMPLES_DIR = REPO_ROOT / "assets" / "examples" / "language-gate"
BLOCKING_TYPES = {
    "cn_ai_explanation_stack",
    "cn_abstract_noun_pileup",
    "authorial_summary_blacklist",
    "summary_statement_overwrite",
}


def run_sample(name: str) -> dict[str, object]:
    text = (SAMPLES_DIR / name).read_text(encoding="utf-8")
    style_profile = parse_style_file(REPO_ROOT / "assets" / "examples" / "language-gate" / "missing-style.md")
    analysis = analyze_text(text, style_profile, None)
    issue_types = [str(item.get("type", "")) for item in analysis["issues"]]
    return {
        "sample": name,
        "verdict": analysis["verdict"],
        "blocking": analysis["blocking"],
        "issue_types": issue_types,
        "high_issue_count": sum(1 for item in analysis["issues"] if item.get("severity") == "high"),
    }


def main() -> int:
    bad = run_sample("ai-tone-bad.md")
    clean = run_sample("clean-pass.md")
    failures: list[str] = []

    if bad["verdict"] != "rewrite" or bad["blocking"] != "yes":
        failures.append("ai-tone-bad.md should be blocking rewrite")
    if not (set(bad["issue_types"]) & BLOCKING_TYPES):
        failures.append("ai-tone-bad.md should hit at least one anti-AI blocking type")

    clean_blocking_hits = set(clean["issue_types"]) & BLOCKING_TYPES
    if clean["verdict"] == "rewrite" or clean_blocking_hits:
        failures.append(f"clean-pass.md should not hit blocking anti-AI types: {sorted(clean_blocking_hits)}")

    payload = {"bad": bad, "clean": clean, "failures": failures}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
