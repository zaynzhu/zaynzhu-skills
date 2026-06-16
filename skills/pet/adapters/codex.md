---
name: codex-adapter
description: OpenAI Codex CLI 平台适配，定义 plugin 打包和 hook 集成方式。
---

### 安装方式

Pet Buddy 支持两种 Codex CLI 安装方式：

#### 方式一：Plugin 安装

将 Pet Buddy 作为 Codex 插件安装，skill 会自动加载。插件根目录同时提供 `hooks.json`，用于支持 Codex 默认发现 hooks 的版本。Codex CLI 没有真正的 statusLine API，因此插件通过 `PostToolUse` hook 在每次工具执行后输出宠物反应、ASCII 画像和状态栏，形成接近常驻的 UI。

```bash
# 1. 复制整个 pet 目录到 Codex 插件目录
cp -r pet ~/.codex/plugins/cache/local/pet

# 2. 注册插件（添加到项目级或全局 marketplace）
# 在 .codex/plugins/marketplace.json 或 ~/.codex/plugins/marketplace.json 中添加：
# { "source": "local", "path": "~/.codex/plugins/cache/local/pet" }

# 3. 增强渲染器（可选；插件 hook 会优先使用 ~/.pet，缺失时回退到插件内置文件）
cp pet/enhance/pet-renderer.mjs ~/.pet/pet-renderer.mjs
cp -r pet/pets ~/.pet/pets
```

插件清单文件 `.codex-plugin/plugin.json` 已配置好 `skills` 引用。安装后，Codex 会发现 `skills/pet/SKILL.md` 中的 skill 入口；支持插件 hook 自动发现的 Codex 版本会同时加载插件根目录的 `hooks.json`。如果当前 Codex 版本没有自动发现 hooks，使用“方式二”手动配置。

#### 方式二：手动安装

仅配置 hooks，不使用 plugin 系统：

```bash
# 1. 复制 hook 脚本到运行时目录
cp pet/hooks/codex/hook-code-success.sh ~/.pet/
cp pet/hooks/codex/hook-bash-result.sh ~/.pet/
cp pet/hooks/codex/apply-decay.sh ~/.pet/
cp pet/hooks/codex/check-achievements.sh ~/.pet/check-achievements.sh
chmod +x ~/.pet/hook-code-success.sh
chmod +x ~/.pet/hook-bash-result.sh
chmod +x ~/.pet/apply-decay.sh
chmod +x ~/.pet/check-achievements.sh

# 2. 配置 hooks（选择以下方式之一）
```

**方式 2a：~/.codex/hooks.json**

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "apply_patch|Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.pet/hook-code-success.sh",
            "statusMessage": "🐱 Pet Buddy reacting..."
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.pet/hook-bash-result.sh",
            "statusMessage": "🐱 Pet Buddy reacting..."
          }
        ]
      }
    ]
  }
}
```

**方式 2b：~/.codex/config.toml（内联）**

```toml
[[hooks.PostToolUse]]
matcher = "apply_patch|Edit|Write"

[[hooks.PostToolUse.hooks]]
type = "command"
command = "bash ~/.pet/hook-code-success.sh"
statusMessage = "🐱 Pet Buddy reacting..."

[[hooks.PostToolUse]]
matcher = "Bash"

