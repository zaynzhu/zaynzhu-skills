---
name: pet
description: CLI 编程伴侣宠物，提供有持久属性的小宠物，能对工作状态做出实时反应。
compatibility: claude-code, codex, opencode
triggers:
  - /pet
  - 宠物
  - pet buddy
  - 小黑
  - 小黄
  - 小白
  - 小花
  - 小橘
  - 喵
  - 汪
  - 关闭宠物
  - 开启宠物
  - 宠物关掉
  - 宠物打开
  - 不要宠物
  - pet off
  - pet on
---

# Pet Buddy — CLI 编程伴侣宠物

## 触发条件

Skill 在以下情况下激活：

| 触发方式 | 说明 |
|---------|------|
| `/pet on` | 激活宠物伴侣，开始追踪工作状态 |
| `/pet off` | 停用宠物伴侣 |
| `/pet status` | 查看宠物完整状态信息 |
| `/pet feed` | 喂食宠物 |
| `/pet play` | 和宠物玩耍 |
| `/pet pet` | 抚摸宠物 |
| `/pet ascii on` | 开启 ASCII 画像常驻显示（每次 AI 回复都带宠物画像） |
| `/pet ascii off` | 关闭 ASCII 画像常驻显示（仅状态栏显示） |
| `/pet sound on` | 开启音效（BEL 终端声音） |
| `/pet sound off` | 关闭音效 |
| `/pet play` | 和宠物玩耍（增强模式下启动接食物小游戏） |
| 自然语言提及宠物 | 如"我的宠物怎么样了"、"喂一下小黑"、"跟宠物玩一下" |
| 首次使用 | 检测到无状态文件时自动触发初始化流程 |

---

## 平台检测

Pet Buddy 支持三个平台：Claude Code、Codex CLI 和 OpenCode。

检测当前平台的方法：

1. 检查环境：
   - 如果在 Claude Code 中运行 → `platform: "claude-code"`
   - 如果在 Codex CLI 中运行 → `platform: "codex"`
   - 如果在 OpenCode 中运行 → `platform: "opencode"`
2. 自动检测启发式：
   - Claude Code：`~/.claude/` 目录存在，或 CLAUDE_CODE 环境变量
   - Codex：`~/.codex/` 目录存在，或 CODEX_HOME 环境变量
   - OpenCode：`~/.config/opencode/` 目录存在，或 OPENCODE_CONFIG 环境变量
3. 如果不确定，询问用户选择

在 `state.json` 中记录 `platform` 字段。对于已有的 Claude Code 状态文件，此字段可选（向后兼容）。

## 各平台初始化

创建 `state.json` 后，根据平台部署对应的 hooks：

- **Claude Code**：遵循 adapters/claude-code.md → 部署 bash hooks 到 ~/.pet/，配置 settings.local.json
- **Codex CLI**：遵循 adapters/codex.md → 部署 bash hooks 到 ~/.pet/，配置 config.toml
- **OpenCode**：遵循 adapters/opencode.md → 部署 TS 插件到 .opencode/plugins/，无需额外配置

### 无 statusLine 平台的状态展示

Codex CLI 和 OpenCode 没有 statusLine 功能。在这些平台上：

- 宠物状态通过 hook/plugin 返回的 `systemMessage` 展示
- 每次工具执行后，hook 输出包含宠物反应和状态信息
- 用户可以通过 `/pet` 或 `/pet status` 手动查看完整状态

示例 systemMessage 输出：
```
🐱 mia 开心地摇着尾巴~ [Lv.6 ❤️100 🍖40 🤝67 ✨343/600]
```

---

## 主流程

### 1. 初始化检测

每次 skill 被触发时，首先检查是否为纯开关指令（`/pet on`、`/pet off`、"关闭宠物"、"开启宠物"等）。如果是，直接操作 `.pet.json` 配置文件，不读取全局状态，不触发初始化流程。

否则，读取状态文件：

```
读取 ~/.pet/state.json

if 文件存在:
  尝试解析 JSON
  if 解析成功:
    继续后续流程
  else (JSON 格式损坏):
    提示用户："状态文件似乎损坏了，是否重新初始化？(y/n)"
    if 用户确认:
      进入首次初始化流程
    else:
      退出，提示手动修复
elif 文件不存在:
  进入首次初始化流程
```

