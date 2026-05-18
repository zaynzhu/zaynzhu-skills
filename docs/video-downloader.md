# video-downloader

Bilibili（B站）、抖音、TikTok 视频下载与元数据查看。

## 功能

- 下载 B 站 / 抖音 / TikTok 视频或图集
- 批量下载、指定画质、自定义输出目录
- 只看元数据不下载
- 支持 MCP Server 模式

## 依赖

- Python ≥ 3.8
- `pip install -r skills/video-downloader/vendor/video-downloader/requirements.txt`
- 抖音 / TikTok 平台还需：`playwright install chromium`

## 快速开始

```bash
# 首次使用，先跑体检
python scripts/video_downloader_bridge.py doctor

# 下载单个视频
python scripts/video_downloader_bridge.py run -- [URL]

# 指定目录和画质
python scripts/video_downloader_bridge.py run -- -o ./downloads -q 1080P [URL]

# 批量下载
python scripts/video_downloader_bridge.py run -- URL1 URL2 URL3

# 只看元数据
python scripts/video_downloader_bridge.py run -- --metadata-only [URL]
```

## 使用方式

对 AI 说：

```
帮我下载这个视频 [粘贴链接]
下载这个 B 站视频
查看这个视频信息但不下载
```

## 文件结构

```
video-downloader/
├── SKILL.md      ← 主指令
├── scripts/      ← 入口脚本
└── vendor/       ← vendored 核心实现（开箱即用）
```