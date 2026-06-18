#!/usr/bin/env python3
"""获取 AIHOT 公开动态，供 ideastorming skill 使用。"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict


API_URL = "https://aihot.virxact.com/api/public/items"
RATE_LIMIT_SECONDS = 2
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)


def buildUrl(args: argparse.Namespace) -> str:
  params: Dict[str, str] = {}

  if args.mode:
    params["mode"] = args.mode

  if args.query:
    params["q"] = args.query

  if args.take:
    params["take"] = str(args.take)

  if args.since:
    params["since"] = args.since

  if args.category:
    params["category"] = args.category

  return f"{API_URL}?{urllib.parse.urlencode(params)}"


def fetchJson(url: str) -> object:
  # 预留限频，避免未来脚本扩展成多次请求时连续打同一服务。
  time.sleep(RATE_LIMIT_SECONDS)

  request = urllib.request.Request(
      url,
      headers={
          "User-Agent": USER_AGENT,
          "Accept": "application/json,text/plain,*/*",
      },
  )

  with urllib.request.urlopen(request, timeout=30) as response:
    charset = response.headers.get_content_charset() or "utf-8"
    body = response.read().decode(charset)
    return json.loads(body)


def parseArgs() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Fetch recent AIHOT public items")
  parser.add_argument("--mode", default="selected", help="AIHOT mode, default: selected")
  parser.add_argument("--take", type=int, default=30, help="number of items to fetch")
  parser.add_argument("--since", help="ISO datetime lower bound")
  parser.add_argument(
      "--category",
      choices=["ai-models", "ai-products", "industry", "paper", "tip"],
      help="AIHOT category",
  )
  parser.add_argument("--query", help="keyword search query")
  return parser.parse_args()


def main() -> int:
  args = parseArgs()
  url = buildUrl(args)

  try:
    data = fetchJson(url)
  except urllib.error.HTTPError as error:
    print(f"AIHOT HTTP error: {error.code} {error.reason}", file=sys.stderr)
    return 1
  except urllib.error.URLError as error:
    print(f"AIHOT request failed: {error.reason}", file=sys.stderr)
    return 1
  except json.JSONDecodeError as error:
    print(f"AIHOT returned invalid JSON: {error}", file=sys.stderr)
    return 1

  json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
  print()
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
