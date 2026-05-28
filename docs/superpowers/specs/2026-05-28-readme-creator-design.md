# readme-creator Skill 设计文档

**日期**: 2026-05-28
**状态**: 已批准
**方案**: 混合方案 A+C（单 SKILL.md + references + 关键脚本）

---

## 1. 概述

**Skill 名称**: `readme-creator`
**定位**: 通用 README 创建器 + 改进器
**触发词**: "创建 readme"、"改进 readme"、"生成 readme"、"write readme"、"improve readme"、"/readme"

能从零为新项目生成完整、炫酷、专业的 README，也能分析并改进现有 README。
参考 QwenPaw、OpenClaw、CrewAI 等热门开源项目的 README 设计模式。

### 核心特性
- 自动检测项目元数据（名称、语言、许可证、依赖等）
- 现有 README 智能分析，逐段询问保留/重写/删除
- 炫酷全面型视觉风格：shields.io 徽章、Star History 图表、contrib.rocks 贡献者网格
- 中英双语支持，头部语言切换链接
- Logo 智能检测 + emoji 降级
- 跨平台兼容（Claude Code / Claude.ai / 其他 AI 工具）

---

## 2. 目录结构

```
skills/readme-creater/
├── SKILL.md                      # 主指令文件（~450 行）
├── scripts/
│   └── detect_project.py         # 项目元数据自动检测脚本
└── references/
    ├── badge-templates.md        # shields.io 徽章模板库（30+ 种徽章）
    ├── section-templates.md      # README 各段落的写作模板
    ├── style-guide.md            # 视觉风格指南（emoji、排版、结构规范）
    └── logo-fallback.md          # emoji 降级 logo 的生成规则
```

---

## 3. 核心流程（5 阶段）

### Phase 1: 项目检测

1. 运行 `scripts/detect_project.py` 获取项目元数据 JSON
2. 如果脚本失败，降级为手动检测：用 Glob 扫描 `package.json`/`setup.py`/`Cargo.toml`/`go.mod`，用 `git remote -v` 获取仓库 URL
3. 展示检测结果摘要，让用户确认

### Phase 2: 现有 README 分析

1. 如果 `has_readme == true`：
   - 读取现有 README 全文
   - 提取结构（段落标题列表）和内容摘要
   - 展示给用户，逐段询问：**保留** / **重写** / **删除**
   - 记录用户的保留偏好
2. 如果没有 README：跳过此阶段

### Phase 3: 交互确认

1. 确认/补充项目信息（名称、描述、标签、目标受众）
2. 选择徽章（展示 badge-templates.md 中的可用徽章，让用户勾选）
3. 确认 logo 策略（已有 logo 路径 / emoji 降级 / 用户提供 URL）
4. 确认语言（中英双语 / 纯英文 / 纯中文）
5. 确认风格（炫酷全面型已默认，可降级为简洁型）
6. 确认额外段落（Star History / Contributors / Comparison / Roadmap / FAQ）

### Phase 4: README 生成

按以下顺序生成 README：

```
1.  Logo/Header（emoji 降级或真实 logo + 标题 + 标签行 + 导航链接）
2.  Language Switcher（中/英 切换链接）
3.  Badges Row（用户选择的徽章，for-the-badge 风格）
4.  Tagline（一句话描述）
5.  > [!TIP] 简介 blockquote
6.  ✨ Features（特性列表，bullet 格式）
7.  🚀 Quick Start（安装 + 最小代码示例）
8.  📦 Installation（详细安装步骤）
9.  💡 Usage（使用示例和代码块）
10. 📚 Documentation（文档链接表格）
11. 🤝 Contributing（贡献指南）
12. 💬 Community（Discord/Issues 链接）
13. ⭐ Star History（star-history.com 图表）
14. 🙏 Contributors（contrib.rocks 网格）
15. 📄 License（许可证声明）
```

中英双语策略：中文版存为 `README.md`，英文版存为 `README_EN.md`（主语言由用户决定）。

### Phase 5: 审查与迭代

1. 读取生成的 README，进行自审：
   - 检查所有链接是否正确（徽章 URL、仓库 URL）
   - 检查代码块是否有语言标注
   - 检查 emoji 是否一致
   - 检查中英文版本结构是否一致
2. 展示自审结果
3. 等待用户反馈，支持迭代修改
4. 如果用户满意，写入文件

---

## 4. `detect_project.py` 脚本设计

### 检测项

