---
name: coding-ai-digest
description: 实时抓取 star-history.com Coding AI Leaderboard 最新排行榜，对每个项目进行 GitHub API 查询 + 网络搜索，生成"能不能用上"速查卡报告。每张卡包含：项目定位、核心机制、适用场景、安装方式、真实评价与注意事项。使用此 skill 的触发词：「抓取排行榜」「leaderboard 分析」「coding AI digest」「分析榜单项目」「帮我看看这周榜单」，或用户希望了解当前最热门 AI 编程工具时。
---

# Coding AI Digest Skill

每次调用时：**实时抓取** Leaderboard → **批量查询** GitHub API → **搜索**每个项目详情 → 生成**速查卡报告**。

---

## 核心能力

本 Skill 为用户提供：
1. **快速了解热门项目**：用一句话概括每个项目的定位
2. **深入理解核心机制**：技术架构、工作流程、关键创新点、对比表格
3. **明确解决什么问题**：痛点分析、具体场景示例、对比表格
4. **判断是否适合自己**：适合场景表格、不适合场景表格、需评估场景
5. **获取真实评价**：正面和负面评价，标注来源，不是官方营销文案
6. **注意事项提醒**：已知 bug、局限性、风险点
7. **同类替代对比**：快速了解其他选择

---

## 执行流程

### Step 0：确认参数

询问用户（若未指定）：
- **榜单类型**：Weekly（默认）/ All-time / Monthly
- **分析深度**：快速（只看 GitHub 基础信息）/ 深度（加搜索详细介绍，默认）
- **数量**：前 N 名（默认 20）
- **GitHub Token**：是否有（有则速率提升 80x，从 60次/h → 5000次/h）

---

### Step 1：获取 Leaderboard 数据

star-history.com 是动态渲染页面，**无法直接 curl**。使用以下替代策略：

**策略 A（推荐）：网络搜索服务**
```
优先使用 Tavily Search 或其他网络搜索服务
搜索词："star-history coding AI leaderboard weekly trending"
→ 从搜索结果中提取榜单数据（项目名、star增量）
→ 这是最可靠的方式，不依赖本地环境
```

**策略 B：GitHub Search API 模拟榜单**
```bash
# 按最近7天 star 增量排序（weekly 模拟）
# GitHub Search 不直接支持增量，用近期创建+高star作为近似
python3 scripts/fetch_leaderboard.py --mode weekly --top 20
```
⚠️ 注意：Windows 环境下可能失败，此时切换到策略 A

**策略 C：直接访问 star-history.com**
```
使用 webfetch 工具访问 https://www.star-history.com/
→ 从页面 HTML 中解析榜单数据
```

**策略 D（最准确）：用户提供**
如果用户已截图或粘贴了项目名列表，直接进入 Step 2。

> 执行 scripts/fetch_leaderboard.py，见脚本文件说明。

---

### Step 2：补全 GitHub 完整仓库名

榜单上的名字常被截断（如 `everything-clau...`），需要搜索补全：

```bash
python3 scripts/resolve_repos.py --names "mempalace,hermes-agent,graphify,..."
```

输出格式：
```json
[
  {"query": "mempalace", "full_name": "milla-jovovich/mempalace", "stars": 34000, "confidence": "high"},
  {"query": "everything-clau...", "full_name": "affaan-m/everything-claude-code", "stars": 8200, "confidence": "medium"}
]
```

confidence 说明：
- `high`：名字完全匹配且 star 数量与榜单周增量吻合
- `medium`：前缀匹配，需人工确认
- `low`：搜索到多个候选，输出所有候选供选择

---

### Step 3：批量获取 GitHub 详情

```bash
python3 scripts/fetch_github_details.py \
  --repos "milla-jovovich/mempalace,NousResearch/hermes-agent,..." \
  --token "$GITHUB_TOKEN"  # 可选，无则匿名60次/h
```

每个项目获取：
- `full_name`, `description`, `language`, `stargazers_count`
- `forks_count`, `open_issues_count`, `updated_at`
- `topics[]`, `license.name`, `homepage`
- `created_at`（判断项目新旧）

---

### Step 4：搜索项目详情（深度模式）

对每个项目执行网络搜索，关键词模板：
```
"{repo_name} GitHub 使用教程 OR review OR 怎么用 2026"
"{repo_name} claude code skill install"
"{owner}/{repo_name} GitHub 介绍 特点"
```

**推荐使用 Tavily Search**：
```bash
python tavily.py "{repo_name} GitHub review"
→ 返回结构化搜索结果，包含 AI 总结
```

