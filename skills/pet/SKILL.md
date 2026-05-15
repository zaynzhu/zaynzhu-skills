---
name: pet-buddy
description: CLI 编程伴侣宠物，提供有持久属性的小宠物，能对工作状态做出实时反应。
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
| 自然语言提及宠物 | 如"我的宠物怎么样了"、"喂一下小黑"、"跟宠物玩一下" |
| 首次使用 | 检测到无状态文件时自动触发初始化流程 |

---

## 主流程

### 1. 初始化检测

每次 skill 被触发时，首先读取状态文件：

```
读取 ~/.pet-buddy/state.json

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

状态文件路径：`~/.pet-buddy/state.json`

---

### 2. 首次初始化

当检测到无状态文件或用户确认重新初始化时，引导用户创建宠物：

```
显示欢迎信息：
"🐾 欢迎使用 Pet Buddy！我是你的 CLI 编程伴侣宠物。"

步骤 1 — 选择宠物类型：
"请选择你的宠物类型："
  1. 🐱 猫咪 — 独立优雅，偶尔撒娇
  2. 🐶 狗狗 — 忠诚热情，时刻陪伴

等待用户输入 → pet_type = "cat" | "dog"

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
  "createdAt": "ISO 时间戳",
  "lastUpdated": "ISO 时间戳"
}
```

保存状态文件后，显示欢迎消息：

```
🎉 {name} 来到了你身边！

  ╱╲
 ( •ω•)
  │ │
  Ｕ Ｕ

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

```
确定状态标签:
  if hunger >= 80:
    status = "hungry"     // 饥饿
  elif mood >= 80:
    status = "happy"      // 开心
  elif mood < 40:
    status = "sad"        // 难过
  elif mood >= 60:
    status = "curious"    // 好奇
  else:
    status = "idle"       // 普通

根据宠物类型和状态选择 ASCII 艺术:

猫咪 — hungry:
  ╱╲
 ( ｏωｏ)  "喵...好饿..."
  │  │
  Ｕ  Ｕ

猫咪 — happy:
  ╱╲
 ( ≖‿≖)  "喵呜~ 开心！"
  │ │
  Ｕ Ｕ

猫咪 — sad:
  ╱╲
 ( ｡•́︿•̀｡)  "喵..."
  │  │
  Ｕ  Ｕ

猫咪 — curious:
  ╱╲
 ( •̀ω•́)✧  "发现了什么？"
  │ │
  Ｕ Ｕ

猫咪 — idle:
  ╱╲
 ( •ω•)   "..."
  │ │
  Ｕ Ｕ

狗狗 — hungry:
  /^_^\
 ( ｏωｏ )  "汪...好饿..."
  │    │
  Ｕ    Ｕ

狗狗 — happy:
  /^_^\
 ( ≖‿≖ )  "汪汪！开心！"
  │ │
  Ｕ Ｕ

狗狗 — sad:
  /^_^\
 ( ｡•́︿•̀｡ )  "呜..."
  │    │
  Ｕ    Ｕ

狗狗 — curious:
  /^_^\
 ( •̀ω•́ )✧  "发现了什么？"
  │ │
  Ｕ Ｕ

狗狗 — idle:
  /^_^\
 ( •ω• )   "..."
  │ │
  Ｕ Ｕ
```

渲染输出格式（状态栏）：

```
{name} Lv.{level}  ❤️ 心情:{mood}  🍖 饥饿:{hunger}  🤝 好感:{bond}  ✨ {exp}/{level*100}
```

示例输出：

```
小黑 Lv.3  ❤️ 心情:75  🍖 饥饿:30  🤝 好感:60  ✨ 45/300

  ╱╲
 ( ≖‿≖)  "喵呜~ 开心！"
  │ │
  Ｕ Ｕ
```

---

### 5. 控制指令处理

| 指令 | 行为 |
|------|------|
| `/pet on` | 设置 `state.active = true`，保存，显示 `"{name} 醒来了！"` + 渲染宠物 |
| `/pet off` | 设置 `state.active = false`，保存，显示 `"{name} 去休息了...晚安 💤"` |
| `/pet status` | 显示完整状态信息（名字、类型、等级、所有属性数值、活跃状态、创建时间） |

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

  ╱╲
 ( •ω•)
  │ │
  Ｕ Ｕ
```

---

### 6. 互动指令处理

| 指令 | 效果 | 提示语模板 |
|------|------|-----------|
| `/pet feed` | hunger -30, mood +5, bond +3 | "{name} 吃得很开心！🍖" |
| `/pet play` | mood +10, bond +5, hunger +5 | "{name} 玩得很开心！🎾" |
| `/pet pet` | mood +3, bond +2 | "{name} 舒服地蹭了蹭你~ 🖐️" |

互动流程：

```
if 指令 == "feed":
  state.hunger = max(state.hunger - 30, 0)
  state.mood = min(state.mood + 5, 100)
  state.bond = min(state.bond + 3, 100)
  显示："{name} 吃得很开心！🍖"

if 指令 == "play":
  state.mood = min(state.mood + 10, 100)
  state.bond = min(state.bond + 5, 100)
  state.hunger = min(state.hunger + 5, 100)
  显示："{name} 玩得很开心！🎾"

if 指令 == "pet":
  state.mood = min(state.mood + 3, 100)
  state.bond = min(state.bond + 2, 100)
  显示："{name} 舒服地蹭了蹭你~ 🖐️"

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
| 状态文件路径不存在 | 自动创建 `~/.pet-buddy/` 目录 |
| 时间戳异常（未来时间） | 将 lastUpdated 重置为当前时间，忽略异常衰减 |
| 互动指令在宠物未激活时使用 | 提示 "请先使用 /pet on 激活宠物" |

---

## 状态文件规范

**路径**: `~/.pet-buddy/state.json`

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
| `lastUpdated` | string | ISO 8601 | 最后更新时间 |
| `createdAt` | string | ISO 8601 | 创建时间 |

**升级规则**: 当 `exp >= level * 100` 时升级，升级后 `exp -= level * 100`，`level += 1`。