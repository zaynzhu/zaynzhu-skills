# TMR

Text Model Rescue：当 Claude Code 文本主模型会话被图片/截图/base64 image block 污染后持续报 `this model does not support image input` 时，扫描并净化本地 JSONL transcript，把图片块替换为纯文本占位，保留文字上下文。与 TMPI 配套（TMPI 预防、TMR 急救）。

## 适用场景

- 当前主模型是文本模型（glm/deepseek/kimi/qwen-code 等），会话突然开始报 `this model does not support image input`
- Playwright / Chrome DevTools / Superpowers Chrome / MCP 工具返回了截图或图片块
- `/rewind` 只能回到很早的用户消息，不想 `/clear` 丢上下文
- 希望保留会话文字上下文，只移除图片污染块

## 依赖

- Python ≥ 3.8（仅标准库，无第三方包、无外部 API 调用）
- TMPI skill（配套预防图片进入）

## 快速开始

在项目根目录运行（建议新开终端，不要 `/clear`）：

```bash
# 1. 只扫描，不修改
python skills/TMR/scripts/tmr.py scan --project .

# 2. 确认检测到图片污染后，备份并净化
python skills/TMR/scripts/tmr.py rescue --project .
```

然后**完全退出** Claude Code 进程，重新进入项目并 resume（旧污染内容可能仍在进程内存里）。

## 命令

```bash
# 列出当前项目可能对应的 Claude Code transcript
python skills/TMR/scripts/tmr.py list --project .

# 只扫描，不修改
python skills/TMR/scripts/tmr.py scan --project .

# 备份并净化 transcript
python skills/TMR/scripts/tmr.py rescue --project .

# 恢复备份
python skills/TMR/scripts/tmr.py restore --backup /path/to/session.jsonl.tmr.bak.<timestamp>
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
- `rescue` 自动创建 `.tmr.bak.<timestamp>` 备份
- 默认只处理最近的 transcript
- 不修改项目代码，不删除整条消息，只递归替换图片内容
- 处理失败可用 `restore` 恢复备份

## 与 TMPI 的关系

- **TMPI**：开局预防，把「文本模型禁止接收图片内容」的规则写入 `CLAUDE.md`
- **TMR**：事后急救，清理已经污染的 transcript

两者建议一起使用。

## 注意

- TMR 修改的是 Claude Code 本地 session transcript，内部格式可能随版本变化，脚本采用递归扫描避免依赖固定字段
- `rescue` 后仍报错时，完全退出 Claude Code 进程再重新打开 resume（旧污染内容可能仍在内存）
- TMR 不是 `/rewind` 的替代品，不恢复 Claude Code 隐藏状态，不修改项目代码