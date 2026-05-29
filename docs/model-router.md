# Model Router 使用文档

动态模型切换 skill，在任务执行中根据上下文自动路由到合适的 AI 模型。

## 核心场景

- Playwright 测试中遇到验证码 → 调用视觉模型识别
- 需要分析截图/图片 → 调用多模态模型
- OCR 文字识别 → 调用视觉模型
- 复杂推理任务 → 调用更强的推理模型

## 快速开始

### 1. 添加模型（交互式）

```bash
python skills/model-router/scripts/model_config.py add
```

按提示选择 provider、模型、设置 API Key。

### 2. 列出已配置模型

```bash
python skills/model-router/scripts/model_config.py list
```

### 3. 测试模型连接

```bash
python skills/model-router/scripts/model_config.py test
```

### 4. 调用模型

```bash
# 自动分类（推荐，从 prompt 推断任务类型）
python skills/model-router/scripts/model_router.py route \
  --auto-task \
  --prompt "帮我看看这个截图里的错误" \
  --image ./screenshot.png

# 指定任务类型（fallback 链自动尝试多个模型）
python skills/model-router/scripts/model_router.py route \
  --task has_image_input \
  --prompt "这个验证码是什么？" \
  --image ./captcha.png

# 成本模式：最便宜的能用的模型
python skills/model-router/scripts/model_router.py route \
  --task quick_task --cost cheapest \
  --prompt "重命名这个文件"

# 直接指定模型
python skills/model-router/scripts/model_router.py route \
  --profile mimo-v25 \
  --prompt "你好"

# 调试分类器
python skills/model-router/scripts/model_router.py classify \
  --prompt "帮我看看这个验证码"
```

### 核心特性

- **Fallback 链**：候选模型按优先级依次尝试，某个失败自动换下一个
- **成本感知路由**：每个模型配置成本（$/1M tokens），支持 cheapest/best/balanced 三种模式
- **查询自动分类**：`--auto-task` 从 prompt 内容自动推断任务类型
- **可重试错误检测**：HTTP 429/5xx 自动换下一个，400/401 不重试

## 支持的 Provider

| Provider | 模型示例 | 能力 | API Key 环境变量 |
|----------|---------|------|-----------------|
| OpenAI | GPT-4o, GPT-4o-mini | text, image | OPENAI_API_KEY |
| Google | Gemini 2.0 Flash | text, image | GOOGLE_API_KEY |
| Anthropic | Claude Opus/Sonnet/Haiku | text, reasoning | ANTHROPIC_API_KEY |
| Ollama | LLaVA, Llama3 | text, image | 无需 key |
| 自定义 | 兼容 OpenAI 协议的任意模型 | 可配置 | 可配置 |

## 配置文件

- `model-router.yaml` — 模型 profiles 和路由规则
- `.env` — API Key（不提交到 git）

## 在对话中使用

在 Claude Code 对话中说"识别这个图片"、"看看这个验证码"即可触发。

在 Playwright 测试场景中，skill 会自动检测图片需求并调用视觉模型。

## 跨平台

核心脚本 `model_router.py` 是平台无关的，任何支持 shell 调用的 CLI 工具都能使用。

详见 `references/cross-platform-guide.md`。
