#!/usr/bin/env python3
"""安全安装 timeline-consistency Skill 与 Hermes Plugin。"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SKILL_NAME = "timeline-consistency"
RUNTIME_SKILL_ENTRIES = ("SKILL.md", "ENVIRONMENTS.md", "references")


@dataclass(frozen=True)
class InstallTarget:
    label: str
    source: Path
    destination: Path
    include_entries: tuple[str, ...] = ()


def install(hermes_home: Path, *, dry_run: bool = False) -> list[str]:
    hermes_home = hermes_home.expanduser().resolve()
    if hermes_home == Path(hermes_home.anchor):
        raise ValueError("--hermes-home 不能指向文件系统根目录")

    skill_root = Path(__file__).resolve().parent.parent
    targets = (
        InstallTarget(
            label="Skill",
            source=skill_root,
            destination=hermes_home / "skills" / SKILL_NAME,
            include_entries=RUNTIME_SKILL_ENTRIES,
        ),
        InstallTarget(
            label="Plugin",
            source=skill_root / "adapters" / "hermes",
            destination=hermes_home / "plugins" / SKILL_NAME,
        ),
    )

    statuses = [_target_status(target) for target in targets]
    conflicts = [target for target, status in zip(targets, statuses) if status == "conflict"]
    if conflicts:
        paths = ", ".join(str(target.destination) for target in conflicts)
        raise FileExistsError(f"目标已存在且内容不同，未写入任何文件：{paths}")

    messages = []
    for target, status in zip(targets, statuses):
        if status == "same":
            messages.append(f"{target.label} 已是相同版本：{target.destination}")
        elif dry_run:
            messages.append(f"将安装 {target.label}：{target.destination}")

    if dry_run:
        return messages

    staged: list[tuple[InstallTarget, Path]] = []
    installed: list[Path] = []
    try:
        for target, status in zip(targets, statuses):
            if status != "missing":
                continue
            target.destination.parent.mkdir(parents=True, exist_ok=True)
            stage = Path(
                tempfile.mkdtemp(
                    prefix=f".{SKILL_NAME}-",
                    dir=target.destination.parent,
                )
            )
            _copy_target(target, stage)
            staged.append((target, stage))

        for target, stage in staged:
            stage.replace(target.destination)
            installed.append(target.destination)
            messages.append(f"已安装 {target.label}：{target.destination}")
    except Exception:
        for destination in reversed(installed):
            if destination.exists():
                shutil.rmtree(destination)
        raise
    finally:
        for _, stage in staged:
            if stage.exists():
                shutil.rmtree(stage)
    return messages


def _target_status(target: InstallTarget) -> str:
    if target.destination.is_symlink():
        return "conflict"
    if not target.destination.exists():
        return "missing"
    if not target.destination.is_dir():
        return "conflict"
    return "same" if _tree_digest(target.source, target.include_entries) == _tree_digest(target.destination) else "conflict"


def _copy_target(target: InstallTarget, stage: Path) -> None:
    if target.include_entries:
        for entry in target.include_entries:
            source = target.source / entry
            destination = stage / entry
            if source.is_dir():
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)
        return

    for source in _iter_files(target.source):
        relative = source.relative_to(target.source)
        destination = stage / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _tree_digest(root: Path, include_entries: tuple[str, ...] = ()) -> str:
    if any(path.is_symlink() for path in root.rglob("*")):
        return "symlink"
    digest = hashlib.sha256()
    files: Iterable[Path]
    if include_entries:
        selected = []
        for entry in include_entries:
            path = root / entry
            if path.is_dir():
                selected.extend(_iter_files(path))
            elif path.is_file():
                selected.append(path)
            else:
                return "missing"
        files = sorted(selected)
    else:
        files = _iter_files(root)

    for path in files:
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _iter_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.name != ".DS_Store"
    )


def _default_hermes_home() -> Path:
    configured = os.environ.get("HERMES_HOME", "").strip()
    return Path(configured) if configured else Path.home() / ".hermes"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="安装 timeline-consistency 到 Hermes profile")
    parser.add_argument(
        "--hermes-home",
        type=Path,
        default=_default_hermes_home(),
        help="Hermes profile 根目录，默认读取 HERMES_HOME 或 ~/.hermes",
    )
    parser.add_argument("--dry-run", action="store_true", help="只显示目标，不写入")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        messages = install(args.hermes_home, dry_run=args.dry_run)
    except (FileExistsError, OSError, ValueError) as exc:
        print(f"安装失败：{exc}", file=sys.stderr)
        return 1

    for message in messages:
        print(message)
    if not args.dry_run:
        print("未自动启用 Plugin。检查文件后运行：hermes plugins enable timeline-consistency")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
