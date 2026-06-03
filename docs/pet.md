# pet

CLI 编程伴侣宠物——有持久属性的小宠物，能对工作状态做出实时反应。

## 功能

- 持久状态（饥饿、心情、等级、羁绊等）
- 7 种宠物可选：猫/狗/仓鼠/兔子/鹦鹉/乌龟/鱼
- 进化系统：Lv.5 → 少年、Lv.15 → 成年、Lv.30 → 觉醒，外观自动进化
- 25 个成就（首次编码、百次命令、首次喂食、连续活跃天数等）
- 对工作状态实时反应（写代码、测试通过/失败、升级等）
- 互动指令：喂食、玩耍、抚摸、训练、特殊、睡觉/唤醒、装扮
- 装扮系统：hat/scarf/glasses/wings/halo，每种宠物有专属装扮描述
- 接食物小游戏（增强模式，Node.js）
- ASCII 画像常驻显示（ANSI 256-color），随状态和进化阶段变化
- 音效反馈（BEL 终端声音）
- 成就解锁动画通知
- 状态栏动态追加模式集成（不覆盖其他 statusLine）
- Hook 自动互动（PostToolUse 触发状态更新）
- **项目级开关**：项目根目录 `.pet.json` 控制启用/禁用
- **多平台支持**：Claude Code、Codex CLI、OpenCode

## 多平台支持

| 平台 | 集成方式 | 状态显示 |
|------|---------|---------|
| Claude Code | Bash hooks + settings.json statusLine | 状态栏持久显示 |
| Codex CLI | Plugin 打包（.codex-plugin/）或 Bash hooks + hooks.json | systemMessage 工具输出 |
| OpenCode | TypeScript 插件 + system prompt 注入 | 工具输出 + AI 自然提及 |

核心状态文件 `~/.pet/state.json` 跨平台共享。

## 宠物类型

| 宠物 | 图标 | 性格 | 唯一属性 |
|------|------|------|---------|
| 🐱 猫咪 | 🐱 | 傲娇、独立 | 独立性 😼 |
| 🐶 狗狗 | 🐶 | 忠诚、热情 | 忠诚度 🐕 |
| 🐹 仓鼠 | 🐹 | 圆滚滚、爱囤食 | 运动量 🏃 |
| 🐰 兔子 | 🐰 | 可爱、活泼 | 跳跃力 🦘 |
| 🦜 鹦鹉 | 🦜 | 聪明、话多 | 学习力 🧠 |
| 🐢 乌龟 | 🐢 | 慢悠悠、长寿 | 耐心 ⏳ |
| 🐟 鱼 | 🐟 | 安静、治愈 | 活力 💧 |

## 进化系统

- **Lv.5** → 少年期（进化阶段 1）
- **Lv.15** → 成年期（进化阶段 2）
- **Lv.30** → 觉醒期（进化阶段 3）

进化时外观自动变化，每种宠物在每个阶段有不同的 ASCII 画像和描述。

## 成就系统

25 个成就，涵盖编码、互动、属性、特殊事件四大类。解锁时显示动画通知。

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
| `/pet train` | 训练 | 训练宠物（消耗饱食度换经验和唯一属性） |
| `/pet special` | 特殊互动 | 触发宠物特殊反应 |
| `/pet sleep` | 睡觉 | 让宠物睡觉（降低饥饿增长速度） |
| `/pet wake` | 唤醒 | 唤醒睡觉中的宠物 |
| `/pet dress [item]` | 穿戴装扮 | hat/scarf/glasses/wings/halo/none |
| `/pet achievements` | 查看成就 | 显示成就列表和进度 |
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
│   └── pet-renderer.mjs
├── hooks/                ← 平台 Hook 脚本
│   ├── claude-code/      ← Claude Code hooks (bash)
│   │   ├── apply-decay.sh
│   │   ├── check-achievements.sh
│   │   ├── hook-bash-result.sh
│   │   ├── hook-code-success.sh
│   │   ├── status-combined.sh
│   │   └── status.sh
│   ├── codex/            ← Codex CLI hooks (bash)
│   │   ├── apply-decay.sh
│   │   ├── check-achievements.sh
│   │   ├── hook-bash-result.sh
│   │   └── hook-code-success.sh
│   └── opencode/         ← OpenCode 插件 (TypeScript)
│       └── pet-plugin.ts
├── pets/                 ← 宠物画像资源
│   ├── registry.json     ← 宠物类型注册表（7种）
│   ├── cat.md            ← 猫咪画像
│   ├── dog.md            ← 狗狗画像
│   ├── hamster.md        ← 仓鼠画像
│   ├── rabbit.md         ← 兔子画像
│   ├── parrot.md         ← 鹦鹉画像
│   ├── turtle.md         ← 乌龟画像
│   └── fish.md           ← 鱼画像
└── state/                ← 状态管理规范
    └── state-manager.md
```