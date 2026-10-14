# BTBTLA / 1LOU Network Failures and 1LOU direct search workaround

## OpenSSL Invalid Library Troubleshooting (`invalid library (0):OPENSSL_internal`)
If `curl_cffi` fails immediately with:
`TLS connect error: error:00000000:invalid library (0):OPENSSL_internal`
This indicates the local Python virtual environment (`.venv`) has compiled/installed `curl_cffi` against a corrupted or mismatched OpenSSL/BoringSSL shared library. 
- **Fix**: Override the python path used by the script by setting the `BT_SEARCH_PYTHON` environment variable:
  ```bash
  export BT_SEARCH_PYTHON=python3
  ```
  The system `python3` usually has a fully functioning ssl module and clean `curl_cffi` installation.

## Problem Statement
Historical note: the old `www.btbtla.com` domain is parked. The current BT影视 domain used by the skill is `www.btbtlb.com`. The material below documents the old outage and should not be used as the current endpoint.

`www.btbtla.com` frequently failed to resolve or connect in restricted network environments (such as behind domestic transits or transparent proxies) due to:
1. **DNS Poisoning**: The domain is often poisoned at the DNS level (resolving to Facebook edge IPs such as `31.13.70.33` or WhatsApp IPs).
2. **GFW SNI Blocking**: Even with correct IP overrides in `/etc/hosts` (e.g. mapping to Cloudflare IPs like `104.21.58.122`), direct TLS handshakes receive `SSL_ERROR_SYSCALL` (connection resets) because the SNI string `www.btbtla.com` is actively blocked.

## The Workaround: Direct 1LOU Forum Crawling
BTBTLA is primarily an indexer portal for the torrent files hosted on the **BT之家1LOU站 (1lou.me)** forum. Because `www.1lou.me` runs on a different domain and uses a BBS structure (Xiuno BBS), it is often not SNI-blocked and remains fully accessible (returning `200 OK`).

If BTBTLA queries timeout or fail, you can bypass the indexer completely and scrape the forum directly.

### Step-by-Step Flow

1. **Search**:
   - Query URL: `https://www.1lou.me/search-{urlencoded_query}.htm`
   - Method: Use Python's `curl_cffi` to bypass Cloudflare protection on the forum.
   - Parsing: Locate thread links matching `thread-\d+\.htm` and their corresponding titles.

2. **Retrieve Thread & Attachments**:
   - Fetch the thread page (e.g., `https://www.1lou.me/thread-1015547.htm`).
   - Parse the attachment download link: Look for `attach-download-\d+\.htm`.
   - Download the attachment directly. It returns `content-type: application/octet-stream` containing the raw `.torrent` file binary data.

3. **Push to qBittorrent**:
   - Do NOT submit via magnet links if you only have the torrent file.
   - Send the binary torrent data as `multipart/form-data` to the `/api/v2/torrents/add` endpoint of qBittorrent.

### Python Automation Recipe

```python
import urllib.request, urllib.parse, http.cookiejar
import re, base64
from curl_cffi.requests import Session

# 1. Search 1lou.me
s = Session()
query_encoded = urllib.parse.quote("师兄啊师兄")
search_url = f"https://www.1lou.me/search-{query_encoded}.htm"
r = s.get(search_url, impersonate="chrome", timeout=10)

# 2. Match threads (Xiuno search list)
threads = re.findall(r"<a href=\"(thread-\d+\.htm)\"[^>]*>(.*?)</a>", r.text, re.DOTALL)
# Filter for the relevant episode thread, e.g. Episode 149
target_thread_url = "https://www.1lou.me/thread-1015547.htm"

# 3. Fetch thread page & download torrent
r_thread = s.get(target_thread_url, impersonate="chrome", timeout=10)
attach_id = re.search(r"attach-download-(\d+)\.htm", r_thread.text).group(1)
torrent_url = f"https://www.1lou.me/attach-download-{attach_id}.htm"

r_torrent = s.get(torrent_url, impersonate="chrome", timeout=15)
torrent_bytes = r_torrent.content # Raw torrent binary

# 4. Upload to qBittorrent WebAPI
QB_URL = "http://<qB地址>:<端口>"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Login
login_data = urllib.parse.urlencode({"username": "<qB用户名>", "password": "<qB密码>"}).encode("utf-8")
headers = {"Referer": QB_URL, "Origin": QB_URL}
req_login = urllib.request.Request(f"{QB_URL}/api/v2/auth/login", data=login_data, headers=headers)
opener.open(req_login)

# Upload torrent
boundary = "----WebKitFormBoundary8M5Txi6bld3QlhWK"
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="torrents"; filename="torrent.torrent"\r\n'
    f"Content-Type: application/x-bittorrent\r\n\r\n"
).encode("utf-8")
body += torrent_bytes
body += (
    f"\r\n--{boundary}\r\n"
    f'Content-Disposition: form-data; name="savepath"\r\n\r\n'
    f"<下载保存目录>\r\n"
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="category"\r\n\r\n'
    f"<分类>\r\n"
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="tags"\r\n\r\n'
    f"<标签>\r\n"
    f"--{boundary}--\r\n"
).encode("utf-8")

req_add = urllib.request.Request(
    f"{QB_URL}/api/v2/torrents/add", 
    data=body, 
    headers={
        "Referer": f"{QB_URL}/", 
        "Origin": QB_URL,
        "Content-Type": f"multipart/form-data; boundary={boundary}"
    }
)
with opener.open(req_add, timeout=10) as resp:
    print("Status:", resp.status, resp.read().decode())
```
