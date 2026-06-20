# TMR - Text Model Rescue

TMR 是一个用于 Claude Code 的会话急救 skill。当你使用 `glm-5.2:cloud`、`deepseek-v4-pro:cloud`、`kimi-k2.7-code:cloud` 等文本模型时，如果 Playwright、Chrome DevTools、Superpowers Chrome 或其他 MCP 工具把截图/image block 写入了 Claude Code 会话，后续请求可能持续报错：

```text
API Error: 400 this model does not support image input
```

普通的补救指令无法执行，因为模型请求在进入推理前就被 API 拒绝。TMR 通过外部脚本直接扫描并净化 Claude Code 本地 JSONL transcript，把图片块替换成纯文本占位，尽量保留原有文字上下文。

## 安装

把整个 `TMR` 目录放到你的 Claude Code skills 目录，例如：

```text
~/.claude/skills/TMR
```

Windows 示例：

```text
C:\Users\你的用户名\.claude\skills\TMR
```

## 快速使用

在项目根目录运行：

```bash
python ~/.claude/skills/TMR/scripts/tmr.py scan --project .
```

确认检测到图片污染后执行：

```bash
python ~/.claude/skills/TMR/scripts/tmr.py rescue --project .
```

然后完全退出 Claude Code，再重新进入项目并 resume。

## Windows 用法

PowerShell 示例：

```powershell
python "$env:USERPROFILE\.claude\skills\TMR\scripts\tmr.py" scan --project .
python "$env:USERPROFILE\.claude\skills\TMR\scripts\tmr.py" rescue --project .
```

## 命令说明

### list

列出当前项目可能对应的 Claude Code transcript。

```bash
python scripts/tmr.py list --project .
```

### scan

只扫描，不修改。

```bash
python scripts/tmr.py scan --project .
```

### rescue

备份并净化 transcript。

```bash
python scripts/tmr.py rescue --project .
```

### restore

恢复备份。

```bash
python scripts/tmr.py restore --backup /path/to/session.jsonl.tmr.bak.20260620_153012
```

## 支持清理的污染类型

- `{"type":"image"}` 对象
- `{"type":"image_url"}` 对象
- `source.type = base64` 且 `media_type` 为 `image/*`
- 字符串里的 `data:image/png;base64,...`
- 字符串里的超长疑似 base64 图片
- 常见 MCP 工具结果中的 image/screenshot 字段

## 安全策略

- `scan` 默认不修改任何文件
- `rescue` 会自动创建 `.tmr.bak.<timestamp>` 备份
- 默认只处理最近的 transcript
- 不修改项目代码
- 不删除整条消息，只递归替换图片内容
- 处理失败可用 `restore` 恢复备份

## 注意事项

TMR 修改的是 Claude Code 本地 session transcript。Claude Code 的内部格式可能随版本变化，所以脚本采用递归扫描方式，尽量避免依赖固定字段。

如果执行 `rescue` 后仍然报错，请完全退出 Claude Code 进程，再重新打开并 resume。原因是旧污染内容可能仍在当前进程内存里。
