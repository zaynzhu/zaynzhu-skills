#!/usr/bin/env python3
"""
resolve_repos.py
补全截断的项目名 → 完整的 owner/repo

用法：
  python3 resolve_repos.py --names "mempalace,hermes-agent,everything-clau..."
  python3 resolve_repos.py --file names.txt  # 每行一个项目名
  python3 resolve_repos.py --names "openclaw" --token ghp_xxx
"""

import argparse
import json
import os
import subprocess
import sys
import time


# 已知映射表（从历史榜单积累的加速缓存，非权威数据：榜单换血后条目会过期，
# 前缀匹配也可能把新项目错解析到旧仓库；可整段清理，清理后仍走 GitHub 搜索兜底）
KNOWN_REPOS = {
    "mempalace": "milla-jovovich/mempalace",
    "hermes-agent": "NousResearch/hermes-agent",
    "graphify": "safishamsi/graphify",
    "career-ops": "santifer/career-ops",
    "claw-code": "ultraworkers/claw-code",
    "everything-claude": "affaan-m/everything-claude-code",
    "everything-clau": "affaan-m/everything-claude-code",
    "caveman": "JuliusBrussee/caveman",
    "superpowers": "obra/superpowers",
    "openscreen": "siddharthvaddem/openscreen",
    "markitdown": "microsoft/markitdown",
    "openclaw": "openclaw/openclaw",
    "agency-agents": "msitarzewski/agency-agents",
    "agent-skills": "addyosmani/agent-skills",
    "rtk": "rtk-ai/rtk",
    "andrej-karpathy-skills": "forrestchang/andrej-karpathy-skills",
    "andrej-karpathy": "forrestchang/andrej-karpathy-skills",
    "gstack": "garrytan/gstack",
    "goose": "aaif-goose/goose",
    "deeptutor": "HKUDS/DeepTutor",
    "claude-code-best": "shanraisshan/claude-code-best-practice",
    "claude-code-best-practice": "shanraisshan/claude-code-best-practice",
}


def github_search_repo(name: str, token: str = None) -> list:
    """搜索 GitHub 仓库，返回候选列表"""
    # 去掉省略号
    clean_name = name.rstrip(".").rstrip("…")
    
    url = (
        f"https://api.github.com/search/repositories"
        f"?q={clean_name}+in:name&sort=stars&order=desc&per_page=5"
    )
    cmd = ["curl", "-s", url, "-H", "Accept: application/vnd.github.v3+json"]
    if token:
        cmd += ["-H", f"Authorization: token {token}"]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    try:
        data = json.loads(result.stdout)
        return [
            {
                "full_name": item["full_name"],
                "stars": item["stargazers_count"],
                "description": (item.get("description") or "")[:60],
                "updated_at": item.get("updated_at", "")[:10],
                "topics": item.get("topics", []),
            }
            for item in data.get("items", [])
        ]
    except (json.JSONDecodeError, KeyError):
        return []


def resolve_name(name: str, token: str = None) -> dict:
    """
    解析单个项目名 → 完整 repo
    返回：{"query", "full_name", "stars", "confidence", "candidates"}
    """
    name_lower = name.lower().rstrip(".")
    
    # 1. 命中已知映射
    for key, full_name in KNOWN_REPOS.items():
        if name_lower == key or name_lower.startswith(key[:8]):
            return {
                "query": name,
                "full_name": full_name,
                "confidence": "known",
                "candidates": [],
            }
    
    # 2. 搜索 GitHub
    candidates = github_search_repo(name, token)
    
    if not candidates:
        return {
            "query": name,
            "full_name": None,
            "confidence": "not_found",
            "candidates": [],
        }
    
    # 3. 评分：名字前缀匹配 + star 数量
    clean = name.lower().rstrip(".")
    
    def score(c):
        repo_name = c["full_name"].split("/")[1].lower()
        prefix_match = repo_name.startswith(clean[:min(len(clean), 8)])
        exact_match = repo_name == clean
        return (exact_match * 10) + (prefix_match * 5) + min(c["stars"] / 1000, 5)
    
    candidates.sort(key=score, reverse=True)
    best = candidates[0]
    confidence = "high" if score(best) >= 10 else ("medium" if score(best) >= 5 else "low")
    
    return {
        "query": name,
        "full_name": best["full_name"],
        "stars": best["stars"],
        "confidence": confidence,
        "candidates": candidates[:3] if confidence == "low" else [],
    }


def main():
    parser = argparse.ArgumentParser(description="补全截断的 GitHub 项目名")
    parser.add_argument("--names", help="逗号分隔的项目名")
    parser.add_argument("--file", help="每行一个项目名的文件")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"))
    parser.add_argument("--output", default="resolved_repos.json")
    args = parser.parse_args()

    names = []
    if args.names:
        names = [n.strip() for n in args.names.split(",") if n.strip()]
    elif args.file:
        with open(args.file) as f:
            names = [line.strip() for line in f if line.strip()]
    else:
        print("[ERROR] 请提供 --names 或 --file", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] 解析 {len(names)} 个项目名...", file=sys.stderr)
    
    results = []
    for name in names:
        r = resolve_name(name, args.token)
        results.append(r)
        
        status = {
            "known": "✓ 已知",
            "high": "✓ 高置信",
            "medium": "? 中置信",
            "low": "! 低置信",
            "not_found": "✗ 未找到",
        }.get(r["confidence"], "?")
        
        print(f"  {status} {name:25s} → {r['full_name'] or '未找到'}", file=sys.stderr)
        
        if r["confidence"] not in ("known", "high"):
            time.sleep(0.3)  # 避免速率限制
    
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n[OK] 结果已保存到 {args.output}", file=sys.stderr)
    
    # 输出需要人工确认的项目
    uncertain = [r for r in results if r["confidence"] in ("low", "medium", "not_found")]
    if uncertain:
        print(f"\n⚠️  以下 {len(uncertain)} 个项目需要人工确认：")
        for r in uncertain:
            print(f"  - {r['query']} → 当前猜测: {r['full_name']}")
            for c in r.get("candidates", [])[:3]:
                print(f"      候选: {c['full_name']} ({c['stars']:,}⭐) {c['description'][:40]}")
    
    # 输出补全后的列表
    full_names = [r["full_name"] for r in results if r["full_name"]]
    print("\n完整 repo 列表（可直接传给 fetch_github_details.py）：")
    print(",".join(full_names))


if __name__ == "__main__":
    main()
