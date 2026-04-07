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

from draft_gate import build_payload


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class DraftGateTest(unittest.TestCase):
    def make_temp_project_dir(self) -> Path:
        path = TEST_TMP_ROOT / f"draft-gate-{uuid.uuid4().hex}"
        path.mkdir(parents=True, exist_ok=False)
        self.addCleanup(lambda: shutil.rmtree(path, ignore_errors=True))
        return path

    def test_build_payload_passes_for_regular_chapter_in_range(self) -> None:
        project_dir = self.make_temp_project_dir()
        chapter_path = project_dir / "03_chapters" / "第001章 开局.md"
        card_path = project_dir / "01_outline" / "chapter-001.md"
        write_text(chapter_path, "字" * 2800)
        write_text(
            card_path,
            "\n".join(
                [
                    "- chapter_tier：regular",
                    "- target_word_count：3000",
                    "- 本章功能：立局",
                ]
            ),
        )

        payload = build_payload(project_dir, 1, chapter_path)

        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["word_count"], 2800)
        self.assertEqual(payload["chapter_tier"], "regular")

    def test_build_payload_fails_when_climax_chapter_is_too_long(self) -> None:
        project_dir = self.make_temp_project_dir()
        chapter_path = project_dir / "03_chapters" / "第009章 爆点.md"
        card_path = project_dir / "01_outline" / "chapter-009.md"
        write_text(chapter_path, "字" * 4600)
        write_text(
            card_path,
            "\n".join(
                [
                    "- chapter_tier：climax",
                    "- target_word_count：4200",
                    "- 本章功能：高潮",
                ]
            ),
        )

        payload = build_payload(project_dir, 9, chapter_path)

        self.assertEqual(payload["status"], "fail")
        self.assertTrue(any("不符合" in item for item in payload["blockers"]))


if __name__ == "__main__":
    unittest.main()
