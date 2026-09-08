# C/C++ 检视规则

> 来源：既有检视规则去重合并；规则与代码托管平台无关

---

## 目录

- [一、代码风格、可读性与自文档化](#一代码风格可读性与自文档化)
  - [CPP-CODE-001: 命名](#cpp-code-001-命名)
  - [CPP-CODE-002: 格式与整洁度](#cpp-code-002-格式与整洁度)
  - [CPP-CODE-003: 头文件管理](#cpp-code-003-头文件管理)
  - [CPP-CODE-004: 注释](#cpp-code-004-注释)
  - [CPP-CODE-005: 表达清晰度](#cpp-code-005-表达清晰度)
  - [CPP-CODE-006: 代码结构与控制流](#cpp-code-006-代码结构与控制流)
  - [CPP-CODE-007: 数据结构设计](#cpp-code-007-数据结构设计)
- [二、架构、API与函数设计](#二架构api与函数设计)
  - [CPP-ARCH-001: 单一职责原则](#cpp-arch-001-单一职责原则)
  - [CPP-ARCH-002: API设计与合约](#cpp-arch-002-api设计与合约)
  - [CPP-ARCH-003: 类型安全与数据表示](#cpp-arch-003-类型安全与数据表示)
  - [CPP-ARCH-004: 初始化](#cpp-arch-004-初始化)
  - [CPP-ARCH-005: 禁止上帝类/反模式](#cpp-arch-005-禁止上帝类反模式)
  - [CPP-ARCH-006: 正确使用移动语义和完美转发](#cpp-arch-006-正确使用移动语义和完美转发)
  - [CPP-ARCH-007: 优先使用enum class而非旧式枚举](#cpp-arch-007-优先使用enum-class而非旧式枚举)
  - [CPP-ARCH-008: 优先使用std::array和std::vector而非原始数组](#cpp-arch-008-优先使用stdarray和stdvector而非原始数组)
- [三、健壮性、错误处理与资源管理](#三健壮性错误处理与资源管理)
  - [CPP-ROBUST-001: 防御性编程](#cpp-robust-001-防御性编程)
  - [CPP-ROBUST-002: 错误与返回值处理](#cpp-robust-002-错误与返回值处理)
  - [CPP-ROBUST-003: Nginx核心：内存池与生命周期管理](#cpp-robust-003-nginx核心内存池与生命周期管理)
  - [CPP-MEM-001: 构造函数/析构函数中禁止调用虚函数](#cpp-mem-001-构造函数析构函数中禁止调用虚函数)
  - [CPP-MEM-002: 析构函数中禁止抛出异常](#cpp-mem-002-析构函数中禁止抛出异常)
  - [CPP-MEM-003: 优先使用智能指针而非原始指针](#cpp-mem-003-优先使用智能指针而非原始指针)
  - [CPP-MEM-004: 检查迭代器失效问题](#cpp-mem-004-检查迭代器失效问题)
- [四、C++ 编码规范特有规则](#四c-编码规范特有规则)
  - [CPP-STD-001: 禁止在头文件中使用using namespace std](#cpp-std-001-禁止在头文件中使用using-namespace-std)
  - [CPP-STD-002: 优先使用C++类型转换而非C风格转换](#cpp-std-002-优先使用c类型转换而非c风格转换)
  - [CPP-STD-003: 减少宏的使用，优先使用constexpr/inline/模板](#cpp-std-003-减少宏的使用优先使用constexprinline模板)
  - [CPP-STD-004: 禁止隐藏继承的非虚函数](#cpp-std-004-禁止隐藏继承的非虚函数)
  - [CPP-STD-005: 优先使用nullptr而非NULL或0](#cpp-std-005-优先使用nullptr而非null或0)
- [五、C 语言特有规则](#五c-语言特有规则)
  - [C-MEM-001: 禁止返回栈上局部变量的地址或指针](#c-mem-001-禁止返回栈上局部变量的地址或指针)
  - [C-MEM-002: 变长数组(VLA)禁止使用外部输入作为长度](#c-mem-002-变长数组vla禁止使用外部输入作为长度)
  - [C-MEM-003: 禁止同一表达式中对同一变量既读又写](#c-mem-003-禁止同一表达式中对同一变量既读又写)
  - [C-MEM-004: 有符号整数右移禁止依赖算术右移](#c-mem-004-有符号整数右移禁止依赖算术右移)
  - [C-SEC-001: 禁止对NULL指针解引用，链式访问前逐级判空](#c-sec-001-禁止对null指针解引用链式访问前逐级判空)
  - [C-SEC-002: 枚举值必须覆盖switch所有情况](#c-sec-002-枚举值必须覆盖switch所有情况)
  - [C-SEC-003: 禁止通过联合体(union)进行类型双关读取](#c-sec-003-禁止通过联合体union进行类型双关读取)
  - [C-SEC-004: 禁止setjmp/longjmp跳转到已返回的函数栈帧](#c-sec-004-禁止setjmplongjmp跳转到已返回的函数栈帧)
  - [C-SEC-005: 信号处理函数中禁止调用非异步安全函数](#c-sec-005-信号处理函数中禁止调用非异步安全函数)
  - [C-SEC-006: 禁止在assert副作用表达式中使用](#c-sec-006-禁止在assert副作用表达式中使用)
- [六、性能与效率](#六性能与效率)
  - [CPP-PERF-001: 避免不必要的拷贝，优先使用引用传递](#cpp-perf-001-避免不必要的拷贝优先使用引用传递)
  - [CPP-PERF-002: 循环中避免不必要的拷贝](#cpp-perf-002-循环中避免不必要的拷贝)
  - [CPP-PERF-003: CPU效率](#cpp-perf-003-cpu效率)
  - [CPP-PERF-004: 内存效率](#cpp-perf-004-内存效率)
  - [CPP-PERF-005: 并发与阻塞](#cpp-perf-005-并发与阻塞)
  - [CPP-PERF-006: 内存管理](#cpp-perf-006-内存管理)
  - [CPP-PERF-007: 性能优化](#cpp-perf-007-性能优化)
- [七、安全编码](#七安全编码)
  - [CPP-SEC-001: 内存安全](#cpp-sec-001-内存安全)
  - [CPP-SEC-002: 输入校验](#cpp-sec-002-输入校验)
  - [CPP-SEC-003: 数据匿名化](#cpp-sec-003-数据匿名化)
  - [CPP-SEC-004: 哈希碰撞](#cpp-sec-004-哈希碰撞)
- [八、测试覆盖度与质量](#八测试覆盖度与质量)
  - [CPP-TEST-001: 依赖注入优先](#cpp-test-001-依赖注入优先)
  - [CPP-TEST-002: 全局依赖的Mock覆盖](#cpp-test-002-全局依赖的mock覆盖)
  - [CPP-TEST-003: 单元测试用例质量](#cpp-test-003-单元测试用例质量)
  - [CPP-TEST-004: 有效利用Mock框架](#cpp-test-004-有效利用mock框架)
  - [CPP-TEST-005: 内存安全检测](#cpp-test-005-内存安全检测)
- [九、构建、部署与运维](#九构建部署与运维)
  - [CPP-BUILD-001: 版本与兼容性](#cpp-build-001-版本与兼容性)
  - [CPP-BUILD-002: 运维与监控](#cpp-build-002-运维与监控)
  - [CPP-BUILD-003: 代码提交与仓库管理](#cpp-build-003-代码提交与仓库管理)

---

## 一、代码风格、可读性与自文档化

### CPP-CODE-001: 命名

- **检查锚点**: 变量名含糊(ret, temp, flag), 布尔变量缺少is/has/can前缀, 命名不符合项目规范(前缀/大小写/_t后缀不一致)
- **反例**: `int ret = func(); bool flag = true; int temp = count;`
- **正例**: `int bytes_read = read(socket, buf, sizeof(buf)); bool is_connected = true; int active_conn_count = count;`
- **触发条件**: 变量名为ret/temp/flag或布尔变量缺少is/has/can前缀
- **严重程度**: suggestion

### CPP-CODE-002: 格式与整洁度

- **检查锚点**: 缩进/大括号风格与项目不一致, 被注释掉的代码, TODO标签, 冗余else块, 多余空行或分号
- **反例**: `if (x > 0) { return true; } else { return false; } // 废弃: old_method();`
- **正例**: `if (x > 0) { return true; } return false;`
- **触发条件**: 缩进/大括号风格不一致，注释掉的代码，TODO标签，冗余else块
- **严重程度**: minor

### CPP-CODE-003: 头文件管理

- **检查锚点**: 多余的#include, 头文件包含顺序不规范, 非自包含头文件, 项目内部头文件使用<>而非""
- **反例**: `#include <my_internal_header.h> #include "stdio.h" // 多余`
- **正例**: `#include "my_internal_header.h" #include <stdio.h>`
- **触发条件**: 头文件包含顺序不规范，内部头文件用<>包含，多余#include
- **严重程度**: minor

### CPP-CODE-004: 注释

- **检查锚点**: 注释重复代码意图(解释What而非Why), 注释与代码不一致, 代码中包含作者/日期/提交记录, 代码中出现外部链接
- **反例**: `// 作者: zhangsan 2024-01-01  i++; // i加1`
- **正例**: `i++; // 延迟计数器递增，用于补偿网络抖动`
- **触发条件**: 注释重复代码意图，注释与代码不一致，代码含作者/日期/提交记录
- **严重程度**: suggestion

### CPP-CODE-005: 表达清晰度

- **检查锚点**: 魔法数字/字符串, 复杂布尔表达式未简化, if/else链可用switch替代, `if (is_ok == true)` 冗余比较
- **反例**: `if (status == 3 && type != 0) { ... } // 3和0含义不明`
- **正例**: `if (status == STATUS_TIMEOUT && type != TYPE_NONE) { ... }`
- **触发条件**: 代码中出现魔法数字/字符串，复杂布尔表达式，冗余比较==true
- **严重程度**: minor

### CPP-CODE-006: 代码结构与控制流

- **检查锚点**: 深层嵌套的if语句(超过3层), 函数入口条件检查后整体缩进, 可用提前返回/卫语句替代的嵌套结构
- **反例**: `void process(Request *req) { if (req != NULL) { if (req->valid) { if (req->data != NULL) { do_work(req); } } } }`
- **正例**: `void process(Request *req) { if (req == NULL) return; if (!req->valid) return; if (req->data == NULL) return; do_work(req); }`
- **触发条件**: if嵌套超过3层，函数入口条件检查后整体缩进
- **严重程度**: minor

### CPP-CODE-007: 数据结构设计

- **检查锚点**: 仅在单个函数内使用的变量被提升为类/结构体成员, 枚举缺少边界值(_MAX/_BUTT)
- **反例**: `struct Handler { int temp_counter; void process() { temp_counter = 0; ... } }; enum Color { RED, GREEN, BLUE };`
- **正例**: `struct Handler { void process() { int counter = 0; ... } }; enum Color { RED, GREEN, BLUE, COLOR_MAX };`
- **触发条件**: 仅单函数使用的变量被提升为类成员，枚举缺少_MAX/_BUTT边界值
- **严重程度**: minor

---

## 二、架构、API与函数设计

### CPP-ARCH-001: 单一职责原则

- **检查锚点**: 函数超过50行/多个抽象层级, 模块职责分散(通用工具散落在业务模块中)
- **反例**: `void process_and_save(Data *d) { validate(d); transform(d); db_save(d); log_action(d); }`
- **正例**: `void process(Data *d) { validate(d); transform(d); } // save和log由调用方分别处理`
- **触发条件**: 函数超过50行或含多个抽象层级，通用工具散落在业务模块中
- **严重程度**: major

### CPP-ARCH-002: API设计与合约

- **检查锚点**: 函数参数超过5个, 入参未用const修饰, 非API函数/全局变量未声明为static, 出参与入参混淆
- **反例**: `void config(int a, int b, int c, int d, int e, int f); int global_cache[256];`
- **正例**: `void config(const ConfigParams *params); static int global_cache[256];`
- **触发条件**: 函数参数超过5个，入参未用const修饰，非API全局变量未声明static
- **严重程度**: minor

### CPP-ARCH-003: 类型安全与数据表示

- **检查锚点**: int64_t截断为ngx_uint_t/int, printf格式说明符与变量类型不匹配(%d对应int64_t), 用int代替bool表示开关状态
- **反例**: `ngx_uint_t len = (ngx_uint_t)content_length; printf("len: %d\n", content_length); // content_length为int64_t`
- **正例**: `ngx_uint_t len = (ngx_uint_t)content_length; printf("len: %L\n", content_length);`
- **触发条件**: int64_t截断为小类型，printf格式说明符与变量类型不匹配
- **严重程度**: major

### CPP-ARCH-004: 初始化

- **检查锚点**: 局部变量声明后未初始化即使用, 结构体成员在构造函数/初始化函数中遗漏赋值
- **反例**: `int count; if (cond) { count = calc(); } use(count); // cond为false时count未定义`
- **正例**: `int count = 0; if (cond) { count = calc(); } use(count);`
- **触发条件**: 局部变量声明后未初始化即使用，结构体成员在构造函数中遗漏赋值
- **严重程度**: major

### CPP-ARCH-005: 禁止上帝类/反模式

- **检查锚点**: 单个类职责过多, 类中方法数过多, 类依赖大量其他类
- **正例**: 遵循单一职责原则，拆分大类
- **触发条件**: 单个类方法数过多或依赖大量其他类
- **严重程度**: major

### CPP-ARCH-006: 正确使用移动语义和完美转发

- **检查锚点**: std::move, std::forward, 右值引用(&&)
- **反例**: `std::vector<int> v2 = v1;` // 不必要的拷贝
- **正例**: `std::vector<int> v2 = std::move(v1);`
- **触发条件**: 可移动对象被拷贝构造/赋值而非std::move
- **严重程度**: minor

### CPP-ARCH-007: 优先使用enum class而非旧式枚举

- **检查锚点**: enum不带class, 枚举值污染外层作用域
- **反例**: `enum Color { RED, GREEN, BLUE };`
- **正例**: `enum class Color { RED, GREEN, BLUE };`
- **触发条件**: enum不带class关键字，枚举值可能污染外层作用域
- **严重程度**: suggestion

### CPP-ARCH-008: 优先使用std::array和std::vector而非原始数组

- **反例**: `int data[100];`
- **正例**: `std::array<int, 100> data;` 或 `std::vector<int> data(100);`
- **触发条件**: C++代码中使用原始数组int data[N]而非std::array/std::vector
- **严重程度**: suggestion

---

## 三、健壮性、错误处理与资源管理

### CPP-ROBUST-001: 防御性编程

- **检查锚点**: 指针入参/返回值未判NULL, 数组索引未做边界检查, 资源(ngx_queue_t等)使用前未确认初始化状态, 数值参数未做范围校验
- **反例**: `void process(Node *node) { node->next->data = value; } // node和next均未判空`
- **正例**: `void process(Node *node) { if (node == NULL || node->next == NULL) return; node->next->data = value; }`
- **触发条件**: 指针入参/返回值未判NULL，数组索引未做边界检查
- **严重程度**: major

### CPP-ROBUST-002: 错误与返回值处理

- **检查锚点**: 函数返回值被忽略(malloc/fopen/open等), 错误日志缺少上下文信息, 日志级别使用不当(错误用INFO)
- **反例**: `fd = open(path, O_RDONLY); read(fd, buf, size); // 未检查open和read返回值`
- **正例**: `fd = open(path, O_RDONLY); if (fd < 0) { log_error("open %s failed: %s", path, strerror(errno)); return ERROR; }`
- **触发条件**: 函数返回值被忽略(malloc/fopen/open等)，错误日志缺少上下文
- **严重程度**: major

### CPP-ROBUST-003: Nginx核心：内存池与生命周期管理

- **检查锚点**: 请求池分配的内存被手动释放(ngx_pfree), 独立内存池缺少销毁路径(ngx_destroy_pool), 短生命周期池地址赋给长生命周期结构体, 资源所有权不明确
- **反例**: `char *buf = ngx_pnalloc(r->pool, size); ... ngx_pfree(r->pool, buf); // 请求池无需手动释放`
- **正例**: `char *buf = ngx_pnalloc(r->pool, size); // 请求结束时自动回收，无需释放`
- **触发条件**: 请求池内存被ngx_pfree手动释放，短生命周期池地址赋给长生命周期结构体
- **严重程度**: major

### CPP-MEM-001: 构造函数/析构函数中禁止调用虚函数

- **检查锚点**: 构造函数中调用this->xxx(), 被调方法为virtual
- **反例**: `Base() { init(); } virtual void init() { ... }`
- **正例**: 在构造后显式调用初始化方法
- **触发条件**: 构造函数或析构函数中调用虚函数(this->virtual_method())
- **严重程度**: major

### CPP-MEM-002: 析构函数中禁止抛出异常

- **检查锚点**: 析构函数中throw, 析构函数中调用可能抛异常的函数
- **触发条件**: 析构函数中出现throw或调用可能抛异常的函数
- **严重程度**: major

### CPP-MEM-003: 优先使用智能指针而非原始指针

- **检查锚点**: new/delete手动管理, 裸指针拥有内存所有权
- **反例**: `Foo *p = new Foo(); ... delete p;`
- **正例**: `auto p = std::make_unique<Foo>();`
- **触发条件**: 代码中使用new/delete手动管理内存，裸指针拥有内存所有权
- **严重程度**: minor

### CPP-MEM-004: 检查迭代器失效问题

- **检查锚点**: 在循环中erase/insert容器元素, 迭代器使用前未重新获取
- **反例**: `for (auto it = vec.begin(); it != vec.end(); ++it) { vec.erase(it); }`
- **正例**: `it = vec.erase(it);`
- **触发条件**: 循环中erase/insert容器元素后迭代器未重新获取
- **严重程度**: major

---

## 四、C++ 编码规范特有规则

### CPP-STD-001: 禁止在头文件中使用using namespace std

- **反例**: `// header.h using namespace std;`
- **正例**: 在头文件中使用std::限定符
- **触发条件**: 头文件中出现using namespace std
- **严重程度**: minor

### CPP-STD-002: 优先使用C++类型转换而非C风格转换

- **反例**: `Derived *d = (Derived *)base;`
- **正例**: `Derived *d = dynamic_cast<Derived *>(base);`
- **触发条件**: 代码中使用C风格类型转换(Type)expr而非C++类型转换
- **严重程度**: minor

### CPP-STD-003: 减少宏的使用，优先使用constexpr/inline/模板

- **反例**: `#define MAX(a,b) ((a)>(b)?(a):(b))`
- **正例**: `constexpr auto max_val = 100; inline int max(int a, int b) { return a > b ? a : b; }`
- **触发条件**: 代码中使用#define宏定义常量或函数式宏
- **严重程度**: minor

### CPP-STD-004: 禁止隐藏继承的非虚函数

- **正例**: 使用override关键字覆盖虚函数，避免重定义非虚函数
- **触发条件**: 派生类重定义基类非虚函数，隐藏继承的非虚函数
- **严重程度**: major

### CPP-STD-005: 优先使用nullptr而非NULL或0

- **反例**: `int *p = NULL;`
- **正例**: `int *p = nullptr;`
- **触发条件**: C++代码中使用NULL或0表示空指针而非nullptr
- **严重程度**: suggestion

---

## 五、C 语言特有规则

### C-MEM-001: 禁止返回栈上局部变量的地址或指针

- **反例**: `int* get_value() { int val = 42; return &val; }`
- **正例**: `int* get_value() { int* val = malloc(sizeof(int)); *val = 42; return val; }`
- **触发条件**: 函数返回局部变量的地址或指针(&局部变量)
- **严重程度**: fatal

### C-MEM-002: 变长数组(VLA)禁止使用外部输入作为长度

- **反例**: `void process(int n) { int buf[n]; }`
- **正例**: `void process(int n) { if (n <= 0 || n > MAX_SIZE) { return; } int *buf = malloc(n * sizeof(int)); }`
- **触发条件**: 变长数组(VLA)使用外部输入作为长度int buf[n]
- **严重程度**: major

### C-MEM-003: 禁止同一表达式中对同一变量既读又写

- **反例**: `arr[i] = i++;`
- **正例**: `arr[i] = i; i++;`
- **触发条件**: 同一表达式中对同一变量既读又写(如arr[i] = i++)
- **严重程度**: major

### C-MEM-004: 有符号整数右移禁止依赖算术右移

- **反例**: `int sign_extend = value >> 31;`
- **正例**: `int sign_extend = value < 0 ? ~0 : 0;`
- **触发条件**: 有符号整数右移value >> N依赖算术右移行为
- **严重程度**: major

### C-SEC-001: 禁止对NULL指针解引用，链式访问前逐级判空

- **反例**: `req->header->type`
- **正例**: `if (req != NULL && req->header != NULL) { type = req->header->type; }`
- **触发条件**: 指针链式访问(req->header->type)前未逐级判空
- **严重程度**: major

### C-SEC-002: 枚举值必须覆盖switch所有情况

- **反例**: `switch (color) { case RED: break; case BLUE: break; }` // 缺default
- **正例**: 添加 `default: return ERROR;`
- **触发条件**: switch语句缺少default分支或未覆盖所有枚举值
- **严重程度**: minor

### C-SEC-003: 禁止通过联合体(union)进行类型双关读取

- **反例**: `union { float f; int i; } u; u.f = 1.0; return u.i;`
- **正例**: `memcpy(&i, &f, sizeof(int));`
- **触发条件**: 通过union进行类型双关读取(u.f=1.0; return u.i)
- **严重程度**: major

### C-SEC-004: 禁止setjmp/longjmp跳转到已返回的函数栈帧

- **正例**: 确保longjmp仅在setjmp所在函数的调用链内使用
- **触发条件**: setjmp/longjmp跨函数栈帧跳转
- **严重程度**: fatal

### C-SEC-005: 信号处理函数中禁止调用非异步安全函数

- **反例**: `void handler(int sig) { printf("signal %d\n", sig); }`
- **正例**: `void handler(int sig) { volatile sig_atomic_t flag = 1; }`
- **触发条件**: 信号处理函数中调用printf/malloc等非异步安全函数
- **严重程度**: fatal

### C-SEC-006: 禁止在assert副作用表达式中使用

- **反例**: `assert(count++ > 0);`
- **正例**: `count++; assert(count > 0);`
- **触发条件**: assert表达式中包含副作用操作(如count++, i++)
- **严重程度**: major

---

## 六、性能与效率

### CPP-PERF-001: 避免不必要的拷贝，优先使用引用传递

- **反例**: `void process(std::vector<int> data) { ... }`
- **正例**: `void process(const std::vector<int> &data) { ... }`
- **触发条件**: 函数参数按值传递大对象而非const引用
- **严重程度**: minor

### CPP-PERF-002: 循环中避免不必要的拷贝

- **反例**: `for (auto item : items) { ... }`
- **正例**: `for (const auto &item : items) { ... }`
- **触发条件**: range-based for循环中按值捕获auto item而非const auto& item
- **严重程度**: minor

### CPP-PERF-003: CPU效率

- **检查锚点**: 循环内重复计算不变值(strlen/size等), 使用低效字符串比较函数(strcmp代替特定优化函数), 循环不变表达式未提取到循环外
- **反例**: `for (int i = 0; i < strlen(str); i++) { process(str[i]); }`
- **正例**: `size_t len = strlen(str); for (int i = 0; i < len; i++) { process(str[i]); }`
- **触发条件**: 循环条件中调用strlen/size等不变函数，循环不变表达式未提取
- **严重程度**: minor

### CPP-PERF-004: 内存效率

- **检查锚点**: 未使用内存池而频繁malloc/free, 大结构体按值传递, 未使用指针或标记位替代大块数据拷贝
- **反例**: `void copy_state(ServerState state) { backup = state; } // ServerState为1KB大结构体`
- **正例**: `void copy_state(const ServerState *state) { backup = *state; }` 或使用内存池分配
- **触发条件**: 大结构体按值传递/拷贝，频繁malloc/free而非使用内存池
- **严重程度**: minor

### CPP-PERF-005: 并发与阻塞

- **检查锚点**: Nginx worker进程中调用阻塞IO(fopen/read/sleep/gethostbyname), 同步锁操作(pthread_mutex_lock)
- **反例**: `ngx_int_t rc = read(fd, buf, size); // 在worker进程中同步阻塞读取`
- **正例**: 使用Nginx异步事件机制: `ngx_handle_read_event(rev, 0);`
- **触发条件**: Nginx worker中调用阻塞IO(fopen/read/sleep/gethostbyname)
- **严重程度**: major

### CPP-PERF-006: 内存管理

- **检查锚点**: 哈希表key为栈上/短生命周期内存, key生命周期短于哈希表本身
- **反例**: `char key[64]; snprintf(key, sizeof(key), "%s:%d", host, port); ngx_hash_add(&hash, key, value); // key在栈上，函数返回后失效`
- **正例**: `char *key = ngx_pnalloc(pool, 64); snprintf(key, 64, "%s:%d", host, port); ngx_hash_add(&hash, key, value);`
- **触发条件**: 哈希表key为栈上/短生命周期内存，key生命周期短于哈希表
- **严重程度**: major

### CPP-PERF-007: 性能优化

- **检查锚点**: 请求处理路径中重复解析配置数据, 每次请求都做的计算可在配置加载时预处理
- **反例**: `int handle_request(Request *r) { parse_config(r->conf_str, &params); // 每次请求都解析 }`
- **正例**: `// 配置加载时预处理 parse_config(conf_str, &cached_params); int handle_request(Request *r) { use_cached(&cached_params); }`
- **触发条件**: 请求处理路径中重复解析配置数据，每次请求重复可预处理计算
- **严重程度**: minor

---

## 七、安全编码

### CPP-SEC-001: 内存安全

- **检查锚点**: 使用sprintf/strcpy/strcat而非安全版本, snprintf_s/memcpy_s参数错误(缓冲区大小不匹配)
- **反例**: `sprintf(buf, "%s:%d", host, port); // 缓冲区溢出风险`
- **正例**: `snprintf_s(buf, sizeof(buf), sizeof(buf) - 1, "%s:%d", host, port);`
- **触发条件**: 使用sprintf/strcpy/strcat等不安全C函数而非安全版本
- **严重程度**: fatal

### CPP-SEC-002: 输入校验

- **检查锚点**: 外部输入(HTTP请求/配置文件/命令行参数)未做合法性校验, 直接使用外部输入作为数组索引/长度/格式字符串
- **反例**: `int idx = atoi(input_str); result = array[idx]; // idx未做范围校验`
- **正例**: `int idx = atoi(input_str); if (idx < 0 || idx >= ARRAY_SIZE) { return ERROR; } result = array[idx];`
- **触发条件**: 外部输入未做合法性校验直接用作数组索引/长度/格式字符串
- **严重程度**: fatal

### CPP-SEC-003: 数据匿名化

- **检查锚点**: 代码中存在明文AK/SK/密码/密钥, 日志中打印敏感信息(手机号/身份证/Token), 硬编码凭证
- **反例**: `const char *access_key = "AKIAIOSFODNN7EXAMPLE"; log_info("user token: %s", token);`
- **正例**: `const char *access_key = load_from_vault("ACCESS_KEY"); log_info("user token: %s", mask_token(token));`
- **触发条件**: 代码中存在明文AK/SK/密码/密钥，日志中打印敏感信息
- **严重程度**: fatal

### CPP-SEC-004: 哈希碰撞

- **检查锚点**: 多字段拼接为哈希key时未加分隔符, 不同字段值组合可能产生相同拼接结果
- **反例**: `snprintf(key, sizeof(key), "%s%s", field_a, field_b); // "ab"+"c" 与 "a"+"bc" 碰撞`
- **正例**: `snprintf(key, sizeof(key), "%s:%s", field_a, field_b); // 使用分隔符避免碰撞`
- **触发条件**: 多字段拼接为哈希key时未加分隔符("%s%s"拼接)
- **严重程度**: major

---

## 八、测试覆盖度与质量

### CPP-TEST-001: 依赖注入优先

- **检查锚点**: 类内部直接new依赖对象, 硬编码依赖关系导致无法独立测试
- **反例**: `class Service { DbClient db_; public: Service() : db_("localhost:3306") {} };`
- **正例**: `class Service { IDbClient &db_; public: Service(IDbClient &db) : db_(db) {} };`
- **触发条件**: 类内部直接new依赖对象，硬编码依赖关系导致无法独立测试
- **严重程度**: minor

### CPP-TEST-002: 全局依赖的Mock覆盖

- **检查锚点**: 代码调用全局函数/静态方法, 对应单元测试中未用mockcpp等框架打桩验证
- **反例**: `time_t now = get_current_time(); // 全局函数调用 // UT中未mock get_current_time`
- **正例**: `time_t now = get_current_time(); // UT中: MOCK(get_current_time).expects(once()).will(returnValue(1000));`
- **触发条件**: 代码调用全局函数/静态方法但UT中未用mock框架打桩验证
- **严重程度**: minor

### CPP-TEST-003: 单元测试用例质量

- **检查锚点**: 单个UT覆盖多个场景, UT命名不清晰(如test1/test_func), 缺少关键状态/值的断言, 未覆盖边界条件
- **反例**: `TEST_F(TestParser, test_all) { auto r = parse(input); EXPECT_TRUE(r.ok); } // 命名模糊，缺少具体断言`
- **正例**: `TEST_F(TestParser, parse_empty_input_returns_error) { auto r = parse(""); EXPECT_EQ(r.code, ERR_EMPTY_INPUT); }`
- **触发条件**: UT命名不清晰(test1/test_func)，缺少关键状态断言，未覆盖边界条件
- **严重程度**: minor

### CPP-TEST-004: 有效利用Mock框架

- **检查锚点**: mock未设置expects()/will()预期行为, mock范围过宽或过窄, 外部交互未完全mock
- **反例**: `MOCK(db_query); // 仅声明mock，未定义行为和预期`
- **正例**: `MOCK(db_query).expects(once()).with(eq("key")).will(returnValue(42));`
- **触发条件**: mock仅声明MOCK()未定义expects()/will()行为和预期
- **严重程度**: minor

### CPP-TEST-005: 内存安全检测

- **检查锚点**: cc_test中缺少-fsanitize=address编译选项, 新增测试未启用ASAN
- **反例**: `cc_test(name = "foo_test", srcs = ["foo_test.cc"]) // 缺少ASAN选项`
- **正例**: `cc_test(name = "foo_test", srcs = ["foo_test.cc"], copts = ["-fsanitize=address"])`
- **触发条件**: cc_test中缺少-fsanitize=address编译选项
- **严重程度**: minor

---

## 九、构建、部署与运维

### CPP-BUILD-001: 版本与兼容性

- **检查锚点**: 数据结构变更未考虑线上分批升级(旧版本无法解析新格式), 协议/接口变更缺少版本号或兼容处理
- **反例**: `struct Config { int new_field; }; // 旧版本解析时new_field为未定义值`
- **正例**: `struct Config { int version; int new_field; }; // 旧版本根据version字段做兼容处理`
- **触发条件**: 数据结构/协议变更未考虑线上分批升级，缺少版本号或兼容处理
- **严重程度**: major

### CPP-BUILD-002: 运维与监控

- **检查锚点**: 关键功能无日志/指标输出, 依赖外部组件无降级/熔断方案, 入口模块无版本号打印
- **反例**: `void call_external_service() { auto resp = http_get(url); return resp.data; } // 无超时/重试/降级`
- **正例**: `void call_external_service() { auto resp = http_get(url, TIMEOUT_MS); if (!resp.ok) { log_warn("external failed, fallback to cache"); return cache_get(key); } }`
- **触发条件**: 关键功能无日志/指标输出，依赖外部组件无降级/熔断方案
- **严重程度**: major

### CPP-BUILD-003: 代码提交与仓库管理

- **检查锚点**: Commit Message不规范(无模块前缀/无变更说明), 单次MR包含不相关修改(夹带), 大规模重构与功能修改混合提交
- **反例**: `git commit -m "fix bug" // 含义不明，且包含格式化+功能修改+新文件`
- **正例**: `git commit -m "[module_x] 修复连接超时未释放资源的缺陷"`
- **触发条件**: Commit Message不规范(无模块前缀/无变更说明)，MR包含不相关修改
- **严重程度**: minor
