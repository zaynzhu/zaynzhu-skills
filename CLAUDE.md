# Zaynzhu Skills 项目规范

## 项目定位

个人 AI 技能合集，将专业工作流封装为可复用的指令集（Skill）。每个 Skill 是 `skills/` 下的独立目录，包含 `SKILL.md` 主文件和可选辅助资源。

## 当前技能清单

| 目录名 | name | 类型 | 核心依赖 |
|--------|------|------|----------|
| `mmy` | mmy | 热榜抓取（登录/匿名） | Python >= 3.8 |
| `video-downloader` | video-downloader | 视频下载 | Python >= 3.8, vendor 内含 |
| `tavily-search-enhanced` | tavily-search-enhanced | 联网搜索 | Python >= 3.8, TAVILY_API_KEY |
| `ideastorming` | ideastorming | AI 热点转项目选题 | Python >= 3.8, AIHOT 公开 API |
| `m3u8-downloader` | m3u8-downloader | m3u8 流下载 | ffmpeg |
| `coding-ai-digest` | coding-ai-digest | 排行榜分析 | Python >= 3.8, 可选 GitHub Token |
| `enhanced-skill-creator` | enhanced-skill-creator | 技能开发 | 无（可选 Python） |
| `enhanced-neat-freak` | enhanced-neat-freak | 知识库同步/交接清理 | 无（可选 shell、git、rg） |
| `pet` | pet | CLI 编程宠物（7种宠物/进化/成就/装扮） | Bash + jq / Node.js |
| `model-debate` | model-debate | 多模型辩论 | Python ≥ 3.8, curl, 模型 API Key |
| `trending-search` | trending-search | 热词搜索 | Python >= 3.8, TAVILY_API_KEY |
| `readme-creater` | readme-creater | README 创建/改进 | Python >= 3.8（可选，自动检测脚本） |
| `article-creater` | 公众号写作 | 公众号文章创作（长文/短内容/续写/改写） | 无（可选 MCP 搜索工具） |
| `model-router` | model-router | 动态模型切换（图片识别/验证码/多模型路由） | Python >= 3.8, curl, 模型 API Key |
| `TMPI` | TMPI | 文本主模型项目初始化（图片输入安全规则） | Python >= 3.8, 配合 model-router |
| `TMR` | TMR | 文本模型会话急救（清理 transcript 图片污染） | Python >= 3.8, 标准库, 配合 TMPI |
| `adversarial-review` | adversarial-review | 对抗性审查（红队审查），对任意内容找出致命弱点并给出改进建议 | 无 |
| `first-principles` | first-principles | 第一性原理推导，穷举现有假设→提炼底层公理→从公理重新推导无约束方案 | 无 |
| `skill-protector` | skill-protector | skill 加密 + license 门禁（AES-256-GCM + Ed25519 签名） | Python >= 3.8, cryptography |
| `project-onboard` | project-onboard | 已有项目规则引导（证据生成 + 受管区块同步 CLAUDE.md/AGENTS.md） | 无（可选 git） |
| `agentseo` | agentseo | 网站智能体可读性审计（浏览器渲染+5维度规则审计+实证任务） | Node ≥ 22, npx agentseo, 浏览器 MCP |
| `steel-man` | steel-man | 双向钢人论证（重述真问题+正反最强论证+找关键变量+只问一个问题+逼出明确判断） | 无 |
| `socratic-questioning` | socratic-questioning | 苏格拉底式提问（最多6问逐个追问+区分事实/解释/价值/目标+整理出真问题+确认后给判断） | 无 |
| `dual-layer-explanation` | dual-layer-explanation | 双层解释法（小白版+专业版两层+三件套：对应关系/易错点/3检查问题） | 无 |

## 强制规则

- **新增/删除 skill 时，README.md 技能索引表和本文件清单必须同步**
- **所有 skill 的 scripts 中涉及外部 API 调用必须做频率限制**，间隔不低于 2 秒
- **SKILL.md 控制在 500 行以内**，复杂逻辑拆到 references 或 agents
- **发布 = 将 skill 目录复制到目标项目的 `.claude/skills/` 或 `.codex/skills/`（取决于目标平台）**
