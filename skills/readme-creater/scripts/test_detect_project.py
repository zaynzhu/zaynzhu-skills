"""Tests for detect_project.py — TDD: written before the implementation."""

import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parent / "detect_project.py"


def run_detect(cwd: Path) -> dict:
    """Run detect_project.py in *cwd* and return parsed JSON."""
    result = subprocess.run(
        ["python", str(SCRIPT), str(cwd)],
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"detect_project.py exited {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return json.loads(result.stdout)


class TestDetectProject(unittest.TestCase):

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _make_dir(self, files: dict[str, str] | None = None) -> Path:
        """Create a temp directory populated with *files* {relative_path: content}."""
        d = Path(tempfile.mkdtemp())
        if files:
            for rel, content in files.items():
                p = d / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(textwrap.dedent(content), encoding="utf-8")
        self.addCleanup(lambda: _rmtree(d))
        return d

    # ------------------------------------------------------------------
    # tests
    # ------------------------------------------------------------------

    def test_empty_directory(self):
        """Empty dir should return defaults with directory name."""
        d = self._make_dir()
        data = run_detect(d)
        self.assertIsInstance(data, dict)
        # name should fall back to directory name
        self.assertEqual(data["name"], d.name)
        # language should be unknown
        self.assertEqual(data["language"], "Unknown")
        # no readme
        self.assertFalse(data["has_readme"])

    def test_python_project(self):
        """Detect Python project from setup.py and requirements.txt."""
        d = self._make_dir({
            "setup.py": textwrap.dedent("""\
                from setuptools import setup
                setup(name="mylib", description="A lib", python_requires=">=3.9")
            """),
            "requirements.txt": "requests>=2.0\nflask\n",
            "main.py": "print('hi')\n",
            "utils.py": "pass\n",
        })
        data = run_detect(d)
        self.assertEqual(data["name"], "mylib")
        self.assertEqual(data["language"], "Python")
        self.assertIn("requests", data["dependencies"])
        self.assertIn("flask", data["dependencies"])
        self.assertIn("3.9", data.get("python_version", ""))

    def test_node_project(self):
        """Detect Node.js project from package.json."""
        d = self._make_dir({
            "package.json": json.dumps({
                "name": "cool-app",
                "description": "An app",
                "dependencies": {"express": "^4.18", "lodash": "^4.0"},
                "devDependencies": {"jest": "^29"},
                "repository": {"url": "https://github.com/user/cool-app.git"},
            }),
            "index.js": "console.log('hi')\n",
            "src/app.js": "module.exports = {}\n",
        })
        data = run_detect(d)
        self.assertEqual(data["name"], "cool-app")
        self.assertEqual(data["description"], "An app")
        self.assertEqual(data["language"], "JavaScript")
        self.assertIn("express", data["dependencies"])
        self.assertIn("lodash", data["dependencies"])
        self.assertEqual(data["repo_url"], "https://github.com/user/cool-app")

    def test_rust_project(self):
        """Detect Rust project from Cargo.toml."""
        d = self._make_dir({
            "Cargo.toml": textwrap.dedent("""\
                [package]
                name = "my-crate"
                description = "A Rust crate"
                license = "MIT"

                [dependencies]
                serde = "1.0"
                tokio = { version = "1", features = ["full"] }
            """),
            "src/main.rs": "fn main() {}\n",
            "src/lib.rs": "pub fn hello() {}\n",
        })
        data = run_detect(d)
        self.assertEqual(data["name"], "my-crate")
        self.assertEqual(data["language"], "Rust")
        self.assertIn("serde", data["dependencies"])
        self.assertIn("tokio", data["dependencies"])
        self.assertIn("MIT", data.get("license", ""))

    def test_existing_readme(self):
        """Detect existing README and extract sections."""
        d = self._make_dir({
            "README.md": textwrap.dedent("""\
                # My Project

                Some intro text.

                ## Installation

                Run pip install.

                ## Usage

                Use it like this.

                ## Contributing

                PRs welcome.
            """),
            "main.py": "pass\n",
        })
        data = run_detect(d)
        self.assertTrue(data["has_readme"])
        summary = data.get("readme_summary", {})
        self.assertIsInstance(summary.get("sections", []), list)
        self.assertIn("Installation", summary["sections"])
        self.assertIn("Usage", summary["sections"])
        self.assertIn("Contributing", summary["sections"])
        self.assertGreater(summary.get("line_count", 0), 5)

    def test_logo_detection(self):
        """Detect logo images in common directories."""
        d = self._make_dir({
            "assets/logo.svg": "<svg></svg>",
            "main.py": "pass\n",
        })
        data = run_detect(d)
        self.assertIsNotNone(data.get("logo_path"))
        self.assertIn("logo", data["logo_path"])

    def test_ci_detection(self):
        """Detect GitHub Actions CI."""
        d = self._make_dir({
            ".github/workflows/ci.yml": textwrap.dedent("""\
                name: CI
                on: [push]
                jobs:
                  test:
                    runs-on: ubuntu-latest
                    steps:
                      - uses: actions/checkout@v4
            """),
            "main.py": "pass\n",
        })
        data = run_detect(d)
        self.assertEqual(data.get("ci_type"), "github_actions")

    def test_go_project(self):
        """Detect Go project from go.mod."""
        d = self._make_dir({
            "go.mod": textwrap.dedent("""\
                module github.com/user/mygo

                go 1.21

                require (
                    github.com/gin-gonic/gin v1.9.1
                    github.com/spf13/cobra v1.8.0
                )
            """),
            "main.go": "package main\n\nfunc main() {}\n",
            "pkg/handler.go": "package pkg\n",
        })
        data = run_detect(d)
        self.assertEqual(data["name"], "mygo")
        self.assertEqual(data["language"], "Go")
        self.assertIn("github.com/gin-gonic/gin", data["dependencies"])
        self.assertIn("github.com/spf13/cobra", data["dependencies"])


def _rmtree(path: Path):
    """Remove a directory tree, ignoring errors (Windows file-locking)."""
    import shutil
    shutil.rmtree(path, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
