---
name: model-router
description: |
  在任务执行过程中动态切换 AI 模型。当当前模型无法处理某些输入（如图片）或需要不同能力（如更强推理）时，
  自动或手动调用合适的外部模型，处理完毕后返回结果继续原始任务。
  当用户需要图片识别、验证码识别、图表分析、多模态处理，或需要切换到更强/更快的模型时触发。
  即使用户只说"用视觉模型看看这个"、"识别一下这个图片"、"这个验证码帮我处理一下"、"配置模型"、"添加模型"，也应该使用此技能。
  支持 Claude Code、Gemini CLI、OpenCode、Codex 等多平台。
compatibility:
  tools: [bash, python]
---

# Model Router — 动态模型切换

在任务执行中，根据上下文自动或手动切换到合适的外部模型。核心价值：让一个不支持图片输入的模型，通过调用视觉模型完成图片相关任务，然后回到原始任务继续执行。

---

## 核心特性

- **Fallback 链**：候选模型按优先级依次尝试，某个失败自动换下一个
- **成本感知路由**：每个模型配置成本（$/1M tokens），支持 cheapest/best/balanced 三种成本模式
- **查询自动分类**：从 prompt 内容自动推断任务类型，无需手动指定 `--task`
- **多 provider 支持**：OpenAI、Anthropic、Google、Ollama、自定义

---

## 工作流概览

```
检测需求 → 自动分类 → 选择候选(按成本排序) → 依次尝试 → 成功返回 / 全部失败报错
```

**脚本位置**：`skills/model-router/scripts/`
- `model_config.py` — 交互式配置管理（add/list/test/remove/edit）
- `model_router.py` — 路由引擎（根据任务类型调用模型）

**跨平台指南**：`skills/model-router/references/cross-platform-guide.md`

---

## 场景一：配置模型（交互式）

当用户说"配置模型"、"添加模型"、"设置 API key" 时：

```bash
python skills/model-router/scripts/model_config.py add
```

交互式引导用户：
1. 选择 provider（OpenAI/Google/Anthropic/Ollama/自定义）
2. 选择或输入模型名称
3. 设置 API Key 环境变量
4. 确认 endpoint
5. 选择能力标签（text/image/reasoning）
6. 配置成本（$/1M tokens，用于成本感知路由）
7. 自动更新路由规则

其他配置命令：
```bash
python skills/model-router/scripts/model_config.py list     # 列出已配置模型（含成本信息）
python skills/model-router/scripts/model_config.py test     # 测试模型连接
python skills/model-router/scripts/model_config.py edit     # 编辑已有模型（含成本）
python skills/model-router/scripts/model_config.py remove   # 删除模型
```

---

## 场景二：调用模型（自动路由）

当检测到需要切换模型的场景时，使用路由引擎：

### 自动分类模式（推荐）

让路由器自动从 prompt 推断任务类型：

```bash
python skills/model-router/scripts/model_router.py route \
  --auto-task \
  --prompt "帮我看看这个截图里的错误信息" \
  --image /path/to/screenshot.png
```

### 图片识别场景

```bash
python skills/model-router/scripts/model_router.py route \
  --task has_image_input \
  --prompt "描述这张图片的内容" \
  --image /path/to/screenshot.png
```

### 复杂推理场景

```bash
python skills/model-router/scripts/model_router.py route \
  --task complex_reasoning \
  --prompt "分析这段代码的架构问题"
```

### 直接指定模型

```bash
python skills/model-router/scripts/model_router.py route \
  --profile gpt4o \
  --prompt "你好"
```

### 成本模式

```bash
# 最便宜的能做这个任务的模型
python skills/model-router/scripts/model_router.py route \
  --task quick_task --cost cheapest --prompt "重命名这个文件"

# 最强的模型（不差钱模式）
python skills/model-router/scripts/model_router.py route \
  --task complex_reasoning --cost best --prompt "分析架构"

# 按配置顺序（默认）
python skills/model-router/scripts/model_router.py route \
  --task has_image_input --cost balanced --prompt "识别图片"
```

### 调试分类器

```bash
# 查看查询会被分类为什么任务类型
python skills/model-router/scripts/model_router.py classify --prompt "帮我看看这个验证码"
python skills/model-router/scripts/model_router.py classify --prompt "分析架构设计" --image shot.png
```

---

## 触发检测规则

分析当前任务上下文，判断是否需要切换模型：

| 检测条件 | 匹配规则 | 任务类型 |
|---------|---------|---------|
| 输入包含图片文件路径 | `.png`/`.jpg`/`.jpeg`/`.gif`/`.webp`/`.bmp` 结尾 | `has_image_input` |
| 输入包含 base64 图片数据 | `data:image/` 前缀 | `has_image_input` |
| 用户提到图片/截图/验证码 | 关键词：图片、截图、验证码、screenshot、captcha、OCR | `has_image_input` |
| 复杂推理任务 | 关键词：深度分析、架构设计、代码审查、review、debug | `complex_reasoning` |
| 轻量任务 | 关键词：格式化、简单查找、重命名、翻译 | `quick_task` |

手动触发关键词：
- "用视觉模型处理这个"
- "识别一下这个图片"
- "这个验证码帮我看看"
- "用更强的模型分析一下"

---

## 路由逻辑

### 三层决策

1. **任务分类**：`--task` 手动指定，或 `--auto-task` 从 prompt 自动推断
2. **候选排序**：按 routing 规则的 `prefer` 列表排序，再按 `cost_mode` 调整
3. **Fallback 链**：依次尝试候选模型，某个失败（超时/限流/报错）自动换下一个

### 成本模式

| 模式 | 行为 | 适用场景 |
|------|------|----------|
| `cheapest` | 最便宜的在前 | 图片识别、简单任务 |
| `best` | 最贵（最强）的在前 | 复杂推理、架构分析 |
| `balanced` | 保持配置文件中的顺序 | 通用 |

### 配置文件中的 cost_mode

每个 routing 规则可以设置默认 cost_mode：

```yaml
routing:
  - match: has_image_input
    prefer: [gpt4o, gemini-vision, ollama-local]
    cost_mode: cheapest     # 图片任务能用就行，省钱优先
  - match: complex_reasoning
    prefer: [claude-opus]
    cost_mode: best         # 推理任务质量优先
  - match: quick_task
    prefer: [claude-haiku]
    cost_mode: cheapest     # 简单任务最便宜的就行
```

CLI 的 `--cost` 参数会覆盖配置文件中的 cost_mode。

---

## 手动模式（curl 直接调用）

如果脚本不可用，可以用 curl 直接调用。详见 `references/cross-platform-guide.md` 中的 API 模板。

---

## 错误处理

| 错误场景 | 处理方式 |
|---------|---------|
| 配置文件不存在 | 运行 `model_config.py add` 创建 |
| API key 未设置 | 运行 `model_config.py add`，脚本会引导设置 |
| 某个模型调用失败 | 自动尝试 prefer 列表中的下一个模型 |
| HTTP 429/5xx | 自动重试下一个候选（可重试错误） |
| HTTP 400/401 | 不重试，直接换下一个（不可重试错误） |
| 所有候选都失败 | 提示用户检查 key 或添加新模型 |

---

## 跨平台使用

本 skill 的核心脚本（`model_config.py`、`model_router.py`）是平台无关的，任何支持 shell 调用的 CLI 工具都能使用。

详见 `references/cross-platform-guide.md`。
