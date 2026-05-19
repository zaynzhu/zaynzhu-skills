#!/usr/bin/env node

/**
 * Pet Buddy Enhanced Renderer
 * Zero-dependency Node.js ESM script for ANSI color rendering,
 * sound effects, and catch-food mini-game.
 *
 * Usage:
 *   node pet-renderer.mjs --mode=render --pet=cat --state=happy --frame=0
 *   node pet-renderer.mjs --mode=statusline
 *   node pet-renderer.mjs --mode=sound --event=success
 *   node pet-renderer.mjs --mode=game
 *   node pet-renderer.mjs --version
 */

import fs from 'fs';
import path from 'path';
import os from 'os';
import readline from 'readline';
import { fileURLToPath } from 'url';

// ─── Constants ───────────────────────────────────────────────────────────────

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const VERSION = '2.0.0';

const COLORS = {
  cat: { primary: 208, secondary: 202, highlight: 226 },
  dog: { primary: 130, secondary: 95, highlight: 226 },
};

const PET_ICONS = { cat: '🐱', dog: '🐶' };

const STATE_LABEL_MAP = {
  eating: '吃东西中', playing: '玩耍中', petting: '被抚摸',
  hungry: '饥饿', angry: '生气', excited: '兴奋',
  happy: '开心', sleepy: '打瞌睡', curious: '好奇',
  sad: '沮丧', confused: '困惑', idle: '普通',
  levelup: '升级', sleeping: '休眠告别', waking: '唤醒欢迎',
};

const STATE_PRIORITY = [
  'eating', 'playing', 'petting', 'hungry', 'angry',
  'excited', 'happy', 'sleepy', 'curious', 'sad',
  'confused', 'idle',
];

// Emoji cycling per state per pet type
const EMOJI_MAP = {
  cat: {
    eating:   ['😋', '😸', '😋'], playing:  ['🎾', '😸', '🎾'],
    petting:  ['😻', '💕', '😻'], hungry:   ['🥺', '😿', '🥺'],
    angry:    ['😾', '😠', '😾'], excited:  ['🤩', '✨', '🤩'],
    happy:    ['😊', '😸', '😻'], sleepy:   ['😴', '💤', '😴'],
    curious:  ['👀', '🧐', '👀'], sad:      ['😿', '😥', '😿'],
    confused: ['😹', '🤔', '😹'], idle:     ['😺', '😻', '😺'],
  },
  dog: {
    eating:   ['🍖', '😋', '🍖'], playing:  ['🎾', '🐶', '🎾'],
    petting:  ['💕', '😊', '💕'], hungry:   ['🥺', '🍖', '🥺'],
    angry:    ['😠', '🐕‍🦺', '😠'], excited:  ['🤩', '✨', '🤩'],
    happy:    ['😊', '🐶', '😄'], sleepy:   ['😴', '💤', '😴'],
    curious:  ['👀', '🐕', '👀'], sad:      ['😢', '🥺', '😢'],
    confused: ['🤔', '🐶', '🤔'], idle:     ['🐶', '😌', '🐶'],
  },
};

