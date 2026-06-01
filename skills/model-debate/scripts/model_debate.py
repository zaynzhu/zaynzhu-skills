#!/usr/bin/env python3
"""Model Debate - 多模型辩论引擎

将同一个问题丢给多个模型，收集回答，可选多轮辩论，最终合成共识。

用法:
    # 单轮辩论（默认）
    python model_debate.py debate --prompt "这段代码有没有安全漏洞？"

    # 多轮辩论
    python model_debate.py debate --prompt "这段代码有没有安全漏洞？" --mode multi

    # 指定参与模型
    python model_debate.py debate --prompt "..." --models gpt4o,claude-sonnet

    # 列出已配置模型
    python model_debate.py list

    # 生成默认配置
    python model_debate.py init
"""

import argparse
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR.parent / "model-debate.yaml"
CONFIG_JSON_PATH = SCRIPT_DIR.parent / "model-debate.json"
STATE_PATH = SCRIPT_DIR.parent / ".state.json"

# 可重试的 HTTP 状态码
RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}


# ---------------------------------------------------------------------------
# 状态记忆（上次使用的模型）
# ---------------------------------------------------------------------------

def save_last_models(model_names, mode):
    """保存上次使用的模型和模式。"""
    state = {}
    if STATE_PATH.exists():
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            pass
    state["last_models"] = model_names
    state["last_mode"] = mode
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def load_last_models():
    """读取上次使用的模型列表。"""
    if STATE_PATH.exists():
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                state = json.load(f)
            return state.get("last_models"), state.get("last_mode")
        except Exception:
            pass
    return None, None


# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