提取：
- 核心功能描述（用自己的话总结，不是复制）
- 技术架构和组件
- 安装命令（精确复制）
- 真实用户评价（从 HN/Reddit/博客，正面和负面都要）
- 已知 bug 或局限性
- 与同类工具对比
- 具体使用场景和痛点

**每条搜索结果的输出要求**：
1. 正面评价：至少 3 条，标注来源
2. 负面评价：至少 3 条，标注来源
3. 注意事项：至少 4 条，编号列出

---

### Step 5：生成速查卡报告

**每个项目输出格式：**

```markdown
## #N 项目名 ⭐ 总stars (+本周增量)

> 一句话定位：这是一个 [做什么] 的 [类型：skill/agent/工具/框架]

### 🔧 核心机制（深入解析）

**技术架构**
[列出项目的技术栈和核心组件，如语言、框架、存储方案等]

**工作流程详解**
[用文字或伪代码描述从用户输入到结果输出的完整流程]

```
用户输入 → 处理步骤 → 输出结果
         ↓
         中间组件说明
```

**关键创新点**
[列出 3-5 个让这个项目与众不同的创新点]

**与同类工具对比表**
| 特性 | 本项目 | 同类工具A | 同类工具B |
|------|--------|-----------|-----------|
| 特性1 | ✓ | ✗ | ✓ |
| 特性2 | ... | ... | ... |

### 🎯 解决什么问题（痛点分析）

**痛点 1：[具体痛点名称]**

| 问题维度 | 没有本项目时 | 有本项目后 |
|----------|-------------|-----------|
| 现状 | [描述用户当前的困扰] | [描述项目如何解决] |
| 用户困扰 | [具体的痛苦场景] | [解决方案] |

**具体场景示例**：
[用实际场景说明痛点，比如"你一个月前做了某个决策，现在想回顾理由，但找不到当时的讨论"]

**痛点 2-5**：[重复上述结构，列出至少 3 个痛点]

### 👤 适合我吗？（场景匹配分析）

**✅ 高度适合的场景**

| 场景 | 为什么适合 | 具体收益 |
|------|-----------|----------|
| [具体场景] | [原因] | [收益量化或具体化] |

**至少列出 5 个适合场景**

**❌ 不太适合的场景**

| 场景 | 为什么不适合 | 风险/代价 |
|------|-------------|----------|
| [具体场景] | [原因] | [风险] |

**至少列出 4 个不适合场景**

**⚖️ 中等适合（需要评估）**

| 场景 | 需要评估的因素 |
|------|---------------|
| [具体场景] | [列出2-3个需要考虑的因素] |

### 💡 实际使用建议

**推荐配置策略：**
[列出 2-3 种不同场景下的推荐配置方案，带具体代码示例]

**安装方式**
```bash
# 最简安装命令
```
支持平台：Claude Code / Codex / OpenCode / Cursor...

**真实评价**
**正面评价**：
- "[引用真实评价，标注来源]"（HN/Reddit/博客）
- 至少列出 3 条正面评价

**负面评价**：
- "[引用真实负面评价，标注来源]"
- 至少列出 3 条负面评价

**注意事项**
1. [已知 bug、局限、坑点，编号列出]
2. 至少列出 4 个注意事项

**同类替代**

| 替代方案 | 差异 |
|----------|------|
| [替代项目名] | [具体差异说明] |

---
```

**报告最后附汇总表：**

| 排名 | 项目 | 类型 | 周增量 | 推荐指数 | 一句话 |
|------|------|------|--------|----------|--------|
| 1 | mempalace | 记忆系统 | +6.6k | ⭐⭐⭐ | 本地离线AI记忆，适合重度Claude用户 |

---

## 输出规范

- 语言：中文（代码、命令保持英文）
- 长度：每张卡 300-500 字（核心机制、解决问题、适合场景要深入）
- 评价立场：中立客观，明确指出局限性
- 安装命令：必须可执行，不写假命令
- 不复制粘贴官方描述，必须用自己理解重写
- **核心机制、解决什么问题、适合我吗**：这三个部分必须深入展开，使用表格对比、具体场景示例、编号列出等格式

---

## 输出保存要求

**必须将报告保存为 Markdown 文件**：

1. **文件名格式**：`coding-ai-leaderboard-{YYYY-MM-DD}.md`
2. **保存位置**：当前工作空间根目录
3. **文件头部标注**：
   ```markdown
   # 📊 star-history Coding AI Leaderboard 速查卡报告
   
   **生成时间**：{YYYY-MM-DD HH:MM:SS}
   **榜单时间范围**：{开始日期} - {结束日期}
   **数据来源**：star-history.com、GitHub API、网络搜索
   ```
