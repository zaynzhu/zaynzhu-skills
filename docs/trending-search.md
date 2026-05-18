# trending-search

X/Twitter 热词搜索工具——搜索最近 24 小时内指定关键词的高互动帖子，生成结构化速报。

## 功能

- 自定义关键词搜索 X/Twitter 热帖
- 按相关性排序输出 Top 20 速报
- 默认监控 NanoBanana Pro 系列，也支持任意关键词（gemini3、OpenAI image 2.0 等）
- 补充互动数据（通过 WebSearch 获取点赞/浏览数）

## 依赖

- Python ≥ 3.8
- `TAVILY_API_KEY` 环境变量
- 推荐：tavily-search-enhanced skill

## 快速开始

```powershell
# 设置 API Key
$env:TAVILY_API_KEY="tvly-..."

cd skills/trending-search

# 默认关键词（NanoBanana Pro 系列）
python scripts/search_tweets.py

# 自定义关键词
python scripts/search_tweets.py --keywords "gemini3" "OpenAI image 2.0"

# 追加关键词（在默认基础上追加）
python scripts/search_tweets.py --extra-keywords "gpt-image-1"

# 调整筛选阈值
python scripts/search_tweets.py --min-likes 50 --min-views 5000

# 限制结果数量
python scripts/search_tweets.py --max-results 10
```

## 触发词

```
热词搜索 / 热搜速报
trending search / hot posts
监控 gemini3 热帖
看看 OpenAI 最近火了什么
/trending 或 /ts
```

## 常用参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--keywords` | NanoBanana Pro 系列 | 完全替换默认关键词 |
| `--extra-keywords` | 无 | 在默认基础上追加关键词 |
| `--min-likes` | 30 | 最低点赞数 |
| `--min-views` | 10000 | 最低浏览量 |
| `--max-results` | 20 | 最多返回条数 |
| `--format` | `md` | 输出格式：`md` 或 `json` |

## 输出说明

脚本输出点赞/浏览数据标注为"数据暂缺"（Tavily API 不返回互动数据），需由 AI 通过 WebSearch 逐条补充。

## 文件结构

```
trending-search/
├── SKILL.md          ← 主指令
├── scripts/          ← 搜索脚本
└── references/       ← 输出模板
```