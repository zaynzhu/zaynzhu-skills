# momoyu-fetch (mmy)

基于 momoyu.cc 的跨平台公开热榜抓取工具。

## 功能

- 13 个公开热榜源（知乎、微博、B 站、抖音等）
- 登录模式获取订阅源（游民、NGA 等）
- 快照保存 / 日报生成
- 关注列表管理
- 一键浏览器打开热榜链接

## 依赖

- Python ≥ 3.8
- 无需额外包

## 快速开始

```powershell
# Windows 下需要先设置编码
[console]::OutputEncoding=[System.Text.Encoding]::UTF8

# 查看当前热榜
cd skills/mmy
python commands/fetch.py

# 指定平台
python commands/fetch.py --sources zhihu,weibo

# 查看所有可用平台
python commands/sources.py

# 保存快照
python commands/snapshot.py

# 生成日报
python commands/daily.py

# 在浏览器打开前 5 条
python commands/open_urls.py 5
```

## 触发词

| 触发词 | 对应命令 |
|--------|----------|
| `/mmy` | 显示当前热榜 |
| `/mmy:setting` | 查看和设置平台 |
| `/mmy:login` | 登录管理 |
| `/mmy:md` | 保存 Markdown 快照 |
| `/mmy:daily` | 生成日报 |
| `/mmy:open-N` | 浏览器打开前 N 条 |

## 登录模式

```powershell
# 首次登录：浏览器打开登录页，手动复制 Cookie
python commands/login.py open

# 保存 Cookie
python commands/login.py save --token "复制的token" --connect-sid "复制的sid"

# 查看登录状态
python commands/login.py status
```

> Cookie 约 30 天过期，过期后需重新登录获取。

## 文件结构

```
mmy/
├── SKILL.md      ← 主指令
├── commands/     ← 快捷命令脚本
└── scripts/      ← 核心抓取脚本
```