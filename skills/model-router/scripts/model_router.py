#!/usr/bin/env python3
"""Model Router - 核心路由引擎

从任意 CLI 工具调用，根据任务类型选择并调用合适的模型。
支持 fallback 链、成本感知路由、查询自动分类。

用法:
    python model_router.py route --task has_image_input --prompt "描述这张图片" --image /path/to/image.png
    python model_router.py route --task complex_reasoning --prompt "分析这段代码的架构"
    python model_router.py route --profile gpt4o --prompt "你好"
    python model_router.py route --auto-task --prompt "帮我看看这个截图" --image shot.png
    python model_router.py route --task quick_task --cost cheapest --prompt "重命名这个文件"
"""

import argparse
import base64
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Windows 编码修复：确保 stdout/stderr 用 UTF-8
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR.parent / "model-router.yaml"
CONFIG_JSON_PATH = SCRIPT_DIR.parent / "model-router.json"
WORKSPACE_DIR_NAME = ".model-router"
IMAGES_DIR_NAME = "images"
RESULTS_DIR_NAME = "results"

# 可重试的 HTTP 状态码
RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}


def load_env():
    """加载 .env 文件中的环境变量（如果 python-dotenv 可用）。"""
    env_path = SCRIPT_DIR.parent / ".env"
    if env_path.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path, override=True)
        except ImportError:
            # 没有 python-dotenv，手动解析
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip("'\"")
                    os.environ.setdefault(key, value)


def load_config():
    """加载配置文件。"""
    load_env()  # 确保环境变量已加载
    if CONFIG_JSON_PATH.exists():
        with open(CONFIG_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    if CONFIG_PATH.exists():
        sys.path.insert(0, str(SCRIPT_DIR))
        from model_config import parse_yaml_simple
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return parse_yaml_simple(f.read())
    raise FileNotFoundError("配置文件不存在。请先运行 'python model_config.py add' 添加模型。")


def prepare_workspace(root="."):
    """创建项目级图片中转目录，避免把图片 payload 直接交给不支持视觉的主模型。"""
    project_root = Path(root).expanduser().resolve()
    workspace_dir = project_root / WORKSPACE_DIR_NAME
    images_dir = workspace_dir / IMAGES_DIR_NAME
    results_dir = workspace_dir / RESULTS_DIR_NAME

    images_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    return {
        "project_root": str(project_root),
        "workspace_dir": str(workspace_dir),
        "images_dir": str(images_dir),
        "results_dir": str(results_dir),
    }


# ---------------------------------------------------------------------------
# 查询分类器
# ---------------------------------------------------------------------------

def _approx_word_count(text):
    """近似词数：中文按字计，英文按词计。"""
    cjk = len(re.findall(r'[一-鿿　-〿＀-￯]', text))
    non_cjk = len(re.findall(r'[a-zA-Z0-9]+', text))
    return cjk + non_cjk


def classify_query(prompt, has_image=False):
    """分析查询内容，返回 (task_type, confidence)。

    基于规则的启发式分类器，零外部依赖。
    """
    if has_image:
        return "has_image_input", 1.0

    lower = prompt.lower()

    # 图片关键词
    image_kw = r"(图片|截图|验证码|screenshot|captcha|ocr|识别一下|看图|照片|png|jpg|jpeg|gif|webp|图表|chart|diagram)"
    if re.search(image_kw, lower):
        return "has_image_input", 0.8

    # 复杂推理 — 深度关键词 + 长查询
    reasoning_kw = (
        r"(分析|架构|设计|审查|review|debug|优化|重构|refactor|"
        r"为什么|解释原理|explain.*architecture|compare.*trade.?off|"
        r"安全审计|security|性能分析|benchmark|设计方案)"
    )
    word_count = _approx_word_count(prompt)
    has_reasoning_kw = bool(re.search(reasoning_kw, lower))

    if word_count > 100 or (word_count > 30 and has_reasoning_kw):
        return "complex_reasoning", 0.9
    if has_reasoning_kw:
        return "complex_reasoning", 0.6

    # 轻量任务 — 短查询 + 简单操作
    quick_kw = (
        r"(重命名|格式化|转换|rename|format|convert|翻译|translate|"
        r"列出|list|查找|find|替换|replace|缩进|indent|排序|sort|"
        r"拼写|spell|总结|summarize|简述)"
    )
    if word_count < 20 or re.search(quick_kw, lower):
        return "quick_task", 0.7

    return "general", 0.5


# ---------------------------------------------------------------------------
# 候选选择（带成本排序）
# ---------------------------------------------------------------------------

def _profile_cost(profile):
    """计算 profile 的综合成本（input + output per 1M tokens）。"""
    cost = profile.get("cost", {})
    return cost.get("input_per_1m", 0) + cost.get("output_per_1m", 0)


def select_candidates(config, task_type=None, profile_name=None, cost_mode=None):
    """返回按优先级排序的候选 (name, profile) 列表。"""
    profiles = config.get("profiles", {})
    routing = config.get("routing", [])

    # 直接指定 profile
    if profile_name:
        if profile_name in profiles:
            return [(profile_name, profiles[profile_name])]
        raise KeyError(f"profile '{profile_name}' 不存在")

    candidates = []
    effective_cost_mode = cost_mode
    default_profile_name = config.get("default_profile")

    if task_type:
        for rule in routing:
            if rule["match"] == task_type:
                # 如果没指定 cost_mode，从 routing 规则继承
                if effective_cost_mode is None:
                    effective_cost_mode = rule.get("cost_mode", "balanced")
                for name in rule.get("prefer", []):
                    if name in profiles:
                        p = profiles[name]
                        env_key = p.get("api_key_env")
                        if env_key is None or os.environ.get(env_key):
                            candidates.append((name, p))
                break

    # 兜底：把 routing 里没列到的可用 profile 也加进来
    for name, p in profiles.items():
        if name not in [c[0] for c in candidates]:
            env_key = p.get("api_key_env")
            if env_key is None or os.environ.get(env_key):
                candidates.append((name, p))

    # 成本排序
    if effective_cost_mode == "cheapest":
        candidates.sort(key=lambda c: _profile_cost(c[1]))
    elif effective_cost_mode == "best":
        candidates.sort(key=lambda c: -_profile_cost(c[1]))
    # balanced: 保持原始顺序

    # setting 配置的默认模型始终先尝试，不受成本排序影响
    if default_profile_name:
        for index, candidate in enumerate(candidates):
            if candidate[0] == default_profile_name:
                candidates.insert(0, candidates.pop(index))
                break

    return candidates


# ---------------------------------------------------------------------------
# 图片编码
# ---------------------------------------------------------------------------

def encode_image(image_path):
    """将图片文件编码为 base64。"""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"图片文件不存在: {image_path}")

    suffix = path.suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }
    mime = mime_map.get(suffix, "image/png")

    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")

    return mime, data


