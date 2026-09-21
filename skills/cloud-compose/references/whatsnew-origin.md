# WhatsNew 来源与抽象

本技能参考 2026-09-21 工作区中的 WhatsNew：

- `.github/workflows/build-nas-images.yml`：手动触发，云端 Linux runner，Compose 校验，Buildx 构建，artifact 交付。
- `Dockerfile`：共享构建阶段，Node 后端与 nginx 前端两个运行 target。
- `deploy/nas/build-image-tar.sh`：按单平台构建/加载两个镜像，`docker save` 打为一包，SHA256 校验。
- `compose.yaml` 与 `deploy/nas/README.md`：镜像和配置分离，NAS 导入运行，数据持久化及升级说明。

技能运行时不依赖该仓库或上述绝对路径；此文件仅记录设计来源。

可复用的是云端构建、匹配版本的镜像与 Compose、离线导入、配置分离及校验链路。不能照搬的是固定 `linux/amd64`、两个服务、端口、Node 版本、Prisma/MySQL、NAS 特定目录、外部数据库和特定分支。

原工作流体现了打包模式，不构成所有项目运行成功的证据。本技能额外要求干净云端 runner 从交付包导入运行，区分镜像离线与业务完全离线，并明确不支持容器化的项目和云端受阻时的替代路径。

## 已读取的修复证据

| WhatsNew commit | 实际修复 | 通用规则 |
|---|---|---|
| `6fb3bb6` | 校验文件改为在输出目录内计算文件名 | 包须在不同解压目录仍能验证 |
| `e2bb31a` | 验证最终 Compose 前创建临时 env_file | 解析所需文件不应从生产环境复制 |
| `66225a7` | 设置目录与配置文件补充权限处理 | 原子写入还依赖父目录权限 |
| `fc9b049` | 干净构建补装 OpenSSL | 干净环境验证生成代码与系统依赖 |

当前 `deploy/nas/README.md` 进一步明确了 env_file 修改后的容器重建、挂载目录 UID/GID、外部数据库和唯一调度器切换。上述 commit 是历史证据；现行配置已经精简为两个容器，不应复活历史权限初始化容器来套用所有项目。
