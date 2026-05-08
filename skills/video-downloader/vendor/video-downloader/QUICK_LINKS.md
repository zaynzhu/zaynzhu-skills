# 🔗 快速链接

不知道从哪里开始？这里是最常用的文档链接。

---

## 🎯 我想...

### 📥 下载视频（独立工具）
- **快速开始**: [README.md](README.md) - 项目主文档
- **详细教程**: [USAGE.md](USAGE.md) - 完整使用指南
- **示例代码**: [quick_start.py](quick_start.py) - 可运行的示例

### 🤖 让 AI 帮我下载（Skill）
- **安装 Skill**: [docs/skill/SKILL_INSTALLATION.md](docs/skill/SKILL_INSTALLATION.md)
- **一键安装**: 
  - Windows: `docs/skill/install_skill.bat`
  - Linux/Mac: `docs/skill/install_skill.sh`

### 📤 提交到 GitHub
- **提交指南**: [docs/github/GIT_COMMIT_GUIDE.md](docs/github/GIT_COMMIT_GUIDE.md)
- **一键提交**:
  - Windows: `docs/github/commit.bat`
  - Linux/Mac: `docs/github/commit.sh`

### 🔧 优化 GitHub 仓库
- **优化建议**: [docs/github/GITHUB_OPTIMIZATION.md](docs/github/GITHUB_OPTIMIZATION.md)

### 👨‍💻 了解项目结构
- **项目总结**: [docs/development/PROJECT_SUMMARY.md](docs/development/PROJECT_SUMMARY.md)
- **贡献指南**: [CONTRIBUTING.md](CONTRIBUTING.md)

### 📚 查看所有文档
- **文档目录**: [docs/README.md](docs/README.md)

---

## 📁 项目结构

```
vdl-skill/
├── video_downloader/      # 核心代码（Python 工具）
├── tests/                 # 测试代码
├── docs/                  # 📚 所有文档
│   ├── skill/            # Skill 相关（AI 调用）
│   ├── github/           # GitHub 相关
│   └── development/      # 开发相关
├── README.md             # 项目主文档
├── USAGE.md              # 详细使用指南
├── CONTRIBUTING.md       # 贡献指南
├── LICENSE               # MIT 许可证
└── requirements.txt      # Python 依赖
```

---

## ⚡ 最快上手方式

### 方式 1: 独立工具（5 分钟）

```bash
# 1. 安装依赖
pip install -r requirements.txt
playwright install chromium

# 2. 下载视频
python -m video_downloader https://www.bilibili.com/video/BV1xx411c7mD
```

### 方式 2: AI Skill（3 分钟）

```bash
# Windows
docs\skill\install_skill.bat

# Linux/Mac
chmod +x docs/skill/install_skill.sh
docs/skill/install_skill.sh
```

然后在 Claude Code 中说："帮我下载这个视频"

---

## 🆘 遇到问题？

1. **查看文档**: [USAGE.md](USAGE.md) 的故障排除部分
2. **提交 Issue**: [GitHub Issues](https://github.com/zaynzhu/vdl-skill/issues)
3. **查看示例**: [quick_start.py](quick_start.py)

---

**选择你需要的链接，开始使用吧！** 🚀
