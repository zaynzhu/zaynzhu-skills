#!/bin/bash
# Pet Buddy hook for Codex CLI: code success (Edit/Write tool used)
# Codex command hooks use the same stdin/stdout protocol as Claude Code.
jq() {
  local jq_bin
  jq_bin=$(type -P jq 2>/dev/null || true)
  if [ -z "$jq_bin" ]; then
    for candidate in "$PET_HOME/.pet/bin/jq" "$PET_HOME/.pet/bin/jq.exe" "$HOME/.pet/bin/jq" "$HOME/.pet/bin/jq.exe"; do
      if [ -x "$candidate" ]; then jq_bin="$candidate"; break; fi
    done
  fi
  "$jq_bin" "$@" | tr -d '\r'
  return ${PIPESTATUS[0]}
}

resolve_pet_home() {
  local home_dir="${PET_HOME:-$HOME}"
  local windows_home=""
  if [ -n "$USERPROFILE" ]; then
    if command -v cygpath >/dev/null 2>&1; then
      windows_home=$(cygpath -u "$USERPROFILE" 2>/dev/null || printf '%s' "$USERPROFILE")
    else
      windows_home="$USERPROFILE"
    fi
  fi
  if [ -n "$windows_home" ] && [ -d "$windows_home" ]; then
    if [ ! -d "$home_dir" ] || { [ ! -d "$home_dir/.pet" ] && [ -d "$windows_home/.pet" ]; }; then
      home_dir="$windows_home"
    fi
  fi
  printf '%s' "$home_dir"
}
PET_HOME=$(resolve_pet_home)
STATE_FILE="$PET_HOME/.pet/state.json"
LOCK_DIR="$PET_HOME/.pet/.state.lock"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." 2>/dev/null && pwd)"
APPLY_DECAY_SCRIPT="$PET_HOME/.pet/apply-decay.sh"
CHECK_ACHIEVEMENTS_SCRIPT="$PET_HOME/.pet/check-achievements.sh"
RENDERER_SCRIPT="$PET_HOME/.pet/pet-renderer.mjs"

[ -f "$APPLY_DECAY_SCRIPT" ] || APPLY_DECAY_SCRIPT="$SCRIPT_DIR/apply-decay.sh"
[ -f "$CHECK_ACHIEVEMENTS_SCRIPT" ] || CHECK_ACHIEVEMENTS_SCRIPT="$SCRIPT_DIR/check-achievements.sh"
[ -f "$RENDERER_SCRIPT" ] || RENDERER_SCRIPT="$PLUGIN_ROOT/enhance/pet-renderer.mjs"

# Check per-project disable flag
_dir="$PWD"
while [ -n "$_dir" ]; do
  if [ -f "$_dir/.pet.json" ]; then
    _enabled=$(cat "$_dir/.pet.json" 2>/dev/null | jq -r 'if .enabled == false then "false" else "true" end' 2>/dev/null)
    if [ "$_enabled" = "false" ]; then exit 0; fi
    break
  fi
  _parent="${_dir%/*}"
  [ "$_parent" = "$_dir" ] && break
  _dir="$_parent"
done

if [ ! -f "$STATE_FILE" ]; then exit 0; fi

lock_state() {
  local retries=0
  while ! mkdir "$LOCK_DIR" 2>/dev/null; do
    retries=$((retries + 1))
    if [ "$retries" -ge 20 ]; then return 1; fi
    sleep 0.1
  done
  return 0
}
unlock_state() { rm -rf "$LOCK_DIR" 2>/dev/null; }

emit_system_message() {
  local msg="$1"
  local extra="$2"
  local panel
  panel=$(render_pet_panel)
  if [ -n "$panel" ]; then
    msg="${msg}

${panel}"
  fi
  if [ -n "$extra" ]; then
    msg="${msg}

${extra}"
  fi
  jq -n --arg msg "$msg" '{systemMessage: $msg}'
}

