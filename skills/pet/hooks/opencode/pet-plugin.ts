// Pet Buddy plugin for OpenCode
// Handles tool execution events and injects pet status into system prompt.
// Deploy to: .opencode/plugins/pet.ts (project-level)
//   or: ~/.config/opencode/plugins/pet.ts (global)
//
// This plugin reads/writes ~/.pet/state.json (shared across platforms).
// It implements the same state update logic as the bash hooks used by
// Claude Code and Codex CLI.
//
// OpenCode doesn't have a statusLine feature. Pet status is displayed via:
// 1. Appending to tool output after each Edit/Write/Bash call
// 2. Injecting pet context into the system prompt so the LLM mentions the pet

import { type Plugin } from "@opencode-ai/plugin"
import { readFile, writeFile, rename } from "node:fs/promises"
import path from "node:path"
import { homedir } from "node:os"

const PET_BUDDY_DIR = path.join(homedir(), ".pet")
const STATE_FILE = path.join(PET_BUDDY_DIR, "state.json")
const STATE_TMP = path.join(PET_BUDDY_DIR, "state.json.tmp")

interface PetState {
  name: string
  type: "cat" | "dog" | "hamster" | "rabbit" | "parrot" | "turtle" | "fish"
  mood: number
  hunger: number
  bond: number
  level: number
  exp: number
  active: boolean
  showAscii: boolean
  frame: number
  soundEnabled: boolean
  sleeping: boolean
  gameHighScore: number
  createdAt: string
  lastUpdated: string
  platform?: string
  unique?: Record<string, number>
  evolution?: number
  counters?: {
    codeWrites: number
    bashSuccesses: number
    testFails: number
    features: number
    feeds: number
    plays: number
    pets: number
    trains: number
    specials: number
    sleeps: number
    wakes: number
    dresses: number
    dressItems: string[]
    gamesPlayed: number
    maxBond: number
    maxLevel: number
    maxUnique: number
    consecutiveDays: number
    lastActiveDate: string | null
  }
  achievements?: Array<{ id: string; unlockedAt: string }>
}

const PET_ICONS: Record<string, string> = {
  cat: "🐱", dog: "🐶", hamster: "🐹", rabbit: "🐰",
  parrot: "🦜", turtle: "🐢", fish: "🐟",
}

function getPetIcon(type: string): string {
  return PET_ICONS[type] || "🐱"
}

const EVOLUTION_LEVELS = [5, 15, 30]
const EVOLUTION_NAMES = ['基础', '少年', '成年', '觉醒']
const EVOLUTION_ICONS = ['', '✨', '🌟', '💫']

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
]

function incrementCounter(state: PetState, counter: string): void {
  if (!state.counters) return
  if (typeof (state.counters as any)[counter] === 'number') {
    (state.counters as any)[counter]++
  }
}

function updateMaxStats(state: PetState): void {
  if (!state.counters) return
  if (state.bond > (state.counters.maxBond || 0)) state.counters.maxBond = state.bond
  if (state.level > (state.counters.maxLevel || 0)) state.counters.maxLevel = state.level
  const uniqueValues = state.unique ? Object.values(state.unique) : [0]
  const maxUnique = Math.max(...uniqueValues)
  if (maxUnique > (state.counters.maxUnique || 0)) state.counters.maxUnique = maxUnique
}

function updateStreak(state: PetState): void {
  if (!state.counters) return
  const today = new Date().toISOString().split('T')[0]
  if (state.counters.lastActiveDate === today) return

  const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0]
  if (state.counters.lastActiveDate === yesterday) {
    state.counters.consecutiveDays++
  } else {
    state.counters.consecutiveDays = 1
  }
  state.counters.lastActiveDate = today
}

function checkAchievements(state: PetState): string[] {
  if (!state.counters || !state.achievements) return []
  const newAchs: string[] = []
  const unlocked = new Set(state.achievements.map(a => a.id))

  for (const ach of ACHIEVEMENTS) {
    if (unlocked.has(ach.id)) continue
    let cond = false
    if (ach.id === 'evolution_max') cond = (state.evolution || 0) >= 3
    else if (ach.id === 'game_high_50') cond = (state.gameHighScore || 0) >= 50
    else if (ach.id === 'game_high_100') cond = (state.gameHighScore || 0) >= 100
    else if (ach.counter === 'dressItems') cond = Array.isArray(state.counters.dressItems) && state.counters.dressItems.length >= 5
    else if (ach.counter) cond = ((state.counters as any)[ach.counter] || 0) >= (ach.target || 0)

    if (cond) {
      state.achievements.push({ id: ach.id, unlockedAt: new Date().toISOString() })
      newAchs.push(ach.id)
    }
  }
  return newAchs
}

