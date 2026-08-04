# Section 写作模板

`project-onboard` 生成的 `CLAUDE.md` / `AGENTS.md` 严格按 11 个固定 section 顺序写。每节从证据账本提炼，不许凭空编。下面是每节的模板、示例和"未发现"写法。

## 1. 项目定位

**写什么**：一句话这个项目是干嘛的。

```markdown
## 项目定位

{{一句话}}。{{可选：核心能力或适用场景的一句补充}}
```

示例：
```markdown
## 项目定位

VibeCalc 是一个本地优先的命令行计算器，支持单位换算和变量定义。适合需要快速计算又不想开浏览器的人。
```

未发现：
```markdown
## 项目定位

未发现 README 或包描述。请补充一句话项目定位。
```

证据来源：`README.md` 首段、`package.json` 的 `description`、`pyproject.toml` 的 `description`。

## 2. 技术栈

**写什么**：语言、框架、运行时、包管理器，列表式。

```markdown
## 技术栈

- 语言：{{}}
- 框架：{{}}
- 运行时：{{版本}}
- 包管理器：{{}}
```

示例：
```markdown
## 技术栈

- 语言：TypeScript 5.3
- 框架：React 18 + Vite 5
- 运行时：Node 18（见 .nvmrc）
- 包管理器：pnpm 8（见 pnpm-lock.yaml）
```

证据来源：`package.json`、`pyproject.toml`、`go.mod`、`Cargo.toml`、`*.csproj`、lock 文件判断包管理器、`.nvmrc`/`.python-version` 判断运行时版本。

## 3. 目录结构

**写什么**：关键目录职责，不照搬整棵 tree，只标注有意义的目录。

```markdown
## 目录结构

- `{{dir}}/` — {{职责}}
- `{{dir}}/` — {{职责}}
```

示例：
```markdown
## 目录结构

- `src/components/` — React 组件
- `src/hooks/` — 自定义 hook
- `src/lib/` — 工具函数
- `src/routes/` — 路由页面
- `test/` — 测试用例
```

职责从门面文件提炼。未发现（空项目）：写"项目几乎无源码，目录结构暂不适用"。

## 4. 开发命令

**写什么**：确切命令 + 各自作用。从 `package.json` scripts / Makefile / pyproject `[project.scripts]` 提取，不许编。

```markdown
## 开发命令

- \`{{cmd}}\` — {{作用}}
```

示例：
```markdown
## 开发命令

- `pnpm dev` — 启动开发服务器（Vite）
- `pnpm build` — 类型检查 + 生产构建
- `pnpm lint` — ESLint 检查
- `pnpm format` — Prettier 格式化
```

未发现（无 scripts/Makefile）：写"未发现声明式命令。直接 {{怎么跑}}（如 `python main.py` / `go run .`）。"

## 5. 测试

**写什么**：怎么跑、测试在哪、框架。

```markdown
## 测试

- 框架：{{}}
- 命令：`{{}}`
- 测试目录：`{{}}`
```

示例：
```markdown
## 测试

- 框架：Vitest
- 命令：`pnpm test`（watch 模式 `pnpm test -- --watch`）
- 测试目录：`test/` 和 `src/**/*.test.ts`
```

未发现：写"未发现测试配置。请确认是否有测试。"

## 6. 代码约定

**写什么**：缩进、分号、命名、语言规则。从 lint/prettier/editorconfig 提取。

```markdown
## 代码约定

- 缩进：{{N 空格}}
- 分号：{{用/不用}}
- 引号：{{single/double}}
- 命名：{{camelCase/snake_case/...}}
- {{语言特定规则}}
```

示例：
```markdown
## 代码约定

- 缩进：2 空格（见 .editorconfig）
- 分号：不用（见 .prettierrc）
- 引号：single
- 命名：变量 camelCase，常量 UPPER_SNAKE_CASE，类型 PascalCase
- React 组件用函数式 + hooks，不用 class
```

未发现（无 lint 配置）：写"未发现 lint/格式化配置。建议参考现有代码风格。"

## 7. 提交规范

