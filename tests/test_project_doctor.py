import sys
import shutil
import unittest
import uuid
from pathlib import Path


TEST_TMP_ROOT = Path(__file__).resolve().parent / ".tmp"
TEST_TMP_ROOT.mkdir(exist_ok=True)
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from project_doctor import build_payload


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class ProjectDoctorTest(unittest.TestCase):
    def make_temp_project_dir(self) -> Path:
        path = TEST_TMP_ROOT / f"project-doctor-{uuid.uuid4().hex}"
        path.mkdir(parents=True, exist_ok=False)
        self.addCleanup(lambda: shutil.rmtree(path, ignore_errors=True))
        return path

    def test_build_payload_fails_when_required_files_are_missing(self) -> None:
        payload = build_payload(self.make_temp_project_dir())

        self.assertEqual(payload["status"], "fail")
        self.assertIn("00_memory", payload["missing_dirs"])
        self.assertIn("00_memory/plan.md", payload["missing_files"])

    def test_build_payload_warns_when_state_is_ahead_of_chapters(self) -> None:
        project_dir = self.make_temp_project_dir()
        for directory in (
            "00_memory/retrieval",
            "00_memory/summaries",
            "01_outline",
            "02_knowledge",
            "03_chapters",
            "04_gate",
        ):
            (project_dir / directory).mkdir(parents=True, exist_ok=True)

        for file_path in (
            "00_memory/plan.md",
            "00_memory/arc_progress.md",
            "00_memory/characters.md",
            "00_memory/character_arcs.md",
            "00_memory/timeline.md",
            "00_memory/foreshadowing.md",
            "00_memory/payoff_board.md",
            "00_memory/style.md",
            "00_memory/voice.md",
            "00_memory/scene_preferences.md",
            "00_memory/findings.md",
            "00_memory/summaries/recent.md",
        ):
            write_text(project_dir / file_path, "ok")

        write_text(project_dir / "00_memory/state.md", "- 当前章节：第12章\n")
        write_text(project_dir / "03_chapters/第001章 开局.md", "正文")

        payload = build_payload(project_dir)

        self.assertEqual(payload["status"], "warn")
        self.assertEqual(payload["chapter_count"], 1)
        self.assertEqual(payload["current_chapter"], 12)
        self.assertTrue(
            any("状态可能超前" in warning for warning in payload["warnings"])
        )
        self.assertTrue(
            any("style_guardrails.md" in warning for warning in payload["warnings"])
        )


if __name__ == "__main__":
    unittest.main()
