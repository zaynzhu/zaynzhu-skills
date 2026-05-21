---
name: state-manager
description: Pet Buddy 状态管理规则，定义 JSON schema、读写逻辑和时间计算。
---

# State Manager

## 1. 状态文件位置

Path: `~/.pet-buddy/state.json`

## 2. JSON Schema

```json
{
  "name": "string - 宠物名字，用户自定义",
  "type": "string - 宠物类型：'cat' | 'dog'",
  "mood": "number - 心情，范围 0-100，初始 80",
  "hunger": "number - 饥饿度，范围 0-100，初始 20",
  "bond": "number - 好感度，范围 0-100，初始 50",
  "level": "number - 等级，范围 1-99，初始 1",
  "exp": "number - 经验值，>= 0，初始 0",
  "active": "boolean - 是否活跃，初始 true",
  "showAscii": "boolean - 是否常驻显示 ASCII 画像，初始 true",
  "frame": "number - 帧计数器，范围 0-999，初始 0，每次触发递增",
  "soundEnabled": "boolean - 是否启用音效，初始 false",
  "gameHighScore": "number - 接食物小游戏最高分，初始 0",
  "createdAt": "string - ISO 8601 创建时间",
  "lastUpdated": "string - ISO 8601 最后更新时间",
  "platform": "string - 运行平台：'claude-code' | 'codex' | 'opencode'，可选字段（向后兼容）"
}
```

NOTE: Use camelCase field names (createdAt, lastUpdated) NOT snake_case.

## 3. 初始状态模板

```json
{
  "name": "",
  "type": "",
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
  "createdAt": "",
  "lastUpdated": "",
  "platform": ""
}
```

// platform 可选字段，初始化时设置，留空表示 Claude Code（向后兼容）

## 4. 属性变化规则

### 心情 (mood)

| 事件 | 变化 | 说明 |
|------|------|------|
| 代码写入成功 | +5 | Edit/Write 工具成功 |
| 测试通过 | +10 | Bash 工具返回成功 |
| 编译/测试失败 | -3 | Bash 工具返回失败 |
| 喂食 | +5 | 互动指令 |
| 玩耍 | +10 | 互动指令 |
| 抚摸 | +3 | 互动指令 |

范围保护：`Math.max(0, Math.min(100, mood))`

### 饥饿度 (hunger)

| 事件 | 变化 | 说明 |
|------|------|------|
| 时间流逝 | +5/小时 | 基于 lastUpdated 计算 |
| 喂食 | -30 | 互动指令 |
| 玩耍 | +5 | 运动消耗 |

范围保护：`Math.max(0, Math.min(100, hunger))`

### 好感度 (bond)

| 事件 | 变化 | 说明 |
|------|------|------|
| 互动（喂食/玩耍/抚摸） | +2~5 | 各互动类型不同 |
| 时间流逝 | -1/天 | 长时间不互动 |
| 完成功能 | +5 | 成功的代码提交 |

范围保护：`Math.max(0, Math.min(100, bond))`

### 经验值 (exp)

| 事件 | 变化 | 说明 |
|------|------|------|
| 写代码 | +1 | Edit/Write 工具 |
| 测试通过 | +10 | Bash 工具成功 |
| 完成功能 | +20 | 重大里程碑 |

升级规则：升级所需经验 = `level * 100`，当 `exp >= level * 100` 时自动升级，升级后 `exp -= level * 100`，`level += 1`，最高等级 99

## 5. 时间流逝计算

```javascript
function applyTimePass(state) {
  const now = new Date();
  const lastUpdated = new Date(state.lastUpdated);

  // Edge case: future lastUpdated → ignore time passage, just update lastUpdated
  if (lastUpdated > now) {
    state.lastUpdated = now.toISOString();
    return state;
  }

  const diffMs = now - lastUpdated;
  const hoursPassed = Math.floor(diffMs / (1000 * 60 * 60));
  const daysPassed = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  // hunger increases over time
  state.hunger += Math.floor(hoursPassed * 5);
  state.hunger = Math.max(0, Math.min(100, state.hunger));

  // bond decreases over time
  state.bond -= Math.floor(daysPassed);
  state.bond = Math.max(0, Math.min(100, state.bond));

  state.lastUpdated = now.toISOString();
  return state;
}
```

## 6. 状态读取

```javascript
function loadState() {
  const filePath = path.join(os.homedir(), '.pet-buddy', 'state.json');

  if (!fs.existsSync(filePath)) {
    return null;
  }

  let data;
  try {
    data = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  } catch (e) {
    return { error: "invalid_json" };
  }

  const requiredFields = ['name', 'type', 'mood', 'hunger', 'bond', 'level', 'exp', 'active', 'showAscii', 'frame', 'soundEnabled', 'gameHighScore', 'createdAt', 'lastUpdated'];
  const missingFields = requiredFields.filter(field => !(field in data));

  if (missingFields.length > 0) {
    return { error: "missing_fields", fields: missingFields };
  }

  return data;
}
```

