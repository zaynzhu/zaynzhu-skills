# 扫描 Checklist

这是 `project-onboard` Phase 1 的扫描清单。AI 逐项用 Glob/Grep/Read 查证，查到就填证据账本，查不到标 `未发现`。**不先识别技术栈**——所有语言的配置文件名都扫一遍，扫到啥算啥，这样多语言 monorepo 不会漏。

## 配置文件 Checklist

### Node / JS / TS

- `package.json` — 项目名、description、scripts（开发命令的核心来源）、main/bin（入口）、依赖、包管理器（看 lock 文件判断 npm/yarn/pnpm）
- `package-lock.json` / `yarn.lock` / `pnpm-lock.yaml` — 判断包管理器
- `tsconfig.json` / `jsconfig.json` — TS 配置、路径别名
- `.eslintrc.{js,cjs,json,yml}` / `eslint.config.{js,mjs}` — 代码约定
- `.prettierrc{,.json,.js,.yml}` / `prettier.config.{js,mjs}` — 格式约定
- `.editorconfig` — 缩进/换行约定（跨语言通用）
- `vite.config.{js,ts}` / `webpack.config.{js,ts}` / `next.config.{js,mjs,ts}` / `nuxt.config.{js,ts}` — 构建框架
- `jest.config.{js,ts,json}` / `vitest.config.{js,ts}` / `playwright.config.{js,ts}` — 测试框架
- `.env.example` / `.env.sample` — 环境变量清单
- `.nvmrc` / `.node-version` — Node 版本

### Python

- `pyproject.toml` — 现代 Python 项目元数据、依赖、scripts（[project.scripts]）、工具配置（ruff/black/mypy/pytest）
- `setup.py` / `setup.cfg` — 老式包元数据、entry_points
- `requirements.txt` / `requirements*.txt` — 依赖
- `Pipfile` / `Pipfile.lock` — pipenv
- `poetry.lock` — poetry
- `ruff.toml` / `.ruff.toml` — 代码约定
- `.flake8` / `setup.cfg[flake8]` — 代码约定
- `.pylintrc` / `pylintrc` — 代码约定
- `mypy.ini` / `.mypy.ini` / `pyproject.toml[mypy]` — 类型检查
- `pytest.ini` / `pyproject.toml[tool.pytest]` / `tox.ini` / `conftest.py` — 测试
- `manage.py` / `asgi.py` / `wsgi.py` — Django 入口
- `.python-version` / `runtime.txt` — Python 版本
- `environment.yml` / `conda.yml` — conda 环境

### Go

- `go.mod` — module 名、Go 版本、依赖
- `go.sum` — 依赖校验
- `Makefile` / `justfile` — 命令
- `.golangci.{yml,yaml}` — lint
- `main.go` — 入口

### Rust

- `Cargo.toml` — 包元数据、依赖、[[bin]] 入口
- `Cargo.lock` — 依赖
- `clippy.toml` / `.clippy.toml` — lint
- `rustfmt.toml` / `.rustfmt.toml` — 格式
- `src/main.rs` / `src/lib.rs` — 入口

### Java / Kotlin / JVM

- `pom.xml` — Maven 元数据、依赖、插件、build 命令
- `build.gradle` / `build.gradle.kts` — Gradle
- `settings.gradle{,.kts}` — Gradle 项目结构
- `gradlew` / `gradlew.bat` — Gradle wrapper（存在即用 `./gradlew`）
- `checkstyle.xml` / `.editorconfig` — 代码约定
- `mvnw` / `mvnw.cmd` — Maven wrapper

### Ruby

- `Gemfile` / `Gemfile.lock` — 依赖
- `Rakefile` — 命令
- `.rubocop.yml` — 代码约定
- `.rspec` — 测试
- `.ruby-version` — Ruby 版本

### C# / .NET

- `*.csproj` / `*.sln` — 项目结构
- `Directory.Build.props` — 构建配置
- `global.json` — SDK 版本

### 通用 / CI / 文档

