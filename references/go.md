# Go 检视规则

> 来源：既有检视规则去重合并；规则与代码托管平台无关

---

## 目录

- [一、架构设计与代码结构](#一架构设计与代码结构)
  - [GO-ARCH-001 ~ GO-ARCH-006](#go-arch-001-包设计)
- [二、代码实现与可读性](#二代码实现与可读性)
  - [GO-CODE-001 ~ GO-CODE-010](#go-code-001-代码格式化)
- [三、Go语言最佳实践](#三go语言最佳实践)
  - [GO-BEST-001 ~ GO-BEST-003](#go-best-001-错误处理)
- [四、性能、并发与资源管理](#四性能并发与资源管理)
  - [GO-PERF-001 ~ GO-PERF-006](#go-perf-001-禁止在循环中拼接字符串)
  - [GO-CON-001 ~ GO-CON-006](#go-con-001-禁止并发读写原生map)
- [五、安全编码](#五安全编码)
  - [GO-SEC-001 ~ GO-SEC-009](#go-sec-001-禁止sql拼接注入)
- [六、单元测试与可测试性](#六单元测试与可测试性)
  - [GO-TEST-001 ~ GO-TEST-004](#go-test-001-表驱动测试)

---

## 一、架构设计与代码结构

### GO-ARCH-001: 包设计

- 单一职责：包的职责是否单一且明确？包内的代码是否内聚性强？
- 循环依赖：是否存在包之间的循环依赖？
- **触发条件**: 包内存在多个不相关职责的代码，或包之间存在A→B→A的循环import
- **严重程度**: major

### GO-ARCH-002: 接口设计

- 接口隔离原则 (ISP)：接口是否小而精？记住"接受接口，返回结构体"的原则。
- 接口位置：接口是否定义在"消费者"一侧，而非"生产者"一侧？
- 接口命名：接口名是否以"er"结尾（如 `Reader`, `Writer`）？
- **触发条件**: 接口包含过多方法（>3个）、接口定义在生产者包中、或接口命名不符合"er"后缀惯例
- **严重程度**: minor

### GO-ARCH-003: 依赖注入

- 代码是否依赖于具体的实现（struct）而非抽象（interface）？是否便于通过构造函数或工厂函数注入依赖？
- **触发条件**: 函数或结构体直接依赖具体结构体而非接口，且无法通过构造函数替换依赖
- **严重程度**: minor

### GO-ARCH-004: 分层与职责

- 各层（如 handler, service, repository）的职责是否清晰？是否存在逻辑泄露？
- **触发条件**: handler层直接操作数据库、service层包含HTTP请求解析、或repository层包含业务逻辑
- **严重程度**: minor

### GO-ARCH-005: 必须使用接口解耦依赖

- **检查锚点**: 函数参数为具体结构体, 直接依赖数据库结构体
- **反例**: `func Process(db *sql.DB)`
- **正例**: `func Process(db DataAccessor)` — 接口参数
- **触发条件**: 函数参数为具体结构体（如*sql.DB、*http.Client）而非接口类型
- **严重程度**: major

### GO-ARCH-006: 禁止循环依赖包

- **检查锚点**: import A→B→A
- **正例**: 提取公共接口到独立包，依赖方向单向
- **触发条件**: 包A导入包B且包B导入包A，形成循环依赖链
- **严重程度**: major

---

## 二、代码实现与可读性

### GO-CODE-001: 代码格式化

- 代码是否使用 `gofmt` 或 `goimports` 进行了格式化？
- **触发条件**: 代码缩进不一致、import未分组排序、或存在gofmt/goimports会修改的格式问题
- **严重程度**: minor

### GO-CODE-002: 命名规范

- 命名是否简洁且表意清晰？是否遵循Go的 `camelCase` 或 `PascalCase` 规范？对导出的标识符是否有必要的godoc注释？
- **触发条件**: 变量/函数使用snake_case命名、导出标识符缺少godoc注释、或命名含糊不清（如data、tmp、info）
- **严重程度**: minor

### GO-CODE-003: 注释质量

- 注释是解释了"Why"而不仅仅是"What"？
- **触发条件**: 注释仅重复代码逻辑（如// increment i++）、或导出函数/类型缺少注释
- **严重程度**: minor

### GO-CODE-004: 代码简洁性

- 是否遵循"卫语句"或"提前返回"原则，减少 `if-else` 嵌套？
- 是否存在"魔法值"？应提炼为常量（`const`），并善用 `iota`。
- 函数是否过长？一个函数应该只做一件事。
- **触发条件**: if-else嵌套超过3层、代码中出现硬编码的魔法数字/字符串、或函数超过50行
- **严重程度**: minor

### GO-CODE-005: 必须处理所有error返回值

- **检查锚点**: `_ =`, `if err != nil`缺失, 忽略error赋值
- **反例**: `f, _ := os.Open(path)`
- **正例**: `f, err := os.Open(path); if err != nil { return err }`
- **触发条件**: 使用`_ =`丢弃error返回值，或调用返回error的函数未检查err
- **严重程度**: major

### GO-CODE-006: 必须使用%w包装错误保留上下文

- **检查锚点**: fmt.Errorf("...%v", err), errors.New丢失原始err
- **反例**: `fmt.Errorf("failed to open: %v", err)` — 丢失链
- **正例**: `fmt.Errorf("failed to open: %w", err)` — 保留链可Unwrap
- **触发条件**: fmt.Errorf中使用%v或%s格式化error而非%w，或errors.New丢失原始err上下文
- **严重程度**: major

### GO-CODE-007: 禁止type assertion不加ok检查

- **反例**: `str := v.(string)` — 若v非string则panic
- **正例**: `str, ok := v.(string); if !ok { ... }`
- **触发条件**: 使用`v.(Type)`形式的type assertion而未使用`v, ok :=.(Type)`的comma-ok模式
- **严重程度**: major

### GO-CODE-008: 禁止空select语句永久阻塞

- **反例**: `select {}` — 永久阻塞goroutine
- **触发条件**: 代码中出现`select {}`空select语句
- **严重程度**: major

### GO-CODE-009: 禁止滥用全局变量

- **检查锚点**: var在包级别声明mutable状态, 全局map, 全局slice
- **正例**: 使用结构体封装状态，通过方法访问
- **触发条件**: 包级别var声明可变状态（如map、slice、指针），且无并发保护
- **严重程度**: major

### GO-CODE-010: 禁止使用init()做复杂逻辑

- **检查锚点**: func init()中网络调用、文件操作、panic
- **正例**: init()仅用于简单注册，复杂逻辑放显式初始化函数
- **触发条件**: init()函数中包含网络请求、文件I/O、数据库连接、或可能panic的操作
- **严重程度**: major

---

## 三、Go语言最佳实践

### GO-BEST-001: 错误处理

- **显式处理**：是否检查了所有可能返回 `error` 的函数调用？严禁使用 `_` 丢弃错误。
- **错误判断**：是否使用 `errors.Is()` 来判断哨兵错误，`errors.As()` 检查特定错误类型？
- **Panic 的使用**：是否滥用 `panic`？应该只用于表示程序无法恢复的致命错误。
- **触发条件**: 使用`_`丢弃error、用`==`比较error而非errors.Is、或在非致命场景使用panic
- **严重程度**: major

### GO-BEST-002: 结构体与接口

- **接收器类型**：值接收器和指针接收器的使用是否恰当？修改对象状态时应使用指针接收器。
- **零值可用性**：结构体的零值是否有意义且可用？
- **构造函数**：是否提供了 `New...` 形式的构造函数来初始化复杂的结构体？
- **触发条件**: 需要修改状态的方法使用值接收器、结构体零值不可用且无构造函数、或同一结构体混用值/指针接收器
- **严重程度**: minor

### GO-BEST-003: 切片与映射

- **预分配容量**：在已知元素数量的情况下，是否使用 `make([]T, len, cap)` 或 `make(map[T]V, size)` 来预分配容量？
- **返回副本**：当返回一个 slice 给调用者时，是否考虑返回其副本以防止外部修改？
- **触发条件**: 已知元素数量但未使用make预分配、或返回内部slice引用导致外部可修改内部状态
- **严重程度**: minor

---

## 四、性能、并发与资源管理

### GO-PERF-001: 禁止在循环中拼接字符串

- **反例**: `for _, s := range items { result += s }`
- **正例**: `var b strings.Builder; for _, s := range items { b.WriteString(s) }`
- **触发条件**: 在for/range循环中使用`+=`拼接字符串
- **严重程度**: major

### GO-PERF-002: 必须预分配slice容量

- **反例**: `var items []int; for i := 0; i < n; i++ { items = append(items, i) }`
- **正例**: `items := make([]int, 0, n); for i := 0; i < n; i++ { items = append(items, i) }`
- **触发条件**: 声明空slice后在循环中append且已知最终元素数量，但未使用make预分配容量
- **严重程度**: minor

### GO-PERF-003: 禁止在热路径中反复编译正则

- **反例**: `func match(s string) { re := regexp.MustCompile("\\d+"); ... }`
- **正例**: `var re = regexp.MustCompile("\\d+"); func match(s string) { re.MatchString(s) }`
- **触发条件**: 在函数内部或循环体内调用regexp.MustCompile/regexp.Compile
- **严重程度**: major

### GO-PERF-004: 禁止N+1数据库查询

- **反例**: `for _, id := range ids { db.Query("SELECT ... WHERE id=$1", id) }`
- **正例**: `db.Query("SELECT ... WHERE id = ANY($1)", ids)` — 批量查询
- **触发条件**: 在循环中执行数据库查询，每次迭代使用不同参数查询单条记录
- **严重程度**: major

### GO-PERF-005: 必须对高频I/O使用bufio缓冲

- **反例**: `conn.Write([]byte("a")); conn.Write([]byte("b"))` — 多次系统调用
- **正例**: `w := bufio.NewWriter(conn); w.WriteString("a"); w.Flush()`
- **触发条件**: 对net.Conn或os.File等I/O对象在循环或热路径中频繁调用Write/Read小数据，未使用bufio包装
- **严重程度**: major

### GO-PERF-006: 内存分配与GC

- **减少堆分配**：是否存在不必要的堆内存分配？应优先在栈上分配。
- **对象复用**：对于高频创建和销毁的对象，是否考虑使用 `sync.Pool` 来减轻GC压力？
- **触发条件**: 热路径中频繁new/make创建短生命周期对象且未使用sync.Pool复用，或返回指针导致逃逸到堆
- **严重程度**: minor

### GO-CON-001: 禁止并发读写原生map

- **反例**: `go func() { m[key] = val }()` — 同时另一goroutine读m
- **正例**: `sync.RWMutex` 保护 或 `sync.Map`
- **触发条件**: 多个goroutine并发访问同一个原生map，且至少一个为写操作，无互斥保护
- **严重程度**: fatal

### GO-CON-002: 必须使用sync.WaitGroup或errgroup等待goroutine完成

- **反例**: `go doWork()` — 不等待完成
- **正例**: `wg.Add(1); go func() { defer wg.Done(); doWork() }(); wg.Wait()`
- **触发条件**: 启动goroutine后未使用WaitGroup/errgroup等待其完成，函数即返回
- **严重程度**: major

### GO-CON-003: 必须使用context控制goroutine生命周期

- **反例**: `go func() { for { doWork() } }()` — 无法停止
- **正例**: `go func(ctx context.Context) { for { select { case <-ctx.Done(): return; default: doWork() } } }(ctx)`
- **触发条件**: 启动长时间运行的goroutine未传入context，且无机制响应取消信号
- **严重程度**: major

### GO-CON-004: 禁止goroutine泄漏

- **反例**: `go func() { ch <- val }()` — 无人消费ch则泄漏
- **正例**: 使用 `select case <-ctx.Done()` 退出
- **触发条件**: goroutine阻塞在channel发送/接收且无select+ctx.Done()退出路径，或goroutine永不退出
- **严重程度**: major

### GO-CON-005: 必须使用defer关闭资源

- **反例**: `f, _ := os.Open(path)` — 无 `defer f.Close()`
- **正例**: `f, err := os.Open(path); if err != nil { ... }; defer f.Close()`
- **触发条件**: 打开文件/数据库连接/HTTP响应体等资源后未使用defer Close()确保释放
- **严重程度**: major

### GO-CON-006: Context最佳实践

- **作为首个参数**：`context.Context` 是否总是作为函数的**第一个参数**，并命名为 `ctx`？
- **禁止存入结构体**：Context 不应被存储在结构体的字段中。
- **取消信号处理**：对于长时间运行的操作，是否在 `select` 中检查了 `<-ctx.Done()`？
- **谨慎使用WithValue**：只用于传递请求范围的元数据，绝不应用于传递函数的可选参数。
- **禁止传递nil**：如果不确定，应传递 `context.TODO()`。
- **触发条件**: context.Context未作为函数首个参数、context存入结构体字段、context.WithValue传递业务参数、或传递nil context
- **严重程度**: minor

---

## 五、安全编码

### GO-SEC-001: 禁止SQL拼接注入

- **反例**: `db.Query(fmt.Sprintf("SELECT * FROM users WHERE id=%s", userID))`
- **正例**: `db.Query("SELECT * FROM users WHERE id=$1", userID)`
- **触发条件**: 使用fmt.Sprintf/string拼接构造SQL语句并传入db.Query/Exec
- **严重程度**: fatal

### GO-SEC-002: 禁止os/exec注入未校验输入

- **反例**: `exec.Command("sh", "-c", userInput)`
- **正例**: `exec.Command("tool", validatedArg)` — 参数分离
- **触发条件**: exec.Command使用"sh -c"执行用户输入、或将未校验的字符串拼入命令参数
- **严重程度**: fatal

### GO-SEC-003: 禁止硬编码密钥和凭证

- **检查锚点**: password=, secret=, apiKey=, token=
- **触发条件**: 源码中出现硬编码的密码、API密钥、Token等凭证字符串（如password=、secret=、apiKey=）
- **严重程度**: fatal

### GO-SEC-004: 禁止使用不安全随机数生成器

- **反例**: `token := fmt.Sprintf("%d", rand.Int())`
- **正例**: `crypto/rand`, `crypto/rand.Read`
- **触发条件**: 使用math/rand生成Token/密钥/会话ID等安全敏感随机值
- **严重程度**: major

### GO-SEC-005: 必须对用户输入做校验

- **反例**: `template.HTML(userInput)` — XSS
- **正例**: 使用 text/template 自动转义
- **触发条件**: 使用template.HTML直接标记用户输入为安全HTML、或未对用户输入进行校验/转义即输出到响应
- **严重程度**: major

### GO-SEC-006: 禁止跳过TLS证书验证

- **反例**: `&tls.Config{InsecureSkipVerify: true}`
- **触发条件**: tls.Config中设置InsecureSkipVerify: true
- **严重程度**: major

### GO-SEC-007: 必须使用安全密码哈希

- **反例**: `md5.Sum([]byte(password))`
- **正例**: `bcrypt.GenerateFromPassword()` 或 `argon2.IDKey()`
- **触发条件**: 使用md5/sha1等弱哈希算法处理密码，而非bcrypt/argon2/scrypt等专用密码哈希
- **严重程度**: major

### GO-SEC-008: 必须防范SSRF

- **反例**: `http.Get(userProvidedURL)`
- **正例**: 校验URL scheme为https、host在白名单内
- **触发条件**: 使用用户提供的URL直接发起HTTP请求，未校验scheme和host白名单
- **严重程度**: major

### GO-SEC-009: unsafe包

- 代码中是否使用了 `unsafe` 包？它的使用必须有极其充分的理由。
- **触发条件**: 代码中import或使用了unsafe包的函数（如unsafe.Pointer、unsafe.Sizeof）
- **严重程度**: major

---

## 六、单元测试与可测试性

### GO-TEST-001: 表驱动测试

- 对于有多个测试用例的函数，是否使用了表驱动的方式，并结合 `t.Run()` 创建子测试？
- **触发条件**: 测试函数中重复多次if/switch测试不同输入输出，而非使用[]struct{name, input, expected}表+t.Run()
- **严重程度**: minor

### GO-TEST-002: 测试覆盖率

- 测试是否覆盖了核心逻辑、边界条件和错误路径？
- **触发条件**: 核心业务函数缺少测试、测试仅覆盖happy path而未测试错误分支和边界条件
- **严重程度**: minor

### GO-TEST-003: 测试替身

- 是否正确使用了Mock、Stub等测试替身来隔离外部依赖？
- **触发条件**: 单元测试直接调用真实数据库/外部服务、或未使用接口替身隔离外部依赖
- **严重程度**: minor

### GO-TEST-004: Go测试生态

- **基准测试**：对于性能关键代码，是否编写了 Benchmark 函数？
- **并发测试**：是否使用了 `-race` 标志来检测数据竞争？
- **避免 time.Sleep**：应使用 channel, `sync.WaitGroup` 等同步原语。
- **触发条件**: 性能关键代码缺少Benchmark、测试中使用time.Sleep做同步而非channel/WaitGroup、或未使用-race检测并发
- **严重程度**: suggestion
