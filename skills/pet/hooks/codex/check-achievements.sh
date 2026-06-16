#!/bin/bash
# Pet Buddy: check achievements after state update
# Source this file and call check_achievements to check for new achievements.
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

check_achievements() {
  local STATE_FILE="$PET_HOME/.pet/state.json"
  if [ ! -f "$STATE_FILE" ]; then return; fi

  local STATE=$(cat "$STATE_FILE" 2>/dev/null)
  if [ -z "$STATE" ]; then return; fi

  local NAME=$(echo "$STATE" | jq -r '.name // "pet"')
  local NEW_ACHS=$(echo "$STATE" | jq -r '
    (.counters // {}) as $c |
    (.achievements // []) as $achs |
    ($achs | map(.id)) as $unlocked |
    [
      {id: "first_code", cond: (($c.codeWrites // 0) >= 1)},
      {id: "code_100", cond: (($c.codeWrites // 0) >= 100)},
      {id: "code_1000", cond: (($c.codeWrites // 0) >= 1000)},
      {id: "code_10000", cond: (($c.codeWrites // 0) >= 10000)},
      {id: "test_pass_100", cond: (($c.bashSuccesses // 0) >= 100)},
      {id: "feature_10", cond: (($c.features // 0) >= 10)},
      {id: "first_feed", cond: (($c.feeds // 0) >= 1)},
      {id: "feed_100", cond: (($c.feeds // 0) >= 100)},
      {id: "play_100", cond: (($c.plays // 0) >= 100)},
      {id: "train_50", cond: (($c.trains // 0) >= 50)},
      {id: "streak_7", cond: (($c.consecutiveDays // 0) >= 7)},
      {id: "streak_30", cond: (($c.consecutiveDays // 0) >= 30)},
      {id: "streak_365", cond: (($c.consecutiveDays // 0) >= 365)},
      {id: "level_10", cond: (($c.maxLevel // 0) >= 10)},
      {id: "level_30", cond: (($c.maxLevel // 0) >= 30)},
      {id: "level_50", cond: (($c.maxLevel // 0) >= 50)},
      {id: "level_99", cond: (($c.maxLevel // 0) >= 99)},
      {id: "evolution_max", cond: ((.evolution // 0) >= 3)},
      {id: "bond_100", cond: (($c.maxBond // 0) >= 100)},
      {id: "first_dress", cond: (($c.dresses // 0) >= 1)},
      {id: "dress_all", cond: (($c.dressItems // []) | length >= 5)},
      {id: "game_10", cond: (($c.gamesPlayed // 0) >= 10)},
      {id: "game_high_50", cond: ((.gameHighScore // 0) >= 50)},
      {id: "game_high_100", cond: ((.gameHighScore // 0) >= 100)}
    ] |
    map(select(.cond and (.id | IN($unlocked[]) | not))) |
    map(.id) |
    .[]
  ' 2>/dev/null)

  if [ -z "$NEW_ACHS" ]; then return; fi

  local NOW=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)
  for ACH_ID in $NEW_ACHS; do
    STATE=$(echo "$STATE" | jq --arg id "$ACH_ID" --arg now "$NOW" '.achievements += [{"id": $id, "unlockedAt": $now}]')
  done
  cp "$STATE_FILE" "$STATE_FILE.bak" 2>/dev/null || true
  echo "$STATE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"

  local ACH_NAMES="first_code:初次编程 code_100:小试牛刀 code_1000:代码达人 code_10000:编程大师 test_pass_100:测试达人 feature_10:功能收割机 first_feed:初次喂食 feed_100:美食家 play_100:游戏达人 train_50:训练达人 streak_7:一周不落 streak_30:月度坚持 streak_365:年度陪伴 level_10:初露锋芒 level_30:渐入佳境 level_50:炉火纯青 level_99:登峰造极 evolution_max:完全觉醒 bond_100:心意相通 first_dress:初次装扮 dress_all:时尚达人 game_10:接食物达人 game_high_50:反应高手 game_high_100:接食物大师 all_pets:宠物收集家"

  for ACH_ID in $NEW_ACHS; do
    local ACH_NAME=$(echo "$ACH_NAMES" | tr ' ' '\n' | grep "^${ACH_ID}:" | cut -d: -f2)
    echo "🏆 ════════════════════════════════ 🏆"
    echo "   ✨ 成就解锁！✨"
    echo ""
    echo "   🏆 ${ACH_NAME}"
    echo "   🎉 恭喜 ${NAME}！"
    echo "🏆 ════════════════════════════════ 🏆"
  done
}
