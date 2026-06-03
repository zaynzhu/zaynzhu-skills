# Zaynzhu Skills 项目规范

## 项目定位

个人 AI 技能合集，将专业工作流封装为可复用的指令集（Skill）。每个 Skill 是 `skills/` 下的独立目录，包含 `SKILL.md` 主文件和可选辅助资源。

## 当前技能清单

| 目录名 | name | 类型 | 核心依赖 |
|--------|------|------|----------|
| `mmy` | mmy | 热榜抓取（登录/匿名） | Python >= 3.8 |
| `video-downloader` | video-downloader | 视频下载 | Python >= 3.8, vendor 内含 |
| `tavily-search-enhanced` | tavily-search-enhanced | 联网搜索 | Python >= 3.8, TAVILY_API_KEY |
| `m3u8-downloader` | m3u8-downloader | m3u8 流下载 | ffmpeg |
| `coding-ai-digest` | coding-ai-digest | 排行榜分析 | Python >= 3.8, 可选 GitHub Token |
| `enhanced-skill-creator` | enhanced-skill-creator | 技能开发 | 无（可选 Python） |
| `pet` | pet | CLI 编程宠物（7种宠物/进化/成就/装扮） | Bash + jq / Node.js |
| `model-debate` | model-debate | 多模型辩论 | Python ≥ 3.8, curl, 模型 API Key |
| `trending-search` | trending-search | 热词搜索 | Python >= 3.8, TAVILY_API_KEY |
| `readme-creater` | readme-creater | README 创建/改进 | Python >= 3.8（可选，自动检测脚本） |
| `article-creater` | 公众号写作 | 公众号文章创作（长文/短内容/续写/改写） | 无（可选 MCP 搜索工具） |
| `model-router` | model-router | 动态模型切换（图片识别/验证码/多模型路由） | Python >= 3.8, curl, 模型 API Key |

## 强制规则

- **新增/删除 skill 时，README.md 技能索引表和本文件清单必须同步**
- **所有 skill 的 scripts 中涉及外部 API 调用必须做频率限制**，间隔不低于 2 秒
- **SKILL.md 控制在 500 行以内**，复杂逻辑拆到 references 或 agents
- **发布 = 将 skill 目录复制到目标项目的 `.claude/skills/`**