| 检测目标 | 检测方式 | 输出字段 |
|---------|---------|---------|
| 项目名称 | `package.json` name / `setup.py` name / `Cargo.toml` name / 目录名 | `name` |
| 描述 | `package.json` description / `setup.py` description / `README.md` 首段 | `description` |
| 主语言 | 文件扩展名统计（`.py`→Python, `.ts`→TypeScript 等） | `language` |
| 许可证 | `LICENSE` 文件 / `package.json` license / `Cargo.toml` license | `license` |
| 仓库 URL | `git remote -v` / `package.json` repository | `repo_url` |
| 依赖 | `requirements.txt` / `package.json` dependencies / `Cargo.toml` deps | `dependencies` |
| 已有 README | 文件存在性 + 内容摘要（前 20 行 + 结构提取） | `has_readme`, `readme_summary` |
| Logo/Banner | 扫描 `assets/`, `docs/`, `images/` 中的图片文件 | `logo_path` |
| CI/CD | `.github/workflows/` / `.gitlab-ci.yml` / `Jenkinsfile` | `ci_type` |
| Python 版本 | `setup.py` python_requires / `pyproject.toml` | `python_version` |
| 包管理器 | `pyproject.toml` / `setup.py` / `package.json` / `Cargo.toml` | `package_manager` |

### 输出格式

```json
{
  "name": "my-project",
  "description": "A cool project",
  "language": "Python",
  "license": "MIT",
  "repo_url": "https://github.com/user/repo",
  "dependencies": ["requests", "click"],
  "has_readme": true,
  "readme_summary": {
    "sections": ["Installation", "Usage"],
    "line_count": 85
  },
  "logo_path": "docs/assets/logo.svg",
  "ci_type": "github-actions",
  "python_version": ">=3.9",
  "package_manager": "pip"
}
```

### 降级策略

- 脚本运行失败 → 手动检测（Glob/Grep/Read）
- 无 Python 环境 → 跳过脚本，纯手动检测
- 无 git 仓库 → 跳过 repo_url 和 Stars/Forks 徽章
- 无 LICENSE 文件 → 跳过 License 徽章，提示用户添加

---

## 5. Reference 文件设计

### `badge-templates.md`

按类别组织 30+ 种 shields.io 徽章模板：

- **基础徽章**: License、Stars、Forks、Issues、PRs、Last Commit
- **语言/包管理**: PyPI Version、PyPI Downloads、Python Version、npm version、Crates.io
- **CI/CD**: GitHub Actions、GitLab CI、Travis CI、Codecov
- **社区**: Discord、Twitter/X、LinkedIn、Blog、Documentation
- **质量**: Code Style (black/prettier)、PRs Welcome、Maintained
- **特殊**: Star History 图表、Contributors (contrib.rocks)、Sponsor

支持 4 种风格：`flat`（默认）、`for-the-badge`（现代）、`flat-square`、`social`。

### `section-templates.md`

为 README 的每个标准段落提供写作模板和示例：
- Header、Tagline、Features、Quick Start、Documentation、Contributing、Community、License、Star History、Contributors

### `style-guide.md`

定义炫酷全面型 README 的视觉规范：
- Emoji 使用规则（段落标题前缀，不超过 1 个/标题）
- 排版规范（水平线分隔、空行间距、代码块语言标注）
- 中英双语格式（头部语言切换链接、双语内容排列）
- Admonition 语法使用场景
- 表格格式规范

### `logo-fallback.md`

定义无 logo 时的 emoji 降级规则：
- 根据项目语言选择对应 emoji（Python→🐍, JavaScript→⚡, Rust→🦀 等）
- 大标题格式：`# <emoji> Project Name`
- 可选 ASCII art banner 的生成规则

---

## 6. 边界情况处理

| 场景 | 处理方式 |
|------|---------|
| 空项目（无代码文件） | 只生成最小 README（标题 + 描述 + License） |
| 单文件脚本 | 简化结构，不生成 Documentation/Contributing 等重型段落 |
| Monorepo | 检测到多个子项目时，询问用户是生成顶层 README 还是每个子项目单独生成 |
| 已有复杂 README（>500 行） | 先摘要再逐段确认，避免一次性展示过多内容 |
| 已有 README 但为空文件 | 视为无 README，走创建流程 |
| 用户想保留的段落与新模板冲突 | 将保留内容嵌入新模板对应位置 |

---

## 7. 兼容性

| 平台 | 支持程度 | 说明 |
|------|---------|------|
| Claude Code | 完整支持 | 脚本 + Glob/Grep/Read/WebFetch 全部可用 |
| Claude.ai | 部分支持 | 无脚本支持（降级为手动检测）、无 WebFetch（徽章 URL 需用户手动验证） |
| 其他 AI 工具 | 基础支持 | SKILL.md 可直接粘贴到 system prompt，脚本部分跳过 |

---

## 8. 与 enhanced-skill-creator 的关系

本 skill 将使用 enhanced-skill-creator 的完整 8 阶段流程开发：
1. 需求收集 ✓（本文档）
2. 草稿编写
3. 自审门控
4. 测试生成与执行
5. 反馈与迭代
6. 描述优化
7. 兼容性报告
8. 打包

开发完成后，skill 可独立使用，不依赖 enhanced-skill-creator。
