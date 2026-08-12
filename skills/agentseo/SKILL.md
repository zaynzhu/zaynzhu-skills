---
name: agentseo
description: 网站智能体可读性审计。从 AI Agent 视角评估一个网页对智能体是否友好：先由 agent 用浏览器渲染抓取页面，再调 `npx agentseo` 跑规则审计（语义化 HTML / 结构化数据 / 可访问性 / Agent 文件 / 可操作性 5 维度打分），并可由 agent 真正上手完成一个任务来实证"可操作性"。触发词：「agentseo」「审计这个网站对 AI 友不友好」「智能体可读性审计」「AI 可读性」「这个站对 agent 友好吗」「llms.txt 检查」「评估网站的 agent 可读性」。即使用户只是贴了一个 URL 并问"这个站 AI 能不能读懂"或"AI agent 能不能用这个站"，也应该触发本技能。
compatibility:
  tools: [bash]
  requires:
    - Node.js ≥ 22（用于 `npx agentseo`；node:sqlite 硬性依赖，缺失直接报错不降级）
  optional:
    - 任一浏览器 MCP（chrome-devtools / playwright / superpowers-chrome；用于渲染抓取与实证任务，全都没有时降级静态抓取并跳过实证）
---

# AgentSEO Skill

从 AI Agent 视角审计一个网页：**agent 渲染抓取页面 → 调 `npx agentseo` 跑规则审计 →（可选）agent 真正上手完成一个任务来实证可操作性 → 出报告**。

规则审计回答"页面长得像不像对 Agent 友好"，实证任务回答"Agent 到底能不能完成这件事"。

---

## 运行要求

- **Node.js ≥ 22**：用于 `npx -y agentseo`（核心库硬依赖 `node:sqlite`）。缺失时直接报错，不静默降级。
- **浏览器 MCP（任一）**：chrome-devtools-mcp / playwright / superpowers-chrome。用于 Step 1 渲染抓取与 Step 3 实证任务。全都没有时降级为静态抓取（见 Step 1 降级说明）。
- **网络可达目标 URL**：agentFiles 维度会去抓目标站的 `/robots.txt`、`/llms.txt`、`/sitemap.xml`。

---

## 执行流程

### Step 0：确认参数

向用户确认（未指定时按默认）：

| 参数 | 说明 | 默认 |
|------|------|------|
| `url` | 要审计的页面 URL（**必须**） | — |
| `task` | 实证任务描述，自然语言，如「找到产品价格」「注册一个账号」 | 不给 → 只跑规则审计，跳过 Step 3 |
| `save` | 是否保存报告为 markdown 文件 | 保存 |

如果用户只给了 URL 没给 task，**明确告知**"将只跑规则审计，不实证任务"，并问一句要不要补一个任务。不要自作主张编造任务。

---

### Step 1：渲染抓取页面

这一步替代了原 AgentSEO 项目里 server 端的 Playwright 渲染，改由 agent 用自己的浏览器 MCP 完成。

**主路径（推荐）：用浏览器 MCP 渲染**

1. 用任一可用的浏览器 MCP `navigate` 到 `url`，等待页面加载完成（`networkidle` 或等价状态）。
2. 取渲染后的完整 HTML：执行 `document.documentElement.outerHTML`（chrome-devtools 的 `evaluate_script` / playwright 的 `browser_evaluate` / superpowers-chrome 的 `eval` 均可），拿到渲染后 DOM 字符串。
   - ⚠️ **JSON 编码坑**：浏览器 MCP 的 eval 返回值通常被 JSON 序列化（字符串被加引号转义）。若直接把返回内容存成文件喂给 `--html`，agentseo 会拿到带引号的非法 HTML。务必先 `JSON.parse` 转回原始字符串再写 `.html` 文件，例：`node -e "const fs=require('fs');fs.writeFileSync('page.html',JSON.parse(fs.readFileSync('page.json','utf8')))"`。
3. 存到临时文件，例如 `agentseo-page.html`（放当前工作区临时目录）。

> 为什么要渲染后 HTML 而不是原始源码：SPA 站点的原始 HTML 常是空壳，规则审计会冤枉打低分。渲染后的 DOM 才是 agent 真正面对的东西。

**降级路径：浏览器 MCP 全部不可用时**

用 WebFetch 取静态 HTML，存临时文件，并在报告里**明确标注**：

> ⚠️ 本次为静态抓取（无浏览器 MCP 渲染）。SPA 站点内容可能缺失，`semanticHtml` / `structuredData` / `a11y` / `actionability` 四个维度的分数可能偏低，`actionability` 实证任务（Step 3）将不可信。

