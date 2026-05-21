// Pet Buddy plugin for OpenCode
// Handles tool execution events and injects pet status into system prompt.
// Deploy to: .opencode/plugins/pet-buddy.ts (project-level)
//   or: ~/.config/opencode/plugins/pet-buddy.ts (global)
//
// This plugin reads/writes ~/.pet-buddy/state.json (shared across platforms).
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

const PET_BUDDY_DIR = path.join(homedir(), ".pet-buddy")
const STATE_FILE = path.join(PET_BUDDY_DIR, "state.json")
const STATE_TMP = path.join(PET_BUDDY_DIR, "state.json.tmp")

interface PetState {
  name: string
  type: "cat" | "dog"
  mood: number
  hunger: number
  bond: number
  level: number
  exp: number
  active: boolean
  showAscii: boolean
  frame: number
  soundEnabled: boolean
  gameHighScore: number
  createdAt: string
  lastUpdated: string
  platform?: string
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

  state.hunger = clamp(state.hunger + 5 * hours, 0, 100)
  state.bond = clamp(state.bond - 1 * days, 0, 100)
  state.frame = (state.frame + 1) % 1000
}

function checkLevelUp(state: PetState): string[] {
  const messages: string[] = []

  while (state.exp >= state.level * 100 && state.level < 99) {
    state.exp -= state.level * 100
    state.level += 1
    state.mood = clamp(state.mood + 20, 0, 100)
    state.hunger = clamp(state.hunger - 10, 0, 100)
    messages.push(`🎉 ${state.name} 升级到了 Lv.${state.level}！`)
  }

  return messages
}

function getReactionText(pet: PetState, event: "code_success" | "bash_success" | "bash_failure"): string {
  const icon = pet.type === "dog" ? "🐶" : "🐱"

  if (event === "code_success") {
    return `${icon} ${pet.name} 看到你写代码，好奇地盯着屏幕~`
  }
  if (event === "bash_success") {
    return `${icon} ${pet.name} 高兴地摇了摇尾巴！测试通过了！🎉`
  }
  return `${icon} ${pet.name} 安静地陪在你身边...别灰心！💪`
}

function formatStatusBar(state: PetState): string {
  const icon = state.type === "dog" ? "🐶" : "🐱"
  const moodEmoji = state.mood >= 80 ? "😊" : state.mood >= 60 ? "😐" : "😢"
  return `${icon} ${state.name} Lv.${state.level} ${moodEmoji} | ❤️${state.mood} 🍖${state.hunger} 🤝${state.bond} ✨${state.exp}/${state.level * 100}`
}

const plugin: Plugin = async (_input) => {
  return {
    // Update pet state after tool execution and append reaction to tool output
    "tool.execute.after": async (input, output) => {
      const state = await readState()
      if (!state || !state.active) return

      applyDecay(state)

      const tool = input.tool || ""

      if (tool === "Edit" || tool === "Write") {
        state.mood = clamp(state.mood + 5, 0, 100)
        state.exp += 1
        state.frame = (state.frame + 1) % 1000

        const levelMessages = checkLevelUp(state)
        await writeState(state)

        const reaction = levelMessages.length > 0
          ? levelMessages.join(" ")
          : getReactionText(state, "code_success")
        output.output += `\n\n${reaction} [${formatStatusBar(state)}]`
        return
      }

      if (tool === "Bash") {
        // Check output for failure indicators
        const isFailure = output.output && /error|fail|exit code [1-9]/i.test(output.output)

        if (isFailure) {
          state.mood = clamp(state.mood - 3, 0, 100)
          state.frame = (state.frame + 1) % 1000
        } else {
          state.exp += 10
          state.mood = clamp(state.mood + 5, 0, 100)
          state.frame = (state.frame + 1) % 1000
        }

        const levelMessages = isFailure ? [] : checkLevelUp(state)
        await writeState(state)

        const event = isFailure ? "bash_failure" : "bash_success"
        const reaction = levelMessages.length > 0
          ? levelMessages.join(" ")
          : getReactionText(state, event)
        output.output += `\n\n${reaction} [${formatStatusBar(state)}]`
        return
      }
    },

    // Inject pet status into system prompt so the LLM is aware of the pet
    "experimental.chat.system.transform": async (_input, output) => {
      const state = await readState()
      if (!state || !state.active) return

      const icon = state.type === "dog" ? "🐶" : "🐱"
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