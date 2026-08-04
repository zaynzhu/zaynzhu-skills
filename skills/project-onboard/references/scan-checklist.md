# 扫描 Checklist

用于 Phase 1 的只读取证。先发现仓库实际使用的生态，再加载相关配置；不要把所有语言的文件逐项读一遍。

## 目录

- 仓库级发现
- 生态配置清单
- 安全读取规则
- 源码扫描方法
- 排除与截断
- 证据账本

## 仓库级发现

### 1. 规则与协作文档

发现但不要自动改动：

- 根目录和嵌套的 `AGENTS.md`、`CLAUDE.md`
- `.cursorrules`、`.windsurfrules`、`.coderc`、`.aider*`
- `.github/copilot-instructions.md`
- `README*`、`CONTRIBUTING*`

根目录两份规则文件是输出目标。嵌套规则只用于理解作用域，除非用户另行授权，否则不要修改。

### 2. Manifest 与 workspace

先列出仓库内 manifest 和 workspace 文件，据此决定读取哪些生态配置：

- Node：`package.json`、`pnpm-workspace.yaml`、`turbo.json`、`nx.json`、`lerna.json`
- Python：`pyproject.toml`、`setup.py`、`setup.cfg`
- Go：`go.mod`、`go.work`
- Rust：`Cargo.toml`
- JVM：`pom.xml`、`settings.gradle`、`settings.gradle.kts`
- .NET：`*.sln`、`*.csproj`
- Ruby：`Gemfile`
- PHP：`composer.json`
- Swift：`Package.swift`、`*.xcodeproj`、`*.xcworkspace`
- Dart / Flutter：`pubspec.yaml`
- Elixir：`mix.exs`
- C / C++：`CMakeLists.txt`、`meson.build`

发现多个 manifest 时识别 monorepo/workspace 边界，不只分析仓库根目录。

### 3. 通用工程配置

- 命令：`Makefile`、`justfile`、`Taskfile.yml`、`Taskfile.yaml`
- 容器：`Dockerfile*`、`compose.yml`、`compose.yaml`、`docker-compose.yml`、`docker-compose.yaml`
- CI：`.github/workflows/*.yml`、`.github/workflows/*.yaml`、`.gitlab-ci.yml`、`Jenkinsfile`、`.circleci/`
- 编辑器：`.editorconfig`
- 提交：`.commitlintrc*`、`commitlint.config.*`、`.husky/`
- 环境变量示例：`.env.example`、`.env.sample`、`.env.template`

## 生态配置清单

只读取已发现生态对应的小节。

### Node / JavaScript / TypeScript

- `package.json`：项目描述、scripts、engines、packageManager、main/bin、workspaces
- `package-lock.json`、`yarn.lock`、`pnpm-lock.yaml`、`bun.lock`、`bun.lockb`：包管理器和依赖锁
- `tsconfig*.json`、`jsconfig.json`：语言配置和路径别名
- `eslint.config.*`、`.eslintrc*`、`.prettierrc*`、`prettier.config.*`：代码约定
- `vite.config.*`、`webpack.config.*`、`next.config.*`、`nuxt.config.*`：构建入口
- `jest.config.*`、`vitest.config.*`、`playwright.config.*`：测试
- `.nvmrc`、`.node-version`：运行时版本
- `deno.json`、`deno.jsonc`：Deno 项目

### Python

- `pyproject.toml`：元数据、依赖、scripts、ruff/black/mypy/pytest 配置
- `setup.py`、`setup.cfg`：老式元数据和 entry points
- `requirements*.txt`、`Pipfile*`、`poetry.lock`、`uv.lock`：依赖管理
- `ruff.toml`、`.ruff.toml`、`.flake8`、`.pylintrc`、`mypy.ini`、`.mypy.ini`：代码约定
- `pytest.ini`、`tox.ini`、`conftest.py`：测试
- `manage.py`、`asgi.py`、`wsgi.py`、`app.py`、`main.py`：入口线索
- `.python-version`、`runtime.txt`：运行时版本

### Go

- `go.mod`、`go.work`：module、workspace、Go 版本
- `.golangci.yml`、`.golangci.yaml`：lint
- 根目录或 `cmd/` 下的 `main.go`：入口

### Rust

- `Cargo.toml`：package、workspace、依赖、bin
- `Cargo.lock`：依赖锁
- `clippy.toml`、`.clippy.toml`、`rustfmt.toml`：代码约定
- `src/main.rs`、`src/lib.rs`：入口

### Java / Kotlin / JVM

- `pom.xml`、`mvnw*`：Maven module、插件和命令
- `build.gradle*`、`settings.gradle*`、`gradlew*`：Gradle module 和 wrapper
- `checkstyle.xml`、`.editorconfig`：代码约定
- `@SpringBootApplication`、`mainClass`：入口线索

