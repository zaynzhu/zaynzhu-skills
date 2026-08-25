# Adapter Contract

通用 Skill 不规定宿主实现，但完整适配器必须提供以下能力。

## 必需能力

### 1. 原始消息锚点

在模型回答前提供：

```json
{
  "source_timestamp": 1787897400.0,
  "source_timestamp_trusted": true,
  "timezone": "Asia/Shanghai",
  "timezone_source": "hermes",
  "session_id": "...",
  "owner_key": "telegram:sha256:...",
  "source_ref": "sha256:..."
}
```

`source_timestamp` 必须来自用户消息 metadata。平台未提供原始时间时，应把 `source_timestamp_trusted` 设为 `false`，不能把接收时间假装成发送时间。

### 2. 当轮上下文注入

注入块使用 `<timeline-consistency-context>`，至少包含当前锚点、模式、时区可信度和少量相关事件。注入只影响当轮模型上下文，不应改写原始 transcript。

### 3. 账本操作

适配器提供创建、查询、修订和忘记四类工具。工具必须：

- 从宿主上下文读取锚点，而不是信任模型传入时间戳。
- 在有歧义时返回 `needs_confirmation=true`，且不提交正式事件。
- 使用精确 `event_id` 修订或删除。
- 返回机器可读 JSON。
- 不在日志中输出原始聊天全文。

### 4. 持久化

账本独立于自然语言 transcript 和压缩摘要。上下文压缩、session rotation 或新会话不能改变已经固化的绝对时间。

## 推荐工具返回

成功：

```json
{
  "ok": true,
  "needs_confirmation": false,
  "event": {"id": "...", "start_at": "..."}
}
```

需要确认：

```json
{
  "ok": true,
  "needs_confirmation": true,
  "confirmation_token": "...",
  "candidate": {"start_at": "..."},
  "reason": "timezone_untrusted"
}
```

降级或错误：

```json
{
  "ok": false,
  "code": "missing_source_timestamp",
  "message": "无法取得当前用户消息的可信发送时间"
}
```

## 能力探测

- 完整能力：注入 `mode=full`。
- 有 timestamp 和确定性解析器、无账本：注入 `mode=session-only`。
- timestamp 或确定性解析器缺失：注入 `mode=degraded` 或不注入伪上下文，由 Skill 进入降级模式。

适配器错误不应阻止宿主启动，但必须明确降级。高风险时间信息在降级后必须追问绝对日期。
