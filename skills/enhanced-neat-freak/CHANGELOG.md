# Enhanced Neat Freak 变更日志

## 迭代 1（2026-06-18）

### 失败的测试用例

- 暂无自动运行结果；本轮为初版创建，先提供 L1/L2/L3 评测用例。

### 具体修改

- 新增 `SKILL.md`：定义知识库同步的五种工作模式、证据账本、最小同步流程、反膨胀规则和交付格式。
- 新增 `references/upgrade-notes.md`：说明相对本地 `neat-freak` 的增强点。
- 新增 `references/change-impact-matrix.md`：把变更类型映射到 README、docs、项目级指令和记忆层。
- 新增 `references/audit-checklist.md`：作为交付前自审门禁。
- 新增 `evals/evals.json`：覆盖正常同步、只审计、歧义输入和危险删除。
- 新增 `ENVIRONMENTS.md`：说明 Claude Code、Codex、OpenCode、OpenClaw 和无 shell 环境下的行为。

### 预期效果

- 新技能比旧版更适合在真实仓库中做最小必要同步。
- 面对歧义或危险请求时优先审计和建立证据，不直接大范围修改。
- 对不能写记忆的环境有明确降级方式。
