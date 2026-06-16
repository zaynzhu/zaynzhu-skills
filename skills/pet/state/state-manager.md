---
name: state-manager
description: Pet Buddy 状态管理规则，定义 JSON schema、读写逻辑和时间计算。
---

# State Manager

## 1. 状态文件位置

Path: `~/.pet/state.json`

## 2. JSON Schema

```json
{
  "name": "string - 宠物名字，用户自定义",
  "type": "string - 宠物类型：'cat' | 'dog' | 'hamster' | 'rabbit' | 'parrot' | 'turtle' | 'fish'",
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
  "platform": "string - 运行平台：'claude-code' | 'codex' | 'opencode'，可选字段（向后兼容）",
  "unique": "object - 独特属性，键名由宠物类型决定。仓鼠: {exercise: 50}, 猫: {independence: 70}, 狗: {loyalty: 60}。向后兼容：旧状态文件无此字段时自动补全",
  "evolution": "number - 进化阶段：0=基础, 1=少年, 2=成年, 3=觉醒。默认 0，向后兼容",
  "sleeping": "boolean - 是否在睡眠中，默认 false，向后兼容",
  "sleepStartedAt": "string - ISO 8601 睡眠开始时间，null 表示未睡眠",
  "outfit": "string - 当前装扮物品：'hat' | 'scarf' | 'glasses' | 'wings' | 'halo' | null。默认 null，向后兼容",
  "counters": "object - 累计计数器，向后兼容：无此字段时自动初始化",
  "achievements": "array - 已解锁的成就列表，每项包含 id 和 unlockedAt，向后兼容：无此字段时初始化为空数组"
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
  "platform": "",
  "unique": {}
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
| 训练 | +3 | 互动指令 |

范围保护：`Math.max(0, Math.min(100, mood))`

### 饥饿度 (hunger)

| 事件 | 变化 | 说明 |
|------|------|------|
| 时间流逝 | +5/小时 | 基于 lastUpdated 计算 |
| 喂食 | -30 | 互动指令 |
| 玩耍 | +5 | 运动消耗 |
| 训练 | -20 | 互动指令 |

范围保护：`Math.max(0, Math.min(100, hunger))`

### 好感度 (bond)

| 事件 | 变化 | 说明 |
|------|------|------|
| 互动（喂食/玩耍/抚摸） | +2~5 | 各互动类型不同 |
| 训练 | +2 | 互动指令 |
| 时间流逝 | -1/天 | 长时间不互动 |
| 完成功能 | +5 | 成功的代码提交 |

范围保护：`Math.max(0, Math.min(100, bond))`

### 经验值 (exp)

| 事件 | 变化 | 说明 |
|------|------|------|
| 写代码 | +1 | Edit/Write 工具 |
| 测试通过 | +10 | Bash 工具成功 |
| 完成功能 | +20 | 重大里程碑 |
| 训练 | +15 | 互动指令 |

升级规则：升级所需经验 = `level * 100`，当 `exp >= level * 100` 时自动升级，升级后 `exp -= level * 100`，`level += 1`，最高等级 99

### 独特属性 (unique)

| 事件 | 变化 | 说明 |
|------|------|------|
| 训练 | unique +10 | 训练提升宠物独特属性 |

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
  const filePath = path.join(os.homedir(), '.pet', 'state.json');

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

1. Reads `~/.pet/state.json`
2. Parses JSON
3. Validates required fields (name, type, mood, hunger, bond, level, exp, active, showAscii, frame, soundEnabled, gameHighScore, createdAt, lastUpdated)
4. Returns state object, or `null` if file doesn't exist, or `{ error: "invalid_json" }` if JSON invalid, or `{ error: "missing_fields", fields: [...] }` if fields missing

## 7. 状态保存（原子写入）

```javascript
function saveState(state) {
  const dir = path.join(os.homedir(), '.pet');
  const filePath = path.join(dir, 'state.json');
  const tmpPath = path.join(dir, 'state.json.tmp');
  const bakPath = path.join(dir, 'state.json.bak');
  const lockPath = path.join(dir, '.state.lock');

  // 1. Update lastUpdated to current ISO time
  state.lastUpdated = new Date().toISOString();

  // 2. Validate all attributes are in valid ranges (clamp)
  state.mood = Math.max(0, Math.min(100, state.mood));
  state.hunger = Math.max(0, Math.min(100, state.hunger));
  state.bond = Math.max(0, Math.min(100, state.bond));
  state.level = Math.max(1, Math.min(99, state.level));
  state.exp = Math.max(0, state.exp);
  state.evolution = Math.max(0, Math.min(3, state.evolution || 0));
  if (state.sleeping === undefined) state.sleeping = false;
  if (state.sleepStartedAt === undefined) state.sleepStartedAt = null;
  if (state.outfit === undefined) state.outfit = null;
  if (state.counters === undefined) {
    state.counters = {
      codeWrites: 0, bashSuccesses: 0, testFails: 0, features: 0,
      feeds: 0, plays: 0, pets: 0, trains: 0, specials: 0,
      sleeps: 0, wakes: 0, dresses: 0, dressItems: [],
      petTypes: [],
      gamesPlayed: 0, maxBond: 50, maxLevel: 1, maxUnique: 0,
      consecutiveDays: 0, lastActiveDate: null
    };
  }
  if (state.achievements === undefined) state.achievements = [];

  // 3. Acquire mkdir-based cross-process lock
  acquireLock(lockPath);
  try {
    // 4. Write to temp file
    fs.writeFileSync(tmpPath, JSON.stringify(state, null, 2), 'utf-8');

    // 5. Keep backup
    if (fs.existsSync(filePath)) {
      fs.copyFileSync(filePath, bakPath);
    }

    // 6. Rename to final (atomic on most filesystems)
    fs.renameSync(tmpPath, filePath);
  } finally {
    releaseLock(lockPath);
  }
}
```

1. Updates `lastUpdated` to current ISO time
2. Validates all attributes are in valid ranges (clamp)
3. Acquires mkdir-based cross-process lock `~/.pet/.state.lock`
4. Writes to temp file `~/.pet/state.json.tmp`
5. Renames to `~/.pet/state.json` (atomic)
6. Keeps backup `~/.pet/state.json.bak`
7. Releases the lock in `finally`

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

  // type is one of the registered pet types
  if ('type' in state && !['cat', 'dog', 'hamster', 'rabbit', 'parrot', 'turtle', 'fish'].includes(state.type)) {
    errors.push("type must be 'cat', 'dog', 'hamster', 'rabbit', 'parrot', 'turtle', or 'fish'");
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

  // unique is optional object
  if ('unique' in state && (typeof state.unique !== 'object' || state.unique === null || Array.isArray(state.unique))) {
    errors.push('unique must be an object');
  }

  // evolution is optional, but if present must be 0-3
  if ('evolution' in state && (typeof state.evolution !== 'number' || state.evolution < 0 || state.evolution > 3)) {
    errors.push('evolution must be a number between 0 and 3');
  }

  // sleeping is optional boolean
  if ('sleeping' in state && typeof state.sleeping !== 'boolean') {
    errors.push('sleeping must be a boolean');
  }
  // sleepStartedAt is optional string or null
  if ('sleepStartedAt' in state && state.sleepStartedAt !== null && typeof state.sleepStartedAt !== 'string') {
    errors.push('sleepStartedAt must be a string or null');
  }

  // outfit is optional, but if present must be valid
  if ('outfit' in state && state.outfit !== null && !['hat', 'scarf', 'glasses', 'wings', 'halo'].includes(state.outfit)) {
    errors.push("outfit must be 'hat', 'scarf', 'glasses', 'wings', 'halo', or null");
  }

  // counters is optional object
  if ('counters' in state && (typeof state.counters !== 'object' || state.counters === null || Array.isArray(state.counters))) {
    errors.push('counters must be an object');
  }
  // achievements is optional array
  if ('achievements' in state && !Array.isArray(state.achievements)) {
    errors.push('achievements must be an array');
  }

  return errors;
}
```

