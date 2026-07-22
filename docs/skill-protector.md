# skill-protector

给任意 skill 套上"加密 + license 门禁"的加密器：把目标 skill 的 `SKILL.md` 和 `references/*.md` 用 AES-256-GCM 加密，产出一个带 license 激活机制的可分发 skill。终端用户没 license 跑不起来，有 license 才解密出真实指令供智能体执行。

## 功能

- **AES-256-GCM 加密**：加密目标 skill 的 `SKILL.md` 正文 + `references/**/*.md`；`scripts/assets/commands` 等其他文件原样明文保留
- **Ed25519 license 门禁**：作者持私钥签发授权码，产物内嵌公钥验签，一物一码、泄露可溯源
- **缺 license 交互流程**：load.py 检测到无 license 时打印提示退场，由智能体转告用户填入 `--license` 重跑，校验通过后自动保存到 `.license`，后续无需再填
- **references 按需解密**：`load.py --ref <name>` 解密单个 reference 到 stdout，不落盘、不撑上下文
- **每 skill 独立 AES key**：单 skill 密钥泄露不波及其他 skill

## 防护定位

**防小白白嫖级别**，不是商业级 DRM。skill 本质是给智能体读的文本，解密加载后内容进入用户可控上下文——懂行人能让智能体吐出明文。本工具防的是"双击打开 .md 抄走"的小白，防不了读 load.py / 读上下文的懂行人。需要商业级防护请另寻方案。

## 依赖

- Python ≥ 3.8
- `cryptography` 库（`pip install cryptography`）

## 快速开始

```bash
# 0. 安装依赖
pip install cryptography

# 1. 一次性生成 Ed25519 密钥对（存到 ~/.skill-protect/）
python skills/skill-protector/scripts/skill_protector.py init

# 2. 加密目标 skill，产物写到同级 .encrypted/<skill-name>（目录名保持原名）
python skills/skill-protector/scripts/skill_protector.py encrypt skills/my-secret-skill skills/.encrypted/my-secret-skill

# 3. 为用户签发 license（user_id 用邮箱/订单号，skill_id 是上一步打印的 name）
python skills/skill-protector/scripts/skill_protector.py license alice@example.com my-secret-skill
# → 把输出的 license 串发给 alice

# 4. 把 .encrypted/my-secret-skill 整个目录发给用户
#    用户复制到自己的 .claude/skills/ 或 .codex/skills/ 即可
```

## 产物目录约定

`<output_dir>` 默认用 `<原 skill 同级目录>/.encrypted/<原 skill 目录名>`，用一层 `.encrypted/` 隔离明文版与加密版。产物目录名必须与原 skill 一致，禁止起 `xxx-encrypted` 这类带后缀的新名。若另行明确指定 output_dir，按指定路径，但仍建议目录名保持原名。例：原 skill 在 `skills/my-skill` → 输出到 `skills/.encrypted/my-skill`。

终端用户首次运行加密 skill 时，智能体会运行 `scripts/load.py`，检测到无 license 后转告用户填入，用户把作者发的 license 贴出，智能体以 `python scripts/load.py --license <code>` 重跑即激活。

## 子命令

| 子命令 | 作用 |
|--------|------|
| `init [--force]` | 生成 Ed25519 密钥对到 `~/.skill-protect/`；`--force` 强制重建（旧 license 全失效） |
| `encrypt <target_dir> <output_dir>` | 加密目标 skill，产出带门禁的 skill 目录 |
| `license <user_id> <skill_id>` | 用私钥签发一份 license 字符串 |

密钥目录可用 `--home` 或环境变量 `SKILL_PROTECT_HOME` 覆盖（测试时用它隔离，避免污染真实密钥）。

## 加密产物结构

```
<原 skill 名>/
├── SKILL.md            ← 明文 loader：frontmatter 继承原 skill + 加载器指令
├── scripts/
│   └── load.py         ← 内嵌公钥 + AES key + 解密/--ref/--license 逻辑
├── payload.enc         ← 原 SKILL.md 正文 + references/*.md，AES-GCM 加密
├── .gitignore          ← 排除 .license
└── scripts/assets 等其他文件 ← 原样明文保留
```

## 安全注意

- **私钥是命脉**：`~/.skill-protect/private_key.pem` 绝不外泄、绝不进 git、绝不放进加密产物
- **只发产物，不发加密器**：作者只把加密后的 skill 目录发给用户/公司，加密器本身和私钥都留在本机
- **加密范围**：仅 `SKILL.md` + `references/**/*.md`；`agents/*.md` 等其他 .md 不加密（如需扩大范围，扩展脚本 `_iter_target_files`）
- **不做有效期 / 吊销**：当前无时间校验、无吊销机制；license_id 字段已预留，将来可加内嵌黑名单 + 重发新版实现吊销

## 平台兼容

机制只依赖 `SKILL.md` + 跑 `python` 脚本，Claude Code / Codex CLI / OpenCode 通用。Windows 下 load.py 已强制 UTF-8 输出，避免控制台编码导致中文乱码。

## 关联技能

- `enhanced-skill-creator`：本 skill 由该工具按既定规格创建