降级时若用户给了 task，**跳过 Step 3** 并告知原因。

---

### Step 2：跑规则审计

```bash
npx -y agentseo --html <临时HTML文件> --url <url> --json
```

- `--html` 用 Step 1 存的渲染后 HTML；`--url` 传原始 URL（`agentFiles` 维度去查 `--url` 的 origin 下的 `/robots.txt`、`/llms.txt`、`/sitemap.xml`——注意 origin 语义陷阱，见 `references/dimensions.md`）。
- `--json` 输出结构化报告，便于 agent 解析。
- ⚠️ **registry 失败降级**：若 `npx -y agentseo` 报网络错（如默认 npm 镜像不可达、ECONNRESET），加官方源重试：`npx -y --registry=https://registry.npmjs.org agentseo --html <文件> --url <url> --json`。

**输出形状**：

```json
{
  "url": "https://example.com",
  "totalScore": 72,
  "grade": "C",
  "dimensions": [
    {
      "dimension": "semanticHtml",
      "score": 80,
      "findings": [
        { "level": "error", "message": "...", "evidence": "...", "suggestion": "..." }
      ]
    }
  ]
}
```

- `totalScore` 加权总分（0-100，缺维度的维度剔除后重新归一化），`grade` 分档 A/B/C/D/F（≥90 A，≥75 B，≥60 C，≥40 D，余 F）。
- 每个 `dimensions[]` 含 `dimension`（5 个之一）、`score`（0-100 或 `null` 表跳过）、`findings[]`（`level` ∈ `error`/`warn`/`ok`）。
- 5 个维度各检查什么、finding 怎么读 → 见 `references/dimensions.md`。

**解析后，先向用户给一句话结论**：总分、等级、最差的 1-2 个维度。细节留到 Step 4 报告里。

---

### Step 3：实证可操作性（仅当 Step 0 给了 task）

这是本 skill 区别于纯 CLI 的核心价值：**让真 agent 真去试一个任务**，而不是用规则猜"能不能操作"。

前置：Step 1 必须用的是浏览器 MCP 主路径（降级路径下跳过本步）。

> 🎯 **任务选择原则**：Step 3 的价值在于验证**交互**可操作性，优先选需要点击/填写/导航的任务（如「打开 package.json 读 engines.node」「把某商品加入购物车」「点到定价页」），而不是纯读取任务（如「找到 README 里的版本号」）。纯读取只能验证"信息能不能被提取"，验证不了"按钮能不能被触发"——而后者才是 actionability 维度真正想回答的。若用户给的 task 是纯读取型，建议主动提议升级为同主题的交互型任务，让用户决定。

**操作步骤**：

1. 页面已在浏览器 MCP 中打开（Step 1 复用，别重新开）。
2. 取页面快照（可交互元素列表）——chrome-devtools 的 `take_snapshot` / playwright 的 `browser_snapshot` / superpowers-chrome 的 `extract` 均可。
3. 根据 `task` 判断需要操作哪些元素，逐步执行：
   - 点击：`click` 对应元素
   - 填写：`fill` / `type` 输入框
   - 每步动作后重新取快照，观察页面变化
4. 判断任务是否完成：
   - **成功**：拿到了 task 要的信息 / 达成了 task 要的目标状态
   - **失败**：超过 8 步仍未完成，或确认页面无法支持该任务
5. 记录 trace，每步一行：`第 N 步：<动作> [目标元素] —— <原因/结果>`

**输出实证结论**：

```json
{
  "task": "找到产品价格",
  "success": true,
  "summary": "首页点 Products → 列表点第一个商品 → 详情页右侧找到价格 ¥299",
  "steps": 3,
  "trace": [
    "第 1 步：click 导航 Products —— 进入产品列表",
    "第 2 步：click 第一个商品卡片 —— 进入详情页",
    "第 3 步：读取价格 —— ¥299，任务完成"
  ]
}
```

> 实证结果**不计入规则总分**，作为独立一节附在报告里。规则分说"页面长得对 agent 友好"，实证说"agent 真能不能完成"，两个答案分开看。

---

### Step 4：综合输出

**报告结构**（markdown）：

