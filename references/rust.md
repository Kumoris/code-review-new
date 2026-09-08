# Rust 检视规则

> 来源：mr-reviewer 独占（其他skill无Rust规则）

---

## 目录

- [一、安全编码](#一安全编码)
  - [RUST-SEC-001: 禁止unsafe块缺少安全论证注释](#rust-sec-001-禁止unsafe块缺少安全论证注释)
  - [RUST-SEC-002: 禁止Command注入用户输入](#rust-sec-002-禁止command注入用户输入)
  - [RUST-SEC-003: 禁止硬编码密钥和凭证](#rust-sec-003-禁止硬编码密钥和凭证)
  - [RUST-SEC-004: 必须禁止整数溢出或显式处理](#rust-sec-004-必须禁止整数溢出或显式处理)
  - [RUST-SEC-005: 禁止跳过TLS证书验证](#rust-sec-005-禁止跳过tls证书验证)
  - [RUST-SEC-006: 必须防范TOCTOU竞态](#rust-sec-006-必须防范toctou竞态)
- [二、并发安全](#二并发安全)
  - [RUST-CON-001: 禁止Send/Sync违规](#rust-con-001-禁止sendsync违规)
  - [RUST-CON-002: 禁止Rc跨线程使用](#rust-con-002-禁止rc跨线程使用)
  - [RUST-CON-003: 必须使用Mutex/RwLock保护共享可变状态](#rust-con-003-必须使用mutexrwlock保护共享可变状态)
  - [RUST-CON-004: 禁止死锁（锁顺序不一致）](#rust-con-004-禁止死锁锁顺序不一致)
  - [RUST-CON-005: 必须正确使用原子操作的内存序](#rust-con-005-必须正确使用原子操作的内存序)
- [三、编码规范](#三编码规范)
  - [RUST-CODE-001: 禁止unwrap/expect在可能失败场景](#rust-code-001-禁止unwrapexpect在可能失败场景)
  - [RUST-CODE-002: 禁止在库代码中panic](#rust-code-002-禁止在库代码中panic)
  - [RUST-CODE-003: 必须使用?运算符传播错误](#rust-code-003-必须使用运算符传播错误)
  - [RUST-CODE-004: 禁止不必要的clone](#rust-code-004-禁止不必要的clone)
  - [RUST-CODE-005: 必须处理Result的所有变体](#rust-code-005-必须处理result的所有变体)
  - [RUST-CODE-006: 必须保证match穷尽性](#rust-code-006-必须保证match穷尽性)
  - [RUST-CODE-007: 禁止RefCell运行时借用冲突](#rust-code-007-禁止refcell运行时借用冲突)
- [四、性能优化](#四性能优化)
  - [RUST-PERF-001: 禁止不必要的堆分配](#rust-perf-001-禁止不必要的堆分配)
  - [RUST-PERF-002: 必须预分配Vec/String容量](#rust-perf-002-必须预分配vecstring容量)
  - [RUST-PERF-003: 禁止在热路径中反复编译正则](#rust-perf-003-禁止在热路径中反复编译正则)
  - [RUST-PERF-004: 禁止N+1数据库查询](#rust-perf-004-禁止n1数据库查询)
  - [RUST-PERF-005: 必须选择正确的智能指针](#rust-perf-005-必须选择正确的智能指针)
- [五、架构设计](#五架构设计)
  - [RUST-ARCH-001: 禁止库类型暴露具体错误实现](#rust-arch-001-禁止库类型暴露具体错误实现)
  - [RUST-ARCH-002: 必须使用trait做抽象而非具体类型](#rust-arch-002-必须使用trait做抽象而非具体类型)

---

## 一、安全编码

### RUST-SEC-001: 禁止unsafe块缺少安全论证注释

- **检查锚点**: unsafe {, unsafe fn, unsafe impl, 无SAFETY注释
- **反例**: `unsafe { ptr::copy(src, dst, len) }` — 无安全说明
- **正例**: 先写 `// SAFETY: src和dst有效且不重叠, len不超过分配大小` 再写unsafe块
- **触发条件**: 代码中出现 `unsafe {}`、`unsafe fn` 或 `unsafe impl` 块，且该块上方或内部无 `// SAFETY:` 注释
- **严重程度**: major

### RUST-SEC-002: 禁止Command注入用户输入

- **反例**: `Command::new("sh").arg("-c").arg(user_input)`
- **正例**: `Command::new("tool").arg(validated_arg)` — 参数分离
- **触发条件**: `Command::new()` 调用中通过 `.arg("-c")` / `.arg("/C")` 等方式将用户输入拼接到shell命令中
- **严重程度**: fatal

### RUST-SEC-003: 禁止硬编码密钥和凭证

- **检查锚点**: password=, secret=, apiKey=, token=, const赋值敏感字符串
- **触发条件**: 代码中出现 `const` 或 `static` 赋值含密码、密钥、token等敏感字符串的字面量（如 `const PASSWORD: &str = "xxx"` 或 `secret= "xxx"`）
- **严重程度**: fatal

### RUST-SEC-004: 必须禁止整数溢出或显式处理

- **反例**: `let size = len as usize` — 可能截断
- **正例**: `let size = usize::try_from(len).map_err(|_| "overflow")?`
- **触发条件**: 使用 `as` 进行整数类型转换（如 `as usize`、`as i32`）且未做溢出检查，或算术运算未使用 `checked_*` / `saturating_*` / `wrapping_*` 方法
- **严重程度**: major

### RUST-SEC-005: 禁止跳过TLS证书验证

- **反例**: `ClientBuilder::new().danger_accept_invalid_certs(true)`
- **触发条件**: 调用 `danger_accept_invalid_certs(true)`、`accept_invalid_hostnames(true)` 或类似跳过TLS证书校验的配置
- **严重程度**: fatal

### RUST-SEC-006: 必须防范TOCTOU竞态

- **反例**: `if path.exists() { fs::open(path) }` — TOCTOU
- **正例**: `fs::OpenOptions::new().write(true).create_new(true).open(path)` — 原子操作
- **触发条件**: 先检查文件/目录状态（`path.exists()`、`fs::metadata()`）再执行操作（`fs::open()`、`fs::create_dir()`），检查与操作之间存在时间窗口
- **严重程度**: major

---

## 二、并发安全

### RUST-CON-001: 禁止Send/Sync违规

- **反例**: `unsafe impl Send for MyStruct {}` — 无安全论证
- **正例**: 使用 Arc<Mutex<T>> 或 Arc<T>(T: Send+Sync)
- **触发条件**: 存在 `unsafe impl Send for ...` 或 `unsafe impl Sync for ...` 且缺少 `// SAFETY:` 安全论证注释
- **严重程度**: major

### RUST-CON-002: 禁止Rc跨线程使用

- **反例**: `thread::spawn(move || rc_cell.borrow())` — Rc非Send
- **正例**: 使用 `Arc<Mutex<T>>` 或 `Arc<T>`
- **触发条件**: 在 `thread::spawn` 闭包或 `std::thread` 相关调用中捕获或使用 `Rc<T>` 类型
- **严重程度**: major

### RUST-CON-003: 必须使用Mutex/RwLock保护共享可变状态

- **反例**: `static mut COUNTER: i32 = 0;` — 多线程不安全
- **正例**: `static COUNTER: AtomicI32 = AtomicI32::new(0);` 或 `Mutex`
- **触发条件**: 存在 `static mut` 全局可变变量且代码中存在多线程访问，或共享可变数据未被 `Mutex`/`RwLock`/`Atomic*` 保护
- **严重程度**: major

### RUST-CON-004: 禁止死锁（锁顺序不一致）

- **检查锚点**: 多个Mutex同时持有, 嵌套lock()
- **正例**: 统一锁获取顺序，或使用单一粗粒度锁
- **触发条件**: 同一作用域或调用链中先后对两个及以上 `Mutex`/`RwLock` 调用 `.lock()` / `.read()` / `.write()`
- **严重程度**: major

### RUST-CON-005: 必须正确使用原子操作的内存序

- **反例**: `flag.store(true, Ordering::Relaxed)` — 用于同步时Relaxed不够
- **正例**: `flag.store(true, Ordering::Release)` 配合 `Acquire` 读取
- **触发条件**: 原子操作（`store`/`load`/`compare_exchange`）使用 `Ordering::Relaxed` 且该原子变量用于线程间同步语义（如标志位通知、引用计数发布）
- **严重程度**: major

---

## 三、编码规范

### RUST-CODE-001: 禁止unwrap/expect在可能失败场景

- **反例**: `file.read_to_end(&mut buf).unwrap()` — 可能失败
- **正例**: `file.read_to_end(&mut buf)?` 或 `match`/`if let` 处理
- **触发条件**: 在可能返回 `Err`/`None` 的表达式上调用 `.unwrap()` 或 `.expect()`（如IO操作、解析操作、索引访问等非确定性场景）
- **严重程度**: major

### RUST-CODE-002: 禁止在库代码中panic

- **反例**: `panic!("unexpected value")` — 库代码中
- **正例**: `return Err(MyError::UnexpectedValue)` — 返回Result
- **触发条件**: 在库（lib crate）代码中使用 `panic!()`、`todo!()` 或 `unimplemented!()` 宏
- **严重程度**: major

### RUST-CODE-003: 必须使用?运算符传播错误

- **反例**: `match result { Ok(v) => v, Err(e) => return Err(e) }`
- **正例**: `let v = result?;`
- **触发条件**: 使用 `match` 手动解包 `Result` 且 `Err` 分支仅做 `return Err(e)` 转发，可被 `?` 运算符替代
- **严重程度**: minor

### RUST-CODE-004: 禁止不必要的clone

- **反例**: `fn process(data: &Vec<u8>) { inner(data.clone()) }` — 内层可接受&
- **正例**: `fn process(data: &Vec<u8>) { inner(data) }` — 传递引用
- **触发条件**: 对已有引用的数据调用 `.clone()`，而下游函数签名实际接受引用类型（&T）
- **严重程度**: minor

### RUST-CODE-005: 必须处理Result的所有变体

- **反例**: `if let Ok(val) = risky_op() { use(val) }` — Err被忽略
- **正例**: `match risky_op() { Ok(val) => use(val), Err(e) => handle(e) }`
- **触发条件**: 使用 `if let Ok(val) = ...` 或 `if let Some(val) = ...` 处理 `Result`/`Option`，但未处理 `Err`/`None` 分支
- **严重程度**: major

### RUST-CODE-006: 必须保证match穷尽性

- **反例**: `match opt { Some(v) => v }` — 缺None
- **正例**: `match opt { Some(v) => v, None => default }`
- **触发条件**: `match` 表达式未覆盖枚举的所有变体，且未使用 `_` 通配符或 `#[non_exhaustive]` 考量
- **严重程度**: minor

### RUST-CODE-007: 禁止RefCell运行时借用冲突

- **反例**: `let r = cell.borrow(); cell.borrow_mut();` — panic
- **正例**: 设计上避免运行时可变借用，或使用 `try_borrow_mut`
- **触发条件**: 在已有 `borrow()` 活跃借用期间调用 `borrow_mut()`，或在已有 `borrow_mut()` 活跃借用期间调用 `borrow()`
- **严重程度**: major

---

## 四、性能优化

### RUST-PERF-001: 禁止不必要的堆分配

- **反例**: `fn name() -> String { "hello".to_string() }` — 每次分配
- **正例**: `fn name() -> &'static str { "hello" }` — 零分配
- **触发条件**: 函数返回 `String`/`Vec`/`Box` 等堆分配类型，但实际可返回 `&'static str`/`&[T]`/栈上值等零分配替代
- **严重程度**: minor

### RUST-PERF-002: 必须预分配Vec/String容量

- **反例**: `let mut v = Vec::new(); for i in 0..1000 { v.push(i) }`
- **正例**: `let mut v = Vec::with_capacity(1000); for i in 0..1000 { v.push(i) }`
- **触发条件**: 使用 `Vec::new()` 或 `String::new()` 创建容器后紧跟循环 `push` 操作，且可预知元素数量但未调用 `with_capacity()`
- **严重程度**: minor

### RUST-PERF-003: 禁止在热路径中反复编译正则

- **反例**: `fn is_match(s: &str) { Regex::new(r"\d+").unwrap().is_match(s) }`
- **正例**: `static RE: Lazy<Regex> = Lazy::new(|| Regex::new(r"\d+").unwrap());`
- **触发条件**: 在函数体或循环内每次调用 `Regex::new()` 编译正则表达式，而非使用 `lazy_static!` / `Lazy` / `OnceLock` 缓存
- **严重程度**: major

### RUST-PERF-004: 禁止N+1数据库查询

- **反例**: 循环中 `sqlx::query("... WHERE id=$1").bind(id).fetch_one(&pool)`
- **正例**: `sqlx::query("... WHERE id = ANY($1)").bind(ids).fetch_all(&pool)`
- **触发条件**: 在循环体内执行数据库查询（如 `for id in ids { query(...).bind(id).fetch_one() }`），每次迭代单独查询而非批量查询
- **严重程度**: major

### RUST-PERF-005: 必须选择正确的智能指针

- **反例**: 单线程用 `Arc<Mutex<T>>` — Arc原子开销无意义
- **正例**: 单线程用 `Rc<RefCell<T>>`，跨线程用 `Arc<Mutex<T>>`
- **触发条件**: 在单线程场景使用 `Arc<Mutex<T>>` 或 `Arc<T>`（无跨线程共享需求），或在多线程场景误用 `Rc<RefCell<T>>`
- **严重程度**: minor

---

## 五、架构设计

### RUST-ARCH-001: 禁止库类型暴露具体错误实现

- **正例**: 库定义 `enum Error { ... }` 实现 std::error::Error，应用层可用 anyhow
- **触发条件**: 库（lib crate）的公共API返回 `anyhow::Error` 或暴露第三方具体错误类型（如 `io::Error`），而非自定义错误枚举
- **严重程度**: major

### RUST-ARCH-002: 必须使用trait做抽象而非具体类型

- **反例**: `fn save(repo: PostgresRepo)`
- **正例**: `fn save(repo: &dyn Repository)` 或 `fn save<R: Repository>(repo: &R)`
- **触发条件**: 函数参数使用具体类型（如 `PostgresRepo`、`FileWriter`）而非trait对象（`&dyn Trait`）或泛型约束（`<T: Trait>`），导致无法替换实现
- **严重程度**: minor
