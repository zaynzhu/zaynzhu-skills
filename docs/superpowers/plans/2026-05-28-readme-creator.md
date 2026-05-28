# readme-creator Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a universal README creator/improver skill that generates stunning, professional READMEs with badges, star history, bilingual support, and smart project detection.

**Architecture:** Single SKILL.md (~450 lines) as the main instruction file, one Python script for project metadata detection, and four reference files for templates/guidelines. The skill follows a 5-phase flow: detect → analyze existing → confirm → generate → review.

**Tech Stack:** Python 3.8+ (detection script), Markdown (SKILL.md + references), shields.io (badges), star-history.com (charts), contrib.rocks (contributors)

---

## File Structure

```
skills/readme-creater/                  ← New skill directory
├── SKILL.md                            ← Main instruction file (~450 lines)
├── scripts/
│   └── detect_project.py               ← Project metadata detection script
└── references/
    ├── badge-templates.md              ← shields.io badge template library (30+ badges)
    ├── section-templates.md            ← README section writing templates
    ├── style-guide.md                  ← Visual style guide (emoji, layout, bilingual)
    └── logo-fallback.md                ← Emoji fallback logo rules

README.md                               ← Add skill to index table
CLAUDE.md                               ← Add skill to inventory table
```

---

### Task 1: Create Directory Structure

**Files:**
- Create: `skills/readme-creater/scripts/` (directory)
- Create: `skills/readme-creater/references/` (directory)

- [ ] **Step 1: Create skill directories**

```bash
cd E:/gemini/antigravity/zaynzhu-skills
mkdir -p skills/readme-creater/scripts
mkdir -p skills/readme-creater/references
```

- [ ] **Step 2: Verify structure**

```bash
ls -la skills/readme-creater/
```

Expected: `scripts/` and `references/` directories visible.

- [ ] **Step 3: Commit**

```bash
git add skills/readme-creater/
git commit -m "feat(readme-creator): scaffold skill directory structure"
```

---

### Task 2: Write detect_project.py with TDD

**Files:**
- Create: `skills/readme-creater/scripts/test_detect_project.py`
- Create: `skills/readme-creater/scripts/detect_project.py`

This script scans a project directory and outputs structured JSON with project metadata. It must handle missing files gracefully and produce valid JSON output in all cases.

- [ ] **Step 1: Write the test file**

Create `skills/readme-creater/scripts/test_detect_project.py`:

```python
"""Tests for detect_project.py"""
import json
import os
import subprocess
import sys
import tempfile
import shutil

SCRIPT = os.path.join(os.path.dirname(__file__), "detect_project.py")


def run_detect(project_dir):
    """Run detect_project.py on a directory and return parsed JSON."""
    result = subprocess.run(
        [sys.executable, SCRIPT, project_dir],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    return json.loads(result.stdout)


def test_empty_directory():
    """Empty dir should return defaults with directory name."""
    with tempfile.TemporaryDirectory() as d:
        data = run_detect(d)
        assert data["name"] == os.path.basename(d)
        assert data["description"] == ""
        assert data["language"] == "Unknown"
        assert data["license"] == ""
        assert data["repo_url"] == ""
        assert data["dependencies"] == []
        assert data["has_readme"] is False
        assert data["logo_path"] == ""
        assert data["ci_type"] == ""
        assert data["package_manager"] == ""


def test_python_project():
    """Detect Python project from setup.py and requirements.txt."""
    with tempfile.TemporaryDirectory() as d:
        # Create setup.py
        with open(os.path.join(d, "setup.py"), "w") as f:
            f.write(
                "from setuptools import setup\n"
                "setup(name='my-tool', description='A cool tool', "
                "license='MIT', python_requires='>=3.9')\n"
            )
        # Create requirements.txt
        with open(os.path.join(d, "requirements.txt"), "w") as f:
            f.write("requests>=2.28\nclick>=8.0\n")
        # Create LICENSE
        with open(os.path.join(d, "LICENSE"), "w") as f:
            f.write("MIT License\n\nCopyright (c) 2026\n")
        # Create some .py files
        with open(os.path.join(d, "main.py"), "w") as f:
            f.write("print('hello')\n")
        with open(os.path.join(d, "utils.py"), "w") as f:
            f.write("def helper(): pass\n")

        data = run_detect(d)
        assert data["name"] == "my-tool"
        assert data["description"] == "A cool tool"
        assert data["language"] == "Python"
        assert data["license"] == "MIT"
        assert data["dependencies"] == ["requests", "click"]
        assert data["has_readme"] is False
        assert data["package_manager"] == "pip"
        assert data["python_version"] == ">=3.9"


def test_node_project():
    """Detect Node.js project from package.json."""
    with tempfile.TemporaryDirectory() as d:
        pkg = {
            "name": "my-app",
            "description": "A web app",
            "license": "Apache-2.0",
            "repository": "https://github.com/user/my-app",
            "dependencies": {"express": "^4.18", "lodash": "^4.17"}
        }
        with open(os.path.join(d, "package.json"), "w") as f:
            json.dump(pkg, f)
        with open(os.path.join(d, "index.js"), "w") as f:
            f.write("console.log('hello')\n")

        data = run_detect(d)
        assert data["name"] == "my-app"
        assert data["description"] == "A web app"
        assert data["language"] == "JavaScript"
        assert data["license"] == "Apache-2.0"
        assert data["repo_url"] == "https://github.com/user/my-app"
        assert set(data["dependencies"]) == {"express", "lodash"}
        assert data["package_manager"] == "npm"


def test_rust_project():
    """Detect Rust project from Cargo.toml."""
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "Cargo.toml"), "w") as f:
            f.write(
                '[package]\nname = "my-crate"\n'
                'description = "A Rust crate"\n'
                'license = "MIT"\n\n'
                '[dependencies]\nserde = "1.0"\ntokio = "1"\n'
            )
        with open(os.path.join(d, "src", "main.rs"), "w") as f:
            os.makedirs(os.path.join(d, "src"), exist_ok=True)
            f.write("fn main() { println!(\"hello\"); }\n")

        data = run_detect(d)
        assert data["name"] == "my-crate"
        assert data["description"] == "A Rust crate"
        assert data["language"] == "Rust"
        assert data["license"] == "MIT"
        assert set(data["dependencies"]) == {"serde", "tokio"}
        assert data["package_manager"] == "cargo"


def test_existing_readme():
    """Detect existing README and extract sections."""
    with tempfile.TemporaryDirectory() as d:
        readme_content = (
            "# My Project\n\n"
            "A great project.\n\n"
            "## Installation\n\n"
            "```\npip install my-project\n```\n\n"
            "## Usage\n\n"
            "```python\nimport my_project\n```\n\n"
            "## License\n\nMIT\n"
        )
        with open(os.path.join(d, "README.md"), "w") as f:
            f.write(readme_content)
        with open(os.path.join(d, "main.py"), "w") as f:
            f.write("print('hello')\n")

        data = run_detect(d)
        assert data["has_readme"] is True
        assert "sections" in data["readme_summary"]
        assert "Installation" in data["readme_summary"]["sections"]
        assert "Usage" in data["readme_summary"]["sections"]
        assert data["readme_summary"]["line_count"] > 0


def test_logo_detection():
    """Detect logo images in common directories."""
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "docs", "assets"))
        with open(os.path.join(d, "docs", "assets", "logo.svg"), "w") as f:
            f.write("<svg></svg>")
        with open(os.path.join(d, "main.py"), "w") as f:
            f.write("print('hello')\n")

        data = run_detect(d)
        assert data["logo_path"] == "docs/assets/logo.svg"


def test_ci_detection():
    """Detect GitHub Actions CI."""
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, ".github", "workflows"))
        with open(os.path.join(d, ".github", "workflows", "ci.yml"), "w") as f:
            f.write("name: CI\non: push\n")
        with open(os.path.join(d, "main.py"), "w") as f:
            f.write("print('hello')\n")

        data = run_detect(d)
        assert data["ci_type"] == "github-actions"


def test_go_project():
    """Detect Go project from go.mod."""
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "go.mod"), "w") as f:
            f.write("module github.com/user/my-go-app\n\ngo 1.21\n")
        with open(os.path.join(d, "main.go"), "w") as f:
            f.write("package main\n\nfunc main() {}\n")

        data = run_detect(d)
        assert data["name"] == "my-go-app"
        assert data["language"] == "Go"
        assert data["package_manager"] == "go-modules"


if __name__ == "__main__":
    # Run all test functions
    import inspect
    tests = [v for k, v in globals().items() if k.startswith("test_") and inspect.isfunction(v)]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {test.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd E:/gemini/antigravity/zaynzhu-skills
python skills/readme-creater/scripts/test_detect_project.py
```

