#!/bin/bash
# Pet Buddy hook: bash result (command success/failure)
STATE_FILE="$HOME/.pet/state.json"
LOCK_DIR="$HOME/.pet/.state.lock"

if [ ! -f "$STATE_FILE" ]; then exit 0; fi

# Per-project config check
_dir="$PWD"; while [ -n "$_dir" ]; do
  if [ -f "$_dir/.pet.json" ]; then
    _enabled=$(jq -r 'if .enabled == false then "false" else "true" end' "$_dir/.pet.json" 2>/dev/null)
    [ "$_enabled" = "false" ] && exit 0
    break
  fi
  _dir="${_dir%/*}"
done

# mkdir-based file lock (atomic, cross-platform)
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

NAME=$(echo "$STATE" | jq -r '.name')
FRAME=$(echo "$STATE" | jq -r '.frame // 0')
NEW_FRAME=$(( (FRAME + 1) % 1000 ))

# Read exit code from stdin JSON
INPUT=$(cat)
EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_response.exitCode // 0' 2>/dev/null)
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
  echo "$NEW_STATE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"

  LEVEL_BEFORE=$(echo "$STATE" | jq -r '.level')
  LEVEL_AFTER=$(echo "$NEW_STATE" | jq -r '.level')

  unlock_state

  if [ "$LEVEL_AFTER" -gt "$LEVEL_BEFORE" ]; then
    LEVELUP_MSG=$(printf '\033[38;5;226m🎉 %s 升级到了 Lv.%d！\033[0m' "$NAME" "$LEVEL_AFTER")
    echo "{\"systemMessage\": \"$LEVELUP_MSG\"}"
  else
    echo "{\"systemMessage\": \"🐱 $NAME 高兴地摇了摇尾巴！测试通过了！🎉\"}"
  fi
else
  NEW_STATE=$(echo "$STATE" | jq --arg now "$NOW" --arg f "$NEW_FRAME" '
    .mood = ((.mood - 3) | if . < 0 then 0 else . end) |
    .frame = ($f | tonumber) |
    .lastUpdated = $now
  ')
  echo "$NEW_STATE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"

  unlock_state

  echo "{\"systemMessage\": \"🐱 $NAME 安静地陪在你身边...别灰心！💪\"}"
fi
