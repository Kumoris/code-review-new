# Java 检视规则

> 来源：既有检视规则去重合并；规则与代码托管平台无关

---

## 目录

- [一、架构设计与代码结构](#一架构设计与代码结构)
  - [JAVA-ARCH-001: SOLID原则](#java-arch-001-solid原则)
  - [JAVA-ARCH-002: 分层与职责](#java-arch-002-分层与职责)
  - [JAVA-ARCH-003: 依赖注入](#java-arch-003-依赖注入)
  - [JAVA-ARCH-004: 设计模式应用](#java-arch-004-设计模式应用)
  - [JAVA-ARCH-005: 可枚举概念必须使用枚举定义](#java-arch-005-可枚举概念必须使用枚举定义)
- [二、代码实现与可读性](#二代码实现与可读性)
  - [JAVA-CODE-001: 文件编码UTF-8](#java-code-001-文件编码utf-8)
  - [JAVA-CODE-002: 命名规范](#java-code-002-命名规范)
  - [JAVA-CODE-003: 注释质量](#java-code-003-注释质量)
  - [JAVA-CODE-004: 代码简洁性](#java-code-004-代码简洁性)
  - [JAVA-CODE-005: 异常处理](#java-code-005-异常处理)
  - [JAVA-CODE-006: 日志规范](#java-code-006-日志规范)
  - [JAVA-CODE-007: 禁止使用Optional.of](#java-code-007-禁止使用optionalof)
  - [JAVA-CODE-008: 禁止直接修改SQL返回对象](#java-code-008-禁止直接修改sql返回对象)
  - [JAVA-CODE-009: 禁止使用java.text.SimpleDateFormat](#java-code-009-禁止使用javatextsimpledateformat)
  - [JAVA-CODE-010: 禁止使用mapstruct的expression](#java-code-010-禁止使用mapstruct的expression)
  - [JAVA-CODE-011: 字符串ID集合转数值类型必须安全转换](#java-code-011-字符串id集合转数值类型必须安全转换)
  - [JAVA-CODE-012: 禁止使用枚举的valueOf方法](#java-code-012-禁止使用枚举的valueof方法)
  - [JAVA-CODE-013: 不信任数据源必须增加校验](#java-code-013-不信任数据源必须增加校验)
  - [JAVA-CODE-014: 禁止使用poi的cell.getStringCellValue](#java-code-014-禁止使用poi的cellgetstringcellvalue)
  - [JAVA-CODE-015: 禁止直接强转，必须instanceof检查](#java-code-015-禁止直接强转必须instanceof检查)
- [三、Java语言最佳实践](#三java语言最佳实践)
  - [JAVA-BEST-001: Optional的使用](#java-best-001-optional的使用)
  - [JAVA-BEST-002: Stream API](#java-best-002-stream-api)
  - [JAVA-BEST-003: 集合（Collections）](#java-best-003-集合collections)
  - [JAVA-BEST-004: 类的设计](#java-best-004-类的设计)
- [四、性能、并发与资源管理](#四性能并发与资源管理)
  - [JAVA-PERF-001: 禁止在循环中拼接字符串](#java-perf-001-禁止在循环中拼接字符串)
  - [JAVA-PERF-002: 禁止在循环中查询数据库](#java-perf-002-禁止在循环中查询数据库)
  - [JAVA-PERF-003: 禁止大循环内创建不必要的对象](#java-perf-003-禁止大循环内创建不必要的对象)
  - [JAVA-PERF-004: 内存使用与GC压力](#java-perf-004-内存使用与gc压力)
  - [JAVA-PERF-005: 并发与锁](#java-perf-005-并发与锁)
  - [JAVA-CON-001: 禁止对共享可变状态无同步访问](#java-con-001-禁止对共享可变状态无同步访问)
  - [JAVA-CON-002: 使用Lock对象时必须在finally块中释放锁](#java-con-002-使用lock对象时必须在finally块中释放锁)
  - [JAVA-CON-003: 使用ThreadLocal传递业务状态时必须在finally块中清理](#java-con-003-使用threadlocal传递业务状态时必须在finally块中清理)
  - [JAVA-PERF-006: 线程池使用](#java-perf-006-线程池使用)
  - [JAVA-PERF-007: 资源管理](#java-perf-007-资源管理)
  - [JAVA-PERF-008: 数据库交互](#java-perf-008-数据库交互)
- [五、安全编码](#五安全编码)
  - [JAVA-SEC-001: 禁止硬编码密码和密钥](#java-sec-001-禁止硬编码密码和密钥)
  - [JAVA-SEC-002: 禁止使用不安全的随机数生成器](#java-sec-002-禁止使用不安全的随机数生成器)
  - [JAVA-SEC-003: 外部参数校验](#java-sec-003-外部参数校验)
  - [JAVA-SEC-004: 敏感信息防泄漏](#java-sec-004-敏感信息防泄漏)
  - [JAVA-SEC-005: SQL注入防护](#java-sec-005-sql注入防护)
  - [JAVA-SEC-006: 序列化与反序列化安全](#java-sec-006-序列化与反序列化安全)
  - [JAVA-SEC-007: 高危数据库操作](#java-sec-007-高危数据库操作)
  - [JAVA-SEC-008: 依赖安全](#java-sec-008-依赖安全)
- [六、易错点](#六易错点)
  - [JAVA-COM-001: MyBatis动态SQL连续字段更新时必须在末尾添加逗号](#java-com-001-mybatis动态sql连续字段更新时必须在末尾添加逗号)
  - [JAVA-COM-002: Stream.toMap必须处理key重复场景](#java-com-002-streamtomap必须处理key重复场景)
  - [JAVA-COM-003: JSON解析后必须空检查](#java-com-003-json解析后必须空检查)
  - [JAVA-COM-004: 处理外部响应数据时必须空指针检查](#java-com-004-处理外部响应数据时必须空指针检查)
  - [JAVA-COM-005: 从Map中取值后必须检查key是否存在](#java-com-005-从map中取值后必须检查key是否存在)
  - [JAVA-COM-006: 链式调用getXxx().getYyy()前必须null检查](#java-com-006-链式调用getxxxgetyyy前必须null检查)
  - [JAVA-COM-007: 遍历集合前必须检查null或空](#java-com-007-遍历集合前必须检查null或空)
  - [JAVA-COM-008: List下标获取元素前必须边界检查](#java-com-008-list下标获取元素前必须边界检查)
  - [JAVA-COM-009: 批量数据库操作必须分批处理](#java-com-009-批量数据库操作必须分批处理)
  - [JAVA-COM-010: 批量数据库操作必须按固定顺序排序避免死锁](#java-com-010-批量数据库操作必须按固定顺序排序避免死锁)
- [七、单元测试与可测试性](#七单元测试与可测试性)
  - [JAVA-TEST-001: 测试技术栈](#java-test-001-测试技术栈)
  - [JAVA-TEST-002: 断言正确性与清晰度](#java-test-002-断言正确性与清晰度)
  - [JAVA-TEST-003: 禁止Mock被测对象本身](#java-test-003-禁止mock被测对象本身)
  - [JAVA-TEST-004: 警惕全局状态与静态依赖](#java-test-004-警惕全局状态与静态依赖)
  - [JAVA-TEST-005: 警惕过度使用PowerMock](#java-test-005-警惕过度使用powermock)
  - [JAVA-TEST-006: 参数化测试](#java-test-006-参数化测试)
  - [JAVA-TEST-007: 序列化兼容性测试](#java-test-007-序列化兼容性测试)
  - [JAVA-TEST-008: 禁止在测试中使用Thread.sleep](#java-test-008-禁止在测试中使用threadsleep)
  - [JAVA-TEST-009: 测试数据规模](#java-test-009-测试数据规模)
  - [JAVA-TEST-010: 避免不必要的IO操作](#java-test-010-避免不必要的io操作)
- [八、构建、部署与环境配置](#八构建部署与环境配置)
  - [JAVA-BUILD-001: 服务器配置显式化](#java-build-001-服务器配置显式化)
  - [JAVA-BUILD-002: 依赖管理](#java-build-002-依赖管理)
  - [JAVA-BUILD-003: 容器化配置](#java-build-003-容器化配置)

---

## 一、架构设计与代码结构

### JAVA-ARCH-001: SOLID原则

- **检查锚点**: 类中存在多个不相关职责的方法(如CRUD+通知+导出), 接口方法数>5且客户端仅用其中1-2个, new具体实现类而非注入接口, 子类重写父类方法抛出UnsupportedOperationException
- **反例**: `class UserManager { void register(); void login(); void deleteUser(); void sendEmail(); void exportReport(); }`
- **正例**: 拆分为 `UserService { register(); deleteUser(); }`, `AuthService { login(); }`, `EmailService { sendEmail(); }`, `ReportService { exportReport(); }`, 通过接口注入协作
- **触发条件**: 类中包含多个不相关职责的方法，或接口方法数>5且客户端仅用其中1-2个，或子类重写父类方法抛出UnsupportedOperationException
- **严重程度**: major

### JAVA-ARCH-002: 分层与职责

- **检查锚点**: Controller中包含业务逻辑判断(if/switch/for计算), Service层直接返回Entity而非DTO, DAO层包含业务条件分支
- **反例**: `@RestController class OrderController { @PostMapping public Result create(@RequestBody OrderReq req) { if (req.getAmount() > 10000) { applyDiscount(req); } orderDao.save(req); notifyService.send(req); } }`
- **正例**: `@RestController class OrderController { @PostMapping public Result create(@RequestBody OrderReq req) { return orderService.createOrder(req); } }`, 业务逻辑在Service层完成
- **触发条件**: Controller中包含if/switch/for等业务逻辑判断，或Service层直接返回Entity而非DTO，或DAO层包含业务条件分支
- **严重程度**: major

### JAVA-ARCH-003: 依赖注入

- **检查锚点**: 方法内new具体实现类, 类中直接引用具体类而非接口, 静态方法调用外部依赖
- **反例**: `class OrderService { private MySqlOrderRepository repo = new MySqlOrderRepository(); private EmailNotifier notifier = new SmtpEmailNotifier(); }`
- **正例**: `class OrderService { private final OrderRepository repo; private final Notifier notifier; public OrderService(OrderRepository repo, Notifier notifier) { this.repo = repo; this.notifier = notifier; } }`
- **触发条件**: 方法内new具体实现类，或类中直接引用具体类而非接口，或静态方法调用外部依赖
- **严重程度**: minor

### JAVA-ARCH-004: 设计模式应用

- **检查锚点**: 大段if-else/switch根据类型分支创建不同对象, 构造函数参数>5个且多数可选, 重复的算法骨架仅步骤不同
- **反例**: `if (type.equals("A")) { obj = new TypeA(); obj.setBase("x"); obj.setSpecialA("y"); } else if (type.equals("B")) { obj = new TypeB(); obj.setBase("x"); obj.setSpecialB("z"); }`
- **正例**: 使用工厂模式创建对象, 建造者模式处理多参数构造, 策略模式消除类型分支, 模板方法模式复用算法骨架
- **触发条件**: 大段if-else/switch根据类型分支创建不同对象，或构造函数参数>5个且多数可选，或重复的算法骨架仅步骤不同
- **严重程度**: minor

### JAVA-ARCH-005: 可枚举概念必须使用枚举定义

- **检查锚点**: 若干个常量定义同一概念(int/string常量组), if-else链判断枚举值
- **反例**: `public static final int STATUS_ACTIVE = 1; public static final int STATUS_INACTIVE = 2;`
- **正例**: `public enum Status { ACTIVE, INACTIVE; }`
- **触发条件**: 若干个常量定义同一概念(int/string常量组)，或if-else链判断枚举值
- **严重程度**: minor

---

## 二、代码实现与可读性

### JAVA-CODE-001: 文件编码UTF-8

- **检查锚点**: .java文件中出现GBK/GB2312/Latin1编码声明, 中文注释乱码, build脚本未指定UTF-8
- **反例**: `// 文件编码为GBK，中文注释在其他环境显示为乱码` 或 `javac -encoding GBK MyClass.java`
- **正例**: `javac -encoding UTF-8 MyClass.java`, pom.xml中 `<project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>`
- **触发条件**: .java文件中出现GBK/GB2312/Latin1编码声明，或build脚本未指定UTF-8编码
- **严重程度**: minor

### JAVA-CODE-002: 命名规范

- **检查锚点**: 变量名单字母(非循环变量i/j/k), 方法名不能表达意图(如doStuff/process/handle), 测试方法名不含when/should语义
- **反例**: `int d; void process(); @Test void test1(); class ums_user_dao;`
- **正例**: `int elapsedTimeInDays; void calculateTotalPrice(); @Test void shouldReturnEmptyList_whenNoRecordsFound(); class UserRepository`
- **触发条件**: 变量名单字母(非循环变量i/j/k)，或方法名不能表达意图(如doStuff/process/handle)，或测试方法名不含when/should语义
- **严重程度**: minor

### JAVA-CODE-003: 注释质量

- **检查锚点**: 注释仅重复代码逻辑(如 // set name to name), TODO/FIXME长期存在, Javadoc缺少@param/@return, 过时注释与代码不一致
- **反例**: `// set the name user.setName(name); // increment count count++;`
- **正例**: `// 使用BET算法优化: 因O(n^2)复杂度在大数据量下超时, 改为分桶预聚合 user.setName(name);`
- **触发条件**: 注释仅重复代码逻辑(如// set name to name)，或TODO/FIXME长期存在，或Javadoc缺少@param/@return，或过时注释与代码不一致
- **严重程度**: minor

### JAVA-CODE-004: 代码简洁性

- **检查锚点**: if-else嵌套超过3层, 代码中存在魔法数字/硬编码字符串, 可用Stream但用了for循环+临时集合
- **反例**: `if (user != null) { if (user.getAge() > 18) { if (user.isActive()) { return "A"; } else { return "B"; } } else { return "C"; } } else { return "D"; }`
- **正例**: `if (user == null) return "D"; if (user.getAge() <= 18) return "C"; return user.isActive() ? "A" : "B";`
- **触发条件**: if-else嵌套超过3层，或代码中存在魔法数字/硬编码字符串，或可用Stream但用了for循环+临时集合
- **严重程度**: minor

### JAVA-CODE-005: 异常处理

- **检查锚点**: catch(Exception e), catch块为空或仅e.printStackTrace(), 异常信息丢失(e.getMessage()丢弃堆栈)
- **反例**: `try { ... } catch (Exception e) { e.printStackTrace(); }`
- **正例**: `try { ... } catch (IOException e) { log.error("读取配置文件失败: {}", configPath, e); throw new ConfigLoadException("配置加载失败", e); }`
- **触发条件**: catch(Exception e)捕获过宽异常，或catch块为空/仅e.printStackTrace()，或异常信息丢失(e.getMessage()丢弃堆栈)
- **严重程度**: major

### JAVA-CODE-006: 日志规范

- **检查锚点**: log.info(e.getMessage()), 循环体内log.debug/info, 关键分支无日志, 日志级别使用不当(正常流程用ERROR)
- **反例**: `catch (BizException e) { log.error(e.getMessage()); }`, `for (Order o : orders) { log.info("processing: {}", o.getId()); }`
- **正例**: `catch (BizException e) { log.error("订单处理失败, orderId={}", orderId, e); }`, 循环外打印汇总: `log.info("处理完成, 总数={}, 成功={}", total, success);`
- **触发条件**: log.info(e.getMessage())丢失堆栈，或循环体内log.debug/info，或关键分支无日志，或日志级别使用不当(正常流程用ERROR)
- **严重程度**: minor

### JAVA-CODE-007: 禁止使用Optional.of

- **检查锚点**: Optional.of(
- **反例**: `Optional.of(value)`
- **正例**: `Optional.ofNullable(value)`
- **触发条件**: 代码中出现Optional.of(调用，当传入null时会抛NullPointerException
- **严重程度**: major

### JAVA-CODE-008: 禁止直接修改SQL返回对象

- **检查锚点**: Mybatis查询结果.getXxxList().clear(), getXxxList().remove(), getXxxList().add()
- **反例**: `trailPO.getNmsTrailPOList().clear();`
- **正例**: `trailPO.setNmsTrailPOList(Collections.emptyList());`
- **触发条件**: Mybatis查询结果对象调用getXxxList().clear()/remove()/add()直接修改SQL返回的集合对象
- **严重程度**: major

### JAVA-CODE-009: 禁止使用java.text.SimpleDateFormat

- **检查锚点**: new SimpleDateFormat, SimpleDateFormat.parse, SimpleDateFormat.format
- **反例**: `new SimpleDateFormat("yyyy-MM-dd").parse(dateStr);`
- **正例**: `DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");`
- **触发条件**: 代码中出现new SimpleDateFormat或SimpleDateFormat.parse/format调用，SimpleDateFormat非线程安全
- **严重程度**: major

### JAVA-CODE-010: 禁止使用mapstruct的expression

- **检查锚点**: @Mapping(expression=, expression中包含复杂逻辑
- **正例**: 复杂转换建议编码实现而非使用expression
- **触发条件**: @Mapping注解中使用expression=属性，expression中包含复杂逻辑难以维护和调试
- **严重程度**: minor

### JAVA-CODE-011: 字符串ID集合转数值类型必须安全转换

- **检查锚点**: Stream.map(Long::valueOf), Stream.map(Integer::valueOf)
- **反例**: `neIds.stream().map(Long::valueOf).collect(...)` - 非数字字符串会抛NumberFormatException
- **正例**: `neIds.stream().map(Longs::tryParse).filter(Objects::nonNull).collect(...)`
- **触发条件**: Stream.map(Long::valueOf)或Stream.map(Integer::valueOf)对字符串ID集合转换，非数字字符串会抛NumberFormatException
- **严重程度**: major

### JAVA-CODE-012: 禁止使用枚举的valueOf方法

- **检查锚点**: Enum.valueOf, xxxEnum.valueOf
- **反例**: `EnableStatus.valueOf(param.getQuantumEncryptState())` 值不在枚举内直接抛IllegalArgumentException
- **正例**: `EnableStatus.getByName` or `EnableStatus.getByValue` 等安全方法
- **触发条件**: 代码中出现Enum.valueOf或xxxEnum.valueOf调用，值不在枚举内直接抛IllegalArgumentException
- **严重程度**: major

### JAVA-CODE-013: 不信任数据源必须增加校验

- **检查锚点**: RPC请求的Response数据直接使用, Rest接口Request数据直接使用
- **反例**: `response.getData().getId();`
- **正例**: `if (response.getData() != null && response.getData().getId() != null)`
- **触发条件**: RPC请求的Response数据或Rest接口Request数据直接使用未做null校验
- **严重程度**: major

### JAVA-CODE-014: 禁止使用poi的cell.getStringCellValue

- **检查锚点**: cell.getStringCellValue()
- **正例**: 先判断单元格类型再取值
- **触发条件**: 代码中出现cell.getStringCellValue()调用，未判断单元格类型直接取字符串值可能导致类型不匹配异常
- **严重程度**: major

### JAVA-CODE-015: 禁止直接强转，必须instanceof检查

- **检查锚点**: (SubClass) obj 强转
- **反例**: `XSSFWorkbook xssfWorkbook = ((SXSSFWorkbook) workbook).getXSSFWorkbook();`
- **正例**: `if (workbook instanceof SXSSFWorkbook) { ... } else { ... }`
- **触发条件**: 代码中出现(SubClass) obj直接强转，未先使用instanceof检查类型
- **严重程度**: major

---

## 三、Java语言最佳实践

### JAVA-BEST-001: Optional的使用

- **检查锚点**: 方法返回null而非Optional, Optional用作字段/方法参数, Optional.get()未先isPresent()检查
- **反例**: `public User findUser(String id) { return null; }`, `Optional<User> opt = ...; opt.get().getName();`
- **正例**: `public Optional<User> findUser(String id) { return Optional.ofNullable(userMap.get(id)); }`, `opt.map(User::getName).orElse("default");`
- **触发条件**: 方法返回null而非Optional，或Optional用作字段/方法参数，或Optional.get()未先isPresent()检查
- **严重程度**: minor

### JAVA-BEST-002: Stream API

- **检查锚点**: for循环中包含filter/map/collect逻辑, 数据库查询后Java内存中过滤/排序(应SQL完成), stream中嵌套stream
- **反例**: `List<User> admins = new ArrayList<>(); for (User u : users) { if ("ADMIN".equals(u.getRole())) { admins.add(u); } }`
- **正例**: `List<User> admins = users.stream().filter(u -> "ADMIN".equals(u.getRole())).collect(Collectors.toList());`, 排序过滤应在SQL: `SELECT * FROM user WHERE role = 'ADMIN' ORDER BY name`
- **触发条件**: for循环中包含filter/map/collect逻辑，或数据库查询后Java内存中过滤/排序(应SQL完成)，或stream中嵌套stream
- **严重程度**: minor

### JAVA-BEST-003: 集合（Collections）

- **检查锚点**: new ArrayList<>()未指定初始容量后大量add, 方法返回可变集合引用(外部可修改内部状态), new HashMap<>()未设初始容量
- **反例**: `List<String> result = new ArrayList<>(); for (int i = 0; i < 10000; i++) { result.add(String.valueOf(i)); }`, `public List<String> getNames() { return this.names; }`
- **正例**: `List<String> result = new ArrayList<>(10000);`, `public List<String> getNames() { return Collections.unmodifiableList(this.names); }`
- **触发条件**: new ArrayList<>()未指定初始容量后大量add，或方法返回可变集合引用(外部可修改内部状态)，或new HashMap<>()未设初始容量
- **严重程度**: minor

### JAVA-BEST-004: 类的设计

- **检查锚点**: static方法访问外部依赖(数据库/缓存), @Data注解在含敏感字段的类上, @Builder注解在含不应外部设置字段的类上, equals/hashCode不一致
- **反例**: `@Data public class UserDTO { private String password; private String username; }`, `public static User getUser(String id) { return userDao.findById(id); }`
- **正例**: `@Getter public class UserDTO { private String username; @ToString.Exclude private String password; }`, 将UserDao通过构造函数注入而非static调用
- **触发条件**: static方法访问外部依赖(数据库/缓存)，或@Data注解在含敏感字段的类上，或@Builder注解在含不应外部设置字段的类上，或equals/hashCode不一致
- **严重程度**: minor

---

## 四、性能、并发与资源管理

### JAVA-PERF-001: 禁止在循环中拼接字符串

- **检查锚点**: +拼接字符串在for/while/stream循环体内
- **反例**: `for (String item : items) { result += item; }`
- **正例**: `StringBuilder sb = new StringBuilder(); for (String item : items) { sb.append(item); }`
- **触发条件**: 在for/while/stream循环体内使用+拼接字符串
- **严重程度**: minor

### JAVA-PERF-002: 禁止在循环中查询数据库

- **检查锚点**: 数据库查询方法在for/while/stream循环体内
- **反例**: `for (Long id : ids) { User user = userMapper.selectById(id); }`
- **正例**: `List<User> users = userMapper.selectBatchIds(ids);`
- **触发条件**: 数据库查询方法(mapper/select/query)在for/while/stream循环体内调用，产生N+1查询问题
- **严重程度**: major

### JAVA-PERF-003: 禁止大循环内创建不必要的对象

- **检查锚点**: new对象在for/while高频循环体内
- **反例**: `for (Item item : items) { DateFormat df = new SimpleDateFormat("yyyy-MM-dd"); }`
- **正例**: `DateTimeFormatter df = DateTimeFormatter.ofPattern("yyyy-MM-dd");`
- **触发条件**: 在for/while高频循环体内new创建对象，如new SimpleDateFormat/new DateFormat等
- **严重程度**: minor

### JAVA-PERF-004: 内存使用与GC压力

- **检查锚点**: static集合只add无remove, 循环内new大对象(大List/byte[]/Bitmap), System.gc()调用, 大量临时对象未复用
- **反例**: `private static List<EventListener> listeners = new ArrayList<>(); // 只add不移除, 导致内存泄漏`
- **正例**: `private static final Set<EventListener> listeners = new ConcurrentHashMap<EventListener, Boolean>().keySet(true);`, 或使用WeakHashMap, 及时remove不再需要的引用
- **触发条件**: static集合只add无remove导致内存泄漏，或循环内new大对象(大List/byte[]/Bitmap)，或System.gc()调用，或大量临时对象未复用
- **严重程度**: major

### JAVA-PERF-005: 并发与锁

- **检查锚点**: synchronized方法/块粒度过大(包裹耗时IO), 多个锁获取顺序不一致, HashMap在多线程中读写
- **反例**: `public synchronized void process() { db.query(); // 耗时IO在锁内 cache.compute(); }`, `// 线程A: lock1.lock(); lock2.lock(); 线程B: lock2.lock(); lock1.lock(); // 死锁`
- **正例**: 缩小锁粒度: `db.query(); synchronized(this) { cache.compute(); }`, 统一锁获取顺序, 使用ConcurrentHashMap替代HashMap
- **触发条件**: synchronized方法/块粒度过大(包裹耗时IO)，或多个锁获取顺序不一致，或HashMap在多线程中读写
- **严重程度**: major

### JAVA-CON-001: 禁止对共享可变状态无同步访问

- **检查锚点**: static可变集合在多线程中读写, 非volatile/Atomic的static变量在多线程中读写
- **反例**: `private static Map<String, Object> cache = new HashMap<>();`
- **正例**: `private static final ConcurrentHashMap<String, Object> cache = new ConcurrentHashMap<>();`
- **触发条件**: static可变集合(如HashMap)在多线程中读写，或非volatile/Atomic的static变量在多线程中读写
- **严重程度**: major

### JAVA-CON-002: 使用Lock对象时必须在finally块中释放锁

- **检查锚点**: Lock.lock(), ReentrantLock, try块中使用锁
- **反例**: `lock.lock(); if(condition) { return; } lock.unlock();`
- **正例**: `lock.lock(); try { ... } finally { lock.unlock(); }`
- **触发条件**: 代码中出现Lock.lock()/ReentrantLock.lock()调用但未在finally块中释放锁，异常路径可能死锁
- **严重程度**: major

### JAVA-CON-003: 使用ThreadLocal传递业务状态时必须在finally块中清理

- **检查锚点**: ThreadLocalUtils.putData, ThreadLocalUtils.getData
- **反例**: `ThreadLocalUtils.putData(KEY, value); // 使用后未清理`
- **正例**: `try { ThreadLocalUtils.putData(KEY, value); } finally { ThreadLocalUtils.remove(KEY); }`
- **触发条件**: 代码中出现ThreadLocalUtils.putData或ThreadLocal.set()但未在finally块中清理，线程池复用时导致数据泄漏
- **严重程度**: major

### JAVA-PERF-006: 线程池使用

- **检查锚点**: Executors.newFixedThreadPool/newCachedThreadPool(无界队列), 线程池未命名(难以排查问题), 拒绝策略使用默认AbortPolicy
- **反例**: `ExecutorService pool = Executors.newFixedThreadPool(10); // LinkedBlockingQueue无界, 可能OOM`
- **正例**: `new ThreadPoolExecutor(5, 10, 60L, TimeUnit.SECONDS, new ArrayBlockingQueue<>(1000), new NamedThreadFactory("order-process"), new ThreadPoolExecutor.CallerRunsPolicy());`
- **触发条件**: 使用Executors.newFixedThreadPool/newCachedThreadPool(无界队列可能导致OOM)，或线程池未命名，或拒绝策略使用默认AbortPolicy
- **严重程度**: major

### JAVA-PERF-007: 资源管理

- **检查锚点**: InputStream/OutputStream/Connection未在finally关闭, try-catch-finally中close()未处理异常, Connection未归还连接池
- **反例**: `InputStream is = new FileInputStream(path); // 使用后未关闭`, `try { ... } finally { conn.close(); // close本身可能抛异常 }`
- **正例**: `try (InputStream is = new FileInputStream(path); BufferedReader br = new BufferedReader(new InputStreamReader(is))) { ... }`
- **触发条件**: InputStream/OutputStream/Connection未在finally或try-with-resources中关闭，或Connection未归还连接池
- **严重程度**: major

### JAVA-PERF-008: 数据库交互

- **检查锚点**: MongoDB查询字段无索引(explain显示COLLSCAN), 查询结果全量拉取到内存, Java原生序列化(ObjectOutputStream)
- **反例**: `mongoCollection.find(eq("status", "ACTIVE")).into(new ArrayList<>()); // 全量加载`, `new ObjectOutputStream(new FileOutputStream(file)).writeObject(data); // Java原生序列化性能差`
- **正例**: 分页查询: `mongoCollection.find(eq("status", "ACTIVE")).skip(0).limit(100);`, 使用Protobuf/Kryo等高性能序列化
- **触发条件**: MongoDB查询字段无索引(explain显示COLLSCAN)，或查询结果全量拉取到内存，或使用Java原生序列化(ObjectOutputStream)
- **严重程度**: major

---

## 五、安全编码

### JAVA-SEC-001: 禁止硬编码密码和密钥

- **检查锚点**: password=, pwd=, secret=, token=, apiKey=
- **反例**: `String password = "admin123";`
- **正例**: `String password = System.getenv("DB_PASSWORD");`
- **触发条件**: 代码中出现password=/pwd=/secret=/token=/apiKey=等硬编码密码和密钥的赋值
- **严重程度**: fatal

### JAVA-SEC-002: 禁止使用不安全的随机数生成器

- **检查锚点**: new Random(), Math.random()
- **正例**: `SecureRandom sr = new SecureRandom();`
- **触发条件**: 代码中出现new Random()或Math.random()用于安全相关场景，应使用SecureRandom
- **严重程度**: major

### JAVA-SEC-003: 外部参数校验

- **检查锚点**: @RequestBody/@RequestParam参数直接使用未校验, REST接口入参未做长度/格式/范围校验
- **反例**: `@PostMapping public Result create(@RequestBody UserReq req) { userService.create(req); // req字段未校验 }`
- **正例**: `@PostMapping public Result create(@RequestBody @Valid UserReq req) { userService.create(req); }`, UserReq中使用 `@NotBlank @Size(max=50)` 等注解约束
- **触发条件**: @RequestBody/@RequestParam参数直接使用未校验，或REST接口入参未做长度/格式/范围校验
- **严重程度**: major

### JAVA-SEC-004: 敏感信息防泄漏

- **检查锚点**: @ToString注解在含password/secret字段的类上, 日志打印整个对象含敏感字段, 错误响应暴露堆栈信息
- **反例**: `@Data @ToString public class UserDTO { private String username; private String password; private String idCard; }`, `log.info("用户信息: {}", userDTO); // 打印含密码的toString`
- **正例**: `@Getter @ToString(exclude = {"password", "idCard"}) public class UserDTO { private String username; @ToString.Exclude private String password; @ToString.Exclude private String idCard; }`
- **触发条件**: @ToString注解在含password/secret字段的类上，或日志打印整个对象含敏感字段，或错误响应暴露堆栈信息
- **严重程度**: major

### JAVA-SEC-005: SQL注入防护

- **检查锚点**: SQL字符串拼接, ${param}在MyBatis mapper中(非#{param}), Statement.executeQuery(sql)拼接参数
- **反例**: `String sql = "SELECT * FROM user WHERE name = '" + name + "'"; statement.executeQuery(sql);`, MyBatis: `WHERE name = '${name}'`
- **正例**: `PreparedStatement ps = conn.prepareStatement("SELECT * FROM user WHERE name = ?"); ps.setString(1, name);`, MyBatis: `WHERE name = #{name}`
- **触发条件**: SQL字符串拼接用户输入，或MyBatis mapper中使用${param}(非#{param})，或Statement.executeQuery(sql)拼接参数
- **严重程度**: fatal

### JAVA-SEC-006: 序列化与反序列化安全

- **检查锚点**: ObjectInputStream.readObject()反序列化不可信数据, Serializable类未声明serialVersionUID, 敏感字段未标记transient
- **反例**: `ObjectInputStream ois = new ObjectInputStream(new FileInputStream(file)); Object obj = ois.readObject(); // 不可信数据可导致RCE`
- **正例**: 使用白名单过滤: `ObjectInputStream ois = new ObjectInputStream(input) { @Override protected Class<?> resolveClass(ObjectStreamClass desc) { if (!ALLOWED_CLASSES.contains(desc.getName())) throw new InvalidClassException("未授权类", desc.getName()); return super.resolveClass(desc); } };`, 实现`Serializable`的类声明 `private static final long serialVersionUID = 1L;`, 敏感字段标记 `transient`
- **触发条件**: ObjectInputStream.readObject()反序列化不可信数据可导致RCE，或Serializable类未声明serialVersionUID，或敏感字段未标记transient
- **严重程度**: fatal

### JAVA-SEC-007: 高危数据库操作

- **检查锚点**: dropDatabase(), collection.drop(), deleteMany({}), deleteMany(new Document()), 无过滤条件的remove/delete操作
- **反例**: `mongoCollection.deleteMany(new Document()); // 删除全部数据`, `db.dropDatabase();`
- **正例**: 执行前先计数验证: `long count = mongoCollection.countDocuments(filter); if (count > MAX_THRESHOLD) { throw new BizException("删除数量超限: " + count); } mongoCollection.deleteMany(filter);`
- **触发条件**: 代码中出现dropDatabase()/collection.drop()/deleteMany({})/deleteMany(new Document())，或无过滤条件的remove/delete操作
- **严重程度**: fatal

### JAVA-SEC-008: 依赖安全

- **检查锚点**: pom.xml中依赖版本过旧(CVE已知漏洞), 使用LATEST/SNAPSHOT版本号, 传递性依赖含已知漏洞(如log4j 2.x < 2.17)
- **反例**: `<dependency><groupId>org.apache.logging.log4j</groupId><artifactId>log4j-core</artifactId><version>2.14.0</version></dependency>`, `<version>LATEST</version>`
- **正例**: 使用OWASP Dependency-Check或Snyk扫描依赖, 锁定具体安全版本: `<version>2.17.1</version>`, 使用`<dependencyManagement>`统一管理版本
- **触发条件**: pom.xml中依赖版本过旧(存在已知CVE漏洞)，或使用LATEST/SNAPSHOT版本号，或传递性依赖含已知漏洞(如log4j 2.x < 2.17)
- **严重程度**: major

---

## 六、易错点

### JAVA-COM-001: MyBatis动态SQL连续字段更新时必须在末尾添加逗号

- **检查锚点**: MyBatis的trim标签内多个set字段
- **反例**: 两个字段都满足条件时缺少逗号
- **正例**: 每个非末尾字段添加逗号
- **触发条件**: MyBatis的trim/set标签内多个动态字段更新时字段间缺少逗号分隔，多字段同时满足条件时SQL语法错误
- **严重程度**: major

### JAVA-COM-002: Stream.toMap必须处理key重复场景

- **检查锚点**: .collect(Collectors.toMap(...))
- **反例**: `stream.collect(Collectors.toMap(Object::getKey, obj -> obj))` - key重复时抛IllegalStateException
- **正例**: `stream.collect(Collectors.toMap(Object::getKey, obj -> obj, (v1, v2) -> v2))`
- **触发条件**: 代码中使用.collect(Collectors.toMap(...))但未提供merge函数处理key重复，key重复时抛IllegalStateException
- **严重程度**: major

### JAVA-COM-003: JSON解析后必须空检查

- **检查锚点**: JSONObject.parseObject, getJSONArray, getJSONObject
- **反例**: `response.getJSONArray("data").getJSONObject(0)`
- **正例**: `JSONArray arr = JSONObject.parseObject(content).getJSONArray("data"); if (arr != null) { ... }`
- **触发条件**: JSONObject.parseObject/getJSONArray/getJSONObject解析后直接链式访问，未对null结果进行检查
- **严重程度**: major

### JAVA-COM-004: 处理外部响应数据时必须空指针检查

- **检查锚点**: 访问RPC/REST/数据库等外部响应数据的属性
- **反例**: 直接链式调用无判空
- **正例**: `if (data != null && data.getId() != null)`
- **触发条件**: 访问RPC/REST/数据库等外部响应数据的属性时直接链式调用无判空
- **严重程度**: major

### JAVA-COM-005: 从Map中取值后必须检查key是否存在

- **检查锚点**: map.get(key).getXxx()
- **反例**: `Integer.parseInt(pathIndex2ServiceTPMap.get(pathIndexKey).getOsuLabel())`
- **正例**: `ServiceTP serviceTP = pathIndex2ServiceTPMap.get(pathIndexKey); if (serviceTP != null) { ... }`
- **触发条件**: map.get(key)后直接调用.getXxx()方法，key不存在时返回null导致NullPointerException
- **严重程度**: major

### JAVA-COM-006: 链式调用getXxx().getYyy()前必须null检查

- **检查锚点**: 对象链式调用
- **反例**: `service.getSnkTP().getOsuLabel()`
- **正例**: `if (service.getSnkTP() != null && service.getSnkTP().getOsuLabel() != null) { ... }`
- **触发条件**: 对象链式调用getXxx().getYyy()前未对中间对象做null检查
- **严重程度**: major

### JAVA-COM-007: 遍历集合前必须检查null或空

- **检查锚点**: CollectionUtils.isNotEmpty(), endpoints.stream()
- **反例**: `if (tpList != null) { tpList.stream()... }`（遗漏了空集合判断）
- **正例**: `if (CollectionUtils.isNotEmpty(tpList)) { tpList.stream()... }`
- **触发条件**: 遍历集合前仅检查null未检查空集合，或集合为null时直接调用stream()/for-each
- **严重程度**: major

### JAVA-COM-008: List下标获取元素前必须边界检查

- **检查锚点**: list.get(0), list.get(index)
- **反例**: `String first = list.get(0);`
- **正例**: `if (!list.isEmpty()) { String first = list.get(0); }`
- **触发条件**: list.get(0)或list.get(index)未先检查isEmpty()或index < list.size()，可能抛IndexOutOfBoundsException
- **严重程度**: major

### JAVA-COM-009: 批量数据库操作必须分批处理

- **检查锚点**: batchDelete/batchUpdate/for循环删除
- **反例**: 一次处理全部数据
- **正例**: `Lists.partition(serviceUuids, MAX_UPDATE_SIZE)` 分批处理
- **触发条件**: batchDelete/batchUpdate/for循环删除等批量数据库操作一次处理全部数据，数据量过大可能导致超时或OOM
- **严重程度**: major

### JAVA-COM-010: 批量数据库操作必须按固定顺序排序避免死锁

- **检查锚点**: batchModify, batchDelete, 多线程并发批量操作
- **正例**: 批量操作前按业务UUID或ID排序，确保所有线程以相同顺序访问资源
- **触发条件**: batchModify/batchDelete等多线程并发批量操作时未按固定顺序排序，不同线程以不同顺序访问资源可能死锁
- **严重程度**: major

---

## 七、单元测试与可测试性

### JAVA-TEST-001: 测试技术栈

- **检查锚点**: import junit.framework.TestCase(JUnit3), import org.junit.Test(JUnit4), 未使用AssertJ的assertThat
- **反例**: `import junit.framework.TestCase; public class UserTest extends TestCase { public void testCreate() { assertEquals("a", "a"); } }`
- **正例**: `import org.junit.jupiter.api.Test; import static org.assertj.core.api.Assertions.assertThat; class UserTest { @Test void shouldReturnUser_whenIdExists() { assertThat(user.getName()).isEqualTo("Alice"); } }`
- **触发条件**: import junit.framework.TestCase(JUnit3)或import org.junit.Test(JUnit4)，或未使用AssertJ的assertThat
- **严重程度**: minor

### JAVA-TEST-002: 断言正确性与清晰度

- **检查锚点**: assertTrue/assertFalse无断言消息, try-catch中fail()断言异常, assertEquals参数顺序颠倒(expected, actual)
- **反例**: `try { service.process(invalidInput); fail(); } catch (BizException e) { assertEquals("error", e.getMessage()); }`
- **正例**: `BizException ex = assertThrows(BizException.class, () -> service.process(invalidInput)); assertThat(ex.getMessage()).isEqualTo("error");`
- **触发条件**: assertTrue/assertFalse无断言消息，或try-catch中fail()断言异常，或assertEquals参数顺序颠倒(expected, actual)
- **严重程度**: minor

### JAVA-TEST-003: 禁止Mock被测对象本身

- **检查锚点**: @InjectMocks和@Spy同时用在同一类, 对SUT的方法调用mockito.when().thenReturn()
- **反例**: `@InjectMocks @Spy UserService userService; @Test void test() { doReturn(true).when(userService).checkPermission(any()); // mock了被测对象的方法 }`
- **正例**: `@InjectMocks UserService userService; @Mock PermissionDao permissionDao; @Test void test() { when(permissionDao.hasPermission(any())).thenReturn(true); // mock依赖而非SUT }`
- **触发条件**: @InjectMocks和@Spy同时用在同一类，或对SUT的方法调用mockito.when().thenReturn()mock了被测对象本身
- **严重程度**: major

### JAVA-TEST-004: 警惕全局状态与静态依赖

- **检查锚点**: 代码中直接调用Singleton.getInstance(), 静态方法访问外部依赖(如Database.query()), System.setProperty()修改全局配置
- **反例**: `public class UserService { public User find(String id) { return CacheManager.getInstance().get(id); // 全局单例 } }`
- **正例**: `public class UserService { private final Cache cache; public UserService(Cache cache) { this.cache = cache; } public User find(String id) { return cache.get(id); } }`
- **触发条件**: 代码中直接调用Singleton.getInstance()，或静态方法访问外部依赖(如Database.query())，或System.setProperty()修改全局配置
- **严重程度**: minor

### JAVA-TEST-005: 警惕过度使用PowerMock

- **检查锚点**: import org.powermock.*, @PrepareForTest注解, @RunWith(PowerMockRunner.class)
- **反例**: `@RunWith(PowerMockRunner.class) @PrepareForTest({StaticUtil.class, NewOperator.class}) class UserServiceTest { @Test void test() { PowerMockito.mockStatic(StaticUtil.class); PowerMockito.whenNew(Dao.class).withNoArguments().thenReturn(mockDao); } }`
- **正例**: 重构代码: 将静态调用提取为实例方法并注入依赖, 使用Mockito的mockStatic(3.4+)替代PowerMock, 设计可测试的代码而非依赖PowerMock
- **触发条件**: import org.powermock.*，或@PrepareForTest注解，或@RunWith(PowerMockRunner.class)
- **严重程度**: minor

### JAVA-TEST-006: 参数化测试

- **检查锚点**: 多个@Test方法仅输入和预期值不同, 测试方法名含数字后缀(testCase1/testCase2), 相同测试逻辑复制粘贴
- **反例**: `@Test void testAdd_positive() { assertEquals(3, calc.add(1, 2)); } @Test void testAdd_negative() { assertEquals(-3, calc.add(-1, -2)); } @Test void testAdd_zero() { assertEquals(0, calc.add(0, 0)); }`
- **正例**: `@ParameterizedTest @CsvSource({"1,2,3", "-1,-2,-3", "0,0,0"}) void shouldReturnSum_whenAdd(int a, int b, int expected) { assertThat(calc.add(a, b)).isEqualTo(expected); }`
- **触发条件**: 多个@Test方法仅输入和预期值不同，或测试方法名含数字后缀(testCase1/testCase2)，或相同测试逻辑复制粘贴
- **严重程度**: suggestion

### JAVA-TEST-007: 序列化兼容性测试

- **检查锚点**: 类实现Serializable但无序列化测试, serialVersionUID被修改但无回归测试
- **反例**: `public class UserDTO implements Serializable { private static final long serialVersionUID = 1L; private String name; // 无序列化兼容性测试 }`
- **正例**: `@Test void shouldPreserveState_afterSerializationRoundTrip() { UserDTO original = new UserDTO("Alice"); UserDTO restored = serializeAndDeserialize(original); assertThat(restored).usingRecursiveComparison().isEqualTo(original); }`
- **触发条件**: 类实现Serializable但无序列化兼容性测试，或serialVersionUID被修改但无回归测试
- **严重程度**: minor

### JAVA-TEST-008: 禁止在测试中使用Thread.sleep

- **检查锚点**: Thread.sleep(在测试代码中), TimeUnit.SECONDS.sleep(在测试代码中)
- **反例**: `@Test void testAsync() { service.asyncProcess(); Thread.sleep(3000); assertThat(result).isNotNull(); // 不稳定, 3秒可能不够 }`
- **正例**: `@Test void testAsync() { service.asyncProcess(); await().atMost(5, SECONDS).until(() -> result != null); assertThat(result).isNotNull(); }`, 或 `verify(mockDao, timeout(3000)).save(any());`
- **触发条件**: 测试代码中出现Thread.sleep()或TimeUnit.SECONDS.sleep()，导致测试不稳定且执行缓慢
- **严重程度**: minor

### JAVA-TEST-009: 测试数据规模

- **检查锚点**: 测试中for循环创建大量对象(>10), 测试数据列表包含几十条记录, 使用Random生成随机测试数据
- **反例**: `List<User> users = new ArrayList<>(); for (int i = 0; i < 1000; i++) { users.add(new User("user" + i)); }`
- **正例**: `List<User> users = List.of(new User("Alice"), new User("Bob"), new User("Charlie")); // 最小且具代表性的数据集`
- **触发条件**: 测试中for循环创建大量对象(>10)，或测试数据列表包含几十条记录，或使用Random生成随机测试数据
- **严重程度**: suggestion

### JAVA-TEST-010: 避免不必要的IO操作

- **检查锚点**: 测试中读取本地文件(new FileInputStream), 测试中启动真实HTTP服务, 测试中连接真实数据库
- **反例**: `@Test void testParse() { String content = new String(Files.readAllBytes(Paths.get("src/test/resources/data.json"))); // IO操作 }`
- **正例**: `@Test void testParse() { String content = "{\"name\":\"Alice\"}"; // 内联测试数据 }`, 或 `@Mock FileService fileService; when(fileService.readContent(any())).thenReturn("{\"name\":\"Alice\"}");`
- **触发条件**: 测试中读取本地文件(new FileInputStream)，或测试中启动真实HTTP服务，或测试中连接真实数据库
- **严重程度**: suggestion

---

## 八、构建、部署与环境配置

### JAVA-BUILD-001: 服务器配置显式化

- **检查锚点**: application.yml/properties中依赖内嵌服务器默认值, 未显式配置server.port/timeout/thread-pool等参数, 使用@SpringBootApplication默认配置未覆盖
- **反例**: `@SpringBootApplication public class App { public static void main(String[] args) { SpringApplication.run(App.class, args); } } // 全部依赖默认配置`
- **正例**: `server.port=8080 server.tomcat.max-threads=200 server.tomcat.connection-timeout=5000ms server.tomcat.max-connections=10000 spring.datasource.hikari.maximum-pool-size=20`
- **触发条件**: application.yml/properties中依赖内嵌服务器默认值，未显式配置server.port/timeout/thread-pool等参数
- **严重程度**: major

### JAVA-BUILD-002: 依赖管理

- **检查锚点**: pom.xml中使用LATEST/SNAPSHOT版本号, 无<dependencyManagement>统一版本, 声明但未使用的依赖, 依赖版本冲突(mvn dependency:tree显示)
- **反例**: `<dependency><groupId>com.google.guava</groupId><artifactId>guava</artifactId><version>LATEST</version></dependency>`, 多模块各自声明不同版本的同一依赖
- **正例**: 父pom中使用 `<dependencyManagement>` 统一版本: `<dependencyManagement><dependencies><dependency><groupId>com.google.guava</groupId><artifactId>guava</artifactId><version>31.1-jre</version></dependency></dependencies></dependencyManagement>`, 子模块不指定version, 使用 `mvn dependency:analyze` 清理未使用依赖
- **触发条件**: pom.xml中使用LATEST/SNAPSHOT版本号，或无<dependencyManagement>统一版本，或声明但未使用的依赖，或依赖版本冲突
- **严重程度**: minor

### JAVA-BUILD-003: 容器化配置

- **检查锚点**: Dockerfile中FROM xxx:latest, 镜像中硬编码配置(数据库地址/密码), 以root用户运行容器, Dockerfile中未设置HEALTHCHECK
- **反例**: `FROM openjdk:latest COPY app.jar /app.jar ENTRYPOINT ["java", "-jar", "/app.jar", "--db.host=10.0.0.1", "--db.password=secret"]`
- **正例**: `FROM openjdk:17-jdk-slim WORKDIR /app COPY app.jar . USER nonroot ENTRYPOINT ["java", "-jar", "app.jar"] HEALTHCHECK CMD curl -f http://localhost:8080/actuator/health || exit 1`, 配置通过环境变量注入: `DB_HOST`, `DB_PASSWORD`
- **触发条件**: Dockerfile中FROM xxx:latest，或镜像中硬编码配置(数据库地址/密码)，或以root用户运行容器，或Dockerfile中未设置HEALTHCHECK
- **严重程度**: major
