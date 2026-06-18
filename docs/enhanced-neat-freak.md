# enhanced-neat-freak

`enhanced-neat-freak` 是知识库收尾、文档同步和交接清理技能。它用于在一个开发阶段结束后，把 README、docs、`CLAUDE.md`、`AGENTS.md` 和可用记忆与当前代码事实对齐，同时避免文档膨胀。

## 适用场景

- 功能完成后说"同步一下文档"、"收尾"、"整理一下"。
- 发现 README、docs、项目级 agent 指令互相冲突。
- 上线、重构或目录改名后，需要检查文档是否过期。
- 要做新人交接或让下一个 agent 能直接接手。
- 用户明确要求更新记忆或输出记忆建议。

不适用于普通磁盘清理、代码格式化或依赖升级。

## 核心增强

相对本地旧版 `neat-freak`，新版增加：

- 五种工作模式：`audit-only`、`sync`、`handoff`、`anti-bloat`、`memory-note`。
- 证据账本：每条更新都要有证据来源、影响层和验证方式。
- 最小同步：只处理与请求、代码事实或文档冲突直接相关的文件。
- 反膨胀：防止把历史叙事塞进 `CLAUDE.md` / `AGENTS.md`。
- 平台降级：不能写记忆时输出建议，不绕过权限。
- L1/L2/L3 评测用例和兼容性说明。

## 目录结构

```text
skills/enhanced-neat-freak/
├── SKILL.md
├── CHANGELOG.md
├── ENVIRONMENTS.md
├── evals/
│   └── evals.json
└── references/
    ├── audit-checklist.md
    ├── change-impact-matrix.md
    └── upgrade-notes.md
```

## 使用方式

在支持 Skills 的工具中安装后，可以直接说：

```text
这个阶段做完了，帮我同步一下文档。
```

```text
先别改文件，检查 README、docs 和 AGENTS.md 有没有冲突。
```

```text
帮我做交接整理，让新人能直接上手。
```

## 验证方式

技能自身没有必需脚本。维护本技能时，至少检查：

```bash
git diff --check
```

并确认 `SKILL.md` 引用的 `references/`、`evals/` 文件存在。

## 环境兼容

详见 `skills/enhanced-neat-freak/ENVIRONMENTS.md`。
