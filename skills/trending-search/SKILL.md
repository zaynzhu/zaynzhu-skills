---
name: trending-search
description: |
  X/Twitter 热词搜索工具。搜索最近24小时内包含指定关键词的高互动帖子，按相关性排序输出 Top 20 速报。
  触发词：「热词搜索」「热搜速报」「trending search」「hot posts」「twitter monitor」。
  关键词可自定义，默认监控 NanoBanana Pro 系列关键词，也可搜索任意话题如「搜索 gemini3 热帖」「看看 OpenAI 最近火了什么」。
compatibility:
  tools: [bash, python]
  requires:
    - TAVILY_API_KEY
    - Python >= 3.8
  recommends:
    - tavily-search-enhanced skill
---

# Trending Search — X/Twitter 热词搜索

搜索 X/Twitter 最近24小时内指定关键词的高互动帖子，生成结构化速报。关键词完全自定义，默认使用 NanoBanana Pro 系列。

---

## 快速开始

```powershell
# 默认关键词（NanoBanana Pro 系列）
cd skills/trending-search
python scripts/search_tweets.py

# 自定义关键词
python scripts/search_tweets.py --keywords "gemini3" "OpenAI image 2.0"

# 追加关键词（在默认基础上追加）
python scripts/search_tweets.py --extra-keywords "gpt-image-1" "DALL-E 4"

# 调整筛选阈值
python scripts/search_tweets.py --min-likes 50 --min-views 5000

# 限制结果数量
python scripts/search_tweets.py --max-results 10
```

---

## 核心流程

### Step 1：确认参数

向用户确认（若未指定则使用默认值）：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `keywords` | 见下方默认关键词列表 | 搜索关键词，支持中英文和日语 |
| `min-likes` | 30 | 最低点赞数筛选阈值 |
| `min-views` | 10000 | 最低浏览量筛选阈值（可放宽） |
| `max-results` | 20 | 最多返回条数 |
| `time-range` | 24h | 搜索时间范围 |

**默认关键词列表：**

```
NanoBanana Pro
Nano Banana Pro
NanoBanana Pro 2
ナノバナナプ口       ← 原始拼写（用户提示词中出现的表记）
ナノバナナプロ       ← 正确日语拼写
Gemini Nano Banana
```

用户可以通过 `--keywords` 完全替换，或用 `--extra-keywords` 在默认基础上追加。

### Step 2：执行搜索

使用 Tavily Search API 对每个关键词独立搜索：

```powershell
python scripts/search_tweets.py --keywords "keyword1" "keyword2" [options]
```

搜索策略：
1. 对每个关键词独立搜索，限定 `x.com` / `twitter.com` 域名
2. 使用 `topic: news` + `time-range: day` 过滤时效性
3. 收集所有搜索结果，按推文 ID 去重
4. 按 Tavily 相关性分数排序（Tavily 不返回点赞/浏览数据）

### Step 3：补充互动数据（关键步骤）

脚本输出结果中点赞/浏览标注为"数据暂缺"。**必须手动补充**：

对结果中相关性最高的前 5-10 条帖子，使用 WebSearch 逐条搜索获取互动数据：

```
WebSearch: @{username} {关键词} likes site:x.com
```

如果 WebSearch 也不返回精确数据：
- 在报告中如实标注"点赞/浏览数据暂缺"
- 用相关性分数（score）代替点赞数排序
- 绝不能编造任何互动数据

### Step 4：筛选与排序

筛选规则（按优先级）：
1. **相关性分数 ≥ 0.15** — 低质量结果自动过滤
2. **点赞数 ≥ min-likes**（默认30）—— 有数据时必须满足
3. **浏览量 ≥ min-views**（默认1万）—— 尽量满足，当天整体数据低时可放宽，但需在报告中注明
4. **内容相关性**：必须是原创帖或明显与关键词相关的内容（转发、无关提及应排除）
5. **排序**：有点赞数据时按点赞降序，否则按相关性分数降序

### Step 5：生成速报

按照 `references/output-template.md` 中的严格模板格式输出。

### Step 6：完整性检查

- 验证所有链接格式为 `https://x.com/用户名/status/帖子ID`
- 确认没有编造的用户名、数据或链接
- 如果结果不足 max-results 条，在报告中说明实际找到的数量

---

## 输出规范

**必须严格遵守 `references/output-template.md` 中的模板格式。**

关键要求：
1. **禁止编造**：所有数据、用户名、链接必须来自真实搜索结果，绝不允许凭空捏造
2. **链接真实**：所有 x.com 链接必须可点击，ID 正确
3. **数据透明**：如果搜索结果中没有互动数据，标注"数据暂缺"而非编造数字
4. **低活跃度提示**：当天确实无高互动内容时，诚实输出"今日24小时内暂无突破1万浏览的高互动帖子，社区比较平静"

---

## 重要说明：互动数据的获取

Tavily Search API 返回的结果**不一定包含精确的点赞数和浏览量**。处理互动数据时遵循以下规则：

1. **有数据时**：直接使用搜索结果中的互动数据
2. **部分数据时**：使用搜索结果中的 `score`（Tavily 相关性分数）作为排序参考，点赞/浏览标注为"数据暂缺"
3. **补充搜索**：对高优先级帖子，可使用 WebSearch 工具搜索 "帖子URL 点赞" 或 "帖子URL likes" 获取补充数据
4. **如实标注**：宁可标注"数据暂缺"，也绝不能编造互动数据

脚本中的排序策略：优先按 Tavily `score` 排序，如有 `likes` 数据则按 `likes` 降序。

---

## 降级策略

| 策略 | 条件 | 说明 |
|------|------|------|
| Tavily 搜索 | 默认 | 需要 TAVILY_API_KEY |
| WebSearch 工具 | Tavily 不可用 | 使用内置 WebSearch 工具 |
| 用户手动提供 | 搜索服务均不可用 | 请用户提供截图或链接列表 |

---

## 交互规范

1. 搜索开始前告知用户"正在搜索，请稍候..."
2. 完整输出速报内容到对话中，让用户直接在聊天界面看到
3. 如果搜索结果为空或极少，主动建议放宽筛选条件
4. 用户追问某条帖子时，尝试进一步搜索获取详情

---

## 触发词示例

- "热词搜索"
- "热搜速报"
- "监控 gemini3 热帖"
- "看看 OpenAI image 2.0 最近火了什么"
- "twitter monitor"
- "hot posts monitor"
- "/trending" 或 "/ts"

---

## 参考文件

- 输出模板：`references/output-template.md`
- 搜索脚本：`scripts/search_tweets.py`