**写什么**：commit 风格 + 是否有 commitlint。commitlint 是强证据，git log 是弱证据。

```markdown
## 提交规范

- 格式：{{}}
- {{有/无}} commitlint 强制校验
```

示例（有 commitlint）：
```markdown
## 提交规范

- 格式：Conventional Commits（`feat: ...` / `fix: ...` / `docs: ...`）
- 有 commitlint + husky 强制校验（见 .commitlintrc.json）
```

示例（仅 git log 弱推断）：
```markdown
## 提交规范

- 现有 commit 多数带 `feat:`/`fix:` 前缀但不统一（git log 观察，仅供参考）
- 无 commitlint 强制校验
```

未发现：写"未发现提交规范配置。"

## 8. 目录约定

**写什么**：生成物/第三方目录明示"别碰"。

```markdown
## 目录约定

以下为生成物或第三方，**不要手动改**：
- `{{dir}}/` — {{生成物/第三方}}
```

示例：
```markdown
## 目录约定

以下为生成物或第三方，**不要手动改**：
- `dist/` — 构建产物
- `node_modules/` — 第三方依赖
- `vendor/` — vendored 第三方代码
```

未发现（无明显生成物目录）：写"未发现典型生成物目录。"

## 9. 环境变量

**写什么**：必需 env 清单，或项目依赖的外部服务/配置项。从 `.env.example`、`application.yml`、`config.toml` 等配置文件提取——不只看 `.env`，Java Spring 等项目用 profile 配置文件管配置。

**不要附加凭据安全提示**：只客观列"依赖哪些服务/变量名"，不写"不要把凭据提交到外部仓库"之类的主观警告。凭据是否该进仓库是项目自己的事，skill 不替它下判断——很多公司内部仓库本来就允许存凭据，写死的安全提示反而是噪音。

```markdown
## 环境变量

- \`{{NAME}}\` — {{作用}}
```

示例：
```markdown
## 环境变量

- `VITE_API_URL` — 后端 API 地址
- `DATABASE_URL` — 数据库连接串
```

未发现：写"未发现 `.env.example`。如需环境变量请补充示例文件。"

## 10. 关键入口

**写什么**：入口文件 + 职责。

```markdown
## 关键入口

- `{{file}}` — {{职责}}
```

示例：
```markdown
## 关键入口

- `src/main.tsx` — React 挂载入口，渲染 App 到 #root
- `src/App.tsx` — 根组件，定义路由结构
- `src/lib/api.ts` — API 客户端，所有后端调用入口
```

未发现：写"未发现明确入口。请补充。"

## 11. 给 agent 的工作指引

**核心差异点**——这是 init 粗版没有的。一段话告诉 agent 在这个项目干活前先看啥、改完怎么自测、怎么提交。综合前面所有 section 提炼。

```markdown
## 给 agent 的工作指引

开工前先读 `{{入口}}` 理解项目结构。改完代码跑 `{{测试命令}}` 自测，`{{lint}}` 检查风格。提交用 `{{commit 格式}}` 格式。{{项目特定注意事项}}
```

示例：
```markdown
## 给 agent 的工作指引

开工前先读 `src/main.tsx` 和 `src/App.tsx` 理解项目结构和路由。改完代码跑 `pnpm test` 自测，`pnpm lint` 检查风格。提交用 `feat: ...` / `fix: ...` 等 Conventional Commits 格式（有 commitlint 校验）。新增组件放 `src/components/`，新增 hook 放 `src/hooks/`，别动 `dist/` 和 `node_modules/`。
```

未发现（信息不全时仍要写，但标注缺失）：
```markdown
## 给 agent 的工作指引

开工前先读 {{已知入口或"主要源码目录"}}。改完代码 {{已知测试命令或"未发现测试命令，请确认"}}。提交 {{已知格式或"未发现规范"}}。{{其他已知注意事项}}
```

## 文件末尾

两份文件末尾都加同步提示：

```markdown

---

<!-- 本文件与 CLAUDE.md / AGENTS.md 保持同步，修改任一份请同步另一份 -->
```