Expected: All tests FAIL with "Script failed" or "No such file" because `detect_project.py` does not exist yet.

- [ ] **Step 3: Write detect_project.py**

Create `skills/readme-creater/scripts/detect_project.py`:

```python
#!/usr/bin/env python3
"""
Detect project metadata and output structured JSON.

Usage: python detect_project.py [project_dir]
If no directory given, uses current working directory.

Output: JSON to stdout with fields:
  name, description, language, license, repo_url, dependencies,
  has_readme, readme_summary, logo_path, ci_type, python_version,
  package_manager
"""
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

# Language detection by file extension
EXT_TO_LANG = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".jsx": "JavaScript", ".tsx": "TypeScript",
    ".rs": "Rust", ".go": "Go", ".java": "Java",
    ".rb": "Ruby", ".php": "PHP", ".cs": "C#",
    ".cpp": "C++", ".c": "C", ".h": "C/C++",
    ".swift": "Swift", ".kt": "Kotlin", ".scala": "Scala",
    ".lua": "Lua", ".r": "R", ".jl": "Julia",
    ".dart": "Dart", ".ex": "Elixir", ".erl": "Erlang",
    ".zig": "Zig", ".nim": "Nim", ".v": "V",
}

# Directories to skip when counting files
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "env", ".env", "dist", "build", ".next", ".nuxt",
    "target", "vendor", ".idea", ".vscode", ".claude",
}


def detect_name(project_dir, configs):
    """Detect project name from config files or directory name."""
    # Try package.json
    if "package.json" in configs:
        try:
            pkg = json.loads(configs["package.json"])
            if "name" in pkg:
                return pkg["name"]
        except (json.JSONDecodeError, KeyError):
            pass

    # Try setup.py
    if "setup.py" in configs:
        match = re.search(r"name\s*=\s*['\"]([^'\"]+)['\"]", configs["setup.py"])
        if match:
            return match.group(1)

    # Try pyproject.toml
    if "pyproject.toml" in configs:
        match = re.search(r'name\s*=\s*"([^"]+)"', configs["pyproject.toml"])
        if match:
            return match.group(1)

    # Try Cargo.toml
    if "Cargo.toml" in configs:
        match = re.search(r'name\s*=\s*"([^"]+)"', configs["Cargo.toml"])
        if match:
            return match.group(1)

    # Try go.mod
    if "go.mod" in configs:
        match = re.search(r"module\s+(\S+)", configs["go.mod"])
        if match:
            # Use last path segment as name
            return match.group(1).rstrip("/").split("/")[-1]

    # Fallback to directory name
    return os.path.basename(os.path.abspath(project_dir))


def detect_description(configs, readme_content):
    """Detect project description from config files or README."""
    if "package.json" in configs:
        try:
            pkg = json.loads(configs["package.json"])
            if "description" in pkg and pkg["description"]:
                return pkg["description"]
        except (json.JSONDecodeError, KeyError):
            pass

    if "setup.py" in configs:
        match = re.search(r"description\s*=\s*['\"]([^'\"]+)['\"]", configs["setup.py"])
        if match:
            return match.group(1)

    if "pyproject.toml" in configs:
        match = re.search(r'description\s*=\s*"([^"]+)"', configs["pyproject.toml"])
        if match:
            return match.group(1)

    if "Cargo.toml" in configs:
        match = re.search(r'description\s*=\s*"([^"]+)"', configs["Cargo.toml"])
        if match:
            return match.group(1)

    # Try first non-heading paragraph from README
    if readme_content:
        lines = readme_content.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("[!") and not line.startswith("!["):
                return line[:200]

    return ""


def detect_language(project_dir):
    """Detect primary language by counting files per extension."""
    counter = Counter()
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in EXT_TO_LANG:
                counter[ext] += 1

    if not counter:
        return "Unknown"

    most_common_ext = counter.most_common(1)[0][0]
    return EXT_TO_LANG[most_common_ext]


def detect_license(project_dir, configs):
    """Detect license from LICENSE file or config."""
    # Check LICENSE file
    for name in ["LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "LICENCE.md"]:
        path = os.path.join(project_dir, name)
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(1000).upper()
                if "MIT" in content:
                    return "MIT"
                if "APACHE" in content:
                    return "Apache-2.0"
                if "GPL" in content:
                    if "VERSION 3" in content or "V3" in content:
                        return "GPL-3.0"
                    return "GPL-2.0"
                if "BSD" in content:
                    if "3-CLAUSE" in content or "3 CLAUSE" in content:
                        return "BSD-3-Clause"
                    return "BSD-2-Clause"
                if "MOZILLA" in content or "MPL" in content:
                    return "MPL-2.0"
                if "ISC" in content:
                    return "ISC"
                if "UNLICENSE" in content:
                    return "Unlicense"
                return "See LICENSE file"
            except (OSError, UnicodeDecodeError):
                pass

    # Check config files
    if "package.json" in configs:
        try:
            pkg = json.loads(configs["package.json"])
            if "license" in pkg:
                return pkg["license"]
        except (json.JSONDecodeError, KeyError):
            pass

    if "Cargo.toml" in configs:
        match = re.search(r'license\s*=\s*"([^"]+)"', configs["Cargo.toml"])
        if match:
            return match.group(1)

    if "setup.py" in configs:
        match = re.search(r"license\s*=\s*['\"]([^'\"]+)['\"]", configs["setup.py"])
        if match:
            return match.group(1)

    return ""


def detect_repo_url(project_dir, configs):
    """Detect repository URL from git remote or config."""
    # Try git remote
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, cwd=project_dir, timeout=10
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            # Convert SSH to HTTPS
            if url.startswith("git@"):
                url = url.replace(":", "/").replace("git@", "https://")
            if url.endswith(".git"):
                url = url[:-4]
            return url
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Try package.json
    if "package.json" in configs:
        try:
            pkg = json.loads(configs["package.json"])
            repo = pkg.get("repository")
            if isinstance(repo, str):
                return repo
            if isinstance(repo, dict) and "url" in repo:
                return repo["url"]
        except (json.JSONDecodeError, KeyError):
            pass

    return ""


def detect_dependencies(configs):
    """Detect dependencies from config files."""
    deps = []

    if "requirements.txt" in configs:
        for line in configs["requirements.txt"].strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("-"):
                # Extract package name (before version specifier)
                name = re.split(r"[><=!~\[]", line)[0].strip()
                if name:
                    deps.append(name)

    if "package.json" in configs:
        try:
            pkg = json.loads(configs["package.json"])
            deps.extend(pkg.get("dependencies", {}).keys())
        except (json.JSONDecodeError, KeyError):
            pass

    if "Cargo.toml" in configs:
        # Simple regex for [dependencies] section
        in_deps = False
        for line in configs["Cargo.toml"].split("\n"):
            if line.strip() == "[dependencies]":
                in_deps = True
                continue
            if in_deps:
                if line.strip().startswith("["):
                    break
                match = re.match(r"^(\w[\w-]*)\s*=", line.strip())
                if match:
                    deps.append(match.group(1))

    if "go.mod" in configs:
        for line in configs["go.mod"].split("\n"):
            line = line.strip()
            # Match require block entries
            match = re.match(r"^([^\s]+)\s+", line)
            if match and not line.startswith("module") and not line.startswith("go "):
                name = match.group(1)
                if "/" in name:  # Go module paths contain /
                    deps.append(name.split("/")[-1])

    return deps


def detect_readme(project_dir):
    """Detect existing README and extract summary."""
    for name in ["README.md", "README.rst", "README.txt", "README"]:
        path = os.path.join(project_dir, name)
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                if not content.strip():
                    return False, {}
                # Extract sections (## headings)
                sections = re.findall(r"^#{1,3}\s+(.+)$", content, re.MULTILINE)
                sections = [s.strip() for s in sections]
                return True, {
                    "sections": sections,
                    "line_count": len(content.split("\n")),
                    "filename": name,
                }
            except (OSError, UnicodeDecodeError):
                pass
    return False, {}


def detect_logo(project_dir):
    """Detect logo/banner images in common directories."""
    search_dirs = [
        "assets", "docs/assets", "docs/images", "docs",
        "images", "img", "static", "public",
    ]
    logo_names = [
        "logo.svg", "logo.png", "logo.jpg", "logo.jpeg", "logo.webp",
        "banner.svg", "banner.png", "banner.jpg", "banner.jpeg",
        "icon.svg", "icon.png",
    ]
    for search_dir in search_dirs:
        full_dir = os.path.join(project_dir, search_dir)
        if os.path.isdir(full_dir):
            for logo_name in logo_names:
                path = os.path.join(full_dir, logo_name)
                if os.path.isfile(path):
                    return os.path.relpath(path, project_dir).replace("\\", "/")
    return ""


def detect_ci(project_dir):
    """Detect CI/CD configuration."""
    if os.path.isdir(os.path.join(project_dir, ".github", "workflows")):
        return "github-actions"
    if os.path.isfile(os.path.join(project_dir, ".gitlab-ci.yml")):
        return "gitlab-ci"
    if os.path.isfile(os.path.join(project_dir, "Jenkinsfile")):
        return "jenkins"
    if os.path.isfile(os.path.join(project_dir, ".travis.yml")):
        return "travis-ci"
    if os.path.isfile(os.path.join(project_dir, "azure-pipelines.yml")):
        return "azure-pipelines"
    if os.path.isfile(os.path.join(project_dir, ".circleci", "config.yml")):
        return "circleci"
    return ""


def detect_python_version(configs):
    """Detect Python version requirement."""
    if "setup.py" in configs:
        match = re.search(r"python_requires\s*=\s*['\"]([^'\"]+)['\"]", configs["setup.py"])
        if match:
            return match.group(1)

    if "pyproject.toml" in configs:
        match = re.search(r'requires-python\s*=\s*"([^"]+)"', configs["pyproject.toml"])
        if match:
            return match.group(1)

    return ""


def detect_package_manager(configs):
    """Detect package manager from config files."""
    if "package.json" in configs:
        if "pnpm-lock.yaml" in configs:
            return "pnpm"
        if "yarn.lock" in configs:
            return "yarn"
        return "npm"
    if "Cargo.toml" in configs:
        return "cargo"
    if "go.mod" in configs:
        return "go-modules"
    if "pyproject.toml" in configs:
        if "[tool.poetry]" in configs["pyproject.toml"]:
            return "poetry"
        if "[project]" in configs["pyproject.toml"]:
            return "pip"
    if "setup.py" in configs or "requirements.txt" in configs:
        return "pip"
    return ""


def detect_project(project_dir):
    """Main detection function. Returns dict with all metadata."""
    project_dir = os.path.abspath(project_dir)

    # Load config files
    config_files = [
        "package.json", "setup.py", "pyproject.toml", "Cargo.toml",
        "go.mod", "requirements.txt", "yarn.lock", "pnpm-lock.yaml",
    ]
    configs = {}
    for name in config_files:
        path = os.path.join(project_dir, name)
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    configs[name] = f.read()
            except OSError:
                pass

    # Read README if exists
    has_readme, readme_summary = detect_readme(project_dir)
    readme_content = ""
    if has_readme:
        for name in ["README.md", "README.rst", "README.txt", "README"]:
            path = os.path.join(project_dir, name)
            if os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        readme_content = f.read()
                except OSError:
                    pass
                break

    return {
        "name": detect_name(project_dir, configs),
        "description": detect_description(configs, readme_content),
        "language": detect_language(project_dir),
        "license": detect_license(project_dir, configs),
        "repo_url": detect_repo_url(project_dir, configs),
        "dependencies": detect_dependencies(configs),
        "has_readme": has_readme,
        "readme_summary": readme_summary,
        "logo_path": detect_logo(project_dir),
        "ci_type": detect_ci(project_dir),
        "python_version": detect_python_version(configs),
        "package_manager": detect_package_manager(configs),
    }


def main():
    project_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    if not os.path.isdir(project_dir):
        print(json.dumps({"error": f"Directory not found: {project_dir}"}))
        sys.exit(1)

    result = detect_project(project_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd E:/gemini/antigravity/zaynzhu-skills
python skills/readme-creater/scripts/test_detect_project.py
```

