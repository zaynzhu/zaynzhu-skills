# bt-search

BT 资源搜索工具：聚合多个公开索引站，按关键词返回融合排序后的磁力链接与种子直链。

## 功能

- 三类分流搜索：
  - `anime`（Mikan → Nyaa → 1LOU → KPkuang → BT影视）
  - `movie`（BT影视 → KPkuang → 1LOU → Nyaa）
  - `adult`（Sukebei）
- 跨源融合：按磁力 btih 精确去重，无 hash 时按规范作品名/年份/集数/分辨率/字幕/编码指纹合并，按中字、分辨率、集数合理性、热度打分
- 反爬传输层：`curl_cffi` 伪装 Chrome TLS 指纹（KPkuang / BT影视 反爬源所需）
- 结果缓存（默认 15 分钟）、单站超时、站点熔断（连续失败 3 次 → 冷却约 5 分钟）
- 结构化 `--json` 输出（含 `query/sites/items` 顶层字段）

## 依赖

- Node.js（无严格版本要求）
- 可选：技能目录 `.venv` 内 `curl_cffi`（不装则反爬源退化为普通抓取）。安装：
  - Linux/macOS：`python3 -m venv .venv && ./.venv/bin/pip install curl_cffi`
  - Windows：`python -m venv .venv && .venv\Scripts\python.exe -m pip install curl_cffi`
- 可选：qBittorrent Web UI（推送下载队列）、Cloudflare WARP 本地代理（特定源被 Cloudflare 拦且处于机房 IP 时）

## 快速开始

```bash
# 自动判断类型（anime/movie/adult）
node scripts/bt.js "关键词"

# 快速模式（约 15s 预算，命中强结果早停）
node scripts/bt.js "关键词" anime --fast

# 结构化 JSON 输出
node scripts/bt.js "关键词" --json
```

## 使用方式

对 AI 说「用 bt-search 搜 <关键词> 的资源」，或按 SKILL.md 用法直接 `/bt-search <关键词>`。

## 常用参数

| 参数 | 说明 |
|------|------|
| `--source mikan,nyaa,onelou,kpkuang,btbtla` | 限定站点 |
| `--timeout 8s` | 单站超时 |
| `--limit 5` | 融合结果条数上限 |
| `--fast` | 首屏优先，早停 |
| `--no-deep` | 只抓搜索页，不进详情/磁力解密层 |
| `--no-cache` | 跳过结果与页面缓存 |
| `--full / --detail / --json / --debug` | 输出粒度开关 |

## 状态与缓存落点

状态文件与页面/结果缓存默认写到本技能目录下 `memory/`（已随技能 `.gitignore` 忽略），不可写时回退系统临时目录。可用环境变量覆盖：`BT_SEARCH_STATE_FILE`、`BT_SEARCH_CACHE_DIR`、`BT_SEARCH_PYTHON`、`BT_SEARCH_RESULT_TTL_MS` 等（前缀 `BT_SEARCH_`，完整清单见 SKILL.md）。

## 文件结构

```
bt-search/
├── SKILL.md                            ← 主指令（用法、各源说明与排坑）
├── references/btbtla-1lou-workaround.md ← 源站故障排查与直连方案
└── scripts/                            ← bt.js 入口 + lib/ + sources/ + tests/
```