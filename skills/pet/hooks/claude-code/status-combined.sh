#!/bin/bash
# Pet Buddy status line - dynamic append mode with frame cycling
# Reads original statusLine command from settings.json, executes it,
# then appends pet status with frame-based emoji/description cycling.

# Auto-detect settings.json location across platforms
SETTINGS_FILE=""
for candidate in "$HOME/.claude/settings.json" "$HOME/.config/claude/settings.json" "$APPDATA/claude/settings.json"; do
  if [ -f "$candidate" ]; then
    SETTINGS_FILE="$candidate"
    break
  fi
done

STATE_FILE="$HOME/.pet/state.json"
ENHANCE_SCRIPT="$HOME/.pet/pet-renderer.mjs"

# --- Per-project config check ---
# Walk up from PWD looking for .pet.json
is_pet_enabled() {
  local dir="$PWD"
  while [ -n "$dir" ]; do
    if [ -f "$dir/.pet.json" ]; then
      local enabled
      enabled=$(jq -r 'if .enabled == false then "false" else "true" end' "$dir/.pet.json" 2>/dev/null)
      [ "$enabled" = "false" ] && return 1
      return 0
    fi
    dir="${dir%/*}"
  done
  return 0
}

PET_ENABLED=true
is_pet_enabled || PET_ENABLED=false

# --- Part 1: Run original statusLine command ---
ORIGINAL_OUTPUT=""
ORIGINAL_CMD=""

# Priority 1: Read from our saved original command file
ORIG_CMD_FILE="$HOME/.pet/original-statusline-cmd.txt"
if [ -f "$ORIG_CMD_FILE" ]; then
  ORIGINAL_CMD=$(cat "$ORIG_CMD_FILE" 2>/dev/null)
fi

# Priority 2: If no saved file, try reading from settings.json (skip our own script)
if [ -z "$ORIGINAL_CMD" ] && [ -f "$SETTINGS_FILE" ]; then
  SETTINGS_CMD=$(jq -r '.statusLine.command // empty' "$SETTINGS_FILE" 2>/dev/null)
  if [ -n "$SETTINGS_CMD" ] && ! echo "$SETTINGS_CMD" | grep -q "status-combined"; then
    ORIGINAL_CMD="$SETTINGS_CMD"
  fi
fi

# Execute the original command if found
if [ -n "$ORIGINAL_CMD" ]; then
  ORIGINAL_OUTPUT=$(eval "$ORIGINAL_CMD" 2>/dev/null)
fi

# --- Part 2: Build pet status (skip if disabled for this project) ---
PET_OUTPUT=""
ENHANCE_MODE=false

if [ "$PET_ENABLED" = "false" ]; then
  # Project has pet disabled, skip pet rendering
  :
else

# Try Node.js enhance mode first
if command -v node >/dev/null 2>&1 && [ -f "$ENHANCE_SCRIPT" ]; then
  ENHANCE_OUTPUT=$(node "$ENHANCE_SCRIPT" --mode=statusline 2>/dev/null)
  if [ $? -eq 0 ] && [ -n "$ENHANCE_OUTPUT" ]; then
    PET_OUTPUT="$ENHANCE_OUTPUT"
    ENHANCE_MODE=true
  fi
fi

