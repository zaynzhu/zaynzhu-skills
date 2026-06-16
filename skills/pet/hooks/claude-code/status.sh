#!/bin/bash
# Pet Buddy status line script for Claude Code
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

if [ ! -f "$STATE_FILE" ]; then
  echo "🐾 /pet to adopt a companion"
  exit 0
fi

STATE=$(cat "$STATE_FILE" 2>/dev/null)
if [ -z "$STATE" ]; then
  echo "🐾 /pet to adopt a companion"
  exit 0
fi

NAME=$(echo "$STATE" | jq -r '.name // "unknown"')
TYPE=$(echo "$STATE" | jq -r '.type // "cat"')
LEVEL=$(echo "$STATE" | jq -r '.level // 1')
MOOD=$(echo "$STATE" | jq -r '.mood // 80')
HUNGER=$(echo "$STATE" | jq -r '.hunger // 20')
BOND=$(echo "$STATE" | jq -r '.bond // 50')
EXP=$(echo "$STATE" | jq -r '.exp // 0')
ACTIVE=$(echo "$STATE" | jq -r '.active // true')

if [ "$ACTIVE" = "false" ]; then
  echo "💤 $NAME (sleeping) /pet on to wake"
  exit 0
fi

# Determine mood emoji using jq comparisons
FACE=$(echo "$STATE" | jq -r '
  if .hunger >= 80 then "🍖"
  elif .mood >= 80 then "😊"
  elif .mood < 40 then "😢"
  elif .mood >= 60 then "👀"
  else "😺" end
')

REGISTRY_FILE="$PET_HOME/.pet/pets/registry.json"
ICON="🐱"
if [ -f "$REGISTRY_FILE" ]; then
  REG_ICON=$(cat "$REGISTRY_FILE" 2>/dev/null | jq -r --arg t "$TYPE" '.types[$t].icon // empty' 2>/dev/null)
  [ -n "$REG_ICON" ] && ICON="$REG_ICON"
else
  [ "$TYPE" = "dog" ] && ICON="🐶"
fi

EXP_NEEDED=$((LEVEL * 100))

echo "$ICON $NAME Lv.$LEVEL $FACE | ❤️$MOOD 🍖$HUNGER 🤝$BOND ✨$EXP/$EXP_NEEDED"
