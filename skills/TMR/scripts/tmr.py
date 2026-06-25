#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TMR - Text Model Rescue

Rescue Claude Code JSONL transcripts polluted by image blocks when using text-only models.

This script is intentionally conservative:
- scan does not modify files
- rescue always writes a backup first
- JSONL lines are parsed and rewritten one by one
- image-like blocks are replaced with plain text placeholders instead of deleting whole messages
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

IMAGE_DATA_URI_RE = re.compile(r"data:image/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=\r\n]+")
LONG_BASE64_RE = re.compile(r"^[A-Za-z0-9+/\r\n]{2000,}={0,2}$")
IMAGE_EXT_RE = re.compile(r"\.(png|jpe?g|gif|webp|bmp|svg|tiff?)$", re.IGNORECASE)

IMAGE_KEYS = {
    "image",
    "images",
    "image_url",
    "imageUrl",
    "screenshot",
    "screenshots",
    "thumbnail",
    "thumbnails",
    "picture",
    "pictures",
}

BASE64_KEYS = {
    "data",
    "base64",
    "bytes",
    "content",
    "blob",
}

PLACEHOLDER_TEXT = (
    "[TMR 已移除一个图片输入块：原始内容疑似为截图、image block、base64 图片或 MCP 图片结果。"
    "该占位用于防止文本模型继续报 this model does not support image input。]"
)


@dataclass
class Finding:
    path: str
    reason: str
    preview: str = ""


@dataclass
class FileReport:
    file: Path
    lines: int
    findings: List[Finding]
    invalid_json_lines: int = 0


def eprint(*args: Any) -> None:
    print(*args, file=sys.stderr)


def normalize_path_for_claude(project: Path) -> str:
    """Approximate Claude Code project directory name under ~/.claude/projects.

    Claude Code commonly stores project sessions under a sanitized absolute path. Different
    versions may vary, so this is only one of several matching strategies.
    """
    resolved = str(project.resolve())
    # Common Claude style: /Users/a/b -> -Users-a-b, C:\x\y -> -C--x-y or C--x-y variants.
    name = resolved.replace("\\", "-").replace("/", "-").replace(":", "-")
    while "--" in name:
        name = name.replace("--", "-")
    return name


def get_claude_config_dir() -> Path:
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".claude"


def possible_project_dirs(project: Path, config_dir: Optional[Path] = None) -> List[Path]:
    config = config_dir or get_claude_config_dir()
    projects_dir = config / "projects"
    if not projects_dir.exists():
        return []

    resolved = project.resolve()
    sanitized = normalize_path_for_claude(resolved)
    candidates: List[Path] = []

    exact = projects_dir / sanitized
    if exact.exists():
        candidates.append(exact)

    # Fuzzy fallback. This handles small format differences across platforms/versions.
    project_name = resolved.name.lower()
    resolved_tail = str(resolved).replace("\\", "/").lower().strip("/")
    for child in projects_dir.iterdir():
        if not child.is_dir():
            continue
        child_name = child.name.lower()
        if child in candidates:
            continue
        if project_name and project_name in child_name:
            candidates.append(child)
            continue
        # Compare last 2 path parts to reduce false positives.
        parts = [p for p in resolved_tail.split("/") if p]
        tail = "-".join(parts[-2:]) if len(parts) >= 2 else (parts[-1] if parts else "")
        if tail and tail.replace(":", "-") in child_name:
            candidates.append(child)

    return candidates