- Required fields exist
- `name` is non-empty string
- `type` is `'cat'`, `'dog'`, `'hamster'`, `'rabbit'`, `'parrot'`, `'turtle'`, or `'fish'`
- `active` is boolean
- `soundEnabled` is boolean
- `gameHighScore` is non-negative number
- `platform` is optional; if present, must be 'claude-code', 'codex', or 'opencode'
- `unique` is optional object; if present, must be a plain object (not array or null)
- `evolution` is optional; if present, must be number 0-3
- `sleeping` is optional; if present, must be boolean
- `sleepStartedAt` is optional; if present, must be string or null
- `outfit` is optional; if present, must be 'hat', 'scarf', 'glasses', 'wings', 'halo', or null
- `counters` is optional; if present, must be a plain object
- `achievements` is optional; if present, must be an array

**Backward Compatibility**: If `unique` is missing from state.json, it will be auto-populated based on the pet's `type` field using `registry.json` defaults. This ensures old state files work without manual migration.

## 9. 升级检查

```javascript
const EVOLUTION_LEVELS = [5, 15, 30]; // 少年/成年/觉醒
const EVOLUTION_NAMES = ['基础', '少年', '成年', '觉醒'];

function getEvolutionForLevel(level) {
  let stage = 0;
  for (let i = 0; i < EVOLUTION_LEVELS.length; i++) {
    if (level >= EVOLUTION_LEVELS[i]) stage = i + 1;
  }
  return stage;
}

function checkLevelUp(state) {
  const messages = [];
  const oldEvolution = state.evolution || 0;

  while (state.exp >= state.level * 100 && state.level < 99) {
    const expNeeded = state.level * 100;
    state.exp -= expNeeded;
    state.level += 1;

    // 升级时恢复部分状态
    state.mood = Math.min(state.mood + 20, 100);
    state.hunger = Math.max(state.hunger - 10, 0);

    messages.push(`🎉 恭喜！${state.name} 升级到了 Lv.${state.level}！`);
  }

  // 检查进化阶段跨越
  const newEvolution = getEvolutionForLevel(state.level);
  if (newEvolution > oldEvolution) {
    state.evolution = newEvolution;
    const oldName = EVOLUTION_NAMES[oldEvolution];
    const newName = EVOLUTION_NAMES[newEvolution];
    messages.push(`🌟 ${state.name} 进化了！${oldName} → ${newName}`);
    messages.push(`✨ 外观已更新！`);
  } else {
    state.evolution = newEvolution;
  }

  return { state, messages };
}
```

