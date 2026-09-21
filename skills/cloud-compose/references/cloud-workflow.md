# 云端工作流配方

依据项目生成 workflow，不提供声称支持所有技术栈的万能 YAML。来源项目的现有 action 版本只是历史实例；真正实现时核对项目已使用版本、组织策略和官方兼容说明，不宣称“最新版”。已有 CI 可以准确完成时直接复用。

## GitHub Actions 离线包主路径

1. 默认 `workflow_dispatch`；版本和目标平台输入限定可接受字符/枚举。只读源码权限 `contents: read`，上传 artifact 不要求发布镜像权限。若用户选 GHCR，仅相关发布 job 使用必需的 `packages: write`。
2. 明确受信任 ref 和 commit SHA，checkout 后检查源码；工作流执行版本与构建源码版本都要能追溯。设置 job 超时与 concurrency，避免取消中的任务被当作成功；不把含凭据发布放到不受信任 PR 或 `pull_request_target` 的代码执行路径。
3. 使用真实云端 runner。按架构能力设置 Buildx；跨架构才考虑 QEMU，原生云端 ARM runner 的可用性/额度先验证。项目需要 OS 特有镜像时不要硬塞进 Linux runner。
4. 用锁文件缓存构建层，缓存键区分服务/平台，私有依赖不要进入不受信任公共缓存。云端安装必要工具，不为了速度跳过锁文件校验或生产构建。
5. 静态配置校验后，构建每个服务并 `--load` 到当前云端 Docker。准备交付 Compose 指向的全部依赖镜像；检查 `docker image inspect` 的平台及身份。
6. 云端运行烟测；使用独立 Compose 项目名、临时配置和卷。记录关键请求/任务结果，失败 job 不能被 `continue-on-error` 或 shell 的忽略退出码包装成成功。
7. `docker save` 导出本次服务和必要依赖；保存 manifest 和部署文件，计算校验。使用单一压缩包携带文件或明确提示脚本执行权限恢复，不依赖 artifact 下载后可执行位还在。
8. 上传 artifact，保留期按项目要求设置并报告。验证 job 在干净 runner 下载同一包、验校验和、load，以 `--pull never --no-build` 运行包里的 Compose；要证明完全离线，还需阻断运行时联网并测关键路径。
9. `always()` 清理仅限本次隔离资源；保存脱敏诊断，不上传真实配置或整库数据。

## 云端命令骨架（不是直接可运行脚本）

以下变量必须由项目实现赋值和校验，仅在云端 runner 执行：

```bash
docker compose --env-file "$testEnv" -f "$composeFile" config --quiet
docker buildx build --platform "$platform" --target "$target" --tag "$imageTag" --load "$buildContext"
docker image inspect "$imageTag"
docker save --output "$archivePath" "$imageTag"
```

多服务必须导出全部实际镜像名；不要照抄最后一行只保存一个镜像。校验和基于包内相对路径，解压到任何目录都能验证。不得将这些命令拿到本机试跑。

## 镜像仓库替代路径

用户选择或离线包超过产物限制时，核实仓库可见性、目标机网络和登录方式后再使用。推送带 commit/版本的镜像并记录 digest；部署 Compose 固定 digest 或不可变版本，附拉取、配置、启动说明。不要为方便直接把私有镜像改成公开。用户仍要求 tar 时，可在云端从已验证 digest 拉取并导出，不能让目标机承担构建。

## 操作工具

已有专用 API/connector 优先；否则 GitHub CLI、Git 或用户已配置的 CI CLI。调用前检查工具与权限状态，不读取或输出 token 文件。手动触发、等待、下载分别记录状态；只看任务名称不足以选 run，要匹配 ref、SHA、触发时间/运行 ID，不能下载另一版本的成功产物。

没有 CLI 时可生成文件并提供 Actions 网页操作步骤。任务依赖真实网页状态才使用已授权浏览器工具；不能用搜索结果推断私有仓库任务状态。
