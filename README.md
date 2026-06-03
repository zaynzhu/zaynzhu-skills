<div align="center">

# ✦ Zaynzhu Skills

**个人 AI 技能合集** · 将专业工作流封装为可复用的指令集

[![GitHub Stars](https://img.shields.io/github/stars/zaynzhu/zaynzhu-skills?style=flat&logo=github&color=yellow&label=Stars)](https://github.com/zaynzhu/zaynzhu-skills/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/zaynzhu/zaynzhu-skills?style=flat&logo=github&color=purple&label=Forks)](https://github.com/zaynzhu/zaynzhu-skills/network)
[![Last Commit](https://img.shields.io/github/last-commit/zaynzhu/zaynzhu-skills?logo=github&label=Last%20Commit)](https://github.com/zaynzhu/zaynzhu-skills/commits/master)
[![Skills](https://img.shields.io/badge/Skills-12-6366f1?style=flat&logo=sparkles&logoColor=white)](./skills/)
[![Platforms](https://img.shields.io/badge/Platforms-Claude%20Code%20%7C%20Codex%20CLI%20%7C%20OpenCode-3775A9?style=flat&logo=clio&logoColor=white)](./)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Bash](https://img.shields.io/badge/Bash-4.0+-4EAA25?style=flat&logo=gnubash&logoColor=white)](https://www.gnu.org/software/bash/)
[![License](https://img.shields.io/badge/License-MIT-0ea5e9?style=flat&logo=opensourceinitiative&logoColor=white)](./LICENSE)

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
| 🐟 | [**mmy**](./skills/mmy/) | 基于 momoyu.cc 的热榜抓取工具，支持登录获取订阅源（游民、NGA等）和匿名公开源。通过 `commands/` 短命令操作：抓取热榜、列出平台、保存快照/日报、管理关注列表、登录管理、一键打开浏览器 | `stable` |
| 🐾 | [**pet**](./skills/pet/) | CLI 编程伴侣宠物。7 种宠物可选（猫/狗/仓鼠/兔/鹦鹉/龟/鱼），支持进化系统（Lv.5/15/30）、25 个成就、装扮/训练/睡觉互动、接食物小游戏，Hook 自动互动，兼容 Claude Code / Codex CLI / OpenCode | `stable` |
| ✍️ | [**article-creater**](./skills/article-creater/) | 公众号写作工具。支持四种模式：长文（4000-8000字）、短内容（200-800字）、续写、改写。先搜索实时热点素材，再结合风格体系写作 | `stable` |
| 📡 | [**trending-search**](./skills/trending-search/) | X/Twitter 热词搜索工具。搜索最近24小时内指定关键词的高互动帖子，按相关性排序输出 Top 20 速报，关键词可自定义，默认监控 NanoBanana Pro 系列 | `experimental` |
| 📝 | [**readme-creater**](./skills/readme-creater/) | 通用 README 创建器 + 改进器。自动检测项目元数据，生成含徽章、Star History、贡献者网格的炫酷专业 README，支持中英双语和现有 README 智能分析 | `experimental` |
| 🔀 | [**model-router**](./skills/model-router/) | 动态模型切换。在任务执行中根据上下文自动路由到合适的 AI 模型（如遇验证码切换视觉模型），支持 OpenAI/Google/Anthropic/Ollama/自定义，交互式配置，跨平台调用 | `stable` |
| 🤔 | [**model-debate**](./skills/model-debate/) | 多模型辩论。将同一问题丢给多个 AI 模型，各自回答后合成共识或多轮互相批评修正，适用于代码审查、架构决策、方案对比等需要多角度分析的场景 | `stable` |

---

## 使用文档

每个 Skill 的详细使用说明：

| 技能 | 文档 |
|------|------|
| enhanced-skill-creator | [使用文档](./docs/enhanced-skill-creator.md) |
| video-downloader | [使用文档](./docs/video-downloader.md) |
| coding-ai-digest | [使用文档](./docs/coding-ai-digest.md) |
| tavily-search-enhanced | [使用文档](./docs/tavily-search-enhanced.md) |
| m3u8-downloader | [使用文档](./docs/m3u8-downloader.md) |
| mmy | [使用文档](./docs/mmy.md) |
| pet | [使用文档](./docs/pet.md) |
| trending-search | [使用文档](./docs/trending-search.md) |
| article-creater | [使用文档](./docs/article-creater.md) |
| readme-creater | [使用文档](./docs/readme-creater.md) |
| model-router | [使用文档](./docs/model-router.md) |
| model-debate | [使用文档](./docs/model-debate.md) |

---

## 如何使用这些 Skill

### 方式一：在支持 Skills 的 AI 工具中安装（推荐）

**适用于**：Claude Code、支持 `.skill` 文件的工具

```bash
# 1. 克隆本仓库
git clone https://github.com/zaynzhu/zaynzhu-skills.git

# 2. 进入想要使用的 skill 目录
cd zaynzhu-skills/skills/enhanced-skill-creator

# 3. 将 skill 目录路径告知 AI 工具，或通过工具的 skill 管理界面安装
```

### 方式二：直接读取 SKILL.md（通用）

**适用于**：任意支持自定义系统提示的 AI 工具

```bash
# 克隆仓库
git clone https://github.com/zaynzhu/zaynzhu-skills.git

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
| `mmy` | Python ≥ 3.8 | 无 | momoyu.cc 账号（获取订阅源） |
| `pet` | Bash + jq / Node.js | 无（Claude Code hooks 可选） | Claude Code / Codex CLI / OpenCode |
| `model-debate` | Python ≥ 3.8 | `curl` | 模型 API Key（多模型配置） |
| `trending-search` | Python ≥ 3.8 | `TAVILY_API_KEY` 环境变量 | tavily-search-enhanced skill |
| `readme-creater` | 通用 | 无 | Python ≥ 3.8（自动检测脚本） |
| `article-creater` | 通用 | 无 | MCP 搜索工具（实时热点素材） |
| `model-router` | Python ≥ 3.8 | `curl` | 模型 API Key（OPENAI_API_KEY / GOOGLE_API_KEY / ANTHROPIC_API_KEY 等） |

> **video-downloader** 核心实现已 vendored 在 `skills/video-downloader/vendor/video-downloader/`，开箱即用；首次使用前运行 `python scripts/video_downloader_bridge.py doctor` 检查运行时状态
>
> **coding-ai-digest** 推荐配置 Tavily Search 以获得最佳数据质量
>
> **tavily-search-enhanced** 依赖 Tavily API Key，建议用环境变量方式注入
>
> **m3u8-downloader** 依赖 ffmpeg，首次使用前请确认已安装
>
> **trending-search** 依赖 Tavily API Key，关键词可自定义（不仅限于 NanoBanana Pro，也支持 gemini3、OpenAI image 2.0 等任意关键词）
>
> **model-router** 支持 OpenAI/Google/Anthropic/Ollama 及兼容 OpenAI 协议的自定义模型（如 MiMo-V2.5），通过 `model_config.py add` 交互式配置

---

## 目录结构

```
zaynzhu-skills/
├── README.md
├── docs/                   ← 各技能使用文档
│   ├── enhanced-skill-creator.md
│   ├── video-downloader.md
│   ├── coding-ai-digest.md
│   ├── tavily-search-enhanced.md
│   ├── m3u8-downloader.md
│   ├── mmy.md
│   ├── pet.md
│   ├── trending-search.md
│   └── model-debate.md
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