Expected: All 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/readme-creater/scripts/
git commit -m "feat(readme-creator): add detect_project.py with tests

Project metadata detection script supporting Python, Node.js, Rust,
Go, and other ecosystems. Extracts name, description, language,
license, dependencies, README structure, logo, and CI config."
```

---

### Task 3: Create badge-templates.md

**Files:**
- Create: `skills/readme-creater/references/badge-templates.md`

This reference file contains 30+ shields.io badge templates organized by category. Each entry includes the badge name, Markdown code with placeholders, applicable scenario, and supported styles.

- [ ] **Step 1: Write badge-templates.md**

Create `skills/readme-creater/references/badge-templates.md`:

```markdown
# Badge Templates

Shields.io badge templates for README generation. Replace `{{OWNER}}`, `{{REPO}}`, and other placeholders with actual values.

## Badge Style Configuration

Supported styles (append `?style=<style>` to any shields.io URL):
- `flat` — Default, clean look
- `for-the-badge` — Modern, bold, uppercase (recommended for stunning READMEs)
- `flat-square` — Squared edges
- `social` — Social media style with icon

Default style for this skill: `for-the-badge`

---

## Basic Badges

### License
```markdown
[![License](https://img.shields.io/github/license/{{OWNER}}/{{REPO}}?style=for-the-badge)](LICENSE)
```
Scenario: Always include. Links to LICENSE file.

### GitHub Stars
```markdown
[![Stars](https://img.shields.io/github/stars/{{OWNER}}/{{REPO}}?style=for-the-badge)](https://github.com/{{OWNER}}/{{REPO}}/stargazers)
```
Scenario: GitHub-hosted projects.

### GitHub Forks
```markdown
[![Forks](https://img.shields.io/github/forks/{{OWNER}}/{{REPO}}?style=for-the-badge)](https://github.com/{{OWNER}}/{{REPO}}/network/members)
```
Scenario: GitHub-hosted projects.

