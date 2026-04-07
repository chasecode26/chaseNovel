import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from chapter_planning_review import detect_target_chapter, extract_next_goal, parse_chapter_card


class ChapterPlanningReviewTest(unittest.TestCase):
    def test_detect_target_chapter_respects_explicit_priority(self) -> None:
        state_text = "- 当前章节：第8章"

        self.assertEqual(detect_target_chapter(state_text, chapter=None, target_chapter=15), 15)
        self.assertEqual(detect_target_chapter(state_text, chapter=8, target_chapter=None), 9)
        self.assertEqual(detect_target_chapter(state_text, chapter=None, target_chapter=None), 9)

    def test_extract_next_goal_supports_inline_and_section_forms(self) -> None:
        self.assertEqual(extract_next_goal("- 下章预告：主角必须先抢下粮道"), "主角必须先抢下粮道")
        self.assertEqual(
            extract_next_goal("## 下章预告\n- 计划内容：先逼出对方底牌\n"),
            "先逼出对方底牌",
        )

    def test_parse_chapter_card_extracts_core_quality_fields(self) -> None:
        card_text = "\n".join(
            [
                "- chapter_tier：regular",
                "- target_word_count：3000",
                "- 本章功能：把潜伏转成公开冲突",
                "- 本章目标：逼反派交底",
                "- 本章冲突：身份即将暴露",
                "- 本章结果类型：局势升级",
                "- 本章章尾钩子：主角发现内鬼就在身边",
                "- 章尾钩子类型：真相揭露",
            ]
        )

        payload = parse_chapter_card(card_text)

        self.assertEqual(payload["chapter_tier"], "regular")
        self.assertEqual(payload["target_word_count"], "3000")
        self.assertEqual(payload["chapter_function"], "把潜伏转成公开冲突")
        self.assertEqual(payload["chapter_goal"], "逼反派交底")
        self.assertEqual(payload["conflict_type"], "身份即将暴露")
        self.assertEqual(payload["result_type"], "局势升级")
        self.assertEqual(payload["hook_text"], "主角发现内鬼就在身边")
        self.assertEqual(payload["hook_type"], "真相揭露")


if __name__ == "__main__":
    unittest.main()