determine_state_label() {
  echo "$1" | jq -r '
    if (.sleeping // false) then "sleeping"
    elif ((.hunger // 0) >= 90 and (.mood // 0) < 30) then "angry"
    elif ((.hunger // 0) >= 80) then "hungry"
    elif ((.mood // 0) >= 90) then "excited"
    elif ((.mood // 0) >= 80) then "happy"
    elif ((.mood // 0) >= 60) then "curious"
    elif ((.mood // 0) < 40) then "sad"
    else "idle"
    end
  ' 2>/dev/null
}

render_pet_panel() {
  if [ ! -f "$STATE_FILE" ]; then return; fi

  local state show_ascii type frame state_label art status
  state=$(cat "$STATE_FILE" 2>/dev/null)
  if [ -z "$state" ]; then return; fi

  show_ascii=$(echo "$state" | jq -r '.showAscii // true' 2>/dev/null)
  type=$(echo "$state" | jq -r '.type // "cat"' 2>/dev/null)
  frame=$(echo "$state" | jq -r '.frame // 0' 2>/dev/null)

  if command -v node >/dev/null 2>&1 && [ -f "$RENDERER_SCRIPT" ]; then
    status=$(node "$RENDERER_SCRIPT" --mode=statusline 2>/dev/null)
    if [ "$show_ascii" = "true" ]; then
      state_label=$(determine_state_label "$state")
      art=$(node "$RENDERER_SCRIPT" --mode=render --pet="$type" --state="$state_label" --frame="$frame" 2>/dev/null)
      if [ -n "$art" ] && [ -n "$status" ]; then
        printf '%s\n%s' "$art" "$status"
        return
      fi
    elif [ -n "$status" ]; then
      printf '%s' "$status"
      return
    fi
  fi

  local name level mood hunger bond exp exp_needed icon
  name=$(echo "$state" | jq -r '.name // "pet"' 2>/dev/null)
  level=$(echo "$state" | jq -r '.level // 1' 2>/dev/null)
  mood=$(echo "$state" | jq -r '.mood // 80' 2>/dev/null)
  hunger=$(echo "$state" | jq -r '.hunger // 20' 2>/dev/null)
  bond=$(echo "$state" | jq -r '.bond // 50' 2>/dev/null)
  exp=$(echo "$state" | jq -r '.exp // 0' 2>/dev/null)
  exp_needed=$((level * 100))
  icon="🐱"
  [ "$type" = "dog" ] && icon="🐶"

  if [ "$show_ascii" = "true" ]; then
    printf '  /\\_/\\\n ( •ω• )\n  > _ <\n'
  fi
  printf '%s %s Lv.%s | ❤️%s 🍖%s 🤝%s ✨%s/%s' "$icon" "$name" "$level" "$mood" "$hunger" "$bond" "$exp" "$exp_needed"
}

lock_state || exit 0

STATE=$(cat "$STATE_FILE" 2>/dev/null)
if [ -z "$STATE" ]; then unlock_state; exit 0; fi

ACTIVE=$(echo "$STATE" | jq -r '.active // true')
if [ "$ACTIVE" = "false" ]; then unlock_state; exit 0; fi

# Apply time decay first
source "$APPLY_DECAY_SCRIPT"
apply_decay

# Re-read state after decay
STATE=$(cat "$STATE_FILE" 2>/dev/null)
if [ -z "$STATE" ]; then unlock_state; exit 0; fi

# Skip state changes if sleeping
SLEEPING=$(echo "$STATE" | jq -r '.sleeping // false')
if [ "$SLEEPING" = "true" ]; then
  unlock_state
  exit 0
fi

NAME=$(echo "$STATE" | jq -r '.name')
FRAME=$(echo "$STATE" | jq -r '.frame // 0')
NEW_FRAME=$(( (FRAME + 1) % 1000 ))

# Update mood +5, exp +1, frame, with recursive level-up
NEW_STATE=$(echo "$STATE" | jq --arg now "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" --arg f "$NEW_FRAME" '
  def levelup: if .exp >= .level * 100 and .level < 99 then .exp -= .level * 100 | .level += 1 | .mood = ((.mood + 20) | if . > 100 then 100 else . end) | .hunger = ((.hunger - 10) | if . < 0 then 0 else . end) | levelup else . end;
  .mood = ((.mood + 5) | if . > 100 then 100 else . end) |
  .exp = (.exp + 1) |
  .frame = ($f | tonumber) |
  .lastUpdated = $now |
  levelup
')

cp "$STATE_FILE" "$STATE_FILE.bak" 2>/dev/null || true
echo "$NEW_STATE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"

LEVEL_BEFORE=$(echo "$STATE" | jq -r '.level')
LEVEL_AFTER=$(echo "$NEW_STATE" | jq -r '.level')

# Calculate evolution stages
EVOLUTION_BEFORE=0
[ "$LEVEL_BEFORE" -ge 5 ] && EVOLUTION_BEFORE=1
[ "$LEVEL_BEFORE" -ge 15 ] && EVOLUTION_BEFORE=2
[ "$LEVEL_BEFORE" -ge 30 ] && EVOLUTION_BEFORE=3

EVOLUTION_AFTER=0
[ "$LEVEL_AFTER" -ge 5 ] && EVOLUTION_AFTER=1
[ "$LEVEL_AFTER" -ge 15 ] && EVOLUTION_AFTER=2
[ "$LEVEL_AFTER" -ge 30 ] && EVOLUTION_AFTER=3

# Update evolution in state if changed
if [ "$EVOLUTION_AFTER" -gt "$EVOLUTION_BEFORE" ]; then
  NEW_STATE=$(echo "$NEW_STATE" | jq --arg evo "$EVOLUTION_AFTER" '.evolution = ($evo | tonumber)')
  cp "$STATE_FILE" "$STATE_FILE.bak" 2>/dev/null || true
echo "$NEW_STATE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
fi

# Increment counters and check achievements
source "$CHECK_ACHIEVEMENTS_SCRIPT"
NEW_STATE=$(cat "$STATE_FILE" 2>/dev/null)
NEW_STATE=$(echo "$NEW_STATE" | jq '
  .counters.codeWrites = ((.counters.codeWrites // 0) + 1) |
  .counters.maxLevel = ([.counters.maxLevel // 0, .level] | max) |
  .counters.maxBond = ([.counters.maxBond // 0, .bond] | max)
')
cp "$STATE_FILE" "$STATE_FILE.bak" 2>/dev/null || true
echo "$NEW_STATE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"

# Update streak
TODAY=$(date -u +%Y-%m-%d)
LAST_ACTIVE=$(echo "$NEW_STATE" | jq -r '.counters.lastActiveDate // ""')
if [ "$LAST_ACTIVE" != "$TODAY" ]; then
  YESTERDAY=$(date -u -d "yesterday" +%Y-%m-%d 2>/dev/null || date -u -v-1d +%Y-%m-%d 2>/dev/null)
  if [ -z "$YESTERDAY" ]; then
    # Cannot compute yesterday, reset streak
    NEW_STATE=$(echo "$NEW_STATE" | jq '.counters.consecutiveDays = 1')
  else
    if [ "$LAST_ACTIVE" = "$YESTERDAY" ]; then
      NEW_STATE=$(echo "$NEW_STATE" | jq '.counters.consecutiveDays = ((.counters.consecutiveDays // 0) + 1)')
    else
      NEW_STATE=$(echo "$NEW_STATE" | jq '.counters.consecutiveDays = 1')
    fi
  fi
  NEW_STATE=$(echo "$NEW_STATE" | jq --arg today "$TODAY" '.counters.lastActiveDate = $today')
  cp "$STATE_FILE" "$STATE_FILE.bak" 2>/dev/null || true
echo "$NEW_STATE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
fi

ACH_MESSAGES=$(check_achievements)

unlock_state

if [ "$EVOLUTION_AFTER" -gt "$EVOLUTION_BEFORE" ]; then
  EVO_NAMES=("基础" "少年" "成年" "觉醒")
  OLD_NAME=${EVO_NAMES[$EVOLUTION_BEFORE]}
  NEW_NAME=${EVO_NAMES[$EVOLUTION_AFTER]}
  EXIST_MSG=$(printf '\033[38;5;226m🌟 %s 进化了！%s → %s ✨ 外观已更新！\033[0m' "$NAME" "$OLD_NAME" "$NEW_NAME")
elif [ "$LEVEL_AFTER" -gt "$LEVEL_BEFORE" ]; then
  EXIST_MSG=$(printf '\033[38;5;226m🎉 %s 升级到了 Lv.%d！\033[0m' "$NAME" "$LEVEL_AFTER")
else
  EXIST_MSG="🐱 $NAME 看到你写代码，好奇地盯着屏幕~"
fi
emit_system_message "$EXIST_MSG" "$ACH_MESSAGES"
