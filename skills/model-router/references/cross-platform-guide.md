# Model Router 跨平台使用指南

## 核心：平台无关的 Python 脚本

所有核心逻辑都在 Python 脚本中，任何支持 shell 调用的 CLI 工具都能使用：

```
skills/model-router/scripts/
├── model_config.py   ← 交互式配置管理（add/list/test/remove/edit）
└── model_router.py   ← 路由引擎（根据任务类型调用模型）
```

## 快速使用（任意 CLI）

### 配置模型
```bash
python skills/model-router/scripts/model_config.py add
```

### 列出已配置模型
```bash
python skills/model-router/scripts/model_config.py list
```

### 测试模型连接
```bash
python skills/model-router/scripts/model_config.py test
```

### 调用模型
```bash
# 根据任务类型自动选择模型
python skills/model-router/scripts/model_router.py route \
  --task has_image_input \
  --prompt "描述这张图片" \
  --image /path/to/screenshot.png

# 直接指定模型
python skills/model-router/scripts/model_router.py route \
  --profile gpt4o \
  --prompt "分析这段代码"

# 图片 URL
python skills/model-router/scripts/model_router.py route \
  --task has_image_input \
  --prompt "这个验证码是什么？" \
  --image-url "https://example.com/captcha.png"
```

## 各平台适配

### Claude Code

直接使用 skill 触发：
- `/model-router` 或自动触发（检测到图片/验证码等关键词）
- Skill 文件：`skills/model-router/SKILL.md`

### Gemini CLI

在 `GEMINI.md` 中引用：
```markdown
## Model Router
当需要图片识别或切换模型时，运行：
python skills/model-router/scripts/model_router.py route --task has_image_input --prompt "..." --image "..."
```

### OpenCode / Codex / Antigravity CLI

在项目的指令文件（如 `AGENTS.md`、`.cursorrules`、`CLAUDE.md` 等）中添加：

```markdown
## 模型切换
遇到需要图片识别的场景（验证码、截图分析等），使用 model_router.py：
python skills/model-router/scripts/model_router.py route --task has_image_input --prompt "..." --image "..."
```

### 通用 Shell

直接在终端使用：
```bash
# 添加模型
python skills/model-router/scripts/model_config.py add

# 识别验证码
python skills/model-router/scripts/model_router.py route \
  --task has_image_input \
  --prompt "这个验证码是什么？请只返回验证码文字" \
  --image ./captcha.png
```

## 环境变量

API Key 通过环境变量设置：
```bash
export OPENAI_API_KEY=sk-xxx
export GOOGLE_API_KEY=AIzaSy-xxx
export ANTHROPIC_API_KEY=sk-ant-xxx
```

或通过配置脚本交互式设置（会写入 `.env` 文件）。