### GitHub Issues
```markdown
[![Issues](https://img.shields.io/github/issues/{{OWNER}}/{{REPO}}?style=for-the-badge)](https://github.com/{{OWNER}}/{{REPO}}/issues)
```
Scenario: Projects accepting issue reports.

### Open Issues
```markdown
[![Open Issues](https://img.shields.io/github/issues-raw/{{OWNER}}/{{REPO}}?style=for-the-badge&color=yellow)](https://github.com/{{OWNER}}/{{REPO}}/issues)
```
Scenario: Highlight open issue count.

### Pull Requests
```markdown
[![PRs](https://img.shields.io/github/issues-pr/{{OWNER}}/{{REPO}}?style=for-the-badge)](https://github.com/{{OWNER}}/{{REPO}}/pulls)
```
Scenario: Projects accepting contributions.

### Last Commit
```markdown
[![Last Commit](https://img.shields.io/github/last-commit/{{OWNER}}/{{REPO}}?style=for-the-badge)](https://github.com/{{OWNER}}/{{REPO}}/commits)
```
Scenario: Show project is actively maintained.

### GitHub Release
```markdown
[![Release](https://img.shields.io/github/v/release/{{OWNER}}/{{REPO}}?style=for-the-badge)](https://github.com/{{OWNER}}/{{REPO}}/releases)
```
Scenario: Projects with versioned releases.

---

## Language / Package Manager Badges

### PyPI Version
```markdown
[![PyPI](https://img.shields.io/pypi/v/{{PACKAGE_NAME}}?style=for-the-badge)](https://pypi.org/project/{{PACKAGE_NAME}}/)
```
Scenario: Python packages published to PyPI.

### PyPI Downloads
```markdown
[![Downloads](https://img.shields.io/pypi/dm/{{PACKAGE_NAME}}?style=for-the-badge)](https://pypi.org/project/{{PACKAGE_NAME}}/)
```
Scenario: Popular Python packages.

### Python Version
```markdown
[![Python](https://img.shields.io/pypi/pyversions/{{PACKAGE_NAME}}?style=for-the-badge)](https://pypi.org/project/{{PACKAGE_NAME}}/)
```
Scenario: Python packages, shows supported versions.

### npm Version
```markdown
[![npm](https://img.shields.io/npm/v/{{PACKAGE_NAME}}?style=for-the-badge)](https://www.npmjs.com/package/{{PACKAGE_NAME}})
```
Scenario: Node.js packages published to npm.

### npm Downloads
```markdown
[![npm Downloads](https://img.shields.io/npm/dm/{{PACKAGE_NAME}}?style=for-the-badge)](https://www.npmjs.com/package/{{PACKAGE_NAME}})
```
Scenario: Popular npm packages.

### Crates.io Version
```markdown
[![Crates.io](https://img.shields.io/crates/v/{{CRATE_NAME}}?style=for-the-badge)](https://crates.io/crates/{{CRATE_NAME}})
```
Scenario: Rust crates published to crates.io.

### Go Reference
```markdown
[![Go Reference](https://img.shields.io/badge/go-reference-007d9c?style=for-the-badge&logo=go)](https://pkg.go.dev/{{MODULE_PATH}})
```
Scenario: Go modules.

---

## CI/CD Badges

### GitHub Actions
```markdown
[![CI](https://img.shields.io/github/actions/workflow/status/{{OWNER}}/{{REPO}}/ci.yml?style=for-the-badge&label=CI)](https://github.com/{{OWNER}}/{{REPO}}/actions/workflows/ci.yml)
```
Scenario: Projects using GitHub Actions. Replace `ci.yml` with actual workflow filename.

### GitLab CI
```markdown
[![Pipeline](https://img.shields.io/gitlab/pipeline/{{OWNER}}/{{REPO}}?style=for-the-badge&logo=gitlab)](https://gitlab.com/{{OWNER}}/{{REPO}}/pipelines)
```
Scenario: Projects using GitLab CI.

### Codecov
```markdown
[![Coverage](https://img.shields.io/codecov/c/github/{{OWNER}}/{{REPO}}?style=for-the-badge&logo=codecov)](https://codecov.io/gh/{{OWNER}}/{{REPO}})
```
Scenario: Projects with code coverage reporting.

---

## Community Badges

### Discord
```markdown
[![Discord](https://img.shields.io/badge/Discord-Join%20Server-5865F2?style=for-the-badge&logo=discord&logoColor=white)]({{DISCORD_URL}})
```
Scenario: Projects with Discord community.

### Twitter / X
```markdown
[![Twitter](https://img.shields.io/badge/Twitter-Follow-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white)](https://twitter.com/{{HANDLE}})
```
Scenario: Projects with Twitter presence.

### LinkedIn
```markdown
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)]({{LINKEDIN_URL}})
```
Scenario: Professional/corporate projects.

### Blog
```markdown
[![Blog](https://img.shields.io/badge/Blog-Read-FC801D?style=for-the-badge)]({{BLOG_URL}})
```
Scenario: Projects with accompanying blog.

### Documentation
```markdown
[![Docs](https://img.shields.io/badge/Docs-Read%20Now-brightgreen?style=for-the-badge)]({{DOCS_URL}})
```
Scenario: Projects with documentation site.

---

## Quality Badges

### Code Style (Black)
```markdown
[![Code Style](https://img.shields.io/badge/code%20style-black-000000?style=for-the-badge)](https://github.com/psf/black)
```
Scenario: Python projects using Black formatter.

### Code Style (Prettier)
```markdown
[![Code Style](https://img.shields.io/badge/code%20style-prettier-ff69b4?style=for-the-badge)](https://prettier.io)
```
Scenario: JS/TS projects using Prettier.

### PRs Welcome
```markdown
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen?style=for-the-badge)](https://github.com/{{OWNER}}/{{REPO}}/pulls)
```
Scenario: Open source projects accepting contributions.

### Maintained
```markdown
[![Maintained](https://img.shields.io/badge/Maintained-Yes-brightgreen?style=for-the-badge)](https://github.com/{{OWNER}}/{{REPO}}/commits)
```
Scenario: Actively maintained projects.

### Made with Love
```markdown
[![Made with Love](https://img.shields.io/badge/Made%20with-%E2%9D%A4-red?style=for-the-badge)](https://github.com/{{OWNER}})
```
Scenario: Personal projects, adds warmth.

---

## Special Elements

### Star History Chart
```markdown
## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos={{OWNER}}/{{REPO}}&type=Date)](https://star-history.com/#{{OWNER}}/{{REPO}}&Date)
```
Scenario: GitHub projects with growing community. Place near bottom of README.

### Contributors (contrib.rocks)
```markdown
## 🙏 Contributors

<a href="https://github.com/{{OWNER}}/{{REPO}}/graphs/contributors">
  <img src="https://contrib.rocks/image?repo={{OWNER}}/{{REPO}}" />
</a>
```
Scenario: Projects with multiple contributors. Place near bottom.

### Sponsor Badge
```markdown
[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-red?style=for-the-badge)]({{SPONSOR_URL}})
```
Scenario: Projects accepting sponsorship.

---

## Recommended Badge Combinations

### Minimal (4 badges)
License + Stars + Issues + Documentation

### Standard (6 badges)
License + Stars + Forks + Issues + CI Status + Documentation

### Full (8-10 badges)
License + Stars + Forks + Issues + PRs + CI Status + PyPI/npm + Documentation + Discord + Code Style
```

- [ ] **Step 2: Commit**

```bash
git add skills/readme-creater/references/badge-templates.md
git commit -m "feat(readme-creator): add badge templates reference

