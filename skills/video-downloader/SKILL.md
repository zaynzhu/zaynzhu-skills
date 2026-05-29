---
name: video-downloader
description: 下载 YouTube、Bilibili（B站）、抖音（Douyin）、Twitter/X、Instagram、TikTok 视频或图集。基于 yt-dlp 核心引擎，抖音支持三级 fallback（yt-dlp → API → Playwright）。当用户提到"帮我下载这个视频""下载这个 B 站/抖音/YouTube 链接""批量下载视频""查看视频信息不下载"时触发。核心实现已 vendored 在 vendor/video-downloader/，开箱即用；也可通过 --project-root 或环境变量指向外部安装。
compatibility:
  tools: [bash, python]
  requires:
    - Python >= 3.8
    - 依赖见 vendor/video-downloader/requirements.txt
    - Playwright 浏览器（仅当底层实现对抖音/TikTok 需要浏览器自动化时）
---

# Video Downloader Skill

这个 skill 包含完整的下载器实现（vendored 在 `vendor/video-downloader/`），可以开箱即用。

入口脚本：

- `scripts/video_downloader_bridge.py`

解析顺序：

1. `--project-root <path>` 指定的本地项目目录
2. 环境变量 `VIDEO_DOWNLOADER_PROJECT`
3. `vendor/video-downloader/`（已内置，默认命中）
4. 当前 Python 环境里可导入的 `video_downloader` 模块

如果四者都没有，它会明确报错。

## 安装依赖

首次使用前，安装 vendor 内项目的 Python 依赖：

```bash
pip install -r skills/video-downloader/vendor/video-downloader/requirements.txt
```

抖音/TikTok 平台还需要 Playwright 浏览器：

```bash
playwright install chromium
```

## 先做什么

第一次使用，先跑体检：

```bash
python scripts/video_downloader_bridge.py doctor
```

如果你已经有另一个本地实现目录：

```bash
python scripts/video_downloader_bridge.py doctor --project-root /path/to/video-downloader
```

或者设置环境变量：

```bash
# PowerShell
$env:VIDEO_DOWNLOADER_PROJECT="/path/to/video-downloader"

# bash
export VIDEO_DOWNLOADER_PROJECT=/path/to/video-downloader
```

## 典型用法

### 1. 下载单个视频

```bash
python scripts/video_downloader_bridge.py run -- [URL]
```

### 2. 指定输出目录、画质、Cookie

```bash
python scripts/video_downloader_bridge.py run -- \
  -o ./downloads \
  -q 1080P \
  -c cookies.txt \
  [URL]
```

### 3. 批量下载

```bash
python scripts/video_downloader_bridge.py run -- URL1 URL2 URL3
```

### 4. 只看元数据，不下载

```bash
python scripts/video_downloader_bridge.py run -- --metadata-only [URL]
```

### 5. 启动 MCP Server

```bash
python scripts/video_downloader_bridge.py mcp
```

如果只解析到 site-packages 里的模块（而非 vendor 或 project-root），包装层无法猜测 MCP 入口，会退回显示模块帮助信息。

## 使用策略

收到下载请求后，按这个顺序处理：

- 先判断用户是要"下载"、还是"只看信息"
- 先跑 `doctor`，确认运行时来源
- 如果没找到运行时，提示用户安装依赖或检查 vendor 目录
- 如果找到运行时，再用 `run` 透传参数
- 需要 MCP 时，优先要求明确的 `--project-root`

## 什么时候需要指定本地项目目录

以下情况优先让用户提供 `--project-root` 或 `VIDEO_DOWNLOADER_PROJECT`：

- 需要启动 `mcp_server.py`（vendor 内已包含，一般不需要额外指定）
- 用户明确说他有一个本地 checkout，想覆盖 vendor 版本
- 你需要确认底层实现版本，而不是使用 vendor 或已安装模块

## 常见问题

### 找不到运行时

先跑：

```bash
python scripts/video_downloader_bridge.py doctor
```

如果输出里：

- `module_importable` 是 `False`
- `project_root` 没设置且 vendor 目录不存在

那就说明依赖缺失。你需要：

- 检查 `vendor/video-downloader/` 是否存在，或
- 安装可导入的 `video_downloader` 模块，或
- 用 `--project-root` 提供一个本地项目目录

### 抖音需要浏览器自动化

抖音使用三级 fallback：yt-dlp（快）→ 直接 API → Playwright 浏览器（稳定）。如果前两级都失败，需要安装 Playwright：

```bash
playwright install chromium
```

YouTube、Bilibili、Twitter/X、Instagram、TikTok 由 yt-dlp 直接支持，不需要 Playwright。

### 403 / 反爬被拦

包装层只负责转发参数。优先尝试把 Cookie、代理、超时等参数直接透传给底层实现：

```bash
python scripts/video_downloader_bridge.py run -- \
  -c cookies.txt \
  --proxy http://127.0.0.1:7890 \
  --timeout 120 \
  [URL]
```

## 当前仓库内文件结构

```text
video-downloader/
├── SKILL.md
├── scripts/
│   └── video_downloader_bridge.py    ← 入口/包装脚本
└── vendor/
    └── video-downloader/             ← 核心实现（已 vendored）
        ├── video_downloader/          ← Python 包
        │   ├── extractors/
        │   │   ├── yt_dlp.py          ← yt-dlp 提取器（6 平台）
        │   │   ├── bilibili.py        ← Bilibili 备选提取器
        │   │   └── douyin.py          ← 抖音三级 fallback
        │   ├── core.py, cli.py, ...
        ├── mcp_server.py
        ├── setup.py
        ├── requirements.txt
        ├── USAGE.md
        └── cookies/                   ← Cookie 示例文件
```

## 更新与同步

vendor 目录里的代码是从外部 video-downloader 项目手动拷入的。如果上游有更新：

1. 用新版本覆盖 `vendor/video-downloader/` 内容（排除 `__pycache__/`、`downloads/`、`.pytest_cache/` 等）
2. 运行 `doctor` 确认解析正常

如果以后希望自动化同步，可以改用 git subtree 或 git submodule。