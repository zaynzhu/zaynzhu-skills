#!/usr/bin/env python3
"""查看和管理关注列表"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from momoyu_public_fetch import load_config, save_config


def show_lists(config: dict) -> None:
    active = config.get("active_list", "default")
    lists = config.get("lists", {})
    for name, sources in lists.items():
        marker = " (当前激活)" if name == active else ""
        print(f"  {'*' if name == active else ' '} {name}{marker}: {', '.join(sources) if sources else '(空)'}")


def main() -> int:
    parser = argparse.ArgumentParser(description="查看和管理关注列表")
    sub = parser.add_subparsers(dest="action")

    sub.add_parser("show", help="显示所有列表")

    sw = sub.add_parser("switch", help="切换激活列表")
    sw.add_argument("name", help="列表名称")

    add = sub.add_parser("add", help="新建列表")
    add.add_argument("name", help="列表名称")
    add.add_argument("--sources", default="", help="平台列表（逗号分隔）")

    rm = sub.add_parser("remove", help="删除列表")
    rm.add_argument("name", help="列表名称")

    args = parser.parse_args()
    config = load_config()

    if args.action == "show" or args.action is None:
        print(f"当前激活列表: {config.get('active_list', 'default')}")
        print(f"去重: {'开启' if config.get('deduplicate') else '关闭'}")
        print(f"每源条目数: {config.get('limit_per_source', 10)}")
        print()
        show_lists(config)

    elif args.action == "switch":
        if args.name not in config.get("lists", {}):
            print(f"列表 '{args.name}' 不存在", file=sys.stderr)
            return 1
        config["active_list"] = args.name
        save_config(config)
        print(f"已切换到列表: {args.name}")

    elif args.action == "add":
        sources = [s.strip() for s in args.sources.split(",") if s.strip()] if args.sources else []
        config.setdefault("lists", {})[args.name] = sources
        save_config(config)
        print(f"已创建列表: {args.name} ({', '.join(sources) if sources else '空'})")

    elif args.action == "remove":
        if args.name == "default":
            print("不能删除默认列表", file=sys.stderr)
            return 1
        config.get("lists", {}).pop(args.name, None)
        if config.get("active_list") == args.name:
            config["active_list"] = "default"
        save_config(config)
        print(f"已删除列表: {args.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())