---
name: codex-adapter
description: OpenAI Codex CLI 平台适配，定义 hook 集成和 skill 加载方式。
---

### Skill 加载方式

Pet Buddy 在 Codex CLI 中通过 skill 系统加载。触发方式与 Claude Code 相同：

1. **自然语言**：提及"宠物"、"pet buddy"、或宠物名字
2. **手动触发**：直接描述宠物相关请求

### 增强模式（Node.js）

与 Claude Code 增强模式完全相同。当系统有 Node.js 且 `~/.pet-buddy/pet-renderer.mjs` 存在时，自动启用：

- **ANSI 彩色渲染**：状态和 ASCII 画像使用 256-color 着色
- **音效**：代码成功/测试通过/升级时播放 BEL 终端声音
- **接食物小游戏**：`/pet play` 启动交互式小游戏

**安装增强渲染器：**
```bash
cp pet-buddy/enhance/pet-renderer.mjs ~/.pet-buddy/pet-renderer.mjs
cp -r pet-buddy/pets ~/.pet-buddy/pets
```

### Hook 配置

在 `~/.codex/config.toml` 中添加以下 hook 配置：

```toml
# Pet Buddy hooks for Codex CLI
# NOTE: Exact TOML schema depends on Codex CLI version.
# Verify against latest Codex docs before deployment.

[[hooks.PostToolUse]]
matcher = "Edit|Write"
type = "command"
command = "bash ~/.pet-buddy/hook-code-success.sh"
timeout_sec = 5
status_message = "🐱 Pet Buddy reacting..."

[[hooks.PostToolUse]]
matcher = "Bash"
type = "command"
command = "bash ~/.pet-buddy/hook-bash-result.sh"
timeout_sec = 5
status_message = "🐱 Pet Buddy reacting..."
```

### Hook 脚本部署

将 hook 脚本从仓库拷贝到运行时目录：

```bash
cp pet-buddy/hooks/codex/hook-code-success.sh ~/.pet-buddy/
cp pet-buddy/hooks/codex/hook-bash-result.sh ~/.pet-buddy/
cp pet-buddy/hooks/codex/apply-decay.sh ~/.pet-buddy/
chmod +x ~/.pet-buddy/hook-code-success.sh
chmod +x ~/.pet-buddy/hook-bash-result.sh
chmod +x ~/.pet-buddy/apply-decay.sh
```

### Hook 动作定义

与 Claude Code 相同（见 adapters/claude-code.md）：

- **code_success**: Edit/Write 工具成功 → mood +5, exp +1, frame +1
- **bash_result**: Bash 工具完成 → 成功时 exp +10, mood +5; 失败时 mood -3

### 状态展示

Codex CLI 使用全屏 TUI，没有 statusLine 功能。宠物状态通过以下方式展示：

1. **Hook systemMessage**: 每次工具执行后，hook 返回的 `systemMessage` 包含宠物反应和当前状态
   - 示例：`{"systemMessage": "🐱 mia 开心地摇着尾巴~ [Lv.6 ❤️100 🍖40 🤝67]"}`

2. **手动查看**: 用户通过自然语言询问宠物状态

### 自定义指令文件

Codex CLI 使用 `AGENTS.md`（而非 `CLAUDE.md`）加载项目级自定义指令。Pet Buddy 的触发词和行为描述可以添加到项目的 `AGENTS.md` 中。

### 权限要求

Pet Buddy 在 Codex CLI 中需要以下权限：

- 读取和写入 `~/.pet-buddy/` 目录
- 执行 hook 脚本（bash）

### 故障排除

**Hook 不触发：**
- 检查 `~/.codex/config.toml` 语法是否正确（TOML 格式）
- 确认 hook 脚本路径正确且可执行
- 重启 Codex CLI 会话

**状态不更新：**
- 检查 `~/.pet-buddy/state.json` 是否存在且可写
- 检查 JSON 格式是否有效
- 尝试询问宠物状态查看当前状态