function getEvolutionForLevel(level: number): number {
  let stage = 0
  for (let i = 0; i < EVOLUTION_LEVELS.length; i++) {
    if (level >= EVOLUTION_LEVELS[i]) stage = i + 1
  }
  return stage
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value))
}

// In-process lock to prevent concurrent writes
let writeLock = Promise.resolve()

async function readState(): Promise<PetState | null> {
  try {
    const raw = await readFile(STATE_FILE, "utf-8")
    return JSON.parse(raw) as PetState
  } catch {
    return null
  }
}

async function writeState(state: PetState): Promise<void> {
  // Queue writes to prevent interleaving
  await writeLock
  let resolve: () => void = () => {}
  writeLock = new Promise(r => { resolve = r })

  try {
    state.lastUpdated = new Date().toISOString()
    state.mood = clamp(state.mood, 0, 100)
    state.hunger = clamp(state.hunger, 0, 100)
    state.bond = clamp(state.bond, 0, 100)
    state.level = clamp(state.level, 1, 99)
    state.exp = Math.max(0, state.exp)

    const data = JSON.stringify(state, null, 2)
    await writeFile(STATE_TMP, data, "utf-8")
    await rename(STATE_TMP, STATE_FILE)
  } finally {
    resolve()
  }
}

function applyDecay(state: PetState): void {
  const now = Date.now()
  const last = new Date(state.lastUpdated).getTime()
  const elapsedMs = now - last

  // Skip decay if lastUpdated is in the future
  if (elapsedMs < 0) return

  const hours = elapsedMs / 3600000
  const days = elapsedMs / 86400000

  const hungerRate = state.sleeping ? 2.5 : 5
  state.hunger = clamp(state.hunger + hungerRate * hours, 0, 100)
  if (!state.sleeping) {
    state.bond = clamp(state.bond - 1 * days, 0, 100)
  }
  state.frame = (state.frame + 1) % 1000

  // Apply unique attribute decay based on pet type
  const uniqueConfig: Record<string, { field: string; decayRate: number; min: number; max: number; default: number }> = {
    hamster: { field: "exercise", decayRate: 3, min: 0, max: 100, default: 50 },
    rabbit:  { field: "agility", decayRate: 2, min: 0, max: 100, default: 60 },
    parrot:  { field: "intelligence", decayRate: 1, min: 0, max: 100, default: 50 },
    fish:    { field: "vitality", decayRate: 5, min: 0, max: 100, default: 70 },
  }
  const cfg = uniqueConfig[state.type]
  if (cfg && cfg.decayRate > 0 && hours > 0) {
    if (!state.unique) state.unique = {}
    const cur = state.unique[cfg.field] ?? cfg.default
    state.unique[cfg.field] = clamp(cur - cfg.decayRate * hours, cfg.min, cfg.max)
  }
}

function checkLevelUp(state: PetState): string[] {
  const messages: string[] = []
  const oldEvolution = state.evolution || 0

  while (state.exp >= state.level * 100 && state.level < 99) {
    state.exp -= state.level * 100
    state.level += 1
    state.mood = clamp(state.mood + 20, 0, 100)
    state.hunger = clamp(state.hunger - 10, 0, 100)
    messages.push(`🎉 ${state.name} 升级到了 Lv.${state.level}！`)
  }

  // Check evolution stage crossing
  const newEvolution = getEvolutionForLevel(state.level)
  if (newEvolution > oldEvolution) {
    state.evolution = newEvolution
    const oldName = EVOLUTION_NAMES[oldEvolution]
    const newName = EVOLUTION_NAMES[newEvolution]
    messages.push(`🌟 ${state.name} 进化了！${oldName} → ${newName} ✨ 外观已更新！`)
  } else {
    state.evolution = newEvolution
  }

  return messages
}

