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

const VERSION = '2.1.0';

// ─── Registry Loading ────────────────────────────────────────────────────────

function resolveRegistryPath() {
  // Runtime layout: pets/ next to this script
  const localPath = path.join(__dirname, 'pets', 'registry.json');
  if (fs.existsSync(localPath)) return localPath;
  // Source layout: pets/ in parent directory
  const srcPath = path.join(__dirname, '..', 'pets', 'registry.json');
  if (fs.existsSync(srcPath)) return srcPath;
  return localPath;
}

function loadRegistry() {
  try {
    return JSON.parse(fs.readFileSync(resolveRegistryPath(), 'utf-8'));
  } catch (e) {
    return { types: {} };
  }
}

const REGISTRY = loadRegistry();

const COLORS = {};
const PET_ICONS = {};
for (const [type, def] of Object.entries(REGISTRY.types)) {
  COLORS[type] = def.colors;
  PET_ICONS[type] = def.icon;
}

const STATE_LABEL_MAP = {
  eating: '吃东西中', playing: '玩耍中', petting: '被抚摸',
  hungry: '饥饿', angry: '生气', excited: '兴奋',
  happy: '开心', sleepy: '打瞌睡', curious: '好奇',
  sad: '沮丧', confused: '困惑', idle: '普通',
  levelup: '升级', sleeping: '深度睡眠', waking: '唤醒欢迎',
  training: '训练中',
  restless: '焦躁', noisy: '话唠', bored: '无聊',
};

const STATE_PRIORITY = [
  'eating', 'playing', 'petting', 'training', 'sleeping',
  'hungry', 'angry', 'excited', 'happy', 'sleepy', 'curious', 'sad',
  'restless', 'noisy', 'bored', 'confused', 'idle',
];

const EVOLUTION_LEVELS = [5, 15, 30];
const EVOLUTION_NAMES = ['基础', '少年', '成年', '觉醒'];
const EVOLUTION_ICONS = ['', '✨', '🌟', '💫'];

const ACHIEVEMENTS = [
  { id: 'first_code', name: '初次编程', desc: '累计编写 1 行代码', icon: '✍️', counter: 'codeWrites', target: 1 },
  { id: 'code_100', name: '小试牛刀', desc: '累计编写 100 行代码', icon: '📝', counter: 'codeWrites', target: 100 },
  { id: 'code_1000', name: '代码达人', desc: '累计编写 1000 行代码', icon: '💻', counter: 'codeWrites', target: 1000 },
  { id: 'code_10000', name: '编程大师', desc: '累计编写 10000 行代码', icon: '🏆', counter: 'codeWrites', target: 10000 },
  { id: 'test_pass_100', name: '测试达人', desc: '测试通过 100 次', icon: '✅', counter: 'bashSuccesses', target: 100 },
  { id: 'feature_10', name: '功能收割机', desc: '完成 10 个功能', icon: '🚀', counter: 'features', target: 10 },
  { id: 'first_feed', name: '初次喂食', desc: '第一次喂食宠物', icon: '🍖', counter: 'feeds', target: 1 },
  { id: 'feed_100', name: '美食家', desc: '喂食 100 次', icon: '🍽️', counter: 'feeds', target: 100 },
  { id: 'play_100', name: '游戏达人', desc: '玩耍 100 次', icon: '🎾', counter: 'plays', target: 100 },
  { id: 'train_50', name: '训练达人', desc: '训练 50 次', icon: '💪', counter: 'trains', target: 50 },
  { id: 'streak_7', name: '一周不落', desc: '连续活跃 7 天', icon: '📅', counter: 'consecutiveDays', target: 7 },
  { id: 'streak_30', name: '月度坚持', desc: '连续活跃 30 天', icon: '🗓️', counter: 'consecutiveDays', target: 30 },
  { id: 'streak_365', name: '年度陪伴', desc: '连续活跃 365 天', icon: '🎂', counter: 'consecutiveDays', target: 365 },
  { id: 'level_10', name: '初露锋芒', desc: '达到 Lv.10', icon: '⭐', counter: 'maxLevel', target: 10 },
  { id: 'level_30', name: '渐入佳境', desc: '达到 Lv.30', icon: '🌟', counter: 'maxLevel', target: 30 },
  { id: 'level_50', name: '炉火纯青', desc: '达到 Lv.50', icon: '💫', counter: 'maxLevel', target: 50 },
  { id: 'level_99', name: '登峰造极', desc: '达到 Lv.99', icon: '👑', counter: 'maxLevel', target: 99 },
  { id: 'evolution_max', name: '完全觉醒', desc: '进化到最终阶段', icon: '🔥', counter: null, target: null },
  { id: 'bond_100', name: '心意相通', desc: '好感度达到 100', icon: '❤️', counter: 'maxBond', target: 100 },
  { id: 'first_dress', name: '初次装扮', desc: '第一次穿戴装扮', icon: '👗', counter: 'dresses', target: 1 },
  { id: 'dress_all', name: '时尚达人', desc: '穿戴过所有装扮', icon: '👑', counter: 'dressItems', target: 5 },
  { id: 'game_10', name: '接食物达人', desc: '玩接食物游戏 10 次', icon: '🎮', counter: 'gamesPlayed', target: 10 },
  { id: 'game_high_50', name: '反应高手', desc: '接食物游戏得分 50+', icon: '🏅', counter: null, target: null },
  { id: 'game_high_100', name: '接食物大师', desc: '接食物游戏得分 100+', icon: '🥇', counter: null, target: null },
  { id: 'all_pets', name: '宠物收集家', desc: '创建过所有 7 种宠物', icon: '🐾', counter: null, target: null },
];

