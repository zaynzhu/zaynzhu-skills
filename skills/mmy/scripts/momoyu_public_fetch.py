#!/usr/bin/env python3
from __future__ import annotations
import argparse
import base64
import html
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

BASE_URL = "https://momoyu.cc"
API_BASE = f"{BASE_URL}/api"
USER_AGENT = "momoyu-public-fetch/1.0"
CONFIG_FILE = Path(__file__).parent / "mmy_config.json"
CREDENTIALS_FILE = Path(__file__).parent / "mmy_credentials.json"
HISTORY_FILE = Path(__file__).parent / "mmy_history.json"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# ==========================================
# 凭证与认证
# ==========================================
def load_credentials() -> dict:
    if not CREDENTIALS_FILE.exists():
        return {}
    try:
        with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_credentials(creds: dict) -> None:
    with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
        json.dump(creds, f, indent=2, ensure_ascii=False)

_SESSION_CACHE: dict | None = None

def _get_session_cookies() -> tuple[str, str]:
    global _SESSION_CACHE
    if _SESSION_CACHE is not None:
        return _SESSION_CACHE["token"], _SESSION_CACHE["connect_sid"]
    creds = load_credentials()
    _SESSION_CACHE = {
        "token": creds.get("token", ""),
        "connect_sid": creds.get("connect_sid", ""),
    }
    return _SESSION_CACHE["token"], _SESSION_CACHE["connect_sid"]

def _build_auth_headers() -> dict:
    token, connect_sid = _get_session_cookies()
    cookie_parts = []
    if token:
        cookie_parts.append(f"token={token}")
    if connect_sid:
        cookie_parts.append(f"connect.sid={connect_sid}")
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
    }
    if cookie_parts:
        headers["Cookie"] = "; ".join(cookie_parts)
    return headers

def _is_session_valid() -> bool:
    token, connect_sid = _get_session_cookies()
    if not token or not connect_sid:
        return False
    try:
        url = f"{API_BASE}/hot/list?type=0"
        req = urllib.request.Request(url, headers=_build_auth_headers())
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            payload = json.loads(raw)
            groups = payload.get("data", [])
            return bool(groups) and len(groups) <= 15
    except Exception:
        return False

