<div align="center">

# ✦ Skill Hub

**个人 AI 技能合集** · 将专业工作流封装为可复用的指令集

[![Skills](https://img.shields.io/badge/skills-6-6366f1?style=flat-square&logo=sparkles&logoColor=white)](./skills/)
[![License](https://img.shields.io/badge/license-MIT-0ea5e9?style=flat-square)](./LICENSE)

</div>

---

## 什么是 Skill？

Skill 是封装了特定专业知识和工作流程的指令集，让 AI 在垂直任务上达到专家水准。每个 Skill 放在 `skills/` 下的独立目录中，包含一个 `SKILL.md` 主文件和可选的辅助资源。

---

## 技能索引

| &nbsp; | 技能 | 简介 | 状态 |
|:------:|------|------|:----:|
| 🛠️ | [**enhanced-skill-creator**](./skills/enhanced-skill-creator/) | Skill 全生命周期管理工具。支持需求收集、草稿自审、分层测试（L1/L2/L3）、量化评测、描述优化和打包交付，内置 5 类技能模板库 | `stable` |
| 📥 | [**video-downloader**](./skills/video-downloader/) | Bilibili / 抖音 / TikTok 视频下载与元数据查看。核心实现已 vendored 在 `vendor/video-downloader/`，开箱即用；也可通过 `--project-root` 或环境变量指向外部安装 | `stable` |
| 📊 | [**coding-ai-digest**](./skills/coding-ai-digest/) | 实时抓取 star-history.com Coding AI 排行榜，对每个项目进行 GitHub API 查询 + 网络搜索，生成「能不能用上」速查卡报告，包含核心机制、适用场景、真实评价与注意事项 | `stable` |
| 🔎 | [**tavily-search-enhanced**](./skills/tavily-search-enhanced/) | Tavily 联网搜索增强版。把原始搜索响应整理成适合直接回答用户的 Markdown 摘要，支持新闻模式、时间过滤、域名限定、精确匹配和结果打分筛选 | `stable` |
| 🎬 | [**m3u8-downloader**](./skills/m3u8-downloader/) | M3U8 视频流下载工具。基于 ffmpeg 下载 m3u8 流并转换为 MP4/TS 格式，支持自定义 Header、代理、自动命名和进度显示 | `stable` |
| 🐟 | [**momoyu-fetch**](./skills/mmy/) | 基于 momoyu.cc 的跨平台公开热榜抓取工具。通过 `commands/` 短命令操作：抓取热榜、列出平台、保存快照/日报、管理关注列表、一键打开浏览器 | `stable` |

---

## 如何使用这些 Skill

### 方式一：在支持 Skills 的 AI 工具中安装（推荐）

**适用于**：Claude Code、支持 `.skill` 文件的工具

```bash
# 1. 克隆本仓库
git clone https://github.com/zaynzhu/person-skill-hub.git

# 2. 进入想要使用的 skill 目录
cd person-skill-hub/skills/enhanced-skill-creator

# 3. 将 skill 目录路径告知 AI 工具，或通过工具的 skill 管理界面安装
```

### 方式二：直接读取 SKILL.md（通用）

**适用于**：任意支持自定义系统提示的 AI 工具

```bash
# 克隆仓库
git clone https://github.com/zaynzhu/person-skill-hub.git

# 在对话中告知 AI：
# "请阅读 <path>/skills/<skill-name>/SKILL.md 并按照其中的指令工作"
```

### 方式三：直接复制粘贴（最简单）

打开对应 skill 目录下的 `SKILL.md`，将其内容复制到 AI 工具的系统提示（System Prompt）或对话开头即可。

---

## 各 Skill 依赖说明

| Skill | 运行环境 | 必需工具 | 可选 |
|-------|---------|---------|------|
| `enhanced-skill-creator` | 通用 | 无 | Python（描述优化脚本） |
| `video-downloader` | Python ≥ 3.8 | 无（vendor 内含完整实现） | `playwright`（是否需要取决于底层实现） |
| `coding-ai-digest` | Python ≥ 3.8 | 无（搜索服务自动选择） | GitHub Token（速率提升 80x） |
| `tavily-search-enhanced` | Python ≥ 3.8 | `TAVILY_API_KEY` 环境变量 | Tavily Search API |
| `m3u8-downloader` | Bash | `ffmpeg` | 无 |
| `momoyu-fetch` | Python ≥ 3.8 | 无 | 无 |

> **video-downloader** 核心实现已 vendored 在 `skills/video-downloader/vendor/video-downloader/`，开箱即用；首次使用前运行 `python scripts/video_downloader_bridge.py doctor` 检查运行时状态
>
> **coding-ai-digest** 推荐配置 Tavily Search 以获得最佳数据质量
>
> **tavily-search-enhanced** 依赖 Tavily API Key，建议用环境变量方式注入
>
> **m3u8-downloader** 依赖 ffmpeg，首次使用前请确认已安装

---

## 目录结构

```
skill-hub/
├── README.md
└── skills/
    └── <skill-name>/
        ├── SKILL.md          ← 主指令文件（必须）
        ├── commands/         ← 短命令脚本（可选）
        ├── scripts/          ← 辅助脚本（可选）
        ├── vendor/           ← 第三方实现（可选）
        ├── agents/           ← 子 agent 指令（可选）
        ├── references/       ← 参考文档（可选）
        └── assets/           ← 静态资源（可选）
```

---

## 添加新技能

```bash
# 1. 新建目录（小写连字符命名）
mkdir skills/my-new-skill

# 2. 创建 SKILL.md（含 YAML frontmatter）
touch skills/my-new-skill/SKILL.md

# 3. 在本文件的技能索引中补充一行记录
```

---

<div align="center">
<sub>持续更新中 · 欢迎 Fork 构建你自己的技能库</sub>
</div>