function getAchievementProgress(state) {
  const unlocked = new Set((state.achievements || []).map(a => a.id));
  const c = state.counters || {};

  return ACHIEVEMENTS.map(ach => {
    const isUnlocked = unlocked.has(ach.id);
    let progress = 0;
    let current = 0;

    if (ach.id === 'evolution_max') {
      current = state.evolution || 0;
      progress = current >= 3 ? 1 : 0;
    } else if (ach.id === 'game_high_50') {
      current = state.gameHighScore || 0;
      progress = current >= 50 ? 1 : 0;
    } else if (ach.id === 'game_high_100') {
      current = state.gameHighScore || 0;
      progress = current >= 100 ? 1 : 0;
    } else if (ach.id === 'all_pets') {
      current = Array.isArray(c.petTypes) ? c.petTypes.length : 0;
      progress = current >= 7 ? 1 : 0;
    } else if (ach.counter === 'dressItems') {
      current = Array.isArray(c.dressItems) ? c.dressItems.length : 0;
      progress = current >= 5 ? 1 : 0;
    } else if (ach.counter) {
      current = c[ach.counter] || 0;
      progress = ach.target ? Math.min(current / ach.target, 1) : 0;
    }

    const unlockedEntry = (state.achievements || []).find(a => a.id === ach.id);
    return { ...ach, isUnlocked, current, progress, unlockedAt: unlockedEntry ? unlockedEntry.unlockedAt : null };
  });
}

function padEndCJK(str, targetWidth) {
  let width = 0;
  for (const char of str) {
    width += char.codePointAt(0) > 0x7F ? 2 : 1;
  }
  return str + ' '.repeat(Math.max(0, targetWidth - width));
}

function renderAchievements(state) {
  const progress = getAchievementProgress(state);
  const unlocked = progress.filter(a => a.isUnlocked);
  const locked = progress.filter(a => !a.isUnlocked);

  let output = `🏆 成就列表 (${unlocked.length}/${progress.length})\n\n`;

  for (const ach of unlocked) {
    const date = ach.unlockedAt ? ach.unlockedAt.split('T')[0] : '';
    output += `✅ ${ach.icon} ${padEndCJK(ach.name, 12)} — 解锁于 ${date}\n`;
  }

  for (const ach of locked) {
    if (ach.target) {
      const pct = Math.round(ach.progress * 100);
      output += `🔒 ${ach.icon} ${padEndCJK(ach.name, 12)} — 进度: ${ach.current}/${ach.target} (${pct}%)\n`;
    } else if (ach.current > 0) {
      output += `🔒 ${ach.icon} ${padEndCJK(ach.name, 12)} — 进度: ${ach.current}/3\n`;
    } else {
      output += `🔒 ${ach.icon} ${padEndCJK(ach.name, 12)} — 未解锁\n`;
    }
  }

  return output;
}

