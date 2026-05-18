# coding-ai-digest

Coding AI 排行榜速查卡生成器。

## 功能

实时抓取 star-history.com Coding AI Leaderboard，对每个项目进行 GitHub API 查询 + 网络搜索，生成"能不能用上"速查卡报告。

每张速查卡包含：
- 项目定位和核心机制
- 解决什么问题（痛点分析）
- 适合场景 / 不适合场景
- 真实评价（非营销文案）
- 同类替代对比

## 依赖

- Python ≥ 3.8
- 可选：GitHub Token（速率提升 80x）

## 使用方式

对 AI 说：

```
抓取排行榜
分析榜单项目
coding AI digest
帮我看看这周榜单
```

支持 Weekly / All-time / Monthly 三种榜单类型。

## 文件结构

```
coding-ai-digest/
├── SKILL.md      ← 主指令
└── scripts/      ← 数据抓取脚本
```