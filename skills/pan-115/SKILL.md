---
name: pan-115
description: 115 网盘集成，支持 115扫码登录/115扫码登陆、二维码图片交互获取 cookies、cookies 保存与验证、目录浏览、文件搜索、离线下载任务添加和任务查询。使用 p115client SDK，基于 cookies 认证。Use when the user asks about 115网盘, 115云盘, 115扫码登录, 115扫码登陆, 115离线下载, p115client, 115 pan, or 115 netdisk operations.
---

# pan-115 — 115 网盘助手

支持 115 App 扫码登录、cookies 保存与验证、目录浏览、文件搜索、添加离线下载任务和查看任务状态。

## 依赖准备

技能目录结构：

```text
pan-115/
├── SKILL.md
├── agents/
├── scripts/
└── requirements.txt
```

脚本分两类，依赖要求不同：

- **扫码登录**（`scripts/login.py`）和 cookies 保存（`scripts/save_cookies.py`）：只依赖 Python 标准库，Windows / macOS / Linux 可用，无需额外安装。
- **业务功能**（`scripts/browse.py`、`scripts/test_connection.py`、`scripts/offline_download.py`）：依赖 `p115client`，固定使用 Python 3.12 和锁定版本的依赖。

首次使用业务脚本前，在技能目录创建私有 `.venv` 并安装依赖：

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt   # Windows 用 .venv\Scripts\python.exe
```

`requirements.txt` 锁定了全部传递依赖版本，保证新安装时行为可复现。脚本检测到技能目录下的 `.venv` 后会自动切换到该环境运行，agent 不需要记住解释器路径；没有 `.venv` 时也可以直接用系统 Python 3.12 安装依赖。

安装后运行 `python -m py_compile scripts/*.py` 验证 Python 脚本语法；仅在 Windows/PowerShell 可用时检查 `scripts/get_cookie.ps1`。如果依赖安装失败，必须在安装阶段明确告知用户，而不是等扫码后才说缺少 `p115client`。

## Agent 兼容约定

本 skill 需要兼容 Codex、OpenClaw、Hermes 和普通 CLI 类 agent。扫码登录脚本不会假设某个平台一定能渲染 Markdown 图片，而是同时输出多种稳定标记：

- `LOGIN_QR_JSON`：紧凑 JSON，包含 `image_path`、`image_uri`、`remote_url`、`markdown`。
- `QR_IMAGE_PATH`：二维码 PNG 本地路径，适合能上传/展示本地图片的 agent。
- `QR_FILE_URI`：`file://` URI，适合能打开本地文件 URI 的 agent。
- `QR_REMOTE_URL`：115 二维码远程图片 URL，适合纯 CLI 或无法读取本地图片的 agent。
- `QR_MARKDOWN`：Markdown 图片语法，适合聊天界面支持本地图片渲染的 agent。

所有 agent 在运行 `scripts/login.py --no-open` 后，应监听 stdout；一旦看到 `AGENT_ACTION_REQUIRED`、`LOGIN_QR_JSON` 或上述任意二维码标记，就立即用自己支持的方式展示、打开或转述给用户，并保持进程继续运行等待用户扫码确认。单纯在 shell 输出里打印 `QR_MARKDOWN` 不等于已经把图片展示给用户。

对 Codex 这类通过工具执行命令的 agent，扫码登录属于长轮询任务，不能一直阻塞等待命令结束后才回复用户。应使用短暂等待启动命令（例如 `yield_time_ms: 1000`），读取首批 stdout；如果看到二维码标记，立刻在普通聊天消息中发送本地图片 Markdown（Codex 桌面端必须使用绝对路径），例如 `![115 登录二维码](C:\...\115-login-qrcode-xxx.png)`，然后再继续轮询后台进程直到登录成功或失败。如果首批输出还没有二维码标记，应继续读取进程输出，直到拿到二维码再展示。`--timeout 0` 只表示脚本不主动超时，115 的二维码 key 仍可能过期；通常保留默认超时即可。

## 快速开始

默认 cookies 路径为 `~/.115-cookies`。当目录浏览、搜索、离线下载等脚本发现该文件不存在或内容为空时，会自动提醒用户扫码登录、生成 115 登录二维码 PNG、等待用户用 115 App 扫码确认，并把 cookies 保存到 `~/.115-cookies`。

agent 看到脚本输出 `LOGIN_QR_JSON: ...`、`QR_IMAGE_PATH: ...`、`QR_FILE_URI: ...`、`QR_REMOTE_URL: ...` 或 `QR_MARKDOWN: ...` 后，应立即把二维码图片发给用户；Codex、OpenClaw、Hermes 或 CLI agent 都不应假设 shell 输出中的 Markdown 会自动弹图，必须由 agent 在普通回复中展示、打开或转述图片目标。如果图片发送失败，提醒用户打开该本地路径或远程 URL 扫码。扫码登录成功后，脚本会默认输出用户基本信息和本 skill 支持的功能点。

### 第一步：获取 Cookies

用户提供的 cookies 格式（4 个字段缺一不可）：
```
UID=xxx; CID=xxx; SEID=xxx; KID=xxx
```

跨平台默认方案：使用纯 Python 标准库登录脚本。agent 应优先运行这个命令，因为它在 Windows / macOS / Linux 上都可用，不依赖 PowerShell，也不依赖 `p115client`：

```bash
python scripts/login.py --no-open
```

如果当前系统只有 `python3` 或 Windows `py` launcher，则改用：

```bash
python3 scripts/login.py --no-open
py -3 scripts/login.py --no-open
```

脚本会把二维码保存为本地 PNG、输出 `AGENT_ACTION_REQUIRED`、`LOGIN_QR_JSON`、`QR_IMAGE_PATH`、`QR_FILE_URI`、`QR_REMOTE_URL` 和 `QR_MARKDOWN`，并继续轮询扫码状态。agent 应把二维码图片发给用户；如果图片没有成功显示，必须提醒用户打开脚本输出的二维码文件路径或远程 URL 自行扫码。用户用 115 App 扫码并确认后，脚本会自动获取 cookies 并默认保存到 `~/.115-cookies`。状态接口偶发 read timeout 时脚本会继续等待，不会立即退出。

可选参数：

```bash
# 指定二维码图片保存位置
python scripts/login.py --qr-path /tmp/115-login-qrcode.png --no-open

# 指定 cookies 保存位置
python scripts/login.py --cookie-path ~/.115-cookies --no-open

# 指定 app 类型，默认 tv
python scripts/login.py --app web --no-open
```

Windows 备用方案：如果用户没有合适的 Python，可用 PowerShell 脚本获取并保存 cookies。不要在 macOS/Linux 上把它作为默认路径：

```powershell
pwsh -ExecutionPolicy Bypass -File scripts/get_cookie.ps1 -NoOpen
```

PowerShell 脚本会把二维码保存为本地 PNG 并输出绝对路径，然后继续轮询扫码状态。agent 应在看到 `二维码图片已保存到：...` 后立刻把图片发给用户，例如：

```markdown
![115 登录二维码](C:\Users\...\AppData\Local\Temp\115-login-qrcode-xxx.png)
```

如果图片没有成功显示，必须提醒用户打开脚本输出的二维码文件路径自行扫码。用户用 115 App 扫码并确认后，脚本会自动获取 cookies 并默认保存到 `~/.115-cookies`。

可选参数：

```powershell
# 指定二维码图片保存位置
pwsh -ExecutionPolicy Bypass -File scripts/get_cookie.ps1 -QrPath "D:\115-login-qrcode.png" -NoOpen

# 允许脚本自动打开二维码图片
pwsh -ExecutionPolicy Bypass -File scripts/get_cookie.ps1

# 只打印 cookies，不保存
pwsh -ExecutionPolicy Bypass -File scripts/get_cookie.ps1 -NoSave

# 保存到指定路径
pwsh -ExecutionPolicy Bypass -File scripts/get_cookie.ps1 -CookiePath "D:\115-cookies.txt"

# 指定 app 类型，默认 tv
pwsh -ExecutionPolicy Bypass -File scripts/get_cookie.ps1 -App web
```

备用方案，如果用户已经手动拿到了 cookies，则保存并验证：

运行保存脚本（自动持久化到 `~/.115-cookies`）：

```bash
printf '%s' 'UID=xxx; CID=xxx; SEID=xxx; KID=xxx' | python3 scripts/save_cookies.py --stdin
```

或使用环境变量 / 交互式运行：
```bash
P115_COOKIES='UID=xxx; CID=xxx; SEID=xxx; KID=xxx' python3 scripts/save_cookies.py --env
python3 scripts/save_cookies.py
```

不推荐把 cookies 直接作为命令行参数传入，因为可能进入 shell 历史或进程列表。

### 第二步：测试连接

```bash
python3 scripts/test_connection.py
```

输出用户信息、存储空间、根目录预览即表示连接正常。

### 第三步：使用功能

```bash
# 浏览目录
python3 scripts/browse.py [目录ID]

# 添加离线下载
python3 scripts/offline_download.py 'magnet:?xt=urn:btih:xxx'

# 查看离线任务
python3 scripts/offline_download.py --list
```

## Cookies 持久化说明

- **标准路径：** `~/.115-cookies`（即 `/root/.115-cookies` 或 `/home/<user>/.115-cookies`）
- **格式：** 纯文本，单行，格式为 `UID=xxx; CID=xxx; SEID=xxx; KID=xxx`
- **权限：** 建议 `chmod 600` 仅本人可读写
- **过期：** Cookies 有有效期，过期后需用户重新扫码或从浏览器获取。脚本用 `Path` 对象初始化 `P115Client(Path(...))`（新版 p115client 已移除 `check_for_relogin` 参数）。
- **读取方式：** 普通字符串会被 p115client 当作 cookies 内容解析；如果要传文件路径，必须传 `pathlib.Path`/`os.PathLike`，或者先 `open().read()` 读取内容。

## ⚠️ 关键 Pitfalls

### 1. 不能把普通字符串路径传给 P115Client

```python
# ❌ 报错 ValueError: dictionary update sequence element #0 has length 1; 2 is required
client = P115Client("/path/to/cookies.txt")

# ✅ 正确：用 PathLike，续期后可写回文件
from pathlib import Path
client = P115Client(Path("/path/to/cookies.txt"))

# ✅ 也可以读取文件内容，但续期后的 cookies 不会自动写回这个文件
with open("/path/to/cookies.txt") as f:
    cookies = f.read().strip()
client = P115Client(cookies)
```

### 2. p115client 0.0.8.4.9 默认解析可能误判 JSON 响应

当前 skill 的 `scripts/lib.py` 会在导入 `p115client` 后修补 `default_parse`：使用响应首尾字节判断 JSON，避免 SDK 把普通 JSON 响应误当作加密内容解密后再解析，从而触发 `P115DataError` / `JSONDecodeError`。业务脚本应通过 `lib.get_client()` 初始化客户端，不要直接裸用 `P115Client(...)`。

### 3. tv cookies 与 web 文件接口登录态可能不通

默认扫码登录 app 仍为 `tv`，可用于扫码和部分账户/离线接口；目录浏览、搜索或存储接口如果返回“请先登录”“登录超时”“请重新登录”，请重新执行：

```bash
python scripts/login.py --app web --no-open
```

### 4. API 字段名是缩写

| 字段 | 含义 | 常见错误 |
|------|------|----------|
| `n` | 文件/文件夹名 | ❌ `name` |
| `s` | 文件大小 (bytes) | ❌ `size` |
| `cid` | 目录 ID | ❌ `folder_id` |
| `fc` | 子项数量 | ❌ `count` |
| `pid` | 父目录 ID | ❌ `parent_id` |
| `pc` | pick code (下载用) | ❌ `pick_code` |
| `t` | 修改时间 (unix) | ❌ `mtime` |

### 5. Web API 在服务器上返回 405

`fs_files()` 从服务器 IP 调用会被拦截。**必须用 `fs_files_aps()`**，参数相同：

```python
# ❌ 服务器上会 405
result = client.fs_files({"cid": dir_id, "limit": 100})

# ✅ 用这个
result = client.fs_files_aps({"cid": dir_id, "limit": 100})
```

### 6. 响应结构

```python
{
    "state": true,
    "data": [  # 直接是列表
        {"cid": "xxx", "n": "文件夹名", "fc": 5, ...},   # 有 cid = 文件夹
        {"fid": "xxx", "n": "文件名", "s": 1048576, ...}  # 有 fid = 文件
    ]
}
```

## 常用 API 速查

```python
from p115client import P115Client

# 初始化
with open(os.path.expanduser("~/.115-cookies")) as f:
    client = P115Client(f.read().strip())

# 用户信息
info = client.user_info()  # info['data']['user_name'], info['data']['is_vip']

# 存储空间
space = client.fs_storage_info()  # {type_id: {total, used}, ...}

# 浏览目录
items = client.fs_files_aps({"cid": 0, "limit": 100})['data']

# 搜索文件
result = client.fs_search({"search_value": "关键词", "limit": 50})

# 获取下载链接
url = client.download_url({"pick_code": "xxx"})

# 离线下载（磁力/ed2k/HTTP）——新版 p115client 方法名为 clouddownload_task_*
client.clouddownload_task_add_url({"url": "magnet:?xt=urn:btih:xxx"})

# 指定保存相对目录用 savepath；指定目录 ID 用 wp_path_id
client.clouddownload_task_add_url({"url": "https://example.com/file.zip", "savepath": "downloads"})

# 离线任务列表（payload 可传页码 int 或 {page, page_size, stat}）
tasks = client.clouddownload_task_list()  # tasks['quota'], tasks['total'], tasks['count'], tasks['tasks']

# 离线下载目录
paths = client.clouddownload_downpath()  # paths['data'] = [{file_id, file_name, is_selected}, ...]

# 创建文件夹
client.fs_mkdir({"cname": "新文件夹", "pid": 0})

# 删除文件
client.fs_delete({"file_id": "xxx"})
```

## 相关资源

- p115client 文档: https://p115client.readthedocs.io/
- GitHub: https://github.com/ChenyangGao/p115client
- 115 开放平台: https://open.115.com/
