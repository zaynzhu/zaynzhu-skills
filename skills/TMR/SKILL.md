---
name: TMR
version: 0.1.0
description: Text Model Rescue. Rescue Claude Code sessions polluted by image blocks when the current text-only model rejects image input.
---

# TMR（Text Model Rescue）

TMR 用于处理当前主模型不支持图片输入时，Claude Code 会话 transcript 被图片、截图、base64 image、MCP image block 污染后导致整个会话持续报错的问题。

典型错误：

```text
API Error: 400 this model does not support image input
```

## 触发时机

当用户遇到以下情况时，应建议使用 TMR：

- Claude Code 当前模型是文本模型，但会话突然开始报 `this model does not support image input`
- Playwright / Chrome DevTools / Superpowers Chrome / MCP 工具返回了截图或图片块
- `/rewind` 只能回到很早的用户消息，用户不想 `/clear` 丢上下文
- 用户希望保留会话文字上下文，只移除图片污染块

## 重要限制

TMR 不是 Claude Code 内置 `/rewind` 的替代品，它不会恢复 Claude Code 的隐藏状态，也不会修改项目代码。

TMR 的目标是：

1. 查找 Claude Code 本地 JSONL transcript
2. 备份原始 transcript
3. 扫描并替换 image block / image_url / base64 图片内容
4. 尽量保留文本上下文和工具调用记录
5. 让文本模型重新可以加载当前会话

## 使用原则

- 默认先 `scan`，不要直接修改
- 执行 `rescue` 前必须备份
- 默认只处理最近的 session
- 不删除整条 JSONL 消息，只把图片内容替换为纯文本占位
- 如处理后仍报错，需要完全退出 Claude Code 后再 resume
- 如果处理错了，使用 `restore` 恢复备份

## 命令

在项目根目录执行：

```bash
python <TMR技能目录>/scripts/tmr.py scan --project .
```

执行急救：

```bash
python <TMR技能目录>/scripts/tmr.py rescue --project .
```

主动存档（在调用截图类工具之前使用，创建当前 transcript 的时间戳快照）：

```bash
python <TMR技能目录>/scripts/tmr.py save --project .
```

列出可疑 transcript：

```bash
python <TMR技能目录>/scripts/tmr.py list --project .
```

恢复备份或快照：

```bash
python <TMR技能目录>/scripts/tmr.py restore --backup <backup-or-snap-file>
```

## /TMR 的参数化触发

用户通过 `/TMR <action>` 调用本 skill 时，按 action 自动选择子命令，无需追问：

- `/TMR` 或 `/TMR scan` → 立即执行 `tmr.py scan --project .`（只读体检）
- `/TMR save` → **立即执行 `tmr.py save --project .`**（主动存档，创建带时间戳的 transcript 快照）。不要先 scan，不要追问，直接存档并回报快照路径。
- `/TMR rescue` → 立即执行 `tmr.py rescue --project .`（备份并净化）
- `/TMR restore` → 询问要恢复哪个备份/快照路径，再执行 `tmr.py restore --backup <path>`
- `/TMR list` → 立即执行 `tmr.py list --project .`

说明：`save` 是事前预防动作，目的是在即将调用可能产生截图的工具（Playwright、Chrome DevTools、Superpowers Chrome 等）之前留一个物理存档点；一旦后续会话被图片污染，可用 `restore` 直接回到这个存档点，比 `rescue` 在脏数据上替换更干净。

## 推荐工作流

遇到图片污染时，不要 `/clear`，先新开一个终端，在当前项目目录执行：

```bash
python ~/.claude/skills/TMR/scripts/tmr.py scan --project .
python ~/.claude/skills/TMR/scripts/tmr.py rescue --project .
```

然后完全退出当前 Claude Code，重新进入项目并 resume。

## 与 TMPI 的关系

- TMPI：开局预防，把“文本模型禁止接收图片内容”的规则写入 `CLAUDE.md`
- TMR：事后急救，清理已经污染的 transcript

这两个 skill 建议一起使用。
