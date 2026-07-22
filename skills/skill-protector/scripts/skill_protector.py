#!/usr/bin/env python3
"""skill-protector —— 给目标 skill 套上"加密 + license 门禁"的加密器。

三个子命令：
  init    生成 Ed25519 密钥对到本机密钥目录
  encrypt 加密目标 skill，产出可分发的加密 skill 目录
  license 用私钥签发一份 license 字符串

密钥目录默认 ~/.skill-protect/，可用环境变量 SKILL_PROTECT_HOME 或 --home 覆盖
（测试时用它指向临时目录，避免污染真实签名密钥）。
"""

import argparse
import base64
import json
import os
import sys
import uuid

sys.stdout.reconfigure(encoding="utf-8")

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    sys.stderr.write(
        "skill-protector 依赖 cryptography 库，请先安装: pip install cryptography\n"
    )
    sys.exit(2)


# ---------------------------------------------------------------------------
# 路径与密钥
# ---------------------------------------------------------------------------

def key_home(args) -> str:
    """返回密钥根目录，优先 --home / 环境变量，最后默认 ~/.skill-protect/。"""
    home = getattr(args, "home", None) or os.environ.get("SKILL_PROTECT_HOME")
    if home:
        return os.path.expanduser(home)
    return os.path.join(os.path.expanduser("~"), ".skill-protect")


def private_key_path(args) -> str:
    return os.path.join(key_home(args), "private_key.pem")


def public_key_path(args) -> str:
    return os.path.join(key_home(args), "public_key.pem")


def ledger_path(args) -> str:
    return os.path.join(key_home(args), "issued.json")


def load_private_key(args):
    path = private_key_path(args)
    if not os.path.exists(path):
        sys.stderr.write(
            f"未找到私钥: {path}\n请先运行: skill-protector.py init\n"
        )
        sys.exit(1)
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def load_public_key_bytes(args) -> bytes:
    """返回公钥的原始 32 字节，用于内嵌进 load.py。"""
    path = public_key_path(args)
    if not os.path.exists(path):
        sys.stderr.write(
            f"未找到公钥: {path}\n请先运行: skill-protector.py init\n"
        )
        sys.exit(1)
    with open(path, "rb") as f:
        pub = serialization.load_pem_public_key(f.read())
    return pub.public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )


# ---------------------------------------------------------------------------
# 通用工具
# ---------------------------------------------------------------------------

def b64u(data: bytes) -> str:
    """base64url 无填充编码。"""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64u_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def split_frontmatter(text: str):
    """把 SKILL.md 拆成 (frontmatter块, 正文)。frontmatter 块含首尾 --- 行。"""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            # 包含到第二个 --- 行结束
            close = text.find("\n", end + 1) + 1
            return text[:close], text[close:]
    return "", text


# ---------------------------------------------------------------------------
# init：生成 Ed25519 密钥对
# ---------------------------------------------------------------------------

def cmd_init(args):
    home = key_home(args)
    os.makedirs(home, exist_ok=True)
    priv_path = private_key_path(args)
    pub_path = public_key_path(args)

    if os.path.exists(priv_path) and not args.force:
        sys.stderr.write(
            f"私钥已存在: {priv_path}\n如需重新生成请加 --force（旧 license 将全部失效）。\n"
        )
        sys.exit(1)

    priv = ed25519.Ed25519PrivateKey.generate()
    pub = priv.public_key()

    priv_pem = priv.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    pub_pem = pub.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # 尽量收紧权限（Windows 上 chmod 作用有限，但不报错）
    with open(priv_path, "wb") as f:
        f.write(priv_pem)
    try:
        os.chmod(priv_path, 0o600)
    except OSError:
        pass
    with open(pub_path, "wb") as f:
        f.write(pub_pem)

    print(f"已生成密钥对：")
    print(f"  私钥（妥善保管，切勿外泄）: {priv_path}")
    print(f"  公钥                       : {pub_path}")
    print(f"下一步：encrypt 加密目标 skill；license 签发授权码。")


# ---------------------------------------------------------------------------
# encrypt：加密目标 skill
# ---------------------------------------------------------------------------

