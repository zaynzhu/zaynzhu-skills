#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TMPI - Text Model Project Init

初始化纯文本主模型项目规则：
- 询问是否已经安装并准备使用 model-router skill
- 将图片输入安全规则写入当前项目 CLAUDE.md / claude.md
- 兼容 Windows / macOS / Linux
- 兼容 UTF-8、UTF-8 BOM、GBK、GB18030
- 幂等更新，不重复插入
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

BEGIN_MARKER = "<!-- TMPI:BEGIN text-model-project-init -->"
END_MARKER = "<!-- TMPI:END text-model-project-init -->"
CANONICAL_FILENAME = "CLAUDE.md"
LEGACY_FILENAMES = ("CLAUDE.md", "claude.md")


@dataclass
class ReadResult:
    text: str
    encoding: str
    had_bom: bool
    newline: str


def write_console(message: str = "") -> None:
    """兼容 GBK/UTF-8 终端输出，避免 Windows 旧终端 UnicodeEncodeError。"""
    encoding = sys.stdout.encoding or "utf-8"
    data = (message + os.linesep).encode(encoding, errors="replace")
    try:
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
    except Exception:
        print(message.encode(encoding, errors="replace").decode(encoding, errors="replace"))


def prompt_yes_no(question: str, default: bool = False) -> bool:
    suffix = " [Y/n]: " if default else " [y/N]: "
    encoding = sys.stdout.encoding or "utf-8"
    try:
        sys.stdout.buffer.write((question + suffix).encode(encoding, errors="replace"))
        sys.stdout.buffer.flush()
    except Exception:
        print(question + suffix, end="")

    answer = sys.stdin.readline().strip().lower()
    if not answer:
        return default
    return answer in {"y", "yes", "是", "已安装", "安装了", "ok", "确认", "1", "true"}


def detect_newline(text: str) -> str:
    crlf_count = text.count("\r\n")
    lf_count = text.count("\n") - crlf_count
    if crlf_count > lf_count:
        return "\r\n"
    return "\n"


def read_text_safely(path: Path) -> ReadResult:
    raw = path.read_bytes()
    candidates = ["utf-8-sig", "utf-8", "gb18030", "gbk", "cp936"]

    for encoding in candidates:
        try:
            text = raw.decode(encoding)
            normalized_encoding = "utf-8" if encoding == "utf-8-sig" else encoding
            had_bom = encoding == "utf-8-sig" and raw.startswith(b"\xef\xbb\xbf")
            return ReadResult(
                text=text,
                encoding=normalized_encoding,
                had_bom=had_bom,
                newline=detect_newline(text),
            )
        except UnicodeDecodeError:
            continue

    # 极端情况下兜底：不丢内容，但会替换无法识别字符
    text = raw.decode("utf-8", errors="replace")
    return ReadResult(text=text, encoding="utf-8", had_bom=False, newline=detect_newline(text))


