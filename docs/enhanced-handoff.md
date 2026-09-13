# enhanced-handoff 使用说明

把一个任务交给没有原始对话的另一位 agent，支持设计转执行、中途续做、执行后交回审查。减少目标、决策和验收偏差，允许实现细节不同。

## 常用请求

```text
把我们确认的设计整理成给另一个模型执行的交接文档，放到 docs/handoffs/local-search.md。
```

```text
这项改造做到一半，我准备换工具。更新当前交接，写清未提交改动和还没跑的验证。
```

```text
实现完成了，整理交接给原模型只读审查，注明审查基准和验证证据。
```

生成端交付文档路径和可复制启动指令。接收端即使未安装技能，也可以直接接受：

```text
请读取 docs/handoffs/local-search.md，按文档中的角色接手；核对当前项目状态，无阻塞就继续，完成后交回结果。
```

发送和接收两端都可以显式调用：

```text
使用 enhanced-handoff，发送当前任务，交给下一位执行。
```

```text
使用 enhanced-handoff，接收 docs/handoffs/local-search.md，先检查交接中的决定、状态和验收，再继续实现。
```

```text
使用 enhanced-handoff，接收 docs/handoffs/local-search.md，做只读审查并交回结论。
```

接收时会先做轻量接手审视，不会因为调用技能就自动修代码或展开全项目审查。未安装时仍可用前述普通启动指令。

若只希望阅读，不要使用“继续执行”；明确说“只读这份文档并告诉我你的理解”。

## 文档维护

优先使用指定位置；否则复用同任务已有文档，默认新建 `docs/handoffs/<任务名>.md`。同任务更新当前状态，不自动产生多份快照。没有写入权限时直接输出 Markdown，明确尚未保存。

交接记录用户确认、模型建议、待定问题，区分已实现与已验证。接手方先核对版本和必要材料，简短复述后继续；实质冲突只暂停受影响部分。完成或受阻交回时更新结果；只读审查没有文档写入授权则在回复中交回。

本技能不自动运行另一工具、不协调同时写入、不安装技能、不重写 AGENTS.md／CLAUDE.md，也不自动提交、推送、合并或发布。

## 安装与兼容性

按目标工具机制加载 [技能目录](../skills/enhanced-handoff/)。项目内安装可将整个目录复制到目标项目 `.codex/skills/` 或 `.claude/skills/`；其他工具按其自身机制加载，不假定 zcode 的发现路径。

具体能力降级及未验证边界见 [环境说明](../skills/enhanced-handoff/ENVIRONMENTS.md)。当前标记为实验性；真实跨工具、跨模型效果需要实际使用验证。

## 与相关技能的区别

- `project-onboard` 维护长期项目规则。
- `enhanced-neat-freak` 同步项目知识。
- `enhanced-handoff` 维护一次任务的可接手状态，无需依赖前两者。

参考 [mattpocock/skills handoff](https://github.com/mattpocock/skills/blob/main/skills/productivity/handoff/SKILL.md)，保留提炼、引用已有产物与脱敏原则，增加决策依据、接手核对、角色限制与结果交回。
