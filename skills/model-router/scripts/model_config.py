#!/usr/bin/env python3
"""Model Router - 交互式模型配置管理器

用法:
    python model_config.py add       # 交互式添加模型
    python model_config.py list      # 列出已配置模型
    python model_config.py test      # 测试模型连接
    python model_config.py remove    # 删除模型
    python model_config.py edit      # 编辑已有模型
"""

import json
import os
import sys
import subprocess
from pathlib import Path

# --- 配置文件路径 ---
SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR.parent / "model-router.yaml"
CONFIG_JSON_PATH = SCRIPT_DIR.parent / "model-router.json"

# --- 预设模板 ---
PROVIDER_TEMPLATES = {
    "openai": {
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "api_key_env": "OPENAI_API_KEY",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-vision-preview"],
        "capabilities": ["text", "image"],
    },
    "google": {
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        "api_key_env": "GOOGLE_API_KEY",
        "models": ["gemini-2.0-flash", "gemini-2.5-pro", "gemini-2.0-flash-lite"],
        "capabilities": ["text", "image"],
    },
    "anthropic": {
        "endpoint": "https://api.anthropic.com/v1/messages",
        "api_key_env": "ANTHROPIC_API_KEY",
        "models": ["claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
        "capabilities": ["text"],
    },
    "ollama": {
        "endpoint": "http://localhost:11434/api/generate",
        "api_key_env": None,
        "models": ["llava", "llava:13b", "bakllava", "llama3", "mistral"],
        "capabilities": ["text", "image"],
    },
    "custom": {
        "endpoint": "",
        "api_key_env": "",
        "models": [],
        "capabilities": ["text"],
    },
}

DEFAULT_ROUTING = [
    {"match": "has_image_input", "prefer": [], "cost_mode": "cheapest"},
    {"match": "complex_reasoning", "prefer": [], "cost_mode": "best"},
    {"match": "quick_task", "prefer": [], "cost_mode": "cheapest"},
]


# --- 简易 YAML 解析器（无需外部依赖）---
def _peek_next_content_line(lines, start_idx):
    """从 start_idx 开始找下一个非空非注释行，返回 (stripped, indent) 或 None。"""
    for idx in range(start_idx, len(lines)):
        s = lines[idx].rstrip()
        if s and not s.lstrip().startswith("#"):
            return s, len(s) - len(s.lstrip())
    return None


def parse_yaml_simple(text):
    """解析简单的 YAML 格式，支持嵌套 dict 和 list（包括 list-of-dict）。"""
    lines = text.split("\n")
    result = {}
    # stack: (container, indent)
    stack = [(result, -1)]
    # 每个 dict 容器 → 它当前正在等待 list 内容的 key
    list_key_map = {}
    # 当前正在构建的 list-of-dict 的 item 及其缩进
    active_list_item = None
    active_list_item_indent = -1

    i = 0
    while i < len(lines):
        stripped = lines[i].rstrip()
        if not stripped or stripped.lstrip().startswith("#"):
            i += 1
            continue

        indent = len(stripped) - len(stripped.lstrip())

        # 如果有活跃的 list item dict，检查当前行是否还属于它
        if active_list_item is not None and indent <= active_list_item_indent:
            active_list_item = None

        # 弹出缩进更深或相等的栈帧
        while len(stack) > 1 and indent <= stack[-1][1]:
            stack.pop()

        parent = stack[-1][0]

        # 获取当前容器对应的 list key（如果有的话）
        current_list_key = list_key_map.get(id(parent))

        # 列表项
        if stripped.lstrip().startswith("- "):
            item_content = stripped.lstrip()[2:].strip()

            # 确定所属的 list 容器
            target_list = None
            if isinstance(parent, list):
                target_list = parent
            elif isinstance(parent, dict) and current_list_key:
                if current_list_key not in parent:
                    parent[current_list_key] = []
                elif not isinstance(parent[current_list_key], list):
                    parent[current_list_key] = []
                target_list = parent[current_list_key]

            if target_list is None:
                i += 1
                continue

            # 检查是否是 "- key: value" 格式（dict list item）
            if ":" in item_content:
                key, _, value = item_content.partition(":")
                key = key.strip()
                value = value.strip()

                new_item = {}
                if value:
                    new_item[key] = _parse_value(value)

                target_list.append(new_item)
                stack.append((new_item, indent))
                active_list_item = new_item
                active_list_item_indent = indent
            else:
                # 简单的 "- value"
                target_list.append(_parse_value(item_content))

            i += 1
            continue

        # 键值对 "key: value"
        if ":" in stripped:
            key, _, value = stripped.lstrip().partition(":")
            key = key.strip()
            value = value.strip()

            if value == "":
                # 空值：前瞻决定初始化为 dict 还是 list
                peek = _peek_next_content_line(lines, i + 1)
                if peek and peek[0].lstrip().startswith("- ") and peek[1] > indent:
                    # 下一行是 list item
                    if isinstance(parent, dict):
                        parent[key] = []
                        list_key_map[id(parent)] = key
                else:
                    # 下一行是 dict 内容
                    if isinstance(parent, dict):
                        parent[key] = {}
                        stack.append((parent[key], indent))
                i += 1
                continue

            # 有值的键值对
            parsed = _parse_value(value)
            if isinstance(parent, dict):
                parent[key] = parsed
            elif isinstance(parent, list) and active_list_item is not None:
                active_list_item[key] = parsed
            i += 1
            continue

        i += 1

    return result


def _parse_value(value):
    """解析单个值。"""
    if value in ("null", "None", "~"):
        return None
    if value in ("true", "True"):
        return True
    if value in ("false", "False"):
        return False
    # 数组 [a, b, c]
    if value.startswith("[") and value.endswith("]"):
        items = value[1:-1].split(",")
        return [item.strip().strip("'\"") for item in items if item.strip()]
    # 数字
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    # 字符串（去引号）
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def yaml_to_str(data, indent=0):
    """将 dict/list 转为 YAML 格式字符串。"""
    lines = []
    prefix = "  " * indent
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.append(yaml_to_str(value, indent + 1))
            elif isinstance(value, list):
                # list 值：纯值用 inline，含 dict 才展开
                if value and any(isinstance(item, dict) for item in value):
                    lines.append(f"{prefix}{key}:")
                    for item in value:
                        if isinstance(item, dict):
                            _render_dict_as_list_item(lines, item, prefix + "  ")
                        else:
                            lines.append(f"{prefix}  - {_format_val(item)}")
                else:
                    lines.append(f"{prefix}{key}: {_format_val(value)}")
            else:
                lines.append(f"{prefix}{key}: {_format_val(value)}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                _render_dict_as_list_item(lines, item, prefix)
            else:
                lines.append(f"{prefix}- {_format_val(item)}")
    return "\n".join(lines)


def _render_dict_as_list_item(lines, item, prefix):
    """将一个 dict 渲染为 YAML list item（- key: value 格式）。"""
    first = True
    for k, v in item.items():
        if isinstance(v, dict):
            if first:
                lines.append(f"{prefix}- {k}:")
                first = False
            else:
                lines.append(f"{prefix}  {k}:")
            lines.append(yaml_to_str(v, len(prefix) // 2 + 2))
        elif isinstance(v, list):
            if v and any(isinstance(x, dict) for x in v):
                if first:
                    lines.append(f"{prefix}- {k}:")
                    first = False
                else:
                    lines.append(f"{prefix}  {k}:")
                for x in v:
                    if isinstance(x, dict):
                        _render_dict_as_list_item(lines, x, prefix + "    ")
                    else:
                        lines.append(f"{prefix}    - {_format_val(x)}")
            else:
                val_str = _format_val(v)
                if first:
                    lines.append(f"{prefix}- {k}: {val_str}")
                    first = False
                else:
                    lines.append(f"{prefix}  {k}: {val_str}")
        else:
            val_str = _format_val(v)
            if first:
                lines.append(f"{prefix}- {k}: {val_str}")
                first = False
            else:
                lines.append(f"{prefix}  {k}: {val_str}")


def _format_val(value):
    """格式化单个值为 YAML 字符串。"""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "[" + ", ".join(str(v) for v in value) + "]"
    if isinstance(value, str) and ("#" in value or ":" in value or "'" in value):
        return f'"{value}"'
    return str(value)


# --- 配置读写 ---
def load_config():
    """加载配置文件。优先 YAML，其次 JSON。"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return parse_yaml_simple(f.read())
    if CONFIG_JSON_PATH.exists():
        with open(CONFIG_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"profiles": {}, "routing": DEFAULT_ROUTING[:]}


def save_config(config):
    """保存配置文件（同时写 YAML 和 JSON）。"""
    # YAML
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write("# Model Router 配置文件\n")
        f.write("# API key 通过环境变量设置，不要写在配置文件中\n\n")
        f.write(yaml_to_str(config))
        f.write("\n")
    # JSON（便于程序读取）
    with open(CONFIG_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"配置已保存到:\n  {CONFIG_PATH}\n  {CONFIG_JSON_PATH}")


# --- 交互式命令 ---
def cmd_add():
    """交互式添加模型。"""
    print("\n=== 添加新模型 ===\n")

    # 选择 provider
    print("可用的 provider 模板:")
    providers = list(PROVIDER_TEMPLATES.keys())
    for i, p in enumerate(providers, 1):
        print(f"  {i}. {p}")
    print()

    while True:
        choice = input("选择 provider (输入编号或名称): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(providers):
            provider = providers[int(choice) - 1]
            break
        if choice in PROVIDER_TEMPLATES:
            provider = choice
            break
        print(f"无效选择，请输入 1-{len(providers)} 或 provider 名称")

    template = PROVIDER_TEMPLATES[provider]
    print(f"\n已选择: {provider}")

    # Profile 名称
    while True:
        name = input("\n给这个模型起个名字 (如 gpt4o, gemini-vision): ").strip()
        if not name:
            print("名称不能为空")
            continue
        if " " in name:
            print("名称不能包含空格，请用连字符 (如 my-model)")
            continue
        break

    # 选择具体模型
    if template["models"]:
        print(f"\n{provider} 可用模型:")
        for i, m in enumerate(template["models"], 1):
            print(f"  {i}. {m}")
        print(f"  {len(template['models']) + 1}. 自定义模型名")

        while True:
            mchoice = input("选择模型 (输入编号): ").strip()
            if mchoice.isdigit():
                idx = int(mchoice)
                if 1 <= idx <= len(template["models"]):
                    model = template["models"][idx - 1]
                    break
                if idx == len(template["models"]) + 1:
                    model = input("输入自定义模型名: ").strip()
                    if model:
                        break
            print("无效选择")
    else:
        model = input("\n输入模型名称: ").strip()
        if not model:
            print("模型名称不能为空")
            return

    # API Key 环境变量
    if template["api_key_env"]:
        default_env = template["api_key_env"]
        env_input = input(f"\nAPI Key 环境变量名 [{default_env}]: ").strip()
        api_key_env = env_input if env_input else default_env

        # 检查环境变量是否已设置
        key_value = os.environ.get(api_key_env)
        if key_value:
            masked = key_value[:4] + "..." + key_value[-4:] if len(key_value) > 8 else "***"
            print(f"  环境变量 {api_key_env} 已设置 ({masked})")
        else:
            print(f"  环境变量 {api_key_env} 未设置")
            set_now = input(f"  现在设置吗？(y/n) [n]: ").strip().lower()
            if set_now == "y":
                key_val = input(f"  输入 {api_key_env} 的值: ").strip()
                if key_val:
                    # 写入 .env 文件
                    env_path = SCRIPT_DIR.parent / ".env"
                    with open(env_path, "a", encoding="utf-8") as f:
                        f.write(f"\n{api_key_env}={key_val}\n")
                    print(f"  已写入 {env_path}")
                    print(f"  请运行: export {api_key_env}={key_val}")
    else:
        api_key_env = None
        print("\n本地模型，无需 API Key")

    # Endpoint
    default_endpoint = template["endpoint"]
    if provider == "custom":
        endpoint = input(f"\nAPI Endpoint URL: ").strip()
        if not endpoint:
            print("Endpoint 不能为空")
            return
    else:
        endpoint_input = input(f"\nAPI Endpoint [{default_endpoint}]: ").strip()
        endpoint = endpoint_input if endpoint_input else default_endpoint

    # 替换 {model} 占位符
    endpoint = endpoint.replace("{model}", model)

    # Capabilities
    default_caps = template["capabilities"]
    print(f"\n模型能力 (当前: {', '.join(default_caps)})")
    print("  可选: text, image, reasoning")
    caps_input = input(f"输入能力标签 [{', '.join(default_caps)}]: ").strip()
    if caps_input:
        capabilities = [c.strip() for c in caps_input.split(",")]
    else:
        capabilities = default_caps

    # Max tokens
    max_tokens_input = input("\nMax tokens [4096]: ").strip()
    max_tokens = int(max_tokens_input) if max_tokens_input.isdigit() else 4096

    # Cost per 1M tokens
    print("\n成本配置（用于成本感知路由，留空跳过）")
    cost_input_input = input("  Input 成本 $/1M tokens []: ").strip()
    cost_output_input = input("  Output 成本 $/1M tokens []: ").strip()
    cost = None
    if cost_input_input or cost_output_input:
        cost = {
            "input_per_1m": float(cost_input_input) if cost_input_input else 0,
            "output_per_1m": float(cost_output_input) if cost_output_input else 0,
        }

    # 构造 profile
    profile = {
        "provider": provider,
        "model": model,
        "api_key_env": api_key_env,
        "capabilities": capabilities,
        "endpoint": endpoint,
        "max_tokens": max_tokens,
    }
    if cost:
        profile["cost"] = cost

    # 确认
    print("\n=== 确认配置 ===")
    for k, v in profile.items():
        print(f"  {k}: {v}")

    confirm = input("\n确认添加？(y/n) [y]: ").strip().lower()
    if confirm == "n":
        print("已取消")
        return

    # 保存
    config = load_config()
    if "profiles" not in config:
        config["profiles"] = {}
    config["profiles"][name] = profile

    # 自动更新 routing
    if "routing" not in config:
        config["routing"] = DEFAULT_ROUTING[:]

    for rule in config["routing"]:
        if "image" in capabilities and rule["match"] == "has_image_input":
            if name not in rule["prefer"]:
                rule["prefer"].append(name)
        if "reasoning" in capabilities and rule["match"] == "complex_reasoning":
            if name not in rule["prefer"]:
                rule["prefer"].append(name)

    save_config(config)
    print(f"\n模型 '{name}' 添加成功！")


def cmd_list():
    """列出已配置模型。"""
    config = load_config()
    profiles = config.get("profiles", {})
    routing = config.get("routing", [])

    if not profiles:
        print("\n尚未配置任何模型。运行 'python model_config.py add' 添加。")
        return

    print("\n=== 已配置模型 ===\n")
    for name, p in profiles.items():
        caps = ", ".join(p.get("capabilities", []))
        key_status = "已设置" if os.environ.get(p.get("api_key_env", "")) else "未设置"
        if p.get("api_key_env") is None:
            key_status = "本地模型"
        cost = p.get("cost", {})
        cost_str = "未设置"
        if cost:
            cost_str = f"${cost.get('input_per_1m', 0)}/{cost.get('output_per_1m', 0)} per 1M tokens"
        print(f"  [{name}]")
        print(f"    provider: {p.get('provider')}")
        print(f"    model: {p.get('model')}")
        print(f"    capabilities: {caps}")
        print(f"    api_key: {p.get('api_key_env')} ({key_status})")
        print(f"    cost: {cost_str}")
        print(f"    endpoint: {p.get('endpoint')}")
        print()

    print("=== 路由规则 ===\n")
    for rule in routing:
        prefer = ", ".join(rule.get("prefer", []))
        print(f"  {rule['match']} → [{prefer}]")


def cmd_test():
    """测试模型连接。"""
    config = load_config()
    profiles = config.get("profiles", {})

    if not profiles:
        print("\n尚未配置任何模型。")
        return

    print("\n=== 测试模型连接 ===\n")
    names = list(profiles.keys())
    for i, name in enumerate(names, 1):
        p = profiles[name]
        caps = ", ".join(p.get("capabilities", []))
        print(f"  {i}. {name} ({p.get('provider')}, {caps})")
    print(f"  {len(names) + 1}. 测试全部")

    choice = input("\n选择要测试的模型 (输入编号): ").strip()

    if choice.isdigit() and int(choice) == len(names) + 1:
        to_test = names
    elif choice.isdigit() and 1 <= int(choice) <= len(names):
        to_test = [names[int(choice) - 1]]
    else:
        print("无效选择")
        return

    for name in to_test:
        p = profiles[name]
        print(f"\n测试 {name} ({p.get('model')})...")

        # 检查 API key
        env_key = p.get("api_key_env")
        if env_key and not os.environ.get(env_key):
            print(f"  SKIP: 环境变量 {env_key} 未设置")
            continue

        # 构造测试请求
        provider = p.get("provider")
        endpoint = p.get("endpoint")
        model = p.get("model")

        try:
            result = _test_api(provider, endpoint, model, env_key)
            if result:
                print(f"  OK: {result[:100]}")
            else:
                print(f"  FAIL: 无响应")
        except Exception as e:
            print(f"  ERROR: {e}")


def _test_api(provider, endpoint, model, env_key):
    """发送测试请求到模型 API。"""
    test_prompt = "Say 'hello' in one word."

    if provider == "openai":
        body = json.dumps({
            "model": model,
            "max_tokens": 10,
            "messages": [{"role": "user", "content": test_prompt}],
        })
        cmd = [
            "curl", "-s", endpoint,
            "-H", f"Authorization: Bearer {os.environ.get(env_key, '')}",
            "-H", "Content-Type: application/json",
            "-d", body,
        ]

    elif provider == "anthropic":
        body = json.dumps({
            "model": model,
            "max_tokens": 10,
            "messages": [{"role": "user", "content": test_prompt}],
        })
        cmd = [
            "curl", "-s", endpoint,
            "-H", f"x-api-key: {os.environ.get(env_key, '')}",
            "-H", "anthropic-version: 2023-06-01",
            "-H", "Content-Type: application/json",
            "-d", body,
        ]

    elif provider == "google":
        api_key = os.environ.get(env_key, "")
        url = f"{endpoint}?key={api_key}"
        body = json.dumps({
            "contents": [{"parts": [{"text": test_prompt}]}],
        })
        cmd = [
            "curl", "-s", url,
            "-H", "Content-Type: application/json",
            "-d", body,
        ]

    elif provider == "ollama":
        body = json.dumps({
            "model": model,
            "prompt": test_prompt,
            "stream": False,
        })
        cmd = [
            "curl", "-s", endpoint,
            "-H", "Content-Type: application/json",
            "-d", body,
        ]

    else:
        # 通用：POST JSON
        body = json.dumps({
            "model": model,
            "prompt": test_prompt,
        })
        api_key = os.environ.get(env_key, "") if env_key else ""
        cmd = [
            "curl", "-s", endpoint,
            "-H", "Content-Type: application/json",
            "-H", f"Authorization: Bearer {api_key}",
            "-d", body,
        ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"curl 失败: {result.stderr}")

    resp = json.loads(result.stdout)

    # 提取响应
    if provider == "openai":
        return resp.get("choices", [{}])[0].get("message", {}).get("content", "")
    elif provider == "anthropic":
        return resp.get("content", [{}])[0].get("text", "")
    elif provider == "google":
        return resp.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    elif provider == "ollama":
        return resp.get("response", "")
    else:
        return json.dumps(resp, ensure_ascii=False)[:200]


def cmd_remove():
    """删除模型。"""
    config = load_config()
    profiles = config.get("profiles", {})

    if not profiles:
        print("\n尚未配置任何模型。")
        return

    print("\n=== 删除模型 ===\n")
    names = list(profiles.keys())
    for i, name in enumerate(names, 1):
        p = profiles[name]
        print(f"  {i}. {name} ({p.get('provider')})")

    choice = input("\n选择要删除的模型 (输入编号): ").strip()

    if not choice.isdigit() or not (1 <= int(choice) <= len(names)):
        print("无效选择")
        return

    name = names[int(choice) - 1]
    confirm = input(f"\n确认删除 '{name}'？(y/n) [n]: ").strip().lower()
    if confirm != "y":
        print("已取消")
        return

    del config["profiles"][name]

    # 从 routing 中移除
    for rule in config.get("routing", []):
        if name in rule.get("prefer", []):
            rule["prefer"].remove(name)

    save_config(config)
    print(f"\n模型 '{name}' 已删除")


def cmd_edit():
    """编辑已有模型。"""
    config = load_config()
    profiles = config.get("profiles", {})

    if not profiles:
        print("\n尚未配置任何模型。")
        return

    print("\n=== 编辑模型 ===\n")
    names = list(profiles.keys())
    for i, name in enumerate(names, 1):
        p = profiles[name]
        print(f"  {i}. {name} ({p.get('provider')})")

    choice = input("\n选择要编辑的模型 (输入编号): ").strip()

    if not choice.isdigit() or not (1 <= int(choice) <= len(names)):
        print("无效选择")
        return

    name = names[int(choice) - 1]
    profile = profiles[name]

    print(f"\n当前配置 ({name}):")
    for k, v in profile.items():
        print(f"  {k}: {v}")

    print("\n输入新值（直接回车保持不变）:")

    fields = [
        ("model", "模型名称"),
        ("endpoint", "API Endpoint"),
        ("api_key_env", "API Key 环境变量名"),
        ("capabilities", "能力标签 (逗号分隔)"),
        ("max_tokens", "Max tokens"),
    ]

    for field, label in fields:
        current = profile.get(field)
        new_val = input(f"  {label} [{current}]: ").strip()
        if new_val:
            if field == "capabilities":
                profile[field] = [c.strip() for c in new_val.split(",")]
            elif field == "max_tokens":
                profile[field] = int(new_val)
            else:
                profile[field] = new_val

    # Cost 编辑
    cost = profile.get("cost", {})
    current_cost = f"${cost.get('input_per_1m', 0)}/{cost.get('output_per_1m', 0)}" if cost else "未设置"
    print(f"\n  当前成本: {current_cost}")
    cost_input_val = input(f"  Input 成本 $/1M tokens (留空保持不变): ").strip()
    cost_output_val = input(f"  Output 成本 $/1M tokens (留空保持不变): ").strip()
    if cost_input_val or cost_output_val:
        profile["cost"] = {
            "input_per_1m": float(cost_input_val) if cost_input_val else cost.get("input_per_1m", 0),
            "output_per_1m": float(cost_output_val) if cost_output_val else cost.get("output_per_1m", 0),
        }

    save_config(config)
    print(f"\n模型 '{name}' 已更新")


# --- 主入口 ---
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()
    commands = {
        "add": cmd_add,
        "list": cmd_list,
        "test": cmd_test,
        "remove": cmd_remove,
        "edit": cmd_edit,
    }

    if cmd in commands:
        commands[cmd]()
    else:
        print(f"未知命令: {cmd}")
        print(f"可用命令: {', '.join(commands.keys())}")


if __name__ == "__main__":
    main()