// Emoji cycling per state per pet type
const EMOJI_MAP = {
  cat: {
    eating:   ['😋', '😸', '😋'], playing:  ['🎾', '😸', '🎾'],
    petting:  ['😻', '💕', '😻'], hungry:   ['🥺', '😿', '🥺'],
    angry:    ['😾', '😠', '😾'], excited:  ['🤩', '✨', '🤩'],
    happy:    ['😊', '😸', '😻'], sleepy:   ['😴', '💤', '😴'],
    curious:  ['👀', '🧐', '👀'], sad:      ['😿', '😥', '😿'],
    confused: ['😹', '🤔', '😹'], idle:     ['😺', '😻', '😺'],
    sleeping: ['😴', '💤', '🌙'], training: ['💪', '😸', '💪'],
  },
  dog: {
    eating:   ['🍖', '😋', '🍖'], playing:  ['🎾', '🐶', '🎾'],
    petting:  ['💕', '😊', '💕'], hungry:   ['🥺', '🍖', '🥺'],
    angry:    ['😠', '🐕‍🦺', '😠'], excited:  ['🤩', '✨', '🤩'],
    happy:    ['😊', '🐶', '😄'], sleepy:   ['😴', '💤', '😴'],
    curious:  ['👀', '🐕', '👀'], sad:      ['😢', '🥺', '😢'],
    confused: ['🤔', '🐶', '🤔'], idle:     ['🐶', '😌', '🐶'],
    sleeping: ['😴', '💤', '🌙'], training: ['💪', '🐶', '💪'],
  },
  hamster: {
    eating:   ['🌰', '😋', '🐹'], playing:  ['🎡', '🐹', '🎡'],
    petting:  ['💕', '😊', '🐹'], hungry:   ['🥺', '🌰', '🥺'],
    angry:    ['😤', '🐹', '😤'], excited:  ['🤩', '✨', '🐹'],
    happy:    ['😊', '🐹', '😌'], sleepy:   ['😴', '💤', '😴'],
    curious:  ['👀', '🧐', '🐹'], sad:      ['😢', '🥺', '🐹'],
    confused: ['🤔', '🐹', '🤔'], idle:     ['😌', '🐹', '😌'],
    restless: ['😣', '🐹', '😣'],
    sleeping: ['😴', '💤', '🌙'], training: ['💪', '🐹', '💪'],
  },
  rabbit: {
    eating:   ['🥕', '😋', '🐰'], playing:  ['🏃', '🐰', '🏃'],
    petting:  ['💕', '😊', '🐰'], hungry:   ['🥕', '🥺', '🥕'],
    angry:    ['😤', '🐰', '😤'], excited:  ['🤩', '✨', '🐰'],
    happy:    ['😊', '🐰', '😌'], sleepy:   ['😴', '💤', '😴'],
    curious:  ['👀', '🧐', '🐰'], sad:      ['😢', '🥺', '🐰'],
    confused: ['🤔', '🐰', '🤔'], idle:     ['😌', '🐰', '😌'],
    restless: ['😣', '🐰', '😣'],
    sleeping: ['😴', '💤', '🌙'], training: ['💪', '🐰', '💪'],
  },
  parrot: {
    eating:   ['🌰', '😋', '🦜'], playing:  ['🎪', '🦜', '🎪'],
    petting:  ['💕', '😊', '🦜'], hungry:   ['🥺', '🌰', '🥺'],
    angry:    ['😤', '🦜', '😤'], excited:  ['🤩', '✨', '🦜'],
    happy:    ['😊', '🦜', '😌'], sleepy:   ['😴', '💤', '😴'],
    curious:  ['👀', '🧐', '🦜'], sad:      ['😢', '🥺', '🦜'],
    confused: ['🤔', '🦜', '🤔'], idle:     ['😌', '🦜', '😌'],
    noisy:    ['🗣️', '🦜', '🗣️'],
    sleeping: ['😴', '💤', '🌙'], training: ['💪', '🦜', '💪'],
  },
  turtle: {
    eating:   ['🥬', '😋', '🐢'], playing:  ['🐢', '😊', '🐢'],
    petting:  ['💕', '😊', '🐢'], hungry:   ['🥬', '🥺', '🥬'],
    angry:    ['😤', '🐢', '😤'], excited:  ['🤩', '✨', '🐢'],
    happy:    ['😊', '🐢', '😌'], sleepy:   ['😴', '💤', '😴'],
    curious:  ['👀', '🧐', '🐢'], sad:      ['😢', '🥺', '🐢'],
    confused: ['🤔', '🐢', '🤔'], idle:     ['😌', '🐢', '😌'],
    sleeping: ['😴', '💤', '🌙'], training: ['💪', '🐢', '💪'],
  },
  fish: {
    eating:   ['🍤', '😋', '🐟'], playing:  ['🫧', '🐟', '🫧'],
    petting:  ['💕', '😊', '🐟'], hungry:   ['🥺', '🍤', '🥺'],
    angry:    ['😤', '🐟', '😤'], excited:  ['🤩', '✨', '🐟'],
    happy:    ['😊', '🐟', '😌'], sleepy:   ['😴', '💤', '😴'],
    curious:  ['👀', '🧐', '🐟'], sad:      ['😢', '🥺', '🐟'],
    confused: ['🤔', '🐟', '🤔'], idle:     ['😌', '🐟', '😌'],
    bored:    ['😐', '🐟', '😐'],
    sleeping: ['😴', '💤', '🌙'], training: ['💪', '🐟', '💪'],
  },
};

function getEmojiMap(petType, evolution = 0) {
  const base = EMOJI_MAP[petType] || EMOJI_MAP.cat;
  if (evolution <= 0) return base;

  // Deep clone base map
  const result = {};
  for (const [state, emojis] of Object.entries(base)) {
    result[state] = [...emojis];
  }

  // Apply evolution emoji boosts
  const stages = getEvolution(petType);
  for (let i = 0; i < evolution && i < stages.length; i++) {
    const boost = stages[i].emojiBoost;
    for (const [stateLabel, replacements] of Object.entries(boost)) {
      if (result[stateLabel]) {
        result[stateLabel] = result[stateLabel].map(emoji => {
          return replacements[emoji] || emoji;
        });
      }
    }
  }

  return result;
}

