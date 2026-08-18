# TMPI

Text Model Project Init：为「主模型仅支持文本输入」的项目初始化 `CLAUDE.md` 图片输入安全规则，避免截图、图片、验证码、图表、UI 自动化截图等视觉内容被直接发送给不支持图片输入的主模型。

## 功能

- 检测当前主模型是否为纯文本/代码模型（如 `glm`、`deepseek`、`kimi`、`qwen-code` 等）
- 询问用户是否已安装并准备使用 `model-router` skill
- 用户确认后，把图片输入安全规则写入当前项目的 `CLAUDE.md` / `claude.md`
- 要求所有视觉任务（截图分析、验证码识别、UI 自动化截图、图表识别、OCR、图片预览）改由 `model-router` 处理
- 写入幂等：多次执行不重复插入同一段内容
- 兼容 Windows / macOS / Linux，处理 UTF-8、UTF-8 BOM、GBK、GB18030 等编码差异

## 依赖

- Python ≥ 3.8
- `model-router` skill（视觉任务路由，需用户先安装）
- 无外部 API 调用，仅本地文件操作

## 快速开始

```bash
cd skills/TMPI

# 交互模式（会先询问是否安装 model-router）
python scripts/tmpi.py --project .

# 已确认安装 model-router，跳过询问
python scripts/tmpi.py --project . --yes

# 强制使用 UTF-8 写入
python scripts/tmpi.py --project . --force-utf8

# 不创建备份
python scripts/tmpi.py --project . --no-backup
```

## 默认行为

- 已有 `CLAUDE.md` / `claude.md`：读取并更新，不覆盖原内容
- 没有 `CLAUDE.md`：创建 `CLAUDE.md`
- 已有 TMPI 规则：替换旧规则，不重复插入
- 已有文件：创建 `CLAUDE.md.tmpi.bak` 备份
- 编码：自动识别 UTF-8 / UTF-8 BOM / GB18030 / GBK / CP936，默认保留原编码；新文件使用 UTF-8

## 执行后检查

1. 读取 `CLAUDE.md` / `claude.md`，确认存在 `TMPI:BEGIN text-model-project-init` 标记
2. 向用户说明规则已写入哪个文件、使用了什么编码、是否创建了备份
3. 提醒用户后续图片任务只能传本地图片路径，不能直接传图片内容

## 注意

- TMPI 只能约束 Claude Code / 工具后续行为，不能修复已经进入会话历史的 image payload
- 已经报 `this model does not support image input` 时，需使用 `/rewind` 回到图片进入上下文之前，或 `/clear` 后重新开始
- 用户未安装 `model-router` 时不会强行写入规则，会提示先安装 `model-router` 再执行 TMPI