# Bash fallback for pet status
if [ "$ENHANCE_MODE" = "false" ]; then
if [ -f "$STATE_FILE" ]; then
  STATE=$(cat "$STATE_FILE" 2>/dev/null)
  if [ -n "$STATE" ]; then
    ACTIVE=$(echo "$STATE" | jq -r '.active // true')
    if [ "$ACTIVE" = "false" ]; then
      NAME=$(echo "$STATE" | jq -r '.name // "pet"')
      PET_OUTPUT="💤 $NAME sleeping  /\_/\  ( -.- )  > v <"
    else
      NAME=$(echo "$STATE" | jq -r '.name // "unknown"')
      TYPE=$(echo "$STATE" | jq -r '.type // "cat"')
      LEVEL=$(echo "$STATE" | jq -r '.level // 1')
      MOOD=$(echo "$STATE" | jq -r '.mood // 80')
      HUNGER=$(echo "$STATE" | jq -r '.hunger // 20')
      BOND=$(echo "$STATE" | jq -r '.bond // 50')
      EXP=$(echo "$STATE" | jq -r '.exp // 0')
      FRAME=$(echo "$STATE" | jq -r '.frame // 0')

      # Determine state label by priority (1=highest, 12=lowest)
      # Use elif chain so first match wins
      STATE_LABEL="idle"
      if [ "$HUNGER" -ge 90 ] && [ "$MOOD" -lt 30 ]; then
        STATE_LABEL="angry"
      elif [ "$HUNGER" -ge 80 ]; then
        STATE_LABEL="hungry"
      elif [ "$MOOD" -ge 90 ]; then
        STATE_LABEL="excited"
      elif [ "$MOOD" -ge 80 ]; then
        STATE_LABEL="happy"
      elif [ "$MOOD" -lt 40 ]; then
        STATE_LABEL="sad"
      elif [ "$MOOD" -ge 60 ]; then
        STATE_LABEL="curious"
      fi
      # Note: eating/playing/petting are interactive states set by skill, not by thresholds

      # Emoji and description cycling per state
      ICON="🐱"
      [ "$TYPE" = "dog" ] && ICON="🐶"

      case "$STATE_LABEL" in
        happy)   EMOJIS=("😊" "😸" "😻"); DESCS=("正在优雅地舔爪子" "歪着头看你" "慢慢眨了眨眼" "尾巴轻轻摆动") ;;
        excited) EMOJIS=("🤩" "✨" "🤩"); DESCS=("兴奋地跑来跑去" "眼睛亮晶晶的" "在你身边转圈" "开心地叫个不停") ;;
        curious) EMOJIS=("👀" "🧐" "👀"); DESCS=("歪着头看你写代码" "凑近屏幕闻了闻" "盯着光标看" "轻轻拍了拍键盘") ;;
        idle)    EMOJIS=("😺" "😻" "😺"); DESCS=("趴在一旁打盹" "歪着头看屏幕" "舔了舔爪子" "伸了个懒腰") ;;
        sad)     EMOJIS=("😿" "😥" "😿"); DESCS=("蜷缩在角落耳朵耷拉着" "轻轻叫了一声" "低头看着地面" "尾巴无力地垂着") ;;
        hungry)  EMOJIS=("🥺" "😿" "🥺"); DESCS=("用爪子轻轻拍你的手" "在食碗旁走来走去" "可怜地看着你" "小声叫唤") ;;
        angry)   EMOJIS=("😾" "😠" "😾"); DESCS=("背弓起来发出嘶嘶声" "用爪子拍了你一下" "拒绝看你" "尾巴炸毛") ;;
        confused) EMOJIS=("😹" "🤔" "😹"); DESCS=("歪头看着你" "眨了眨眼" "在原地转了一圈" "用爪子碰了碰你的手") ;;
        sleepy)  EMOJIS=("😴" "💤" "😴"); DESCS=("安静地睡着了" "打了个哈欠" "眼皮越来越重" "蜷成一团") ;;
        eating)  EMOJIS=("😋" "😸" "😋"); DESCS=("正在吃东西" "小口地品尝" "吃完舔了舔嘴" "满意地眯起眼") ;;
        playing) EMOJIS=("🎾" "😸" "🎾"); DESCS=("追着光标跑" "扑向你的手指" "抓住了逗猫棒" "兴奋地蹦来蹦去") ;;
        petting) EMOJIS=("😻" "💕" "😻"); DESCS=("发出满足的呼噜声" "眯着眼享受" "用头蹭你的手" "身体软绵绵的") ;;
        *)       EMOJIS=("😺" "😺" "😺"); DESCS=("...") ;;
      esac

      # Dog overrides
      if [ "$TYPE" = "dog" ]; then
        case "$STATE_LABEL" in
          happy)   EMOJIS=("😊" "🐶" "😄"); DESCS=("尾巴摇得快要飞起来了" "开心地蹭你的腿" "眼睛亮亮地看着你" "兴奋地转圈") ;;
          excited) EMOJIS=("🤩" "✨" "🤩"); DESCS=("疯狂地摇尾巴" "围着你转圈圈" "高兴得跳起来" "汪汪汪叫个不停") ;;
          curious) EMOJIS=("👀" "🐕" "👀"); DESCS=("鼻子凑过来闻你的代码" "歪着头看你" "发现了新东西" "用爪子拍了拍键盘") ;;
          idle)    EMOJIS=("🐶" "😌" "🐶"); DESCS=("趴在脚边安静地陪着你" "用鼻子蹭了蹭你的手" "打了个哈欠" "歪着头看你") ;;
          sad)     EMOJIS=("😢" "🥺" "😢"); DESCS=("耷拉着耳朵默默看着你" "蜷成一团不动" "小声地呜了一声" "低着头") ;;
          hungry)  EMOJIS=("🥺" "🍖" "🥺"); DESCS=("用湿漉漉的鼻子蹭你的手" "在食碗旁焦急地转圈" "可怜巴巴地看着你" "小声汪汪叫") ;;
          angry)   EMOJIS=("😠" "🐕‍🦺" "😠"); DESCS=("低吼了一声" "背上的毛竖起来" "不愿意看你" "汪汪叫了两声") ;;
          confused) EMOJIS=("🤔" "🐶" "🤔"); DESCS=("歪头看着你" "眨了眨眼" "在原地转了一圈" "用鼻子推了推你的手") ;;
          sleepy)  EMOJIS=("😴" "💤" "😴"); DESCS=("蜷成一团偶尔抽动一下腿" "打了个大哈欠" "眼睛快闭上了" "呼呼睡着了") ;;
          eating)  EMOJIS=("🍖" "😋" "🍖"); DESCS=("狼吞虎咽尾巴还在摇" "大口大口地吃" "吃完舔了舔嘴" "满足地打了个饱嗝") ;;
          playing) EMOJIS=("🎾" "🐶" "🎾"); DESCS=("兴奋地跑来跑去" "叼着球跑回来" "绕着你转圈" "跳起来想接飞盘") ;;
          petting) EMOJIS=("💕" "😊" "💕"); DESCS=("肚皮朝上享受地眯着眼" "尾巴还在轻轻摇" "用头蹭你的手掌" "发出满足的哼哼声") ;;
        esac
      fi

      EMOJI_IDX=$(( FRAME % ${#EMOJIS[@]} ))
      EMOJI="${EMOJIS[$EMOJI_IDX]}"
      DESC_IDX=$(( FRAME % ${#DESCS[@]} ))
      DESC="${DESCS[$DESC_IDX]}"

      EXP_NEEDED=$((LEVEL * 100))

      # Unique attribute display
      UNIQUE_DISPLAY=""
      REGISTRY_FILE="$HOME/.pet/pets/registry.json"
      if [ -f "$REGISTRY_FILE" ]; then
        U_FIELD=$(jq -r --arg t "$TYPE" '.types[$t].unique.field // empty' "$REGISTRY_FILE" 2>/dev/null)
        U_ICON=$(jq -r --arg t "$TYPE" '.types[$t].unique.icon // empty' "$REGISTRY_FILE" 2>/dev/null)
        U_DEFAULT=$(jq -r --arg t "$TYPE" '.types[$t].unique.default // 50' "$REGISTRY_FILE" 2>/dev/null)
        U_DECAY=$(jq -r --arg t "$TYPE" '.types[$t].unique.decayRate // 0' "$REGISTRY_FILE" 2>/dev/null)
        U_GROW=$(jq -r --arg t "$TYPE" '.types[$t].unique.growRate // 0' "$REGISTRY_FILE" 2>/dev/null)
        if [ -n "$U_FIELD" ] && { [ "$U_DECAY" -gt 0 ] 2>/dev/null || [ "$U_GROW" -gt 0 ] 2>/dev/null; }; then
          U_VALUE=$(echo "$STATE" | jq -r --arg f "$U_FIELD" --arg d "$U_DEFAULT" '.unique[$f] // ($d | tonumber)')
          UNIQUE_DISPLAY=" ${U_ICON}${U_VALUE}"
        fi
      fi

      PET_OUTPUT="$ICON $NAME Lv.$LEVEL $EMOJI | ❤️$MOOD 🍖$HUNGER 🤝$BOND${UNIQUE_DISPLAY} ✨$EXP/$EXP_NEEDED $DESC"

      # Increment frame and save (modulo 1000 to prevent overflow)
      NEW_FRAME=$(( (FRAME + 1) % 1000 ))
      NEW_STATE=$(echo "$STATE" | jq --arg f "$NEW_FRAME" '.frame = ($f | tonumber)')
      LOCK_DIR="$HOME/.pet/.state.lock"
      retries=0; while ! mkdir "$LOCK_DIR" 2>/dev/null; do retries=$((retries+1)); [ "$retries" -ge 20 ] && break; sleep 0.1; done
      echo "$NEW_STATE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
      rm -rf "$LOCK_DIR" 2>/dev/null
    fi
  fi
fi
  # Strip any color markers from Bash fallback output
  PET_OUTPUT=$(echo "$PET_OUTPUT" | sed 's/\[[0-9]*\]//g')
fi # end ENHANCE_MODE check
fi # end PET_ENABLED check

# --- Part 3: Combine outputs ---
if [ -n "$ORIGINAL_OUTPUT" ] && [ -n "$PET_OUTPUT" ]; then
  echo "$ORIGINAL_OUTPUT  │  $PET_OUTPUT"
elif [ -n "$ORIGINAL_OUTPUT" ]; then
  echo "$ORIGINAL_OUTPUT"
elif [ -n "$PET_OUTPUT" ]; then
  echo "$PET_OUTPUT"
else
  echo "🐾 /pet to adopt a companion"
fi
