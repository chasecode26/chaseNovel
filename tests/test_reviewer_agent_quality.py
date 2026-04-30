from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime.agents.reviewer import ReviewerAgent


def _write_manuscript(directory: Path, text: str) -> Path:
    path = directory / "reader_manuscript.md"
    path.write_text(text.strip() + "\n", encoding="utf-8")
    return path


def _verdict(payload: dict[str, object], dimension: str):
    verdicts = ReviewerAgent().review(payload)
    for item in verdicts:
        if item.dimension == dimension:
            return item
    raise AssertionError(f"missing verdict: {dimension}")


class ReviewerAgentQualityFixturesTest(unittest.TestCase):
    def test_opening_failure_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            opening = (
                "这片大陆的等级体系极其复杂，势力分布也延续了三千年。"
                "世界背景牵涉九大宗门、七十二座城和无数古老家族。"
                "在这个漫长而宏大的历史进程中，人们逐渐形成了固定秩序。"
                "所有修行者都必须理解规则，理解规则之后才能理解命运。"
                "因此，本故事的核心矛盾来源于制度与人的冲突。"
            )
            manuscript = _write_manuscript(root, opening * 8)
            verdict = _verdict(
                {
                    "project": str(root),
                    "chapter": 1,
                    "manuscript_path": str(manuscript),
                    "scene_cards": [],
                    "outcome_signature": {},
                    "scene_beat_plan": {"beats": []},
                },
                "opening_diagnostics",
            )
            self.assertEqual(verdict.status, "fail")
            self.assertTrue(verdict.blocking)

    def test_expectation_gap_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manuscript = _write_manuscript(root, "他推开门。\n\n“人呢？”\n\n屋里没有回答。")
            verdict = _verdict(
                {
                    "project": str(root),
                    "chapter": 3,
                    "manuscript_path": str(manuscript),
                    "scene_cards": [{"summary": "入场", "result_type": "turn", "cost_type": "cost"}],
                    "outcome_signature": {"chapter_result": "找到空屋"},
                    "scene_beat_plan": {"beats": [{"scene_goal": "找人"}]},
                },
                "expectation_integrity",
            )
            self.assertEqual(verdict.status, "fail")
            self.assertTrue(verdict.blocking)

    def test_genre_framework_drift_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text = (
                "设定一规定资源必须按规则流转。设定二规定门派按规则审核。"
                "设定三规定身份按规则登记。设定四规定任务按规则结算。"
                "设定五规定奖惩按规则执行。设定六规定所有规则不得违背。"
            )
            manuscript = _write_manuscript(root, text)
            verdict = _verdict(
                {
                    "project": str(root),
                    "chapter": 4,
                    "manuscript_path": str(manuscript),
                    "scene_cards": [{"summary": "说明规则", "result_type": "info", "cost_type": "none"}],
                    "outcome_signature": {"chapter_result": "解释规则", "next_pull": "继续解释"},
                    "scene_beat_plan": {"beats": [{"scene_goal": "交代规则"}]},
                },
                "genre_framework_fit",
            )
            self.assertEqual(verdict.status, "fail")
            self.assertTrue(verdict.blocking)

    def test_ai_like_prose_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text = """
他终于意识到，真正的问题并不在眼前，而在命运本身。

她也明白，这意味着所有选择都将走向不可避免的结局。

本质上，他们不得不承认，归根结底一切都只是成长。

关键在于，他知道自己已经无法回头，也终于明白了代价。
"""
            manuscript = _write_manuscript(root, text)
            verdict = _verdict(
                {
                    "project": str(root),
                    "chapter": 5,
                    "manuscript_path": str(manuscript),
                    "scene_cards": [{"summary": "心理总结", "result_type": "none", "cost_type": "none"}],
                    "outcome_signature": {"chapter_result": "心理变化", "next_pull": "继续思考"},
                    "scene_beat_plan": {
                        "beats": [
                            {
                                "short_expectation": "他是否行动",
                                "new_expectation": "下一步更难",
                                "expectation_gap_risk": "心理太多",
                                "genre_framework_hint": "通用爽文",
                            }
                        ]
                    },
                },
                "prose_concreteness",
            )
            self.assertEqual(verdict.status, "fail")
            self.assertTrue(verdict.blocking)

    def test_soft_chapter_tail_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manuscript = _write_manuscript(root, "他想了很久。\n\n因此，一切都结束了。")
            verdict = _verdict(
                {
                    "project": str(root),
                    "chapter": 6,
                    "manuscript_path": str(manuscript),
                    "scene_cards": [{"summary": "收束", "result_type": "end", "cost_type": "none"}],
                    "outcome_signature": {},
                    "scene_beat_plan": {
                        "beats": [
                            {
                                "short_expectation": "是否收住",
                                "new_expectation": "下一章更难",
                                "expectation_gap_risk": "尾钩太软",
                                "genre_framework_hint": "通用爽文",
                            }
                        ]
                    },
                },
                "hook_integrity",
            )
            self.assertEqual(verdict.status, "fail")
            self.assertTrue(verdict.blocking)


if __name__ == "__main__":
    unittest.main()
