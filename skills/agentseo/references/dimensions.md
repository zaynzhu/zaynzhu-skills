# 审计维度释义

AgentSEO 规则审计共 5 个维度，加权合成总分（默认权重见下表）。每个维度返回 `score`（0-100，或 `null` 表跳过）和 `findings[]`（每条含 `level` ∈ `error` / `warn` / `ok`，可选 `evidence`、`suggestion`）。

| 维度 key | 中文名 | 默认权重 | 检查对象 |
|-----------|--------|---------|---------|
| `semanticHtml` | 语义化 HTML | 0.25 | DOM 结构 |
| `structuredData` | 结构化数据 | 0.25 | JSON-LD / Microdata |
| `a11y` | 可访问性 | 0.20 | img alt / 按钮名 / 表单 label / lang |
| `agentFiles` | Agent 文件 | 0.15 | robots.txt / llms.txt / sitemap.xml（需联网） |
| `actionability` | 可操作性 | 0.15 | 表单 action / 按钮定位 / 伪链接 |

> `score` 为 `null` 的维度（如缺 URL 时 `agentFiles` 跳过）不参与总分，剩余维度权重重新归一化。总分 ≥90 为 A，≥75 B，≥60 C，≥40 D，余 F。

下面逐个说明各维度检查什么、计分怎么算、finding 怎么读。本文件供 agent 解读 `npx agentseo --json` 输出时参考，**不要**在报告里照抄本文件，按实际 findings 转述即可。

---

## 1. semanticHtml（语义化 HTML）

**检查什么**：页面 DOM 是否用了语义化标签，让 agent 能靠标签结构而非视觉猜内容边界。4 类检查：

1. **h1 主标题**：必须恰好 1 个。0 个 error 扣 25；>1 个 warn 扣 10。
2. **标题层级跳跃**：如 h1 直接跳 h3。命中 warn 扣 10；连续则 ok。
3. **语义地标**：`<main>`（缺 error 扣 20）、`<nav>`（缺 warn 扣 10）、`<header>`/`<footer>`（缺各 warn 扣 5）。
4. **内容分块**：无 `<article>`/`<section>` warn 扣 10。
5. **div 汤比例**：`div数 / (div数 + 语义块数)`。>80% error 扣 20；>60% warn 扣 10；否则 ok。

**计分**：`max(0, 100 - 累计扣分)`。

**怎么读**：低分通常意味着页面用纯 `<div>` 堆布局，agent 无法区分导航/正文/页脚。`evidence` 给出典型 div 片段，`suggestion` 给替代的语义标签。

---

## 2. structuredData（结构化数据）

**检查什么**：页面有没有 JSON-LD（`<script type="application/ld+json">`），声明了哪些 schema.org 类型。这是 agent 明确理解"本页是什么实体"的最高价值信号。

**计分（分支）**：
- 无任何结构化数据且无 Microdata → **20 分**（error）。
- 仅 Microdata（`itemscope`）无 JSON-LD → **50 分**（warn，多数 agent 优先 JSON-LD）。
- 有 JSON-LD 但全部解析失败 → **35 分**（error）。
- 有合法 JSON-LD：基础 **50 分** + 每种 `@type` 加 10（封顶 5 种 = +50）- 扣分。
  - 部分块解析失败：warn 扣 10。
  - 有 JSON-LD 但无 `@type`：warn 扣 20。
  - 有 `@type` 但无"高价值类型"（Product/Article/Organization/FAQPage/HowTo/Event/JobPosting 等）：warn 扣 10。

**怎么读**：满分 100 需要至少 5 种合法 schema.org 类型且都含高价值类型。20-35 分是"完全没结构化数据"，是最常见的低分原因，`suggestion` 会附 JSON-LD 示例。

---

## 3. a11y（可访问性）

**检查什么**：对人类可访问性的检查同时利好 agent——可访问名、label、lang 都是 agent 理解元素的依据。4 项：

1. **img alt**：缺 alt 的图片占比。`alt=""` 视为显式装饰图，通过。按缺 alt 比例扣分，至少扣 10，最高约 45。
2. **按钮可访问名**：纯图标/无文本按钮 error，每个扣 8（封顶 30）。可访问名来源：aria-label / aria-labelledby / value / title / 内含 img alt / 文本。
3. **表单控件 label**：无任何 label 关联 error 每个扣 6（封顶 25）；仅 placeholder 无 label warn 每个扣 3（封顶 10）。
4. **html lang**：缺 `<html lang>` warn 扣 5。

