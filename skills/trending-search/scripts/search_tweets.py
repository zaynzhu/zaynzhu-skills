#!/usr/bin/env python3
"""Trending Search — search X/Twitter for hot posts matching given keywords.

Part of the trending-search skill. Uses Tavily Search API to find recent
high-engagement tweets for any keyword set, outputs a structured report.
Engagement data (likes/views) is NOT available from Tavily — the AI
assistant should supplement it via WebSearch or mark it as "数据暂缺".
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone


sys.stdout.reconfigure(encoding="utf-8")

TAVILY_URL = "https://api.tavily.com/search"

DEFAULT_KEYWORDS = [
    "NanoBanana Pro",
    "Nano Banana Pro",
    "NanoBanana Pro 2",
    "ナノバナナプ口",
    "ナノバナナプロ",
    "Gemini Nano Banana",
]

MIN_RELEVANCE_SCORE = 0.15


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search X/Twitter for hot posts matching keywords."
    )
    parser.add_argument(
        "--keywords",
        nargs="+",
        default=None,
        help="Search keywords (replaces defaults entirely).",
    )
    parser.add_argument(
        "--extra-keywords",
        nargs="+",
        default=[],
        help="Additional keywords to append to defaults.",
    )
    parser.add_argument(
        "--min-likes",
        type=int,
        default=30,
        help="Minimum likes threshold (used as metadata, Tavily cannot filter by likes).",
    )
    parser.add_argument(
        "--min-views",
        type=int,
        default=10000,
        help="Minimum views threshold (used as metadata, Tavily cannot filter by views).",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=20,
        help="Maximum number of results to return (default: 20).",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=MIN_RELEVANCE_SCORE,
        help="Minimum Tavily relevance score to include (default: 0.15).",
    )
    parser.add_argument(
        "--format",
        choices=("md", "json"),
        default="md",
        help="Output format (default: md).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="HTTP timeout in seconds (default: 30).",
    )
    return parser.parse_args()


def build_keywords(args: argparse.Namespace) -> list[str]:
    if args.keywords:
        keywords = list(args.keywords)
    else:
        keywords = list(DEFAULT_KEYWORDS)
    keywords.extend(args.extra_keywords)
    return list(dict.fromkeys(keywords))


def search_tavily(keyword: str, timeout: int) -> dict:
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        raise SystemExit("TAVILY_API_KEY is not set. Set it with: $env:TAVILY_API_KEY='tvly-...'")

    # Use include_domains instead of site: in query to avoid double-filtering
    payload = {
        "query": keyword,
        "topic": "news",
        "search_depth": "advanced",
        "max_results": 10,
        "include_answer": False,
        "include_raw_content": False,
        "time_range": "day",
        "include_domains": ["x.com", "twitter.com"],
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    request = urllib.request.Request(
        TAVILY_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP Error {exc.code}: {body}", file=sys.stderr)
        return {"results": [], "query": keyword}
    except urllib.error.URLError as exc:
        print(f"Network Error: {exc.reason}", file=sys.stderr)
        return {"results": [], "query": keyword}


def is_twitter_url(url: str) -> bool:
    try:
        domain = urllib.parse.urlparse(url).netloc.lower()
        return domain in ("x.com", "twitter.com", "www.x.com", "www.twitter.com", "mobile.x.com", "mobile.twitter.com")
    except ValueError:
        return False


def extract_tweet_id(url: str) -> str:
    try:
        path = urllib.parse.urlparse(url).path.rstrip("/")
        parts = path.split("/")
        for i, part in enumerate(parts):
            if part == "status" and i + 1 < len(parts):
                return parts[i + 1]
    except (ValueError, IndexError):
        pass
    return ""


def extract_username(url: str) -> str:
    try:
        path = urllib.parse.urlparse(url).path.rstrip("/")
        parts = path.split("/")
        for i, part in enumerate(parts):
            if part == "status":
                if i > 0:
                    return parts[i - 1]
                break
    except (ValueError, IndexError):
        pass
    return ""


def deduplicate(results: list[dict]) -> list[dict]:
    seen_ids = set()
    deduped = []
    for item in results:
        url = item.get("url", "")
        tweet_id = extract_tweet_id(url)
        key = tweet_id if tweet_id else url
        if key not in seen_ids:
            seen_ids.add(key)
            deduped.append(item)
    return deduped


def generate_trend(results: list[dict], keywords: list[str]) -> str:
    """Generate a brief trend observation based on search results."""
    if not results:
        return "社区较为平静"

    top_scores = [float(r.get("score", 0) or 0) for r in results[:5]]
    avg_score = sum(top_scores) / len(top_scores) if top_scores else 0

    if avg_score >= 0.7:
        return "🔥 社区讨论非常火爆"
    elif avg_score >= 0.4:
        return "社区讨论活跃"
    elif avg_score >= 0.2:
        return "社区有零星讨论"
    else:
        return "社区较为平静"


def format_md(
    results: list[dict],
    keywords: list[str],
    min_likes: int,
    min_views: int,
    max_results: int,
) -> str:
    now_cst = datetime.now(timezone(timedelta(hours=8)))
    time_str = now_cst.strftime("%Y年%m月%d日 %H:%M")

    keyword_label = " / ".join(keywords[:3])
    if len(keywords) > 3:
        keyword_label += f" 等{len(keywords)}个关键词"

    lines = []
    lines.append(f"# [{keyword_label} 24小时热帖速报]")
    lines.append("")
    lines.append(f"统计时间：{time_str} (UTC+8)")
    lines.append("前24小时")
    lines.append("")

    if not results:
        lines.append(f"**今日24小时内暂无关于{keyword_label}的高热度讨论，社区较为平静。**")
        lines.append("")
        lines.append("**严禁编造任何数据、ID或链接。**")
        return "\n".join(lines)

    top_score = max(float(r.get("score", 0) or 0) for r in results)
    trend = generate_trend(results, keywords)
    lines.append(f"最高相关性分数：{top_score:.2f} | {trend}")
    lines.append("")
    lines.append("> ⚠️ 点赞/浏览数据暂缺 — Tavily API 不返回互动数据，需通过 WebSearch 补充")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Filter to only actual tweet URLs (must have /status/ path)
    tweet_results = [r for r in results if extract_tweet_id(r.get("url", ""))]
    tweet_results = tweet_results[:max_results]

    for i, item in enumerate(tweet_results, start=1):
        url = item.get("url", "")
        username = extract_username(url) or url
        tweet_id = extract_tweet_id(url)
        title = item.get("title", "")
        content = item.get("content", "") or ""
        score = float(item.get("score", 0) or 0)
        published = item.get("published_date", "")

        display_url = f"https://x.com/{username}/status/{tweet_id}" if username and tweet_id and username != url else url

        # Prefer content over title for tweet descriptions
        description = (content[:120] if content else title).strip()
        if not description:
            description = "（无描述）"

        lines.append(f"### {i}. @{username}")
        lines.append("")
        lines.append(f"{description}")
        lines.append("")
        lines.append(f"相关性：{score:.2f}")
        if published:
            lines.append(f"发布时间：{published}")
        lines.append(f"点赞/浏览：数据暂缺（筛选标准：≥{min_likes}赞 / ≥{min_views}浏览）")
        lines.append("")
        lines.append(display_url)
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## 统计摘要")
    lines.append("")
    lines.append(f"- 搜索关键词：{'、'.join(keywords)}")
    lines.append(f"- 筛选标准：点赞 ≥ {min_likes}，浏览 ≥ {min_views}")
    lines.append(f"- 相关性阈值：≥ {MIN_RELEVANCE_SCORE:.2f}")
    lines.append(f"- 有效结果数：{len(tweet_results)}条（目标：{max_results}条）")
    lines.append("- 数据来源：Tavily Search API（互动数据需 WebSearch 补充）")
    lines.append("")
    lines.append("### 后续步骤")
    lines.append("")
    lines.append("对以上结果中相关性高的帖子，建议使用 WebSearch 逐条搜索获取点赞/浏览数据：")
    lines.append("```")
    lines.append("WebSearch: site:x.com @{username} likes")
    lines.append("```")

    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    keywords = build_keywords(args)

    all_results = []
    for keyword in keywords:
        result = search_tavily(keyword, timeout=args.timeout)
        for item in result.get("results", []):
            url = item.get("url", "")
            if is_twitter_url(url):
                item["_keyword"] = keyword
                all_results.append(item)

    all_results = deduplicate(all_results)

    # Filter by minimum relevance score
    all_results = [
        r for r in all_results
        if float(r.get("score", 0) or 0) >= args.min_score
    ]

    # Sort by Tavily relevance score (proxy for engagement)
    all_results.sort(key=lambda x: float(x.get("score", 0) or 0), reverse=True)

    if args.format == "json":
        output = {
            "keywords": keywords,
            "min_likes": args.min_likes,
            "min_views": args.min_views,
            "min_score": args.min_score,
            "max_results": args.max_results,
            "total_found": len(all_results),
            "results": all_results[:args.max_results],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(format_md(all_results, keywords, args.min_likes, args.min_views, args.max_results))


if __name__ == "__main__":
    main()