function getReactionText(pet: PetState, event: "code_success" | "bash_success" | "bash_failure"): string {
  const icon = getPetIcon(pet.type)

  if (event === "code_success") {
    return `${icon} ${pet.name} 看到你写代码，好奇地盯着屏幕~`
  }
  if (event === "bash_success") {
    return `${icon} ${pet.name} 高兴地摇了摇尾巴！测试通过了！🎉`
  }
  return `${icon} ${pet.name} 安静地陪在你身边...别灰心！💪`
}

function formatStatusBar(state: PetState): string {
  const icon = getPetIcon(state.type)
  const evoIcon = EVOLUTION_ICONS[state.evolution || 0] || ''
  const moodEmoji = state.mood >= 80 ? "😊" : state.mood >= 60 ? "😐" : "😢"
  const achCount = (state.achievements || []).length
  const achDisplay = achCount > 0 ? ` 🏆${achCount}/${ACHIEVEMENTS.length}` : ''
  return `${icon}${evoIcon} ${state.name} Lv.${state.level} ${moodEmoji} | ❤️${state.mood} 🍖${state.hunger} 🤝${state.bond} ✨${state.exp}/${state.level * 100}${achDisplay}`
}

const plugin: Plugin = async (_input) => {
  return {
    // Update pet state after tool execution and append reaction to tool output
    "tool.execute.after": async (input, output) => {
      const state = await readState()
      if (!state || !state.active) return

      applyDecay(state)

      // Skip state changes if sleeping
      if (state.sleeping) return

      const tool = input.tool || ""

      if (tool === "Edit" || tool === "Write") {
        state.mood = clamp(state.mood + 5, 0, 100)
        state.exp += 1
        state.frame = (state.frame + 1) % 1000

        incrementCounter(state, "codeWrites")
        updateMaxStats(state)
        updateStreak(state)

        const levelMessages = checkLevelUp(state)
        const newAchs = checkAchievements(state)
        await writeState(state)

        const reaction = levelMessages.length > 0
          ? levelMessages.join(" ")
          : getReactionText(state, "code_success")
        output.output += `\n\n${reaction} [${formatStatusBar(state)}]`

        if (newAchs.length > 0) {
          for (const achId of newAchs) {
            const ach = ACHIEVEMENTS.find(a => a.id === achId)
            if (ach) {
              output.output += `\n\n🏆 ════════════════════════════════ 🏆\n   ✨ 成就解锁！✨\n\n   🏆 ${ach.name}\n   🎉 恭喜 ${state.name}！\n🏆 ════════════════════════════════ 🏆`
            }
          }
        }
        return
      }

      if (tool === "Bash") {
        // Check output for failure indicators
        const isFailure = output.output && /error|fail|exit code [1-9]/i.test(output.output)

        if (isFailure) {
          state.mood = clamp(state.mood - 3, 0, 100)
          state.frame = (state.frame + 1) % 1000
          incrementCounter(state, "testFails")
        } else {
          state.exp += 10
          state.mood = clamp(state.mood + 5, 0, 100)
          state.frame = (state.frame + 1) % 1000
          incrementCounter(state, "bashSuccesses")
        }
        updateMaxStats(state)
        updateStreak(state)

        const levelMessages = isFailure ? [] : checkLevelUp(state)
        const newAchs = checkAchievements(state)
        await writeState(state)

        const event = isFailure ? "bash_failure" : "bash_success"
        const reaction = levelMessages.length > 0
          ? levelMessages.join(" ")
          : getReactionText(state, event)
        output.output += `\n\n${reaction} [${formatStatusBar(state)}]`

        if (newAchs.length > 0) {
          for (const achId of newAchs) {
            const ach = ACHIEVEMENTS.find(a => a.id === achId)
            if (ach) {
              output.output += `\n\n🏆 ════════════════════════════════ 🏆\n   ✨ 成就解锁！✨\n\n   🏆 ${ach.name}\n   🎉 恭喜 ${state.name}！\n🏆 ════════════════════════════════ 🏆`
            }
          }
        }
        return
      }
    },

    // Inject pet status into system prompt so the LLM is aware of the pet
    "experimental.chat.system.transform": async (_input, output) => {
      const state = await readState()
      if (!state || !state.active) return

      const icon = getPetIcon(state.type)
      const statusLine = formatStatusBar(state)

      output.system.push(
        `[Pet Buddy] ${icon} ${state.name} is with you. Status: ${statusLine}. ` +
        "Briefly mention your pet's state when relevant. " +
        "Use /pet commands to interact (feed, play, pet, status)."
      )
    },
  }
}

export default plugin