- `README{,.md,.rst,.txt}` — 项目定位、描述
- `CONTRIBUTING{,.md}` — 贡献流程（提交规范线索）
- `LICENSE{,.md,.txt}` — 许可证
- `Makefile` / `justfile` / `Taskfile.{yml,yaml}` — 命令（跨语言通用）
- `docker-compose.{yml,yaml}` / `Dockerfile` — 部署/环境
- `.github/workflows/*.yml` — CI（构建/测试命令线索）
- `.gitlab-ci.yml` / `Jenkinsfile` / `.circleci/` — CI
- `.commitlintrc{,.js,.json}` / `commitlint.config.{js,ts}` / `.husky/` — 提交规范
- `.env.example` — 环境变量（任何语言都常见）

## 源码扫描方法论（门面文件策略）

### 第一步：骨架

Glob 拿排除后的目录树，限深 3 层。用 `Glob` 模式 `*`、`*/*`、`*/*/*`（在项目根依次扫），排除清单已写在 SKILL.md。不无限递归——超过 3 层的深目录靠门面文件覆盖即可。

### 第二步：门面文件

对每个含源码的目录，按优先级找门面文件。门面文件通常 re-export 或聚合模块公共接口，读它就懂目录职责，不用读实现。

| 优先级 | 文件 | 读取 |
|--------|------|------|
| 1 | `index.{ts,js,tsx,jsx}`、`__init__.py`、`mod.rs`、`lib.rs`、`main.go`、`main.{py,js,ts}`、barrel 文件 | 全文 |
| 2 | 目录名最能代表的文件（如 `user.controller.ts` 之于 `user/`，`parser.py` 之于 `parser/`） | 全文 |
| 3 | 无门面文件时 | 列文件名 + 最大文件前 50 行 |

判断"目录名最能代表的文件"：文件名包含目录名、或文件名是该目录下唯一的主文件、或文件名暗示核心职责（controller/service/model/handler/api/server/app 等关键词）。

### 第三步：入口深读 + 一层 import 链

从配置推断关键入口：
- Node：`package.json` 的 `main`/`bin`/`scripts.start` 指向的文件
- Python：`pyproject.toml` 的 `[project.scripts]`、`manage.py`、`app.py`、`main.py`
- Go：`main.go`（通常在根或 `cmd/`）
- Rust：`Cargo.toml` 的 `[[bin]]` 或 `src/main.rs`
- Java：`pom.xml` 的 `mainClass`、`@SpringBootApplication` 标注的类

关键入口**完整读**，顺 import/require/include 链**走一层**——读它直接引用的模块的门面文件。这理解"项目怎么启动、核心模块怎么连起来"。不追第二层，避免无限蔓延。

### 防爆护栏

- 目录树 glob 限深 3 层
- 门面文件读全文；非门面文件只读前 50 行
- 源码总读取软上限 **40 个文件**。超了按目录重要性截断（根目录 > 一级 > 二级），在证据账本标注"已截断，X 个目录未深读"
- 配置文件不计数（通常就二三十个，全读）

## 证据账本格式

Phase 1 Step 4 展示给用户的账本表格：

```markdown
## 证据账本

| 维度 | 证据来源 | 内容摘要 | 状态 |
|------|---------|---------|------|
| 项目定位 | README.md:1-10 | "XXX 是一个 YYY 工具" | ✅ |
| 技术栈 | package.json | Node 18 / TypeScript / React / pnpm | ✅ |
| 开发命令 | package.json:scripts | dev=`vite`、build=`tsc&&vite build`、test=`vitest` | ✅ |
| 测试 | vitest.config.ts | vitest，测试在 `test/` | ✅ |
| 代码约定 | .eslintrc.cjs, .prettierrc | 2空格/无分号/single quote | ✅ |
| 提交规范 | .commitlintrc.json | conventional commits (feat/fix/docs) | ✅ |
| 提交规范 | git log --oneline -20 | 参差，多数带前缀但不统一 | ⚠️弱 |
| 目录约定 | dist/, .next/ 存在 | 生成物，别碰 | ✅ |
| 环境变量 | .env.example | VITE_API_URL, DATABASE_URL | ✅ |
| 关键入口 | src/main.tsx | React 挂载入口 | ✅ |
| 目录结构 | Glob 限深3层 | src/{components,hooks,lib,routes}/ | ✅ |
| 代码约定 | .editorconfig | (未发现) | ❌未发现 |
```

状态取值：
- `✅` — 有明确证据
- `⚠️弱` — 证据参差（如 git log）
- `❌未发现` — 扫了但没扫到，保留 section 写"未发现"
- `—` — 该语言不适用（如 Python 项目不查 Cargo.toml）