#!/usr/bin/env python3
"""Enhanced Tavily search helper with readable Markdown output."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime


sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_URL = "https://api.tavily.com/search"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search Tavily and render either Markdown or raw JSON."
    )
    parser.add_argument("query", help="Search query text.")
    parser.add_argument(
        "--format",
        choices=("md", "json"),
        default="md",
        help="Output format. Defaults to Markdown.",
    )
    parser.add_argument(
        "--topic",
        choices=("general", "news", "finance"),
        default="general",
        help="Tavily topic filter.",
    )
    parser.add_argument(
        "--search-depth",
        choices=("basic", "advanced", "fast", "ultra-fast"),
        default="fast",
        help="Search depth/latency tradeoff.",
    )
    parser.add_argument(
        "--answer",
        choices=("none", "basic", "advanced"),
        default="basic",
        help="Include Tavily answer summary.",
    )
    parser.add_argument(
        "--raw-content",
        choices=("none", "markdown", "text"),
        default="none",
        help="Include raw page content in API response.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="Maximum search results to request (1-20 recommended).",
    )
    parser.add_argument(
        "--time-range",
        choices=("day", "week", "month", "year", "d", "w", "m", "y"),
        help="Relative date filter.",
    )
    parser.add_argument("--start-date", help="Absolute start date in YYYY-MM-DD.")
    parser.add_argument("--end-date", help="Absolute end date in YYYY-MM-DD.")
    parser.add_argument(
        "--days",
        type=int,
        help="Days back for news topic queries.",
    )
    parser.add_argument(
        "--include-domains",
        nargs="+",
        help="Only include these domains. Space-separated.",
    )
    parser.add_argument(
        "--exclude-domains",
        nargs="+",
        help="Exclude these domains. Space-separated.",
    )
    parser.add_argument("--country", help="Country boost for general topic.")
    parser.add_argument(
        "--auto-parameters",
        action="store_true",
        help="Let Tavily infer topic/depth when beneficial.",
    )
    parser.add_argument(
        "--exact-match",
        action="store_true",
        help='Require quoted phrases in query to match exactly.',
    )
    parser.add_argument(
        "--include-favicon",
        action="store_true",
        help="Include favicon URLs in results.",
    )
    parser.add_argument(
        "--include-images",
        action="store_true",
        help="Include image search results.",
    )
    parser.add_argument(
        "--include-image-descriptions",
        action="store_true",
        help="Include descriptions for returned images.",
    )
    parser.add_argument(
        "--include-usage",
        action="store_true",
        help="Include Tavily credit usage details.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Hide displayed results below this score threshold.",
    )
    parser.add_argument(
        "--snippet-chars",
        type=int,
        default=240,
        help="Maximum snippet length for Markdown rendering.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="HTTP timeout in seconds.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.max_results < 1 or args.max_results > 20:
        raise SystemExit("--max-results must be between 1 and 20.")
    if args.snippet_chars < 80:
        raise SystemExit("--snippet-chars must be at least 80.")
    if args.days is not None and args.days < 1:
        raise SystemExit("--days must be >= 1.")
    if args.time_range and (args.start_date or args.end_date):
        raise SystemExit("Use either --time-range or --start-date/--end-date, not both.")
    for value, flag in ((args.start_date, "--start-date"), (args.end_date, "--end-date")):
        if value:
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError as exc:
                raise SystemExit(f"{flag} must use YYYY-MM-DD format.") from exc


def build_payload(args: argparse.Namespace) -> dict:
    payload = {
        "query": args.query,
        "topic": args.topic,
        "search_depth": args.search_depth,
        "max_results": args.max_results,
        "include_answer": False if args.answer == "none" else args.answer,
        "include_raw_content": False if args.raw_content == "none" else args.raw_content,
        "include_favicon": args.include_favicon,
        "include_images": args.include_images,
        "include_image_descriptions": args.include_image_descriptions,
        "include_usage": args.include_usage,
        "auto_parameters": args.auto_parameters,
        "exact_match": args.exact_match,
    }

    optional_fields = {
        "time_range": args.time_range,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "days": args.days,
        "include_domains": args.include_domains,
        "exclude_domains": args.exclude_domains,
        "country": args.country,
    }
    for key, value in optional_fields.items():
        if value:
            payload[key] = value
    return payload


def fetch_results(payload: dict, timeout: int) -> dict:
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        raise SystemExit("TAVILY_API_KEY is not set.")

    url = os.environ.get("TAVILY_API_URL", DEFAULT_URL)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def truncate(text: str, limit: int) -> str:
    cleaned = " ".join((text or "").split())
    if not cleaned:
        return ""
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "..."


def domain_for(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc or "unknown"
    except ValueError:
        return "unknown"


def pick_snippet(result: dict, snippet_chars: int) -> str:
    raw_content = result.get("raw_content")
    content = raw_content if isinstance(raw_content, str) and raw_content.strip() else result.get("content", "")
    return truncate(content, snippet_chars)


def markdown_lines(result: dict, payload: dict, min_score: float, snippet_chars: int) -> list[str]:
    lines: list[str] = []
    lines.append("# Tavily Search")
    lines.append("")
    lines.append(f"Query: {result.get('query', payload['query'])}")
    lines.append(
        "Mode: "
        f"topic={payload.get('topic', 'general')}, "
        f"depth={payload.get('search_depth', 'fast')}, "
        f"results={payload.get('max_results', 5)}"
    )

    meta_parts = []
    if result.get("response_time") is not None:
        meta_parts.append(f"response_time={result['response_time']}s")
    if result.get("request_id"):
        meta_parts.append(f"request_id={result['request_id']}")
    if result.get("usage", {}).get("credits") is not None:
        meta_parts.append(f"credits={result['usage']['credits']}")
    if meta_parts:
        lines.append("Meta: " + ", ".join(meta_parts))

    auto_params = result.get("auto_parameters")
    if auto_params:
        serialized = ", ".join(f"{key}={value}" for key, value in auto_params.items())
        lines.append(f"Auto Parameters: {serialized}")

    answer = (result.get("answer") or "").strip()
    if answer:
        lines.append("")
        lines.append("## Summary")
        lines.append(answer)

    results = result.get("results", [])
    filtered = [item for item in results if float(item.get("score", 0.0) or 0.0) >= min_score]

    lines.append("")
    lines.append("## Top Results")
    if not filtered:
        lines.append("No results passed the display threshold.")
    else:
        for index, item in enumerate(filtered, start=1):
            title = item.get("title") or item.get("url") or f"Result {index}"
            url = item.get("url", "")
            score = item.get("score")
            score_text = f"{float(score):.2f}" if score is not None else "n/a"
            metadata = [f"score: {score_text}", f"domain: {domain_for(url)}"]
            if item.get("published_date"):
                metadata.append(f"published: {item['published_date']}")
            lines.append(f"[{index}] {title}")
            lines.append(" | ".join(metadata))
            if url:
                lines.append(f"url: {url}")
            snippet = pick_snippet(item, snippet_chars)
            if snippet:
                lines.append(f"snippet: {snippet}")
            favicon = item.get("favicon")
            if favicon:
                lines.append(f"favicon: {favicon}")
            lines.append("")

    images = result.get("images") or []
    if images:
        lines.append("## Images")
        for index, image in enumerate(images[:5], start=1):
            if isinstance(image, dict):
                lines.append(f"[{index}] {image.get('url', '')}")
                description = image.get("description")
                if description:
                    lines.append(f"description: {truncate(description, snippet_chars)}")
            else:
                lines.append(f"[{index}] {image}")
        lines.append("")

    lines.append("## Sources")
    if not filtered:
        lines.append("No sources available.")
    else:
        for index, item in enumerate(filtered, start=1):
            url = item.get("url", "")
            title = item.get("title") or url or f"Source {index}"
            lines.append(f"[{index}] {title} - {url}")

    return lines


def main() -> None:
    args = parse_args()
    validate_args(args)
    payload = build_payload(args)

    try:
        result = fetch_results(payload, timeout=args.timeout)
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP Error: {exc.code}", file=sys.stderr)
        print(details, file=sys.stderr)
        raise SystemExit(1) from exc
    except urllib.error.URLError as exc:
        print(f"Network Error: {exc.reason}", file=sys.stderr)
        raise SystemExit(1) from exc
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    lines = markdown_lines(
        result=result,
        payload=payload,
        min_score=args.min_score,
        snippet_chars=args.snippet_chars,
    )
    print("\n".join(lines).rstrip())


if __name__ == "__main__":
    main()