// Description text cycling per state per pet type
const DESCRIPTION_MAP = {
  cat: {
    eating:   ['优雅地吃着东西', '小口小口地品尝', '吃完后舔了舔嘴', '满意地眯起眼'],
    playing:  ['追着光标跑', '扑向你的手指', '抓住了逗猫棒', '兴奋地蹦来蹦去'],
    petting:  ['发出满足的呼噜声', '眯着眼享受', '用头蹭你的手', '身体软绵绵的'],
    hungry:   ['用爪子轻轻拍你的手', '在食碗旁走来走去', '可怜地看着你', '小声喵喵叫'],
    angry:    ['背弓起来发出嘶嘶声', '用爪子拍了你一下', '拒绝看你', '尾巴炸毛'],
    excited:  ['兴奋地跑来跑去', '眼睛亮晶晶的', '在你身边转圈', '开心地喵喵叫'],
    happy:    ['正在优雅地舔爪子', '歪着头看你', '慢慢眨了眨眼', '尾巴轻轻摆动'],
    sleepy:   ['安静地睡着了', '打了个哈欠', '眼皮越来越重', '蜷成一团'],
    curious:  ['歪着头看你写代码', '凑近屏幕闻了闻', '盯着光标看', '轻轻拍了拍键盘'],
    sad:      ['蜷缩在角落耳朵耷拉着', '轻轻叫了一声', '低头看着地面', '尾巴无力地垂着'],
    confused: ['歪头看着你', '眨了眨眼', '在原地转了一圈', '用爪子碰了碰你的手'],
    idle:     ['趴在一旁打盹', '歪着头看屏幕', '舔了舔爪子', '伸了个懒腰'],
  },
  dog: {
    eating:   ['狼吞虎咽尾巴还在摇', '大口大口地吃', '吃完舔了舔嘴', '满足地打了个饱嗝'],
    playing:  ['兴奋地跑来跑去', '叼着球跑回来', '绕着你转圈', '跳起来想接飞盘'],
    petting:  ['肚皮朝上享受地眯着眼', '尾巴还在轻轻摇', '用头蹭你的手掌', '发出满足的哼哼声'],
    hungry:   ['用湿漉漉的鼻子蹭你的手', '在食碗旁焦急地转圈', '可怜巴巴地看着你', '小声汪汪叫'],
    angry:    ['低吼了一声', '背上的毛竖起来', '不愿意看你', '汪汪叫了两声'],
    excited:  ['疯狂地摇尾巴', '围着你转圈圈', '高兴得跳起来', '汪汪汪叫个不停'],
    happy:    ['尾巴摇得快要飞起来了', '开心地蹭你的腿', '眼睛亮亮地看着你', '兴奋地转圈'],
    sleepy:   ['蜷成一团偶尔抽动一下腿', '打了个大哈欠', '眼睛快闭上了', '呼呼睡着了'],
    curious:  ['鼻子凑过来闻你的代码', '歪着头看你', '发现了新东西', '用爪子拍了拍键盘'],
    sad:      ['耷拉着耳朵默默看着你', '蜷成一团不动', '小声地呜了一声', '低着头'],
    confused: ['歪头看着你', '眨了眨眼', '在原地转了一圈', '用鼻子推了推你的手'],
    idle:     ['趴在脚边安静地陪着你', '用鼻子蹭了蹭你的手', '打了个哈欠', '歪着头看你'],
  },
};

// ─── Color System ────────────────────────────────────────────────────────────

function colorize(text, colorCode) {
  return `\x1b[38;5;${colorCode}m${text}\x1b[0m`;
}

function stripColorMarkers(text) {
  return text.replace(/\[\d+\]/g, '');
}

function applyColors(line, defaultColor) {
  const parts = line.split(/(\[\d+\])/);
  if (parts.length === 1) {
    return defaultColor != null ? colorize(line, defaultColor) : line;
  }
  let result = '';
  let currentColor = defaultColor;
  for (const part of parts) {
    const markerMatch = part.match(/^\[(\d+)\]$/);
    if (markerMatch) {
      currentColor = parseInt(markerMatch[1], 10);
    } else if (part.length > 0) {
      result += currentColor != null ? colorize(part, currentColor) : part;
    }
  }
  return result;
}

// ─── State Loader ────────────────────────────────────────────────────────────

