---
name: skill-protector
description: |
  给任意 skill 套上"加密 + license 门禁"的加密器。当用户想保护自己的 skill 不被随手白嫖、想给 skill 加授权码门禁、想把 skill 加密后分发给客户/公司、想给 skill 做 license 激活机制时触发。
  即使用户只说"加密这个 skill"、"给 skill 加 license"、"保护我的 skill"、"skill 防复制"、"授权码 skill"、"加密分发 skill"，也应该触发本技能。
  本技能只做轻量防护（防小白白嫖，懂行人仍可破），不做商业级 DRM。依赖 Python cryptography 库。
---

# Skill Protector —— 加密并给 skill 加 license 门禁

把一个目标 skill 的 `SKILL.md` 和 `references/*.md` 用 AES-256-GCM 加密，产出一个带 license 门禁的可分发 skill。终端用户没 license 就跑不起来；有 license 才解密出真实指令供智能体执行。

## 防护定位（必须先理解）

这是**防小白白嫖**级别的轻量方案，不是商业级 DRM：

- skill 的本质是给智能体读的文本，智能体一旦解密加载，内容就进了用户可控的上下文——**懂行人能让智能体把解密后的明文吐出来**。这是 skill 载体的固有矛盾，无法用任何加密消除。
- 因此本工具防的是"双击打开 .md 抄走"的小白；防不了"懂行人读 load.py / 读上下文"。如果你需要商业级防护，本工具不是答案。
- license 用 Ed25519 非对称签名：作者持私钥签发，load.py 内嵌公钥验证。load.py 泄露只能"验"不能"伪造新码"。

## 依赖

- Python ≥ 3.8
- `cryptography` 库（`pip install cryptography`）
- 加密器脚本：`scripts/skill_protector.py`

## 机制一览

加密后产物结构（目录名与原 skill 同名）：

```
<原 skill 名>/
├── SKILL.md            ← 明文 loader：frontmatter 继承原 skill + 加载器指令
├── scripts/
│   └── load.py         ← 内嵌公钥 + AES key + 解密/--ref/--license 逻辑
├── payload.enc         ← 原 SKILL.md 正文 + references/*.md，AES-GCM 加密
├── .gitignore          ← 排除 .license
└── scripts/assets/commands 等其他文件 ← 原样明文保留
```

加载流程（终端用户侧）：
1. 智能体触发 skill → 读明文 loader SKILL.md → 被告知运行 `python scripts/load.py`。
2. load.py 没找到 license → 打印提示退场 → 智能体转告用户 → 用户提供 license → 智能体以 `--license` 重跑。
3. load.py 用内嵌公钥验签 license（含 user_id/skill_id/license_id）→ 通过则存 `.license` → 用内嵌 AES key 解密 payload → 把真实 SKILL.md 正文打印到 stdout。
4. 智能体读 stdout 当作真实指令执行。后续触发自动读 `.license`，不再问。
5. references 已加密：真实指令里提到读 `references/xxx.md` 时，智能体改用 `python scripts/load.py --ref xxx.md` 获取（loader 正文已写死这条覆盖指令）。

## 三个子命令

脚本：`scripts/skill_protector.py`。密钥目录默认 `~/.skill-protect/`，可用 `--home` 或环境变量 `SKILL_PROTECT_HOME` 覆盖（测试时用它隔离，别污染真实密钥）。

### 1. init —— 生成密钥对（一次性）

```bash
python scripts/skill_protector.py init
```

- 生成 Ed25519 密钥对：`~/.skill-protect/private_key.pem`（私钥，**绝不外泄**）、`public_key.pem`。
- 已存在私钥时默认拒绝覆盖，加 `--force` 才重建（重建后旧 license 全部失效）。

### 2. encrypt —— 加密目标 skill

```bash
python scripts/skill_protector.py encrypt <target_skill_dir> <output_dir>
```

- 读取目标 skill 的 `SKILL.md` frontmatter（name/description 原样继承进 loader）、正文 + `references/**/*.md`。
- 生成随机 AES-256 key 加密 payload，把公钥和 AES key 内嵌进产物的 `load.py`。
- `scripts/`、`assets/`、`commands/` 等其他文件原样明文复制。
- 打印 `skill_id`（取自 frontmatter 的 name），下一步签发 license 要用。

### 3. license —— 签发授权码

```bash
python scripts/skill_protector.py license <user_id> <skill_id>
```

- 用私钥签发 `sign(user_id + skill_id + license_id)`，输出 license 字符串（JWT 风格 `head.sig`）。
- `user_id` 用邮箱/订单号等，实现一物一码、泄露可溯源（license 里就带 user_id，base64 解开即可读）。
- 可选备忘账本 `~/.skill-protect/issued.json` 自动追加记录。
- 把 license 字符串发给对应用户；用户首次运行加密 skill 时填入即可。

## 完整工作流

```bash
# 0. 安装依赖
pip install cryptography

# 1. 一次性生成密钥
python scripts/skill_protector.py init

# 2. 加密某个 skill（产物写到 ./dist/<skill-name>）
python scripts/skill_protector.py encrypt skills/my-secret-skill ./dist/my-secret-skill

# 3. 为每个用户签发 license
python scripts/skill_protector.py license alice@example.com my-secret-skill
# → 把输出的 license 串发给 alice

# 4. 把 dist/my-secret-skill 整个目录发给用户/公司
#    用户复制到自己的 .claude/skills/ 或 .codex/skills/ 即可
```

## 发布

- 产物目录直接复制到目标平台：`.claude/skills/<skill-name>/` 或 `.codex/skills/<skill-name>/`。
- **不要把加密器本身（本 skill）发给公司**——你只负责加密，只把加密产物发出去。私钥始终留在你本机。
- 产物里的 `.gitignore` 已排除 `.license`；如果用户要提交到自己的 git，确认 `.license` 已被忽略。

## 安全与边界

- **私钥保管**：`~/.skill-protect/private_key.pem` 是整套机制的命脉，绝不外泄、绝不进 git、绝不放进加密产物。公钥可以外发。
- **每 skill 独立 AES key**：加密时随机生成，单 skill 的 key 泄露不波及其他 skill。
- **不做有效期 / 吊销**：当前 license 无有效期、无吊销机制；license_id 字段已预留，将来要做吊销（内嵌黑名单 + 重发新版）时不用改 license 结构。
- **不加密的文件**：`scripts/`、`assets/`、`commands/` 等保持明文。如果目标 skill 的核心机密在 `agents/*.md` 等非 references 的 .md 文件里，当前不会加密——加密范围仅 `SKILL.md` + `references/**/*.md`。如需扩大范围，扩展 `skill_protector.py` 的 `_iter_target_files`。
- **改本机时间无效**：因为没做有效期，没有时间校验，所以也不存在改时间绕过的问题。

## 平台兼容

机制只依赖 `SKILL.md` + 跑 `python` 脚本，Claude Code / Codex CLI / OpenCode 均通用。load.py 的 stdout 注入和缺 license 对话流程写在 loader 正文里，跨平台行为一致。

## 常见问题

- **用户报"license 无效"**：确认他填的 license 是你为**这个 skill_id** 签发的（license 绑定 skill_id，换 skill 不能通用）；确认私钥没被 `--force` 重建过。
- **用户重装 skill 后又要填 license**：`.license` 存在 skill 目录内，删了 skill 就没了，属正常。想跨重装保留可改成存全局配置（当前未实现）。
- **想换一套加密方案给公司**：本工具暂不支持可插拔方案；如需国密 SM4/SM2 等公司指定方案，仿写一个简化版即可。