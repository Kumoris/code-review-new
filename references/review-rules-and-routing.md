# 检视规则与路由

本文档定义规则路径识别、标准维度和任务路由规则。主 Agent 使用 `prescan.json`、文件路径和扩展名路由；Prescan 结果优先于关键词推断。

## 规则文件映射

| 规则文件 | 适用语言/场景 | 触发条件 |
|----------|-------------|----------|
| `references/common.md` | 所有语言 | 始终加载 |
| `references/java.md` | Java | `.java` 文件 |
| `references/c-cpp.md` | C/C++ | `.c`, `.cpp`, `.cc`, `.cxx`, `.h`, `.hpp`, `.hxx` 文件 |
| `references/go.md` | Go | `.go` 文件 |
| `references/python.md` | Python | `.py`, `.pyi` 文件 |
| `references/js-ts.md` | JavaScript/TypeScript | `.js`, `.jsx`, `.ts`, `.tsx`, `.mjs` 文件 |
| `references/shell.md` | Shell | `.sh`, `.bash`, `.zsh` 文件 |
| `references/csharp.md` | C# | `.cs` 文件 |
| `references/rust.md` | Rust | `.rs` 文件 |
| `references/codeguard.md` | 安全规则 | prescan 安全信号或安全路径 fallback |
| `references/false-positive-avoidance.md` | 误报规避 | 始终加载 |
| `references/spark-rules.md` | Spark代码与数据管道 | `.py`/`.java`文件含`SparkSession`/`DataFrame`/`RDD`/`Dataset`，或变更文件含`*.dataset.yaml`/`*.pipeline.yaml`时加载 |
| `references/jsx-prop-detection.md` | JSX prop检测 | React/JSX 组件变更时加载 |
| `references/xml.md` | XML配置文件 | `.xml` 文件变更时加载 |
| `references/structured-files.md` | 结构化配置文件语法校验 | `.yaml`/`.yml`/`.json`/`.csv`/`.html`/`.htm` 文件变更时加载 |

## 安全关键字触发列表

当 Prescan 无法完成 Always-Check 时，以下关键词作为 fail-safe fallback 加载 `codeguard.md`：

- 认证: auth, login, password, token, certificate, credential, session, cookie, mfa
- 加密: crypto, encrypt, decrypt, cipher, key, ssl, tls, rsa, aes
- 注入: inject, sql, xss, csrf, command, exec, eval, format
- 数据: database, storage, query, select, insert, update, delete
- 文件: upload, download, file, path, directory
- 序列化: serialize, deserialize, xml, json, yaml, pickle
- 日志: log, audit, monitor, trace
- 隐私: privacy, pii, gdpr, personal, sensitive
- 供应链: dependency, package, import, require, npm, pip, maven
- 基础设施: dockerfile, kubernetes, k8s, helm, terraform, iac, container, ci, cd
- MCP: mcp, model context protocol

## 规则优先级

1. 仓库规则（`codespec/guidelines/**/*.md`，如可用）
2. 领域规则（SKILL.md、delta-spec.md 等）
3. 安全规则（codeguard.md）
4. 语言规则（`{language}.md`）
5. 通用规则（common.md）

当已加载规则直接适用时，问题必须引用该规则；没有适用规则时，`fatal`/`major`/`minor` 只能来自代码证据可证明的真实缺陷。

## 标准维度

| 维度 | 说明 | 自动触发条件 |
|------|------|-------------|
| `CODE_DESIGN` | 架构、API、代码结构、可读性、语言最佳实践 | 可执行代码变更（默认） |
| `BEHAVIOR` | 功能正确性、健壮性、异常处理、资源管理、性能、并发 | 可执行代码变更（默认） |
| `SECURITY` | 安全编码、敏感信息、依赖安全 | 涉及认证/鉴权/日志/敏感字段/序列化/依赖/外部输入 |
| `TEST` | 单元测试、可测试性、静态分析 | 涉及测试文件 |
| `BUILD_OPS` | 构建、部署、环境配置、兼容性 | 涉及构建脚本/部署/CI/Dockerfile/依赖声明 |
| `DOMAIN_RULES` | 内置领域规则 | SKILL.md、AGENTS.md、delta-spec.md 变更 |
| `ARCHITECTURE` | 架构边界、依赖方向、兼容性 | 可执行代码变更 |
| `BUSINESS` | 当前业务路径和数据流影响 | 有 workspace 或业务设计文档 |

## 任务路由规则

1. 若 `changed_files` 为空，不生成 manifest，不启动 Reviewer。
2. 可执行代码变更默认生成 `CODE_DESIGN` + `BEHAVIOR`。
3. 安全关键字命中时追加 `SECURITY`。
4. 测试文件命中时追加 `TEST`。
5. 构建/部署文件命中时追加 `BUILD_OPS`。
6. 领域规则命中时追加 `DOMAIN_RULES`。
7. 按语言+维度分组文件，最多 8 个任务；运行时最多 5 个 Reviewer 并发，超出时分批。
8. 一个文件可属于多个任务。
9. `ARCHITECTURE`/`BUSINESS` task 只加载 common、false-positive、rule-registry 和对应维度规则，不重复加载语言/安全规则。
10. `routed_files` 与 `unsupported_files` 必须不相交，且并集精确等于 `changed_files`；失败时记录 `scope-drift` 并停止发布。
11. Local `whole_repo` 中的 `changed_files` 表示已声明纳入基线审计的快照文件，不表示 Git 变更；按模块/语言合并成不超过 8 个 task，且每个文件仍须出现在精确 coverage 中。
