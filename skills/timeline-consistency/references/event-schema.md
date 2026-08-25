# 事件账本 Schema

通用适配器可以使用不同存储实现，但应提供以下语义字段。

```json
{
  "id": "事件版本 ID",
  "root_id": "逻辑事件 ID",
  "version": 1,
  "supersedes_id": null,
  "label": "请假",
  "kind": "date",
  "start_at": "2026-08-29T00:00:00+08:00",
  "end_at": "2026-08-29T23:59:59.999999+08:00",
  "timezone": "Asia/Shanghai",
  "status": "planned",
  "risk_level": "high",
  "certainty": "deterministic",
  "source_expression": "明天",
  "source_timestamp": 1787897400.0,
  "source_session_id": "session-id",
  "source_ref": "不可逆消息指纹",
  "is_current": true,
  "created_at": 1787897401.0
}
```

## 字段约束

- `kind`：`date`、`datetime` 或 `interval`。
- `status`：`planned`、`completed`、`cancelled` 或 `historical`。
- `risk_level`：`low` 或 `high`。
- `certainty`：`deterministic`、`confirmed` 或 `inferred`。
- `source_expression` 只保存必要的时间短语，不保存整段聊天内容。
- `source_ref` 使用 session、发送时间和消息内容生成不可逆哈希，避免复制真实聊天正文。
- 同一 `root_id` 只能有一个 `is_current=true` 的版本。

## 修订

修订不是覆盖：

1. 读取当前版本。
2. 将当前版本设为非当前。
3. 插入 `version + 1`，并让 `supersedes_id` 指向旧版本。
4. 新版本成为当前版本。

改期改变时间；完成或取消只改变状态，也应生成新版本。

风险等级采用单调保护：当前版本为 `high` 时，修订不能仅凭模型传参降为 `low`。第一版不提供自动降级通道。

## 删除

用户明确要求忘记事件时，删除对应 `root_id` 的全部版本与待确认记录。隐私删除不保留可检索墓碑；操作日志最多记录匿名计数，不能保存事件名或原文。

## 所有者隔离

账本至少按 agent profile 和用户隔离：

- Gateway：`platform + sender_id 的不可逆哈希`，不在账本保存原始 sender ID
- 本地单用户 CLI：`local`
- 无稳定用户标识时：退回 `session_id`，并声明不能跨会话共享

查询和修改必须始终携带同一个 `owner_key`，防止不同聊天用户互相看到时间线。