def login_and_save_session(email: str, password: str) -> dict | None:
    global _SESSION_CACHE
    login_url = f"{API_BASE}/user/login"
    body = json.dumps({"email": email, "password": password}).encode()
    req = urllib.request.Request(
        login_url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/plain, */*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            payload = json.loads(raw)
            if payload.get("status") != 100000:
                print(f"登录失败: {payload.get('message', '未知错误')}", file=sys.stderr)
                return None
    except urllib.error.HTTPError as e:
        print(f"登录请求失败: HTTP {e.code}", file=sys.stderr)
        return None

    set_cookie_headers = resp.headers.get_all("Set-Cookie") or []
    token_val = ""
    connect_sid_val = ""
    for cookie_str in set_cookie_headers:
        for part in cookie_str.split(","):
            part = part.strip()
            if part.startswith("token="):
                token_val = part.split("=", 1)[1].split(";")[0]
            elif part.startswith("connect.sid="):
                connect_sid_val = part.split("=", 1)[1].split(";")[0]

    if not token_val or not connect_sid_val:
        return None

    creds = load_credentials() or {}
    creds["token"] = token_val
    creds["connect_sid"] = connect_sid_val
    creds["login_time"] = datetime.now().strftime("%Y-%m-%d")
    save_credentials(creds)
    _SESSION_CACHE = {
        "token": token_val,
        "connect_sid": connect_sid_val,
    }
    return creds

# ==========================================
# 核心网络请求
# ==========================================
def fetch_text(url: str) -> str:
    headers = _build_auth_headers()
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8")

def fetch_json(path: str) -> dict:
    raw = fetch_text(f"{API_BASE}{path}")
    payload = json.loads(raw)
    if payload.get("status") != 100000:
        raise RuntimeError(
            f"Unexpected API payload: status={payload.get('status')} message={payload.get('message')}"
        )
    return payload["data"]

def build_rss_url(ids: list[int]) -> str:
    raw = ",".join(str(item) for item in ids)
    code = base64.b64encode(raw.encode("utf-8")).decode("ascii")
    return f"{API_BASE}/hot/rss?code={urllib.parse.quote(code)}"

# ==========================================
# 数据处理
# ==========================================
def get_source_groups() -> list[dict]:
    data = fetch_json("/hot/list?type=0")
    if data and len(data) <= 15:
        return data
    creds = load_credentials()
    has_session = bool(creds.get("token")) and bool(creds.get("connect_sid"))
    if not has_session:
        return data
    print("提示: 登录会话可能已过期，返回的是公开源而非订阅源。", file=sys.stderr)
    print("请运行: python commands/login.py open 重新登录", file=sys.stderr)
    return data

def flatten_items(groups: list[dict]) -> list[dict]:
    items = []
    for group in groups:
        for entry in group.get("data", []):
            items.append(
                {
                    "source_id": group["id"],
                    "source_key": group.get("source_key", ""),
                    "source_name": group["name"],
                    "title": entry["title"],
                    "extra": entry.get("extra", ""),
                    "link": entry["link"],
                    "item_id": entry["id"],
                }
            )
    return items

def parse_source_filters(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [part.strip().lower() for part in raw.split(",") if part.strip()]

def source_matches(group: dict, filters: list[str]) -> bool:
    if not filters:
        return True
    candidates = {
        str(group["id"]).lower(),
        group.get("source_key", "").lower(),
        group["name"].lower(),
    }
    return any(token in candidates for token in filters)

def filter_groups(groups: list[dict], raw_filters: str | None) -> list[dict]:
    filters = parse_source_filters(raw_filters)
    selected = [group for group in groups if source_matches(group, filters)]
    if filters and not selected:
        raise ValueError(f"No public source matched: {raw_filters}")
    return selected

# ==========================================
# 配置与历史记录 (Skill 扩展功能)
# ==========================================
def load_config() -> dict:
    default_config = {
        "limit_per_source": 10,
        "deduplicate": False,
        "active_list": "default",
        "lists": {
            "default": ["zhihu", "weibo", "hupu", "47"]
        }
    }
    if not CONFIG_FILE.exists():
        return default_config
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            # 合并默认配置，防止字段缺失
            for k, v in default_config.items():
                if k not in config:
                    config[k] = v
            return config
    except Exception:
        return default_config

def save_config(config: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def load_history() -> dict:
    if not HISTORY_FILE.exists():
        return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_history(history: dict) -> None:
    # 自动清理 7 天前的记录
    cutoff = datetime.now() - timedelta(days=7)
    cleaned = {}
    for item_id, ts_str in history.items():
        try:
            ts = datetime.fromisoformat(ts_str)
            if ts > cutoff:
                cleaned[item_id] = ts_str
        except Exception:
            pass
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False)

def deduplicate_groups(groups: list[dict], history: dict) -> tuple[list[dict], int]:
    deduped_groups = []
    removed_count = 0
    now_str = datetime.now().isoformat()
    
    for group in groups:
        new_group = group.copy()
        new_data = []
        for item in group.get("data", []):
            item_id = str(item.get("id", ""))
            if not item_id:
                new_data.append(item)
                continue
                
            if item_id in history:
                removed_count += 1
            else:
                new_data.append(item)
                history[item_id] = now_str
                
        new_group["data"] = new_data
        if new_data: # 如果去重后这个组还有数据，就保留这个组
            deduped_groups.append(new_group)
            
    return deduped_groups, removed_count

# ==========================================
# 渲染输出
# ==========================================
def render_html(groups: list[dict], fetched_at: str, limit_per_source: int) -> str:
    sections = []
    for group in groups:
        cards = []
        for index, entry in enumerate(group.get("data", [])[:limit_per_source], start=1):
            title = html.escape(entry["title"])
            extra = html.escape(entry.get("extra", "").strip())
            link = html.escape(entry["link"], quote=True)
            meta = f'<div class="meta">{extra}</div>' if extra else ""
            cards.append(
                f"""
                <a class="item" href="{link}" target="_blank" rel="noopener noreferrer">
                  <div class="rank">{index}</div>
                  <div class="content">
                    <div class="title">{title}</div>
                    {meta}
                    <div class="url">{link}</div>
                  </div>
                </a>
                """.strip()
            )
        section_body = "\n".join(cards) if cards else '<div class="empty">当前没有公开条目</div>'
        sections.append(
            f"""
            <section class="source">
              <div class="source-head">
                <h2>{html.escape(group["name"])}</h2>
                <div class="source-meta">{group["id"]} / {html.escape(group.get("source_key", ""))}</div>
              </div>
              <div class="items">
                {section_body}
              </div>
            </section>
            """.strip()
        )

    body = "\n".join(sections)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>摸摸鱼公开热榜</title>
  <style>
    :root {{
      --bg: #f5efe3;
      --panel: rgba(255,255,255,0.82);
      --panel-strong: #fffdf8;
      --text: #1f2a37;
      --muted: #6b7280;
      --line: rgba(31,42,55,0.12);
      --accent: #ba4a00;
      --accent-soft: #fff1e8;
      --shadow: 0 20px 50px rgba(83, 43, 16, 0.12);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, #ffe1c4 0, transparent 28%),
        radial-gradient(circle at top right, #f7d8cc 0, transparent 24%),
        linear-gradient(180deg, #f8f0e5 0%, #f2e9de 100%);
    }}
    .wrap {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 32px 20px 56px;
    }}
    .hero {{
      padding: 28px;
      border: 1px solid var(--line);
      border-radius: 24px;
      background: var(--panel);
      backdrop-filter: blur(10px);
      box-shadow: var(--shadow);
    }}
    .hero h1 {{
      margin: 0 0 10px;
      font-size: 34px;
    }}
    .hero p {{
      margin: 6px 0;
      color: var(--muted);
    }}
    .sources {{
      margin-top: 24px;
      display: grid;
      gap: 18px;
    }}
    .source {{
      border: 1px solid var(--line);
      border-radius: 22px;
      background: var(--panel-strong);
      box-shadow: var(--shadow);
      overflow: hidden;
    }}
    .source-head {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: baseline;
      padding: 18px 20px;
      background: linear-gradient(135deg, #fff8f2 0%, #fff1e4 100%);
      border-bottom: 1px solid var(--line);
    }}
    .source-head h2 {{
      margin: 0;
      font-size: 22px;
    }}
    .source-meta {{
      color: var(--muted);
      font-size: 13px;
    }}
    .items {{
      padding: 14px;
      display: grid;
      gap: 12px;
    }}
    .item {{
      display: grid;
      grid-template-columns: 48px 1fr;
      gap: 14px;
      align-items: start;
      text-decoration: none;
      color: inherit;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: #fffdfa;
      padding: 14px;
      transition: transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease;
    }}
    .item:hover {{
      transform: translateY(-2px);
      border-color: rgba(186, 74, 0, 0.28);
      box-shadow: 0 14px 30px rgba(186, 74, 0, 0.08);
    }}
    .rank {{
      width: 48px;
      height: 48px;
      display: grid;
      place-items: center;
      border-radius: 14px;
      background: var(--accent-soft);
      color: var(--accent);
      font-weight: 700;
      font-size: 18px;
    }}
    .title {{
      font-size: 17px;
      line-height: 1.45;
      margin-bottom: 8px;
    }}
    .meta {{
      display: inline-block;
      margin-bottom: 8px;
      padding: 4px 9px;
      border-radius: 999px;
      background: #f7f1ea;
      color: #8a5a2b;
      font-size: 13px;
    }}
    .url {{
      color: var(--muted);
      font-size: 13px;
      word-break: break-all;
    }}
    .empty {{
      color: var(--muted);
      padding: 8px 2px;
    }}
    @media (max-width: 720px) {{
      .wrap {{ padding: 18px 14px 36px; }}
      .hero {{ padding: 20px; border-radius: 18px; }}
      .hero h1 {{ font-size: 28px; }}
      .source-head {{ padding: 16px; flex-direction: column; align-items: start; }}
      .item {{ grid-template-columns: 40px 1fr; padding: 12px; }}
      .rank {{ width: 40px; height: 40px; border-radius: 12px; font-size: 16px; }}
      .title {{ font-size: 16px; }}
    }}
  </style>
</head>
<body>
  <main class="wrap">
    <section class="hero">
      <h1>摸摸鱼公开热榜</h1>
      <p>匿名抓取，不使用账号，不带 Cookie。</p>
      <p>抓取时间：{html.escape(fetched_at)}</p>
      <p>说明：点击任意条目会用系统默认浏览器打开原始链接。</p>
    </section>
    <section class="sources">
      {body}
    </section>
  </main>
</body>
</html>
"""

SOURCE_ICONS = {
    "zhihu": "\U0001f9e0",
    "weibo": "\U0001f525",
    "hupu": "\U0001f3c0",
    "douyin": "\U0001f3b5",
    "bilibili": "\U0001f3ac",
    "tieba": "\U0001f4ac",
    "toutiao": "\U0001f4f0",
    "36kr": "\U0001f680",
    "zhihu_daily": "\U0001f4c5",
    "sina": "\U0001f4fa",
    "github": "\U0001f4bb",
    "v2ex": "\U0001f517",
    "csdn": "\U0001f4d6",
    "juejin": "\U0001f48e",
    "segmentfault": "\U0001f527",
    "news_qq": "\U0001f4e2",
    "ifeng": "\U0001f981",
    "netease": "\U0001f3a8",
    "ithome": "\U0001f4f1",
    "weixin": "\U0001f4f2",
    "youmin_steam": "\U0001f3ae",
    "nga": "\U0001f418",
}

SOURCE_LABELS = {
    "zhihu": "知乎热榜",
    "weibo": "微博热搜",
    "hupu": "虎扑步行街",
    "douyin": "抖音热榜",
    "bilibili": "B站热门",
    "tieba": "百度贴吧",
    "toutiao": "今日头条",
    "36kr": "36氪",
    "zhihu_daily": "知乎日报",
    "sina": "新浪热点",
    "github": "GitHub趋势",
    "v2ex": "V2EX",
    "csdn": "CSDN",
    "juejin": "掘金",
    "segmentfault": "思否",
    "news_qq": "腾讯新闻",
    "ifeng": "凤凰新闻",
    "netease": "网易新闻",
    "ithome": "IT之家",
    "weixin": "微信热议",
    "youmin_steam": "游民娱乐榜",
    "nga": "NGA",
}


def _icon_for(key: str) -> str:
    return SOURCE_ICONS.get(key, "\U0001f4ca")


def _label_for(key: str, name: str) -> str:
    return SOURCE_LABELS.get(key, name)


def _humanize_extra(extra: str) -> str:
    s = extra.strip()
    if not s:
        return ""
    return s


def render_markdown(groups: list[dict], fetched_at: str, limit_per_source: int) -> str:
    total = sum(len(g.get("data", [])[:limit_per_source]) for g in groups)
    lines: list[str] = []
    lines.append("**🐟 摸摸鱼热榜**")
    lines.append("")
    lines.append(f"共 {total} 条 · {fetched_at}")
    lines.append("")

    global_idx = 0
    for group in groups:
        source_key = group.get("source_key", "")
        label = _label_for(source_key, group["name"])

        items = group.get("data", [])[:limit_per_source]
        if not items:
            lines.append(f"## {label}")
            lines.append("")
            lines.append("*暂无公开条目*")
            lines.append("")
            continue

        lines.append(f"## {label}")
        lines.append("")

        for entry in items:
            global_idx += 1
            title = entry["title"]
            link = entry["link"]
            extra = _humanize_extra(entry.get("extra", ""))

            title_line = f"{global_idx}. **{title}**"
            if extra:
                title_line += f" — {extra}"
            lines.append(title_line)
            lines.append(f"   [原文]({link})")

        lines.append("")

    if global_idx == 0:
        lines.append("*暂无数据*")
        lines.append("")

    return "\n".join(lines)


# ==========================================
# CLI 命令处理函数
# ==========================================
def print_sources(args: argparse.Namespace) -> None:
    groups = get_source_groups()
    for group in groups[: args.limit]:
        print(f'{group["id"]:>4}  {group.get("source_key", ""):<16}  {group["name"]}')

def print_top(args: argparse.Namespace) -> None:
    items = fetch_json("/hot/top")
    for index, item in enumerate(items[: args.limit], start=1):
        extra = f" [{item.get('extra', '').strip()}]" if item.get("extra") else ""
        print(f"{index:>2}. {item['name']}{extra}")
        print(f"    {item['title']}")
        print(f"    {item['link']}")

def print_list(args: argparse.Namespace) -> None:
    groups = filter_groups(get_source_groups(), args.source)
    items = flatten_items(groups)
    for index, item in enumerate(items[: args.limit], start=1):
        extra = f" [{item['extra'].strip()}]" if item["extra"] else ""
        print(
            f"{index:>2}. {item['source_name']} ({item['source_id']}/{item['source_key']}){extra}"
        )
        print(f"    {item['title']}")
        print(f"    {item['link']}")

def print_rss_url(args: argparse.Namespace) -> None:
    ids = [int(part.strip()) for part in args.ids.split(",") if part.strip()]
    if not ids:
        raise ValueError("No source ids provided.")
    print(build_rss_url(ids))

def print_rss(args: argparse.Namespace) -> None:
    ids = [int(part.strip()) for part in args.ids.split(",") if part.strip()]
    if not ids:
        raise ValueError("No source ids provided.")
    print(fetch_text(build_rss_url(ids)))

def write_view(args: argparse.Namespace) -> None:
    groups = filter_groups(get_source_groups(), args.sources)
    fetched_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    html_text = render_html(groups, fetched_at, args.limit_per_source)
    output_path = Path(args.output).resolve()
    output_path.write_text(html_text, encoding="utf-8")
    print(output_path)
    if args.open:
        webbrowser.open(output_path.as_uri())

# Skill 相关的 CLI 包装
def skill_api(args: argparse.Namespace) -> None:
    config = load_config()
    history = load_history()
    
    # 确定平台源
    source_filters_str = args.sources
    if not source_filters_str:
        active = config.get("active_list", "default")
        source_filters = config.get("lists", {}).get(active, [])
        source_filters_str = ",".join(source_filters)
    
    groups = filter_groups(get_source_groups(), source_filters_str)
    
    # 去重处理
    removed_count = 0
    if config.get("deduplicate", False):
        groups, removed_count = deduplicate_groups(groups, history)
        save_history(history)
        
    fetched_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    limit = config.get("limit_per_source", 10)
    
    # 获取格式化输出
    if args.format == "markdown":
        output = render_markdown(groups, fetched_at, limit)
        if config.get("deduplicate", False):
            output += f"\n\n*注：已过滤 {removed_count} 条已读历史记录*"
        print(output)
    elif args.format == "json":
        # 简化版 JSON 用于纯数据处理
        json_out = {"fetched_at": fetched_at, "filtered": removed_count, "groups": groups}
        print(json.dumps(json_out, ensure_ascii=False, indent=2))
        
    if args.open_count:
        count = int(args.open_count)
        opened = 0
        for g in groups:
            for item in g.get("data", [])[:count]:
                link = item.get("link")
                if link:
                    webbrowser.open(link)
                    opened += 1
        print(f"\n已自动打开 {opened} 个链接。")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Anonymous read-only helper for public momoyu.cc endpoints. "
            "Use it without your account. The site's RSS feed currently advertises ttl=10, "
            "so avoid polling faster than every 10 minutes."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sources_parser = subparsers.add_parser("sources", help="List public source ids.")
    sources_parser.add_argument("--limit", type=int, default=50)
    sources_parser.set_defaults(func=print_sources)

    top_parser = subparsers.add_parser("top", help="Show the public top hot items.")
    top_parser.add_argument("--limit", type=int, default=20)
    top_parser.set_defaults(func=print_top)

    list_parser = subparsers.add_parser(
        "list", help="Show aggregated items, optionally filtered by source id/key/name."
    )
    list_parser.add_argument("--source", help="Example: zhihu, 1, hupu, weibo")
    list_parser.add_argument("--limit", type=int, default=30)
    list_parser.set_defaults(func=print_list)

    view_parser = subparsers.add_parser(
        "view",
        help="Generate a local clickable HTML page for selected public sources.",
    )
    view_parser.add_argument(
        "--sources",
        required=True,
        help="Comma-separated ids/keys/names. Example: zhihu,weibo,47",
    )
    view_parser.add_argument("--limit-per-source", type=int, default=20)
    view_parser.add_argument("--output", default="momoyu_view.html")
    view_parser.add_argument("--open", action="store_true")
    view_parser.set_defaults(func=write_view)

    rss_url_parser = subparsers.add_parser(
        "rss-url", help="Generate a public RSS feed URL from comma-separated source ids."
    )
    rss_url_parser.add_argument("--ids", required=True, help="Example: 1,3,47")
    rss_url_parser.set_defaults(func=print_rss_url)

    rss_parser = subparsers.add_parser(
        "rss", help="Fetch RSS XML for comma-separated public source ids."
    )
    rss_parser.add_argument("--ids", required=True, help="Example: 1,3,47")
    rss_parser.set_defaults(func=print_rss)
    
    # 新增 api 命令供 Skill 使用
    api_parser = subparsers.add_parser("api", help="Skill API integration.")
    api_parser.add_argument("--sources", help="Override config sources (comma-separated)")
    api_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    api_parser.add_argument("--open-count", type=int, help="Open top N links for each fetched source in browser")
    api_parser.set_defaults(func=skill_api)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
