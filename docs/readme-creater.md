# readme-creater

通用 README 创建器 + 改进器——自动检测项目元数据，生成炫酷、专业的项目 README。

## 功能

- 自动检测项目元数据（名称、语言、许可证、依赖、CI、Logo 等）
- 现有 README 智能分析，逐段询问保留/重写/删除
- 生成含 shields.io 徽章、Star History 图表、contrib.rocks 贡献者网格的炫酷 README
- 中英双语支持，头部语言切换链接
- Logo 智能检测 + emoji 降级
- 跨平台兼容（Claude Code / Claude.ai / 其他 AI 工具）

## 依赖

- Python >= 3.8（可选，用于自动检测脚本 `scripts/detect_project.py`）
- 无外部 API 依赖

## 使用方式

在支持 Skills 的 AI 工具中安装后，说以下任意触发词即可：

- 中文：`创建 readme`、`改进 readme`、`生成 readme`、`写 readme`、`优化 readme`
- 英文：`write readme`、`improve readme`、`generate readme`
- 斜杠命令：`/readme`

## 流程概览

1. **项目检测** — 运行 `detect_project.py` 或手动扫描项目结构，提取元数据
2. **现有 README 分析** — 如果已有 README，逐段展示并询问保留/重写/删除
3. **交互确认** — 确认徽章组合、Logo 策略、语言模式、风格、额外段落
4. **README 生成** — 按 15 个标准段落顺序生成完整 README
5. **审查与迭代** — 自动审查（链接、代码块、emoji、占位符），用户确认后写入文件

## 目录结构

```
skills/readme-creater/
├── SKILL.md                      # 主指令文件（~400 行）
├── scripts/
│   └── detect_project.py         # 项目元数据自动检测脚本
└── references/
    ├── badge-templates.md        # shields.io 徽章模板库（30+ 种徽章）
    ├── section-templates.md      # README 各段落的写作模板
    ├── style-guide.md            # 视觉风格指南
    └── logo-fallback.md          # emoji 降级 logo 规则
```

## 支持的项目类型

脚本自动检测以下项目配置：

| 配置文件 | 生态系统 | 检测字段 |
|---------|---------|---------|
| `package.json` | Node.js / npm / pnpm / yarn | name, description, license, dependencies, repo |
| `setup.py` | Python (pip) | name, description, license, python_requires |
| `pyproject.toml` | Python (pip / poetry) | name, description, license, dependencies |
| `Cargo.toml` | Rust | name, description, license, dependencies |
| `go.mod` | Go | module name, go version |

无配置文件时，通过文件扩展名统计推断主语言，从 LICENSE 文件识别许可证类型。

## 注意事项

- SKILL.md 保持在 500 行以内，复杂模板拆到 `references/` 目录
- 脚本仅做只读操作，不修改任何项目文件
- 生成 README 前会备份已有 README 为 `README.old.md`
