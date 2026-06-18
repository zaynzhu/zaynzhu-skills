# ideastorming

从 AIHOT 最近 AI 热点生成适合个人开发者、适合 vibe coding 的可开发项目选题。

## 功能

- 获取 AIHOT 精选动态、分类动态、关键词动态或指定时间后的动态
- 把热点转换为 1 到 7 天可完成 demo 的项目点子
- 优先输出开发者工具、AI 工作流工具、RAG / 知识库工具、文档处理工具、浏览器插件、小型 SaaS 原型
- 每个项目包含目标用户、核心痛点、MVP、进阶功能、技术栈、展示价值和第一条开发提示词
- 区分普通 AI 资讯简报场景：只想看新闻摘要时应使用 aihot 类技能，本技能只做“热点转项目”

## 依赖

- Python ≥ 3.8
- 可访问 `https://aihot.virxact.com`
- 无需 API Key

## 快速开始

```powershell
cd skills/ideastorming

# 默认精选动态
python scripts/fetch_aihot_items.py --mode selected --take 30

# 指定分类
python scripts/fetch_aihot_items.py --mode selected --category ai-products --take 30

# 精选动态 + 关键词过滤
python scripts/fetch_aihot_items.py --mode selected --query "Agent" --take 30

# 指定起始时间
python scripts/fetch_aihot_items.py --mode selected --since 2026-06-15T00:00:00+08:00 --take 50
```

## 触发词

```
最近 AI 有什么能做成项目
给我 5 个 vibe coding 项目
根据 AI 热点想项目
AIHOT 热点转项目
找一些个人开发者能做的 AI 项目灵感
```

## 常用参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--mode` | `selected` | AIHOT 模式 |
| `--take` | `30` | 获取条数 |
| `--since` | 无 | ISO 时间下限 |
| `--category` | 无 | 分类：`ai-models` / `ai-products` / `industry` / `paper` / `tip` |
| `--query` | 无 | 关键词过滤，可与 `--mode selected` 叠加 |

## 输出结构

每次默认输出 5 到 10 个项目点子。每个项目包含：

- 对应热点
- 背后趋势
- 项目一句话
- 目标用户
- 核心痛点
- MVP 功能
- 进阶功能
- 技术栈建议
- 为什么适合 vibe coding
- 开发难度
- 展示价值
- 第一条开发提示词

## Windows 终端编码

脚本使用 UTF-8 JSON 输出。在 GBK codepage 的 Windows 终端里直接打印中文时可能显示乱码，但重定向到文件或由 Agent 读取时不影响 JSON 内容。

## 文件结构

```
ideastorming/
├── SKILL.md      ← 主指令
└── scripts/      ← AIHOT 抓取脚本
```
