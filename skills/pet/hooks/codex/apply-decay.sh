#!/bin/bash
# Pet Buddy: shared time decay function
# Source this file and call apply_decay to update hunger/bond based on elapsed time.
# Also increments the frame counter for animation cycling.
STATE_FILE="$HOME/.pet/state.json"
REGISTRY_FILE="$HOME/.pet/pets/registry.json"

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

  # Apply unique attribute decay if registry exists
  if [ -f "$REGISTRY_FILE" ] && [ "$ELAPSED_HOURS" -gt 0 ]; then
    local PET_TYPE=$(echo "$NEW_STATE" | jq -r '.type // "cat"')
    local DECAY_RATE=$(jq -r --arg t "$PET_TYPE" '.types[$t].unique.decayRate // 0' "$REGISTRY_FILE" 2>/dev/null)
    local FIELD=$(jq -r --arg t "$PET_TYPE" '.types[$t].unique.field // empty' "$REGISTRY_FILE" 2>/dev/null)
    local RANGE_MIN=$(jq -r --arg t "$PET_TYPE" '.types[$t].unique.range[0] // 0' "$REGISTRY_FILE" 2>/dev/null)
    local RANGE_MAX=$(jq -r --arg t "$PET_TYPE" '.types[$t].unique.range[1] // 100' "$REGISTRY_FILE" 2>/dev/null)
    local DEFAULT=$(jq -r --arg t "$PET_TYPE" '.types[$t].unique.default // 50' "$REGISTRY_FILE" 2>/dev/null)

    if [ -n "$FIELD" ] && [ "$DECAY_RATE" -gt 0 ] 2>/dev/null; then
      NEW_STATE=$(echo "$NEW_STATE" | jq \
        --arg field "$FIELD" \
        --arg rate "$DECAY_RATE" \
        --arg hours "$ELAPSED_HOURS" \
        --arg min "$RANGE_MIN" \
        --arg max "$RANGE_MAX" \
        --arg default "$DEFAULT" '
        (.unique[$field] // ($default | tonumber)) as $cur |
        .unique[$field] = ([$cur - ($rate | tonumber) * ($hours | tonumber), ($min | tonumber)] | max |
                          if . > ($max | tonumber) then ($max | tonumber) else . end)
      ')
      echo "$NEW_STATE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
    fi
  fi

  return 0
}