1. Reads `~/.pet-buddy/state.json`
2. Parses JSON
3. Validates required fields (name, type, mood, hunger, bond, level, exp, active, showAscii, frame, soundEnabled, gameHighScore, createdAt, lastUpdated)
4. Returns state object, or `null` if file doesn't exist, or `{ error: "invalid_json" }` if JSON invalid, or `{ error: "missing_fields", fields: [...] }` if fields missing

## 7. 状态保存（原子写入）

```javascript
function saveState(state) {
  const dir = path.join(os.homedir(), '.pet-buddy');
  const filePath = path.join(dir, 'state.json');
  const tmpPath = path.join(dir, 'state.json.tmp');
  const bakPath = path.join(dir, 'state.json.bak');

  // 1. Update lastUpdated to current ISO time
  state.lastUpdated = new Date().toISOString();

  // 2. Validate all attributes are in valid ranges (clamp)
  state.mood = Math.max(0, Math.min(100, state.mood));
  state.hunger = Math.max(0, Math.min(100, state.hunger));
  state.bond = Math.max(0, Math.min(100, state.bond));
  state.level = Math.max(1, Math.min(99, state.level));
  state.exp = Math.max(0, state.exp);

  // 3. Write to temp file
  fs.writeFileSync(tmpPath, JSON.stringify(state, null, 2), 'utf-8');

  // 4. Keep backup
  if (fs.existsSync(filePath)) {
    fs.copyFileSync(filePath, bakPath);
  }

  // 5. Rename to final (atomic on most filesystems)
  fs.renameSync(tmpPath, filePath);
}
```

1. Updates `lastUpdated` to current ISO time
2. Validates all attributes are in valid ranges (clamp)
3. Writes to temp file `~/.pet-buddy/state.json.tmp`
4. Renames to `~/.pet-buddy/state.json` (atomic)
5. Keeps backup `~/.pet-buddy/state.json.bak`

## 8. 状态验证

```javascript
function validateState(state) {
  const errors = [];

  // Required fields exist
  const requiredFields = ['name', 'type', 'mood', 'hunger', 'bond', 'level', 'exp', 'active', 'showAscii', 'frame', 'soundEnabled', 'gameHighScore', 'createdAt', 'lastUpdated'];
  for (const field of requiredFields) {
    if (!(field in state)) {
      errors.push(`Missing field: ${field}`);
    }
  }

  // name is non-empty string
  if ('name' in state && (typeof state.name !== 'string' || state.name.trim() === '')) {
    errors.push('name must be a non-empty string');
  }

  // type is 'cat' or 'dog'
  if ('type' in state && !['cat', 'dog'].includes(state.type)) {
    errors.push("type must be 'cat' or 'dog'");
  }

  // active is boolean
  if ('active' in state && typeof state.active !== 'boolean') {
    errors.push('active must be a boolean');
  }

  // soundEnabled is boolean
  if ('soundEnabled' in state && typeof state.soundEnabled !== 'boolean') {
    errors.push('soundEnabled must be a boolean');
  }

  // gameHighScore is non-negative number
  if ('gameHighScore' in state && (typeof state.gameHighScore !== 'number' || state.gameHighScore < 0)) {
    errors.push('gameHighScore must be a non-negative number');
  }

  // platform is optional, but if present must be valid
  if ('platform' in state && !['claude-code', 'codex', 'opencode'].includes(state.platform)) {
    errors.push("platform must be 'claude-code', 'codex', or 'opencode'");
  }

  return errors;
}
```

- Required fields exist
- `name` is non-empty string
- `type` is `'cat'` or `'dog'`
- `active` is boolean
- `soundEnabled` is boolean
- `gameHighScore` is non-negative number
- `platform` is optional; if present, must be 'claude-code', 'codex', or 'opencode'

## 9. 升级检查

```javascript
function checkLevelUp(state) {
  const messages = [];

  while (state.exp >= state.level * 100 && state.level < 99) {
    const expNeeded = state.level * 100;
    state.exp -= expNeeded;
    state.level += 1;

    // 升级时恢复部分状态
    state.mood = Math.min(state.mood + 20, 100);
    state.hunger = Math.max(state.hunger - 10, 0);

    messages.push(`🎉 恭喜！${state.name} 升级到了 Lv.${state.level}！`);
  }

  return { state, messages };
}
```

Loops while `exp >= level * 100` and `level < 99`. On each iteration: `exp -= level * 100`, then `level += 1`. Level-up also restores mood (+20, max 100) and reduces hunger (-10, min 0). Returns updated state and level-up messages.