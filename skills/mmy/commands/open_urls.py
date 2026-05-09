#!/usr/bin/env python3
"""在浏览器中打开热榜条目"""
import argparse
import sys
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from momoyu_public_fetch import load_config, get_source_groups, filter_groups


def main() -> int:
    parser = argparse.ArgumentParser(description="在浏览器中打开热榜条目")
    parser.add_argument("count", type=int, nargs="?", default=5, help="每个平台打开前 N 条（默认 5）")
    parser.add_argument("--sources", help="指定平台（逗号分隔，如 zhihu,weibo）")
    args = parser.parse_args()

    config = load_config()
    active = config.get("active_list", "default")
    source_filters = args.sources or ",".join(config.get("lists", {}).get(active, []))

    groups = filter_groups(get_source_groups(), source_filters or None)

    opened = 0
    for group in groups:
        for item in group.get("data", [])[: args.count]:
            link = item.get("link")
            if link:
                webbrowser.open(link)
                opened += 1

    print(f"已打开 {opened} 个链接。")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())