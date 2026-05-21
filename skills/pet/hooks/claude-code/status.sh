#!/bin/bash
# Pet Buddy status line script for Claude Code
STATE_FILE="$HOME/.pet-buddy/state.json"

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

ICON="🐱"
[ "$TYPE" = "dog" ] && ICON="🐶"

EXP_NEEDED=$((LEVEL * 100))

echo "$ICON $NAME Lv.$LEVEL $FACE | ❤️$MOOD 🍖$HUNGER 🤝$BOND ✨$EXP/$EXP_NEEDED"
