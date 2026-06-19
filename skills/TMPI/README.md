# TMPI（Text Model Project Init）

TMPI 是一个 Claude Code skill，用来初始化“文本主模型项目”的 `CLAUDE.md` 规则，避免截图、图片、验证码、图表、UI 自动化截图等视觉内容被直接发送给不支持图片输入的主模型。

## 使用方式

进入当前项目根目录后运行：

```bash
python <TMPI技能目录>/scripts/tmpi.py --project .
```

如果已经确认安装了 model-router skill，可以跳过询问：

```bash
python <TMPI技能目录>/scripts/tmpi.py --project . --yes
```

默认行为：

- 已有 `CLAUDE.md` / `claude.md`：读取并更新，不覆盖原内容
- 没有 `CLAUDE.md`：创建 `CLAUDE.md`
- 已有 TMPI 规则：替换旧规则，不重复插入
- 已有文件：创建 `CLAUDE.md.tmpi.bak` 备份
- 编码：自动识别 UTF-8 / UTF-8 BOM / GB18030 / GBK / CP936，默认保留原编码
- 新文件：使用 UTF-8

## 参数

```bash
python scripts/tmpi.py --project .
python scripts/tmpi.py --project . --yes
python scripts/tmpi.py --project . --force-utf8
python scripts/tmpi.py --project . --no-backup
```

## 注意

TMPI 只能约束 Claude Code / 工具后续行为，不能修复已经进入会话历史的 image payload。已经报 `this model does not support image input` 时，需要使用 `/rewind` 回到图片进入上下文之前，或者 `/clear` 后重新开始。
