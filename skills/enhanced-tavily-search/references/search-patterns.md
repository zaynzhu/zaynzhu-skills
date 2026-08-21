# Tavily Search Patterns

## 参数选择建议

- 用户问最新事件、今天新闻、市场波动、体育比分、政策更新时，用 `--topic news`
- 用户说“最新”“今天”“最近”，优先加 `--time-range day` 或 `--time-range week`
- 结果质量优先于速度时，用 `--search-depth advanced`
- 快速侦察、只需要前几条结果和简短摘要时，用 `--search-depth fast`
- 需要权威来源时，用 `--include-domains`
- 查询中有必须精确匹配的短语或实体时，用 `--exact-match`
- 结果太杂时，把 `--min-score` 提到 `0.55` 或更高

## 输出建议

- 默认使用 Markdown 输出，方便直接纳入最终回答
- 对时效性问题，回答中保留具体日期，不只写“今天”或“最近”
- 片段不宜过长；默认摘要长度足够即可
- 只有在调试、自动化处理、或需要完整原始响应时再切到 `--format json`
- 回答结尾保留来源列表，方便引用与复查

## 示例命令

```powershell
python .\scripts\tavily_search.py "OpenAI API pricing" --include-domains openai.com platform.openai.com
python .\scripts\tavily_search.py "NVIDIA earnings latest" --topic news --time-range week --search-depth advanced
python .\scripts\tavily_search.py "\"John Smith\" CEO Acme" --exact-match --format json
```
