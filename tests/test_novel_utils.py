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

from novel_utils import chapter_number_from_name, load_due_foreshadow_ids, useful_lines


class NovelUtilsTest(unittest.TestCase):
    def make_temp_project_dir(self) -> Path:
        path = TEST_TMP_ROOT / f"novel-utils-{uuid.uuid4().hex}"
        path.mkdir(parents=True, exist_ok=False)
        self.addCleanup(lambda: shutil.rmtree(path, ignore_errors=True))
        return path

    def test_chapter_number_from_name_supports_multiple_naming_styles(self) -> None:
        self.assertEqual(chapter_number_from_name("第003章 山雨欲来.md"), 3)
        self.assertEqual(chapter_number_from_name("chapter-012.md"), 12)
        self.assertEqual(chapter_number_from_name("ch7-冲突升级.md"), 7)
        self.assertEqual(chapter_number_from_name("001-开局.md"), 1)

    def test_load_due_foreshadow_ids_filters_recycled_and_future_items(self) -> None:
        project_dir = self.make_temp_project_dir()
        memory_dir = project_dir / "00_memory"
        memory_dir.mkdir(parents=True)
        (memory_dir / "foreshadowing.md").write_text(
            "\n".join(
                [
                    "| ID | 伏笔 | 埋设章 | 当前状态 | 触发条件 | 回收方式 | 到期章 | 热度 | 状态 |",
                    "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                    "| F1 | 身份异动 | 第1章 | 活跃 | 曝光 | 摊牌 | 第5章 | 高 | 进行中 |",
                    "| F2 | 旧敌回归 | 第2章 | 活跃 | 相遇 | 开战 | 第9章 | 高 | 进行中 |",
                    "| F3 | 假线索 | 第3章 | 活跃 | 反转 | 废弃 | 第4章 | 低 | 已废弃 |",
                    "| F4 | 真底牌 | 第4章 | 活跃 | 强敌压境 | 兑现 | 第5章 | 高 | 已回收 |",
                ]
            ),
            encoding="utf-8",
        )

        self.assertEqual(load_due_foreshadow_ids(project_dir, 5), ["F1"])

    def test_useful_lines_skips_placeholders_and_tables(self) -> None:
        text = "\n".join(
            [
                "# 标题",
                "",
                "有效信息一",
                "| 列1 | 列2 |",
                "| --- | --- |",
                "{PLACEHOLDER}",
                "<!-- hidden -->",
                "> 引用",
                "有效信息二",
            ]
        )

        self.assertEqual(useful_lines(text, 5), ["有效信息一", "有效信息二"])


if __name__ == "__main__":
    unittest.main()
