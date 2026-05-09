#!/usr/bin/env python3
"""保存 Markdown 快照到文件（带时间戳文件名）"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from momoyu_public_fetch import (
    load_config,
    get_source_groups,
    filter_groups,
    render_markdown,
    load_history,
    save_history,
    deduplicate_groups,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="保存 Markdown 快照到文件")
    parser.add_argument("--sources", help="覆盖配置的平台（逗号分隔）")
    parser.add_argument("--output", help="输出文件名（默认自动生成）")
    args = parser.parse_args()

    config = load_config()
    active = config.get("active_list", "default")
    source_filters = args.sources or ",".join(config.get("lists", {}).get(active, []))

    groups = filter_groups(get_source_groups(), source_filters or None)

    removed_count = 0
    if config.get("deduplicate", False):
        history = load_history()
        groups, removed_count = deduplicate_groups(groups, history)
        save_history(history)

    fetched_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    limit = config.get("limit_per_source", 10)

    output = render_markdown(groups, fetched_at, limit)
    if config.get("deduplicate", False) and removed_count:
        output += f"\n\n*注：已过滤 {removed_count} 条已读历史记录*"

    filename = args.output or f"mmy-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    filepath = Path(filename).resolve()
    filepath.write_text(output, encoding="utf-8")
    print(filepath)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())