### 其他生态

- Ruby：`Gemfile*`、`Rakefile`、`.rubocop.yml`、`.rspec`
- .NET：`*.sln`、`*.csproj`、`Directory.Build.props`、`global.json`
- PHP：`composer.json`、`composer.lock`、`phpunit.xml*`
- Swift：`Package.swift`、Xcode project/workspace、`.swiftlint.yml`
- Dart / Flutter：`pubspec.yaml`、`analysis_options.yaml`
- Elixir：`mix.exs`、`mix.lock`、`.formatter.exs`
- C / C++：`CMakeLists.txt`、`meson.build`、`Makefile`、`.clang-format`

## 安全读取规则

### 允许读取

- manifest、lockfile、CI、lint、format、test 和公开示例配置
- `.env.example`、`.env.sample`、`.env.template` 中的变量名和注释
- 配置文件里的 `${ENV_NAME}`、键路径和非敏感结构
- `git status --short`、`git log --oneline -20`

### 禁止读取或展示

- 真实 `.env`、`.env.local`、`.env.production` 等运行配置
- `*.pem`、`*.key`、`*.p12`、`id_rsa*`、认证缓存、cookie、keychain
- 原始 token、密码、连接串、私钥、证书正文
- `git remote` URL

不要整段输出可能包含值的配置文件。优先使用只返回变量名、键名或 `${ENV_NAME}` 引用的搜索；不可避免看到疑似秘密值时，不复制到证据账本或回复，只写“键名（已脱敏）”。

## 源码扫描方法

### 第一步：骨架与 workspace

1. 获取排除生成物后的全仓文件清单。
2. 识别 workspace/package 根。
3. 相对仓库根和各 workspace 根展示限深 3 层的关键目录，不照搬完整 tree。

深度限制只用于展示，不用于 manifest 和入口发现。

### 第二步：门面文件

对关键源码目录按顺序选择：

| 优先级 | 文件 | 读取方式 |
|--------|------|----------|
| 1 | `index.*`、`__init__.py`、`mod.rs`、`lib.rs`、`main.*`、barrel 文件 | 全文 |
| 2 | 与目录同名或职责明确的 controller/service/model/handler/api/server/app 文件 | 全文 |
| 3 | 无门面文件 | 文件名清单 + 最大文件前 50 行 |

不要假定所有目录都有门面文件；目录职责必须由文件名、导出或调用关系支持。

### 第三步：入口与一层调用链

从 manifest、scripts 和框架配置识别关键入口。完整读取入口，只跟随它直接引用的一层模块；不继续追第二层。

### 第四步：代码风格抽样

只有缺少 lint/format 配置时才抽样现有源码。把结果记为“弱证据”，使用“现有代码多数……”之类描述，不生成强制规范。

## 排除与截断

### 始终排除

- `.git/`
- 明确缓存目录，如 `__pycache__/`、`.cache/`、`coverage/`
- manifest 已确认的依赖目录，如 Node 的 `node_modules/`
- manifest 已确认的构建产物，如 Next.js 的 `.next/`、Rust/Maven 的 `target/`

### 不得全局排除

`bin/`、`env/`、`target/`、`vendor/`、`dist/`、`build/` 可能是正式源码或手写资产。只有配置、忽略规则或生态约定明确证明它们是生成物/第三方目录时才排除。

源码读取软上限为 40 个文件，配置文件不计数。超过上限时按入口、workspace 根、一级模块、二级模块的顺序保留，并在账本记录截断范围。

## 证据账本

按工程维度汇总，不为每个未使用语言生成一行：

```markdown
| 维度 | 证据来源 | 摘要 | 可信度 | 冲突 |
|------|----------|------|--------|------|
| 技术栈 | package.json:engines、pnpm-lock.yaml | Node 20 / TypeScript / pnpm | 强事实 | 无 |
| 开发命令 | package.json:scripts | dev、build、test | 强事实 | 无 |
| 包管理器 | AGENTS.md、package-lock.json | 规则要求 pnpm，但存在 npm lockfile | 冲突 | 待确认 |
| 提交规范 | git log --oneline -20 | 多数使用 feat/fix 前缀 | 弱证据 | 无 |
| 环境变量 | .env.example | DATABASE_URL、API_BASE_URL | 强事实 | 值未读取 |
```

只展示：

- 已发现且会影响规则的证据
- 影响执行的关键缺失项，如没有测试命令
- 需要用户裁决的冲突
- 扫描截断或未覆盖范围

缺失信息留在交付报告，不写入受管规则区块。
