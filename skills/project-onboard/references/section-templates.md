# Section 写作模板

生成高信号共享规则区块。以下 11 个 section 是推荐顺序，不是必须保留的空骨架；没有可靠证据时省略，并在交付报告列出缺失项。

## 目录

- 受管区块外壳
- 项目定位
- 技术栈
- 目录结构
- 开发命令
- 测试
- 代码约定
- 提交规范
- 目录约定
- 环境变量
- 关键入口
- 给 agent 的工作指引
- 交付报告

## 受管区块外壳

```markdown
<!-- project-onboard:begin -->
<!-- 此区块由 project-onboard 维护；区块外可保留平台专属规则 -->

{{已验证的 section}}

<!-- project-onboard:end -->
```

新建文件时可在受管区块前写：

```markdown
# 项目工程规则
```

不要在受管区块中加入“与另一份文件保持整份同步”的提示；只同步受管区块。

## 1. 项目定位

依据 README 首段或 manifest description，用一到两句说明项目用途。来源互相冲突时省略并报告。

```markdown
## 项目定位

VibeCalc 是一个本地优先的命令行计算器，支持单位换算和变量定义。
```

## 2. 技术栈

只列 manifest、lockfile 或运行时版本文件能证明的项目。

```markdown
## 技术栈

- 语言：TypeScript
- 框架：React 18 + Vite 5
- 运行时：Node 20（见 `.nvmrc`）
- 包管理器：pnpm（见 `pnpm-lock.yaml`）
```

版本没有证据时不猜版本；某个字段不适用时直接省略。

## 3. 目录结构

只列关键目录和由门面文件、入口或 manifest 支持的职责。

```markdown
## 目录结构

- `src/components/` — React 组件
- `src/hooks/` — 自定义 hook
- `src/routes/` — 路由页面
- `test/` — 测试用例
```

monorepo 先按 workspace 分组。不要照搬整棵 tree。

## 4. 开发命令

只列 manifest scripts、Makefile、Taskfile、CI 等声明的确切命令，不根据生态常识补写。

```markdown
## 开发命令

- `pnpm dev` — 启动开发服务器
- `pnpm build` — 执行生产构建
- `pnpm lint` — 执行静态检查
```

不要在规则文件中声称这些命令已经验证；统一在交付报告注明“本次只读取配置，未实际执行项目命令”。

## 5. 测试

至少有测试命令、测试配置或测试目录证据之一时才生成。

```markdown
## 测试

- 框架：Vitest
- 命令：`pnpm test`
- 测试位置：`test/`、`src/**/*.test.ts`
```

某个字段未知时省略该字段，不写占位符。

## 6. 代码约定

优先使用 lint、format、editorconfig 等强事实。

```markdown
## 代码约定

- 缩进：2 空格（见 `.editorconfig`）
- 分号：不用（见 `.prettierrc`）
- 引号：single
```

没有配置时可以抽样源码，但必须写成观察性描述，例如“现有 TypeScript 文件多数使用无分号风格”，不要升级成强制规则。命名和框架习惯只有明确配置或现有规则支持时才写。

## 7. 提交规范

commitlint、贡献文档或用户确认属于明确证据。

```markdown
## 提交规范

- 使用 Conventional Commits：`feat: ...`、`fix: ...`、`docs: ...`
- commitlint 和 husky 会校验提交信息
```

仅从 git log 观察到风格时，写成“历史提交多数……，未发现强制配置”，不要要求 agent 必须遵循。

## 8. 目录约定

只有配置、忽略规则或生态 manifest 能证明目录是生成物/第三方时才写“不要手动修改”。

```markdown
## 目录约定

以下目录为生成物或第三方内容，不要手动修改：

- `.next/` — Next.js 构建产物
- `node_modules/` — pnpm 安装的第三方依赖
```

不要把 `bin/`、`env/`、`target/`、`vendor/`、`dist/`、`build/` 一概视为生成物。

## 9. 环境变量

只列变量名和用途，不复制任何值。

```markdown
## 环境变量

- `VITE_API_URL` — 后端 API 地址
- `DATABASE_URL` — 数据库连接配置
```

来源可以是安全示例文件、`${ENV_NAME}` 引用或用户确认。不要读取真实 `.env`，也不要在生成文件中附加与项目无关的通用凭据说教。

## 10. 关键入口

列出 manifest、scripts、框架配置或调用关系能证明的入口。

```markdown
## 关键入口

- `src/main.tsx` — React 挂载入口
- `src/App.tsx` — 根组件和路由结构
- `src/lib/api.ts` — API 客户端入口
```

## 11. 给 agent 的工作指引

只组合前面已经确认的可执行信息，不重复整份文档。

```markdown
## 给 agent 的工作指引

开工前先读 `src/main.tsx` 和 `src/App.tsx` 理解入口与路由。改完代码运行 `pnpm test` 和 `pnpm lint`。新增组件放在 `src/components/`，不要手动修改 `.next/`。
```

测试、lint、提交格式或入口缺失时，删掉对应句子；不要写“请确认”“未发现”或模板占位。

## 交付报告

缺失信息和验证边界放在回复中，不写进受管区块：

```markdown
本次更新：

- 已写入：项目定位、技术栈、目录、开发命令、关键入口
- 未发现：测试命令、强制提交规范
- 待确认冲突：现有规则要求 pnpm，但仓库存在 package-lock.json
- 验证边界：只读取配置，未执行测试、构建或安装命令
- 自审：受管区块一致、脱敏检查通过、第二次生成无 diff
```
