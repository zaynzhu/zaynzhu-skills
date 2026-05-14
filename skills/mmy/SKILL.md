---
name: mmy
description: 摸摸鱼公开热榜抓取器，支持在对话中读取、配置平台、去重历史、生成 Markdown 日报和一键打开浏览器功能。触发词包含 /mmy 系列命令。
compatibility:
  tools: [bash, python]
  requires:
    - Python >= 3.8
---

# 摸摸鱼热榜助手 (mmy)

基于 `momoyu.cc` 公开接口的热榜抓取工具。核心脚本在 `scripts/momoyu_public_fetch.py`，快捷命令在 `commands/` 目录。

> **所有命令均从本 Skill 根目录（`SKILL.md` 所在目录）执行。**

## 命令速查

| 命令 | 用途 |
|------|------|
| `python commands/fetch.py` | 在对话中显示当前热榜（`/mmy`） |
| `python commands/fetch.py --sources zhihu,weibo` | 指定平台抓取 |
| `python commands/fetch.py --format json` | JSON 格式输出 |
| `python commands/sources.py` | 列出所有可用平台 |
| `python commands/snapshot.py` | 保存 Markdown 快照文件 |
| `python commands/daily.py` | 生成当日汇总日报 |
| `python commands/open_urls.py 5` | 在浏览器打开前 5 条 |
| `python commands/open_urls.py --sources zhihu 3` | 只打开知乎前 3 条 |
| `python commands/lists.py show` | 查看所有关注列表 |
| `python commands/lists.py add tech --sources github,csdn` | 新建列表 |
| `python commands/lists.py switch tech` | 切换激活列表 |
| `python commands/lists.py remove tech` | 删除列表 |
| `python commands/config.py show` | 显示完整配置 |
| `python commands/config.py sources zhihu,weibo,hupu` | 设置当前列表的平台 |
| `python commands/config.py dedup on` | 开启历史去重 |
| `python commands/config.py limit 15` | 设置每源条目数 |

## 对应关系

| 触发词 | 对应命令 |
|--------|----------|
| `/mmy` | `python commands/fetch.py` |
| `/mmy:setting` | `python commands/sources.py` + `python commands/config.py sources ...` |
| `/mmy:md` | `python commands/snapshot.py` |
| `/mmy:daily` | `python commands/daily.py` |
| `/mmy:open-N` | `python commands/open_urls.py N` |
| `/mmy:open-平台-N` | `python commands/open_urls.py --sources 平台 N` |
| `/mmy:list` | `python commands/lists.py show` |

## Windows 编码

Windows PowerShell 下必须加编码前缀：

```powershell
[console]::OutputEncoding=[System.Text.Encoding]::UTF8; python commands/fetch.py
```

Linux/macOS 下直接 `python commands/fetch.py`。

## 交互规范

1. **反馈及时**：耗时操作前先说"正在抓取，请稍候..."
2. **避免刷屏**：`snapshot`、`daily`、`open_urls` 只报告结果，不在对话中打印全部内容；只有 `fetch` 才需要打印
3. **配置先行**：如果是第一次使用，先跑 `python commands/sources.py` 让用户选择平台