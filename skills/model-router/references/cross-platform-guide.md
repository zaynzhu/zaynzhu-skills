# Model Router 跨平台使用指南

## 核心：平台无关的 Python 脚本

所有核心逻辑都在 Python 脚本中，任何支持 shell 调用的 CLI 工具都能使用：

```
skills/model-router/scripts/
├── model_config.py   ← 交互式配置管理（setting/add/list/test/remove/edit）
└── model_router.py   ← 路由引擎（根据任务类型调用模型）
```

## 快速使用（任意 CLI）

### 配置默认模型
```bash
python skills/model-router/scripts/model_config.py setting
```

依次输入 `openai` 或 `anthropic` 协议、模型 URL、模型名和 API Key。配置完成后，后续路由会优先使用该模型。

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
# 不支持图片输入的主模型先准备图片中转目录
python skills/model-router/scripts/model_router.py prepare

# 根据任务类型自动选择模型
python skills/model-router/scripts/model_router.py route \
  --task has_image_input \
  --prompt "描述这张图片" \
  --image .model-router/images/screenshot.png

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

如果当前主模型不支持图片输入，可以在项目 `CLAUDE.md` 写短规则：

```markdown
当前主模型不支持图片输入。任何截图、验证码、图片、图表、UI 自动化截图都不得直接作为图片内容发送给主模型，必须使用 model-router skill。
```

触发后，skill 会先运行：

```bash
python skills/model-router/scripts/model_router.py prepare
```

然后要求截图、验证码、图表和 UI 自动化图片保存到 `.model-router/images/`，再用 `route --image` 调用视觉模型。

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
python skills/model-router/scripts/model_router.py prepare
python skills/model-router/scripts/model_router.py route --task has_image_input --prompt "..." --image ".model-router/images/..."
```

### 通用 Shell

直接在终端使用：
```bash
# 配置默认模型
python skills/model-router/scripts/model_config.py setting

# 识别验证码
python skills/model-router/scripts/model_router.py prepare
python skills/model-router/scripts/model_router.py route \
  --task has_image_input \
  --prompt "这个验证码是什么？请只返回验证码文字" \
  --image .model-router/images/captcha.png
```

## 环境变量

API Key 通过环境变量设置：
```bash
export OPENAI_API_KEY=sk-xxx
export GOOGLE_API_KEY=AIzaSy-xxx
export ANTHROPIC_API_KEY=sk-ant-xxx
export MODEL_ROUTER_API_KEY=your-default-model-key
```

或通过配置脚本交互式设置（会写入 `.env` 文件）。
