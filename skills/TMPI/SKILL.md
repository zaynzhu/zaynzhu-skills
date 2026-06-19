---
name: TMPI
description: |
  文本主模型项目初始化工具。当主模型是纯文本/代码模型（glm、deepseek、kimi、qwen-code 等不支持图片输入），且项目启用了可能产生截图的工具（Playwright、Chrome DevTools MCP、Superpowers Chrome），或项目涉及截图分析、验证码识别、UI 自动化截图、图表识别、OCR、图片预览时使用。
  执行后向当前项目的 CLAUDE.md / claude.md 写入图片输入安全规则，禁止把截图/验证码/UI 截图/base64/MCP image block 作为 image payload 直接发送给主模型，要求所有视觉任务改由 model-router skill 处理。写入幂等、兼容多编码、不覆盖已有内容。
  当用户说"不要让图片进入主模型"、"主模型不支持图片"、"防止截图进入上下文"、"初始化文本模型项目规则"、"TMPI"时触发。只在当前项目目录执行，规则只写入当前项目级 CLAUDE.md，不向上冒泡到全局。
---

# TMPI（Text Model Project Init）

## 作用

TMPI 用于初始化“主模型仅支持文本输入”的项目规则，防止 Claude Code / MCP / 浏览器自动化工具把截图、图片、验证码、图表或 UI 截图作为 image payload 直接发送给不支持视觉输入的主模型。

执行后，它会先询问用户是否已经安装并准备使用 `model-router` skill。用户确认后，TMPI 会把一段图片输入安全规则写入当前项目的 `CLAUDE.md` / `claude.md`，要求所有视觉任务都通过 `model-router` 处理。

## 适用场景

在以下情况应优先使用本 skill：

- 当前主模型是纯文本/代码模型，例如某些 `glm`、`deepseek`、`kimi`、`qwen-code` 等模型。
- 项目启用了 Playwright、Chrome DevTools MCP、Superpowers Chrome 等可能产生截图的工具。
- 项目可能涉及截图分析、验证码识别、UI 自动化截图、图表识别、OCR、图片预览。
- 用户要求“不要让图片进入主模型上下文”。

## 必须遵守

1. 不得把任何图片、截图、base64、image payload、MCP image block 直接发送给主模型。
2. 不得为了确认图片内容而直接读取图片为视觉消息。
3. 必须先询问用户是否已经安装并准备使用 `model-router` skill。
4. 用户确认后，才把规则写入当前项目的 `CLAUDE.md`。
5. 写入时必须兼容 Windows / macOS / Linux，并处理 UTF-8、UTF-8 BOM、GBK、GB18030 等编码差异。
6. 如果当前项目已有 `CLAUDE.md` 或 `claude.md`，必须更新而不是覆盖已有内容。
7. 写入规则必须幂等：多次执行不能重复插入同一段内容。

## 执行流程

在当前项目根目录执行脚本：

```bash
python scripts/tmpi.py --project .
```

如果脚本不在当前目录，需要使用本 skill 目录下的实际脚本路径，例如：

```bash
python <TMPI技能目录>/scripts/tmpi.py --project .
```

非交互环境或用户已明确确认时，可以使用：

```bash
python <TMPI技能目录>/scripts/tmpi.py --project . --yes
```

## 执行后检查

写入完成后需要：

1. 读取 `CLAUDE.md` / `claude.md`，确认存在 `TMPI:BEGIN text-model-project-init` 标记。
2. 向用户说明规则已写入哪个文件、使用了什么编码、是否创建了备份。
3. 提醒用户后续图片任务只能传本地图片路径，不能直接传图片内容。

## 用户未安装 model-router 时

如果用户回答未安装 `model-router`，不要强行写入规则。应提示用户先安装 `model-router` skill，安装后再执行 TMPI。

可以给出提示：

```text
请先安装 model-router skill。安装完成后重新执行 TMPI，我会把图片输入安全规则写入当前项目 CLAUDE.md。
```