状态文件路径：`~/.pet/state.json`

---

### 1.5 增强模式检测

每次 skill 触发时，检测增强模式可用性：

```
增强模式条件（全部满足）：
  1. node 命令可用（command -v node 成功）
  2. ~/.pet/pet-renderer.mjs 存在

if 增强模式可用:
  enhanceMode = true
  渲染输出使用 ANSI 256-color 着色
  音效系统可用
  接食物小游戏可用
else:
  enhanceMode = false
  使用纯文本 Bash 回退渲染
  音效和小游戏不可用
```

增强模式提供：
- **ANSI 彩色渲染**：宠物 ASCII 画像是彩色的（猫=橙色系，狗=棕色系）
- **音效**：成功/失败/升级时播放 BEL 终端声音
- **接食物小游戏**：`/pet play` 启动交互式小游戏

---

### 2. 首次初始化

当检测到无状态文件或用户确认重新初始化时，引导用户创建宠物：

```
显示欢迎信息：
"🐾 欢迎使用 Pet Buddy！我是你的 CLI 编程伴侣宠物。"

步骤 1 — 选择宠物类型：
"请选择你的宠物类型："

从 pets/registry.json 读取所有类型，动态生成选项列表：
  1. {icon} {name} — {personality}
  2. {icon} {name} — {personality}
  ...
（当前可用：猫咪🐱、狗狗🐶、仓鼠🐹）

等待用户输入 → pet_type = registry 中对应的 key

步骤 2 — 为宠物命名：
"给你的宠物起个名字吧！（直接输入名字，或按回车使用默认名）"

if 用户输入为空:
  if pet_type == "cat":
    name = "小黑"
  else:
    name = "小黄"

步骤 3 — 创建初始状态：
```

初始状态结构：

```json
{
  "name": "用户输入的名字",
  "type": "cat 或 dog",
  "mood": 80,
  "hunger": 20,
  "bond": 50,
  "level": 1,
  "exp": 0,
  "active": true,
  "showAscii": true,
  "frame": 0,
  "soundEnabled": false,
  "gameHighScore": 0,
  "createdAt": "ISO 时间戳",
  "lastUpdated": "ISO 时间戳"
}
```

保存状态文件后，显示欢迎消息：

```
🎉 {name} 来到了你身边！

   /\_/\
  ( •ω• )
   >   <

{name} 现在是你的编程伙伴了！
当你写代码时，{name} 会陪伴你、为你加油。
使用 /pet feed 喂食、/pet play 玩耍、/pet pet 抚摸。
```

---

### 3. 状态更新阶段

每次 skill 触发时（非控制指令），执行状态更新：

```
加载 state.json

if state.active == false:
  显示："{name} 正在休息中... 使用 /pet on 唤醒。"
  退出

计算时间流逝:
  now = 当前时间
  // 注意：JavaScript Date 差值为毫秒，需除以 3600000 转小时，86400000 转天
  elapsed_hours = (now - lastUpdated) / 3600000 (毫秒转小时)
  elapsed_days = (now - lastUpdated) / 86400000 (毫秒转天)

时间衰减规则:
  state.hunger += 5 * elapsed_hours     // 饥饿度每小时 +5
  state.bond -= 1 * elapsed_days         // 好感度每天 -1（最低为 0）

根据触发指令更新属性:
  // 具体数值见"互动指令处理"和"工作状态反应"

属性值范围约束（clamp）:
  state.hunger = clamp(state.hunger, 0, 100)
  state.mood = clamp(state.mood, 0, 100)
  state.bond = clamp(state.bond, 0, 100)
  state.exp = max(state.exp, 0)

升级检测:
  while state.exp >= state.level * 100 and state.level < 99:
    expNeeded = state.level * 100
    state.exp -= expNeeded
    state.level += 1
    显示升级消息：
    "🎉 {name} 升级了！现在 Lv.{state.level}！"
    // 升级时恢复部分状态
    state.mood = min(state.mood + 20, 100)
    state.hunger = max(state.hunger - 10, 0)

保存 state.json
```

---

### 4. 渲染阶段

根据宠物当前状态，决定显示内容和 ASCII 艺术：

