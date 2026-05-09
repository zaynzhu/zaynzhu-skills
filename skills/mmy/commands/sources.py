#!/usr/bin/env python3
"""列出所有可用平台源"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from momoyu_public_fetch import get_source_groups


def main() -> int:
    parser = argparse.ArgumentParser(description="列出所有可用平台源")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    groups = get_source_groups()
    for group in groups[: args.limit]:
        print(f'{group["id"]:>4}  {group.get("source_key", ""):<16}  {group["name"]}')

    return 0


if __name__ == "__main__":
    raise SystemExit(main())