# load.py 模板。占位符用 <<NAME>> 风格避免与模板自身代码冲突。
LOAD_PY_TEMPLATE = '''#!/usr/bin/env python3
"""加密 skill 解密加载器（由 skill-protector 自动生成）。

用法：
  python scripts/load.py                    # 解密并输出真实 SKILL.md 指令
  python scripts/load.py --ref <name>       # 解密并输出某个 references 文件
  python scripts/load.py --license <code>   # 首次激活：校验并保存 license
"""
import base64
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    sys.stdout.write("本 skill 需要 cryptography 库，请运行: pip install cryptography\\n")
    sys.exit(2)

# ---- 内嵌参数（base64 存储，轻量混淆）----
_PUB = "<<PUBKEY>>"        # Ed25519 公钥
_K = "<<AES_KEY>>"          # AES-256 密钥
_N = "<<NONCE>>"            # AES-GCM nonce
_C = "<<CIPHERTEXT>>"       # 加密后的 payload
_SKILL_ID = "<<SKILL_ID>>"

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LICENSE_FILE = os.path.join(_ROOT, ".license")
_MARKER = "# === DECRYPTED SKILL INSTRUCTIONS BELOW ==="


def _b64d(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _decrypt_payload():
    aes = AESGCM(_b64d(_K))
    data = aes.decrypt(_b64d(_N), _b64d(_C), None)
    return json.loads(data.decode("utf-8"))


def _verify_license(code):
    try:
        head, sig = code.split(".", 1)
        payload = json.loads(_b64d(head).decode("utf-8"))
        if payload.get("skill_id") != _SKILL_ID:
            return False
        pub = ed25519.Ed25519PublicKey.from_public_bytes(_b64d(_PUB))
        # 验签对象必须与签发时一致：head 的 ascii 字节
        pub.verify(_b64d(sig), head.encode("ascii"))
        return True
    except Exception:
        return False


def _get_license(arg):
    if arg:
        return arg
    if os.path.exists(_LICENSE_FILE):
        with open(_LICENSE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def _prompt_no_license():
    sys.stdout.write(
        "未检测到 license。请向作者索取 license，然后以 --license 参数重跑：\\n"
        "    python scripts/load.py --license <你的license>\\n"
        "license 校验通过后会自动保存到 .license，下次无需再填。\\n"
    )
    sys.exit(1)


def _prompt_bad_license():
    sys.stdout.write(
        "license 无效（签名校验失败或与当前 skill 不匹配）。请向作者确认后重跑：\\n"
        "    python scripts/load.py --license <你的license>\\n"
    )
    sys.exit(1)


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--ref", help="要解密的 references 文件名或相对路径")
    p.add_argument("--license", help="首次激活时填入的 license")
    a = p.parse_args()

    code = _get_license(a.license)
    if not code:
        _prompt_no_license()
    if not _verify_license(code):
        _prompt_bad_license()
    if a.license:  # 校验通过才落盘
        with open(_LICENSE_FILE, "w", encoding="utf-8") as f:
            f.write(a.license.strip() + "\\n")

    files = _decrypt_payload()

    if a.ref:
        # 灵活匹配：精确键 / references+arg / 以 arg 结尾
        candidates = [
            a.ref,
            "references/" + a.ref.lstrip("/"),
            "references/" + a.ref.replace("\\\\", "/"),
        ]
        key = None
        for c in candidates:
            if c in files:
                key = c
                break
        if key is None:
            for k in files:
                if k.endswith("/" + a.ref) or k.endswith(a.ref):
                    key = k
                    break
        if key is None:
            sys.stderr.write(f"未找到 references: {a.ref}\\n")
            sys.exit(3)
        sys.stdout.write(files[key])
        return

    sys.stdout.write(_MARKER + "\\n")
    sys.stdout.write(files.get("SKILL.md", ""))


if __name__ == "__main__":
    main()
'''