4. **底部标注**：
   ```markdown
   ---
   
   **报告生成时间**：{YYYY-MM-DD HH:MM:SS}
   **数据来源**：star-history.com、GitHub API、网络搜索
   **分析深度**：深度模式（网络搜索 + GitHub详情）
   ```

---

## 执行中可能遇到的问题及解决方案

### 问题 1：GitHub API 调用失败

**现象**：
```
[ERROR] API 返回非 JSON 内容: ...
[OK] 已保存 0 个项目到 leaderboard.json
```

**原因**：
- Windows 环境下 curl 命令可能有问题
- 未设置 GITHUB_TOKEN 导致速率限制
- 网络问题或 GitHub API 不可用

**解决方案**：
1. **首选**：使用 Tavily Search 或其他网络搜索服务获取榜单数据
2. **备选**：直接访问 star-history.com 网页获取榜单
3. **手动**：让用户提供榜单截图或项目名列表

### 问题 2：本地 Token 服务无法连接

**现象**：
```
ERROR: 无法从本地服务获取 token: <urlopen error [WinError 10061]>
```

**原因**：
- AutoGLM WebSearch 等服务依赖本地 token 服务
- 本地服务未启动或端口被占用

**解决方案**：
1. **切换搜索服务**：使用 Tavily Search（不依赖本地服务）
2. **启动本地服务**：确认本地 token 服务已启动、端口可访问（端口以所用服务自己的配置为准，本技能不内置任何私有端口）
3. **手动搜索**：用浏览器搜索项目详情并总结

### 问题 3：Windows 环境脚本执行问题

**现象**：
- Python 脚本输出编码乱码
- curl 命令行为与 Linux/Mac 不同

**原因**：
- Windows PowerShell 编码问题
- curl 在 Windows 可能是 Invoke-WebRequest 的别名，而非真正的 curl

**解决方案**：
1. **编码处理**：在 Python 脚本开头添加 `sys.stdout.reconfigure(encoding='utf-8')`
2. **curl 替代**：使用 Python 的 urllib.request 或 requests 库代替 curl
3. **PowerShell 处理**：在 PowerShell 中使用 `curl.exe`（真正的 curl）而非 `curl`

### 问题 4：多数据源一致性

**现象**：
- 不同搜索服务返回的项目信息有差异
- Star 数量不一致

**解决方案**：
1. **优先级**：star-history.com 搜索结果 > GitHub API > 其他搜索
2. **标注来源**：在报告中标注每个数据的具体来源
3. **交叉验证**：重要信息（如 Star 数）用多个数据源验证

---

## 数据获取策略（按优先级）

| 策略 | 可靠性 | 速度 | 适用场景 |
|------|--------|------|----------|
| 1. Tavily Search 搜索 star-history | 高 | 快 | 默认使用 |
| 2. 直接访问 star-history.com | 最高 | 中 | 需要最准确数据时 |
| 3. GitHub Search API 模拟 | 中 | 快 | 无网络搜索服务时 |
| 4. 用户提供榜单截图/列表 | 最高 | 最快 | 用户已获取榜单时 |

---

## 脚本文件说明

见 `scripts/` 目录：
- `fetch_leaderboard.py`：模拟抓取 leaderboard（GitHub Search API）
- `resolve_repos.py`：补全截断的项目名
- `fetch_github_details.py`：批量获取 GitHub 仓库详情

若脚本因网络/权限问题失败，退回到 web_search 手动搜索每个项目。

---

## 快速触发示例

用户说这些时触发本 skill：
- "帮我看看这周 star-history 榜单"
- "最近有什么火的 AI 编程工具"
- "coding AI digest"
- "抓一下 leaderboard 分析一下"
- 上传了 star-history 截图并问"这些都是什么"

---

## 用户核心需求（重要）

根据用户反馈，本 Skill 必须重点展开以下三个部分：

### 1. 核心机制（必须深入）

**必须包含**：
- 技术架构（语言、框架、存储方案、核心组件）
- 工作流程详解（伪代码或文字描述从输入到输出的完整流程）
- 关键创新点（3-5个让项目与众不同的创新）
- 与同类工具对比表（至少对比2个同类工具的5个特性）

**长度要求**：300-500 字，使用表格、代码块、编号列表等格式

### 2. 解决什么问题（必须深入）

**必须包含**：
- 痛点编号列出（至少 3 个痛点）
- 每个痛点使用对比表格（没有本项目 vs 有本项目）
- 具体场景示例（用真实场景说明痛点）
- 解决方案说明（项目如何解决每个痛点）

