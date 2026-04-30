from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime.contracts import ChapterBrief, ChapterContextPacket, EvaluatorVerdict, RuntimeDecision
from runtime.memory_sync import RuntimeMemorySync


def _packet() -> ChapterContextPacket:
    return ChapterContextPacket(
        project="demo",
        chapter=7,
        active_volume="第一卷",
        active_arc="试水",
        time_anchor="夜里",
        current_place="旧楼",
        location_anchor="旧楼走廊",
        next_goal="拿回主动权",
        present_characters=["林砚"],
        knowledge_boundary="只有林砚知道账本位置",
        message_flow="电话尚未打出",
        arrival_timing="十分钟后",
        who_knows_now="林砚",
        who_cannot_know_yet="债主",
        travel_time_floor="十分钟",
        resource_state="只剩一枚钥匙",
        progress_floor="必须拿到账本",
        progress_ceiling="不能揭开幕后人",
        must_not_payoff_yet=["幕后人身份"],
        allowed_change_scope=["拿到账本"],
        open_threads=["债主逼近"],
        forbidden_inventions=["不能凭空出现帮手"],
        voice_rules=[],
    )


def _brief() -> ChapterBrief:
    return ChapterBrief(
        chapter=7,
        chapter_function="林砚拿回半步主动权",
        must_advance=["拿到账本"],
        must_not_repeat=[],
        hook_goal="账本里少了一页",
        allowed_threads=["幕后人身份"],
        disallowed_moves=[],
        progress_floor="拿到账本",
        progress_ceiling="不揭幕后人",
        must_not_payoff_yet=["幕后人身份"],
        allowed_change_scope=["账本到手"],
        voice_constraints=[],
        required_payoff_or_pressure=["账本到手但少页"],
        result_change="账本到手",
        closing_hook="少掉的一页在债主手里",
        core_conflict="债主堵门",
    )


class MemorySyncExpectationTrackingTest(unittest.TestCase):
    def test_expectation_tracking_patch_collects_runtime_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            schema_dir = Path(tmp) / "00_memory" / "schema"
            schema_dir.mkdir(parents=True)
            draft_payload = {
                "scene_beat_plan": {
                    "beats": [
                        {
                            "short_expectation": "林砚能不能拿到账本",
                            "long_expectation": "幕后人身份何时揭开",
                            "expectation_payoff": "账本到手",
                            "new_expectation": "少掉的一页在哪里",
                            "expectation_gap_risk": "拿到账本后没有新问题会断期待",
                            "genre_framework_hint": "都市逆袭：现实不爽点先落地。",
                        }
                    ]
                },
                "outcome_signature": {
                    "chapter_result": "账本到手",
                    "next_pull": "少掉的一页在债主手里",
                },
            }
            verdicts = [
                EvaluatorVerdict(
                    dimension="expectation_integrity",
                    status="warn",
                    blocking=False,
                    evidence=["新挂期待偏弱"],
                    why_it_breaks="",
                    minimal_fix="",
                    rewrite_scope="chapter_tail",
                )
            ]
            patch = RuntimeMemorySync()._build_expectation_tracking_patch(
                schema_dir,
                _packet(),
                _brief(),
                RuntimeDecision(decision="pass", rewrite_brief=None, blocking_dimensions=[]),
                verdicts,
                draft_payload,
            )
            chapters = patch.after["chapters"]
            self.assertEqual(len(chapters), 1)
            entry = chapters[0]
            self.assertEqual(entry["chapter"], 7)
            self.assertIn("林砚能不能拿到账本", entry["shortExpectations"])
            self.assertIn("幕后人身份何时揭开", entry["longExpectations"])
            self.assertIn("少掉的一页在哪里", entry["newExpectations"])
            self.assertIn("都市逆袭：现实不爽点先落地。", entry["genreFrameworkHints"])
            self.assertIn("expectation_integrity", entry["advisoryDimensions"])


if __name__ == "__main__":
    unittest.main()