[[hooks.PostToolUse.hooks]]
type = "command"
command = "bash ~/.pet/hook-bash-result.sh"
statusMessage = "🐱 Pet Buddy reacting..."
```

### Plugin 结构

```
pet/
├── .codex-plugin/
│   └── plugin.json          ← 插件清单（引用 skills）
├── hooks.json               ← Codex 插件 hook 自动发现入口
├── skills/
│   └── pet/
│       └── SKILL.md         ← Codex 插件 skill 入口
├── codex-hooks/
│   └── hooks.json           ← 兼容旧文档路径的 PostToolUse hook 配置
├── hooks/
│   └── codex/               ← Bash hook 脚本
│       ├── hook-code-success.sh
│       ├── hook-bash-result.sh
│       └── apply-decay.sh
├── SKILL.md                  ← Skill 定义（兼容 Codex 的 AGENTS.md）
├── adapters/
│   └── codex.md              ← 本文档
├── pets/
├── state/
└── enhance/
```

### Hook 事件处理

| 事件 | Matcher | 行为 | 状态变化 |
|------|---------|------|---------|
| PostToolUse | `apply_patch\|Edit\|Write` | 代码写入成功 | mood +5, exp +1, frame +1 |
| PostToolUse | `Bash` | 命令执行结果 | 成功: exp +10, mood +5; 失败: mood -3 |

**注意：** Codex 的工具名 `apply_patch` 是代码编辑的规范名称，`Edit` 和 `Write` 是其别名。三个名称都需包含在 matcher 中。

### Hook 输入格式

Codex PostToolUse hook 通过 stdin 接收 JSON，格式如下：

```json
{
  "session_id": "...",
  "hook_event_name": "PostToolUse",
  "tool_name": "Bash",
  "tool_use_id": "...",
  "tool_input": {"command": "..."},
  "tool_response": { ... },
  "cwd": "...",
  "model": "...",
  "permission_mode": "...",
  "turn_id": "...",
  "transcript_path": "..."
}
```

`tool_response` 的结构取决于具体工具（schema 为 unconstrained）。hook-bash-result.sh 会尝试多种常见 exit code 字段名（`exit_code`、`exitCode`），默认为 0（成功）。

### Hook 输出格式

```json
{"systemMessage": "🐱 mia 看到你写代码，好奇地盯着屏幕~\n\n  /\\_/\\\n ( •ω• )\n  > _ <\n🐱 mia Lv.3 😸 | ❤️85 🍖35 🤝63 ✨66/300 舔了舔爪子"}
```

Codex 支持 `systemMessage`（UI 可见）和 `additionalContext`（模型可见）两种输出字段。

### Skill 加载方式

Pet Buddy 在 Codex CLI 中通过 plugin 的 skills 引用自动加载。也可手动部署：

1. **项目级**：`.codex/skills/pet/SKILL.md`
2. **全局级**：`~/.codex/skills/pet/SKILL.md`

触发方式与 Claude Code 相同：

1. **自然语言**：提及"宠物"、"pet buddy"、或宠物名字
2. **手动触发**：直接描述宠物相关请求

### 增强模式（Node.js）

与 Claude Code 增强模式完全相同。当系统有 Node.js 且 `~/.pet/pet-renderer.mjs` 存在时，自动启用：

- **ANSI 彩色渲染**：状态和 ASCII 画像使用 256-color 着色
- **音效**：代码成功/测试通过/升级时播放 BEL 终端声音
- **接食物小游戏**：`/pet play` 启动交互式小游戏

**安装增强渲染器：**
```bash
cp pet/enhance/pet-renderer.mjs ~/.pet/pet-renderer.mjs
cp -r pet/pets ~/.pet/pets
```

### 状态展示

Codex CLI 使用全屏 TUI，没有 statusLine 功能。宠物状态通过以下方式展示：

1. **Hook systemMessage**: 每次工具执行后，hook 返回的 `systemMessage` 包含宠物反应、ASCII 画像和状态栏
   - 这不是底部常驻栏，但在 Codex 当前能力范围内是安装后自动显示的最接近方案

2. **手动查看**: 用户通过自然语言询问宠物状态

### 自定义指令文件

Codex CLI 使用 `AGENTS.md`（而非 `CLAUDE.md`）加载项目级自定义指令。Pet Buddy 的触发词和行为描述可以添加到项目的 `AGENTS.md` 中。

### 权限要求

Pet Buddy 在 Codex CLI 中需要以下权限：

- 读取和写入 `~/.pet/` 目录
- 执行 hook 脚本（bash）
- 如果当前 Codex 版本要求显式开启插件 hooks：`[features] plugin_hooks = true`

### 故障排除

**Plugin 不加载：**
- 确认 `~/.codex/config.toml` 中 `[features] plugin_hooks = true`
- 确认插件路径在 marketplace.json 中正确配置
- 重启 Codex CLI 会话

**Hook 不触发（手动安装）：**
- 检查 `~/.codex/hooks.json` 或 `~/.codex/config.toml` 语法是否正确
- 确认 hook 脚本路径正确且可执行（`chmod +x`）
- 确认 matcher 模式包含 `apply_patch`（不仅是 `Edit|Write`）
- 重启 Codex CLI 会话

**状态不更新：**
- 检查 `~/.pet/state.json` 是否存在且可写
- 检查 JSON 格式是否有效
- 尝试询问宠物状态查看当前状态
