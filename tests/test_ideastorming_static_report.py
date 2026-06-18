"""ideastorming 静态报告渲染测试。"""

import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parent.parent / "skills" / "ideastorming" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from build_static_report import buildHtml, splitProjects


class TestSplitProjects(unittest.TestCase):
    def test_parses_documented_heading_levels(self):
        markdown = """### 项目 A

#### 对应热点
热点 A

#### MVP 功能
- 功能 A

#### 第一条开发提示词
请实现 A
"""

        projects = splitProjects(markdown)

        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["name"], "项目 A")
        self.assertEqual(projects[0]["sections"]["对应热点"], "热点 A")
        self.assertEqual(projects[0]["sections"]["MVP 功能"], "- 功能 A")
        self.assertEqual(projects[0]["sections"]["第一条开发提示词"], "请实现 A")

    def test_parses_shifted_heading_levels_by_section_titles(self):
        markdown = """## 项目 A

### 对应热点
热点 A

### MVP功能
- 功能 A

### 第一条开发提示词
请实现 A

## 项目 B

### 对应热点
热点 B
"""

        projects = splitProjects(markdown)

        self.assertEqual([project["name"] for project in projects], ["项目 A", "项目 B"])
        self.assertEqual(projects[0]["sections"]["对应热点"], "热点 A")
        self.assertEqual(projects[0]["sections"]["MVP功能"], "- 功能 A")
        self.assertEqual(projects[0]["sections"]["第一条开发提示词"], "请实现 A")
        self.assertEqual(projects[1]["sections"]["对应热点"], "热点 B")


class TestBuildHtml(unittest.TestCase):
    def test_fails_when_all_projects_have_no_sections(self):
        markdown = """### 项目 A

### 项目 B
"""

        with self.assertRaises(SystemExit) as context:
            buildHtml("测试报告", markdown, "20260618-120000")

        self.assertIn("所有项目都没有小节", str(context.exception))

    def test_rendered_html_contains_copyable_prompt(self):
        markdown = """## 项目 A

### 第一条开发提示词
请实现 A
"""

        output = buildHtml("测试报告", markdown, "20260618-120000")

        self.assertIn("项目 A", output)
        self.assertIn("复制提示词", output)
        self.assertIn("请实现 A", output)


if __name__ == "__main__":
    unittest.main()