Loops while `exp >= level * 100` and `level < 99`. On each iteration: `exp -= level * 100`, then `level += 1`. Level-up also restores mood (+20, max 100) and reduces hunger (-10, min 0). After leveling, checks if the new level crosses an evolution threshold (5/15/30). If so, updates `state.evolution` and emits evolution messages. Returns updated state and level-up messages.

## 10. 计数器与成就

```javascript
function incrementCounter(state, counterName) {
  if (!state.counters) return;
  if (typeof state.counters[counterName] === 'number') {
    state.counters[counterName]++;
  }
}

function updateMaxStats(state) {
  if (!state.counters) return;
  if (state.bond > (state.counters.maxBond || 0)) state.counters.maxBond = state.bond;
  if (state.level > (state.counters.maxLevel || 0)) state.counters.maxLevel = state.level;
  const uniqueValues = state.unique ? Object.values(state.unique) : [0];
  const maxUnique = Math.max(...uniqueValues);
  if (maxUnique > (state.counters.maxUnique || 0)) state.counters.maxUnique = maxUnique;
}

function updateStreak(state) {
  if (!state.counters) return;
  const today = new Date().toISOString().split('T')[0];
  if (state.counters.lastActiveDate === today) return;

  const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];
  if (state.counters.lastActiveDate === yesterday) {
    state.counters.consecutiveDays++;
  } else {
    state.counters.consecutiveDays = 1;
  }
  state.counters.lastActiveDate = today;
}
```

```javascript
function checkAchievements(state) {
  if (!state.counters || !state.achievements) return [];
  const newAchievements = [];
  const c = state.counters;
  const unlocked = new Set(state.achievements.map(a => a.id));

  const checks = [
    { id: 'first_code', cond: c.codeWrites >= 1 },
    { id: 'code_100', cond: c.codeWrites >= 100 },
    { id: 'code_1000', cond: c.codeWrites >= 1000 },
    { id: 'code_10000', cond: c.codeWrites >= 10000 },
    { id: 'test_pass_100', cond: c.bashSuccesses >= 100 },
    { id: 'feature_10', cond: c.features >= 10 },
    { id: 'first_feed', cond: c.feeds >= 1 },
    { id: 'feed_100', cond: c.feeds >= 100 },
    { id: 'play_100', cond: c.plays >= 100 },
    { id: 'train_50', cond: c.trains >= 50 },
    { id: 'streak_7', cond: c.consecutiveDays >= 7 },
    { id: 'streak_30', cond: c.consecutiveDays >= 30 },
    { id: 'streak_365', cond: c.consecutiveDays >= 365 },
    { id: 'level_10', cond: c.maxLevel >= 10 },
    { id: 'level_30', cond: c.maxLevel >= 30 },
    { id: 'level_50', cond: c.maxLevel >= 50 },
    { id: 'level_99', cond: c.maxLevel >= 99 },
    { id: 'evolution_max', cond: (state.evolution || 0) >= 3 },
    { id: 'bond_100', cond: c.maxBond >= 100 },
    { id: 'first_dress', cond: c.dresses >= 1 },
    { id: 'dress_all', cond: Array.isArray(c.dressItems) && c.dressItems.length >= 5 },
    { id: 'game_10', cond: c.gamesPlayed >= 10 },
    { id: 'game_high_50', cond: (state.gameHighScore || 0) >= 50 },
    { id: 'game_high_100', cond: (state.gameHighScore || 0) >= 100 },
  ];

  for (const check of checks) {
    if (!unlocked.has(check.id) && check.cond) {
      state.achievements.push({ id: check.id, unlockedAt: new Date().toISOString() });
      newAchievements.push(check.id);
    }
  }
  return newAchievements;
}
```

- `incrementCounter(state, name)` — increments a named counter by 1
- `updateMaxStats(state)` — updates maxBond, maxLevel, maxUnique counters
- `updateStreak(state)` — tracks consecutive active days
- `checkAchievements(state)` — checks all achievement conditions, returns array of newly unlocked achievement IDs
