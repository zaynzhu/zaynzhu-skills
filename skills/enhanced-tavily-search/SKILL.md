---
name: enhanced-tavily-search
description: 使用 Tavily Search API 进行结构化联网检索，并把结果整理成适合直接回答用户的 Markdown 摘要。适用于需要最新信息、新闻检索、限定站点搜索、时间范围过滤、结果打分筛选、或需要同时返回摘要与来源列表的场景。用户提到 Tavily、联网搜索、查最新资讯、找资料、限定官网来源、需要引用链接时使用。
---

# Tavily Search Enhanced

把 Tavily 搜索结果从原始 JSON 提升为可直接给用户使用的结构化 Markdown 输出。

运行要求：
- Python >= 3.8
- 已设置 `TAVILY_API_KEY` 环境变量

默认输出包括：
- `Summary`：Tavily 生成的简短结论
- `Top Results`：按相关性排序的结果卡片，包含分数、域名、日期、摘要
- `Sources`：单独列出的来源链接，便于引用和二次打开

---

## 快速开始

先设置 API Key：

```powershell
$env:TAVILY_API_KEY="tvly-..."
```

然后执行：

```powershell
cd skills/enhanced-tavily-search
python .\scripts\tavily_search.py "OpenAI API pricing"
```

如果需要原始响应而不是整理后的展示：

```powershell
python .\scripts\tavily_search.py "OpenAI API pricing" --format json
```

---

## 适用场景

### 1. 最新资讯或时效性问题

适用于：
- 最新新闻
- 财报、市场动态
- 比赛结果、政策变化
- 软件/API 最近更新

推荐参数：

```powershell
python .\scripts\tavily_search.py "OpenAI latest announcements" `
  --topic news `
  --time-range week `
  --search-depth advanced
```

### 2. 限定权威来源

当用户明确要求“只看官网”“只看官方文档”“只看 GitHub”时：

```powershell
python .\scripts\tavily_search.py "Responses API tools" `
  --include-domains openai.com platform.openai.com github.com
```

### 3. 精确实体或短语检索

当查询里有必须精确匹配的人名、产品名、quoted phrase：

```powershell
python .\scripts\tavily_search.py "\"John Smith\" CEO Acme" --exact-match
```

### 4. 降噪筛选

当结果较杂，需要压掉低质量命中时：

```powershell
python .\scripts\tavily_search.py "AI coding tools" --min-score 0.55
```

---

## 输出规范

使用本 Skill 时，默认遵守以下规则：

1. 不直接把整段 JSON 回给用户，除非用户明确要求原始响应
2. 对时效性问题，回答中保留明确日期，不只写“今天”“最近”
3. 展示结果时保留 `score`、域名和可用日期，方便判断可信度
4. 如果结果质量不足，明确指出，而不是强行得出确定结论
5. 回答结尾附来源列表，便于引用

---

## 脚本参数

主脚本：

```powershell
python .\scripts\tavily_search.py "query" [options]
```

常用参数：

- `--format md|json`
- `--topic general|news|finance`
- `--search-depth basic|advanced|fast|ultra-fast`
- `--time-range day|week|month|year`
- `--start-date YYYY-MM-DD`
- `--end-date YYYY-MM-DD`
- `--include-domains domain1 domain2`
- `--exclude-domains domain1 domain2`
- `--exact-match`
- `--min-score 0.6`
- `--include-favicon`
- `--include-images`
- `--include-usage`

更多参数组合建议见 `references/search-patterns.md`。

---

## 输出示例

```markdown
# Tavily Search

Query: OpenAI API pricing
Mode: topic=general, depth=fast, results=5
Meta: response_time=1.23s, credits=1

## Summary
...

## Top Results
[1] OpenAI Pricing
score: 0.94 | domain: openai.com
url: https://openai.com/api/pricing
snippet: ...

## Sources
[1] OpenAI Pricing - https://openai.com/api/pricing
```

---

## 参考文件

- 参数和使用策略：`references/search-patterns.md`
- 执行脚本：`scripts/tavily_search.py`