**计分**：`max(0, 100 - 累计扣分)`。

**怎么读**：a11y 低分说明 agent（和屏幕阅读器）无法知道按钮干什么、表单填什么。修复成本通常低——补 aria-label 和 label 即可。

---

## 4. agentFiles（Agent 文件）

**检查什么**：目标站 well-known 文件对 AI agent 的可达性。**需要联网**，抓取 `{origin}/robots.txt`、`/llms.txt`、`/sitemap.xml`。无 URL 时整维跳过（`score: null`）。

> 注意 SPA 陷阱：很多 SPA 站对任意路径都回退返回 `index.html`（伪 200）。检查器会识别返回体是否像 HTML，像 HTML 则判为"非真实文件"。

1. **robots.txt AI 爬虫可达性**：
   - 缺失：warn 不扣分（默认放行），提示可声明规则。
   - 全站屏蔽 AI **访问/搜索**爬虫（如 GPTBot 等访问类）：error，每只扣 6，封顶 35。
   - 屏蔽 AI **训练**爬虫（如训练类）：warn 不扣分（常是站主有意为之）。
2. **/llms.txt**：缺失 error 扣 50；存在但内容太简单（缺 Markdown 标题 / 缺链接 / < 200 字符）warn 扣 15；完整则 ok。
3. **/sitemap.xml**：缺失 error 扣 40；存在但无 `<url>`/`<sitemap>` 条目 warn 扣 10；正常则 ok。

**计分**：`max(0, 100 - 累计扣分)`。

**怎么读**：这是唯一需要联网的维度。报告里若它 `score: null`，说明 `--url` 没传或解析失败，不是站点问题。低分常因没部署 `/llms.txt`——这是对 agent 导览价值最高的文件。

> ⚠️ **origin 语义陷阱（重要）**：agentFiles 查的是 `--url` 的 **origin**（协议+域名），不是被审页面本身。当你审计的是大平台上的某个子路径（如 `github.com/<owner>/<repo>`、`<用户>.gitlab.io/<项目>`、`<tenant>.notion.site/<page>`），agentFiles 拿到的 robots/llms.txt/sitemap 分数反映的是 **github.com / gitlab.io / notion.site 整站策略**，不是你审的那个仓库/项目能控制的。例如审计一个 GitHub 仓库页，agentFiles 常因 github.com 全站屏蔽 AI 爬虫而得低分——这不是该仓库的问题，报告里必须点明"此项反映平台整站策略，非被审页面可控"，避免误导用户去改自己改不了的东西。判断标准：被审 URL 的 origin 是否属于一个你不拥有的大平台；是则标注。

---

## 5. actionability（可操作性）

**检查什么**：页面上的可交互元素能否被 agent 稳定定位并正确触发。规则层面的"可操作性"——真正的实证由 skill 的 Step 3 完成。4 项：

1. **表单可执行性**：`<form>` 缺 `action` warn 每个扣 10（封顶 25）；表单控件缺 `name` error 每个扣 5（封顶 20）。无表单则跳过该项 ok。
2. **按钮稳定定位**：按钮缺 `id`/`name`/`data-*`/`aria-label`（只能靠易变的 class 定位）error，按比例扣 10-30。
3. **伪链接**：`<a>` 无有效 href（`""`/`#`/`javascript:`）warn 每个扣 3（封顶 15）——agent 无法识别为导航。
4. **非语义点击元素**：`<div onclick>`/`<span onclick>` warn 每个扣 5（封顶 15）——agent 不识别为可点。

**计分**：`max(0, 100 - 累计扣分)`。

**怎么读**：规则分高≠真可操作。`<button>` 都有 aria-label 但点击后走 JS 路由、没真实 href，规则分可能不错，但 agent 实证时可能点不动。这就是为什么本 skill 还要跑 Step 3 实证——规则分和实证分要分开看。

---

## 规则分 vs 实证分

- **规则分**（5 维度加权）：回答"页面长得像不像对 agent 友好"。便宜、确定性、可 CI 化。
- **实证分**（Step 3，本 skill 独有）：回答"agent 真能不能完成这个任务"。贵、要 agent 在场、样本量 = 1。

两者会打架：规则分 80 的站，agent 实证可能失败（JS 路由、shadow DOM、动态加载）。这**不是 bug**，是两种不同的答案。报告里永远分开呈现，不要试图合并成一个"真实分数"。