**长度要求**：400-600 字，表格对比 + 场景示例

### 3. 适合我吗？（必须深入）

**必须包含**：
- ✅ 高度适合场景表格（至少 5 个场景，含原因和收益）
- ❌ 不太适合场景表格（至少 4 个场景，含原因和风险）
- ⚖️ 中等适合场景表格（含需评估因素）
- 推荐配置策略（2-3 种不同场景的配置方案）

**长度要求**：300-400 字，使用表格对比

---

## ⚠️ 强制检查机制（防止遗漏项目）

**这是最重要的检查环节，必须在报告生成前后执行！**

### Step 6：完整性检查（必须执行）

**报告生成前检查**：

1. **确认项目数量**：
   ```
   用户要求分析前 N 名 → 必须生成 N 个项目的完整报告
   默认：前 20 名 → 必须生成 20 个项目的完整报告
   ```

2. **记录项目列表**：
   ```
   在开始处理前，先列出所有要分析的项目：
   
   项目清单（共 20 个）：
   1. ultraworkers/claw-code
   2. milla-jovovich/mempalace
   3. NousResearch/hermes-agent
   4. affaan-m/everything-claude-code
   5. VoltAgent/awesome-design-md
   6. santifer/career-ops
   7. siddharthvaddem/openscreen
   8. safishamsi/graphify
   9. obra/superpowers
   10. chenglou/pretext
   11. openclaw/openclaw
   12. msitarzewski/agency-agents
   13. aaif-goose/goose
   14. garrytan/gstack
   15. paperclipai/paperclip
   16. anthropics/claude-code
   17. onyx-dot-app/onyx
   18. karpathy/autoresearch
   19. Yeachan-Heo/oh-my-claudecode
   20. anomalyco/opencode
   
   ⚠️ 每处理完一个项目，标记为已完成 ✓
   ```

3. **进度跟踪**：
   ```
   处理进度：
   #1 ✓ | #2 ✓ | #3 ✓ | #4 ✓ | #5 ✓ | ... | #20 ✓
   
   未完成项目：[列出尚未处理的项目编号]
   ```

**报告生成后检查**：

1. **数量验证**：
   ```bash
   # 检查报告中的项目数量
   grep -c "^## #" coding-ai-leaderboard-{YYYY-MM-DD}.md
   
   # 必须等于用户要求的项目数量（默认20）
   # 如果不等于，必须补充缺失项目
   ```

2. **编号连续性验证**：
   ```bash
   # 检查项目编号是否连续（1-20）
   grep "^## #\d+" coding-ai-leaderboard-{YYYY-MM-DD}.md
   
   # 如果跳号（如 #10 后直接是 #12，跳过 #11），必须补充
   ```

3. **完整性声明**：
   ```markdown
   在报告底部添加完整性声明：
   
   ---
   
   ## ✅ 报告完整性检查
   
   **项目数量**：20 个（完整）
   **编号连续性**：#1-#20（无遗漏）
   **每项内容**：核心机制 + 解决问题 + 适合场景（均完整）
   
   检查时间：{YYYY-MM-DD HH:MM:SS}
   检查结果：通过 ✓
   ```

### 分批处理策略（避免一次性处理导致遗漏）

**如果项目数量超过10个，必须分批处理**：

```
批次划分：
- 第1批：#1-#5（5个项目）
- 第2批：#6-#10（5个项目）
- 第3批：#11-#15（5个项目）
- 第4批：#16-#20（5个项目）

每批处理完成后：
1. 检查该批项目是否都完成
2. 在进度表中标记已完成
3. 继续下一批

全部批次完成后：
1. 执行完整性检查
2. 确认无遗漏
3. 生成完整性声明
```

### 防止遗漏的强制规则

**必须遵守以下规则**：

1. ❌ **禁止跳过项目**：不允许跳过任何项目，即使项目信息较少
2. ❌ **禁止合并项目**：不允许将多个项目合并为一条
3. ❌ **禁止省略内容**：每个项目必须包含核心机制、解决问题、适合场景三个部分
4. ✅ **必须按顺序处理**：严格按照排名顺序处理，#1 → #2 → ... → #20
5. ✅ **必须检查编号**：生成后必须检查编号连续性
6. ✅ **必须补充遗漏**：发现遗漏必须立即补充

---

## 完整示例

参见生成的报告文件：`coding-ai-leaderboard-{YYYY-MM-DD}.md`

**完整报告必须包含**：
- 20 个项目的完整介绍（每个项目包含核心机制、解决问题、适合场景）
- 项目编号连续（#1-#20，无跳号）
- 完整性检查声明（在报告底部）
