# 环境兼容性说明

## Claude Code

完整支持：

- 可读取项目 `CLAUDE.md`、README、docs 和 `~/.claude/skills/`。
- 如当前 Claude Code 记忆系统可用，并且用户明确要求，可按平台规则更新记忆。
- 可用 shell 和 git 做文件枚举、diff、验证。

注意：

- 不应把所有历史记录追加到 `CLAUDE.md`。
- 删除历史文档前需要证据，风险高时先确认。

## OpenAI Codex

完整支持文档同步，记忆层按 Codex 环境规则降级：

- 项目规则通常在 `AGENTS.md`。
- 如果当前系统禁止自动写记忆，只输出"建议写入记忆"文本。
- 使用 PowerShell、bash 或平台 shell 的等价命令完成枚举和验证。

## OpenCode

基础支持：

- 可读取 `.opencode/`、`.claude/skills/`、`.codex/skills/` 等常见目录。
- 没有独立记忆系统时，把重点放在 README、docs 和项目级 agent 指令。

## OpenClaw

基础支持：

- 可作为 workspace skill 或 personal skill 使用。
- 若工作区存在 `.openclaw/skills/`，优先检查项目级 skill。
- 不假设 OpenClaw 有 Claude Code 式记忆目录。

## Claude.ai 或无 shell 环境

部分支持：

- 无法运行 `git diff`、`rg`、链接检查等命令时，在对话中执行人工审计。
- 只能基于用户上传或粘贴的文件判断，不声称已全仓库验证。
- 输出改动建议或可复制的补丁，由用户确认后应用。

## 必需工具

- 基础：能读取和编辑 Markdown 文件。
- 推荐：shell、git、`rg`。
- 可选：Markdown 链接检查器或项目已有 lint。

## 优雅降级

| 缺少能力 | 降级方式 |
|----------|----------|
| 无 `rg` | 使用 `find`、`Get-ChildItem`、IDE 文件搜索等价能力 |
| 无 git | 用文件列表和人工 diff 说明验证不足 |
| 无记忆写入权限 | 输出记忆建议，不写入 |
| 无法访问下游项目 | 当前项目先同步，风险项列出待检查路径和关键词 |
| 无法运行文档命令 | 只做静态路径和内容验证 |
