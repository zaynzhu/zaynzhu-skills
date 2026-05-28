"""Scan a project directory and output structured JSON with project metadata.

Usage:
    python detect_project.py [directory]

If no directory is given, the current working directory is used.
Output is always valid JSON on stdout.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# Directories to skip when counting source files
SKIP_DIRS = {"node_modules", ".git", "__pycache__", "venv", ".venv",
             "env", ".env", ".tox", "dist", "build", "target", ".idea",
             ".vscode", "vendor"}

# Extension → language mapping
EXT_LANG: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".rs": "Rust",
    ".go": "Go",
    ".java": "Java",
    ".rb": "Ruby",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C",
    ".hpp": "C++",
    ".cs": "C#",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".php": "PHP",
    ".lua": "Lua",
    ".sh": "Shell",
    ".zig": "Zig",
}


def detect(root: Path) -> dict[str, Any]:
    """Return a metadata dict for the project at *root*."""
    result: dict[str, Any] = {
        "name": root.name,
        "description": "",
        "language": "Unknown",
        "license": "",
        "repo_url": "",
        "dependencies": [],
        "has_readme": False,
        "readme_summary": {"sections": [], "line_count": 0},
        "logo_path": None,
        "ci_type": None,
        "python_version": "",
        "package_manager": "",
    }

    # ---- config files -------------------------------------------------------
    _detect_from_configs(root, result)

    # ---- language (by file extension counting) -------------------------------
    _detect_language(root, result)

    # ---- license -------------------------------------------------------------
    _detect_license(root, result)

    # ---- repo url ------------------------------------------------------------
    _detect_repo_url(root, result)

    # ---- readme --------------------------------------------------------------
    _detect_readme(root, result)

    # ---- logo ----------------------------------------------------------------
    _detect_logo(root, result)

    # ---- CI ------------------------------------------------------------------
    _detect_ci(root, result)

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _detect_from_configs(root: Path, result: dict[str, Any]) -> None:
    """Detect metadata from project config files."""

    # -- package.json (Node) --------------------------------------------------
    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
            result["name"] = pkg.get("name", result["name"])
            result["description"] = pkg.get("description", result["description"])
            deps: dict = {}
            deps.update(pkg.get("dependencies", {}))
            deps.update(pkg.get("devDependencies", {}))
            result["dependencies"] = sorted(deps.keys())
            repo = pkg.get("repository")
            if isinstance(repo, dict) and repo.get("url"):
                result["repo_url"] = _clean_git_url(repo["url"])
            elif isinstance(repo, str):
                result["repo_url"] = _clean_git_url(repo)
            # package manager
            if (root / "pnpm-lock.yaml").exists():
                result["package_manager"] = "pnpm"
            elif (root / "yarn.lock").exists():
                result["package_manager"] = "yarn"
            else:
                result["package_manager"] = "npm"
        except (json.JSONDecodeError, OSError):
            pass

    # -- setup.py / pyproject.toml (Python) -----------------------------------
    setup_py = root / "setup.py"
    if setup_py.exists():
        _parse_setup_py(setup_py, result)

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        _parse_pyproject_toml(pyproject, result)

    # -- requirements.txt (Python) --------------------------------------------
    req_txt = root / "requirements.txt"
    if req_txt.exists():
        try:
            lines = req_txt.read_text(encoding="utf-8").splitlines()
            reqs = _parse_requirements(lines)
            existing = set(result["dependencies"])
            for r in reqs:
                if r not in existing:
                    result["dependencies"].append(r)
            result["dependencies"] = sorted(result["dependencies"])
        except OSError:
            pass

    # -- Cargo.toml (Rust) ----------------------------------------------------
    cargo = root / "Cargo.toml"
    if cargo.exists():
        _parse_cargo_toml(cargo, result)

    # -- go.mod (Go) ----------------------------------------------------------
    go_mod = root / "go.mod"
    if go_mod.exists():
        _parse_go_mod(go_mod, result)


def _parse_setup_py(path: Path, result: dict[str, Any]) -> None:
    """Best-effort extraction from setup.py."""
    try:
        text = path.read_text(encoding="utf-8")
        m = re.search(r"""name\s*=\s*['"]([^'"]+)['"]""", text)
        if m:
            result["name"] = m.group(1)
        m = re.search(r"""description\s*=\s*['"]([^'"]+)['"]""", text)
        if m:
            result["description"] = m.group(1)
        m = re.search(r"""python_requires\s*=\s*['"]([^'"]+)['"]""", text)
        if m:
            result["python_version"] = m.group(1)
        m = re.search(r"""license\s*=\s*['"]([^'"]+)['"]""", text)
        if m and not result["license"]:
            result["license"] = m.group(1)
    except OSError:
        pass


def _parse_pyproject_toml(path: Path, result: dict[str, Any]) -> None:
    """Best-effort extraction from pyproject.toml without toml lib."""
    try:
        text = path.read_text(encoding="utf-8")
        # Try [project] table (PEP 621)
        for key, field in [("name", "name"), ("description", "description"),
                           ("license", "license")]:
            m = re.search(
                rf'^\s*{key}\s*=\s*["\']([^"\']+)["\']',
                text, re.MULTILINE,
            )
            if m and (not result[field] or field == "name"):
                val = m.group(1)
                if field == "license":
                    result["license"] = val
                else:
                    result[field] = val
        # python_requires
        m = re.search(r'requires-python\s*=\s*["\']([^"\']+)["\']', text)
        if m:
            result["python_version"] = m.group(1)
        # dependencies
        deps = _extract_toml_array(text, "dependencies")
        if deps:
            parsed = _parse_requirements(deps)
            existing = set(result["dependencies"])
            for r in parsed:
                if r not in existing:
                    result["dependencies"].append(r)
            result["dependencies"] = sorted(result["dependencies"])
    except OSError:
        pass


def _extract_toml_array(text: str, key: str) -> list[str]:
    """Extract a TOML inline or multi-line array for a given key."""
    pattern = rf'^\s*{key}\s*=\s*\[(.*?)\]'
    m = re.search(pattern, text, re.DOTALL | re.MULTILINE)
    if not m:
        return []
    body = m.group(1)
    items = re.findall(r'["\']([^"\']+)["\']', body)
    return items


def _parse_cargo_toml(path: Path, result: dict[str, Any]) -> None:
    """Extract metadata from Cargo.toml."""
    try:
        text = path.read_text(encoding="utf-8")
        m = re.search(r'^\s*name\s*=\s*"([^"]+)"', text, re.MULTILINE)
        if m:
            result["name"] = m.group(1)
        m = re.search(r'^\s*description\s*=\s*"([^"]+)"', text, re.MULTILINE)
        if m:
            result["description"] = m.group(1)
        m = re.search(r'^\s*license\s*=\s*"([^"]+)"', text, re.MULTILINE)
        if m:
            result["license"] = m.group(1)
        # dependencies
        deps: list[str] = []
        in_deps = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped == "[dependencies]":
                in_deps = True
                continue
            if in_deps:
                if stripped.startswith("["):
                    break
                m = re.match(r'^([a-zA-Z0-9_-]+)\s*=', stripped)
                if m:
                    deps.append(m.group(1))
        if deps:
            result["dependencies"] = sorted(deps)
    except OSError:
        pass


def _parse_go_mod(path: Path, result: dict[str, Any]) -> None:
    """Extract metadata from go.mod."""
    try:
        text = path.read_text(encoding="utf-8")
        # module name → derive project name as last path segment
        m = re.search(r'^module\s+(\S+)', text, re.MULTILINE)
        if m:
            mod = m.group(1)
            result["name"] = mod.rstrip("/").rsplit("/", 1)[-1]
            result["repo_url"] = f"https://{mod}" if not mod.startswith("http") else mod
        m = re.search(r'^go\s+(\S+)', text, re.MULTILINE)
        if m:
            result["python_version"] = f"go{m.group(1)}"
        # dependencies
        deps: list[str] = []
        in_req = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("require"):
                in_req = True
                # inline require like: require github.com/foo v1.0
                inline = re.match(r'require\s+(\S+)\s+', stripped)
                if inline and "(" not in stripped:
                    deps.append(inline.group(1))
                    in_req = False
                continue
            if in_req:
                if stripped == ")":
                    in_req = False
                    continue
                m = re.match(r'^(\S+)\s+', stripped)
                if m:
                    deps.append(m.group(1))
        if deps:
            result["dependencies"] = sorted(deps)
    except OSError:
        pass


def _parse_requirements(lines: list[str]) -> list[str]:
    """Parse requirement lines, stripping version specifiers and comments."""
    reqs: list[str] = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Strip extras like package[extra]
        name = re.split(r'[<>=!\[;@\s]', line)[0]
        if name:
            reqs.append(name)
    return sorted(reqs)


def _clean_git_url(url: str) -> str:
    """Convert SSH git URLs to HTTPS and strip .git suffix."""
    url = url.strip()
    # git@github.com:user/repo.git → https://github.com/user/repo
    m = re.match(r'git@([^:]+):(.+)', url)
    if m:
        url = f"https://{m.group(1)}/{m.group(2)}"
    if url.endswith(".git"):
        url = url[:-4]
    # Remove trailing slash
    return url.rstrip("/")


def _detect_language(root: Path, result: dict[str, Any]) -> None:
    """Count source files by extension to determine the primary language."""
    counter: Counter[str] = Counter()
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune skipped directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            ext = Path(fn).suffix.lower()
            if ext in EXT_LANG:
                counter[EXT_LANG[ext]] += 1
    if counter:
        lang, _count = counter.most_common(1)[0]
        result["language"] = lang


def _detect_license(root: Path, result: dict[str, Any]) -> None:
    """Detect license from LICENSE file content or config files."""
    if result["license"]:
        return
    for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE",
                 "LICENCE.md", "LICENCE.txt", "license", "license.md"):
        p = root / name
        if p.exists():
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")[:2000]
                for keyword in ("MIT", "Apache", "GPL", "BSD", "ISC",
                                "MPL", "LGPL", "AGPL", "Unlicense"):
                    if keyword.upper() in text.upper():
                        result["license"] = keyword
                        return
                result["license"] = "See LICENSE file"
                return
            except OSError:
                pass


def _detect_repo_url(root: Path, result: dict[str, Any]) -> None:
    """Try git remote, then fall back to config-file URLs."""
    if result["repo_url"]:
        return
    try:
        out = subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            cwd=str(root), stderr=subprocess.DEVNULL, text=True,
        ).strip()
        result["repo_url"] = _clean_git_url(out)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass


def _detect_readme(root: Path, result: dict[str, Any]) -> None:
    """Find a README and extract section headings + line count."""
    for name in ("README.md", "README.rst", "README.txt", "README",
                 "readme.md", "readme.rst"):
        p = root / name
        if p.exists():
            result["has_readme"] = True
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
                lines = text.splitlines()
                sections = [
                    line.lstrip("#").strip()
                    for line in lines
                    if re.match(r'^#{1,3}\s+\S', line)
                ]
                result["readme_summary"] = {
                    "sections": sections,
                    "line_count": len(lines),
                }
            except OSError:
                result["readme_summary"] = {"sections": [], "line_count": 0}
            return


def _detect_logo(root: Path, result: dict[str, Any]) -> None:
    """Scan common asset directories for logo files."""
    search_dirs = [
        "assets", "docs/assets", "docs/images", "images", "img",
        "static", "public", ".",
    ]
    for rel in search_dirs:
        d = root / rel
        if not d.is_dir():
            continue
        try:
            for fn in sorted(d.iterdir()):
                if fn.is_file() and fn.stem.lower() in ("logo", "logo-dark",
                                                         "logo-light"):
                    result["logo_path"] = str(fn.relative_to(root)).replace("\\", "/")
                    return
        except OSError:
            pass


def _detect_ci(root: Path, result: dict[str, Any]) -> None:
    """Detect the CI system in use."""
    gh_workflows = root / ".github" / "workflows"
    if gh_workflows.is_dir():
        for f in gh_workflows.iterdir():
            if f.suffix in (".yml", ".yaml"):
                result["ci_type"] = "github_actions"
                return
    if (root / ".gitlab-ci.yml").exists():
        result["ci_type"] = "gitlab_ci"
        return
    if (root / "Jenkinsfile").exists():
        result["ci_type"] = "jenkins"
        return
    if (root / ".travis.yml").exists():
        result["ci_type"] = "travis"
        return
    if (root / "azure-pipelines.yml").exists():
        result["ci_type"] = "azure_pipelines"
        return
    if (root / ".circleci").is_dir():
        result["ci_type"] = "circleci"
        return


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) > 1:
        root = Path(sys.argv[1]).resolve()
    else:
        root = Path.cwd()

    if not root.is_dir():
        json.dump({"error": f"Not a directory: {root}"}, sys.stdout)
        sys.exit(1)

    try:
        result = detect(root)
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    except Exception as exc:
        json.dump({"error": str(exc)}, sys.stdout)
        sys.exit(1)


if __name__ == "__main__":
    main()