# loader SKILL.md 正文模板。frontmatter 由目标 skill 原样继承，拼在本正文之前。
# 注意：本模板不以 --- 开头，frontmatter 由外部提供，避免出现两个 frontmatter 块。
LOADER_BODY_TEMPLATE = '''# 加密 Skill 加载器

本 skill 的真实指令已加密，需运行解密脚本获取。请严格按以下步骤执行。

## 执行步骤

1. 在本 skill 目录下运行 `python scripts/load.py`。
2. 若脚本成功输出内容：其 stdout 即为本 skill 的**真实指令正文**，请严格照其执行，等同于这是 SKILL.md 的正文。输出开头会有一行标记 `# === DECRYPTED SKILL INSTRUCTIONS BELOW ===`，标记以下即为真实指令。
3. 若脚本退出并提示缺少 license：
   - 脚本会打印一段带 `--license` 参数的重跑指令。
   - 请把该提示转告用户，请用户提供 license。
   - 收到 license 后，以 `python scripts/load.py --license <license>` 重跑。
   - 成功后 license 会自动保存到 `.license`，后续触发无需再问。
4. 若提示 license 无效：请用户向作者确认正确的 license 后再以 `--license` 重跑。

## references 加载规则（重要覆盖）

本 skill 的 `references/` 目录内容已加密，磁盘上不存在明文文件。**凡是真实指令里提到读取 `references/xxx.md` 的，一律改用以下命令获取其内容，不要直接读文件：**

```
python scripts/load.py --ref xxx.md
```

`--ref` 既接受 `foo.md`，也接受 `references/foo.md` 或带子目录的路径。脚本 stdout 输出的即为该 reference 的完整内容。

## 约束

- 不要尝试自行解读 `payload.enc` 或绕过加密；任何解密失败都按"缺 license / license 无效"处理并回到上面的对话流程。
- `scripts/`、`assets/` 等其他文件为明文，可正常读取调用，不受加密影响。
'''


def _iter_target_files(target_dir: str):
    """枚举需要加密的文件：SKILL.md + references/**/*.md。返回 (payload键, 绝对路径)。"""
    result = []
    skill_md = os.path.join(target_dir, "SKILL.md")
    if os.path.exists(skill_md):
        result.append(("SKILL.md", skill_md))
    refs_dir = os.path.join(target_dir, "references")
    if os.path.isdir(refs_dir):
        for root, _dirs, names in os.walk(refs_dir):
            for name in names:
                if name.lower().endswith(".md"):
                    abs_path = os.path.join(root, name)
                    rel = os.path.relpath(abs_path, target_dir).replace("\\", "/")
                    result.append((rel, abs_path))
    return result