def load_config():
    """加载配置文件。"""
    if CONFIG_JSON_PATH.exists():
        with open(CONFIG_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    if CONFIG_PATH.exists():
        sys.path.insert(0, str(SCRIPT_DIR))
        try:
            from model_config_debate import parse_yaml_simple
        except ImportError:
            # 回退：用 model-router 的解析器（如果存在）
            router_scripts = Path(__file__).parent.parent.parent / "model-router" / "scripts"
            if router_scripts.exists():
                sys.path.insert(0, str(router_scripts))
                from model_config import parse_yaml_simple
            else:
                print("错误: 无法加载 YAML 解析器。请先运行 'python model_debate.py init' 生成 JSON 配置。")
                sys.exit(1)
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return parse_yaml_simple(f.read())
    print("错误: 配置文件不存在。请先运行 'python model_debate.py init' 生成配置。")
    sys.exit(1)


def init_config():
    """生成默认配置文件（YAML + JSON）。"""
    config = {
        "models": {
            "gpt4o": {
                "provider": "openai",
                "model": "gpt-4o",
                "api_key_env": "OPENAI_API_KEY",
                "endpoint": "https://api.openai.com/v1/chat/completions",
                "max_tokens": 4096,
            },
            "claude-sonnet": {
                "provider": "anthropic",
                "model": "claude-sonnet-4-6",
                "api_key_env": "ANTHROPIC_API_KEY",
                "endpoint": "https://api.anthropic.com/v1/messages",
                "max_tokens": 4096,
            },
            "gemini-flash": {
                "provider": "google",
                "model": "gemini-2.0-flash",
                "api_key_env": "GOOGLE_API_KEY",
                "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                "max_tokens": 4096,
            },
        },
        "debate": {
            "participants": ["gpt4o", "claude-sonnet", "gemini-flash"],
            "default_mode": "single",
            "max_rounds": 3,
            "convergence_ratio": 0.8,
        },
    }

    # 写 JSON
    with open(CONFIG_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    # 写 YAML（简单手写，不依赖序列化器）
    yaml_content = """# Model Debate 配置文件
# 在 models 中定义参与辩论的模型
# API key 通过环境变量设置，不要写在配置文件中

models:
  gpt4o:
    provider: openai
    model: gpt-4o
    api_key_env: OPENAI_API_KEY
    endpoint: https://api.openai.com/v1/chat/completions
    max_tokens: 4096

  claude-sonnet:
    provider: anthropic
    model: claude-sonnet-4-6
    api_key_env: ANTHROPIC_API_KEY
    endpoint: https://api.anthropic.com/v1/messages
    max_tokens: 4096

  gemini-flash:
    provider: google
    model: gemini-2.0-flash
    api_key_env: GOOGLE_API_KEY
    endpoint: https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent

debate:
  participants: [gpt4o, claude-sonnet, gemini-flash]
  default_mode: single
  max_rounds: 3
  convergence_ratio: 0.8
"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    print(f"配置已生成:\n  {CONFIG_PATH}\n  {CONFIG_JSON_PATH}")
    print("\n编辑 model-debate.yaml 添加你自己的模型，然后运行:")
    print("  python model_debate.py debate --prompt '你的问题'")


# ---------------------------------------------------------------------------
# API 调用（复用 model-router 的模式）
# ---------------------------------------------------------------------------

def build_request(model_cfg, messages):
    """构造 API 请求。messages 是完整的对话消息列表。"""
    provider = model_cfg["provider"]
    model = model_cfg["model"]
    endpoint = model_cfg["endpoint"]
    max_tokens = model_cfg.get("max_tokens", 4096)

    if provider == "openai":
        body = json.dumps({
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        })
        env_key = model_cfg.get("api_key_env", "")
        headers = {
            "Authorization": f"Bearer {os.environ.get(env_key, '')}",
            "Content-Type": "application/json",
        }

    elif provider == "anthropic":
        body = json.dumps({
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        })
        env_key = model_cfg.get("api_key_env", "")
        headers = {
            "x-api-key": os.environ.get(env_key, ""),
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    elif provider == "google":
        # Google 用 contents 格式
        endpoint = endpoint.replace("{model}", model)
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        body = json.dumps({"contents": contents})
        env_key = model_cfg.get("api_key_env", "")
        api_key = os.environ.get(env_key, "")
        endpoint = f"{endpoint}?key={api_key}"
        headers = {"Content-Type": "application/json"}

    elif provider == "ollama":
        body = json.dumps({
            "model": model,
            "prompt": messages[-1]["content"],
            "stream": False,
        })
        headers = {"Content-Type": "application/json"}

    else:
        body = json.dumps({
            "model": model,
            "messages": messages,
        })
        env_key = model_cfg.get("api_key_env", "")
        api_key = os.environ.get(env_key, "") if env_key else ""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    return endpoint, headers, body


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


def call_api(endpoint, headers, body, timeout=120):
    """用 curl 调用 API。"""
    cmd = ["curl", "-s", "--max-time", str(timeout), "-w", "\n%{http_code}"]
    for k, v in headers.items():
        cmd.extend(["-H", f"{k}: {v}"])
    cmd.extend(["-d", body, endpoint])

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout + 10)
    if result.returncode != 0:
        raise RuntimeError(f"curl 失败: {result.stderr}")

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
        raise RuntimeError(f"HTTP {status_code}: {resp_body[:200]}")

    return json.loads(resp_body)


def query_model(model_name, model_cfg, messages):
    """查询单个模型，返回回答文本。"""
    provider = model_cfg["provider"]
    endpoint, headers, body = build_request(model_cfg, messages)
    response_json = call_api(endpoint, headers, body)
    return extract_response(provider, response_json)


# ---------------------------------------------------------------------------
# 辩论逻辑
# ---------------------------------------------------------------------------

# 单轮辩论的 prompt 模板
SINGLE_DEBATE_PROMPT = """你被要求独立回答以下问题。请给出你最准确、最全面的回答。

问题：{question}

请直接回答，不要提及这是辩论或引用其他模型。"""

# 多轮辩论：看到其他模型回答后的修正 prompt
MULTI_ROUND_PROMPT = """你正在参与一场多模型辩论。以下是其他模型对同一个问题的回答：

{other_answers}

请重新审视你的原始回答：

原始回答：{my_answer}

原始问题：{question}

请根据其他模型的观点，修正或坚持你的回答。如果你被说服了，说明为什么改变了观点。如果你坚持原观点，说明为什么其他模型的观点不够有说服力。给出你修正后的最终回答。"""

# 共识合成 prompt
SYNTHESIS_PROMPT = """你是一个公正的裁判。以下是对同一个问题，{n}个不同模型的回答：

{all_answers}

请分析这些回答，给出一个综合的最终结论。要求：
1. 提取所有模型的共识点（大家都同意的部分）
2. 标注分歧点（模型之间有不同意见的部分）
3. 对于分歧，给出你认为最合理的判断和理由
4. 最终结论应该比任何单个模型的回答都更全面、更准确

请用以下格式输出：

## 共识结论
（综合所有观点后的最终答案）

## 各模型观点摘要
（每个模型的核心论点，2-3 句话）

## 分歧分析
（模型之间的分歧点及你的判断）"""


def run_single_debate(config, prompt, model_names):
    """单轮辩论：并行问所有模型，合成共识。"""
    models = config["models"]
    debate_cfg = config.get("debate", {})

    # 确定参与模型
    if not model_names:
        model_names = debate_cfg.get("participants", list(models.keys()))

    # 验证模型存在
    for name in model_names:
        if name not in models:
            print(f"错误: 模型 '{name}' 未在配置中找到")
            sys.exit(1)

    print(f"=== 单轮辩论 ===", file=sys.stderr)
    print(f"参与模型: {', '.join(model_names)}", file=sys.stderr)
    print(f"问题: {prompt[:80]}...", file=sys.stderr)
    print(file=sys.stderr)

    # 并行收集各模型回答
    answers = {}
    with ThreadPoolExecutor(max_workers=len(model_names)) as executor:
        future_to_name = {}
        for name in model_names:
            model_cfg = models[name]
            messages = [{"role": "user", "content": SINGLE_DEBATE_PROMPT.format(question=prompt)}]
            future = executor.submit(query_model, name, model_cfg, messages)
            future_to_name[future] = name
            print(f"[{name}] 回答中...", file=sys.stderr)

        for future in future_to_name:
            name = future_to_name[future]
            try:
                answer = future.result()
                answers[name] = answer
                print(f"[{name}] 完成 ({len(answer)} 字符)", file=sys.stderr)
            except Exception as e:
                print(f"[{name}] 失败: {e}", file=sys.stderr)
                answers[name] = f"[调用失败: {e}]"

    # 合成共识
    print(f"\n[共识合成] 分析中...", file=sys.stderr)
    all_answers_text = "\n\n".join(
        f"### {name}\n{answer}" for name, answer in answers.items()
    )
    synthesis_messages = [{"role": "user", "content": SYNTHESIS_PROMPT.format(
        n=len(answers),
        all_answers=all_answers_text,
    )}]

    # 用第一个成功的模型做合成
    synthesis_model = None
    for name in model_names:
        if answers.get(name) and not answers[name].startswith("[调用失败"):
            synthesis_model = name
            break

    if synthesis_model:
        try:
            consensus = query_model(synthesis_model, models[synthesis_model], synthesis_messages)
            print(f"[共识合成] 完成", file=sys.stderr)
        except Exception as e:
            consensus = f"共识合成失败: {e}"
            print(f"[共识合成] 失败: {e}", file=sys.stderr)
    else:
        consensus = "所有模型均调用失败，无法合成共识。"

    return answers, consensus


def run_multi_debate(config, prompt, model_names):
    """多轮辩论：每轮模型看到其他人的回答后修正。"""
    models = config["models"]
    debate_cfg = config.get("debate", {})
    max_rounds = debate_cfg.get("max_rounds", 3)
    convergence_ratio = debate_cfg.get("convergence_ratio", 0.8)

    if not model_names:
        model_names = debate_cfg.get("participants", list(models.keys()))

    for name in model_names:
        if name not in models:
            print(f"错误: 模型 '{name}' 未在配置中找到")
            sys.exit(1)

    print(f"=== 多轮辩论（最多 {max_rounds} 轮）===", file=sys.stderr)
    print(f"参与模型: {', '.join(model_names)}", file=sys.stderr)
    print(f"问题: {prompt[:80]}...", file=sys.stderr)
    print(file=sys.stderr)

    # 第 1 轮：独立回答
    print(f"--- 第 1 轮：独立回答 ---", file=sys.stderr)
    answers = {}
    for name in model_names:
        model_cfg = models[name]
        messages = [{"role": "user", "content": SINGLE_DEBATE_PROMPT.format(question=prompt)}]
        print(f"[{name}] 回答中...", file=sys.stderr)
        try:
            answer = query_model(name, model_cfg, messages)
            answers[name] = answer
            print(f"[{name}] 完成", file=sys.stderr)
        except Exception as e:
            print(f"[{name}] 失败: {e}", file=sys.stderr)
            answers[name] = f"[调用失败: {e}]"

    all_rounds = [dict(answers)]

    # 后续轮次：互相批评修正
    for round_num in range(2, max_rounds + 1):
        print(f"\n--- 第 {round_num} 轮：互相审视 ---", file=sys.stderr)
        new_answers = {}

        for name in model_names:
            if answers.get(name, "").startswith("[调用失败"):
                new_answers[name] = answers[name]
                continue

            # 构造其他模型的回答
            other_text = "\n\n".join(
                f"### {other_name}\n{other_answer}"
                for other_name, other_answer in answers.items()
                if other_name != name and not other_answer.startswith("[调用失败")
            )

            if not other_text:
                new_answers[name] = answers[name]
                continue

            messages = [{"role": "user", "content": MULTI_ROUND_PROMPT.format(
                other_answers=other_text,
                my_answer=answers[name],
                question=prompt,
            )}]

            print(f"[{name}] 修正中...", file=sys.stderr)
            try:
                revised = query_model(name, models[name], messages)
                new_answers[name] = revised
                print(f"[{name}] 完成", file=sys.stderr)
            except Exception as e:
                print(f"[{name}] 失败，保留原回答: {e}", file=sys.stderr)
                new_answers[name] = answers[name]

        # 收敛检测：如果大多数模型回答未变化，提前结束
        changed = sum(1 for name in model_names if new_answers.get(name) != answers.get(name))
        unchanged_ratio = 1 - changed / max(len(model_names), 1)
        answers = new_answers
        all_rounds.append(dict(answers))

        if unchanged_ratio >= convergence_ratio:
            print(f"\n--- 第 {round_num} 轮后收敛（{unchanged_ratio:.0%} 未变化），提前结束 ---", file=sys.stderr)
            break

    # 合成共识
    print(f"\n[共识合成] 分析中...", file=sys.stderr)
    all_answers_text = "\n\n".join(
        f"### {name}\n{answer}" for name, answer in answers.items()
    )
    synthesis_messages = [{"role": "user", "content": SYNTHESIS_PROMPT.format(
        n=len(answers),
        all_answers=all_answers_text,
    )}]

    synthesis_model = None
    for name in model_names:
        if answers.get(name) and not answers[name].startswith("[调用失败"):
            synthesis_model = name
            break

    if synthesis_model:
        try:
            consensus = query_model(synthesis_model, models[synthesis_model], synthesis_messages)
            print(f"[共识合成] 完成", file=sys.stderr)
        except Exception as e:
            consensus = f"共识合成失败: {e}"
    else:
        consensus = "所有模型均调用失败，无法合成共识。"

    return all_rounds, consensus


# ---------------------------------------------------------------------------
# 输出格式化
# ---------------------------------------------------------------------------

def format_single_output(answers, consensus):
    """格式化单轮辩论输出。"""
    lines = [consensus, "", "---", "", "## 各模型原始回答", ""]
    for name, answer in answers.items():
        lines.append(f"### {name}")
        lines.append(answer)
        lines.append("")
    return "\n".join(lines)


def format_multi_output(all_rounds, consensus):
    """格式化多轮辩论输出。"""
    lines = [consensus, "", "---", ""]

    for i, round_answers in enumerate(all_rounds):
        round_label = f"第 {i + 1} 轮" if i > 0 else "第 1 轮（独立回答）"
        lines.append(f"## {round_label}")
        lines.append("")
        for name, answer in round_answers.items():
            lines.append(f"### {name}")
            lines.append(answer)
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 配置保存
# ---------------------------------------------------------------------------

def save_config(config):
    """保存配置（同时写 JSON 和 YAML）。"""
    with open(CONFIG_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    # 手写 YAML（简单可靠）
    lines = ["# Model Debate 配置文件", ""]
    lines.append("models:")
    for name, m in config.get("models", {}).items():
        lines.append(f"  {name}:")
        for k, v in m.items():
            if v is None:
                lines.append(f"    {k}: null")
            elif isinstance(v, int):
                lines.append(f"    {k}: {v}")
            else:
                lines.append(f"    {k}: {v}")
        lines.append("")

    debate = config.get("debate", {})
    lines.append("debate:")
    lines.append(f"  participants: [{', '.join(debate.get('participants', []))}]")
    lines.append(f"  default_mode: {debate.get('default_mode', 'single')}")
    lines.append(f"  max_rounds: {debate.get('max_rounds', 3)}")
    lines.append(f"  convergence_ratio: {debate.get('convergence_ratio', 0.8)}")
    lines.append("")

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# 协议模板（API 格式 + 默认 endpoint）
PROTOCOL_TEMPLATES = {
    "openai": {
        "label": "OpenAI 协议（兼容大多数第三方：DeepSeek、Kimi、Groq、vLLM 等）",
        "default_endpoint": "https://api.openai.com/v1/chat/completions",
        "default_key_env": "OPENAI_API_KEY",
    },
    "anthropic": {
        "label": "Anthropic 协议（Claude 系列）",
        "default_endpoint": "https://api.anthropic.com/v1/messages",
        "default_key_env": "ANTHROPIC_API_KEY",
    },
    "google": {
        "label": "Google 协议（Gemini 系列）",
        "default_endpoint": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        "default_key_env": "GOOGLE_API_KEY",
    },
    "ollama": {
        "label": "Ollama 协议（本地模型）",
        "default_endpoint": "http://localhost:11434/api/generate",
        "default_key_env": None,
    },
}

# 常用服务预设（方便快速选择）
SERVICE_PRESETS = {
    "openai":    {"protocol": "openai",    "endpoint": "https://api.openai.com/v1/chat/completions",       "key_env": "OPENAI_API_KEY"},
    "anthropic": {"protocol": "anthropic", "endpoint": "https://api.anthropic.com/v1/messages",            "key_env": "ANTHROPIC_API_KEY"},
    "google":    {"protocol": "google",    "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", "key_env": "GOOGLE_API_KEY"},
    "deepseek":  {"protocol": "openai",    "endpoint": "https://api.deepseek.com/v1/chat/completions",    "key_env": "DEEPSEEK_API_KEY"},
    "kimi":      {"protocol": "openai",    "endpoint": "https://api.moonshot.cn/v1/chat/completions",     "key_env": "KIMI_API_KEY"},
    "groq":      {"protocol": "openai",    "endpoint": "https://api.groq.com/openai/v1/chat/completions", "key_env": "GROQ_API_KEY"},
    "ollama":    {"protocol": "ollama",    "endpoint": "http://localhost:11434/api/generate",              "key_env": None},
    "custom":    {"protocol": "openai",    "endpoint": "",                                                  "key_env": ""},
}


# ---------------------------------------------------------------------------
# CLI 命令
# ---------------------------------------------------------------------------

def cmd_add():
    """交互式添加模型（1问1答）。"""
    config = load_config()
    models = config.setdefault("models", {})

    print("\n=== 添加模型 ===\n")

    # 1. 选服务（预设 or 自定义）
    services = list(SERVICE_PRESETS.keys())
    for i, s in enumerate(services, 1):
        preset = SERVICE_PRESETS[s]
        extra = f" ({preset['endpoint'][:40]}...)" if s not in ("custom",) and preset["endpoint"] else ""
        print(f"  {i}. {s}{extra}")
    choice = input("\n选择服务 (编号或名称): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(services):
        service = services[int(choice) - 1]
    elif choice in SERVICE_PRESETS:
        service = choice
    else:
        print("无效选择")
        return

    preset = SERVICE_PRESETS[service]

    # 2. 协议（自动根据服务选择，可覆盖）
    default_protocol = preset["protocol"]
    protocols = list(PROTOCOL_TEMPLATES.keys())
    print(f"\nAPI 协议:")
    for i, p in enumerate(protocols, 1):
        label = PROTOCOL_TEMPLATES[p]["label"]
        marker = " (推荐)" if p == default_protocol else ""
        print(f"  {i}. {p} — {label}{marker}")
    proto_input = input(f"\n选择协议 [{default_protocol}]: ").strip()
    if proto_input.isdigit() and 1 <= int(proto_input) <= len(protocols):
        protocol = protocols[int(proto_input) - 1]
    elif proto_input in PROTOCOL_TEMPLATES:
        protocol = proto_input
    elif not proto_input:
        protocol = default_protocol
    else:
        print("无效选择")
        return

    # 3. Endpoint URL
    default_endpoint = preset["endpoint"]
    if not default_endpoint:
        endpoint = input("\nAPI Endpoint URL: ").strip()
    else:
        endpoint_input = input(f"\nEndpoint URL [{default_endpoint}]: ").strip()
        endpoint = endpoint_input if endpoint_input else default_endpoint

    # 4. 模型名
    model = input("\n模型名称 (如 gpt-4o, kimi-k2.6:cloud): ").strip()
    if not model:
        print("模型名不能为空")
        return

    endpoint = endpoint.replace("{model}", model)

    # 5. Profile 名称
    default_name = model.replace("/", "-").replace(":", "-")
    name = input(f"\n起个名字 [{default_name}]: ").strip()
    if not name:
        name = default_name

    # 6. API Key
    default_env = preset.get("key_env") or ""
    if protocol == "ollama" and not default_env:
        api_key_env = None
        print("\n本地 Ollama 模型，无需 API Key")
    else:
        env_input = input(f"\nAPI Key 环境变量名 [{default_env}]: ").strip()
        api_key_env = env_input if env_input else default_env
        if api_key_env:
            key_value = os.environ.get(api_key_env)
            if key_value:
                masked = key_value[:4] + "..." + key_value[-4:] if len(key_value) > 8 else "***"
                print(f"  已设置 ({masked})")
            else:
                print(f"  未设置。请先运行: export {api_key_env}=你的key")

    # 7. 保存
    profile = {
        "provider": protocol,
        "model": model,
        "api_key_env": api_key_env,
        "endpoint": endpoint,
        "max_tokens": 4096,
    }

    config["models"][name] = profile

    # 自动加入辩论参与者
    participants = config.setdefault("debate", {}).setdefault("participants", [])
    if name not in participants:
        participants.append(name)
        print(f"\n已自动加入辩论参与者列表")

    save_config(config)
    print(f"\n模型 '{name}' 添加成功！")
    print(f"  协议: {protocol}")
    print(f"  模型: {model}")
    print(f"  Endpoint: {endpoint}")
    print(f"\n运行 debate 时可用 --models {name} 指定使用它")


def cmd_remove():
    """删除模型。"""
    config = load_config()
    models = config.get("models", {})

    if not models:
        print("没有可删除的模型。")
        return

    print("\n=== 删除模型 ===\n")
    names = list(models.keys())
    for i, name in enumerate(names, 1):
        m = models[name]
        print(f"  {i}. {name} ({m.get('provider')}/{m.get('model')})")

    choice = input("\n选择要删除的模型 (编号): ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(names)):
        print("无效选择")
        return

    name = names[int(choice) - 1]
    confirm = input(f"\n确认删除 '{name}'？(y/n) [n]: ").strip().lower()
    if confirm != "y":
        print("已取消")
        return

    del config["models"][name]

    # 从参与者列表移除
    participants = config.get("debate", {}).get("participants", [])
    if name in participants:
        participants.remove(name)

    save_config(config)
    print(f"\n模型 '{name}' 已删除")


def cmd_list():
    """列出已配置模型。"""
    config = load_config()
    models = config.get("models", {})
    debate = config.get("debate", {})
    participants = debate.get("participants", [])

    if not models:
        print("尚未配置任何模型。运行 'python model_debate.py init' 生成配置。")
        return

    print("\n=== 已配置模型 ===\n")
    for name, m in models.items():
        role = " (辩论参与者)" if name in participants else ""
        key_env = m.get("api_key_env", "")
        key_status = "已设置" if os.environ.get(key_env) else "未设置"
        if key_env is None:
            key_status = "本地模型"
        print(f"  [{name}]{role}")
        print(f"    provider: {m.get('provider')}")
        print(f"    model: {m.get('model')}")
        print(f"    api_key: {key_env} ({key_status})")
        print()

    print("=== 辩论设置 ===\n")
    print(f"  参与者: {', '.join(participants)}")
    print(f"  默认模式: {debate.get('default_mode', 'single')}")
    print(f"  最大轮数: {debate.get('max_rounds', 3)}")


def cmd_debate(prompt, mode=None, model_names=None):
    """运行辩论。"""
    config = load_config()
    debate_cfg = config.get("debate", {})

    # 没指定模型时，用上次的
    if not model_names:
        last_models, last_mode = load_last_models()
        if last_models:
            model_names = last_models
            print(f"[记忆] 使用上次的模型: {', '.join(model_names)}", file=sys.stderr)
        if not mode and last_mode:
            mode = last_mode

    if not mode:
        mode = debate_cfg.get("default_mode", "single")

    if mode == "single":
        answers, consensus = run_single_debate(config, prompt, model_names)
        print(format_single_output(answers, consensus))
    elif mode == "multi":
        all_rounds, consensus = run_multi_debate(config, prompt, model_names)
        print(format_multi_output(all_rounds, consensus))
    else:
        print(f"错误: 未知模式 '{mode}'，支持 single 和 multi")
        sys.exit(1)

    # 记住本次使用的模型
    actual_models = list(answers.keys()) if mode == "single" else list(all_rounds[-1].keys()) if all_rounds else []
    if actual_models:
        save_last_models(actual_models, mode)


def main():
    parser = argparse.ArgumentParser(description="Model Debate - 多模型辩论引擎")
    subparsers = parser.add_subparsers(dest="command")

    # debate 子命令
    debate_parser = subparsers.add_parser("debate", help="运行辩论")
    debate_parser.add_argument("--prompt", required=True, help="要辩论的问题")
    debate_parser.add_argument("--mode", choices=["single", "multi"], help="辩论模式: single(一轮) 或 multi(多轮)")
    debate_parser.add_argument("--models", help="参与模型（逗号分隔，如 gpt4o,claude-sonnet）")

    # list 子命令
    subparsers.add_parser("list", help="列出已配置模型")

    # add 子命令
    subparsers.add_parser("add", help="交互式添加模型")

    # remove 子命令
    subparsers.add_parser("remove", help="删除模型")

    # init 子命令
    subparsers.add_parser("init", help="生成默认配置文件")

    args = parser.parse_args()

    if args.command == "debate":
        model_names = [m.strip() for m in args.models.split(",")] if args.models else None
        cmd_debate(args.prompt, args.mode, model_names)

    elif args.command == "list":
        cmd_list()

    elif args.command == "add":
        cmd_add()

    elif args.command == "remove":
        cmd_remove()

    elif args.command == "init":
        init_config()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
