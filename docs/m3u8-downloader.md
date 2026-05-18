# m3u8-downloader

M3U8 视频流下载工具，基于 ffmpeg。

## 功能

- 下载 m3u8 视频流并自动转换为 MP4 / TS 格式
- 自定义输出目录、文件名
- 支持 HTTP Header（Referer / Cookie）
- 支持代理

## 依赖

- ffmpeg（`brew install ffmpeg` / `apt install ffmpeg` / `choco install ffmpeg`）

## 快速开始

```bash
# 基本下载（自动命名，保存到 ~/Downloads/）
bash scripts/m3u8_download.sh "https://example.com/video/index.m3u8"

# 指定格式、目录、文件名
bash scripts/m3u8_download.sh -f ts -o ./videos -n "我的视频" "https://example.com/video/index.m3u8"

# 带 Header（需要 Referer 或 Cookie 的站点）
bash scripts/m3u8_download.sh -H "Referer: https://example.com" -H "Cookie: token=abc" "https://example.com/video/index.m3u8"
```

## 使用方式

对 AI 说：

```
帮我下载这个 m3u8 视频
下载这个视频流
```

或直接粘贴 `.m3u8` 链接并表达下载意图。

## 全部参数

| 参数 | 说明 |
|------|------|
| `-o <目录>` | 保存目录（默认 `~/Downloads`） |
| `-n <文件名>` | 文件名，不含扩展名 |
| `-f <格式>` | `mp4` 或 `ts`（默认 mp4） |
| `-H <header>` | 添加 HTTP Header，可多次使用 |
| `-p <proxy>` | 使用 HTTP/SOCKS 代理 |

## 文件结构

```
m3u8-downloader/
├── SKILL.md      ← 主指令
└── scripts/      ← 下载脚本
```