**增强模式渲染**：当 `enhanceMode == true` 时，使用 `node ~/.pet/pet-renderer.mjs --mode=render --pet={type} --state={stateLabel} --frame={frame}` 输出带 ANSI 256-color 的彩色 ASCII 画像。猫为橙色系（primary:208, secondary:202），狗为棕色系（primary:130, secondary:95）。彩色输出仅在支持 ANSI 的终端中可见。

**Bash 回退渲染**：当增强模式不可用时，使用纯文本 ASCII 画像，`sed 's/\[[0-9]*\]//g'` 剥离颜色标记。

**常驻显示规则**：当 `state.showAscii == true` 且 `state.active == true` 时，AI 的**每次回复**末尾都必须附带宠物 ASCII 画像 + 状态栏。当 `showAscii == false` 时，仅在主动互动（feed/play/pet）或状态查询时显示画像，日常回复不带。

#### 4.1 状态优先级

```
1. eating    — 互动中（正在吃东西）
2. playing   — 互动中（正在玩耍）
3. petting   — 互动中（正在被抚摸）
4. hungry    — hunger >= 80
5. angry     — hunger >= 90 && mood < 30
6. excited   — mood >= 90
7. happy     — mood >= 80
8. sleepy    — 长时间闲置 > 30min
9. curious   — mood >= 60
10. sad      — mood < 40
11. confused — 不识别的指令
12. idle     — 默认
```

#### 4.2 帧选择与描述随机化

每种状态的 ASCII 画像有 2-3 帧，描述文字有 2-4 个变体。根据 `state.frame` 计数器选择：

```
frame = state.frame
selectedFrame = frames[frame % len(frames)]
selectedDesc = descriptions[frame % len(descriptions)]
selectedEmoji = emojis[frame % len(emojis)]
```

帧计数器递增时机：
- 每次 statusLine 刷新（status-combined.sh）
- 每次 hook 触发（hook-code-success.sh、hook-bash-result.sh）
- 每次时间衰减（apply-decay.sh）
- 状态变化时：重置为 0（新状态从第一帧开始）

frame 范围：0-999，递增后取模 `frame = (frame + 1) % 1000`

#### 4.3 状态栏格式

```
{icon} {name} Lv.{level} {emoji} | ❤️{mood} 🍖{hunger} 🤝{bond} ✨{exp}/{level*100} {description}
```

增强模式下各属性有独立 ANSI 256-color 颜色：

| 属性 | 颜色 | ANSI 码 |
|------|------|---------|
| icon | 猫=橙色 208，狗=棕色 130 | `38;5;208` / `38;5;130` |
| Lv.{level} | 绿色 | `38;5;82` |
| ❤️{mood} | 粉红 | `38;5;199` |
| 🍖{hunger} | 橙色 | `38;5;208` |
| 🤝{bond} | 蓝色 | `38;5;75` |
| ✨{exp}/{threshold} | 黄色 | `38;5;226` |

其中：
- `icon`: 猫=🐱，狗=🐶
- `emoji`: 从状态对应的 emoji 循环中选择
- `description`: 从状态对应的描述变体中选择

示例：
```
帧0: 🐱 mia Lv.3 😊 | ❤️85 🍖35 🤝63 ✨66/100
帧1: 🐱 mia Lv.3 😸 | ❤️85 🍖35 🤝63 ✨66/100 舔了舔爪子
帧2: 🐱 mia Lv.3 😻 | ❤️85 🍖35 🤝63 ✨66/100 伸了个懒腰
```

#### 4.4 ASCII 画像选择

根据 `(petType, stateLabel, frame)` 选择具体帧。详见 `pets/cat.md` 和 `pets/dog.md` 中的多帧定义。

示例（猫咪 happy）：
```
帧0:   /\_/\ ( ≖‿≖ )  喵呜~   > ^ <
帧1:   /\_/\ ( ≖‿≖ )  喵呜~   > ~ <   ← 尾巴摆动
帧2:   /\_/\ ( -‿- )  喵~   > ^ <   ← 眨眼
```

---

### 5. 控制指令处理