def find_transcripts(project: Path, config_dir: Optional[Path] = None) -> List[Path]:
    dirs = possible_project_dirs(project, config_dir=config_dir)
    files: List[Path] = []
    for d in dirs:
        files.extend(d.glob("*.jsonl"))
    # If nothing matched, fallback to all recent jsonl under ~/.claude/projects.
    if not files:
        base = (config_dir or get_claude_config_dir()) / "projects"
        if base.exists():
            files = list(base.glob("**/*.jsonl"))
    files = [p for p in files if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def short_preview(value: Any, limit: int = 120) -> str:
    try:
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    except Exception:
        text = repr(value)
    text = text.replace("\n", "\\n").replace("\r", "\\r")
    return text[:limit] + ("..." if len(text) > limit else "")


def looks_like_base64_image(s: str) -> bool:
    text = s.strip()
    if not text:
        return False
    if IMAGE_DATA_URI_RE.search(text):
        return True
    if not LONG_BASE64_RE.match(text):
        return False
    # Try sniffing image headers from the first decoded bytes.
    try:
        sample = text[:4096]
        raw = base64.b64decode(sample + "=" * ((4 - len(sample) % 4) % 4), validate=False)
    except Exception:
        return False
    return raw.startswith((
        b"\x89PNG\r\n\x1a\n",
        b"\xff\xd8\xff",
        b"GIF87a",
        b"GIF89a",
        b"RIFF",  # could be WEBP, checked below loosely
        b"BM",
        b"<svg",
    ))


def is_image_object(obj: Dict[str, Any]) -> Optional[str]:
    t = obj.get("type")
    if isinstance(t, str) and t.lower() in {"image", "image_url", "input_image", "screenshot"}:
        return f"type={t}"

    media_type = obj.get("media_type") or obj.get("mime_type") or obj.get("mimeType")
    source = obj.get("source")
    if isinstance(media_type, str) and media_type.lower().startswith("image/"):
        return f"media_type={media_type}"
    if isinstance(source, dict):
        src_type = source.get("type")
        src_media = source.get("media_type") or source.get("mime_type") or source.get("mimeType")
        if isinstance(src_media, str) and src_media.lower().startswith("image/"):
            return f"source media_type={src_media}"
        if isinstance(src_type, str) and src_type.lower() in {"base64", "image", "image_url"}:
            if any(k in source for k in ("data", "url", "image_url")):
                return f"source.type={src_type}"

    # Tool-specific shapes: { screenshot: { data: ..., mimeType: image/png } }
    for key, value in obj.items():
        if key in IMAGE_KEYS:
            if isinstance(value, (dict, list)):
                return f"image-like key={key}"
            if isinstance(value, str) and (looks_like_base64_image(value) or IMAGE_EXT_RE.search(value)):
                return f"image-like key={key}"

    return None


def text_placeholder(reason: str) -> Dict[str, str]:
    return {
        "type": "text",
        "text": f"{PLACEHOLDER_TEXT} 原因：{reason}",
    }


def sanitize(obj: Any, path: str = "$", findings: Optional[List[Finding]] = None) -> Tuple[Any, int]:
    if findings is None:
        findings = []

    if isinstance(obj, dict):
        reason = is_image_object(obj)
        if reason:
            findings.append(Finding(path=path, reason=reason, preview=short_preview(obj)))
            return text_placeholder(reason), 1

        changed = 0
        new_obj: Dict[str, Any] = {}
        for key, value in obj.items():
            child_path = f"{path}.{key}"

            # Handle image-like keys conservatively.
            if key in IMAGE_KEYS:
                findings.append(Finding(path=child_path, reason=f"image-like key={key}", preview=short_preview(value)))
                new_obj[key] = f"{PLACEHOLDER_TEXT} 原因：image-like key={key}"
                changed += 1
                continue

            if isinstance(value, str):
                new_value, n = sanitize_string(value, child_path, key, findings)
                new_obj[key] = new_value
                changed += n
                continue

            new_value, n = sanitize(value, child_path, findings)
            new_obj[key] = new_value
            changed += n
        return new_obj, changed

    if isinstance(obj, list):
        changed = 0
        new_list: List[Any] = []
        for i, item in enumerate(obj):
            new_item, n = sanitize(item, f"{path}[{i}]", findings)
            new_list.append(new_item)
            changed += n
        return new_list, changed

    if isinstance(obj, str):
        return sanitize_string(obj, path, "", findings)

    return obj, 0


def sanitize_string(value: str, path: str, key: str, findings: List[Finding]) -> Tuple[str, int]:
    changed = 0
    text = value

    if IMAGE_DATA_URI_RE.search(text):
        findings.append(Finding(path=path, reason="data:image base64 URI", preview=short_preview(text)))
        text = IMAGE_DATA_URI_RE.sub("[TMR 已移除 data:image base64 图片内容]", text)
        changed += 1

    key_lower = key.lower() if key else ""
    if key in BASE64_KEYS or "base64" in key_lower or key_lower in {"data", "content"}:
        if looks_like_base64_image(text):
            findings.append(Finding(path=path, reason=f"base64 image string key={key}", preview=short_preview(text)))
            return f"{PLACEHOLDER_TEXT} 原因：base64 image string key={key}", changed + 1

    return text, changed


def scan_file(file: Path, max_lines: Optional[int] = None) -> FileReport:
    findings: List[Finding] = []
    invalid = 0
    line_count = 0
    try:
        with file.open("r", encoding="utf-8", errors="replace") as f:
            for line_no, line in enumerate(f, start=1):
                line_count = line_no
                if max_lines and line_no > max_lines:
                    break
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    obj = json.loads(stripped)
                except json.JSONDecodeError:
                    invalid += 1
                    # Fall back to raw string scan for data URI.
                    if IMAGE_DATA_URI_RE.search(stripped) or looks_like_base64_image(stripped):
                        findings.append(Finding(path=f"line {line_no}", reason="raw image-like JSONL line", preview=short_preview(stripped)))
                    continue
                before_count = len(findings)
                sanitize(obj, path=f"line {line_no}", findings=findings)
                # Prefix recent findings with line number if needed.
                for item in findings[before_count:]:
                    if not item.path.startswith("line"):
                        item.path = f"line {line_no}:{item.path}"
    except FileNotFoundError:
        raise
    return FileReport(file=file, lines=line_count, findings=findings, invalid_json_lines=invalid)


def rescue_file(file: Path, dry_run: bool = False) -> Tuple[Path, int, List[Finding]]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = file.with_name(file.name + f".tmr.bak.{timestamp}")
    all_findings: List[Finding] = []
    changed_total = 0
    output_lines: List[str] = []

    with file.open("r", encoding="utf-8", errors="replace", newline="") as f:
        for line_no, line in enumerate(f, start=1):
            raw_newline = "\n" if line.endswith("\n") else ""
            stripped = line.strip()
            if not stripped:
                output_lines.append(line)
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError:
                # For invalid JSON lines, only sanitize data URI strings to avoid corrupting unknown structure.
                findings: List[Finding] = []
                new_text, n = sanitize_string(line, f"line {line_no}", "", findings)
                for item in findings:
                    if not item.path.startswith("line"):
                        item.path = f"line {line_no}:{item.path}"
                all_findings.extend(findings)
                changed_total += n
                output_lines.append(new_text)
                continue

            findings: List[Finding] = []
            new_obj, n = sanitize(obj, path=f"line {line_no}", findings=findings)
            all_findings.extend(findings)
            changed_total += n
            if n:
                output_lines.append(json.dumps(new_obj, ensure_ascii=False, separators=(",", ":")) + raw_newline)
            else:
                output_lines.append(line)

    if changed_total and not dry_run:
        shutil.copy2(file, backup)
        tmp = file.with_name(file.name + f".tmr.tmp.{timestamp}")
        with tmp.open("w", encoding="utf-8", newline="") as f:
            f.writelines(output_lines)
        os.replace(tmp, file)
    return backup, changed_total, all_findings


def print_file_report(report: FileReport, max_items: int = 20) -> None:
    print(f"文件：{report.file}")
    print(f"行数：{report.lines}，可疑图片污染：{len(report.findings)}，无效 JSON 行：{report.invalid_json_lines}")
    for i, finding in enumerate(report.findings[:max_items], start=1):
        print(f"  {i}. {finding.path} | {finding.reason} | {finding.preview}")
    if len(report.findings) > max_items:
        print(f"  ... 还有 {len(report.findings) - max_items} 项未显示")


def cmd_list(args: argparse.Namespace) -> int:
    project = Path(args.project).expanduser()
    transcripts = find_transcripts(project, Path(args.config_dir).expanduser() if args.config_dir else None)
    if not transcripts:
        print("未找到 Claude Code transcript。请确认 CLAUDE_CONFIG_DIR 或 ~/.claude/projects 是否存在。")
        return 1
    print("找到以下 transcript，按最近修改时间排序：")
    for i, file in enumerate(transcripts[: args.limit], start=1):
        stat = file.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        size_kb = stat.st_size / 1024
        print(f"[{i}] {mtime}  {size_kb:.1f} KB  {file}")
    return 0


def choose_target(args: argparse.Namespace) -> Optional[Path]:
    if args.file:
        return Path(args.file).expanduser()
    project = Path(args.project).expanduser()
    transcripts = find_transcripts(project, Path(args.config_dir).expanduser() if args.config_dir else None)
    if not transcripts:
        return None
    index = max(args.index - 1, 0)
    if index >= len(transcripts):
        eprint(f"指定 index={args.index} 超出范围，共找到 {len(transcripts)} 个 transcript。")
        return None
    return transcripts[index]


def cmd_scan(args: argparse.Namespace) -> int:
    target = choose_target(args)
    if not target:
        print("未找到可扫描的 transcript。可先执行 list，或用 --file 指定 JSONL 文件。")
        return 1
    report = scan_file(target, max_lines=args.max_lines)
    print_file_report(report, max_items=args.max_items)
    if report.findings:
        print("\n建议：确认这是当前报错会话后，执行 rescue。")
        print(f"命令示例：python {Path(__file__).name} rescue --file \"{target}\"")
        return 2
    print("\n未发现明显图片污染。")
    return 0


def cmd_rescue(args: argparse.Namespace) -> int:
    target = choose_target(args)
    if not target:
        print("未找到可急救的 transcript。可先执行 list，或用 --file 指定 JSONL 文件。")
        return 1

    if not target.exists():
        print(f"文件不存在：{target}")
        return 1

    backup, changed, findings = rescue_file(target, dry_run=args.dry_run)
    if args.dry_run:
        print(f"dry-run：将处理 {target}")
        print(f"预计替换图片污染块：{changed}")
        for i, finding in enumerate(findings[: args.max_items], start=1):
            print(f"  {i}. {finding.path} | {finding.reason} | {finding.preview}")
        return 0 if changed == 0 else 2

    if changed == 0:
        print(f"未发现需要替换的图片污染块：{target}")
        return 0

    print(f"已净化 transcript：{target}")
    print(f"已创建备份：{backup}")
    print(f"替换图片污染块：{changed}")
    print("\n下一步：完全退出当前 Claude Code 进程，然后重新进入项目并 resume。")
    print("如果处理后异常，执行 restore 恢复备份。")
    return 0


def cmd_save(args: argparse.Namespace) -> int:
    """Create a timestamped snapshot of the most recent transcript (proactive checkpoint).

    Unlike rescue (which sanitizes an already-polluted transcript), save copies the
    current transcript verbatim to a .tmr.snap.<timestamp> file so the user can
    restore back to this exact point if a later tool call injects image blocks.
    """
    target = choose_target(args)
    if not target or not target.exists():
        print("未找到可存档的 transcript。可先执行 list，或用 --file 指定 JSONL 文件。")
        return 1

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snap = target.with_name(target.name + f".tmr.snap.{timestamp}")
    shutil.copy2(target, snap)
    size_kb = snap.stat().st_size / 1024
    print(f"已创建 transcript 快照：{snap}")
    print(f"源文件：{target}")
    print(f"大小：{size_kb:.1f} KB")
    print("\n用途：当会话被图片污染后，用此快照覆盖回原文件即可回到存档点。")
    print(f"恢复命令：python {Path(__file__).name} restore --backup \"{snap}\"")
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    backup = Path(args.backup).expanduser()
    if not backup.exists():
        print(f"备份不存在：{backup}")
        return 1

    name = backup.name
    markers = (".tmr.bak.", ".tmr.snap.")
    target: Optional[Path] = None
    for marker in markers:
        if marker in name:
            target = backup.with_name(name.split(marker, 1)[0])
            break
    if target is None:
        if not args.force:
            print("这个文件名不像 TMR 备份或快照。若确认要恢复，请加 --force。")
            return 1
        # Fallback: remove final suffix if any.
        target = backup.with_name(name.rsplit(".", 1)[0])

    if target.exists() and not args.force:
        safety = target.with_name(target.name + ".before-tmr-restore." + datetime.now().strftime("%Y%m%d_%H%M%S"))
        shutil.copy2(target, safety)
        print(f"已先备份当前文件：{safety}")

    shutil.copy2(backup, target)
    print(f"已恢复：{target}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tmr.py",
        description="TMR - Text Model Rescue for Claude Code JSONL transcripts polluted by image blocks.",
    )
    parser.add_argument("--version", action="version", version="TMR 0.1.0")

    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--project", default=".", help="项目目录，默认当前目录。")
        p.add_argument("--config-dir", default=None, help="Claude 配置目录，默认读取 CLAUDE_CONFIG_DIR 或 ~/.claude。")
        p.add_argument("--file", default=None, help="直接指定 transcript JSONL 文件。")
        p.add_argument("--index", type=int, default=1, help="使用第几个最近的 transcript，默认 1。")

    p_list = sub.add_parser("list", help="列出可能的 Claude Code transcript。")
    p_list.add_argument("--project", default=".", help="项目目录，默认当前目录。")
    p_list.add_argument("--config-dir", default=None, help="Claude 配置目录，默认读取 CLAUDE_CONFIG_DIR 或 ~/.claude。")
    p_list.add_argument("--limit", type=int, default=10, help="最多显示数量。")
    p_list.set_defaults(func=cmd_list)

    p_scan = sub.add_parser("scan", help="扫描图片污染，不修改文件。")
    add_common(p_scan)
    p_scan.add_argument("--max-lines", type=int, default=None, help="最多扫描行数，默认全部。")
    p_scan.add_argument("--max-items", type=int, default=20, help="最多显示发现项。")
    p_scan.set_defaults(func=cmd_scan)

    p_rescue = sub.add_parser("rescue", help="备份并净化 transcript。")
    add_common(p_rescue)
    p_rescue.add_argument("--dry-run", action="store_true", help="只预览，不写文件。")
    p_rescue.add_argument("--max-items", type=int, default=20, help="dry-run 最多显示发现项。")
    p_rescue.set_defaults(func=cmd_rescue)

    p_restore = sub.add_parser("restore", help="从 TMR 备份或快照恢复 transcript。")
    p_restore.add_argument("--backup", required=True, help="备份或快照文件路径。")
    p_restore.add_argument("--force", action="store_true", help="强制恢复非标准备份名，或跳过部分保护。")
    p_restore.set_defaults(func=cmd_restore)

    p_save = sub.add_parser("save", help="为最近 transcript 创建时间戳快照（主动存档，预防图片污染）。")
    add_common(p_save)
    p_save.set_defaults(func=cmd_save)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        eprint("已取消。")
        return 130
    except Exception as exc:
        eprint(f"错误：{exc}")
        if os.environ.get("TMR_DEBUG"):
            raise
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