function loadState() {
  const filePath = path.join(os.homedir(), '.pet-buddy', 'state.json');
  try {
    if (!fs.existsSync(filePath)) return null;
    const raw = fs.readFileSync(filePath, 'utf-8');
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function saveState(state) {
  const dir = path.join(os.homedir(), '.pet-buddy');
  const filePath = path.join(dir, 'state.json');
  const tmpPath = path.join(dir, 'state.json.tmp');
  const bakPath = path.join(dir, 'state.json.bak');

  state.mood = Math.max(0, Math.min(100, state.mood));
  state.hunger = Math.max(0, Math.min(100, state.hunger));
  state.bond = Math.max(0, Math.min(100, state.bond));
  state.level = Math.max(1, Math.min(99, state.level));
  state.exp = Math.max(0, state.exp);
  state.frame = state.frame % 1000;
  state.lastUpdated = new Date().toISOString();

  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(tmpPath, JSON.stringify(state, null, 2), 'utf-8');
  if (fs.existsSync(filePath)) fs.copyFileSync(filePath, bakPath);
  fs.renameSync(tmpPath, filePath);
}

// ─── Argument Parser ────────────────────────────────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2);
  const parsed = { mode: 'render', state: null, frame: 0, pet: null, event: null, version: false };
  for (const arg of args) {
    if (arg.startsWith('--mode='))      parsed.mode = arg.slice(7);
    else if (arg.startsWith('--state=')) parsed.state = arg.slice(8);
    else if (arg.startsWith('--frame=')) parsed.frame = parseInt(arg.slice(8), 10) || 0;
    else if (arg.startsWith('--pet='))   parsed.pet = arg.slice(6);
    else if (arg.startsWith('--event=')) parsed.event = arg.slice(8);
    else if (arg === '--version')        parsed.version = true;
  }
  return parsed;
}

// ─── Pet Definition Parser ──────────────────────────────────────────────────

function findSkillDir() {
  // Look for pets/ next to this script first (runtime layout: ~/.pet-buddy/pets/)
  const localPets = path.join(__dirname, 'pets');
  if (fs.existsSync(path.join(localPets, 'cat.md'))) return __dirname;
  // Fallback: source layout (pets/ in parent directory)
  const srcPets = path.join(__dirname, '..', 'pets');
  if (fs.existsSync(path.join(srcPets, 'cat.md'))) return path.dirname(srcPets);
  return __dirname;
}

const SKILL_DIR = findSkillDir();

function parsePetArt(petType) {
  const petFile = path.join(SKILL_DIR, 'pets', `${petType}.md`);
  if (!fs.existsSync(petFile)) return {};

  const content = fs.readFileSync(petFile, 'utf-8');

  const chnToEng = {};
  for (const [eng, chn] of Object.entries(STATE_LABEL_MAP)) {
    chnToEng[chn] = eng;
  }

  const frames = {};
  const codeBlockRegex = /```([\s\S]*?)```/g;
  let codeMatch;

  while ((codeMatch = codeBlockRegex.exec(content)) !== null) {
    const blockContent = codeMatch[1];
    const blockStart = codeMatch.index;
    const before = content.slice(0, blockStart);
    const headerRegex = /\*\*([^*]+)\*\*/g;
    let headerMatch, lastHeader = null;
    while ((headerMatch = headerRegex.exec(before)) !== null) {
      lastHeader = headerMatch[1];
    }
    if (!lastHeader) continue;

    let engLabel = null;
    for (const [chn, eng] of Object.entries(chnToEng)) {
      if (lastHeader.includes(chn)) { engLabel = eng; break; }
    }
    if (!engLabel) continue;

    const frameLines = {};
    const lines = blockContent.split('\n');
    let currentFrame = null;

    for (const line of lines) {
      const frameStartMatch = line.match(/^帧(\d+):/);
      if (frameStartMatch) {
        currentFrame = parseInt(frameStartMatch[1], 10);
        frameLines[currentFrame] = [];
      } else if (currentFrame !== null) {
        if (line.trim() === '' && frameLines[currentFrame].length === 0) continue;
        frameLines[currentFrame].push(line);
      }
    }

    for (const idx of Object.keys(frameLines)) {
      const arr = frameLines[idx];
      while (arr.length > 0 && arr[arr.length - 1].trim() === '') arr.pop();
    }

    if (Object.keys(frameLines).length > 0) frames[engLabel] = frameLines;
  }

  return frames;
}

const petArtCache = {};

function getPetArt(petType) {
  if (!petArtCache[petType]) petArtCache[petType] = parsePetArt(petType);
  return petArtCache[petType];
}

// ─── ASCII Art Renderer ──────────────────────────────────────────────────────

function renderAsciiArt(petType, stateLabel, frame) {
  const art = getPetArt(petType);
  const stateFrames = art[stateLabel] || art['idle'];

  if (!stateFrames) {
    const fallback = petType === 'cat'
      ? '  /\\_/\\\n ( •ω• )\n  > _ <'
      : '  / \\__\n (    @\\___\n  /         O\n /   (_____/\n/_____/   U';
    return stripColorMarkers(fallback);
  }

  const frameKeys = Object.keys(stateFrames).map(Number).sort((a, b) => a - b);
  const selectedIdx = frame % frameKeys.length;
  const selectedFrame = stateFrames[frameKeys[selectedIdx]];
  if (!selectedFrame) return '';

  const petColors = COLORS[petType] || COLORS.cat;
  return selectedFrame.map(line => applyColors(line, petColors.primary)).join('\n');
}

// ─── State Label Determination ───────────────────────────────────────────────

function determineStateLabel(state) {
  if (state.hunger >= 90 && state.mood < 30) return 'angry';
  if (state.hunger >= 80) return 'hungry';
  if (state.mood >= 90) return 'excited';
  if (state.mood >= 80) return 'happy';
  if (state.mood >= 60) return 'curious';
  if (state.mood < 40) return 'sad';
  if (state.lastUpdated) {
    const lastUpdated = new Date(state.lastUpdated);
    const diffMinutes = (Date.now() - lastUpdated.getTime()) / (1000 * 60);
    if (diffMinutes > 30) return 'sleepy';
  }
  return 'idle';
}

// ─── Statusline Renderer ────────────────────────────────────────────────────

function renderStatusLine(state) {
  const petType = state.type || 'cat';
  const petColors = COLORS[petType] || COLORS.cat;
  const frame = state.frame || 0;
  const stateLabel = determineStateLabel(state);

  const emojis = (EMOJI_MAP[petType] && EMOJI_MAP[petType][stateLabel]) || EMOJI_MAP.cat.idle;
  const descriptions = (DESCRIPTION_MAP[petType] && DESCRIPTION_MAP[petType][stateLabel]) || DESCRIPTION_MAP.cat.idle;

  const emoji = emojis[frame % emojis.length];
  const description = descriptions[frame % descriptions.length];

  const icon = PET_ICONS[petType] || PET_ICONS.cat;
  const coloredIcon = colorize(icon, petColors.primary);

  const name = state.name || petType;
  const level = state.level || 1;
  const mood = state.mood || 0;
  const hunger = state.hunger || 0;
  const bond = state.bond || 0;
  const exp = state.exp || 0;
  const expThreshold = level * 100;

  // Color each attribute differently
  const coloredLevel = colorize(`Lv.${level}`, 82);      // green
  const coloredMood = colorize(`❤️${mood}`, 199);         // pink/red
  const coloredHunger = colorize(`🍖${hunger}`, 208);     // orange
  const coloredBond = colorize(`🤝${bond}`, 75);          // blue
  const coloredExp = colorize(`✨${exp}/${expThreshold}`, 226); // yellow/gold

  return `${coloredIcon} ${name} ${coloredLevel} ${emoji} | ${coloredMood} ${coloredHunger} ${coloredBond} ${coloredExp} ${description}`;
}

// ─── Sound System ────────────────────────────────────────────────────────────

const SOUND_MAP = {
  success:  [{ count: 1, delay: 0 }],
  testPass: [{ count: 2, delay: 200 }],
  testFail:  [{ count: 1, delay: 0 }],
  levelUp:  [{ count: 3, delay: 300 }],
  interact: [{ count: 1, delay: 0 }],
};

function playSound(eventType, state) {
  if (state && state.soundEnabled === false) return;
  if (!process.stdout.isTTY) return;

  const pattern = SOUND_MAP[eventType];
  if (!pattern) return;

  const BEL = '\x07';
  for (const step of pattern) {
    for (let i = 0; i < step.count; i++) {
      if (i > 0) {
        const end = Date.now() + step.delay;
        while (Date.now() < end) { /* busy wait */ }
      }
      process.stdout.write(BEL);
    }
  }
}

// ─── Catch-food Mini-game ────────────────────────────────────────────────────

const GAME_WIDTH = 20;
const GAME_HEIGHT = 10;
const GAME_ROUNDS = 10;
const GAME_TICK_MS = 150;

const GAME_FOOD = {
  cat: ['🐟', '🍗'],
  dog: ['🦴', '🥩'],
};
const GAME_OBSTACLE = '💩';

function renderGameFrame(petCol, items, petEmoji, score, round) {
  const grid = [];
  for (let r = 0; r < GAME_HEIGHT; r++) {
    grid[r] = new Array(GAME_WIDTH).fill(' ');
  }
  for (const item of items) {
    if (item.row >= 0 && item.row < GAME_HEIGHT && item.col >= 0 && item.col < GAME_WIDTH) {
      grid[item.row][item.col] = item.emoji;
    }
  }

  const lines = [];
  lines.push(`🎮 Catch-the-Food! Round ${round}/${GAME_ROUNDS}  Score: ${score}`);
  lines.push('+' + '-'.repeat(GAME_WIDTH) + '+');

  for (let r = 0; r < GAME_HEIGHT; r++) {
    let rowStr = '|';
    for (let c = 0; c < GAME_WIDTH; c++) {
      if (r === GAME_HEIGHT - 1 && c === petCol) {
        rowStr += petEmoji;
      } else {
        rowStr += grid[r][c];
      }
    }
    rowStr += '|';
    lines.push(rowStr);
  }

  lines.push('+' + '-'.repeat(GAME_WIDTH) + '+');
  lines.push('←→ Move  Q Quit');
  return lines.join('\n');
}

async function startGame() {
  if (!process.stdin.isTTY) {
    console.log('🎮 Catch-the-Food requires an interactive terminal (TTY).');
    console.log('Please run this command in a terminal to play.');
    process.exit(0);
  }

  const state = loadState();
  if (!state) {
    console.log('No pet found. Please initialize your pet first with /pet');
    process.exit(1);
  }

  const petType = state.type || 'cat';
  const petEmoji = PET_ICONS[petType];
  const petColors = COLORS[petType] || COLORS.cat;
  const foodItems = GAME_FOOD[petType] || GAME_FOOD.cat;

  let petCol = Math.floor(GAME_WIDTH / 2);
  let items = [];
  let score = 0;
  let currentRound = 0;
  let gameOver = false;
  let foodCaught = 0;
  let obstaclesHit = 0;

  readline.emitKeypressEvents(process.stdin);
  process.stdin.setRawMode(true);
  process.stdin.resume();
  process.stdout.write('\x1b[?25l');

  function onKey(str, key) {
    if (gameOver) return;
    if (key.name === 'left' || key.name === 'a') {
      petCol = Math.max(0, petCol - 1);
    } else if (key.name === 'right' || key.name === 'd') {
      petCol = Math.min(GAME_WIDTH - 1, petCol + 1);
    } else if (key.name === 'q' || (key.ctrl && key.name === 'c')) {
      gameOver = true;
      cleanup();
      process.exit(0);
    }
  }

  process.stdin.on('keypress', onKey);

  function cleanup() {
    process.stdout.write('\x1b[?25h');
    process.stdin.setRawMode(false);
    process.stdin.removeListener('keypress', onKey);
    process.stdin.pause();
  }

  function spawnRound() {
    currentRound++;
    const itemCount = Math.min(2 + Math.floor(currentRound / 3), 4);
    for (let i = 0; i < itemCount; i++) {
      const isObstacle = Math.random() < 0.25;
      items.push({
        col: Math.floor(Math.random() * GAME_WIDTH),
        row: 0,
        type: isObstacle ? 'obstacle' : 'food',
        emoji: isObstacle ? GAME_OBSTACLE : foodItems[Math.floor(Math.random() * foodItems.length)],
      });
    }
  }

  function gameTick() {
    if (gameOver) return;

    if (items.filter(i => i.row < GAME_HEIGHT).length === 0 && currentRound < GAME_ROUNDS) {
      spawnRound();
    }

    for (const item of items) item.row++;

    const remainingItems = [];
    for (const item of items) {
      if (item.row >= GAME_HEIGHT) {
        if (item.col === petCol) {
          if (item.type === 'food') { score += 10; foodCaught++; }
          else { score = Math.max(0, score - 5); obstaclesHit++; }
        }
      } else {
        remainingItems.push(item);
      }
    }
    items = remainingItems;

    process.stdout.write('\x1b[2J\x1b[H');
    const frame = renderGameFrame(petCol, items, petEmoji, score, Math.min(currentRound, GAME_ROUNDS));
    process.stdout.write(frame + '\n');

    if (currentRound >= GAME_ROUNDS && items.length === 0) {
      gameOver = true;
      endGame();
    }
  }

  function endGame() {
    cleanup();
    process.stdout.write('\x1b[2J\x1b[H');

    const coloredIcon = colorize(petEmoji, petColors.primary);
    const resultLines = [
      '',
      colorize('🎯 Game Over!', petColors.highlight),
      '',
      `${coloredIcon} ${state.name} caught ${foodCaught} food item${foodCaught !== 1 ? 's' : ''}!`,
      `   Score: ${colorize(String(score), petColors.highlight)} points`,
      `   Obstacles hit: ${obstaclesHit}`,
      '',
    ];

    if (score >= 50) resultLines.push(colorize('🌟 Amazing!', petColors.highlight));
    else if (score >= 20) resultLines.push(colorize('👍 Good job!', petColors.primary));
    else resultLines.push('Better luck next time!');

    resultLines.push('');
    console.log(resultLines.join('\n'));

    const stateUpdate = loadState() || state;
    stateUpdate.mood = Math.max(0, Math.min(100, (stateUpdate.mood || 50) + (score > 0 ? 5 : -5)));
    stateUpdate.hunger = Math.max(0, Math.min(100, (stateUpdate.hunger || 20) - Math.min(foodCaught * 3, 30)));
    stateUpdate.exp = (stateUpdate.exp || 0) + 10 + Math.floor(score / 5);
    stateUpdate.bond = Math.max(0, Math.min(100, (stateUpdate.bond || 50) + 3));
    stateUpdate.gameHighScore = Math.max(stateUpdate.gameHighScore || 0, score);
    stateUpdate.frame = ((stateUpdate.frame || 0) + 1) % 1000;

    while (stateUpdate.exp >= stateUpdate.level * 100 && stateUpdate.level < 99) {
      stateUpdate.exp -= stateUpdate.level * 100;
      stateUpdate.level += 1;
      stateUpdate.mood = Math.min(stateUpdate.mood + 20, 100);
      stateUpdate.hunger = Math.max(stateUpdate.hunger - 10, 0);
      console.log(colorize(`🎉 ${stateUpdate.name} 升级到了 Lv.${stateUpdate.level}！`, petColors.highlight));
    }

    saveState(stateUpdate);
    process.exit(0);
  }

  spawnRound();
  gameTick();

  const gameInterval = setInterval(() => {
    if (gameOver) { clearInterval(gameInterval); return; }
    gameTick();
  }, GAME_TICK_MS);

  process.on('exit', () => { if (!gameOver) cleanup(); });
}

// ─── Main Entry Point ────────────────────────────────────────────────────────

const args = parseArgs();

if (args.version) {
  console.log(`pet-renderer v${VERSION}`);
  process.exit(0);
}

switch (args.mode) {
  case 'render': {
    const petType = args.pet || 'cat';
    const stateLabel = args.state || 'idle';
    const frame = args.frame || 0;
    console.log(renderAsciiArt(petType, stateLabel, frame));
    break;
  }
  case 'statusline': {
    const state = loadState();
    if (!state) {
      console.log('Pet Buddy: No pet found');
      process.exit(0);
    }
    console.log(renderStatusLine(state));
    break;
  }
  case 'sound': {
    const state = loadState();
    playSound(args.event || 'interact', state);
    break;
  }
  case 'game': {
    startGame();
    break;
  }
  default:
    console.error(`Unknown mode: ${args.mode}`);
    process.exit(1);
}