function getDescriptionMap(petType, evolution = 0) {
  const base = DESCRIPTION_MAP[petType] || DESCRIPTION_MAP.cat;
  if (evolution <= 0) return base;

  // Deep clone base map
  const result = {};
  for (const [state, descs] of Object.entries(base)) {
    result[state] = [...descs];
  }

  // Apply evolution description boosts
  const stages = getEvolution(petType);
  for (let i = 0; i < evolution && i < stages.length; i++) {
    const boost = stages[i].descBoost;
    for (const [stateLabel, replacement] of Object.entries(boost)) {
      if (result[stateLabel]) {
        result[stateLabel] = result[stateLabel].map(desc => {
          return desc === replacement.old ? replacement.new : desc;
        });
      }
    }
  }

  return result;
}

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
    sleeping: ['安静地睡着了', '偶尔动一下', '做了个美梦', '发出轻微的呼吸声'],
    training: ['认真地训练中', '专注地练习', '努力地锻炼', '汗流浃背地训练'],
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
    sleeping: ['安静地睡着了', '偶尔动一下', '做了个美梦', '发出轻微的呼吸声'],
    training: ['认真地训练中', '专注地练习', '努力地锻炼', '汗流浃背地训练'],
  },
  hamster: {
    eating:   ['两颊塞得满满的', '小口小口地啃', '偷偷往腮帮子里塞', '吃完满足地舔嘴'],
    playing:  ['在转轮上飞速奔跑', '兴奋地钻进钻出管道', '追着小球跑', '跑得刹不住车'],
    petting:  ['发出满足的咕噜声', '眯着眼享受', '蜷成小球蹭你的手', '身体软绵绵的'],
    hungry:   ['两颊空空到处找食物', '焦急地在笼子里转圈', '可怜巴巴地看着你', '用爪子扒拉食盆'],
    angry:    ['气鼓鼓地膨胀成一团', '发出吱吱的抗议声', '背对着你', '小脚跺来跺去'],
    excited:  ['在转轮上疯狂跑步', '兴奋地蹦来蹦去', '跑转轮停不下来', '眼睛亮晶晶的'],
    happy:    ['满足地嚼着瓜子', '两颊鼓鼓地看着你', '蜷成小毛球打盹', '偷偷把食物藏进角落'],
    sleepy:   ['眼皮越来越重', '打了个小哈欠', '蜷成一个毛球', '安静地睡着了'],
    curious:  ['鼻子一抽一抽地闻味道', '歪着头看你', '发现了新东西', '用小爪子碰了碰你的手'],
    sad:      ['耳朵耷拉着缩在角落', '小声地吱了一声', '低着头不说话', '蜷得更紧了'],
    confused: ['歪头看着你', '鼻子抽了抽', '在原地转了一圈', '用小爪子挠了挠头'],
    idle:     ['蜷成一团打盹', '半眯着眼发呆', '小耳朵动了动', '慢悠悠地伸了个懒腰'],
    restless: ['来回踱步坐立不安', '焦躁地跳来跳去', '用爪子抓笼子', '浑身不自在'],
    sleeping: ['安静地睡着了', '偶尔动一下', '做了个美梦', '发出轻微的呼吸声'],
    training: ['认真地训练中', '专注地练习', '努力地锻炼', '汗流浃背地训练'],
  },
  rabbit: {
    eating:   ['小口小口地啃胡萝卜', '两颊鼓鼓地嚼', '吃完满足地舔嘴', '偷偷藏了一根'],
    playing:  ['在笼子里疯狂蹦跳', '高高跳起转圈', '追着小球跑', '蹦得刹不住车'],
    petting:  ['发出满足的咕噜声', '眯着眼享受', '耳朵放松垂下来', '身体软绵绵的'],
    hungry:   ['到处找胡萝卜', '焦急地在笼子里转圈', '可怜巴巴地看着你', '用爪子扒拉食盆'],
    angry:    ['气鼓鼓地跺脚', '发出吱吱的抗议声', '背对着你', '后脚使劲跺'],
    excited:  ['兴奋地蹦来蹦去', '跳得好高差点飞起来', '在你身边转圈蹦', '眼睛亮晶晶的'],
    happy:    ['开心地原地蹦跳', '耳朵竖得高高的', '用鼻子蹭你的手', '满足地嚼着草'],
    sleepy:   ['眼皮越来越重', '打了个小哈欠', '蜷成一个毛球', '安静地睡着了'],
    curious:  ['鼻子一抽一抽地闻味道', '长耳朵转向声音方向', '歪着头看你', '用爪子碰了碰你的手'],
    sad:      ['耳朵耷拉着缩在角落', '小声地吱了一声', '低着头不说话', '蜷得更紧了'],
    confused: ['歪头看着你', '鼻子抽了抽', '在原地转了一圈', '用小爪子挠了挠头'],
    idle:     ['蜷成一团打盹', '半眯着眼发呆', '小耳朵动了动', '慢悠悠地伸了个懒腰'],
    restless: ['来回踱步坐立不安', '焦躁地蹦来蹦去', '用爪子抓笼子', '浑身不自在'],
    sleeping: ['安静地睡着了', '偶尔动一下', '做了个美梦', '发出轻微的呼吸声'],
    training: ['认真地训练中', '专注地练习', '努力地锻炼', '汗流浃背地训练'],
  },
  parrot: {
    eating:   ['小口小口地啄食物', '用喙灵巧地剥壳', '吃完满足地梳毛', '偷偷藏了一颗'],
    playing:  ['在笼子里飞来飞去', '追着玩具跑', '展示翻跟头', '兴奋地嘎嘎叫'],
    petting:  ['发出满足的咕咕声', '眯着眼享受', '羽毛蓬松放松', '用头蹭你的手指'],
    hungry:   ['用爪子扒拉食盆', '在笼子里焦急地走来走去', '可怜地看着你', '大声嘎嘎叫'],
    angry:    ['展翅威吓', '用喙啄了你一下', '拒绝看你', '羽毛炸开'],
    excited:  ['兴奋地展翅蹦跳', '在栖木上跳来跳去', '眼睛亮晶晶的', '开心地嘎嘎叫'],
    happy:    ['开心地梳理羽毛', '歪着头看你', '嘎嘎叫了两声', '展示漂亮的尾羽'],
    sleepy:   ['单脚站立睡着了', '打了个小哈欠', '眼皮越来越重', '把头埋进翅膀里'],
    curious:  ['歪着头看你写代码', '凑近屏幕看了看', '盯着光标看', '用爪子拍了拍键盘'],
    sad:      ['羽毛蓬松地缩在角落', '小声地嘎了一声', '低着头不说话', '无精打采的'],
    confused: ['歪头看着你', '眨了眨眼', '在原地转了一圈', '模仿了一下你的声音'],
    idle:     ['安静地站在栖木上', '半眯着眼发呆', '梳理了一下羽毛', '慢悠悠地伸展翅膀'],
    noisy:    ['嘎嘎嘎说个不停', '模仿你说话', '大声展示新学的词', '兴奋地展翅'],
    sleeping: ['安静地睡着了', '偶尔动一下', '做了个美梦', '发出轻微的呼吸声'],
    training: ['认真地训练中', '专注地练习', '努力地锻炼', '汗流浃背地训练'],
  },
  turtle: {
    eating:   ['慢慢地啃菜叶', '小口小口地嚼', '吃了好久才吃完', '满足地眨了眨眼'],
    playing:  ['慢慢地爬来爬去', '追着菜叶跑（虽然很慢）', '用壳顶了顶球', '慢悠悠地探索'],
    petting:  ['慢慢地伸出头享受', '眼睛眯了起来', '壳微微颤动', '满足地不动了'],
    hungry:   ['慢慢地爬向食盆', '可怜巴巴地看着你', '用鼻子碰了碰菜叶', '小口小口地啃'],
    angry:    ['缩进壳里不理你', '慢慢地转过身去', '头缩进去又伸出来', '哼了一声'],
    excited:  ['难得地爬快了一点', '眼睛亮了亮', '慢慢地转了个圈', '开心地伸长了脖子'],
    happy:    ['慢慢地伸展四肢', '悠闲地晒太阳', '满足地眨了眨眼', '慢悠悠地爬了两步'],
    sleepy:   ['眼皮越来越慢地闭上', '四脚慢慢缩进壳里', '安静地睡着了', '偶尔动一下'],
    curious:  ['慢慢地转头看向你', '伸出脖子观察', '用慢动作凑近闻了闻', '眨了眨眼'],
    sad:      ['缩进壳里不出来', '慢慢地叹了口气', '低着头不动', '无精打采的'],
    confused: ['慢慢地歪头', '眨了眨眼', '用慢动作转了一圈', '伸长脖子看了看'],
    idle:     ['安静地趴着发呆', '半眯着眼晒太阳', '四脚缩进壳里', '慢慢地眨了一下眼'],
    sleeping: ['安静地睡着了', '偶尔动一下', '做了个美梦', '发出轻微的呼吸声'],
    training: ['认真地训练中', '专注地练习', '努力地锻炼', '汗流浃背地训练'],
  },
  fish: {
    eating:   ['快速游向鱼食', '一口一口地吃', '吐了一串满足的泡泡', '吃完满足地游'],
    playing:  ['追着气泡跑', '在水草间穿梭', '快速游来游去', '用嘴顶小球'],
    petting:  ['游近你的手指', '用嘴轻轻碰了碰', '慢慢地游来游去', '满足地吐泡泡'],
    hungry:   ['游到水面等鱼食', '焦急地转圈', '可怜巴巴地看着你', '用嘴碰了碰鱼缸壁'],
    angry:    ['快速转圈游', '用尾巴甩水', '吐了一串泡泡抗议', '躲进水草里'],
    excited:  ['兴奋地快速游动', '追着泡泡跑', '在鱼缸里转圈', '眼睛亮晶晶的'],
    happy:    ['开心地吐了一串泡泡', '尾巴轻轻摆动', '在水草间穿梭', '悠闲地游来游去'],
    sleepy:   ['慢慢地沉到缸底', '偶尔动一下鳍', '安静地不动了', '在水草间睡着'],
    curious:  ['游近鱼缸壁看你', '歪着头观察', '发现了新东西', '用嘴碰了碰水草'],
    sad:      ['无力地漂浮着', '尾巴不动了', '躲在水草后面', '慢慢地沉到缸底'],
    confused: ['歪头看着你', '在原地转了一圈', '用嘴碰了碰玻璃', '游近又游远'],
    idle:     ['慢悠悠地游来游去', '静静地漂浮着', '偶尔摆一下尾巴', '在水草间休息'],
    bored:    ['无力地漂浮着', '偶尔动一下', '对什么都没兴趣', '需要换水了'],
    sleeping: ['安静地睡着了', '偶尔动一下', '做了个美梦', '发出轻微的呼吸声'],
    training: ['认真地训练中', '专注地练习', '努力地锻炼', '汗流浃背地训练'],
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
  const filePath = path.join(os.homedir(), '.pet', 'state.json');
  try {
    if (!fs.existsSync(filePath)) return null;
    const raw = fs.readFileSync(filePath, 'utf-8');
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function saveState(state) {
  const dir = path.join(os.homedir(), '.pet');
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

  if (!state.counters) state.counters = {};
  if (!Array.isArray(state.counters.petTypes)) state.counters.petTypes = [];
  if (state.type && !state.counters.petTypes.includes(state.type)) {
    state.counters.petTypes.push(state.type);
  }

  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(tmpPath, JSON.stringify(state, null, 2), 'utf-8');
  if (fs.existsSync(filePath)) fs.copyFileSync(filePath, bakPath);
  fs.renameSync(tmpPath, filePath);
}

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
    { id: 'all_pets', cond: Array.isArray(c.petTypes) && c.petTypes.length >= 7 },
  ];

  for (const check of checks) {
    if (!unlocked.has(check.id) && check.cond) {
      state.achievements.push({ id: check.id, unlockedAt: new Date().toISOString() });
      newAchievements.push(check.id);
    }
  }

  return newAchievements;
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
  // Look for pets/ next to this script first (runtime layout: ~/.pet/pets/)
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

// ─── Evolution Parser ────────────────────────────────────────────────────────

const evolutionCache = {};

function parseEvolution(petType) {
  const petFile = path.join(SKILL_DIR, 'pets', `${petType}.md`);
  if (!fs.existsSync(petFile)) return [];

  const content = fs.readFileSync(petFile, 'utf-8');

  // Find the "进化装饰" section
  const evoSectionMatch = content.match(/### 进化装饰\n([\s\S]*?)(?=\n### |\n---|$)/);
  if (!evoSectionMatch) return [];

  const section = evoSectionMatch[1];
  const stages = [];

  // Parse each stage block: **少年 (level >= N):**
  const stageRegex = /\*\*(.+?) \(level >= (\d+)\):\*\*\n([\s\S]*?)(?=\n\*\*.+? \(level >=|\s*$)/g;
  let match;

  while ((match = stageRegex.exec(section)) !== null) {
    const stageName = match[1];
    const level = parseInt(match[2], 10);
    const body = match[3];

    const stage = { level, name: stageName, faceMap: {}, decoTop: '', decoBottom: '', colorBoost: {}, emojiBoost: {}, descBoost: {} };

    // Parse 表情升级: A → B, C → D
    const faceMatch = body.match(/表情升级:\s*(.+)/);
    if (faceMatch) {
      const pairs = faceMatch[1].split(',');
      for (const pair of pairs) {
        const [old, newStr] = pair.split('→').map(s => s.trim());
        if (old && newStr) stage.faceMap[old] = newStr;
      }
    }

    // Parse 装饰行: [COLOR] text[0]
    const decoTopMatch = body.match(/装饰行:\s*(.+)/);
    if (decoTopMatch) stage.decoTop = decoTopMatch[1].trim();

    // Parse 尾部装饰: [COLOR] text[0]
    const decoBottomMatch = body.match(/尾部装饰:\s*(.+)/);
    if (decoBottomMatch) stage.decoBottom = decoBottomMatch[1].trim();

    // Parse 颜色增强: old → new, old2 → new2
    const colorMatch = body.match(/颜色增强:\s*(.+)/);
    if (colorMatch) {
      const pairs = colorMatch[1].split(',');
      for (const pair of pairs) {
        const [old, newStr] = pair.split('→').map(s => s.trim());
        if (old && newStr) stage.colorBoost[old] = newStr;
      }
    }

    // Parse emoji 增强: (multi-line, indented)
    const emojiSection = body.match(/emoji 增强:\n([\s\S]*?)(?=\n描述增强:|\n\*\*|$)/);
    if (emojiSection) {
      const lines = emojiSection[1].trim().split('\n');
      for (const line of lines) {
        const lineMatch = line.match(/^\s*(\w+):\s*(.+)/);
        if (lineMatch) {
          const stateLabel = lineMatch[1];
          stage.emojiBoost[stateLabel] = {};
          const pairs = lineMatch[2].split(',');
          for (const pair of pairs) {
            const [old, newStr] = pair.split('→').map(s => s.trim());
            if (old && newStr) stage.emojiBoost[stateLabel][old] = newStr;
          }
        }
      }
    }

    // Parse 描述增强: (multi-line, indented)
    const descSection = body.match(/描述增强:\n([\s\S]*?)(?=\n\*\*|$)/);
    if (descSection) {
      const lines = descSection[1].trim().split('\n');
      for (const line of lines) {
        const lineMatch = line.match(/^\s*(\w+):\s*(.+)/);
        if (lineMatch) {
          const stateLabel = lineMatch[1];
          const [old, newStr] = lineMatch[2].split('→').map(s => s.trim());
          if (old && newStr) stage.descBoost[stateLabel] = { old, new: newStr };
        }
      }
    }

    stages.push(stage);
  }

  return stages;
}

function getEvolution(petType) {
  if (!evolutionCache[petType]) evolutionCache[petType] = parseEvolution(petType);
  return evolutionCache[petType];
}

function applyEvolution(frameLines, petType, evolution) {
  if (evolution <= 0) return frameLines;

  const stages = getEvolution(petType);
  let lines = [...frameLines];

  for (let i = 0; i < evolution && i < stages.length; i++) {
    const stage = stages[i];

    // 1. Face replacement
    if (Object.keys(stage.faceMap).length > 0) {
      lines = lines.map(line => {
        let result = line;
        for (const [old, rep] of Object.entries(stage.faceMap)) {
          result = result.split(old).join(rep);
        }
        return result;
      });
    }

    // 2. Color boost: replace [old] with [new]
    if (Object.keys(stage.colorBoost).length > 0) {
      lines = lines.map(line => {
        let result = line;
        for (const [old, rep] of Object.entries(stage.colorBoost)) {
          result = result.split(`[${old}]`).join(`[${rep}]`);
        }
        return result;
      });
    }

    // 3. Top decoration
    if (stage.decoTop) {
      lines = [stage.decoTop, ...lines];
    }

    // 4. Bottom decoration
    if (stage.decoBottom) {
      lines = [...lines, stage.decoBottom];
    }
  }

  return lines;
}

// ─── Outfit Parser ───────────────────────────────────────────────────────────

const outfitCache = {};

function parseOutfit(petType) {
  const petFile = path.join(SKILL_DIR, 'pets', `${petType}.md`);
  if (!fs.existsSync(petFile)) return {};

  const content = fs.readFileSync(petFile, 'utf-8');

  // Find the "装扮物品" section
  const outfitSectionMatch = content.match(/### 装扮物品\n([\s\S]*?)(?=\n### |\n---|$)/);
  if (!outfitSectionMatch) return {};

  const section = outfitSectionMatch[1];
  const outfits = {};

  // Parse each outfit block: **帽子:**
  const outfitRegex = /\*\*(.+?):\*\*\n([\s\S]*?)(?=\n\*\*.+?:|\s*$)/g;
  let match;

  while ((match = outfitRegex.exec(section)) !== null) {
    const itemName = match[1].trim();
    const body = match[2];

    const outfit = { decoTop: '', decoBottom: '', faceMap: {}, leftDeco: '', rightDeco: '' };

    // Parse 装饰行
    const decoTopMatch = body.match(/装饰行:\s*(.+)/);
    if (decoTopMatch) outfit.decoTop = decoTopMatch[1].trim();

    // Parse 尾部装饰
    const decoBottomMatch = body.match(/尾部装饰:\s*(.+)/);
    if (decoBottomMatch) outfit.decoBottom = decoBottomMatch[1].trim();

    // Parse 表情替换
    const faceMatch = body.match(/表情替换:\s*(.+)/);
    if (faceMatch) {
      const pairs = faceMatch[1].split(',');
      for (const pair of pairs) {
        const [old, newStr] = pair.split('→').map(s => s.trim());
        if (old && newStr) outfit.faceMap[old] = newStr;
      }
    }

    // Parse 左装饰
    const leftMatch = body.match(/左装饰:\s*(.+)/);
    if (leftMatch) outfit.leftDeco = leftMatch[1].trim();

    // Parse 右装饰
    const rightMatch = body.match(/右装饰:\s*(.+)/);
    if (rightMatch) outfit.rightDeco = rightMatch[1].trim();

    // Map Chinese name to English key
    const keyMap = { '帽子': 'hat', '围巾': 'scarf', '眼镜': 'glasses', '翅膀': 'wings', '光环': 'halo' };
    const key = keyMap[itemName] || itemName.toLowerCase();
    outfits[key] = outfit;
  }

  return outfits;
}

function getOutfit(petType) {
  if (!outfitCache[petType]) outfitCache[petType] = parseOutfit(petType);
  return outfitCache[petType];
}

function applyOutfit(frameLines, petType, outfitKey) {
  if (!outfitKey) return frameLines;

  const outfits = getOutfit(petType);
  const outfit = outfits[outfitKey];
  if (!outfit) return frameLines;

  let lines = [...frameLines];

  // 1. Face replacement
  if (Object.keys(outfit.faceMap).length > 0) {
    lines = lines.map(line => {
      let result = line;
      for (const [old, rep] of Object.entries(outfit.faceMap)) {
        result = result.split(old).join(rep);
      }
      return result;
    });
  }

  // 2. Left/Right decoration (for wings etc.)
  if (outfit.leftDeco || outfit.rightDeco) {
    lines = lines.map(line => {
      const left = outfit.leftDeco ? outfit.leftDeco + ' ' : '';
      const right = outfit.rightDeco ? ' ' + outfit.rightDeco : '';
      return left + line + right;
    });
  }

  // 3. Top decoration
  if (outfit.decoTop) {
    lines = [outfit.decoTop, ...lines];
  }

  // 4. Bottom decoration
  if (outfit.decoBottom) {
    lines = [...lines, outfit.decoBottom];
  }

  return lines;
}

// ─── ASCII Art Renderer ──────────────────────────────────────────────────────

function renderAsciiArt(petType, stateLabel, frame, evolution = 0, outfit = null) {
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

  // Apply evolution decorations
  const decoratedFrame = applyEvolution(selectedFrame, petType, evolution);

  // Apply outfit decorations
  const finalFrame = applyOutfit(decoratedFrame, petType, outfit);

  const petColors = COLORS[petType] || COLORS.cat;
  return finalFrame.map(line => applyColors(line, petColors.primary)).join('\n');
}

// ─── State Label Determination ───────────────────────────────────────────────

function determineStateLabel(state) {
  // Check sleeping state first
  if (state.sleeping) return 'sleeping';

  // Check unique-attribute-triggered states first (type-specific)
  const petType = state.type || 'cat';
  const typeDef = REGISTRY.types[petType];
  if (typeDef && typeDef.unique) {
    const field = typeDef.unique.field;
    const value = state.unique?.[field] ?? typeDef.unique.default;
    if (field === 'exercise' && value < 30) return 'restless';
    if (field === 'agility' && value < 30) return 'restless';
    if (field === 'intelligence' && value >= 80) return 'noisy';
    if (field === 'vitality' && value < 20) return 'bored';
  }

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

// ─── Unique Attribute Display ────────────────────────────────────────────────

function getUniqueDisplay(state) {
  const type = state.type || 'cat';
  const typeDef = REGISTRY.types[type];
  if (!typeDef || !typeDef.unique) return '';
  const field = typeDef.unique.field;
  const value = state.unique?.[field] ?? typeDef.unique.default;
  // Always show unique attribute if it has a value, regardless of decay/grow rates
  return ` ${typeDef.unique.icon}${value}`;
}

// ─── Statusline Renderer ────────────────────────────────────────────────────

function renderStatusLine(state) {
  const petType = state.type || 'cat';
  const petColors = COLORS[petType] || COLORS.cat;
  const frame = state.frame || 0;
  const evolution = state.evolution || 0;
  const stateLabel = determineStateLabel(state);

  const emojis = getEmojiMap(petType, evolution)[stateLabel] || EMOJI_MAP.cat.idle;
  const descriptions = getDescriptionMap(petType, evolution)[stateLabel] || DESCRIPTION_MAP.cat[stateLabel] || DESCRIPTION_MAP.cat.idle;

  const emoji = emojis[frame % emojis.length];
  const description = descriptions[frame % descriptions.length];

  const icon = PET_ICONS[petType] || PET_ICONS.cat;
  const coloredIcon = colorize(icon, petColors.primary);
  const evoIcon = EVOLUTION_ICONS[evolution] || '';

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

  const uniqueDisplay = getUniqueDisplay(state);

  const achCount = (state.achievements || []).length;
  const achDisplay = achCount > 0 ? ` 🏆${achCount}/${ACHIEVEMENTS.length}` : '';

  return `${coloredIcon}${evoIcon} ${name} ${coloredLevel} ${emoji} | ${coloredMood} ${coloredHunger} ${coloredBond}${uniqueDisplay} ${coloredExp}${achDisplay} ${description}`;
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
    stateUpdate.counters = stateUpdate.counters || {};
    stateUpdate.counters.gamesPlayed = (stateUpdate.counters.gamesPlayed || 0) + 1;
    checkAchievements(stateUpdate);
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
    const state = loadState();
    const evolution = (state && state.evolution) || 0;
    const outfit = (state && state.outfit) || null;
    console.log(renderAsciiArt(petType, stateLabel, frame, evolution, outfit));
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
  case 'achievements': {
    const state = loadState();
    if (!state) {
      console.log('Pet Buddy: No pet found');
      process.exit(0);
    }
    console.log(renderAchievements(state));
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