#!/bin/bash
# Pet Buddy: shared time decay function
# Source this file and call apply_decay to update hunger/bond based on elapsed time.
# Also increments the frame counter for animation cycling.
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
REGISTRY_FILE="$PET_HOME/.pet/pets/registry.json"

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
    LAST_TS=$(date -u -d "$LAST" +%s 2>/dev/null || date -u -j -f "%Y-%m-%d %H:%M:%S" "$LAST" +%s 2>/dev/null || echo "0")
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

  local SLEEPING=$(echo "$STATE" | jq -r '.sleeping // false')
  local HUNGER_RATE=5
  if [ "$SLEEPING" = "true" ]; then HUNGER_RATE=2; fi

  local NEW_STATE=$(echo "$STATE" | jq --arg hours "$ELAPSED_HOURS" --arg days "$ELAPSED_DAYS" --arg now "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" --arg f "$NEW_FRAME" --arg rate "$HUNGER_RATE" '
    .hunger = ((.hunger + ($rate | tonumber) * ($hours | tonumber)) | if . > 100 then 100 elif . < 0 then 0 else . end) |
    .bond = ((.bond - 1 * ($days | tonumber)) | if . < 0 then 0 elif . > 100 then 100 else . end) |
    .frame = ($f | tonumber) |
    .lastUpdated = $now
  ')

  # If sleeping, skip bond decay by restoring pre-decay value
  if [ "$SLEEPING" = "true" ]; then
    local BOND_BEFORE=$(echo "$STATE" | jq '.bond // 50')
    NEW_STATE=$(echo "$NEW_STATE" | jq --argjson bond "$BOND_BEFORE" '.bond = $bond')
  fi

  echo "$NEW_STATE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"

  # Apply unique attribute decay if registry exists (use fractional hours for sub-hour precision)
  if [ -f "$REGISTRY_FILE" ] && [ "$ELAPSED" -gt 0 ]; then
    local PET_TYPE=$(echo "$NEW_STATE" | jq -r '.type // "cat"')
    local DECAY_RATE=$(cat "$REGISTRY_FILE" 2>/dev/null | jq -r --arg t "$PET_TYPE" '.types[$t].unique.decayRate // 0' 2>/dev/null)
    local FIELD=$(cat "$REGISTRY_FILE" 2>/dev/null | jq -r --arg t "$PET_TYPE" '.types[$t].unique.field // empty' 2>/dev/null)
    local RANGE_MIN=$(cat "$REGISTRY_FILE" 2>/dev/null | jq -r --arg t "$PET_TYPE" '.types[$t].unique.range[0] // 0' 2>/dev/null)
    local RANGE_MAX=$(cat "$REGISTRY_FILE" 2>/dev/null | jq -r --arg t "$PET_TYPE" '.types[$t].unique.range[1] // 100' 2>/dev/null)
    local DEFAULT=$(cat "$REGISTRY_FILE" 2>/dev/null | jq -r --arg t "$PET_TYPE" '.types[$t].unique.default // 50' 2>/dev/null)

    if [ -n "$FIELD" ] && [ "$DECAY_RATE" -gt 0 ] 2>/dev/null; then
      NEW_STATE=$(echo "$NEW_STATE" | jq \
        --arg field "$FIELD" \
        --arg rate "$DECAY_RATE" \
        --arg seconds "$ELAPSED" \
        --arg min "$RANGE_MIN" \
        --arg max "$RANGE_MAX" \
        --arg default "$DEFAULT" '
        (.unique[$field] // ($default | tonumber)) as $cur |
        .unique[$field] = ([$cur - ($rate | tonumber) * ($seconds | tonumber) / 3600, ($min | tonumber)] | max |
                          if . > ($max | tonumber) then ($max | tonumber) else . end)
      ')
      echo "$NEW_STATE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
    fi
  fi

  return 0
}
