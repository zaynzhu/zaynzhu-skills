---
name: mmy
description: 摸摸鱼热榜抓取器，支持登录获取订阅源（游民、NGA等）和匿名公开源。触发词包含 /mmy 系列命令。
compatibility:
  tools: [bash, python]
  requires:
    - Python >= 3.8
---

# 摸摸鱼热榜助手 (mmy)

基于 `momoyu.cc` 的热榜抓取工具，支持**登录模式**（获取订阅源）和**匿名模式**（公开源）。

核心脚本在 `scripts/momoyu_public_fetch.py`，快捷命令在 `commands/` 目录。

> **所有命令均从本 Skill 根目录（`SKILL.md` 所在目录）执行。**

## 两种模式

| 模式 | 说明 | 平台数 |
|------|------|--------|
| **匿名** | 默认，无需登录 | 13个公开源 |
| **登录** | 保存账号后获取订阅源 | 用户自选（含游民娱乐榜、NGA等私有源） |

登录凭证保存在 `scripts/mmy_credentials.json`（**不在 Git 中**）。

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
| `python commands/config.py show` | 显示完整配置（隐藏敏感信息） |
| `python commands/config.py sources zhihu,weibo,hupu` | 设置当前列表的平台 |
| `python commands/config.py dedup on` | 开启历史去重 |
| `python commands/config.py limit 15` | 设置每源条目数 |
| `python commands/login.py status` | 查看登录状态和订阅源 |
| `python commands/login.py save --email XX --password XX` | 保存账号密码 |
| `python commands/login.py save --token XX --connect-sid XX` | 手动保存会话 Cookie |
| `python commands/login.py open` | 浏览器打开登录页（手动复制 Cookie） |
| `python commands/login.py login` | 用已保存账号自动登录 |
| `python commands/login.py clear` | 清除凭证，回退匿名模式 |

## 对应关系

| 触发词 | 对应命令 |
|--------|----------|
| `/mmy` | `python commands/fetch.py` |
| `/mmy:setting` | `python commands/sources.py` + `python commands/config.py sources ...` |
| `/mmy:login` | `python commands/login.py status` |
| `/mmy:md` | `python commands/snapshot.py` |
| `/mmy:daily` | `python commands/daily.py` |
| `/mmy:open-N` | `python commands/open_urls.py N` |
| `/mmy:open-平台-N` | `python commands/open_urls.py --sources 平台 N` |
| `/mmy:list` | `python commands/lists.py show` |

## 登录流程

1. **首次登录**：运行 `python commands/login.py open` 在浏览器登录，然后从开发者工具复制 `token` 和 `connect.sid` Cookie
2. **保存 Cookie**：`python commands/login.py save --token "复制的token" --connect-sid "复制的sid"`
3. **查看状态**：`python commands/login.py status` 确认订阅源列表正确
4. **会话过期**：如果 `fetch.py` 提示会话过期，重新执行步骤 1-2

> 注意：`connect.sid` 约 30 天过期，过期后需重新登录获取。

## Windows 编码

Windows PowerShell 下必须加编码前缀：

```powershell
[console]::OutputEncoding=[System.Text.Encoding]::UTF8; python commands/fetch.py
```

Linux/macOS 下直接 `python commands/fetch.py`。

## 交互规范

1. **反馈及时**：耗时操作前先说"正在抓取，请稍候..."
2. **避免刷屏**：`snapshot`、`daily`、`open_urls` 只报告结果，不在对话中打印全部内容；只有 `fetch` 才需要打印
3. **会话检测**：如果登录会话过期（返回公开源而非订阅源），提示用户重新登录