30+ shields.io badge templates organized by category: basic,
language/package, CI/CD, community, quality, and special elements.
Includes style configuration and recommended combinations."
```

---

### Task 4: Create section-templates.md

**Files:**
- Create: `skills/readme-creater/references/section-templates.md`

- [ ] **Step 1: Write section-templates.md**

Create `skills/readme-creater/references/section-templates.md`:

```markdown
# Section Templates

README section writing templates. Each template includes the section structure, placeholder format, and an example.

---

## Logo / Header

### With Real Logo
```markdown
<div align="center">

[![Logo]({{LOGO_PATH}})]({{DOCS_URL}})

# {{PROJECT_NAME}}

**{{TAGLINE}}**

[{{NAV_LINKS}}]

</div>
```

### Emoji Fallback (No Logo)
```markdown
<div align="center">

# {{EMOJI}} {{PROJECT_NAME}}

**{{TAGLINE}}**

[Homepage]({{HOMEPAGE_URL}) | [Documentation]({{DOCS_URL}}) | [Changelog]({{CHANGELOG_URL}})

</div>
```

Use `references/logo-fallback.md` to select the emoji based on project language.

---

## Language Switcher

```markdown
<div align="center">

[中文](README.md) | [English](README_EN.md)

</div>
```

Place immediately after the header. Only include when generating bilingual READMEs.

---

## Badges Row

```markdown
<div align="center">

{{BADGE_MARKDOWN}}

</div>
```

Place after language switcher. Use `references/badge-templates.md` to select badges.
All badges should be wrapped in a centered div for visual alignment.

---

## Tagline

One sentence describing the project. Keep it under 120 characters.

### Patterns:
- **What it is**: "{{Project}} is a {{type}} for {{audience}} that {{benefit}}."
- **Action-oriented**: "{{Verb}} {{object}} with {{project}} — {{benefit}}."
- **Problem-first**: "Tired of {{pain}}? {{Project}} {{solution}}."

---

## Introduction (Blockquote)

```markdown
> {{PROJECT_NAME}} is a {{TYPE}} that {{CORE_CAPABILITY}}.
> It {{KEY_BENEFIT_1}} and {{KEY_BENEFIT_2}}.
>
> Built for {{TARGET_AUDIENCE}} who need {{USE_CASE}}.
```

Use GitHub admonition syntax when appropriate:
- `> [!TIP]` for helpful information
- `> [!NOTE]` for important context
- `> [!WARNING]` for caveats

---

## ✨ Features

```markdown
## ✨ Features

- **{{Feature 1}}** — {{Description}}
- **{{Feature 2}}** — {{Description}}
- **{{Feature 3}}** — {{Description}}
- **{{Feature 4}}** — {{Description}}
- **{{Feature 5}}** — {{Description}}
```

Keep to 5-8 features. Lead with the most impressive differentiator.

---

## 🚀 Quick Start

```markdown
## 🚀 Quick Start

### Installation

\`\`\`bash
{{INSTALL_COMMAND}}
\`\`\`

### Minimal Example

\`\`\`{{LANG}}
{{MINIMAL_CODE_EXAMPLE}}
\`\`\`
```

Show the absolute minimum to get something working. Detailed usage goes in the Usage section.

---

## 📦 Installation

```markdown
## 📦 Installation

### {{Method 1 (e.g., pip)}}

\`\`\`bash
{{INSTALL_COMMAND_1}}
\`\`\`

### {{Method 2 (e.g., from source)}}

\`\`\`bash
git clone {{REPO_URL}}
cd {{PROJECT_NAME}}
{{INSTALL_COMMAND_2}}
\`\`\`

### Requirements

- {{Requirement 1}}
- {{Requirement 2}}
```

Include multiple installation methods when applicable (pip, conda, docker, from source).

---

## 💡 Usage

```markdown
## 💡 Usage

### {{Use Case 1}}

\`\`\`{{LANG}}
{{CODE_EXAMPLE_1}}
\`\`\`

### {{Use Case 2}}

\`\`\`{{LANG}}
{{CODE_EXAMPLE_2}}
\`\`\`

For more examples, see the [documentation]({{DOCS_URL}}).
```

Show 2-3 common use cases with real code. Each example should be self-contained.

---

## 📚 Documentation

```markdown
## 📚 Documentation

| Topic | Description |
|-------|-------------|
| [Getting Started]({{URL}}) | Installation and first steps |
| [API Reference]({{URL}}) | Complete API documentation |
| [Examples]({{URL}}) | Code examples and tutorials |
| [FAQ]({{URL}}) | Frequently asked questions |
```

Use a table format for quick scanning. Link to actual docs when available.

---

## 🤝 Contributing

```markdown
## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide]({{CONTRIBUTING_URL}}) before submitting a PR.

### Quick Start

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

\`\`\`bash
git clone {{REPO_URL}}
cd {{PROJECT_NAME}}
{{DEV_INSTALL_COMMAND}}
{{RUN_TESTS_COMMAND}}
\`\`\`
```

---

## 💬 Community

```markdown
## 💬 Community

- [Discord]({{DISCORD_URL}}) — Join our community
- [GitHub Discussions]({{DISCUSSIONS_URL}}) — Ask questions and share ideas
- [Twitter/X]({{TWITTER_URL}}) — Follow for updates
- [Stack Overflow]({{SO_URL}}) — Tag: `{{TAG}}`
```

Only include links that actually exist. Don't add placeholder community links.

---

## ⭐ Star History

```markdown
## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos={{OWNER}}/{{REPO}}&type=Date)](https://star-history.com/#{{OWNER}}/{{REPO}}&Date)
```

Place near the bottom. Only for GitHub-hosted projects.

---

## 🙏 Contributors

```markdown
## 🙏 Contributors

<a href="https://github.com/{{OWNER}}/{{REPO}}/graphs/contributors">
  <img src="https://contrib.rocks/image?repo={{OWNER}}/{{REPO}}" />
</a>
```

Place near the bottom. Auto-generates contributor avatar grid.

---

## 📄 License

```markdown
## 📄 License

This project is licensed under the {{LICENSE_NAME}} License — see the [LICENSE](LICENSE) file for details.
```

Always include. Link to the actual LICENSE file.

---

## Comparison Table (Optional)

```markdown
## 🔄 How {{PROJECT}} Compares

| Feature | {{PROJECT}} | {{Competitor 1}} | {{Competitor 2}} |
|---------|:-----------:|:----------------:|:----------------:|
| {{Feature 1}} | ✅ | ✅ | ❌ |
| {{Feature 2}} | ✅ | ❌ | ✅ |
| {{Feature 3}} | ✅ | ❌ | ❌ |
```

Use sparingly. Only include when you have clear differentiators.

---

## Roadmap (Optional)

```markdown
## 🗺️ Roadmap

| Area | Feature | Status |
|------|---------|--------|
| Core | {{Feature 1}} | ✅ Done |
| Core | {{Feature 2}} | 🚧 In Progress |
| Plugin | {{Feature 3}} | 📋 Planned |
```

---

## FAQ (Optional)

```markdown
## ❓ FAQ

<details>
<summary>{{Question 1}}?</summary>

{{Answer 1}}

</details>

<details>
<summary>{{Question 2}}?</summary>

{{Answer 2}}

</details>
```

Use HTML `<details>` for collapsible FAQ entries.
```

- [ ] **Step 2: Commit**

```bash
git add skills/readme-creater/references/section-templates.md
git commit -m "feat(readme-creator): add section templates reference

Templates for all standard README sections: header, badges, features,
quick start, installation, usage, docs, contributing, community,
star history, contributors, license, plus optional sections."
```

---

### Task 5: Create style-guide.md

**Files:**
- Create: `skills/readme-creater/references/style-guide.md`

- [ ] **Step 1: Write style-guide.md**

Create `skills/readme-creater/references/style-guide.md`:

```markdown
# Style Guide

