---
name: opencode-adapter
description: OpenCode (anomalyco/sst) 平台适配，定义 plugin 集成和 skill 加载方式。
---

### Skill 加载方式

Pet Buddy 在 OpenCode 中通过 skill 系统加载。OpenCode 兼容 `.claude/skills/` 目录结构，因此可以使用以下任一方式部署 SKILL.md：

1. **项目级**：`.opencode/skills/pet/SKILL.md`
2. **项目级（Claude 兼容）**：`.claude/skills/pet/SKILL.md`
3. **全局级**：`~/.config/opencode/skills/pet/SKILL.md`
4. **全局级（Claude 兼容）**：`~/.claude/skills/pet/SKILL.md`

OpenCode 会自动发现这些路径中的 skill。触发方式与 Claude Code 相同：

1. **Skill 工具调用**：AI 代理通过 `skill({ name: "pet" })` 主动加载
2. **自然语言**：提及"宠物"、"pet buddy"、或宠物名字

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

### Plugin 集成

OpenCode 使用 JS/TS 插件系统而非 bash hook 脚本。Pet Buddy 的插件文件位于 `pet/hooks/opencode/pet-plugin.ts`。

**配置方式：**

在 `~/.config/opencode/opencode.json` 中添加插件引用：

```json
{
  "plugin": [
    "~/.config/opencode/node_modules/superpowers",
    "~/.config/opencode/plugins/pet.ts"
  ]
}
```

**或项目级部署（随项目版本控制）：**
```bash
cp pet/hooks/opencode/pet-plugin.ts .opencode/plugins/pet.ts
```

**插件依赖：**
- `@opencode-ai/plugin` — OpenCode 插件类型定义（需安装到 OpenCode 的 node_modules 中）
- Node.js 内置模块：`fs/promises`, `path`, `os`

**安装插件依赖：**
```bash
cd ~/.config/opencode && bun install
```

### Plugin 事件处理

| Hook | 行为 | 状态变化 |
|------|------|---------|
| `tool.execute.after` (Edit/Write) | 代码写入后更新宠物状态，追加反应到工具输出 | mood +5, exp +1, frame +1 |
| `tool.execute.after` (Bash) | 命令执行后根据输出判断成功/失败 | 成功: exp +10, mood +5; 失败: mood -3 |
| `experimental.chat.system.transform` | 每次对话开始时注入宠物状态到系统提示 | 无状态变化，仅展示 |

### Hook 动作定义

与 Claude Code 适配器相同的逻辑（见 adapters/claude-code.md），但通过 TypeScript 实现：

- **code_success**: `tool.execute.after` 事件中，tool 为 "Edit" 或 "Write" → mood +5, exp +1, frame +1
- **bash_result**: `tool.execute.after` 事件中，tool 为 "Bash" → 检查输出中的 error/fail/exit code 判断成功或失败

**Bash 失败检测逻辑：** 插件通过正则匹配工具输出中的 `error`、`fail`、`exit code [1-9]` 关键词来判断命令是否失败。匹配到则 mood -3，未匹配则视为成功（exp +10, mood +5）。

### 状态展示

OpenCode 使用 TUI 界面，**没有 statusLine 功能**。宠物状态通过以下两种方式展示：

1. **工具输出追加**: `tool.execute.after` 事件在每次 Edit/Write/Bash 工具调用后，将宠物反应和状态栏追加到工具输出中
   - 示例：`🐱 mia 看到你写代码，好奇地盯着屏幕~ [🐱 mia Lv.3 😊 | ❤️85 🍖35 🤝63 ✨66/300]`

2. **系统提示注入**: `experimental.chat.system.transform` 在每次对话开始时将宠物状态注入到系统提示，让 AI 自然地提及宠物
   - 示例：`[Pet Buddy] 🐱 mia is with you. Status: 🐱 mia Lv.3 😊 | ❤️85 🍖35 🤝63 ✨66/300`

3. **手动查看**: 用户通过自然语言询问宠物状态（如"我的宠物怎么样了"）

### 自定义指令文件

OpenCode 使用 `AGENTS.md` 加载项目级自定义指令。可以通过 `/init` 命令自动生成。

### 权限要求

Pet Buddy 在 OpenCode 中需要以下权限：

- 读取和写入 `~/.pet/` 目录（通过 Node.js fs 模块）
- 插件自动加载（OpenCode 默认加载 `.opencode/plugins/` 和 `~/.config/opencode/plugins/`）

### 故障排除

**Plugin 不加载：**
- 确认插件文件位于 `.opencode/plugins/` 或 `~/.config/opencode/plugins/`
- 确认 `opencode.json` 的 `plugin` 数组中包含插件路径
- 检查 TypeScript 语法是否正确
- 重启 OpenCode 会话

**状态不更新：**
- 检查 `~/.pet/state.json` 是否存在且可写
- 检查 JSON 格式是否有效
- 查看插件是否有错误日志

**Skill 不触发：**
- 确认 SKILL.md 位于正确的 skill 目录
- 确认文件名为大写 `SKILL.md`
- 检查 frontmatter 中的 `name` 字段是否为 `pet`

**宠物状态不在对话中显示：**
- `experimental.chat.system.transform` 是实验性 API，可能在某些 OpenCode 版本中不可用
- 确认 OpenCode 版本 >= 1.3.0
- 工具输出追加（`tool.execute.after`）仍会工作