#!/usr/bin/env python3
"""读取和修改热榜配置"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from momoyu_public_fetch import load_config, save_config


def main() -> int:
    parser = argparse.ArgumentParser(description="读取和修改热榜配置")
    sub = parser.add_subparsers(dest="action")

    sub.add_parser("show", help="显示当前完整配置（JSON）")

    src = sub.add_parser("sources", help="设置当前激活列表的平台源")
    src.add_argument("keys", help="平台列表（逗号分隔，如 zhihu,weibo,hupu）")
    src.add_argument("--list", dest="list_name", default=None, help="指定列表名（默认当前激活列表）")

    dedup = sub.add_parser("dedup", help="开关历史去重")
    dedup.add_argument("state", choices=["on", "off"], help="on 或 off")

    limit = sub.add_parser("limit", help="设置每源条目数")
    limit.add_argument("n", type=int, help="每源条目数")

    args = parser.parse_args()
    config = load_config()

    if args.action == "show" or args.action is None:
        print(json.dumps(config, ensure_ascii=False, indent=2))

    elif args.action == "sources":
        list_name = args.list_name or config.get("active_list", "default")
        sources = [k.strip() for k in args.keys.split(",") if k.strip()]
        config.setdefault("lists", {})[list_name] = sources
        save_config(config)
        print(f"已设置列表 '{list_name}': {', '.join(sources)}")

    elif args.action == "dedup":
        config["deduplicate"] = args.state == "on"
        save_config(config)
        print(f"去重已{'开启' if args.state == 'on' else '关闭'}")

    elif args.action == "limit":
        config["limit_per_source"] = args.n
        save_config(config)
        print(f"每源条目数已设为 {args.n}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())