Visual style specifications for the "stunning full" README style.

---

## Emoji Rules

### Section Headers
Prefix each section header with exactly one relevant emoji:

| Section | Emoji |
|---------|-------|
| Features | ✨ |
| Quick Start | 🚀 |
| Installation | 📦 |
| Usage | 💡 |
| Documentation | 📚 |
| Contributing | 🤝 |
| Community | 💬 |
| Star History | ⭐ |
| Contributors | 🙏 |
| License | 📄 |
| Comparison | 🔄 |
| Roadmap | 🗺️ |
| FAQ | ❓ |
| Changelog | 📝 |
| Security | 🔒 |

### Rules
- Maximum 1 emoji per header
- Do NOT use emojis in body text (except in tables for status indicators: ✅ ❌ 🚧 📋)
- Do NOT use emojis in code blocks
- Emojis should enhance scanning, not decorate

---

## Typography

### Horizontal Rules
Use `---` (three dashes) to separate major sections. Place one blank line before and after.

### Spacing
- One blank line before each `##` header
- One blank line after each `##` header
- One blank line between paragraphs
- No trailing whitespace

### Code Blocks
- Always specify the language: ` ```python `, ` ```bash `, ` ```json `
- Use ` ```bash ` for shell commands
- Use ` ``` ` (no language) only for generic text blocks
- Inline code for file names, function names, variable names: `setup.py`, `detect_name()`

### Links
- Use descriptive link text, never "click here" or bare URLs
- Format: `[descriptive text](url)`
- For external links, consider adding the domain: `[GitHub](https://github.com)`

---

## Centered Elements

Use `<div align="center">` for:
- Logo/header area
- Badge rows
- Language switcher

Close with `</div>` after each centered block.

Example:
```markdown
<div align="center">

# 🐍 My Project

**A brief tagline**

[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

</div>
```

---

## Admonitions

Use GitHub admonition syntax for callouts:

```markdown
> [!NOTE]
> Useful information that users should know.

> [!TIP]
> Helpful advice for doing something better.

> [!IMPORTANT]
> Critical information necessary for users to succeed.

> [!WARNING]
> Urgent info that needs immediate user attention.

> [!CAUTION]
> Negative potential consequences of an action.
```

Use sparingly. Maximum 2-3 admonitions per README.

---

## Tables

### Alignment
- Left-align text columns
- Center-align status/icon columns
- Right-align numeric columns

### Status Indicators
Use emoji for status in tables:
- ✅ Done / Supported / Yes
- ❌ Not done / Not supported / No
- 🚧 In progress
- 📋 Planned
- ⚠️ Partial / Caveat

Example:
```markdown
| Feature | Status |
|---------|--------|
| Authentication | ✅ Done |
| File Upload | 🚧 In Progress |
| AI Integration | 📋 Planned |
```

---

## Bilingual Format

### File Naming
- Primary language: `README.md`
- Secondary language: `README_EN.md` (if primary is Chinese) or `README_CN.md` (if primary is English)

### Language Switcher
Place immediately after the header, before badges:

```markdown
<div align="center">

[中文](README.md) | [English](README_EN.md)

</div>
```

### Content Parity
Both language versions MUST have:
- Same section structure (same headers in same order)
- Same badge set
- Same code examples (code doesn't need translation)
- Equivalent information (not word-for-word translation)

### Translation Notes
- Technical terms can stay in English in Chinese version (e.g., API, SDK, Docker)
- Code comments should be in the primary language
- Keep URLs, file paths, and command examples identical

---

## README Length Guidelines

| Project Type | Recommended Length |
|-------------|-------------------|
| Single-file script | 50-100 lines |
| Small library | 100-200 lines |
| Medium project | 200-400 lines |
| Large framework | 400-600 lines |
| Enterprise platform | 600-1000 lines |

If approaching 500+ lines, consider moving detailed docs to a separate documentation site and linking from the README.
```

- [ ] **Step 2: Commit**

```bash
git add skills/readme-creater/references/style-guide.md
git commit -m "feat(readme-creator): add style guide reference

Visual style specifications for emoji usage, typography, centered
elements, admonitions, tables, bilingual formatting, and README
length guidelines."
```

---

### Task 6: Create logo-fallback.md

**Files:**
- Create: `skills/readme-creater/references/logo-fallback.md`

- [ ] **Step 1: Write logo-fallback.md**

Create `skills/readme-creater/references/logo-fallback.md`:

```markdown
# Logo Fallback Rules

When no logo/banner image is detected in the project, use an emoji-enhanced H1 heading as the visual header.

---

## Language-to-Emoji Mapping

| Language | Emoji | Usage |
|----------|-------|-------|
| Python | 🐍 | `# 🐍 Project Name` |
| JavaScript | ⚡ | `# ⚡ Project Name` |
| TypeScript | 💎 | `# 💎 Project Name` |
| Rust | 🦀 | `# 🦀 Project Name` |
| Go | 🔵 | `# 🔵 Project Name` |
| Java | ☕ | `# ☕ Project Name` |
| Ruby | 💎 | `# 💎 Project Name` |
| PHP | 🐘 | `# 🐘 Project Name` |
| C# | 💜 | `# 💜 Project Name` |
| C++ | ⚙️ | `# ⚙️ Project Name` |
| Swift | 🦅 | `# 🦅 Project Name` |
| Kotlin | 🟣 | `# 🟣 Project Name` |
| Dart | 🎯 | `# 🎯 Project Name` |
| Lua | 🌙 | `# 🌙 Project Name` |
| R | 📊 | `# 📊 Project Name` |
| Julia | 🔷 | `# 🔷 Project Name` |
| Zig | ⚡ | `# ⚡ Project Name` |
| Elixir | 💧 | `# 💧 Project Name` |
| Multi-language | 🌐 | `# 🌐 Project Name` |
| Unknown | 📦 | `# 📦 Project Name` |

---

## Category-Based Emoji (Alternative)

If the project type is more recognizable than its language, use a category emoji:

| Category | Emoji | Example |
|----------|-------|-------|
| Web Framework | 🌐 | `# 🌐 Express.js` |
| CLI Tool | 🖥️ | `# 🖥️ My CLI` |
| API | 🔌 | `# 🔌 My API` |
| Database | 🗄️ | `# 🗄️ My DB` |
| AI/ML | 🤖 | `# 🤖 My Model` |
| Chat Bot | 💬 | `# 💬 My Bot` |
| Game | 🎮 | `# 🎮 My Game` |
| Mobile App | 📱 | `# 📱 My App` |
| Browser Extension | 🧩 | `# 🧩 My Extension` |
| DevOps Tool | 🔧 | `# 🔧 My Tool` |
| Security Tool | 🔒 | `# 🔒 My Scanner` |
| Data Tool | 📊 | `# 📊 My Analyzer` |
| Documentation | 📖 | `# 📖 My Docs` |
| Testing Tool | 🧪 | `# 🧪 My Test Lib` |

---

## Full Header Template

```markdown
<div align="center">

# {{EMOJI}} {{PROJECT_NAME}}

**{{TAGLINE}}**

{{NAV_LINKS}}

</div>
```

### Example (Python project, no logo)

```markdown
<div align="center">

# 🐍 My Awesome Tool

**A powerful CLI tool for automating mundane tasks**

[Documentation](https://docs.example.com) | [PyPI](https://pypi.org/project/my-awesome-tool/) | [GitHub](https://github.com/user/my-awesome-tool)

</div>
```

---

## ASCII Art Banner (Optional)

For projects that want extra visual impact, a simple ASCII art banner can be generated. Use monospace font and keep it compact:

```
 ███╗   ███╗██╗   ██╗
 ████╗ ████║╚██╗ ██╔╝
 ██╔████╔██║ ╚████╔╝
 ██║╚██╔╝██║  ╚██╔╝
 ██║ ╚═╝ ██║   ██║
 ╚═╝     ╚═╝   ╚═╝
```

Rules:
- Only use for personal/brand projects
- Maximum 6 lines tall
- Must render correctly in monospace font
- Place above the project name
- Wrap in `<pre>` tags for proper rendering

---

## Decision Flow

```
1. Does the project have a logo/banner image?
   ├── Yes → Use real logo: [![Logo](path)](url)
   └── No → Continue to step 2

2. Is the project language clearly identifiable?
   ├── Yes → Use language emoji from mapping table
   └── No → Continue to step 3

3. Is the project category identifiable?
   ├── Yes → Use category emoji
   └── No → Use 📦 as default
```
```

- [ ] **Step 2: Commit**

```bash
git add skills/readme-creater/references/logo-fallback.md
git commit -m "feat(readme-creator): add logo fallback reference

Emoji fallback rules for projects without logo images. Includes
language-to-emoji mapping, category-based alternatives, ASCII art
banner guidelines, and decision flow."
```

---

### Task 7: Write SKILL.md

**Files:**
- Create: `skills/readme-creater/SKILL.md`

This is the main instruction file. It defines the 5-phase flow, references the other files, and contains all the logic for creating/improving READMEs. Target: ~450 lines.

- [ ] **Step 1: Write SKILL.md**

Create `skills/readme-creater/SKILL.md`:

```markdown
---
name: readme-creator
description: |
  通用 README 创建器 + 改进器。从零为项目生成炫酷、专业的 README（含徽章、Star History、贡献者网格、中英双语），也能分析并改进现有 README。
  触发词：创建 readme、改进 readme、生成 readme、写 readme、优化 readme、write readme、improve readme、generate readme、/readme。
  即使用户只是说"帮我写个 readme"、"这个项目的文档太丑了"、"给项目加个专业的 readme"，只要上下文涉及项目文档生成或改进，就应该触发。
---

# README Creator

你是一个专业的 README 工程师，帮助用户创建和改进项目 README。

参考 QwenPaw、OpenClaw、CrewAI 等热门开源项目的设计模式，生成视觉效果出众、结构完整的 README。

## 核心理念

好的 README 是项目的门面——它决定了第一印象。一个炫酷的 README 不仅要信息完整，还要视觉上引人入胜：醒目的 logo、整齐的徽章、清晰的结构、恰到好处的 emoji。

## 流程概览

```
⬜ Phase 1: 项目检测  ⬜ Phase 2: 现有 README 分析  ⬜ Phase 3: 交互确认  ⬜ Phase 4: README 生成  ⬜ Phase 5: 审查与迭代
```

每次回复时在消息顶部展示当前进度。

---

## Phase 1: 项目检测

**目标**: 自动收集项目元数据，减少用户手动输入。

### Step 1: 运行检测脚本

尝试运行 `scripts/detect_project.py`：

```bash
python <skill-path>/scripts/detect_project.py <project-dir>
```

如果脚本不可用（无 Python 环境或脚本报错），降级为手动检测：

### Step 2: 手动检测降级

用以下工具逐项检测：

1. **项目名称**: 用 Glob 找 `package.json`/`setup.py`/`Cargo.toml`/`go.mod`，Read 文件提取 name 字段；找不到则用目录名
2. **描述**: 同上文件中的 description 字段；找不到则读 README.md 首段
3. **主语言**: 用 Glob 统计各扩展名文件数量（`.py`→Python, `.ts`→TypeScript, `.rs`→Rust 等）
4. **许可证**: 用 Glob 找 `LICENSE`/`LICENSE.md`/`LICENSE.txt`，Read 文件识别类型
5. **仓库 URL**: 用 Bash 运行 `git remote get-url origin`；找不到则看 `package.json` 的 repository 字段
6. **依赖**: 用 Glob 找 `requirements.txt`/`package.json`/`Cargo.toml`，Read 文件提取
7. **已有 README**: 用 Glob 找 `README.md`/`README.rst`/`README`
8. **Logo**: 用 Glob 扫描 `assets/`、`docs/`、`images/` 中的图片文件（svg/png/jpg）
9. **CI/CD**: 用 Glob 找 `.github/workflows/`、`.gitlab-ci.yml`、`Jenkinsfile`

### Step 3: 展示检测结果

向用户展示检测到的信息摘要，格式如下：

```
📋 项目检测结果

| 项目 | 值 |
|------|-----|
| 名称 | {{name}} |
| 描述 | {{description}} |
| 主语言 | {{language}} |
| 许可证 | {{license}} |
| 仓库 | {{repo_url}} |
| 依赖 | {{dependencies}} |
| 已有 README | {{has_readme}} |
| Logo | {{logo_path}} |
| CI/CD | {{ci_type}} |
| 包管理 | {{package_manager}} |

请确认以上信息，或告诉我需要修正的部分。
```

等待用户确认后进入下一阶段。

---

## Phase 2: 现有 README 分析

**仅在检测到已有 README 时执行此阶段。** 如果没有 README，直接跳到 Phase 3。

### Step 1: 读取并分析

读取现有 README 全文，提取：
- 所有段落标题（`##` 级别）
- 每个段落的内容摘要（一句话）
- 总行数

### Step 2: 逐段确认

向用户展示段落列表，逐段询问：

```
📄 现有 README 分析

发现 {{N}} 个段落，请告诉我每个段落的处理方式：

| # | 段落 | 摘要 | 处理方式 |
|---|------|------|---------|
| 1 | {{标题}} | {{摘要}} | 保留 / 重写 / 删除 |
| 2 | {{标题}} | {{摘要}} | 保留 / 重写 / 删除 |
| ... | | | |

请告诉我每个段落的处理方式（如 "1保留, 2重写, 3删除"），或说 "全部重写"。
```

### Step 3: 记录偏好

记录用户对每个段落的决定，用于 Phase 4 生成时：
- **保留**: 原样嵌入新 README 对应位置
- **重写**: 用新模板重写，但保持主题一致
- **删除**: 不包含在新 README 中

---

## Phase 3: 交互确认

通过一系列问题确认 README 的详细配置。使用 AskUserQuestion 工具提问，每次最多问 2 个问题。

### 问题 1: 徽章选择

从 `references/badge-templates.md` 中选择适合项目的徽章，展示推荐组合：

```
🏷️ 徽章推荐（基于检测到的项目信息）

推荐以下徽章组合：
{{根据项目类型列出推荐徽章}}

可选额外徽章：
{{列出其他可用徽章}}

请确认推荐，或告诉我想添加/移除哪些徽章。
```

### 问题 2: Logo 策略

```
🖼️ Logo 策略

检测到的 Logo: {{logo_path 或 "无"}}

选项：
1. 使用检测到的 Logo: {{path}}
2. 使用 emoji 降级（根据语言自动选择 emoji）
3. 我来提供 Logo URL/路径
```

### 问题 3: 语言与风格

```
🌐 语言设置

选项：
1. 中英双语（生成 README.md + README_EN.md）
2. 纯英文
3. 纯中文

🎨 风格设置

选项：
1. 炫酷全面型（徽章 + Star History + 贡献者网格 + emoji）— 推荐
2. 简洁专业型（基本徽章 + 清晰结构）
```

### 问题 4: 额外段落

```
📎 额外段落

以下段落可选添加：
- ⭐ Star History（Star 增长图表）
- 🙏 Contributors（贡献者头像网格）
- 🔄 Comparison（与竞品对比表）
- 🗺️ Roadmap（开发路线图）
- ❓ FAQ（常见问题）

推荐：{{根据项目类型推荐}}

请告诉我想添加哪些。
```

确认所有信息后，进入生成阶段。

---

## Phase 4: README 生成

根据确认的信息生成完整 README。按以下顺序组织内容：

### 生成顺序

1. **Header** — Logo（真实或 emoji 降级）+ 标题 + 导航链接
   - 使用 `references/logo-fallback.md` 选择 emoji
   - 包裹在 `<div align="center">` 中
2. **Language Switcher** — 仅双语模式，`[中文](README.md) | [English](README_EN.md)`
3. **Badges Row** — 用户选择的徽章，包裹在 `<div align="center">` 中
   - 使用 `references/badge-templates.md` 中的模板，替换占位符
4. **Tagline** — 一句话描述（< 120 字符）
5. **Introduction** — `> [!TIP]` blockquote，2-3 句话介绍核心能力
6. **✨ Features** — 5-8 个特性，用 `**粗体**` 标注特性名
7. **🚀 Quick Start** — 安装命令 + 最小代码示例
8. **📦 Installation** — 详细安装步骤（多种方式）
9. **💡 Usage** — 2-3 个使用场景，每个有代码示例
10. **📚 Documentation** — 文档链接表格（如果有文档站）
11. **🤝 Contributing** — 贡献指南
12. **💬 Community** — 社区链接（仅包含实际存在的链接）
13. **⭐ Star History** — star-history.com 图表（仅 GitHub 项目）
14. **🙏 Contributors** — contrib.rocks 网格（仅 GitHub 项目）
15. **📄 License** — 许可证声明

### 双语生成

如果是双语模式：
- 先生成主语言版本（由用户选择，默认中文）
- 再翻译为副语言版本
- 两个版本结构必须完全一致
- 代码示例保持不变
- 技术术语在中文版中可保留英文

### 边界情况处理

| 场景 | 处理方式 |
|------|---------|
| 空项目（无代码文件） | 只生成 Header + Tagline + License |
| 单文件脚本 | 简化结构，跳过 Documentation/Contributing |
| 无 git 仓库 | 跳过 Stars/Forks/Star History/Contributors 徽章 |
| 无 LICENSE | 跳过 License 徽章，在 README 中提示添加 |
| 用户保留了某些段落 | 将保留内容嵌入新模板对应位置 |

### 写作风格

详细写作规范见 `references/style-guide.md` 和 `references/section-templates.md`。

关键原则：
- 每个段落标题前加 1 个 emoji
- 代码块必须标注语言
- 用 `---` 分隔大段
- 表格对齐整齐
- 链接文字要有描述性

---

## Phase 5: 审查与迭代

### Step 1: 自审

生成完成后，读取生成的 README 进行自审：

1. **链接检查**: 所有徽章 URL 是否正确？仓库 URL 是否匹配？
2. **代码块**: 是否每段代码都有语言标注？
3. **Emoji 一致性**: 每个 `##` 标题前是否都有且只有 1 个 emoji？
4. **结构完整性**: 是否缺少用户要求的段落？
5. **双语一致性**: 中英文版本结构是否完全一致？
6. **占位符检查**: 是否有遗漏的 `{{placeholder}}`？

### Step 2: 展示结果

向用户展示：
- 生成的 README 预览（全文或摘要）
- 自审结果（问题列表，如有）

### Step 3: 迭代修改

等待用户反馈。常见修改：
- 调整措辞
- 增删段落
- 修改徽章
- 调整代码示例

根据反馈修改后重新展示，直到用户满意。

### Step 4: 写入文件

用户确认后，将 README 写入项目根目录：
- 主语言版本: `README.md`
- 副语言版本: `README_EN.md` 或 `README_CN.md`

如果是改进现有 README，先备份原文件为 `README.old.md`。

---

## 引用文件

- `references/badge-templates.md` — shields.io 徽章模板库（30+ 种徽章）
- `references/section-templates.md` — README 各段落的写作模板
- `references/style-guide.md` — 视觉风格指南（emoji、排版、双语格式）
- `references/logo-fallback.md` — emoji 降级 logo 的生成规则
- `scripts/detect_project.py` — 项目元数据自动检测脚本
```

- [ ] **Step 2: Verify line count**

```bash
wc -l skills/readme-creater/SKILL.md
```

Expected: ~400-480 lines (under 500 line limit).

- [ ] **Step 3: Commit**

```bash
git add skills/readme-creater/SKILL.md
git commit -m "feat(readme-creator): add SKILL.md main instruction file

5-phase flow: project detection, existing README analysis, interactive
confirmation, README generation, and review/iteration. Supports
bilingual output, smart logo fallback, and stunning visual style."
```

---

### Task 8: Update README.md and CLAUDE.md Index

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add skill to README.md index table**

In the skill index table in `README.md`, add a new row after the last skill entry:

```markdown
| `readme-creater` | readme-creator | README 创建器 + 改进器，生成炫酷专业的项目文档 | experimental |
```

Also add a row to the documentation table:

```markdown
| [readme-creater](docs/readme-creater.md) | readme-creator 使用文档 |
```

Also add a row to the dependency table:

```markdown
| readme-creater | Python >= 3.8（可选，用于自动检测脚本） |
```

- [ ] **Step 2: Add skill to CLAUDE.md inventory table**

In the skill inventory table in `CLAUDE.md`, add a new row:

```markdown
| `readme-creater` | readme-creator | README 创建/改进 | Python >= 3.8（可选） |
```

- [ ] **Step 3: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs: add readme-creator to skill index and inventory"
```

---

### Task 9: Self-Review and Verification

**Files:**
- Review: All files in `skills/readme-creater/`

- [ ] **Step 1: Verify all files exist**

```bash
find skills/readme-creater/ -type f | sort
```

Expected output:
```
skills/readme-creater/SKILL.md
skills/readme-creater/references/badge-templates.md
skills/readme-creater/references/logo-fallback.md
skills/readme-creater/references/section-templates.md
skills/readme-creater/references/style-guide.md
skills/readme-creater/scripts/detect_project.py
skills/readme-creater/scripts/test_detect_project.py
```

- [ ] **Step 2: Run detect_project.py tests one final time**

```bash
python skills/readme-creater/scripts/test_detect_project.py
```

Expected: All 8 tests PASS.

- [ ] **Step 3: Verify SKILL.md line count**

```bash
wc -l skills/readme-creater/SKILL.md
```

Expected: Under 500 lines.

- [ ] **Step 4: Check for dangling references**

Verify every file referenced in SKILL.md exists:
- `references/badge-templates.md` ✓
- `references/section-templates.md` ✓
- `references/style-guide.md` ✓
- `references/logo-fallback.md` ✓
- `scripts/detect_project.py` ✓

- [ ] **Step 5: Test detect_project.py on this project**

```bash
python skills/readme-creater/scripts/detect_project.py E:/gemini/antigravity/zaynzhu-skills
```

Expected: Valid JSON output with project metadata.

- [ ] **Step 6: Final commit**

```bash
git add -A skills/readme-creater/
git commit -m "feat(readme-creator): complete skill implementation

Universal README creator/improver with:
- Auto project metadata detection (Python, Node, Rust, Go)
- Existing README analysis with per-section keep/rewrite/delete
- 30+ badge templates with shields.io
- Stunning visual style with emoji headers, Star History, contributors
- Bilingual support (Chinese + English)
- Smart logo detection with emoji fallback"
```
