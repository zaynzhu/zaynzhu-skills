# pet

CLI 编程伴侣宠物——有持久属性的猫/狗宠物，能对工作状态做出实时反应。

## 功能

- 持久状态（饥饿、心情、等级等）
- 对工作状态实时反应（写代码、修 bug、提交成功等）
- 互动指令：喂食、玩耍、抚摸
- ASCII 画像常驻显示（ANSI 256-color）
- 音效反馈（BEL 终端声音）
- 增强模式：接食物小游戏
- 状态栏集成 + Hook 自动互动
- **项目级开关**：不同项目可独立启用/禁用宠物
- **多平台支持**：Claude Code、Codex CLI、OpenCode

## 多平台支持

| 平台 | 集成方式 | 状态显示 |
|------|---------|---------|
| Claude Code | Bash hooks + settings.json statusLine | 状态栏持久显示 |
| Codex CLI | Plugin 打包（.codex-plugin/）或 Bash hooks + hooks.json | systemMessage 工具输出 |
| OpenCode | TypeScript 插件 + system prompt 注入 | 工具输出 + AI 自然提及 |

核心状态文件 `~/.pet/state.json` 跨平台共享。

## 项目级开关

在项目根目录放 `.pet.json` 控制该项目是否启用宠物：

```json
{"enabled": false}  // 该项目禁用宠物
{"enabled": true}   // 该项目启用宠物（默认）
```

也可用自然语言控制：说"关闭宠物"或"开启宠物"即可。

## 依赖

- Bash + jq（Claude Code / Codex CLI hooks）
- Node.js（增强模式渲染器、OpenCode 插件）
- 无需额外 Python 包

## 触发词

| 命令 | 自然语言 | 说明 |
|------|---------|------|
| `/pet on` | 开启宠物、要宠物 | 项目级激活 |
| `/pet off` | 关闭宠物、不要宠物 | 项目级停用 |
| `/pet status` | 宠物状态 | 查看完整状态 |
| `/pet feed` | 喂食 | 喂食宠物 |
| `/pet play` | 玩耍 | 玩耍（增强模式启动接食物小游戏） |
| `/pet pet` | 摸摸 | 抚摸宠物 |
| `/pet ascii on` | - | 开启 ASCII 画像常驻显示 |
| `/pet ascii off` | - | 关闭画像，仅状态栏 |
| `/pet sound on` | - | 开启音效 |
| `/pet sound off` | - | 关闭音效 |

也可以用自然语言触发，如"我的宠物怎么样了"、"喂一下小黑"、"跟宠物玩一下"。

## 状态文件

宠物状态保存在 `~/.pet/state.json`，跨会话持久。

## 文件结构

```
pet/
├── SKILL.md              ← 主指令
├── .codex-plugin/        ← Codex CLI 插件清单
│   └── plugin.json
├── adapters/             ← 平台适配文档
│   ├── claude-code.md    ← Claude Code 适配
│   ├── codex.md          ← Codex CLI 适配
│   └── opencode.md       ← OpenCode 适配
├── codex-hooks/          ← Codex hook 事件配置
│   └── hooks.json
├── enhance/              ← 增强模式渲染器
├── hooks/                ← 平台 Hook 脚本
│   ├── claude-code/      ← Claude Code hooks (bash)
│   ├── codex/            ← Codex CLI hooks (bash)
│   └── opencode/         ← OpenCode 插件 (TypeScript)
├── pets/                 ← 宠物画像资源
└── state/                ← 状态管理规范
```