def _copy_plaintext(target_dir: str, output_dir: str, encrypted_keys: set):
    """把目标 skill 里非加密文件原样复制到产物目录（scripts/assets/commands 等）。"""
    for root, dirs, names in os.walk(target_dir):
        # 跳过 references 整个目录（已加密）和 SKILL.md
        rel_root = os.path.relpath(root, target_dir)
        if rel_root == ".":
            # 根目录：跳过 SKILL.md；references 在子目录分支处理
            names = [n for n in names if n != "SKILL.md"]
        if rel_root.split(os.sep)[0] == "references":
            continue
        for name in names:
            src = os.path.join(root, name)
            rel = os.path.relpath(src, target_dir)
            dst = os.path.join(output_dir, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
                fdst.write(fsrc.read())


def cmd_encrypt(args):
    target_dir = os.path.abspath(args.target_skill_dir)
    output_dir = os.path.abspath(args.output_dir)
    if not os.path.isdir(target_dir):
        sys.stderr.write(f"目标 skill 目录不存在: {target_dir}\n")
        sys.exit(1)
    if not os.path.exists(os.path.join(target_dir, "SKILL.md")):
        sys.stderr.write(f"目标目录下没有 SKILL.md: {target_dir}\n")
        sys.exit(1)

    # 1. 读取原 SKILL.md，拆 frontmatter
    with open(os.path.join(target_dir, "SKILL.md"), "r", encoding="utf-8") as f:
        original = f.read()
    frontmatter, body = split_frontmatter(original)
    if not frontmatter:
        sys.stderr.write("无法解析目标 SKILL.md 的 frontmatter（缺少 --- 块）。\n")
        sys.exit(1)

    # skill_id 取 frontmatter 里的 name，取不到就用目录名
    skill_id = os.path.basename(target_dir.rstrip("/\\"))
    for line in frontmatter.splitlines():
        m = line.strip()
        if m.startswith("name:") and not m.startswith("name: |"):
            val = m[len("name:"):].strip().strip('"').strip("'")
            if val:
                skill_id = val
                break

    # 2. 收集要加密的文件，构建 payload
    files = {}
    files["SKILL.md"] = body  # 只加密正文，frontmatter 由 loader 继承
    for key, abs_path in _iter_target_files(target_dir):
        if key == "SKILL.md":
            continue
        with open(abs_path, "r", encoding="utf-8") as f:
            files[key] = f.read()
    payload_json = json.dumps(files, ensure_ascii=False).encode("utf-8")

    # 3. AES-256-GCM 加密
    aes_key = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)
    aes = AESGCM(aes_key)
    ciphertext = aes.encrypt(nonce, payload_json, None)

    # 4. 公钥（内嵌进 load.py 供 license 验签）
    pub_bytes = load_public_key_bytes(args)

    # 5. 准备产物目录
    os.makedirs(output_dir, exist_ok=True)
    scripts_dir = os.path.join(output_dir, "scripts")
    os.makedirs(scripts_dir, exist_ok=True)

    # 6. 生成 load.py
    load_py = (
        LOAD_PY_TEMPLATE
        .replace("<<PUBKEY>>", b64u(pub_bytes))
        .replace("<<AES_KEY>>", b64u(aes_key))
        .replace("<<NONCE>>", b64u(nonce))
        .replace("<<CIPHERTEXT>>", b64u(ciphertext))
        .replace("<<SKILL_ID>>", skill_id)
    )
    with open(os.path.join(scripts_dir, "load.py"), "w", encoding="utf-8") as f:
        f.write(load_py)

    # 7. 生成 loader SKILL.md（原 frontmatter + loader 正文）
    loader_md = frontmatter.rstrip() + "\n\n" + LOADER_BODY_TEMPLATE.lstrip("\n")
    with open(os.path.join(output_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(loader_md)

    # 8. 写 payload.enc（nonce + 密文，留作离线备份；运行时解密用的是 load.py 内嵌的副本）
    with open(os.path.join(output_dir, "payload.enc"), "wb") as f:
        f.write(nonce + ciphertext)

    # 9. .gitignore
    with open(os.path.join(output_dir, ".gitignore"), "w", encoding="utf-8") as f:
        f.write(".license\n")

    # 10. 原样复制 scripts/assets/commands 等明文文件
    _copy_plaintext(target_dir, output_dir, set(files.keys()))

    print(f"已加密 skill: {skill_id}")
    print(f"  产物目录: {output_dir}")
    print(f"  加密文件: SKILL.md" + (f" + {len(files)-1} 个 references" if len(files) > 1 else ""))
    print(f"  明文复制: scripts/assets 等原样保留")
    print(f"下一步：用 license 子命令为 user_id 签发授权码：")
    print(f"  skill-protector.py license <user_id> {skill_id}")


# ---------------------------------------------------------------------------
# license：签发授权码
# ---------------------------------------------------------------------------

def cmd_license(args):
    priv = load_private_key(args)
    license_id = uuid.uuid4().hex
    payload = {
        "user_id": args.user_id,
        "skill_id": args.skill_id,
        "license_id": license_id,
    }
    head = b64u(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    sig = priv.sign(head.encode("ascii"))
    license_code = head + "." + b64u(sig)

    # 可选备忘账本
    try:
        ledger_path(args)
        os.makedirs(key_home(args), exist_ok=True)
        ledger = []
        if os.path.exists(ledger_path(args)):
            with open(ledger_path(args), "r", encoding="utf-8") as f:
                try:
                    ledger = json.load(f)
                except json.JSONDecodeError:
                    ledger = []
        ledger.append({
            "user_id": args.user_id,
            "skill_id": args.skill_id,
            "license_id": license_id,
        })
        with open(ledger_path(args), "w", encoding="utf-8") as f:
            json.dump(ledger, f, ensure_ascii=False, indent=2)
    except OSError:
        pass  # 账本写不进去不影响签发

    print(license_code)


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        description="加密 skill 并加 license 门禁。子命令: init / encrypt / license"
    )
    p.add_argument("--home", help="密钥目录（默认 ~/.skill-protect，可用 SKILL_PROTECT_HOME 覆盖）")
    sub = p.add_subparsers(dest="command", required=True)

    pi = sub.add_parser("init", help="生成 Ed25519 密钥对")
    pi.add_argument("--force", action="store_true", help="私钥已存在时强制重新生成")
    pi.set_defaults(func=cmd_init)

    pe = sub.add_parser("encrypt", help="加密目标 skill")
    pe.add_argument("target_skill_dir", help="目标 skill 目录")
    pe.add_argument("output_dir", help="产物输出目录（加密后的 skill 目录）")
    pe.set_defaults(func=cmd_encrypt)

    pl = sub.add_parser("license", help="签发一份 license")
    pl.add_argument("user_id", help="用户标识（邮箱/订单号等，用于一物一码溯源）")
    pl.add_argument("skill_id", help="目标 skill 的 name（加密时打印的 skill_id）")
    pl.set_defaults(func=cmd_license)

    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()