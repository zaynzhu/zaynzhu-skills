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
HEADING_RE = re.compile(r"^(#{2,6})\s+(.+?)\s*$")
KNOWN_SECTIONS = {
  "对应热点",
  "背后趋势",
  "项目一句话",
  "目标用户",
  "核心痛点",
  "MVP 功能",
  "进阶功能",
  "技术栈建议",
  "为什么适合 vibe coding",
  "开发难度",
  "展示价值",
  "第一条开发提示词",
}
PROMPT_SECTION_NAME = "第一条开发提示词"
STAMP_RE = re.compile(r"^\d{8}-\d{6}$")


def normTitle(title: str) -> str:
  return re.sub(r"\s+", "", title).strip().lower()


KNOWN_SECTION_KEYS = {normTitle(title) for title in KNOWN_SECTIONS}


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
    headingMatch = HEADING_RE.match(line)
    if headingMatch:
      title = headingMatch.group(2).strip()
      if normTitle(title) in KNOWN_SECTION_KEYS:
        flushSection()
        if current is not None:
          currentSection = title
          buffer = []
        continue

      flushSection()
      if current is not None:
        projects.append(current)
      current = {"name": title, "sections": {}}
      currentSection = ""
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
  detailSectionCount = len([sectionName for sectionName in sections if sectionName != PROMPT_SECTION_NAME])

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
      <div class="project-heading">
        <span class="project-index">{index:02d}</span>
        <div>
          <p class="project-label">项目 {index:02d}</p>
          <h2>{html.escape(name)}</h2>
        </div>
      </div>
      <span class="section-count">{detailSectionCount} 个小节</span>
    </header>
    <div class="section-grid">
      {''.join(sectionHtml)}
    </div>
    <section class="dev-prompt" aria-labelledby="prompt-title-{index}">
      <div class="prompt-title">
        <div>
          <p class="prompt-kicker">可复制给 Agent</p>
          <h3 id="prompt-title-{index}">第一条开发提示词</h3>
        </div>
        <button type="button" data-copy-target="prompt-{index}" aria-label="复制第 {index:02d} 个项目的开发提示词">复制提示词</button>
      </div>
      <div id="prompt-{index}" class="prompt-body">{promptHtml}</div>
    </section>
  </article>
  """.strip()


def buildHtml(title: str, markdown: str, stamp: str) -> str:
  projects = splitProjects(markdown)
  if projects and all(not project.get("sections") for project in projects):
    raise SystemExit(
      f"解析失败：识别到 {len(projects)} 个标题，但所有项目都没有小节。"
      "请检查 Markdown 是否使用了项目标题 + 已知小节标题结构，例如 '### 项目名' + '#### 小节'。"
    )

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
      --bg: #eef2ec;
      --panel: #fffef9;
      --ink: #181512;
      --muted: #687064;
      --line: #d8ded2;
      --accent: #087f68;
      --accent-strong: #c2410c;
      --accent-warm: #f4c430;
      --accent-soft: #dff3eb;
      --prompt-bg: #171812;
      --prompt-ink: #fff8e8;
      --shadow: rgba(24, 21, 18, 0.18);
      --focus: #0b84d8;
    }}
    * {{
      box-sizing: border-box;
    }}
    html {{
      scroll-behavior: smooth;
    }}
    body {{
      margin: 0;
      font-family: "Noto Serif SC", "Source Han Serif SC", "Songti SC", "Microsoft YaHei", serif;
      color: var(--ink);
      background:
        linear-gradient(90deg, rgba(24, 21, 18, 0.05) 1px, transparent 1px) 0 0 / 36px 36px,
        linear-gradient(rgba(24, 21, 18, 0.04) 1px, transparent 1px) 0 0 / 36px 36px,
        var(--bg);
    }}
    .app-header {{
      position: relative;
      padding: 38px 24px 28px;
      border-bottom: 2px solid var(--ink);
      background: var(--panel);
    }}
    .app-header::after {{
      position: absolute;
      right: 0;
      bottom: -2px;
      left: 0;
      height: 6px;
      content: "";
      background: linear-gradient(90deg, var(--accent), var(--accent-strong), var(--accent-warm));
    }}
    .app-header-inner {{
      max-width: 1220px;
      margin: 0 auto;
    }}
    h1 {{
      max-width: 820px;
      margin: 0 0 14px;
      font-size: clamp(30px, 4vw, 54px);
      line-height: 1.05;
      letter-spacing: 0;
    }}
    .summary {{
      margin: 0;
      color: var(--muted);
      font-size: 15px;
      line-height: 1.8;
    }}
    main {{
      max-width: 1220px;
      margin: 0 auto;
      padding: 28px 24px 42px;
    }}
    .project-card {{
      margin-bottom: 28px;
      padding: 24px;
      background: var(--panel);
      border: 2px solid var(--ink);
      border-radius: 8px;
      box-shadow: 8px 8px 0 var(--shadow);
    }}
    .project-header {{
      display: flex;
      justify-content: space-between;
      gap: 18px;
      align-items: center;
      margin-bottom: 20px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--line);
    }}
    .project-heading {{
      display: flex;
      min-width: 0;
      gap: 14px;
      align-items: center;
    }}
    .project-index {{
      display: inline-flex;
      flex: 0 0 auto;
      width: 46px;
      height: 46px;
      align-items: center;
      justify-content: center;
      border: 2px solid var(--ink);
      border-radius: 8px;
      background: var(--accent-warm);
      color: var(--ink);
      font-weight: 700;
      font-variant-numeric: tabular-nums;
    }}
    .project-label, .prompt-kicker {{
      margin: 0 0 4px;
      color: var(--accent-strong);
      font-size: 12px;
      font-weight: 700;
      line-height: 1.3;
    }}
    .project-header h2 {{
      margin: 0;
      font-size: clamp(21px, 2vw, 30px);
      line-height: 1.25;
    }}
    .section-count {{
      flex: 0 0 auto;
      padding: 7px 10px;
      border: 1px solid var(--line);
      border-radius: 999px;
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }}
    .section-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 0 26px;
      border-top: 1px solid var(--line);
    }}
    .section {{
      min-width: 0;
      padding: 16px 0 14px;
      border-bottom: 1px solid var(--line);
    }}
    .section h3, .dev-prompt h3 {{
      margin: 0 0 8px;
      font-size: 15px;
      color: var(--ink);
      line-height: 1.35;
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
      margin-top: 20px;
      border-radius: 8px;
      overflow: hidden;
      border: 2px solid var(--prompt-bg);
      background: var(--prompt-bg);
      color: var(--prompt-ink);
    }}
    .prompt-title {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      padding: 14px 16px;
      border-bottom: 1px solid rgba(255, 248, 232, 0.2);
    }}
    .prompt-title h3 {{
      margin: 0;
      color: var(--prompt-ink);
    }}
    .prompt-kicker {{
      color: #f4c430;
    }}
    button {{
      flex: 0 0 auto;
      border: 1px solid rgba(255, 248, 232, 0.55);
      border-radius: 6px;
      background: #fff8e8;
      color: var(--ink);
      padding: 8px 12px;
      cursor: pointer;
      font: inherit;
      font-size: 14px;
      transition: transform 160ms ease, background-color 160ms ease;
    }}
    button:hover {{
      background: #f4c430;
      transform: translateY(-1px);
    }}
    button:focus-visible {{
      outline: 3px solid var(--focus);
      outline-offset: 3px;
    }}
    .prompt-body {{
      padding: 16px;
    }}
    .prompt-body p, .prompt-body li {{
      color: var(--prompt-ink);
      font-size: 14px;
      line-height: 1.8;
    }}
    code {{
      background: rgba(8, 127, 104, 0.12);
      border-radius: 4px;
      padding: 2px 4px;
      font-family: "Cascadia Code", "SFMono-Regular", Consolas, monospace;
    }}
    pre {{
      overflow: auto;
      padding: 12px;
      border-radius: 6px;
      background: #0f100c;
      color: var(--prompt-ink);
      font-family: "Cascadia Code", "SFMono-Regular", Consolas, monospace;
      line-height: 1.7;
    }}
    .raw-markdown {{
      border-top: 0;
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
      .project-header {{
        align-items: flex-start;
        flex-direction: column;
      }}
      .section-grid {{
        grid-template-columns: 1fr;
      }}
      .prompt-title {{
        align-items: flex-start;
        flex-direction: column;
      }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      html {{
        scroll-behavior: auto;
      }}
      button {{
        transition: none;
      }}
      button:hover {{
        transform: none;
      }}
    }}
  </style>
</head>
<body>
  <header class="app-header">
    <div class="app-header-inner">
      <h1>{html.escape(title)}</h1>
      <p class="summary">生成时间：{generatedAt} · 文件时间戳：{html.escape(stamp)} · 项目数：{len(projects)}</p>
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
        const original = button.textContent
        try {{
          if (!navigator.clipboard) {{
            throw new Error("clipboard unavailable")
          }}
          await navigator.clipboard.writeText(text)
          button.textContent = "已复制"
        }} catch (error) {{
          button.textContent = "复制失败"
        }} finally {{
          setTimeout(() => {{
            button.textContent = original
          }}, 1200)
        }}
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
