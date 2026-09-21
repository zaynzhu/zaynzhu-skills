# cloud-compose — 云端 Docker / Compose 交付

## 解决什么问题

让 AI agent 把一个已有项目变成可追溯、可导入、可启动的容器交付物，默认走 **GitHub Actions → 单架构镜像 tar → Compose 离线部署包**，目标机器只负责导入和运行，**本机零 Docker 依赖**。

用户说"给项目打 Docker""打个 Compose""GitHub 云端打包""不装本地 Docker 部署到 NAS"时使用；不用于仅解释 Docker 概念、一般 CI 修改或原生应用安装包构建。

## 功能一览

| 交付物 | 内容 | 生成位置 |
|---|---|---|
| Dockerfile / .dockerignore | 锁文件安装、多阶段构建、最小 COPY | 目标项目内 |
| 部署用 compose.yaml | 只引用 `image:`，不含 `build:` / 源码挂载 | 目标项目内 |
| 配置示例 | compose.env.example、app.env.example，权限 0600 | 目标项目内 |
| 云端 workflow | GitHub Actions，默认手动触发、单一目标架构 | `.github/workflows/` |
| 离线部署包 | `<project>-<version>-<platform>/`：images.tar、SHA256SUMS、compose.yaml、示例、manifest.json、README.md | 云端 artifact |

## 默认路径：严格云端

- 本地仅允许：读写文件、Git 操作、调用远端工具（CLI / API）、下载产物
- 依赖安装、编译、Docker 构建、Compose 校验、烟测全部在**云端 runner** 执行
- 不探测、不安装、不启动本地 Docker，也不使用本地 VM / self-hosted runner 绕过
- 只有用户在当前任务**明确说**"用本地 Docker / 本地环境构建"才启用本地路径；"本地有 Docker""随便怎么做""云端失败"都不算授权

## 执行顺序（SKILL.md 五节）

1. **侦察**：读目标项目 AGENTS.md / CLAUDE.md，按技术栈适配表确定最小方案（[`references/project-adaptation.md`](../skills/cloud-compose/references/project-adaptation.md)）
2. **生成交付文件**：Dockerfile、compose.yaml、配置示例、workflow（[`references/cloud-workflow.md`](../skills/cloud-compose/references/cloud-workflow.md)）
3. **云端构建与验证**：`docker compose config --quiet` → buildx `--load` + `docker save` → 干净 job 离线导入烟测
4. **收集产物**：含 SHA256SUMS、manifest.json、commit、run 链接、各镜像架构与 image ID
5. **遇阻推进**：每次给出"原因 → 已尝试 → 首选解法 → 备选解法 → 需要用户做的一步"（[`references/fallbacks.md`](../skills/cloud-compose/references/fallbacks.md)）

## 交付状态等级

| 状态 | 可声称的结果 |
|---|---|
| 已生成 | 文件完成，尚无云端运行证据 |
| 已构建 | 镜像产物已生成，运行验收不完整 |
| 已验证 | 云端构建 + 离线导入 / 仓库拉取 + 声明范围的运行验收全通过 |
| 受阻 / 部分完成 | 指明失败步骤、证据、可用文件、替代方案 |

报告必须按以上等级如实交付，不编造 run URL、镜像 digest 或验证日志。

## 禁区

- 不用生产数据库、生产凭据，不复制用户 `.env` 进 CI 或产物
- 不因为"首次手动触发不可用"擅自合并到默认分支
- 不用 `docker export` 冒充镜像、不把"解析通过"当"运行通过"
- 未授权不上传源码到新服务、不改仓库可见性、不发公开镜像、不开付费资源

## 参考与回归用例

- 原方案可复用点与失效假设：[`references/origin-project-notes.md`](../skills/cloud-compose/references/origin-project-notes.md)
- 不同工具环境下的执行方式：[`ENVIRONMENTS.md`](../skills/cloud-compose/ENVIRONMENTS.md)
- 行为评测（不代表实际镜像已构建）：[`evals/evals.json`](../skills/cloud-compose/evals/evals.json)