```markdown
# AgentSEO 智能体可读性审计报告

**审计时间**：{YYYY-MM-DD HH:MM:SS}
**目标 URL**：{url}
**抓取方式**：浏览器 MCP 渲染 / 静态抓取（降级）
**规则审计引擎**：npx agentseo（agentseo-core）

## 总评

- 总分：{totalScore}/100，等级 {grade}
- 最弱维度：{维度名}（{score}）

## 规则审计明细

### {维度中文名}（{dimension}）  {score}/100
- ✗/⚠/✓ {finding.message}
  - 证据：{finding.evidence}
  - 建议：{finding.suggestion}

（5 个维度依次列出；score 为 null 的标注"该维度未参与计分"）

## 实证可操作性（若有）

- 任务：{task}
- 结果：成功 / 失败
- 步数：{steps}
- 摘要：{summary}
- 执行轨迹：
  1. {trace 第 1 步}
  2. ...

---

**报告生成时间**：{YYYY-MM-DD HH:MM:SS}
**数据来源**：agentseo-core 规则审计 + agent 浏览器实证
```

**保存要求**（默认 `save=true`）：

1. 文件名：`agentseo-report-{域名}-{YYYY-MM-DD}.md`（域名取 URL 的 host，`:` `/` 等替换为 `-`）
2. 保存位置：当前工作区根目录
3. 文件头尾标注按上面模板的"审计时间"与"报告生成时间"块

`save=false`（用户明确说不要文件）时，只在终端输出完整报告，不落盘。

---

## 输出规范

1. 终端先给一句话结论（总分 + 等级 + 最弱维度），再给报告文件路径（若保存）。
2. 报告里 finding 的 `evidence` / `suggestion` 有就列，没有就省，不要编造。
3. 实证任务失败不是"错误"，如实写失败原因和卡在哪一步。
4. 降级抓取时，必须在报告顶部和终端结论里都标注"静态抓取"警告。
5. 若被审 URL 的 origin 属于不归用户所有的大平台（github.com / gitlab.io / notion.site 等），`agentFiles` 维度反映的是平台整站策略而非被审页面可控——报告里必须点明这一项，避免误导用户去改自己改不了的 robots/llms.txt（详见 `references/dimensions.md` 的 origin 语义陷阱）。
6. 语言中文，命令/代码/HTML 片段保持英文原样。

---

## 执行中可能遇到的问题

### 问题 1：`npx agentseo` 报错或找不到

**现象**：`npx -y agentseo` 失败、报 `node:sqlite` 找不到、命令不存在、或网络错（ECONNRESET 等）。

**原因**：Node 版本 < 22；未装 Node；或默认 npm 镜像不可达。

**解决**：
1. `node --version` 确认 ≥ 22.13（`node:sqlite` 在 22.13 起稳定）。
2. 网络错（ECONNRESET / socket disconnected / 镜像超时）→ 加官方源重试：`npx -y --registry=https://registry.npmjs.org agentseo ...`。
3. 若环境确实没 Node，明确告知用户"规则审计需要 Node ≥ 22，实证任务可独立进行但无规则分"，让用户决定是否继续只跑实证。

### 问题 2：浏览器 MCP 渲染超时或页面打不开

**现象**：navigate 超时、页面白屏、或 `outerHTML` 取到空壳。

**解决**：
1. 重试一次，延长等待。
2. 仍失败 → 走降级路径（WebFetch 静态抓取），并在报告标注。
3. 若是目标站本身不可达（DNS/超时），直接报错，不要降级到空 HTML 跑审计（空 HTML 会让所有维度报错，结果无意义）。

### 问题 3：实证任务里元素找不到或点不动

**现象**：快照里没有 task 相关的可交互元素，或点击后页面没反应。

**解决**：
1. 先尝试滚动页面再取快照（元素可能在视口外）。
2. 检查是否需要先打开某个菜单/折叠面板。
3. 确认页面是否用 shadow DOM / iframe（快照可能取不到内部元素），如实记录"无法定位，疑似 shadow DOM"。
4. 如实记为失败，写明卡在哪步，不要硬凑成功。

### 问题 4：Windows 下临时文件路径或编码问题

**解决**：临时 HTML 文件路径用绝对路径喂给 `npx`，避免空格路径；报告文件写入用 UTF-8。

---

## 参考文件

- 5 个审计维度的定义与 finding 解读：`references/dimensions.md`
- 规则审计引擎源码（不在本 skill 内）：https://github.com/zaynzhu/AgentSEO

---

## 快速触发示例

用户说这些时触发本 skill：

- "agentseo https://example.com"
- "审计一下 https://example.com 对 AI 友不友好"
- "这个站 https://example.com agent 能不能读懂"
- "帮我看看 https://example.com 的 llms.txt 和 agent 可读性"
- "评估 https://example.com 的智能体可读性，任务：找到产品价格"（带实证任务）
- "这个网页 AI agent 能不能用" + 一个 URL

收到后按 Step 0 → 4 执行，先确认 task 是否需要实证，再渲染抓取 → 跑审计 →（可选）实证 → 出报告。