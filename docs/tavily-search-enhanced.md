# tavily-search-enhanced

Tavily 联网搜索增强版——把原始搜索响应整理成可直接回答用户的 Markdown 摘要。

## 功能

- 最新资讯 / 时效性问题检索
- 限定权威来源（只看官网、只看 GitHub）
- 精确实体或短语检索
- 降噪筛选（按相关性分数过滤）
- 时间范围过滤（day / week / month / year）
- 同时返回摘要与来源列表

## 依赖

- Python ≥ 3.8
- `TAVILY_API_KEY` 环境变量

## 快速开始

```powershell
# 设置 API Key
$env:TAVILY_API_KEY="tvly-..."

# 基本搜索
cd skills/tavily-search-enhanced
python scripts/tavily_search.py "OpenAI API pricing"

# 限定来源 + 时间范围
python scripts/tavily_search.py "OpenAI latest" --topic news --time-range week --include-domains openai.com

# JSON 格式输出
python scripts/tavily_search.py "query" --format json
```

## 常用参数

| 参数 | 说明 |
|------|------|
| `--topic general\|news\|finance` | 搜索主题 |
| `--search-depth basic\|advanced` | 搜索深度 |
| `--time-range day\|week\|month\|year` | 时间范围 |
| `--include-domains` | 限定域名 |
| `--exclude-domains` | 排除域名 |
| `--exact-match` | 精确匹配 |
| `--min-score` | 最低相关性分数 |

## 文件结构

```
tavily-search-enhanced/
├── SKILL.md      ← 主指令
├── scripts/      ← 搜索脚本
└── references/   ← 参考文档
```