# model-debate

多模型辩论——将同一个问题丢给多个 AI 模型，让它们各自回答后合成共识，或多轮互相批评修正。

## 两种模式

- **Single（单轮）**：每个模型独立回答，然后由一个模型综合所有观点生成共识
- **Multi（多轮）**：第 1 轮各模型独立回答，第 2 轮起看到其他人的回答后修正自己的观点，最多跑 `max_rounds` 轮

## 适用场景

| 场景 | 为什么适合 |
|------|-----------|
| 代码审查 | 不同模型擅长发现不同类型的问题 |
| 架构决策 | 多角度分析 trade-off |
| 安全审计 | 降低单模型遗漏风险 |
| 方案对比 | 让不同模型分别站在不同立场论证 |
| 事实核查 | 多模型交叉验证减少幻觉 |

## 快速开始

```bash
# 第一次使用：生成配置
python skills/model-debate/scripts/model_debate.py init

# 单轮辩论
python skills/model-debate/scripts/model_debate.py debate \
  --prompt "这段代码有没有安全漏洞？"

# 多轮辩论
python skills/model-debate/scripts/model_debate.py debate \
  --prompt "这个架构方案合理吗？" \
  --mode multi
```

## 配置文件

`model-debate.yaml` 定义参与模型和辩论参数。支持 OpenAI、Anthropic、Google、Ollama 等多 provider。

## 依赖

- Python ≥ 3.8
- `curl`（调用模型 API）
- 模型 API Key（各模型各自配置）