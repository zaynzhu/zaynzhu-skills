#!/usr/bin/env python3
"""把 ideastorming Markdown 结果渲染成静态 HTML 页面。"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import shutil
from pathlib import Path
from typing import Dict, List


DEFAULT_TITLE = "Ideastorming 项目选题报告"
PROJECT_HEADING_RE = re.compile(r"^###\s+(.+?)\s*$")
SECTION_HEADING_RE = re.compile(r"^####\s+(.+?)\s*$")
PROMPT_SECTION_NAME = "第一条开发提示词"
STAMP_RE = re.compile(r"^\d{8}-\d{6}$")


def parseArgs() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Build a static HTML report from ideastorming Markdown")
  parser.add_argument("--input", required=True, help="ideastorming Markdown result path")
  parser.add_argument("--output-dir", required=True, help="directory for timestamped Markdown and HTML report files")
  parser.add_argument("--title", default=DEFAULT_TITLE, help="report title")
  parser.add_argument("--stamp", help="timestamp suffix, format: YYYYMMDD-HHMMSS")
  return parser.parse_args()


def buildStamp(value: str | None = None) -> str:
  if value:
    if not STAMP_RE.match(value):
      raise ValueError("--stamp must use format YYYYMMDD-HHMMSS")
    return value
  return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def readText(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def splitProjects(markdown: str) -> List[Dict[str, object]]:
  projects: List[Dict[str, object]] = []
  current: Dict[str, object] | None = None
  currentSection = ""
  buffer: List[str] = []

  def flushSection() -> None:
    nonlocal buffer
    if current is None or not currentSection:
      buffer = []
      return
    sections = current.setdefault("sections", {})
    assert isinstance(sections, dict)
    sections[currentSection] = "\n".join(buffer).strip()
    buffer = []

  for line in markdown.splitlines():
    projectMatch = PROJECT_HEADING_RE.match(line)
    if projectMatch:
      flushSection()
      if current is not None:
        projects.append(current)
      current = {"name": projectMatch.group(1).strip(), "sections": {}}
      currentSection = ""
      buffer = []
      continue

    sectionMatch = SECTION_HEADING_RE.match(line)
    if sectionMatch and current is not None:
      flushSection()
      currentSection = sectionMatch.group(1).strip()
      buffer = []
      continue

    if current is not None and currentSection:
      buffer.append(line)

  flushSection()
  if current is not None:
    projects.append(current)

  return projects


def renderInline(text: str) -> str:
  escaped = html.escape(text)
  escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
  escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
  return escaped


def renderMarkdownBlock(markdown: str) -> str:
  lines = markdown.strip().splitlines()
  output: List[str] = []
  listOpen = False
  codeOpen = False
  codeLines: List[str] = []

  def closeList() -> None:
    nonlocal listOpen
    if listOpen:
      output.append("</ul>")
      listOpen = False

  for line in lines:
    stripped = line.strip()

    if stripped.startswith("```"):
      if codeOpen:
        output.append(f"<pre><code>{html.escape(chr(10).join(codeLines))}</code></pre>")
        codeLines = []
        codeOpen = False
      else:
        closeList()
        codeOpen = True
      continue

    if codeOpen:
      codeLines.append(line)
      continue

    if not stripped:
      closeList()
      continue

    if stripped.startswith("- "):
      if not listOpen:
        output.append("<ul>")
        listOpen = True
      output.append(f"<li>{renderInline(stripped[2:].strip())}</li>")
      continue

    closeList()
    output.append(f"<p>{renderInline(stripped)}</p>")

  if codeOpen:
    output.append(f"<pre><code>{html.escape(chr(10).join(codeLines))}</code></pre>")
  closeList()
  return "\n".join(output)


def renderProjectCard(project: Dict[str, object], index: int) -> str:
  name = str(project.get("name", f"项目 {index}"))
  sections = project.get("sections", {})
  assert isinstance(sections, dict)
  prompt = str(sections.get(PROMPT_SECTION_NAME, "")).strip()
  promptHtml = renderMarkdownBlock(prompt) if prompt else "<p>未提供开发提示词。</p>"

  sectionHtml: List[str] = []
  for sectionName, content in sections.items():
    if sectionName == PROMPT_SECTION_NAME:
      continue
    sectionHtml.append(
        f"""
        <section class="section">
          <h3>{html.escape(str(sectionName))}</h3>
          {renderMarkdownBlock(str(content))}
        </section>
        """.strip()
    )

  return f"""
  <article class="project-card">
    <header class="project-header">
      <span class="project-index">{index:02d}</span>
      <h2>{html.escape(name)}</h2>
    </header>
    <div class="section-grid">
      {''.join(sectionHtml)}
    </div>
    <section class="dev-prompt">
      <div class="prompt-title">
        <h3>第一条开发提示词</h3>
        <button type="button" data-copy-target="prompt-{index}">复制</button>
      </div>
      <div id="prompt-{index}" class="prompt-body">{promptHtml}</div>
    </section>
  </article>
  """.strip()


def buildHtml(title: str, markdown: str, stamp: str) -> str:
  projects = splitProjects(markdown)
  generatedAt = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  cards = "\n".join(renderProjectCard(project, index + 1) for index, project in enumerate(projects))

  if not projects:
    cards = f"""
    <article class="project-card">
      <h2>未识别到项目卡片</h2>
      <p>请确认 Markdown 中使用了 <code>### 项目名称</code> 和 <code>#### 第一条开发提示词</code> 结构。</p>
      <section class="section raw-markdown">
        <h3>原始 Markdown</h3>
        <pre><code>{html.escape(markdown)}</code></pre>
      </section>
    </article>
    """.strip()

  return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f5f7fb;
      --panel: #ffffff;
      --ink: #162033;
      --muted: #627086;
      --line: #dce3ee;
      --accent: #0f766e;
      --accent-soft: #e0f2f1;
      --prompt-bg: #111827;
      --prompt-ink: #f8fafc;
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
      color: var(--ink);
      background: var(--bg);
    }}
    .app-header {{
      padding: 36px 24px 22px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }}
    .app-header-inner {{
      max-width: 1180px;
      margin: 0 auto;
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: 30px;
      line-height: 1.2;
      letter-spacing: 0;
    }}
    .summary {{
      margin: 0;
      color: var(--muted);
      line-height: 1.7;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px;
    }}
    .project-card {{
      margin-bottom: 22px;
      padding: 22px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
    }}
    .project-header {{
      display: flex;
      gap: 12px;
      align-items: center;
      margin-bottom: 16px;
    }}
    .project-index {{
      display: inline-flex;
      width: 38px;
      height: 38px;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      background: var(--accent-soft);
      color: var(--accent);
      font-weight: 700;
    }}
    .project-header h2 {{
      margin: 0;
      font-size: 22px;
      line-height: 1.25;
    }}
    .section-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 12px;
    }}
    .section {{
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfe;
    }}
    .section h3, .dev-prompt h3 {{
      margin: 0 0 8px;
      font-size: 14px;
      color: var(--muted);
    }}
    .section p, .section li {{
      font-size: 14px;
      line-height: 1.7;
    }}
    .section p {{
      margin: 0 0 8px;
    }}
    .section ul {{
      margin: 0;
      padding-left: 20px;
    }}
    .dev-prompt {{
      margin-top: 16px;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid #1f2937;
      background: var(--prompt-bg);
      color: var(--prompt-ink);
    }}
    .prompt-title {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      padding: 12px 14px;
      border-bottom: 1px solid #374151;
    }}
    .prompt-title h3 {{
      color: #cbd5e1;
      margin: 0;
    }}
    button {{
      border: 1px solid #64748b;
      border-radius: 6px;
      background: #f8fafc;
      color: #111827;
      padding: 6px 10px;
      cursor: pointer;
      font-size: 13px;
    }}
    .prompt-body {{
      padding: 14px;
    }}
    .prompt-body p, .prompt-body li {{
      color: var(--prompt-ink);
      font-size: 14px;
      line-height: 1.8;
    }}
    code {{
      background: rgba(148, 163, 184, 0.18);
      border-radius: 4px;
      padding: 2px 4px;
    }}
    pre {{
      overflow: auto;
      padding: 12px;
      border-radius: 6px;
      background: #0b1120;
      color: #e5e7eb;
    }}
    @media (max-width: 680px) {{
      .app-header {{
        padding: 28px 16px 18px;
      }}
      main {{
        padding: 16px;
      }}
      .project-card {{
        padding: 16px;
      }}
      .section-grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <header class="app-header">
    <div class="app-header-inner">
      <h1>{html.escape(title)}</h1>
      <p class="summary">生成时间：{generatedAt} · 文件时间戳：{html.escape(stamp)} · 项目数：{len(projects)} · 每张卡片底部突出展示可复制的第一条开发提示词。</p>
    </div>
  </header>
  <main>
    {cards}
  </main>
  <script>
    document.querySelectorAll("button[data-copy-target]").forEach((button) => {{
      button.addEventListener("click", async () => {{
        const target = document.getElementById(button.dataset.copyTarget)
        const text = target ? target.innerText.trim() : ""
        if (!text) return
        await navigator.clipboard.writeText(text)
        const original = button.textContent
        button.textContent = "已复制"
        setTimeout(() => {{
          button.textContent = original
        }}, 1200)
      }})
    }})
  </script>
</body>
</html>
"""


def main() -> int:
  args = parseArgs()
  inputPath = Path(args.input).resolve()
  outputDir = Path(args.output_dir).resolve()
  outputDir.mkdir(parents=True, exist_ok=True)
  stamp = buildStamp(args.stamp)

  markdown = readText(inputPath)
  markdownOutput = outputDir / f"ideas-{stamp}.md"
  htmlOutput = outputDir / f"index-{stamp}.html"

  if inputPath != markdownOutput:
    shutil.copyfile(inputPath, markdownOutput)

  htmlOutput.write_text(buildHtml(args.title, markdown, stamp), encoding="utf-8")

  print(f"Markdown: {markdownOutput}")
  print(f"HTML: {htmlOutput}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
