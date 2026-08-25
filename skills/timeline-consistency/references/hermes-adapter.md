# Hermes 默认适配

## 为什么需要 Plugin

Hermes 的消息表会保存 `timestamp`，但 Skill 本身只是按需加载的知识文档，无法可靠读取每条消息 metadata，也不能保证每轮执行。默认适配因此使用 Hermes Plugin：

- `pre_llm_call` 在当前用户消息已经带 timestamp 后读取锚点。
- Plugin tools 在最终回答前执行确定性解析和账本写入。
- `plugin_db()` 把账本放在 profile 对应的 `plugin-data/timeline-consistency/data.db`。
- 相关事件以临时上下文注入，不改写 transcript。

## 安装

在技能目录执行：

```bash
python3 scripts/install_hermes.py --hermes-home /absolute/path/to/hermes-home
```

安装器复制 Skill 与 Plugin，但不会覆盖已有不同文件，也不会自动启用 Plugin。检查内容后手动启用：

```bash
hermes plugins enable timeline-consistency
```

如果使用默认 `~/.hermes`，可以省略 `--hermes-home`。先用 `--dry-run` 查看目标。

建议在当前 profile 的 `config.yaml` 中显式设置用户时区：

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

## 时区

适配器优先级：

1. Plugin 的 `timezone` 设置
2. Hermes 的 IANA timezone 配置
3. 系统时区

系统时区不等于用户时区。远程 Gateway 的高风险事件在只取得系统时区时会要求用户确认。

## 时间戳可信度

Hermes transcript 的每条消息都有 timestamp，但远程平台没有事件时间时可能使用接收时间。Plugin 默认只信任本地 CLI、Desktop 和 oneshot 的当轮时间；远程 Gateway timestamp 可用于解析依赖锚点的候选，但低风险结果标为 `inferred`，高风险结果必须确认。带完整年份的绝对日期不依赖消息日期，可以直接固化。

只有核实目标 adapter 始终把平台原始发送时间传给 Hermes 后，才设置 `trust_remote_timestamps: true`。这个开关按 profile 生效，不能根据一次看似正确的消息推断。

## 保留期限

`retention_days` 默认为 `0`，表示不自动删除。设为正整数后，只清理超过期限的已完成、已取消或历史事件版本链；仍在计划中的事件不会被自动删除。用户明确要求“忘掉这件事”时不受该期限影响，会立即删除整个版本链。

## 压缩

账本与 transcript 分离，因此 Hermes 的自然语言压缩不会改写账本。v0.1 不替换 ContextEngine，也不启用 fail-closed compression checkpoint，因为账本在每个相关回合的工具调用中即时写入。

如果未来需要在压缩前归档所有原始证据，再单独实现 MemoryProvider `on_pre_compress` checkpoint；不要为此接管整个 ContextEngine。

## 已知限制

- 平台 adapter 没有提供原始发送时间时，Hermes 只能保存接收时间；Plugin 无法从单个 timestamp 自动辨别两者，因此远程时间默认不可信。
- 模型仍需遵循 Plugin 注入并调用工具；v0.1 是对话一致性辅助，不是硬实时调度系统。
- 不执行提醒、日历写入或现实操作。
- Plugin 不读取历史聊天全文建立账本；只有安装后、实际触发工具的事件进入账本。