def write_text_atomic(path: Path, text: str, encoding: str, had_bom: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    write_encoding = "utf-8-sig" if encoding == "utf-8" and had_bom else encoding
    with tempfile.NamedTemporaryFile(
        "w",
        encoding=write_encoding,
        newline="",
        delete=False,
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    ) as handle:
        tmp_path = Path(handle.name)
        handle.write(text)

    tmp_path.replace(path)


def find_claude_file(project_dir: Path) -> Path:
    for filename in LEGACY_FILENAMES:
        candidate = project_dir / filename
        if candidate.exists():
            return candidate

    # 在大小写敏感系统里，兼容 ClaUDe.md 等异常大小写
    for child in project_dir.iterdir() if project_dir.exists() else []:
        if child.is_file() and child.name.lower() == "claude.md":
            return child

    return project_dir / CANONICAL_FILENAME


def build_rule_block(newline: str) -> str:
    lines = [
        BEGIN_MARKER,
        "## 图片输入与视觉任务规则（TMPI）",
        "",
        "当前主模型可能不支持图片输入。本项目必须按纯文本主模型约束处理所有视觉任务。",
        "",
        "任何截图、验证码、图片、图表、浏览器截图、UI 自动化截图、OCR 任务，都不得直接作为图片内容、base64、image payload、MCP image block 发送给主模型。",
        "",
        "尤其禁止以下行为：",
        "",
        "1. 使用 Playwright、Chrome DevTools、Superpowers Chrome 等工具后，将截图结果直接返回给主模型。",
        "2. 将本地图片文件直接读取为 image input。",
        "3. 将图片转成 base64 放入上下文。",
        "4. 将工具生成的 screenshot/image artifact 作为视觉消息继续传给主模型。",
        "5. 在当前主模型不支持图片时，尝试让主模型直接“看图”“识图”“读截图”。",
        "",
        "遇到视觉任务时，必须使用 model-router skill：",
        "",
        "1. 图片、截图、图表必须先保存为本地文件路径，例如 `.model-router/images/xxx.png`。",
        "2. 主模型只能接收图片路径，不能接收图片内容。",
        "3. 使用 model-router 调用支持视觉输入的模型进行识别。",
        "4. 后续只基于视觉模型返回的文本结果继续分析。",
        "5. 如果某个工具只能返回图片内容，不能保存为本地路径，则必须暂停并说明原因，不得继续调用主模型。",
        "",
        "建议流程：",
        "",
        "```bash",
        "python skills/model-router/scripts/model_router.py prepare",
        "python skills/model-router/scripts/model_router.py route --task has_image_input --image .model-router/images/example.png --prompt \"请识别图片内容并返回纯文本结果\"",
        "```",
        "",
        "如果 model-router skill 不在项目内的 `skills/model-router/` 路径，应先定位已安装的 model-router skill 目录，再按其实际脚本路径执行。",
        "",
        "用户以后如果说“看图”“截图”“识别这张图”“分析 UI 截图”，必须先要求提供本地图片路径，或者将截图保存到 `.model-router/images/`，不得直接把图片内容送入主模型。",
        END_MARKER,
    ]
    return newline.join(lines)


def upsert_block(existing_text: str, block: str, newline: str) -> tuple[str, str]:
    pattern = re.compile(
        re.escape(BEGIN_MARKER) + r".*?" + re.escape(END_MARKER),
        flags=re.DOTALL,
    )

    if pattern.search(existing_text):
        updated = pattern.sub(block, existing_text, count=1)
        return updated, "updated"

    if not existing_text.strip():
        return block + newline, "created_block"

    # 放在 CLAUDE.md 靠前位置：如果有首个标题，插入到标题后；否则插入到文件开头。
    lines = existing_text.splitlines(keepends=True)
    if lines and lines[0].lstrip().startswith("#"):
        insert_at = 1
        while insert_at < len(lines) and lines[insert_at].strip() == "":
            insert_at += 1
        prefix = "".join(lines[:insert_at])
        suffix = "".join(lines[insert_at:])
        separator = newline + newline if not prefix.endswith(newline + newline) else ""
        tail_separator = newline + newline if suffix and not suffix.startswith(newline) else ""
        return prefix + separator + block + tail_separator + suffix, "inserted_after_title"

    return block + newline + newline + existing_text, "inserted_at_top"


def make_backup(path: Path) -> Optional[Path]:
    if not path.exists():
        return None
    backup = path.with_name(path.name + ".tmpi.bak")
    shutil.copy2(path, backup)
    return backup


def init_project(project_dir: Path, yes: bool, force_utf8: bool, no_backup: bool) -> int:
    project_dir = project_dir.expanduser().resolve()
    if not project_dir.exists() or not project_dir.is_dir():
        write_console(f"错误：项目目录不存在或不是目录：{project_dir}")
        return 2

    if not yes:
        ok = prompt_yes_no("是否已经安装并准备使用 model-router skill？", default=False)
        if not ok:
            write_console("已停止：请先安装 model-router skill，安装完成后重新执行 TMPI。")
            return 0

    claude_path = find_claude_file(project_dir)

    if claude_path.exists():
        read_result = read_text_safely(claude_path)
        encoding = "utf-8" if force_utf8 else read_result.encoding
        had_bom = False if force_utf8 else read_result.had_bom
        newline = read_result.newline or ("\r\n" if os.name == "nt" else "\n")
        original_text = read_result.text
    else:
        encoding = "utf-8"
        had_bom = False
        newline = "\r\n" if os.name == "nt" else "\n"
        original_text = ""

    block = build_rule_block(newline)
    updated_text, action = upsert_block(original_text, block, newline)

    backup_path = None
    if claude_path.exists() and not no_backup:
        backup_path = make_backup(claude_path)

    write_text_atomic(claude_path, updated_text, encoding=encoding, had_bom=had_bom)

    write_console("TMPI 初始化完成。")
    write_console(f"文件：{claude_path}")
    write_console(f"动作：{action}")
    write_console(f"编码：{encoding}{' with BOM' if had_bom else ''}")
    write_console(f"换行：{'CRLF' if newline == chr(13) + chr(10) else 'LF'}")
    if backup_path:
        write_console(f"备份：{backup_path}")
    else:
        write_console("备份：未创建（新文件或已指定 --no-backup）")
    write_console("后续图片任务请只传本地图片路径，并通过 model-router skill 处理。")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TMPI：初始化纯文本主模型项目规则，防止图片进入主模型上下文。"
    )
    parser.add_argument(
        "--project",
        default=".",
        help="当前项目目录，默认是当前工作目录。",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="跳过交互询问，视为已安装并准备使用 model-router skill。",
    )
    parser.add_argument(
        "--force-utf8",
        action="store_true",
        help="无论原文件编码如何，都将 CLAUDE.md 转为 UTF-8（默认保留原编码）。",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="不创建 .tmpi.bak 备份文件。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return init_project(
        project_dir=Path(args.project),
        yes=args.yes,
        force_utf8=args.force_utf8,
        no_backup=args.no_backup,
    )


if __name__ == "__main__":
    raise SystemExit(main())