# ---------------------------------------------------------------------------
# API 请求构造
# ---------------------------------------------------------------------------

def build_request(profile, prompt, image_path=None, image_url=None):
    """构造 API 请求。"""
    provider = profile["provider"]
    model = profile["model"]
    endpoint = profile["endpoint"]
    max_tokens = profile.get("max_tokens", 4096)

    headers = {}
    body = {}

    if provider == "openai":
        content = [{"type": "text", "text": prompt}]
        if image_path:
            mime, data = encode_image(image_path)
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{data}"},
            })
        elif image_url:
            content.append({
                "type": "image_url",
                "image_url": {"url": image_url},
            })

        body = json.dumps({
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": content}],
        })
        env_key = profile.get("api_key_env") or ""
        headers = {
            "Authorization": f"Bearer {os.environ.get(env_key, '')}",
            "Content-Type": "application/json",
        }

    elif provider == "anthropic":
        content = []
        if image_path:
            mime, data = encode_image(image_path)
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime,
                    "data": data,
                },
            })
        elif image_url:
            # Anthropic API 不支持 URL 类型的图片源，需要下载后以 base64 发送
            import urllib.request as urlreq
            try:
                with urlreq.urlopen(image_url, timeout=30) as resp:
                    img_bytes = resp.read()
                # 从 URL 推断 MIME 类型
                url_path = image_url.split("?")[0].lower()
                mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                            ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp"}
                suffix = "." + url_path.rsplit(".", 1)[-1] if "." in url_path else ".png"
                mime = mime_map.get(suffix, "image/png")
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime,
                        "data": base64.b64encode(img_bytes).decode("utf-8"),
                    },
                })
            except Exception as e:
                raise RuntimeError(f"无法下载图片 URL: {image_url}, 错误: {e}")
        content.append({"type": "text", "text": prompt})
        body = json.dumps({
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": content}],
        })
        env_key = profile.get("api_key_env") or ""
        headers = {
            "x-api-key": os.environ.get(env_key, ""),
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    elif provider == "google":
        endpoint = endpoint.replace("{model}", model)
        parts = [{"text": prompt}]
        if image_path:
            mime, data = encode_image(image_path)
            parts.append({"inline_data": {"mime_type": mime, "data": data}})
        elif image_url:
            parts.append({"file_data": {"mime_type": "image/png", "file_uri": image_url}})

        body = json.dumps({"contents": [{"parts": parts}]})
        env_key = profile.get("api_key_env") or ""
        api_key = os.environ.get(env_key, "")
        endpoint = f"{endpoint}?key={api_key}"
        headers = {"Content-Type": "application/json"}

    elif provider == "ollama":
        req = {"model": model, "prompt": prompt, "stream": False}
        if image_path:
            _, data = encode_image(image_path)
            req["images"] = [data]
        body = json.dumps(req)
        headers = {"Content-Type": "application/json"}

    else:
        body = json.dumps({"model": model, "prompt": prompt})
        env_key = profile.get("api_key_env", "")
        api_key = os.environ.get(env_key, "") if env_key else ""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    return endpoint, headers, body


# ---------------------------------------------------------------------------
# 响应解析
# ---------------------------------------------------------------------------

def _safe_first(lst, default=""):
    """安全取列表第一个元素，处理空列表和 None 元素。"""
    if not lst:
        return default
    item = lst[0]
    return item if item is not None else default


def extract_response(provider, response_json):
    """从 API 响应中提取文本。"""
    if provider == "openai":
        if "choices" not in response_json:
            return f"[调用失败: API 返回异常 {json.dumps(response_json, ensure_ascii=False)[:200]}]"
        return _safe_first(response_json["choices"], {}).get("message", {}).get("content", "")
    elif provider == "anthropic":
        if "content" not in response_json:
            return f"[调用失败: API 返回异常 {json.dumps(response_json, ensure_ascii=False)[:200]}]"
        return _safe_first(response_json["content"], {}).get("text", "")
    elif provider == "google":
        if "candidates" not in response_json:
            return f"[调用失败: API 返回异常 {json.dumps(response_json, ensure_ascii=False)[:200]}]"
        candidate = _safe_first(response_json["candidates"], {})
        parts = candidate.get("content", {}).get("parts", [{}])
        return _safe_first(parts, {}).get("text", "")
    elif provider == "ollama":
        if "error" in response_json:
            return f"[调用失败: {response_json['error']}]"
        return response_json.get("response", "")
    else:
        return json.dumps(response_json, ensure_ascii=False)


# ---------------------------------------------------------------------------
# API 调用（带状态码检测）
# ---------------------------------------------------------------------------

def call_api(endpoint, headers, body, timeout=60):
    """用 curl 调用 API。区分可重试/不可重试错误。通过 stdin 管道传 body，避免 Windows 命令行长度限制。"""
    cmd = ["curl", "-s", "--max-time", str(timeout), "-w", "\n%{http_code}"]

    for k, v in headers.items():
        cmd.extend(["-H", f"{k}: {v}"])

    cmd.extend(["-d", "@-", endpoint])

    result = subprocess.run(cmd, input=body, capture_output=True, text=True, timeout=timeout + 10, encoding="utf-8", errors="replace")

    if result.returncode != 0:
        raise RuntimeError(f"curl 失败: {result.stderr}")

    # 分离 body 和 status code（curl -w 追加在末尾）
    output = result.stdout.strip()
    lines = output.rsplit("\n", 1)
    if len(lines) == 2 and lines[1].strip().isdigit():
        code = int(lines[1].strip())
        if 100 <= code <= 599:
            resp_body = lines[0]
            status_code = code
        else:
            resp_body = output
            status_code = 200
    else:
        resp_body = output
        status_code = 200

    if status_code in RETRYABLE_STATUS:
        raise RuntimeError(f"HTTP {status_code}（可重试）")
    if status_code >= 400:
        raise RuntimeError(f"HTTP {status_code}（不可重试）: {resp_body[:200]}")

    return json.loads(resp_body)


# ---------------------------------------------------------------------------
# 主路由函数（带 fallback 链）
# ---------------------------------------------------------------------------

def route(task_type=None, profile_name=None, prompt=None,
          image_path=None, image_url=None, cost_mode=None, auto_task=False):
    """主路由函数。返回 (profile_name, profile, response_text)。"""
    config = load_config()

    # 自动分类
    if auto_task and not task_type and not profile_name:
        has_img = bool(image_path or image_url)
        task_type, confidence = classify_query(prompt or "", has_img)
        print(f"--- [Auto Classify] ---", file=sys.stderr)
        print(f"检测任务: {task_type} (置信度: {confidence:.0%})", file=sys.stderr)

    candidates = select_candidates(config, task_type, profile_name, cost_mode)

    if not candidates:
        raise ValueError("没有可用的模型。请运行 'python model_config.py add' 添加模型。")

    if not prompt:
        raise ValueError("必须提供 --prompt 参数")

    last_error = None
    tried = []

    for name, profile in candidates:
        try:
            print(f"--- [Model Router] ---", file=sys.stderr)
            print(f"尝试: {name} ({profile.get('provider')}/{profile.get('model')})", file=sys.stderr)
            print(f"任务: {task_type or 'direct'}", file=sys.stderr)
            if cost_mode:
                print(f"成本模式: {cost_mode}", file=sys.stderr)
            print(f"--- 调用中... ---", file=sys.stderr)

            endpoint, headers, body = build_request(profile, prompt, image_path, image_url)
            response_json = call_api(endpoint, headers, body)
            text = extract_response(profile["provider"], response_json)

            if tried:
                print(f"--- 成功 (前 {len(tried)} 个候选失败后) ---", file=sys.stderr)
            else:
                print(f"--- 完成 ---", file=sys.stderr)

            return name, profile, text

        except (RuntimeError, json.JSONDecodeError, Exception) as e:
            last_error = e
            tried.append(name)
            print(f"警告: {name} 失败 ({e})，尝试下一个...", file=sys.stderr)
            continue

    raise RuntimeError(f"所有 {len(tried)} 个候选模型均失败。最后错误: {last_error}。已尝试: {', '.join(tried)}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Model Router - 模型路由引擎")
    subparsers = parser.add_subparsers(dest="command")

    # route 子命令
    route_parser = subparsers.add_parser("route", help="路由到合适的模型并调用")
    route_parser.add_argument("--task", choices=["has_image_input", "complex_reasoning", "quick_task", "general"],
                              help="任务类型（自动选择模型）")
    route_parser.add_argument("--profile", help="直接指定 profile 名称")
    route_parser.add_argument("--prompt", required=True, help="发送给模型的 prompt")
    route_parser.add_argument("--image", help="本地图片路径")
    route_parser.add_argument("--image-url", help="图片 URL")
    route_parser.add_argument("--cost", choices=["cheapest", "best", "balanced"],
                              help="成本模式: cheapest=最便宜, best=最强, balanced=按配置顺序")
    route_parser.add_argument("--auto-task", action="store_true",
                              help="自动从 prompt 内容推断任务类型")

    # list 子命令
    subparsers.add_parser("list", help="列出可用模型")

    # prepare 子命令
    prepare_parser = subparsers.add_parser("prepare", help="创建图片中转目录")
    prepare_parser.add_argument("--root", default=".", help="项目根目录，默认当前目录")
    prepare_parser.add_argument("--json", action="store_true", help="以 JSON 输出目录信息")

    # classify 子命令（调试用）
    classify_parser = subparsers.add_parser("classify", help="查看查询分类结果（调试用）")
    classify_parser.add_argument("--prompt", required=True, help="要分类的查询文本")
    classify_parser.add_argument("--image", help="本地图片路径（存在则自动标记为图片任务）")

    args = parser.parse_args()

    if args.command == "route":
        try:
            name, profile, text = route(
                task_type=args.task,
                profile_name=args.profile,
                prompt=args.prompt,
                image_path=args.image,
                image_url=args.image_url,
                cost_mode=args.cost,
                auto_task=args.auto_task,
            )
            print(text)
        except (FileNotFoundError, KeyError, ValueError, RuntimeError) as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "list":
        config = load_config()
        profiles = config.get("profiles", {})
        for name, p in profiles.items():
            caps = ", ".join(p.get("capabilities", []))
            cost = p.get("cost", {})
            cost_str = ""
            if cost:
                cost_str = f" ${cost.get('input_per_1m', '?')}/{cost.get('output_per_1m', '?')} per 1M"
            print(f"{name}: {p.get('provider')}/{p.get('model')} [{caps}]{cost_str}")

    elif args.command == "prepare":
        paths = prepare_workspace(args.root)
        if args.json:
            print(json.dumps(paths, ensure_ascii=False, indent=2))
        else:
            print("Model Router 工作目录已准备好")
            print(f"项目根目录: {paths['project_root']}")
            print(f"图片目录: {paths['images_dir']}")
            print(f"结果目录: {paths['results_dir']}")
            print("后续截图、验证码、图表和 UI 自动化图片必须先保存到图片目录，再把路径交给 route --image。")

    elif args.command == "classify":
        has_img = bool(args.image)
        task_type, confidence = classify_query(args.prompt, has_img)
        print(f"task_type: {task_type}")
        print(f"confidence: {confidence:.0%}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