| 指令 | 自然语言 | 行为 |
|------|---------|------|
| `/pet on` | "开启宠物"、"宠物打开"、"要宠物" | 在当前项目根目录写入 `.pet.json {"enabled": true}`，显示 `"{name} 在这个项目中激活了！"` + 渲染宠物 |
| `/pet off` | "关闭宠物"、"宠物关掉"、"不要宠物" | 在当前项目根目录写入 `.pet.json {"enabled": false}`，显示 `"{name} 在这个项目中去休息了... 💤"` |
| `/pet status` | "宠物状态"、"宠物怎么样了" | 显示完整状态信息 + 当前项目开关状态 |
| `/pet special` | 专属互动（仓鼠=跑转轮，猫=独立散步，狗=叼飞盘） | unique +25, mood +5, bond +2 |

**实现细节**：`/pet on` 和 `/pet off` 操作的是当前工作目录（项目根目录）下的 `.pet.json` 文件，不是全局 `state.json` 的 `active` 字段。宠物数据仍然是全局共享的。

```
/pet off  → cwd/.pet.json = {"enabled": false}
/pet on   → cwd/.pet.json = {"enabled": true}
```

**项目级开关机制**：hooks 和 statusLine 在运行时从 `$PWD` 往上查找 `.pet.json` 文件。如果找到且 `enabled: false`，则跳过所有宠物相关逻辑（不更新状态、不输出消息、statusLine 不显示宠物）。默认 `enabled: true`（无文件或文件中无 enabled 字段时）。

`/pet ascii` 指令：

| 指令 | 行为 |
|------|------|
| `/pet ascii on` | 设置 `state.showAscii = true`，保存，显示 `"ASCII 画像已开启 🎨"` + 渲染宠物 |
| `/pet ascii off` | 设置 `state.showAscii = false`，保存，显示 `"ASCII 画像已关闭，宠物仍会出现在状态栏"` |

`/pet sound` 指令（需要增强模式）：

| 指令 | 行为 |
|------|------|
| `/pet sound on` | 设置 `state.soundEnabled = true`，保存，播放一声 BEL 确认音效已开启 |
| `/pet sound off` | 设置 `state.soundEnabled = false`，保存，显示 `"音效已关闭 🔇"` |

音效事件映射：
- 代码成功 / 测试通过 → `success` / `testPass`（1-2 声 BEL）
- 测试失败 → `testFail`（1 声 BEL）
- 升级 → `levelUp`（3 声 BEL）
- 互动 → `interact`（1 声 BEL）

音效通过 `node ~/.pet/pet-renderer.mjs --mode=sound --event={type}` 播放，仅在 `soundEnabled == true` 且终端为 TTY 时生效。

`/pet status` 完整输出示例：

```
📊 {name} 的状态报告

  名字: {name}
  类型: {type == "cat" ? "猫咪 🐱" : "狗狗 🐶"}
  等级: Lv.{level}
  ❤️ 心情: {mood}/100
  🍖 饥饿: {hunger}/100
  🤝 好感度: {bond}/100
  ✨ 经验: {exp}/{level * 100}
  📅 陪伴天数: {(now - createdAt) / 86400} 天
  🟢 状态: 活跃中

   /\_/\
  ( •ω• )
   >   <
```

---

### 6. 互动指令处理

| 指令 | 效果 | 提示语模板 |
|------|------|-----------|
| `/pet feed` | hunger -30, mood +5, bond +3 | "{name} 吃得很开心！🍖" |
| `/pet play` | mood +10, bond +5, hunger +5 | "{name} 玩得很开心！🎾" |
| `/pet pet` | mood +3, bond +2 | "{name} 舒服地蹭了蹭你~ 🖐️" |
| `/pet special` | unique +25, mood +5, bond +2 | "{name} {type-specific action}！{type-specific emoji}" |

互动流程：

