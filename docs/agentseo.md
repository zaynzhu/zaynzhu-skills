# agentseo

网站智能体可读性审计——从 AI Agent 视角评估一个网页对智能体是否友好，并可由 agent 真正上手完成一个任务来实证可操作性。

## 功能

- 5 维度规则审计：语义化 HTML / 结构化数据 / 可访问性 / Agent 文件（robots.txt · llms.txt · sitemap.xml）/ 可操作性，加权出总分与等级
- 浏览器渲染抓取：agent 用浏览器 MCP 取渲染后 HTML，覆盖 SPA 站点（无浏览器时降级静态抓取）
- 实证可操作性：agent 真正在浏览器里完成用户给的任务，记录步骤与成败，回答"agent 到底能不能完成"
- 报告输出：默认保存 markdown 报告（含规则分 + 实证结果），可选只终端输出

## 依赖

- **Node.js ≥ 22**（`npx agentseo` 硬依赖 `node:sqlite`）
- **任一浏览器 MCP**：chrome-devtools / playwright / superpowers-chrome（缺失时降级静态抓取，实证任务跳过）

## 快速开始

在支持 Skills 的 AI 工具中触发即可，无需手动跑脚本：

```
# 只跑规则审计
agentseo https://example.com

# 规则审计 + 实证任务
审计 https://example.com 的智能体可读性，任务：找到产品价格

# 不落盘，只终端输出
agentseo https://example.com，不要保存文件
```

skill 内部会执行：

```bash
# 1. agent 用浏览器 MCP 渲染抓取页面，存临时 HTML
# 2. 调规则审计引擎
npx -y agentseo --html <临时HTML> --url <url> --json
# 3.（可选）agent 在浏览器里实证完成用户任务
# 4. 合成报告
```

## 审计维度

| 维度 | 中文名 | 权重 | 检查对象 |
|------|--------|------|----------|
| semanticHtml | 语义化 HTML | 0.25 | h1/标题层级/语义地标/div 汤比例 |
| structuredData | 结构化数据 | 0.25 | JSON-LD / Microdata / schema.org 类型 |
| a11y | 可访问性 | 0.20 | img alt / 按钮可访问名 / 表单 label / lang |
| agentFiles | Agent 文件 | 0.15 | robots.txt AI 爬虫可达 / llms.txt / sitemap.xml |
| actionability | 可操作性 | 0.15 | 表单 action / 按钮稳定定位 / 伪链接 |

各维度详细检查项与计分逻辑见 `skills/agentseo/references/dimensions.md`。

总分 ≥90 A，≥75 B，≥60 C，≥40 D，余 F。

## 规则分 vs 实证分

- **规则分**：5 维度加权，回答"页面长得像不像对 agent 友好"。便宜、确定性。
- **实证分**：agent 真去试一个任务，回答"agent 真能不能完成"。贵、样本量 1。

两者会打架（规则 80 分的站 agent 实证可能失败），报告里分开呈现，不合并成单一分数。

## 报告

默认保存到当前工作区根目录：

```
agentseo-report-{域名}-{YYYY-MM-DD}.md
```

含审计时间、抓取方式、总分等级、5 维度明细（findings 带证据与建议）、实证结果（若有）。

## 文件结构

```
agentseo/
├── SKILL.md                 ← 主指令（执行流程 Step 0..4）
└── references/
    └── dimensions.md        ← 5 维度释义与计分
```

## 规则审计引擎

本 skill 不含审计引擎源码，通过 `npx agentseo` 调用已发布到 npm 的 [agentseo-core](https://github.com/zaynzhu/AgentSEO)。引擎源码与 CLI 在 AgentSEO 仓库维护。