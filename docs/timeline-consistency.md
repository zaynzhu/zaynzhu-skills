# Timeline Consistency

`timeline-consistency` 用来解决 agent 在长对话、跨天和上下文压缩后把“明天”“下周一”等表达重新锚定到错误日期的问题。

## 工作方式

通用 Skill 规定时间语义、确认、复述、冲突和修订规则。Hermes 默认 Plugin 负责读取当前用户消息的 timestamp、执行确定性日期解析、维护独立事件账本，并把少量相关事件注入当轮上下文。

```text
用户原始消息时间
→ 相对时间解析
→ 歧义与冲突检查
→ 可修订事件账本
→ 基于绝对时间回答
```

账本不写入 Hermes 的 `state.db`，而是使用 profile 下的 `plugin-data/timeline-consistency/data.db`。因此自然语言上下文压缩不会重算已经固化的日期。

## Hermes 安装

当前 Hermes Agent 需要 Python 3.11–3.13；安装脚本本身不负责创建或切换 Hermes 的 Python 环境。

先预览：

```bash
python3 skills/timeline-consistency/scripts/install_hermes.py \
  --hermes-home /absolute/path/to/hermes-home \
  --dry-run
```

确认后安装：

```bash
python3 skills/timeline-consistency/scripts/install_hermes.py \
  --hermes-home /absolute/path/to/hermes-home
```

安装器不会覆盖不同内容，也不会自动启用 Plugin。检查后执行：

```bash
hermes plugins enable timeline-consistency
```

建议在当前 Hermes profile 的 `config.yaml` 中明确用户时区；否则远程平台或无法确认本机时区的高风险日期会进入确认流程：

```yaml
plugins:
  enabled:
    - timeline-consistency
  entries:
    timeline-consistency:
      settings:
        timezone: Asia/Shanghai
        retention_days: 0
        trust_remote_timestamps: false
```

`retention_days: 0` 表示不自动删除；正整数只清理超过期限且已经完成、取消或归档的事件，不清理仍在计划中的事件。

Hermes 会给所有消息写入 timestamp，但远程平台缺少事件时间时可能退回接收时间。Plugin 默认不把远程 timestamp 当作已验证的原始发送时间：依赖消息日期的低风险表达会标为推定，高风险表达会要求确认；带完整年份的绝对日期不受这个限制。只有确认目标 adapter 始终提供平台原始发送时间后，才把 `trust_remote_timestamps` 改为 `true`。

## 支持范围

- 中文和英文常见相对日期
- 时间点、全天日期和闭合区间
- 跨日、周、月、年与 IANA 时区
- 计划、历史事件、改期、完成、取消和删除
- 跨 Hermes session 的用户级账本

第一版不提供重复日程、农历、财年、提醒、日历写入或自动现实操作。

## 隐私

事件账本只保存必要的事件名、时间短语、绝对时间和不可逆来源指纹，不复制整段聊天正文。Gateway 用户按 `platform + sender_id 哈希` 隔离，不保存原始 sender ID；明确“忘掉这件事”会删除整个事件版本链及关联待确认候选。

## 降级

没有 Hermes Plugin 时，Skill 仍能规范当前会话中的时间推理；没有可信消息 timestamp 时，高风险相对日期必须追问绝对时间，不能使用模型当前时间冒充历史锚点。
