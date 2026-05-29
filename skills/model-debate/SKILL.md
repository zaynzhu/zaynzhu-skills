---
name: model-debate
description: |
  多模型辩论：将同一个问题丢给多个 AI 模型，让它们各自回答后合成共识，或多轮互相批评修正。
  当用户想要"多个模型一起讨论"、"让 AI 辩论一下"、"看看不同模型的观点"、"综合多个模型的答案"时触发。
  适用于代码审查、架构决策、方案对比、安全审计等需要多角度分析的场景。
  即使用户只说"让模型们讨论一下"、"辩论一下"、"综合一下"、"second opinion"、"多问几个模型"，也应该触发。
compatibility:
  tools: [bash, python]
---

# Model Debate — 多模型辩论

让多个 AI 模型对同一个问题各自给出回答，然后合成一个比任何单个模型都更好的共识结论。

核心价值：单个模型可能会遗漏或犯错，但多个模型互相挑刺就能把问题看得更全面。

---

## 工作流

```
用户提问 → 并行问 N 个模型 → 收集回答 → [可选: 多轮互相修正] → 合成共识 → 输出
```

**脚本位置**：`skills/model-debate/scripts/model_debate.py`

---

## 快速开始

### 第一次使用：生成配置

```bash
python skills/model-debate/scripts/model_debate.py init
```

这会在 `skills/model-debate/` 下生成 `model-debate.yaml` 和 `model-debate.json`。编辑 YAML 添加你自己的模型和 API key。

### 运行辩论

```bash
# 单轮辩论（3 个模型各自回答，合成共识）
python skills/model-debate/scripts/model_debate.py debate \
  --prompt "这段代码有没有安全漏洞？"

# 多轮辩论（模型们互相审视修正）
python skills/model-debate/scripts/model_debate.py debate \
  --prompt "这个架构方案合理吗？" \
  --mode multi

# 指定参与模型
python skills/model-debate/scripts/model_debate.py debate \
  --prompt "比较 React 和 Vue 的优劣" \
  --models gpt4o,claude-sonnet
```

---

## 两种辩论模式

### Single（单轮，默认）

每个模型独立回答，然后由一个模型综合所有观点生成共识。

**适用场景**：快速获取多角度观点，不需要深度讨论。

```
问题 → [GPT-4o 回答] + [Claude 回答] + [Gemini 回答] → 合成共识
```

### Multi（多轮）

第 1 轮各模型独立回答。第 2 轮起，每个模型看到其他人的回答后修正自己的观点。最多跑 `max_rounds` 轮。

**适用场景**：复杂问题需要深度讨论，模型之间可能互相说服。

```
第 1 轮: 各自独立回答
第 2 轮: 看到其他人的回答 → 修正或坚持
第 3 轮: 再次审视 → 趋于收敛
→ 合成共识
```

---

## 配置文件

`model-debate.yaml` 结构：

```yaml
models:
  gpt4o:
    provider: openai
    model: gpt-4o
    api_key_env: OPENAI_API_KEY
    endpoint: https://api.openai.com/v1/chat/completions
    max_tokens: 4096

debate:
  participants: [gpt4o, claude-sonnet, gemini-flash]  # 参与辩论的模型
  default_mode: single    # 默认模式
  max_rounds: 3           # 多轮模式最大轮数
  convergence_ratio: 0.8  # 收敛阈值
```

添加新模型：在 `models` 下加一个条目，填写 provider/model/api_key_env/endpoint 即可。

---

## 输出格式

```
## 共识结论
（综合所有模型观点的最终答案）

## 各模型观点摘要
### GPT-4o
（核心论点）
### Claude
（核心论点）

## 分歧分析
（模型之间的分歧点及判断）

---
## 各模型原始回答
（完整回答）
```

---

## 适用场景

| 场景 | 为什么适合 |
|------|-----------|
| 代码审查 | 不同模型擅长发现不同类型的问题 |
| 架构决策 | 多角度分析 trade-off |
| 安全审计 | 降低单模型遗漏风险 |
| 方案对比 | 让不同模型分别站在不同立场论证 |
| 事实核查 | 多模型交叉验证减少幻觉 |

---

## 配置管理

```bash
python skills/model-debate/scripts/model_debate.py list   # 查看已配置模型
python skills/model-debate/scripts/model_debate.py init   # 重新生成默认配置
```

---

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| 某个模型调用失败 | 跳过该模型，用剩余模型继续 |
| 所有模型都失败 | 报错，无共识 |
| 合成模型失败 | 直接输出各模型原始回答 |
| API key 未设置 | `list` 命令会显示"未设置" |
