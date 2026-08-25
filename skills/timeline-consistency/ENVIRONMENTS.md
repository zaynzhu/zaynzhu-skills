# 环境兼容性说明

## Hermes Agent（完整支持）

安装默认 Plugin 后可读取当前用户消息 timestamp、使用独立 SQLite 账本、跨 session 查询，并在压缩后保持已固化事件不变。当前 Hermes Agent 需要 Python 3.11–3.13 和 Plugin API v1。

本地 CLI/Desktop 的当轮 timestamp 默认可信；远程 Gateway 必须核实 adapter 确实提供原始发送时间后，才能开启 `trust_remote_timestamps`。

## Claude Code / Codex CLI / OpenCode（部分支持）

Skill 的语义、确认、复述和冲突规则可用。如果宿主或第三方 adapter 提供原始消息 timestamp 与 Adapter Contract 工具，可以进入完整模式；否则只维护当前上下文，不承诺跨会话持久化。

## 纯提示词环境（降级）

没有可信 timestamp 时，重要相对日期必须询问绝对日期。低风险内容可以根据显式提供的对话时间推定并标注，但不能把模型当前时间当作历史消息时间。

## 必需工具

- 通用 Skill：无
- Hermes 完整模式：Python 3.11–3.13、Hermes Plugin API、SQLite（Python 标准库）

## 明确不支持

- 农历、财年和复杂重复日程
- 到点提醒、日历写入或自动执行现实动作
- 从未提供时间戳的旧消息中恢复真实发送时间
