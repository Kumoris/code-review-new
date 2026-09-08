# 检视规则索引

> 所有规则文件位于当前 Skill 的 `references/` 目录。

---

## 目录

- [文件清单](#文件清单)
- [按维度分类索引](#按维度分类索引)
  - [一、跨语言通用规则 (common.md)](#一跨语言通用规则-commonmd)
  - [二、CodeGuard安全规则 (codeguard.md)](#二codeguard安全规则-codeguardmd)
  - [三、误判规避规则 (false-positive-avoidance.md)](#三误判规避规则-false-positive-avoidancemd)
- [按语言索引](#按语言索引)
  - [Java规则分布](#java规则分布)
  - [C/C++规则分布](#cc规则分布)
  - [Go规则分布](#go规则分布)
  - [Python规则分布](#python规则分布)
  - [JS/TS规则分布](#jsts规则分布)
  - [Shell规则分布](#shell规则分布)
  - [C#规则分布](#c规则分布)
  - [Rust规则分布](#rust规则分布)
- [规则来源映射](#规则来源映射)

---

## 文件清单

| 文件 | 类型 | 规则数 | 来源 |
|------|------|--------|------|
| [common.md](common.md) | 跨语言通用规则 | 38条（9大类别） | 既有规则去重合并 |
| [java.md](java.md) | Java规则 | 66条 | 既有规则去重合并 |
| [c-cpp.md](c-cpp.md) | C/C++规则 | 56条（含Nginx专项） | 既有规则去重合并 |
| [go.md](go.md) | Go规则 | 44条 | 既有规则去重合并 |
| [python.md](python.md) | Python规则 | 53条 | 既有规则去重合并 |
| [js-ts.md](js-ts.md) | JS/TS规则 | 37条（含React/TS特有） | 既有规则去重合并 |
| [shell.md](shell.md) | Shell规则 | 21条 | 既有规则去重合并 |
| [csharp.md](csharp.md) | C#规则 | 26条 | 既有规则整理 |
| [rust.md](rust.md) | Rust规则 | 25条 | 既有规则整理 |
| [codeguard.md](codeguard.md) | CodeGuard安全规则 | 20条 | 安全规则整理 |
| [false-positive-avoidance.md](false-positive-avoidance.md) | 误判规避规则 | 28个场景 | 误判案例整理 |
| [xml.md](xml.md) | XML配置文件规则 | 5条（3语法+2错误码） | code-review-new 独占 |
| [structured-files.md](structured-files.md) | 结构化配置文件语法校验 | 15条（1通用+4YAML+4JSON+3CSV+3HTML） | code-review-new 独占 |
| [spark-rules.md](spark-rules.md) | Spark代码与数据管道规则 | 20条（5SQL+5DF+3UDF+3缓存+4管道） | code-review-new 独占 |
| [jsx-prop-detection.md](jsx-prop-detection.md) | JSX Prop检测规则 | 1条（JSTS-PROP-001） | code-review-new 独占 |
| [severity-guidelines.md](severity-guidelines.md) | 严重程度定级指南 | 4级别 | 既有规则去重合并 |
| [review-rules-and-routing.md](review-rules-and-routing.md) | 规则路由表 | 路由映射 | code-review-new 独占 |
| [prescan-rules.md](prescan-rules.md) | Prescan 信号契约 | 确定性信号 | code-review-new 独占 |
| [architecture-review.md](architecture-review.md) | 架构维度规则 | 3条 | code-review-new 独占 |
| [business-review.md](business-review.md) | 业务维度规则 | 3条 | code-review-new 独占 |
| [dispatch-contract.md](dispatch-contract.md) | Agent 派发契约 | 身份与回执 | code-review-new 独占 |
| [integrity-artifacts.md](integrity-artifacts.md) | 完整性契约 | 哈希与状态 | code-review-new 独占 |
| [rule-registry.md](rule-registry.md) | 规则状态注册表 | 发布门 | code-review-new 独占 |

---

## 按维度分类索引

### 一、跨语言通用规则 (common.md)

| 类别 | 规则编号 | 规则名称 |
|------|----------|----------|
| 审查策略 | — | 审查流程与原则 |
| 架构设计 | — | SOLID、模块化、设计模式、全局状态、循环导入、类型标注、硬编码配置、嵌套深度、函数复杂度、枚举扩展性检查、调用链影响分析 |
| 代码实现 | — | 编码规范、命名、文档、简洁性、异常处理、DRY |
| 性能与资源 | — | 字符串拼接、N+1查询、正则预编译、生成器、并发异步、缓存 |
| 安全编码 | — | SQL注入、命令注入、硬编码凭证、不安全反序列化、SSL/TLS、日志泄露、依赖审计 |
| 单元测试 | — | 测试技术栈、断言、Mock规范、参数化 |
| 构建部署 | — | 依赖管理、容器化、服务器配置 |
| 业务规则 | — | 外部参数校验、幂等性、事务一致性 |
| 严重级别 | — | Fatal/Critical/Major/Normal/Minor/Info判定指南 |

### 二、CodeGuard安全规则 (codeguard.md)

| 类别 | 规则编号 | 规则名称 |
|------|----------|----------|
| 加密安全 | CG-CRYPTO-001 | 密码学算法与后量子就绪 |
| 加密安全 | CG-CRYPTO-002 | 数字证书最佳实践 |
| 加密安全 | CG-CRYPTO-003 | 硬编码凭证禁止 |
| 加密安全 | CG-CRYPTO-004 | 附加密码学与TLS |
| 认证与MFA | CG-AUTH-001 | 认证与多因素认证 |
| 授权与访问控制 | CG-AUTHZ-001 | 授权与访问控制 |
| 输入验证与注入防御 | CG-INJECT-001 | 输入验证与注入防御 |
| 客户端Web安全 | CG-WEB-001 | 客户端Web安全 |
| 会话管理与Cookie | CG-SESS-001 | 会话管理与Cookie |
| 数据存储安全 | CG-DATA-001 | 数据库与存储安全 |
| 文件处理与上传 | CG-FILE-001 | 文件上传安全 |
| XML与序列化 | CG-XML-001 | XML与序列化加固 |
| 日志与监控 | CG-LOG-001 | 日志与监控 |
| 隐私与数据保护 | CG-PRIV-001 | 隐私与数据保护 |
| 供应链安全 | CG-SUPPLY-001 | 依赖与供应链安全 |
| DevOps与容器 | CG-DEVOPS-001 | DevOps、CI/CD与容器 |
| Kubernetes安全 | CG-K8S-001 | Kubernetes加固 |
| 基础设施即代码 | CG-IAC-001 | 基础设施即代码安全 |
| MCP安全 | CG-MCP-001 | MCP (Model Context Protocol) 安全 |
| 移动应用安全 | CG-MOBILE-001 | 移动应用安全 |
| 框架与语言指南 | CG-FRAMEWORK-001 | 框架与语言安全指南 |

### 三、误判规避规则 (false-positive-avoidance.md)

| 场景编号 | 场景名称 |
|----------|----------|
| 场景1 | Javadoc注释缺失误判 — diff显示不全 |
| 场景2 | import语句间空行规范过度使用 |
| 场景3 | 新增文件版权年份检查未生效 |
| 场景4 | 正面评价类意见无需提交 |
| 场景5 | 空值检查建议需结合数据库表结构判断 |
| 场景6 | "变量使用但未声明"误报 |
| 场景7 | C++命名规范误判 — 小驼峰 vs snake_case |
| 场景8 | IF_TRACE_METHOD_ERROR_CONTINUE_EX宏的跳过逻辑误判 |
| 场景9 | 方法内部实现 vs 调用处上下文混淆 |
| 场景10 | RestfulParametes参数传递方式误判 |
| 场景11 | 检视意见必须基于变更后的代码 |
| 场景12 | 空值检查建议需结合上下文判断 |
| 场景13 | "变量使用但未声明"意见必须双重验证 |
| 场景14 | 条件运算符变更需检查是否有逻辑拆分 |
| 场景15 | 一套代码交付多个产品时配置差异误判 |
| 场景16 | 方法签名变更需检查调用处是否同步修改 |
| 场景17 | 调用处参数检查必须基于diff变更结果 |
| 场景18 | 方法重命名必须验证diff中是否同步修改调用处 |
| 场景19 | 方法删除必须验证diff中是否同步删除调用处 |
| 场景20 | 工具类方法语义必须结合取反运算符和业务含义综合判断 |
| 场景21 | boolean类型参数的方法必须完整解析if-else分支逻辑 |
| 场景22 | 遍历数组/集合的通用方法必须验证是否支持新元素扩展 |
| 场景23 | 删除字段/变量后不能仅因方法名相似就臆测存在依赖 |
| 场景24 | 变量重新赋值后检查必须结合错误日志和上下文判断意图 |
| 场景25 | 循环内重复操作检测必须验证代码是否真正在循环内部 |
| 场景26 | JSX组件新增prop时必须检查是否遗漏原有prop绑定 |
| 场景27 | 新增枚举/常量值时条件判断同步更新检查 |
| 场景28 | 枚举/常量传递后的调用链影响误判规避 |

---

## 按语言索引

### Java规则分布
| 来源文件 | 规则类别 | 规则编号 |
|----------|----------|----------|
| java.md | 架构设计 | JAVA-ARCH-001~005 |
| java.md | 代码实现 | JAVA-CODE-001~015 |
| java.md | 最佳实践 | JAVA-BEST-001~004 |
| java.md | 性能与并发 | JAVA-PERF-001~010 |
| java.md | 安全 | JAVA-SEC-001~008 |
| java.md | 易错点 | JAVA-PITFALL-001~010 |
| java.md | 单元测试 | JAVA-TEST-001~010 |
| java.md | 构建部署 | JAVA-BUILD-001~003 |
| codeguard.md | 加密/认证/授权/注入/会话/XML/日志 | CG-CRYPTO-001~004, CG-AUTH-001, CG-AUTHZ-001, CG-INJECT-001, CG-SESS-001, CG-XML-001, CG-LOG-001, CG-FRAMEWORK-001 |
| codeguard.md | 移动应用(Java/Kotlin) | CG-MOBILE-001 |

### C/C++规则分布
| 来源文件 | 规则类别 | 规则编号 |
|----------|----------|----------|
| c-cpp.md | 代码风格 | CPP-STYLE-001~007 |
| c-cpp.md | 架构设计 | CPP-ARCH-001~008 |
| c-cpp.md | 健壮性 | CPP-ROBUST-001~004 |
| c-cpp.md | Nginx专项 | NGINX-001~003 |
| c-cpp.md | C++编码 | CPP-CODE-001~005 |
| c-cpp.md | C语言特有 | C-CODE-001~010 |
| c-cpp.md | 性能 | CPP-PERF-001~007 |
| c-cpp.md | 安全 | CPP-SEC-001~004 |
| c-cpp.md | 测试 | CPP-TEST-001~005 |
| c-cpp.md | 构建 | CPP-BUILD-001~003 |
| codeguard.md | 安全C函数 | CG-CRYPTO-004(含safe-c-functions), CG-INJECT-001, CG-XML-001 |

### Go规则分布
| 来源文件 | 规则类别 | 规则编号 |
|----------|----------|----------|
| go.md | 架构 | GO-ARCH-001~006 |
| go.md | 代码 | GO-CODE-001~010 |
| go.md | 最佳实践 | GO-BEST-001~003 |
| go.md | 性能与并发 | GO-PERF-001~011 |
| go.md | 安全 | GO-SEC-001~009 |
| go.md | 测试 | GO-TEST-001~004 |
| codeguard.md | 安全/加密 | CG-CRYPTO-004, CG-AUTH-001, CG-AUTHZ-001, CG-INJECT-001 |

### Python规则分布
| 来源文件 | 规则类别 | 规则编号 |
|----------|----------|----------|
| python.md | 架构 | PY-ARCH-001~009 |
| python.md | 代码实现 | PY-CODE-001~015 |
| python.md | 安全 | PY-SEC-001~009 |
| python.md | 性能 | PY-PERF-001~008 |
| python.md | 并发 | PY-CON-001~003 |
| python.md | 测试 | PY-TEST-001~006 |
| python.md | 构建 | PY-BUILD-001~003 |
| codeguard.md | 安全/加密 | CG-CRYPTO-004, CG-AUTH-001, CG-AUTHZ-001, CG-INJECT-001, CG-XML-001 |

### JS/TS规则分布
| 来源文件 | 规则类别 | 规则编号 |
|----------|----------|----------|
| js-ts.md | 代码风格 | JSTS-CODE-001~006 |
| js-ts.md | 架构 | JSTS-ARCH-001~006 |
| js-ts.md | 安全 | JSTS-SEC-001~008 |
| js-ts.md | 并发 | JSTS-CON-001~003 |
| js-ts.md | React/TS特有 | JSTS-REACT-001~009 |
| js-ts.md | 性能 | JSTS-PERF-001~005 |
| codeguard.md | 安全/加密 | CG-CRYPTO-004, CG-AUTH-001, CG-AUTHZ-001, CG-INJECT-001, CG-WEB-001, CG-SESS-001, CG-MCP-001 |

### Shell规则分布
| 来源文件 | 规则类别 | 规则编号 |
|----------|----------|----------|
| shell.md | 健壮性 | SH-ROBUST-001~005 |
| shell.md | 可移植性 | SH-PORT-001~002 |
| shell.md | 代码风格 | SH-STYLE-001~004 |
| shell.md | 安全 | SH-SEC-001~005 |
| shell.md | 性能 | SH-PERF-001~003 |
| shell.md | 测试 | SH-TEST-001~002 |
| codeguard.md | 注入防御 | CG-INJECT-001 |

### C#规则分布
| 来源文件 | 规则类别 | 规则编号 |
|----------|----------|----------|
| csharp.md | 安全 | CS-SEC-001~009 |
| csharp.md | 并发 | CS-CON-001~005 |
| csharp.md | 编码 | CS-CODE-001~006 |
| csharp.md | 性能 | CS-PERF-001~004 |
| csharp.md | 架构 | CS-ARCH-001~002 |
| codeguard.md | 安全/加密 | CG-CRYPTO-004, CG-AUTH-001, CG-AUTHZ-001, CG-INJECT-001, CG-XML-001, CG-SESS-001 |

### Rust规则分布
| 来源文件 | 规则类别 | 规则编号 |
|----------|----------|----------|
| rust.md | 安全 | RUST-SEC-001~006 |
| rust.md | 并发 | RUST-CON-001~005 |
| rust.md | 编码 | RUST-CODE-001~007 |
| rust.md | 性能 | RUST-PERF-001~005 |
| rust.md | 架构 | RUST-ARCH-001~002 |
| codeguard.md | 安全/加密 | CG-MCP-001 |

---

## 规则来源映射

| Skill | 语言规则 | 安全规则 | 误判规避 |
|-------|----------|----------|----------|
| **语言规则集** | Java, C/C++, Go, Python, Shell, TypeScript, Rust, C# | severity_guidelines | — |
| **安全与误判规则集** | — | CodeGuard 安全规则 | 误判规避场景 |
