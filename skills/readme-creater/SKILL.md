---
name: readme-creator
description: |
  通用 README 创建器 + 改进器。从零为项目生成炫酷、专业的 README（含徽章、Star History、贡献者网格、中英双语），也能分析并改进现有 README。
  触发词：创建 readme、改进 readme、生成 readme、写 readme、优化 readme、write readme、improve readme、generate readme、/readme。
  即使用户只是说"帮我写个 readme"、"这个项目的文档太丑了"、"给项目加个专业的 readme"，只要上下文涉及项目文档生成或改进，就应该触发。
---

# README Creator

通用 README 创建器 + 改进器。从零为任何项目生成专业、炫酷的 README，也能分析并改进现有 README。

设计灵感来自 [QwenPaw](https://github.com/QwenLM/QwenPaw)、[OpenClaw](https://github.com/openclaw)、[CrewAI](https://github.com/crewAIInc/crewAI) 等项目的文档风格——它们的 README 都具备：清晰的视觉层级、完整的徽章组合、渐进式信息披露、以及中英双语支持。

---

## 进度追踪

每条回复的开头都要展示当前进度：

```
⬜ Phase 1: 项目检测  ⬜ Phase 2: 现有 README 分析  ⬜ Phase 3: 交互确认  ⬜ Phase 4: README 生成  ⬜ Phase 5: 审查与迭代
```

当某个 phase 进行中时标记为 `🔄`，完成后标记为 `✅`。

---

## Phase 1: 项目检测

**目标**: 自动收集项目的元数据，为后续生成提供素材。

### Step 1: 运行检测脚本

```bash
python <skill-dir>/scripts/detect_project.py <project-dir>
```

脚本输出 JSON，包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 项目名称 |
| `description` | string | 项目描述 |
| `language` | string | 主编程语言 |
| `license` | string | 许可证类型 |
| `repo_url` | string | 仓库 URL |
| `dependencies` | string[] | 依赖列表 |
| `has_readme` | boolean | 是否存在 README |
| `readme_summary` | object | README 的 section 列表和行数 |
| `logo_path` | string | Logo 文件路径（可能为 null） |
| `ci_type` | string | CI 系统类型（可能为 null） |
| `python_version` | string | Python 版本要求 |
| `package_manager` | string | 包管理器类型 |

如果脚本执行成功，直接跳到 Step 3 展示结果。脚本会自动处理：
- SSH 到 HTTPS 的 URL 转换
- 多种配置文件格式的解析（package.json、setup.py、pyproject.toml、Cargo.toml、go.mod）
- 许可证关键词识别（从 LICENSE 文件内容中提取）
- Logo 文件扫描（在 assets/、docs/、images/ 等常见目录中查找）

### Step 2: 手动检测回退

如果脚本执行失败（缺少 Python、权限问题等），用以下工具逐项手动检测。检测顺序很重要——后面的字段可能依赖前面的结果（比如 repo_url 用于构造徽章 URL）。

**项目名 (name)**
- 用 Glob 查找 `package.json`、`setup.py`、`pyproject.toml`、`Cargo.toml`、`go.mod`
- 用 Read 读取找到的配置文件，提取 `name` 字段
- 回退：使用项目根目录的文件夹名
- 为什么重要：项目名出现在 README 标题、徽章占位符、Star History URL 中

**描述 (description)**
- 读取上述配置文件的 `description` 字段
- 回退：读取现有 README 的第一段非标题文本
- 为什么重要：描述用于生成 tagline 和 introduction blockquote

**主语言 (language)**
- 用 Glob 扫描项目文件，统计各扩展名数量
- 映射规则：`.py` → Python、`.ts` / `.tsx` → TypeScript、`.js` / `.jsx` → JavaScript、`.rs` → Rust、`.go` → Go、`.java` → Java、`.rb` → Ruby、`.c` / `.h` → C、`.cpp` / `.hpp` → C++
- 数量最多的语言为主语言
- 排除目录：`node_modules`、`.git`、`__pycache__`、`venv`、`dist`、`build`、`target`
- 为什么重要：语言决定 Logo Emoji 回退、Quick Start 安装命令、代码块语言标注

**许可证 (license)**
- 用 Glob 查找 `LICENSE`、`LICENSE.md`、`LICENSE.txt`、`LICENCE`、`LICENCE.md`
- 用 Read 读取文件前 2000 字符，识别关键词：MIT、Apache、GPL、BSD、ISC、MPL、LGPL、AGPL、Unlicense
- 为什么重要：许可证决定 License 徽章和 License section 的内容

**仓库 URL (repo_url)**
- 用 Bash 执行 `git remote get-url origin`
- 将 SSH URL（`git@github.com:user/repo.git`）转换为 HTTPS 格式
- 回退：读取 `package.json` 的 `repository` 字段
- 为什么重要：从 URL 中提取 `{{OWNER}}` 和 `{{REPO}}`，用于所有徽章、Star History、Contributors 的占位符替换

**依赖 (dependencies)**
- Python：读取 `requirements.txt`，解析包名（去掉版本号和注释）
- Node.js：读取 `package.json` 的 `dependencies` + `devDependencies`
- Rust：读取 `Cargo.toml` 的 `[dependencies]` 段
- Go：读取 `go.mod` 的 `require` 段
- 为什么重要：依赖列表帮助判断项目复杂度，决定推荐徽章组合和 Installation section 的详略

**现有 README**
- 用 Glob 匹配 `README.md`、`README.rst`、`README.txt`、`README`、`readme.md`
- 如果找到，用 Read 读取全文
- 为什么重要：决定是否进入 Phase 2 分析流程

**Logo**
- 用 Glob 扫描 `assets/`、`docs/`、`images/`、`img/`、`static/`、`public/` 目录
- 匹配文件名包含 `logo` 的 svg/png/jpg/jpeg/webp 文件
- 为什么重要：有 Logo 用真实图片，无 Logo 用 Emoji 回退方案

**CI 系统**
- 用 Glob 检查 `.github/workflows/*.yml`、`.gitlab-ci.yml`、`Jenkinsfile`、`.travis.yml`、`azure-pipelines.yml`、`.circleci/`
- 为什么重要：有 CI 才能添加 Build Status 徽章

### Step 3: 展示结果摘要

以表格形式展示检测结果，等待用户确认或补充：

```
| 字段       | 检测结果           |
|------------|-------------------|
| 项目名     | {{name}}          |
| 描述       | {{description}}   |
| 主语言     | {{language}}      |
| 许可证     | {{license}}       |
| 仓库 URL   | {{repo_url}}      |
| 依赖数量   | {{dep_count}}     |
| 现有 README | {{has_readme}}   |
| Logo       | {{logo_path}}     |
| CI 系统    | {{ci_type}}       |
```

如果某个字段为空或不准确，提示用户补充。特别注意：
- `description` 为空时，要求用户提供一句话描述（用于 tagline 和 introduction）
- `repo_url` 为空时，询问是否为 GitHub 项目（影响 Star History 和 Contributors 的生成）
- `license` 为空时，提示用户建议添加 LICENSE 文件

确认后进入下一 phase。

---

## Phase 2: 现有 README 分析

**仅当 `has_readme = true` 时执行此 phase。** 否则直接跳到 Phase 3。

### 分析步骤

1. 读取现有 README 全文
2. 提取所有 `##` 级标题，列出各 section 的内容摘要（每段 1-2 句话）
3. 统计总行数，对照 `references/style-guide.md` 的长度指南评估是否需要扩展或精简
4. 生成 section 决策表：

```
| Section         | 行数 | 内容摘要             | 建议操作     |
|-----------------|------|---------------------|-------------|
| {{heading_1}}   | N    | {{summary}}         | 保留/重写/删除 |
| {{heading_2}}   | N    | {{summary}}         | 保留/重写/删除 |
```

5. 逐项与用户确认每个 section 的处理方式
6. 记录用户对每个 section 的偏好：保留原文 / 基于原文改进 / 完全重写 / 删除
7. 汇总确认结果，列出将在 Phase 4 中生成的 section 列表（包括保留的和新增的）

### 分析维度

对现有 README 从以下五个维度进行评估，在 Phase 4 生成时针对性改进：

- **完整性**: 是否缺少关键 section（Features、Installation、Usage、License）。对照 section-templates.md 的 15 个标准 section 逐项检查。
- **准确性**: 代码示例是否过时、链接是否有效、API 是否更新。尝试用 Read 检查代码中引用的模块/函数是否在项目中存在。
- **视觉质量**: 是否有徽章、Emoji 前缀、表格、代码块语言标注。对照 style-guide.md 的规范逐项评分。
- **风格一致性**: 标题层级是否统一（`##` vs `###`）、间距是否规范、Emoji 使用是否一致。
- **信息密度**: 是否有冗余段落或过于简略的说明。理想情况：每个 section 有足够的上下文让用户理解，但不重复其他 section 的内容。

---

## Phase 3: 交互确认

使用 AskUserQuestion 工具，依次确认以下选项。每个问题都要展示推荐值和可选值。

### 3.1 徽章组合

根据项目类型推荐徽章方案（参见 `references/badge-templates.md` 的"Recommended Badge Combinations"）：

- **Minimal (4 badges)**: License + Stars + Last Commit + Issues — 适合小型个人项目
- **Standard (6 badges)**: 上述 + Forks + Build Status + Release — 适合活跃开源项目
- **Full (8-10 badges)**: 上述 + Coverage + PRs Welcome + Pull Requests — 适合成熟社区项目

展示推荐方案，让用户选择或自定义。替换 `{{OWNER}}` 和 `{{REPO}}` 占位符。

**自动选择逻辑**：
- 无 Git 仓库 → 跳过 Stars/Forks/Issues 等 GitHub 徽章
- 无 CI 配置 → 跳过 Build Status 徽章
- 无 LICENSE → 跳过 License 徽章，提示用户添加
- 有 PyPI/npm/crates.io 发布 → 自动添加对应的版本和下载徽章

### 3.2 Logo 策略

三种选项，按优先级排列：

1. **检测到 Logo** — 展示路径和预览，确认是否使用，询问宽度（默认 200px）。Logo 文件放在 `<div align="center">` 中居中显示。
2. **用户自定义** — 用户提供图片 URL 或本地路径。询问是否需要调整宽度。
3. **Emoji 回退** — 使用 `references/logo-fallback.md` 的决策流程：
   - 有主语言 → 使用语言对应 Emoji（Python → 🐍、TypeScript → 💎、Rust → 🦀）
   - 有项目类别 → 使用类别对应 Emoji（CLI Tool → 🖥️、AI/ML → 🤖）
   - 默认 → 📦

Emoji 回退模式下，header 格式为：`# {{EMOJI}} {{PROJECT_NAME}}`

### 3.3 语言模式

- **bilingual (推荐)**: 主语言 README.md + 副语言 README_EN.md 或 README_CN.md
- **English-only**: 仅生成英文 README.md
- **Chinese-only**: 仅生成中文 README.md

如果用户未明确指定，根据已有 README 的语言和项目来源推断：
- 已有 README 为中文 → 推荐 bilingual（中文主 + 英文副）
- 已有 README 为英文 → 推荐 bilingual（英文主 + 中文副）或 English-only
- 无现有 README → 推荐 bilingual（英文主 + 中文副），因为英文是开源社区通用语言

### 3.4 风格选择

- **stunning full (推荐)**: 完整版，含所有视觉元素——Emoji 标题、徽章、Star History、贡献者网格、对比表格、FAQ 折叠面板
- **clean professional**: 精简版，侧重内容而非装饰，适合企业/内部项目，省略 Star History 和 Contributors

### 3.5 可选额外 section

| Section | 何时推荐 | 说明 |
|---------|---------|------|
| Star History | GitHub 项目有 100+ Stars | 展示 Star 增长曲线，使用 `<picture>` 标签支持暗色/亮色主题 |
| Contributors | 有 3+ 贡献者 | contrib.rocks 头像网格，链接到 GitHub Contributors 页面 |
| Comparison | 有同类竞品 | 功能对比表格，用 ✅/❌/⚠️ 标记各竞品的功能支持情况 |
| Roadmap | 有明确开发计划 | 区域/功能/状态表格，用 ✅ Done / 🔄 In Progress / 📋 Planned 标记 |
| FAQ | API 或 CLI 工具 | `<details>` 可折叠问答，建议 3-5 个常见问题 |

如果用户选择"快速生成"模式，根据以下规则自动决定：
- Star History：repo_url 包含 `github.com` 时默认启用
- Contributors：读取 git log 统计贡献者数量，>= 3 时默认启用
- Comparison / Roadmap / FAQ：默认不启用，除非用户明确要求

---

## Phase 4: README 生成

按以下顺序逐段生成。每段都使用 `references/section-templates.md` 中对应的模板，用实际值替换 `{{PLACEHOLDER}}`。

### 生成顺序

每个 section 都使用 `references/section-templates.md` 中的对应模板。生成时用实际项目数据替换 `{{PLACEHOLDER}}` 占位符。

1. **Logo/Header** — 有 Logo 用 Variant A（`<img>` 标签），无 Logo 用 Variant B（Emoji 回退）。居中对齐，包含项目名和导航链接行。
2. **Language Switcher** — 仅 bilingual 模式，格式：`[中文](README.md) | [English](README_EN.md)`。放在 header 之后、badges 之前。
3. **Badges Row** — 从 `references/badge-templates.md` 选取徽章，居中排列。替换 `{{OWNER}}`/`{{REPO}}`/`{{PACKAGE_NAME}}`。
4. **Tagline** — 一句话，120 字符以内。从三种 pattern 中选择最合适的一种：Pattern A（"What it is"）、Pattern B（"Action-oriented"）、Pattern C（"Problem-first"）。
5. **Introduction** — `> [!TIP]` 块引用，2-3 句话描述核心能力和适用场景。不要重复 tagline 的内容。
6. **✨ Features** — 5-8 个加粗功能名 + 简短描述，每个一行。格式：`**Feature Name** -- Description`。
7. **🚀 Quick Start** — 安装命令 + 最小可运行代码示例。代码示例必须是可以直接复制粘贴运行的。
8. **📦 Installation** — 详细安装方式（pip/npm/cargo/go get/源码编译等）+ 依赖列表。提供至少 2 种安装方式。
9. **💡 Usage** — 2-3 个使用场景，每个包含标题和代码块。展示最常见的用例。
10. **📚 Documentation** — 表格形式，列出文档主题和描述。链接到实际存在的文档文件。
11. **🤝 Contributing** — Fork/Branch/Commit/PR 工作流 + 开发环境搭建命令。链接到 CONTRIBUTING.md（如果存在）。
12. **💬 Community** — 社区链接列表。只包含项目实际有的社区渠道。
13. **⭐ Star History** — 仅 GitHub 项目。使用 `<picture>` 标签支持暗色/亮色主题。
14. **🙏 Contributors** — 仅 GitHub 项目。使用 contrib.rocks 头像网格，链接到 GitHub Contributors 页面。
15. **📄 License** — 许可证名称 + 链接到 LICENSE 文件。格式参考 section-templates.md。

### 风格规范

所有视觉规则严格遵循 `references/style-guide.md`：

- **Emoji**: 每个 `##` 标题最多 1 个前缀 Emoji，正文和代码块内禁止使用
- **居中**: Logo、徽章行、语言切换器使用 `<div align="center">`，不嵌套
- **分隔**: 主要 section 之间用 `---` 分隔，前后各留空行
- **代码块**: 必须标注语言标识符（`bash`、`python`、`json` 等）
- **表格**: 文本左对齐，状态指示符居中，数字右对齐
- **链接**: 使用描述性链接文本，禁止 "click here"、"this link" 等模糊措辞
- **Admonitions**: 每个 README 最多 2-3 个 `> [!TIP]` / `> [!NOTE]` 块

### 双语处理

- bilingual 模式：主语言写 `README.md`，副语言写 `README_EN.md` 或 `README_CN.md`
- 两个版本的 section 结构必须完全一致（相同的 section 数量和顺序）
- 代码示例在两个版本中保持不变
- 技术术语（API 名称、库名、CLI 命令）在中文版中保留英文
- 语言切换器放在 header 之后、badges 之前

### 边界情况处理

| 场景 | 处理方式 |
|------|---------|
| 空项目（无代码） | 生成最简 README：Header + 描述 + License，跳过 Features/Usage |
| 单文件脚本 | 简化结构：Header + Quick Start（含用法）+ License，目标 50-100 行 |
| 无 Git 仓库 | 跳过 Stars/Forks/Issues 徽章、Star History、Contributors section |
| 无 LICENSE 文件 | 跳过 License 徽章和 section，在末尾提示用户添加许可证 |
| 私有仓库 | 跳过 Stars/Forks/Issues 徽章，保留 Build/Release 徽章 |
| Monorepo | 使用根目录名称，Dependencies 列出主要子包 |
| 纯文档项目（无代码） | 省略 Quick Start/Usage，强调 Documentation 和 Community |
| 多语言混合项目 | 主语言取文件数最多的，Features 中提及多语言支持 |

---

## Phase 5: 审查与迭代

### 自动审查清单

生成完成后，逐项检查以下内容。每项标注 ✅ 通过或 ❌ 失败：

1. **链接有效性** — 所有 URL 格式正确（`https://` 开头），相对路径指向存在的文件（用 Glob 验证）
2. **代码块语言标注** — 每个 ``` 后面都有语言标识符，无遗漏。用 Grep 扫描裸 ``` 块
3. **Emoji 一致性** — section 标题 Emoji 与 `references/style-guide.md` 映射表一致（Features → ✨、Quick Start → 🚀 等）
4. **Section 完整性** — 用户在 Phase 3 确认的所有 section 都已生成，无遗漏
5. **双语一致性** — bilingual 模式下两个文件的 section 数量和顺序一致，代码示例相同
6. **占位符扫描** — 用 Grep 搜索 `{{`、`TODO`、`FIXME`、`TBD`，确保无遗漏的占位符
7. **长度合理性** — 对照 style-guide.md 的长度指南（单文件脚本 50-100 行，中型项目 200-400 行，大型框架 400-600 行）
8. **格式规范** — `---` 前后有空行、`<div>` 标签正确闭合、无尾部空格、文件末尾有且仅有一个换行

### 预览与确认

1. 展示自审结果表格，标注每项检查的 ✅/❌ 状态
2. 展示 README 预览（直接输出 Markdown 内容），让用户在终端中查看最终效果
3. 等待用户反馈，进行迭代修改。常见修改请求：
   - 调整措辞（更正式/更轻松的语气）
   - 增删某个 section
   - 修改徽章样式或数量
   - 调整代码示例
   - 修改 tagline 或 introduction
4. 每次修改后重新运行审查清单中的相关检查项
5. 用户确认后写入文件

### 写入文件

- 确保目标目录存在（如不存在则创建）
- 写入 `README.md`（始终）
- 写入 `README_EN.md` 或 `README_CN.md`（bilingual 模式时）
- 写入完成后提示用户检查文件

---

## References

| 文件 | 用途 |
|------|------|
| `references/badge-templates.md` | Shields.io 徽章模板，含风格配置和推荐组合 |
| `references/section-templates.md` | 每个 section 的 Markdown 模板和代码示例 |
| `references/style-guide.md` | 视觉风格规范（Emoji、排版、表格、双语格式） |
| `references/logo-fallback.md` | Logo 缺失时的 Emoji 回退规则和决策流程 |
| `scripts/detect_project.py` | 项目元数据自动检测脚本（Python） |

---

## 使用示例

### 场景 1: 为新项目从零创建 README

```
用户: 帮我给这个项目写个 README
助手: [Phase 1] 运行 detect_project.py，展示检测结果表格
      [Phase 3] 确认徽章组合 → Logo 策略 → 语言模式 → 风格 → 额外 section
      [Phase 4] 按顺序生成 15 个 section
      [Phase 5] 自动审查 → 预览 → 用户确认 → 写入文件
```

### 场景 2: 改进现有 README

```
用户: 这个项目的 README 太简陋了，帮我优化一下
助手: [Phase 1] 检测项目元数据
      [Phase 2] 分析现有 README：提取 section 列表，评估完整性
      [Phase 3] 确认每个 section 的处理方式（保留/重写/删除）
      [Phase 4] 生成改进版
      [Phase 5] 对比原版和改进版 → 审查 → 写入
```

### 场景 3: 双语 README

```
用户: 给项目写个中英双语的 readme
助手: [Phase 1] 检测项目
      [Phase 3] 确认 bilingual 模式，主语言中文
      [Phase 4] 生成 README.md（中文）+ README_EN.md（英文）
      [Phase 5] 检查双语一致性 → 审查 → 写入两个文件
```

### 场景 4: 快速生成（跳过交互）

如果用户明确说"直接生成"或"不需要确认"，可以跳过 Phase 3 的交互确认，使用默认推荐值：
- 徽章：Standard (6 badges)
- Logo：自动检测 + Emoji 回退
- 语言：根据检测结果推断
- 风格：stunning full
- 额外 section：根据项目规模自动决定

---

## 设计原则

1. **渐进式披露**: SKILL.md 控制主流程和决策点，详细模板放在 `references/` 中。这样主文件保持精简，引用文件按需加载。SKILL.md 本身控制在 500 行以内。
2. **WHY 不只是 WHAT**: 每个推荐都要解释为什么选这个方案。例如："Standard 徽章组合适合活跃开源项目，因为它展示了社区活跃度和构建状态，同时不会因为徽章过多而显得杂乱。"
3. **Emoji 一致性**: 严格遵循 style-guide.md 的 Emoji 映射表，不在正文或代码块中使用 Emoji。每个 `##` 标题最多 1 个 Emoji 前缀。
4. **边到边覆盖**: 从空项目到成熟项目，从单文件脚本到大型框架，每个阶段都有对应的处理策略。不遗漏任何边界情况。
5. **用户控制**: 所有决策最终由用户确认，推荐值只是起点。提供"快速生成"模式跳过交互，但默认走完整确认流程。
