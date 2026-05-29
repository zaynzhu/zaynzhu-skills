#!/bin/bash
# Pet Buddy: shared time decay function
# Source this file and call apply_decay to update hunger/bond based on elapsed time.
# Also increments the frame counter for animation cycling.
STATE_FILE="$HOME/.pet/state.json"

apply_decay() {
  if [ ! -f "$STATE_FILE" ]; then return 1; fi

  local STATE=$(cat "$STATE_FILE" 2>/dev/null)
  if [ -z "$STATE" ]; then return 1; fi

  local ACTIVE=$(echo "$STATE" | jq -r '.active // true')
  if [ "$ACTIVE" = "false" ]; then return 0; fi

  local NOW=$(date -u +%s)
  local LAST=$(echo "$STATE" | jq -r '.lastUpdated // empty' | sed 's/\.[0-9]*Z$//' | sed 's/T/ /')
  local LAST_TS=0
  if [ -n "$LAST" ]; then
    LAST_TS=$(date -u -d "$LAST" +%s 2>/dev/null || echo "0")
  fi

  if [ "$LAST_TS" -eq 0 ] || [ "$LAST_TS" -gt "$NOW" ]; then
    # Invalid or future timestamp — just update lastUpdated, skip decay
    local NEW_STATE=$(echo "$STATE" | jq --arg now "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" '
      .lastUpdated = $now
    ')
    echo "$NEW_STATE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
    return 0
  fi

  local ELAPSED=$((NOW - LAST_TS))
  local ELAPSED_HOURS=$((ELAPSED / 3600))
  local ELAPSED_DAYS=$((ELAPSED / 86400))

  local FRAME=$(echo "$STATE" | jq -r '.frame // 0')
  local NEW_FRAME=$(( (FRAME + 1) % 1000 ))

  local NEW_STATE=$(echo "$STATE" | jq --arg hours "$ELAPSED_HOURS" --arg days "$ELAPSED_DAYS" --arg now "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" --arg f "$NEW_FRAME" '
    .hunger = ((.hunger + 5 * ($hours | tonumber)) | if . > 100 then 100 elif . < 0 then 0 else . end) |
    .bond = ((.bond - 1 * ($days | tonumber)) | if . < 0 then 0 elif . > 100 then 100 else . end) |
    .frame = ($f | tonumber) |
    .lastUpdated = $now
  ')

  echo "$NEW_STATE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
  return 0
}