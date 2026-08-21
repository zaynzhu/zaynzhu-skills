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
| `first-principles` | first-principles | 第一性原理（拆四类:基本事实/习惯假设/目标/资源约束→提炼公理→重新推导→输出表面修补/新路径/前提/验证第一步） | 无 |
| `skill-protector` | skill-protector | skill 加密 + license 门禁（AES-256-GCM + Ed25519 签名） | Python >= 3.8, cryptography |
| `project-onboard` | project-onboard | 已有项目规则引导（证据生成 + 受管区块同步 CLAUDE.md/AGENTS.md） | 无（可选 git） |
| `agentseo` | agentseo | 网站智能体可读性审计（浏览器渲染+5维度规则审计+实证任务） | Node ≥ 22, npx agentseo, 浏览器 MCP |
| `steel-man` | steel-man | 双向钢人论证（重述真问题+正反各5项钢人画像:最强理由/适用条件/收益/风险/反对意见+找分歧/关键变量/缺信息+只问一个+逼出判断+适用条件+下一步） | 无 |
| `socratic-questioning` | socratic-questioning | 苏格拉底式提问（最多6问逐个追问+区分事实/解释/价值/目标+整理出真问题+确认后给判断） | 无 |
| `dual-layer-explanation` | dual-layer-explanation | 双层解释法（小白版+专业版两层+三件套：对应关系/易错点/3检查问题） | 无 |
| `reverse-deconstruction` | reverse-deconstruction | 反向拆解（一句话问题+五点分析+三件套：可复用规律/应用清单/小练习） | 无（URL抓取可选浏览器MCP） |
| `enhanced-hv-analysis` | enhanced-hv-analysis | 增强版横纵分析（纵轴路径依赖/能力/包袱+横轴选择与放弃+未来3路径预警信号+证据规则可追溯+结论先行出PDF） | 联网搜索, WeasyPrint(可选) |
| `fact-check` | fact-check | 事实核查（拆事实/结论/价值三层+事实5级核查+推理链5查+四件套输出+笛卡尔怀疑底色） | 联网搜索(无网降级) |
| `expert-panel` | expert-panel | 专家会诊（3互补视角独立答4问+互相质疑挖分歧假设+综合方案保留分歧+退出条件挂钩假设） | 子Agent(无则降级内联) |
| `cross-domain-borrowing` | cross-domain-borrowing | 跨领域借解（剥术语找底层结构+历史+3远领域结构同构借机制+3机制翻译方案+1可逆实验+案例标置信核实） | 联网搜索(核实非著名案例,可选) |
| `minimum-experiment` | minimum-experiment | 用最小实验替代空想（3假设选1+低成本可逆7天实验6件+明天第一个动作+第二轮解读结果判断继续/调方向/停止+不可逆改可逆） | 无 |
| `talent-mining` | talent-mining | 挖掘隐藏天赋（多轮苏格拉底对话最多10主问+4主线:童年/无意识胜任/能量/嫉妒+出个人天赋说明书6部分+反宿命论能量审计阴影即宝藏+长度自适应不编造） | 无 |
| `life-odyssey` | life-odyssey | 人生设计斯坦福法（多轮对话6-9主问4阶段+分清重力问题/可设计问题+三个完全不同五年奥德赛计划+原型行动+出个人人生设计蓝图8部分+看未来与talent-mining互补+长度自适应） | 无 |

## 强制规则

- **新增/删除 skill 时，README.md 技能索引表和本文件清单必须同步**
- **所有 skill 的 scripts 中涉及外部 API 调用必须做频率限制**，间隔不低于 2 秒
- **SKILL.md 控制在 500 行以内**，复杂逻辑拆到 references 或 agents
- **发布 = 将 skill 目录复制到目标项目的 `.claude/skills/` 或 `.codex/skills/`（取决于目标平台）**
