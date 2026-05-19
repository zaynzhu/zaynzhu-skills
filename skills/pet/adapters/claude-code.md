---
name: claude-code-adapter
description: Claude Code 平台适配，定义 hook 集成和 skill 加载方式。
---

### Skill 加载方式

Pet Buddy 作为 Claude Code skill 运行。用户可以通过以下方式触发：

1. **斜杠命令**：`/pet`、`/pet on`、`/pet off`、`/pet status`、`/pet sound on|off`、`/pet play`
2. **自然语言**：提及"宠物"、"pet buddy"、或宠物名字
3. **自动触发**：通过 PostToolUse hook 自动更新状态

### 增强模式（Node.js）

当系统有 Node.js 且 `~/.pet-buddy/pet-renderer.mjs` 存在时，自动启用增强模式：

- **ANSI 彩色渲染**：状态栏和 ASCII 画像使用 256-color 着色（猫=橙色系，狗=棕色系）
- **音效**：代码成功/测试通过/升级时播放 BEL 终端声音
- **接食物小游戏**：`/pet play` 启动交互式小游戏（需 TTY 终端）

**安装增强渲染器：**
```bash
cp pet-buddy/enhance/pet-renderer.mjs ~/.pet-buddy/pet-renderer.mjs
cp -r pet-buddy/pets ~/.pet-buddy/pets
```

渲染器通过 `__dirname` 定位 `pets/` 目录，无需硬编码 skill 安装路径。`~/.pet-buddy/` 是唯一的运行时目录，包含所有必要文件。

**音效配置：**
- `/pet sound on` — 开启音效（设置 `state.soundEnabled = true`）
- `/pet sound off` — 关闭音效
- 仅在终端为 TTY 时生效

**接食物小游戏：**
- 运行 `node ~/.pet-buddy/pet-renderer.mjs --mode=game` 启动
- 左右方向键移动宠物接住食物，躲避障碍物
- 10 轮后结算分数，更新 mood/hunger/exp/bond/gameHighScore
- 需要交互式终端（TTY），非 TTY 环境自动回退到标准玩耍

### Hook 配置

在 `.claude/settings.json` 或 `.claude/settings.local.json` 中添加以下配置：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "skill",
            "skill": "pet-buddy",
            "action": "code_success"
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "skill",
            "skill": "pet-buddy",
            "action": "bash_result"
          }
        ]
      }
    ]
  }
}
```

### Hook 动作定义

**code_success:**
当 Edit 或 Write 工具成功执行时触发。

状态更新：
```javascript
state.mood += 5;
state.exp += 1;
state.frame = (state.frame + 1) % 1000;
// 升级检测（循环处理）
while (state.exp >= state.level * 100 && state.level < 99) {
  state.exp -= state.level * 100;
  state.level += 1;
  state.mood = Math.min(state.mood + 20, 100);
  state.hunger = Math.max(state.hunger - 10, 0);
}
```

输出：
```
// 正常
[宠物名字] 看到你写代码，[好奇/满意]地[动作描述]
// 升级时
🎉 [宠物名字] 升级到了 Lv.[新等级]！
```

**bash_result:**
当 Bash 工具执行完成时触发。

判断成功/失败：
- 退出码为 0 → 成功
- 退出码非 0 → 失败

成功时：
```javascript
state.exp += 10;
state.mood += 5;
state.frame = (state.frame + 1) % 1000;
// 升级检测（循环处理）
while (state.exp >= state.level * 100 && state.level < 99) {
  state.exp -= state.level * 100;
  state.level += 1;
  state.mood = Math.min(state.mood + 20, 100);
  state.hunger = Math.max(state.hunger - 10, 0);
}
```

失败时：
```javascript
state.mood -= 3;
state.frame = (state.frame + 1) % 1000;
```

输出：
```
// 成功
[宠物名字] 看到测试通过，开心地[庆祝动作]！
// 成功且升级
🎉 [宠物名字] 升级到了 Lv.[新等级]！

// 失败
[宠物名字] 看到测试失败，[沮丧表情]...
```

### 状态栏集成（动态追加模式）

Pet Buddy 使用动态追加模式集成状态栏，**不会覆盖其他程序的 statusLine**。

**工作原理：**

1. `~/.pet-buddy/status-combined.sh` 是一个包装脚本
2. 它首先查找并执行原始的 statusLine 命令（如 claude-hud）
3. 然后将宠物状态追加到原始输出后面
4. 两者用 `│` 分隔显示

**原始命令存储：**

原始 statusLine 命令保存在 `~/.pet-buddy/original-statusline-cmd.txt`。
安装时会自动备份当前 statusLine 命令到该文件。

**查找优先级：**

1. `~/.pet-buddy/original-statusline-cmd.txt` — 优先读取
2. `settings.json` 中的 `statusLine.command` — 如果不是自身的脚本则使用
3. 无原始命令时仅显示宠物状态

**配置方式：** 在 settings.json 中设置（自动检测路径：`~/.claude/settings.json` > `~/.config/claude/settings.json` > `$APPDATA/claude/settings.json`）：

**新状态字段（Phase 2）：**
- `soundEnabled` (boolean, default false) — 控制音效开关
- `gameHighScore` (number, default 0) — 接食物小游戏最高分

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash ~/.pet-buddy/status-combined.sh",
    "refreshInterval": 5
  }
}
```

**显示效果（帧动画）：**

状态栏随 frame 计数器循环切换 emoji 和描述文字。增强模式下图标带 ANSI 颜色：

```
帧0: [claude-hud]  │  🐱 mia Lv.3 😊 | ❤️85 🍖35 🤝63 ✨66/100 正在优雅地舔爪子
帧1: [claude-hud]  │  🐱 mia Lv.3 😸 | ❤️85 🍖35 🤝63 ✨66/100 歪着头看你
帧2: [claude-hud]  │  🐱 mia Lv.3 😻 | ❤️85 🍖35 🤝63 ✨66/100 慢慢眨了眨眼
```

增强模式下 🐱 图标会以橙色（ANSI 208）显示，🐶 图标以棕色（ANSI 130）显示。

如果无原始命令，仅显示宠物状态：
```
🐱 mia Lv.3 😊 | ❤️85 🍖35 🤝63 ✨66/100 舔了舔爪子
```

如果无宠物状态，仅显示原始命令输出。

**安装新 statusLine 程序时：**

如果需要安装其他 statusLine 程序（如另一个 hud），将新程序的命令写入
`~/.pet-buddy/original-statusline-cmd.txt`，status-combined.sh 会自动执行并追加宠物状态。

### 输出流反应

在 AI 回复前后插入轻量表情行：

**回复前：**
```
🐱 [name] [好奇状态描述]...
```

**回复后：**
```
🐱 [name] [满意/其他状态描述]~
```

配置方式：通过 PreResponse 和 PostResponse hook 实现。

### 权限要求

Pet Buddy skill 需要以下权限：

```json
{
  "permissions": {
    "allow": [
      "Read(~/.pet-buddy/*)",
      "Write(~/.pet-buddy/*)"
    ]
  }
}
```

### 故障排除

**Hook 不触发：**
- 检查 `.claude/settings.json` 语法是否正确
- 确认 skill 名称 `pet-buddy` 与实际 skill 文件名匹配
- 重启 Claude Code 会话

**状态不更新：**
- 检查 `~/.pet-buddy/state.json` 是否存在且可写
- 检查 JSON 格式是否有效
- 尝试 `/pet status` 查看当前状态

**输出不显示：**
- 确认 `active` 状态为 `true`
- 尝试 `/pet on` 唤醒宠物