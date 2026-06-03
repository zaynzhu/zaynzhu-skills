#!/bin/bash
# Pet Buddy hook for Codex CLI: bash result (command success/failure)
# Codex PostToolUse hook reads tool_name and tool_response from stdin JSON.
# Output: {"systemMessage": "..."} on stdout.
STATE_FILE="$HOME/.pet/state.json"
LOCK_DIR="$HOME/.pet/.state.lock"

# Check per-project disable flag
_dir="$PWD"
while [ -n "$_dir" ]; do
  if [ -f "$_dir/.pet.json" ]; then
    _enabled=$(jq -r '.enabled // true' "$_dir/.pet.json" 2>/dev/null)
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

lock_state || exit 0

STATE=$(cat "$STATE_FILE" 2>/dev/null)
if [ -z "$STATE" ]; then unlock_state; exit 0; fi

ACTIVE=$(echo "$STATE" | jq -r '.active // true')
if [ "$ACTIVE" = "false" ]; then unlock_state; exit 0; fi

# Apply time decay first
source "$HOME/.pet/apply-decay.sh"
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

# Read exit code from stdin JSON
# Codex PostToolUse input: {"tool_name":"Bash", "tool_response":{...}, "tool_input":{...}}
# tool_response structure is unconstrained — try common exit code field names
INPUT=$(cat)
EXIT_CODE=$(echo "$INPUT" | jq -r '
  (.tool_response.exit_code // .tool_response.exitCode // .exit_code // 0)
' 2>/dev/null)
NOW=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)

if [ "$EXIT_CODE" = "0" ] || [ -z "$EXIT_CODE" ]; then
  NEW_STATE=$(echo "$STATE" | jq --arg now "$NOW" --arg f "$NEW_FRAME" '
    def levelup: if .exp >= .level * 100 and .level < 99 then .exp -= .level * 100 | .level += 1 | .mood = ((.mood + 20) | if . > 100 then 100 else . end) | .hunger = ((.hunger - 10) | if . < 0 then 0 else . end) | levelup else . end;
    .mood = ((.mood + 5) | if . > 100 then 100 else . end) |
    .exp = (.exp + 10) |
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
  source "$HOME/.pet/check-achievements.sh"
  NEW_STATE=$(cat "$STATE_FILE" 2>/dev/null)
  NEW_STATE=$(echo "$NEW_STATE" | jq '
    .counters.bashSuccesses = ((.counters.bashSuccesses // 0) + 1) |
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
    EXIST_MSG="🐱 $NAME 高兴地摇了摇尾巴！测试通过了！🎉"
  fi
  echo "{\"systemMessage\": \"$EXIST_MSG\"}"
  if [ -n "$ACH_MESSAGES" ]; then
    echo "$ACH_MESSAGES"
  fi
else
  NEW_STATE=$(echo "$STATE" | jq --arg now "$NOW" --arg f "$NEW_FRAME" '
    .mood = ((.mood - 3) | if . < 0 then 0 else . end) |
    .frame = ($f | tonumber) |
    .lastUpdated = $now
  ')
  cp "$STATE_FILE" "$STATE_FILE.bak" 2>/dev/null || true
  echo "$NEW_STATE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"

  # Increment failure counter
  NEW_STATE=$(cat "$STATE_FILE" 2>/dev/null)
  NEW_STATE=$(echo "$NEW_STATE" | jq '.counters.testFails = ((.counters.testFails // 0) + 1)')
  cp "$STATE_FILE" "$STATE_FILE.bak" 2>/dev/null || true
  echo "$NEW_STATE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"

  # Check achievements
  source "$HOME/.pet/check-achievements.sh"
  ACH_MESSAGES=$(check_achievements)

  unlock_state

  echo "{\"systemMessage\": \"🐱 $NAME 安静地陪在你身边...别灰心！💪\"}"
  if [ -n "$ACH_MESSAGES" ]; then
    echo "$ACH_MESSAGES"
  fi
fi