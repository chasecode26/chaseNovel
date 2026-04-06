import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from language_audit import analyze_text


class LanguageAuditTest(unittest.TestCase):
    def build_style_profile(self, genre: str = "都市") -> dict[str, object]:
        return {
            "title": "测试书",
            "genre": genre,
            "forbidden_phrases": [],
            "caution_phrases": [],
            "forbidden_words": [],
            "caution_words": [],
            "allowed_phrases": [],
            "allowed_authorial_patterns": [],
            "repetition_alert_words": [],
            "thresholds": {
                "authorial_narration_tolerance": 0,
                "soft_authorial_tolerance": 1,
                "abstract_word_tolerance": 2,
                "repeated_phrase_tolerance": 1,
                "lyrical_paragraph_tolerance": 1,
                "vague_expression_tolerance": 1,
            },
            "explicit_thresholds": {},
            "narration_rules": [],
            "preferred_patterns": [],
            "dialogue_ratio_baseline": "",
            "rhythm_baseline": "",
            "narration_density": "",
            "sentence_cadence": "",
            "narration_distance": "",
            "must_keep_voice": "",
            "target_reading_feel": "",
            "clarity_baseline": "默认说大白话",
            "suspense_reveal_boundary": "只有悬疑关键点才允许留白",
        }

    def test_non_suspense_text_flags_vague_expression(self) -> None:
        style_profile = self.build_style_profile()
        text = "那个人没有把那件事说破，只留下一句谁都听不懂的话。"

        analysis = analyze_text(text, style_profile)

        issue_types = [item["type"] for item in analysis["issues"]]
        self.assertIn("vague_expression", issue_types)
        self.assertEqual(analysis["verdict"], "rewrite")

    def test_suspense_text_allows_small_amount_of_concealment(self) -> None:
        style_profile = self.build_style_profile("悬疑/推理")
        text = "那个人把线索压在桌角，没有说破真相，只让他先去看那张照片。"

        analysis = analyze_text(text, style_profile)

        issue_types = [item["type"] for item in analysis["issues"]]
        self.assertNotIn("vague_expression", issue_types)


if __name__ == "__main__":
    unittest.main()
