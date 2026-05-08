#!/usr/bin/env python3
import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_VENDOR_ROOT = SKILL_DIR / "vendor" / "video-downloader"
ENV_PROJECT_ROOT = "VIDEO_DOWNLOADER_PROJECT"
MODULE_NAME = "video_downloader"


def module_importable(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def normalize_project_root(project_root: str | None) -> Path | None:
    if project_root:
        return Path(project_root).expanduser().resolve()

    env_value = os.environ.get(ENV_PROJECT_ROOT)
    if env_value:
        return Path(env_value).expanduser().resolve()

    if DEFAULT_VENDOR_ROOT.exists():
        return DEFAULT_VENDOR_ROOT.resolve()

    return None


def project_has_markers(project_root: Path) -> bool:
    markers = [
        project_root / "video_downloader",
        project_root / "mcp_server.py",
        project_root / "pyproject.toml",
        project_root / "setup.py",
    ]
    return any(marker.exists() for marker in markers)


def build_subprocess_env(project_root: Path | None) -> dict[str, str]:
    env = dict(os.environ)
    if project_root:
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(project_root) if not existing else str(project_root) + os.pathsep + existing
    return env


def resolve_runtime(project_root: str | None) -> tuple[str, Path | None]:
    root = normalize_project_root(project_root)
    if root:
        if not root.exists():
            raise FileNotFoundError(f"Project root does not exist: {root}")
        if not project_has_markers(root):
            raise FileNotFoundError(
                f"Project root does not look like a video_downloader checkout: {root}"
            )
        return "project-root", root

    if module_importable(MODULE_NAME):
        return "installed-module", None

    raise FileNotFoundError(
        "No downloader runtime found. Install/import `video_downloader`, "
        f"or set {ENV_PROJECT_ROOT} / --project-root to a local checkout."
    )


def run_module(args: argparse.Namespace) -> int:
    _, root = resolve_runtime(args.project_root)
    command = [sys.executable, "-m", MODULE_NAME, *args.module_args]
    result = subprocess.run(
        command,
        cwd=str(root) if root else None,
        env=build_subprocess_env(root),
        check=False,
    )
    return result.returncode


def run_mcp(args: argparse.Namespace) -> int:
    mode, root = resolve_runtime(args.project_root)
    if mode == "installed-module":
        command = [sys.executable, "-m", MODULE_NAME, "--help"]
        print(
            "warning: resolved an installed module, but this wrapper cannot infer its MCP entrypoint.",
            file=sys.stderr,
        )
        print("warning: showing module help instead; use --project-root if you need mcp_server.py.", file=sys.stderr)
    else:
        mcp_server = root / "mcp_server.py"
        if not mcp_server.exists():
            raise FileNotFoundError(f"mcp_server.py not found under project root: {root}")
        command = [sys.executable, str(mcp_server)]

    result = subprocess.run(
        command,
        cwd=str(root) if root else None,
        env=build_subprocess_env(root),
        check=False,
    )
    return result.returncode


def run_doctor(args: argparse.Namespace) -> int:
    print(f"skill_dir\t{SKILL_DIR}")
    print(f"python\t{sys.version.split()[0]}")
    print(f"default_vendor_root\t{DEFAULT_VENDOR_ROOT}")
    print(f"module_importable\t{module_importable(MODULE_NAME)}")
    print(f"playwright_importable\t{module_importable('playwright')}")

    root = normalize_project_root(args.project_root)
    if root is None:
        print("project_root\t<not set>")
    else:
        print(f"project_root\t{root}")
        print(f"project_root_exists\t{root.exists()}")
        print(f"project_has_markers\t{project_has_markers(root) if root.exists() else False}")

    try:
        mode, resolved_root = resolve_runtime(args.project_root)
        print(f"runtime_mode\t{mode}")
        print(f"runtime_root\t{resolved_root or '<site-packages>'}")
        return 0
    except FileNotFoundError as exc:
        print(f"runtime_error\t{exc}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Portable bridge for the video-downloader skill. "
            "It resolves an installed `video_downloader` module or a local project checkout."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Check how the runtime will be resolved.")
    doctor.add_argument("--project-root", help="Local checkout that contains the downloader implementation.")
    doctor.set_defaults(func=run_doctor)

    run_cmd = subparsers.add_parser(
        "run",
        help="Run `python -m video_downloader` through the resolved runtime.",
    )
    run_cmd.add_argument("--project-root", help="Local checkout that contains the downloader implementation.")
    run_cmd.add_argument("module_args", nargs=argparse.REMAINDER, help="Arguments passed to `python -m video_downloader`.")
    run_cmd.set_defaults(func=run_module)

    mcp = subparsers.add_parser("mcp", help="Run the runtime's MCP server entrypoint when available.")
    mcp.add_argument("--project-root", help="Local checkout that contains mcp_server.py.")
    mcp.set_defaults(func=run_mcp)

    return parser


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