```
if 指令 == "feed":
  state.hunger = max(state.hunger - 30, 0)
  state.mood = min(state.mood + 5, 100)
  state.bond = min(state.bond + 3, 100)
  显示："{name} 吃得很开心！🍖"

if 指令 == "play":
  if enhanceMode && stdin.isTTY:
    // 增强模式：启动接食物小游戏
    运行：node ~/.pet/pet-renderer.mjs --mode=game
    游戏结束后自动更新 state.json（mood/hunger/exp/bond/gameHighScore）
    显示游戏结果
  else:
    // 标准模式：简单互动
    state.mood = min(state.mood + 10, 100)
    state.bond = min(state.bond + 5, 100)
    state.hunger = min(state.hunger + 5, 100)
    显示："{name} 玩得很开心！🎾"

if 指令 == "pet":
  state.mood = min(state.mood + 3, 100)
  state.bond = min(state.bond + 2, 100)
  显示："{name} 舒服地蹭了蹭你~ 🖐️"

if 指令 == "special":
  state.unique = min(state.unique + 25, 100)   // unique 字段名因宠物类型而异
  state.mood = min(state.mood + 5, 100)
  state.bond = min(state.bond + 2, 100)
  type-specific 行为：
    hamster: "{name} 在转轮上跑得飞快！🐹"
    cat:     "{name} 独自去探险了一圈回来了！😼"
    dog:     "{name} 兴奋地叼着飞盘跑回来！🐶"

// 互动后执行完整的渲染阶段输出
```

---

### 7. 工作状态反应

宠物能够感知编程工作状态，并做出相应反应：

| 工作事件 | 属性变化 | 宠物反应 |
|---------|---------|---------|
| 代码编写/提交成功 | mood +5, exp +1 | "{name} 看着你写代码，眼神充满期待~" |
| 测试通过 | exp +10, mood +5 | "{name} 高兴地摇了摇尾巴！测试全通过了！🎉" |
| 测试失败 | mood -3 | "{name} 安静地陪在你身边...别灰心！💪" |

工作状态反应触发方式：

```
当检测到以下自然语言或事件时触发：
  - 用户说"写完了"、"提交了"、"完成了代码" → 代码编写成功
  - 用户说"测试通过了"、"全绿了" → 测试通过
  - 用户说"测试失败了"、"有个 bug"、"测试报错了" → 测试失败
  - CI/构建成功的通知 → 代码编写成功
  - CI/构建失败的通知 → 测试失败

触发后：
  1. 检查宠物是否处于活跃状态（active == true），非活跃时不触发反应
  2. 执行状态更新（含时间衰减）
  3. 应用对应属性变化
  4. 显示宠物反应 + 状态栏
```

---

## 错误处理

| 异常情况 | 处理方式 |
|---------|---------|
| 状态文件缺失 | 自动进入首次初始化流程 |
| JSON 解析失败 | 提示用户确认是否重新初始化，确认后走初始化流程 |
| 属性值超出范围 | 自动 clamp 到合法范围（0-100），无需用户干预 |
| 未知宠物类型 | 默认使用 "cat"（猫咪），提示用户类型已重置 |
| 状态文件路径不存在 | 自动创建 `~/.pet/` 目录 |
| 时间戳异常（未来时间） | 将 lastUpdated 重置为当前时间，忽略异常衰减 |
| 互动指令在宠物未激活时使用 | 提示 "请先使用 /pet on 激活宠物" |

---

## 状态文件规范

**路径**: `~/.pet/state.json`

**字段定义**:

| 字段 | 类型 | 范围 | 说明 |
|------|------|------|------|
| `name` | string | - | 宠物名字 |
| `type` | string | "cat" / "dog" | 宠物类型 |
| `hunger` | number | 0-100 | 饥饿度，0=饱，100=极饿 |
| `mood` | number | 0-100 | 心情值，越高越好 |
| `bond` | number | 0-100 | 亲密度，越高越好 |
| `exp` | number | 0+ | 经验值 |
| `level` | number | 1+ | 等级 |
| `active` | boolean | - | 是否活跃 |
| `showAscii` | boolean | - | 是否在 AI 回复中常驻显示 ASCII 画像 |
| `frame` | number | 0-999 | 帧计数器，用于动画帧和描述循环选择 |
| `soundEnabled` | boolean | - | 是否启用音效（BEL 终端声音） |
| `gameHighScore` | number | 0+ | 接食物小游戏最高分 |
| `lastUpdated` | string | ISO 8601 | 最后更新时间 |
| `platform` | string | "claude-code" / "codex" / "opencode" | 运行平台标识（可选，向后兼容） |
| `createdAt` | string | ISO 8601 | 创建时间 |

**升级规则**: 当 `exp >= level * 100` 时升级，升级后 `exp -= level * 100`，`level += 1`。