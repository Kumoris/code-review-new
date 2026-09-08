# 跨语言通用检视规则

> 来源：既有检视规则去重合并；规则与代码托管平台无关

---

## 目录

- [一、通用审查策略](#一通用审查策略)
- [二、架构设计与代码结构](#二架构设计与代码结构)
  - [COM-ARCH-001: SOLID原则](#com-arch-001-solid原则)
  - [COM-ARCH-002: 依赖注入](#com-arch-002-依赖注入)
  - [COM-ARCH-003: 分层与职责](#com-arch-003-分层与职责)
  - [COM-ARCH-004: 模块化与耦合度](#com-arch-004-模块化与耦合度)
  - [COM-ARCH-005: 设计模式的应用](#com-arch-005-设计模式的应用)
  - [COM-ARCH-006: 避免全局可变状态](#com-arch-006-避免全局可变状态)
- [三、代码实现与可读性](#三代码实现与可读性)
  - [COM-CODE-001: 命名规范](#com-code-001-命名规范)
  - [COM-CODE-002: 注释质量](#com-code-002-注释质量)
  - [COM-CODE-003: 代码简洁性](#com-code-003-代码简洁性)
  - [COM-CODE-004: 异常处理](#com-code-004-异常处理)
  - [COM-CODE-005: DRY - Don't Repeat Yourself](#com-code-005-dry---dont-repeat-yourself)
  - [COM-CODE-006: 日志规范](#com-code-006-日志规范)
- [四、性能与资源管理](#四性能与资源管理)
  - [COM-PERF-001: 循环中拼接字符串](#com-perf-001-循环中拼接字符串)
  - [COM-PERF-002: N+1数据库查询](#com-perf-002-n1数据库查询)
  - [COM-PERF-003: 资源管理](#com-perf-003-资源管理)
  - [COM-PERF-004: 不必要的对象创建](#com-perf-004-不必要的对象创建)
- [五、安全编码](#五安全编码)
  - [COM-SEC-001: 禁止硬编码凭证](#com-sec-001-禁止硬编码凭证)
  - [COM-SEC-002: 外部参数校验](#com-sec-002-外部参数校验)
  - [COM-SEC-003: SQL注入防护](#com-sec-003-sql注入防护)
  - [COM-SEC-004: 敏感信息防泄漏](#com-sec-004-敏感信息防泄漏)
  - [COM-SEC-005: 不安全加密算法](#com-sec-005-不安全加密算法)
  - [COM-SEC-006: 依赖安全](#com-sec-006-依赖安全)
  - [COM-SEC-007: 命令注入防护](#com-sec-007-命令注入防护)
  - [COM-SEC-008: 禁止禁用TLS/SSL证书验证](#com-sec-008-禁止禁用tlsssl证书验证)
  - [COM-SEC-009: 不安全反序列化](#com-sec-009-不安全反序列化)
  - [COM-SEC-010: 必须使用安全密码哈希](#com-sec-010-必须使用安全密码哈希)
- [六、单元测试与可测试性](#六单元测试与可测试性)
  - [COM-TEST-001: 测试覆盖](#com-test-001-测试覆盖)
  - [COM-TEST-002: 禁止Mock被测对象本身](#com-test-002-禁止mock被测对象本身)
  - [COM-TEST-003: 测试独立性](#com-test-003-测试独立性)
  - [COM-TEST-004: 禁止在测试中使用sleep](#com-test-004-禁止在测试中使用sleep)
  - [COM-TEST-005: 避免不必要的IO操作](#com-test-005-避免不必要的io操作)
- [七、构建、部署与环境配置](#七构建部署与环境配置)
  - [COM-BUILD-001: 服务器配置显式化](#com-build-001-服务器配置显式化)
  - [COM-BUILD-002: 依赖管理](#com-build-002-依赖管理)
  - [COM-BUILD-003: 容器化配置](#com-build-003-容器化配置)
- [八、业务相关通用规则](#八业务相关通用规则)
  - [COM-BIZ-001: 性能优化类修改必须验证数据一致性](#com-biz-001-性能优化类修改必须验证数据一致性)
  - [COM-BIZ-002: 进行除法或模运算前必须判断除数是否为零](#com-biz-002-进行除法或模运算前必须判断除数是否为零)
- [九、严重级别判定](#九严重级别判定)

---

## 一、通用审查策略

1. **优先理解意图**：首先通读代码，理解其业务逻辑和设计意图。代码是为业务服务的。
2. **从宏观到微观**：先评估整体架构和设计是否合理，再深入到具体的实现细节、命名和语法。
3. **权衡与取舍**：理解没有绝对完美的标准。当"简洁性"与"可扩展性"冲突时，要能根据上下文判断哪一个更重要。
4. **关注"代码的坏味道"**：对重复代码、过长方法/函数、过大类、复杂的条件判断等保持高度敏感。

---

## 二、架构设计与代码结构

### COM-ARCH-001: SOLID原则

- **检查锚点**: 类拥有多个不相关职责的方法, 接口方法数超过5个且调用方只使用部分方法, 子类覆写父类方法抛出UnsupportedOperationException, new具体类出现在业务逻辑中, if/switch按类型分支选择不同行为
- **反例**:
  ```java
  class UserManager {
      void createUser() { ... }
      void generateReport() { ... }   // 与用户管理无关的职责
      void sendEmail() { ... }        // 与用户管理无关的职责
  }
  ```
- **正例**:
  ```java
  class UserManager { void createUser() { ... } }
  class ReportService { void generateReport() { ... } }
  class EmailService { void sendEmail() { ... } }
  ```
- **触发条件**: 类拥有多个不相关职责的方法, 接口方法数超过5个且调用方只使用部分方法, 子类覆写父类方法抛出UnsupportedOperationException, new具体类出现在业务逻辑中, if/switch按类型分支选择不同行为
- **严重程度**: major

### COM-ARCH-002: 依赖注入

- **检查锚点**: `new` 具体实现类出现在业务逻辑中, 构造函数无接口参数, 测试时无法替换外部依赖
- **反例**:
  ```java
  class OrderService {
      void process(Order order) {
          PaymentGateway gateway = new StripeGateway();  // 直接依赖具体实现
          gateway.charge(order.getAmount());
      }
  }
  ```
- **正例**:
  ```java
  class OrderService {
      private final PaymentGateway gateway;  // 依赖接口
      OrderService(PaymentGateway gateway) { this.gateway = gateway; }  // 构造函数注入
      void process(Order order) { gateway.charge(order.getAmount()); }
  }
- **触发条件**: `new` 具体实现类出现在业务逻辑中, 构造函数无接口参数, 测试时无法替换外部依赖
- **严重程度**: major
  ```

### COM-ARCH-003: 分层与职责

- **检查锚点**: Controller/Handler中包含业务计算逻辑, Service层直接操作SQL/ORM, DTO/Entity中包含业务方法
- **反例**:
  ```java
  @RestController
  class UserController {
      @PostMapping("/users")
      User create(@RequestBody UserReq req) {
          if (req.getAge() < 18) throw new BizException("未成年");  // 业务逻辑在Controller
          return userRepository.save(req);  // 直接操作数据层
      }
  }
  ```
- **正例**:
  ```java
  @RestController
  class UserController {
      @PostMapping("/users")
      User create(@RequestBody UserReq req) { return userService.createUser(req); }
  }
  class UserService {
      User createUser(UserReq req) {
          if (req.getAge() < 18) throw new BizException("未成年");
          return userRepository.save(req);
      }
  }
- **触发条件**: Controller/Handler中包含业务计算逻辑, Service层直接操作SQL/ORM, DTO/Entity中包含业务方法
- **严重程度**: major
  ```

### COM-ARCH-004: 模块化与耦合度

- **检查锚点**: 模块间存在循环import/require, 一个类修改引发多模块连锁修改, 模块A直接操作模块B的内部数据结构
- **反例**:
  ```python
  # module_a.py
  from module_b import BService
  class AService:
      def do_something(self):
          b = BService()
          b._internal_state = "hacked"  # 直接操作另一个模块的内部状态
  # module_b.py
  from module_a import AService  # 循环依赖
  ```
- **正例**:
  ```python
  # module_a.py
  class AService:
      def __init__(self, b_service: BServiceInterface):
          self._b_service = b_service
      def do_something(self):
          self._b_service.update_state("value")  # 通过公共接口交互
  # 无循环依赖，通过接口解耦
  ```
- **触发条件**: 模块间存在循环import/require, 一个类修改引发多模块连锁修改, 模块A直接操作模块B的内部数据结构
- **严重程度**: major

### COM-ARCH-005: 设计模式的应用

- **检查锚点**: 大量if/else或switch按类型分支, 相同构造逻辑散落多处, 新增类型需修改已有代码(OCP违反), 简单问题引入过多抽象层
- **反例**:
  ```java
  // 每增加一种通知方式都要修改此类
  void notify(String type, String msg) {
      if (type.equals("email")) { emailSender.send(msg); }
      else if (type.equals("sms")) { smsSender.send(msg); }
      else if (type.equals("push")) { pushSender.send(msg); }
  }
  ```
- **正例**:
  ```java
  interface Notifier { void send(String msg); }
  // 新增通知方式只需实现接口，无需修改已有代码
  void notify(List<Notifier> notifiers, String msg) {
      notifiers.forEach(n -> n.send(msg));
  }
- **触发条件**: 大量if/else或switch按类型分支, 相同构造逻辑散落多处, 新增类型需修改已有代码(OCP违反), 简单问题引入过多抽象层
- **严重程度**: minor
  ```

### COM-ARCH-006: 避免全局可变状态

- **检查锚点**: 模块级/类级可变变量(static mutable field), 全局字典/Map被多处读写, 单例中持有可变状态
- **反例**:
  ```python
  # 模块级全局可变状态，任何地方都能修改
  _global_cache = {}
  def set_cache(key, val): _global_cache[key] = val
  def get_cache(key): return _global_cache[key]
  ```
- **正例**:
  ```python
  class CacheService:
      def __init__(self):
          self._cache = {}  # 实例级状态，通过依赖注入管理
      def set(self, key, val): self._cache[key] = val
      def get(self, key): return self._cache[key]
  # 通过构造函数注入CacheService实例
  ```
- **触发条件**: 模块级/类级可变变量(static mutable field), 全局字典/Map被多处读写, 单例中持有可变状态
- **严重程度**: major

### COM-ARCH-007: 枚举/常量扩展性检查

- **检查锚点**: 新增枚举值或新增int/String常量到已有常量组, if/switch/三元表达式按枚举/常量值分支, 新增值后已有条件判断未同步更新
- **反例**:
  ```java
  // 原有: POLICY_CREATE=0, POLICY_UPDATE=1, POLICY_FAKE=3
  // 新增: POLICY_UPDATE_DISABLE=5, POLICY_UPDATE_ENABLE=6
  // 但校验器中的if只检查了POLICY_CREATE和POLICY_UPDATE，新增值被跳过
  if (action == POLICY_CREATE || action == POLICY_UPDATE) {
      doValidation();  // 新增值5/6不会进入此分支，校验被绕过
  }
  ```
- **正例**:
  ```java
  // 方案1: 使用枚举+switch，编译器强制穷举检查
  switch (action) {
      case POLICY_CREATE: case POLICY_UPDATE:
      case POLICY_UPDATE_DISABLE: case POLICY_UPDATE_ENABLE:
          doValidation(); break;
      case POLICY_FAKE: break;  // 不需要校验
      default: throw new IllegalArgumentException("Unknown action: " + action);
  }
  // 方案2: 若必须用int常量，新增值时必须grep所有if/switch引用处
  ```
- **触发条件**: diff中新增枚举值或新增常量到已有常量组，且该枚举/常量在代码中用于if/switch/三元表达式条件判断
- **严重程度**: major

### COM-ARCH-008: 枚举/常量传递后的调用链影响分析

- **检查锚点**: 新增枚举值或常量作为参数传递给其他方法, 被调用方法内部根据参数值走不同逻辑分支, 新增值在被调用方法中未被正确处理
- **反例**:
  ```java
  // 调用方新增了POLICY_UPDATE_ENABLE_WIFI传给checkParam
  tuneupPolicyCheck.checkParam(context, issuePolicyInfo, PolicyConstant.POLICY_UPDATE_ENABLE_WIFI);
  
  // 但checkParam内部调用的checkWholeNetworkPolicy只处理了POLICY_CREATE和POLICY_UPDATE
  // POLICY_UPDATE_ENABLE_WIFI被跳过，全网校验被绕过
  private boolean checkWholeNetworkPolicy(int action, ...) {
      if (action == POLICY_CREATE || action == POLICY_UPDATE) {
          return validate(...);
      }
      return true;  // 其他action直接返回true——新增值绕过了校验
  }
  ```
- **正例**:
  ```java
  // checkWholeNetworkPolicy中显式处理新增值
  private boolean checkWholeNetworkPolicy(int action, ...) {
      if (action == POLICY_CREATE || action == POLICY_UPDATE
          || action == POLICY_UPDATE_ENABLE_WIFI) {
          return validate(...);
      }
      if (action == POLICY_FAKE || action == POLICY_UPDATE_DISABLE_WIFI) {
          return true;  // 明确不需要校验的值
      }
      throw new IllegalArgumentException("Unhandled action: " + action);
  }
  ```
- **触发条件**: diff中将新增的枚举值或常量作为参数传递给其他方法，且被调用方法内部存在基于该参数值的条件分支逻辑
- **严重程度**: major

---

## 三、代码实现与可读性

### COM-CODE-001: 命名规范

- **检查锚点**: 变量名为`data`, `temp`, `info`, `result`, `handle`, `flag`, `x1/x2`, 缩写未通用认可(如`usrMst`), 测试方法名为`test1`, `testMethod`
- **反例**:
  ```java
  int d;  // elapsed time in days
  List<User> list1;
  void handle() { ... }
  @Test void test1() { ... }
  ```
- **正例**:
  ```java
  int elapsedTimeInDays;
  List<User> activeUsers;
  void processPendingOrders() { ... }
  @Test void shouldRejectOrderWhenInsufficientStock() { ... }
  ```
- **触发条件**: 变量名为`data`, `temp`, `info`, `result`, `handle`, `flag`, `x1/x2`, 缩写未通用认可(如`usrMst`), 测试方法名为`test1`, `testMethod`
- **严重程度**: suggestion

### COM-CODE-002: 注释质量

- **检查锚点**: 注释重复代码本身(如`i++; // i加1`), 注释解释What而非Why, 注释与代码不一致, 被注释掉的代码块
- **反例**:
  ```java
  // 设置价格为100
  price = 100;
  // i++;
  // oldLogic();
  ```
- **正例**:
  ```java
  // 使用100作为默认价格，因合同条款规定新用户首月固定费率
  price = 100;
  // 删除的代码通过版本控制管理，不留在注释中
  ```
- **触发条件**: 注释重复代码本身(如`i++; // i加1`), 注释解释What而非Why, 注释与代码不一致, 被注释掉的代码块
- **严重程度**: suggestion

### COM-CODE-003: 代码简洁性

- **检查锚点**: if-else嵌套超过3层, 代码中出现未命名的字面量(如`3.14`, `"ACTIVE"`), 三元表达式嵌套, 单个方法超过50行
- **反例**:
  ```java
  String getLabel(Status s) {
      if (s != null) {
          if (s.isActive()) {
              if (s.isPremium()) {
                  return "Premium Active";
              } else {
                  return "Normal Active";
              }
          } else {
              return "Inactive";
          }
      } else {
          return "Unknown";
      }
  }
  ```
- **正例**:
  ```java
  String getLabel(Status s) {
      if (s == null) return "Unknown";
      if (!s.isActive()) return "Inactive";
      return s.isPremium() ? "Premium Active" : "Normal Active";
  }
- **触发条件**: if-else嵌套超过3层, 代码中出现未命名的字面量(如`3.14`, `"ACTIVE"`), 三元表达式嵌套, 单个方法超过50行
- **严重程度**: minor
  ```

### COM-CODE-004: 异常处理

- **检查锚点**: `catch (Exception e)`, `except Exception`, 空`catch`/`except`块, 仅打印异常消息`e.getMessage()`后继续执行
- **反例**:
  ```java
  try {
      processOrder(order);
  } catch (Exception e) {
      // 忽略
  }
  ```
  ```python
  try:
      process_order(order)
  except Exception:
      pass  # 吞噬异常
  ```
- **正例**:
  ```java
  try {
      processOrder(order);
  } catch (InsufficientStockException e) {
      logger.error("订单{}库存不足: {}", order.getId(), e.getMessage(), e);
      throw new OrderRejectException(e);
  }
- **触发条件**: `catch (Exception e)`, `except Exception`, 空`catch`/`except`块, 仅打印异常消息`e.getMessage()`后继续执行
- **严重程度**: major
  ```

### COM-CODE-005: DRY - Don't Repeat Yourself

- **检查锚点**: 相同或高度相似的代码块出现2次以上, 相同逻辑通过复制粘贴到多处, 修改一个业务规则需改多处代码
- **反例**:
  ```java
  // 方法A中
  double discount = price * 0.9;
  if (discount > 100) discount = 100;
  // 方法B中（复制粘贴）
  double discount = price * 0.9;
  if (discount > 100) discount = 100;
  ```
- **正例**:
  ```java
  double calculateDiscount(double price) {
      double discount = price * 0.9;
      return Math.min(discount, 100);
  }
  // 方法A和方法B都调用 calculateDiscount(price)
  ```
- **触发条件**: 相同或高度相似的代码块出现2次以上, 相同逻辑通过复制粘贴到多处, 修改一个业务规则需改多处代码
- **严重程度**: minor

### COM-CODE-006: 日志规范

- **检查锚点**: `catch`块中仅`printStackTrace()`或`console.log(e.message)`, 日志中缺失关键业务ID, 循环内`logger.info()`, 使用`ERROR`级别记录非错误信息
- **反例**:
  ```java
  try {
      charge(amount);
  } catch (PaymentFailedException e) {
      log.error("支付失败");  // 缺少订单ID和异常堆栈
  }
  for (Order order : orders) {
      log.info("处理订单: " + order.getId());  // 循环中高频打印INFO
  }
  ```
- **正例**:
  ```java
  try {
      charge(amount);
  } catch (PaymentFailedException e) {
      log.error("订单{}支付失败, 金额:{}", orderId, amount, e);  // 含上下文+异常对象
  }
  log.info("批量处理完成, 总数:{}, 成功:{}", total, success);  // 循环外汇总日志
  ```
- **触发条件**: `catch`块中仅`printStackTrace()`或`console.log(e.message)`, 日志中缺失关键业务ID, 循环内`logger.info()`, 使用`ERROR`级别记录非错误信息
- **严重程度**: minor

---

## 四、性能与资源管理

### COM-PERF-001: 循环中拼接字符串

- **检查锚点**: 循环体内使用`+`或`+=`拼接字符串, `for`/`while`内对String类型做拼接赋值
- **反例**:
  ```java
  String result = "";
  for (String item : items) {
      result += item;  // 每次循环都创建新String对象
  }
  ```
- **正例**:
  ```java
  StringBuilder sb = new StringBuilder();
  for (String item : items) {
      sb.append(item);
  }
  String result = sb.toString();
  ```
  ```python
  result = "".join(items)
  ```
  ```go
  var sb strings.Builder
  for _, item := range items { sb.WriteString(item) }
  result := sb.String()
  ```
- **触发条件**: 循环体内使用`+`或`+=`拼接字符串, `for`/`while`内对String类型做拼接赋值
- **严重程度**: minor

### COM-PERF-002: N+1数据库查询

- **检查锚点**: 循环体内调用数据库查询方法(select/find/getById), 查询次数与集合大小成正比
- **反例**:
  ```java
  for (Long id : userIds) {
      User user = userMapper.selectById(id);  // N次查询
      users.add(user);
  }
  ```
- **正例**:
  ```java
  List<User> users = userMapper.selectBatchIds(userIds);  // 1次批量查询
  ```
- **触发条件**: 循环体内调用数据库查询方法(select/find/getById), 查询次数与集合大小成正比
- **严重程度**: major

### COM-PERF-003: 资源管理

- **检查锚点**: 打开IO流/数据库连接后无对应的close/dispose, 未使用try-with-resources/defer/with/using, 资源关闭放在非finally路径
- **反例**:
  ```java
  InputStream is = new FileInputStream("data.txt");
  // 读取数据...
  is.close();  // 若读取抛异常，close永远不会执行
  ```
- **正例**:
  ```java
  try (InputStream is = new FileInputStream("data.txt")) {
      // 读取数据...
  }  // 自动关闭
  ```
  ```python
  with open("data.txt") as f:
      data = f.read()  # 自动关闭
  ```
  ```go
  f, err := os.Open("data.txt")
  if err != nil { return err }
  defer f.Close()  // 函数返回时自动关闭
  ```
- **触发条件**: 打开IO流/数据库连接后无对应的close/dispose, 未使用try-with-resources/defer/with/using, 资源关闭放在非finally路径
- **严重程度**: major

### COM-PERF-004: 不必要的对象创建

- **检查锚点**: 在高频调用方法内`new`对象, 循环内创建可复用的临时对象, 每次调用都重新解析不变的配置/格式化对象
- **反例**:
  ```java
  String format(Date date) {
      SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");  // 每次调用都创建
      return sdf.format(date);
  }
  ```
- **正例**:
  ```java
  // 方案1: 使用线程安全的DateTimeFormatter(不可变，可复用)
  private static final DateTimeFormatter FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd");
  String format(LocalDate date) { return FMT.format(date); }
  // 方案2: 若必须用SimpleDateFormat，使用ThreadLocal
  ```
- **触发条件**: 在高频调用方法内`new`对象, 循环内创建可复用的临时对象, 每次调用都重新解析不变的配置/格式化对象
- **严重程度**: minor

---

## 五、安全编码

### COM-SEC-001: 禁止硬编码凭证

- **检查锚点**: password=, pwd=, secret=, token=, apiKey=, 硬编码字符串值中包含敏感关键词
- **反例**: `String password = "admin123";`
- **正例**: `String password = System.getenv("DB_PASSWORD");`
- **触发条件**: password=, pwd=, secret=, token=, apiKey=, 硬编码字符串值中包含敏感关键词
- **严重程度**: fatal

### COM-SEC-002: 外部参数校验

- **检查锚点**: 方法参数直接来自HTTP请求/RPC/消息队列且未经校验即进入业务逻辑, 外部输入未做非空/格式/范围检查
- **反例**:
  ```java
  @PostMapping("/transfer")
  void transfer(@RequestBody TransferReq req) {
      accountService.transfer(req.getFrom(), req.getTo(), req.getAmount());  // 未校验
  }
  ```
- **正例**:
  ```java
  @PostMapping("/transfer")
  void transfer(@RequestBody @Valid TransferReq req) {
      // @Valid触发JSR303校验，或手动校验
      if (req.getAmount() == null || req.getAmount().compareTo(BigDecimal.ZERO) <= 0) {
          throw new IllegalArgumentException("转账金额必须大于0");
      }
      accountService.transfer(req.getFrom(), req.getTo(), req.getAmount());
  }
- **触发条件**: 方法参数直接来自HTTP请求/RPC/消息队列且未经校验即进入业务逻辑, 外部输入未做非空/格式/范围检查
- **严重程度**: major
  ```

### COM-SEC-003: SQL注入防护

- **检查锚点**: SQL语句通过字符串拼接外部输入, `"SELECT ... WHERE " + userInput`, 使用${}而非#{}的MyBatis映射
- **反例**: `"SELECT * FROM users WHERE id=" + userId`
- **正例**: 使用参数化查询 / PreparedStatement / ORM
- **触发条件**: SQL语句通过字符串拼接外部输入, `"SELECT ... WHERE " + userInput`, 使用${}而非#{}的MyBatis映射
- **严重程度**: fatal

### COM-SEC-004: 敏感信息防泄漏

- **检查锚点**: `log.info()`/`log.debug()`中打印密码/身份证/AK-SK/Token, `toString()`方法包含敏感字段, 异常消息中含凭证信息
- **反例**:
  ```java
  log.info("用户登录: password={}", user.getPassword());
  public String toString() {
      return "User(ssn=" + ssn + ", password=" + password + ")";
  }
  ```
- **正例**:
  ```java
  log.info("用户登录: userId={}", user.getId());
  public String toString() {
      return "User(id=" + id + ", name=" + name + ")";  // 敏感字段脱敏
  }
- **触发条件**: `log.info()`/`log.debug()`中打印密码/身份证/AK-SK/Token, `toString()`方法包含敏感字段, 异常消息中含凭证信息
- **严重程度**: fatal
  ```

### COM-SEC-005: 不安全加密算法

- **检查锚点**: 使用MD5/SHA1用于密码哈希, 使用DES/3DES/RC4/AES-ECB加密, RSA密钥长度小于2048位
- **反例**:
  ```java
  String hash = DigestUtils.md5Hex(password);  // MD5哈希密码
  Cipher cipher = Cipher.getInstance("DES");    // DES加密
  Cipher cipher = Cipher.getInstance("AES/ECB/PKCS5Padding");  // AES-ECB模式
  ```
- **正例**:
  ```java
  String hash = BCrypt.hashpw(password, BCrypt.gensalt());  // bcrypt哈希密码
  Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");  // AES-GCM模式
  ```
- **触发条件**: 使用MD5/SHA1用于密码哈希, 使用DES/3DES/RC4/AES-ECB加密, RSA密钥长度小于2048位
- **严重程度**: fatal

### COM-SEC-006: 依赖安全

- **检查锚点**: 依赖版本包含已知CVE漏洞, 未使用依赖锁文件(lockfile), 引入已废弃的库(如Commons FileUpload 1.x)
- **反例**:
  ```xml
  <dependency>
      <groupId>log4j</groupId>
      <artifactId>log4j</artifactId>
      <version>2.14.0</version>  <!-- CVE-2021-44228 -->
  </dependency>
  ```
- **正例**:
  ```xml
  <dependency>
      <groupId>org.apache.logging.log4j</groupId>
      <artifactId>log4j-core</artifactId>
      <version>2.17.1</version>  <!-- 已修复的版本 -->
  </dependency>
  ```
- **触发条件**: 依赖版本包含已知CVE漏洞, 未使用依赖锁文件(lockfile), 引入已废弃的库(如Commons FileUpload 1.x)
- **严重程度**: fatal

### COM-SEC-007: 命令注入防护

- **检查锚点**: `exec()`/`Runtime.getRuntime().exec()`/`subprocess.call()`使用字符串拼接外部输入, `os.system()`拼接用户输入
- **反例**: `exec("ls " + userDir)`
- **正例**: `execFile("ls", [userDir])` — 参数分离
- **触发条件**: `exec()`/`Runtime.getRuntime().exec()`/`subprocess.call()`使用字符串拼接外部输入, `os.system()`拼接用户输入
- **严重程度**: fatal

### COM-SEC-008: 禁止禁用TLS/SSL证书验证

- **检查锚点**: InsecureSkipVerify: true, verify=False, CERT_NONE
- **反例**: `requests.get(url, verify=False)`
- **正例**: 保持证书验证开启
- **触发条件**: InsecureSkipVerify: true, verify=False, CERT_NONE, SSLContext自定义TrustManager接受所有证书
- **严重程度**: fatal

### COM-SEC-009: 不安全反序列化

- **检查锚点**: `pickle.loads()`/`ObjectInputStream.readObject()`/`BinaryFormatter.Deserialize()`处理不可信数据, YAML.load()未指定SafeLoader
- **反例**: `pickle.loads(external_data)`, `new BinaryFormatter().Deserialize(stream)`
- **正例**: 使用 JSON 等安全格式
- **触发条件**: `pickle.loads()`/`ObjectInputStream.readObject()`/`BinaryFormatter.Deserialize()`处理不可信数据, YAML.load()未指定SafeLoader
- **严重程度**: fatal

### COM-SEC-010: 必须使用安全密码哈希

- **反例**: 使用 MD5/SHA1 哈希密码
- **正例**: 使用 bcrypt / argon2 / PBKDF2
- **触发条件**: 使用 MD5/SHA1/SHA256 哈希密码, 自定义哈希算法用于密码存储
- **严重程度**: fatal

---

## 六、单元测试与可测试性

### COM-TEST-001: 测试覆盖

- **检查锚点**: 核心业务方法无对应测试文件, 测试仅覆盖正常路径(happy path), 边界值和异常路径未测试
- **反例**:
  ```java
  // 被测方法有三个分支，测试只覆盖了一个
  @Test
  void testCalculate() {
      assertEquals(100, service.calculate(100, "STANDARD"));
      // 缺少: PREMIUM分支、null入参、负数入参
  }
  ```
- **正例**:
  ```java
  @Test void shouldCalculateStandardRate() { assertEquals(100, service.calculate(100, "STANDARD")); }
  @Test void shouldCalculatePremiumRate() { assertEquals(80, service.calculate(100, "PREMIUM")); }
  @Test void shouldThrowWhenNegativeAmount() { assertThrows(IllegalArgumentException.class, () -> service.calculate(-1, "STANDARD")); }
  @Test void shouldThrowWhenNullRateType() { assertThrows(IllegalArgumentException.class, () -> service.calculate(100, null)); }
- **触发条件**: 核心业务方法无对应测试文件, 测试仅覆盖正常路径(happy path), 边界值和异常路径未测试
- **严重程度**: major
  ```

### COM-TEST-002: 禁止Mock被测对象本身

- **检查锚点**: 对被测类(SUT)使用`mock()`/`spy()`, 测试中调用的方法是Mock返回值而非真实逻辑
- **反例**:
  ```java
  @Test
  void testCalculate() {
      OrderService sut = mock(OrderService.class);  // Mock了被测对象本身
      when(sut.calculate(any())).thenReturn(100);    // 返回值是预设的，不是真实逻辑
      assertEquals(100, sut.calculate(order));
  }
  ```
- **正例**:
  ```java
  @Test
  void testCalculate() {
      PaymentGateway gateway = mock(PaymentGateway.class);  // Mock依赖
      OrderService sut = new OrderService(gateway);          // 被测对象用真实实例
      assertEquals(100, sut.calculate(order));               // 调用真实逻辑
  }
- **触发条件**: 对被测类(SUT)使用`mock()`/`spy()`, 测试中调用的方法是Mock返回值而非真实逻辑
- **严重程度**: major
  ```

### COM-TEST-003: 测试独立性

- **检查锚点**: 测试方法依赖其他测试的执行顺序, 测试共享可变静态变量, 测试方法间有隐式依赖(如@TestMethodOrder)
- **反例**:
  ```java
  static int sharedCounter = 0;  // 测试间共享可变状态
  @Test void testIncrement() { sharedCounter++; assertEquals(1, sharedCounter); }
  @Test void testDouble() { sharedCounter *= 2; assertEquals(2, sharedCounter); }  // 依赖testIncrement先执行
  ```
- **正例**:
  ```java
  @Test void testIncrement() {
      Counter counter = new Counter(0);  // 每个测试独立初始化
      counter.increment();
      assertEquals(1, counter.getValue());
  }
  @Test void testDouble() {
      Counter counter = new Counter(1);  // 独立初始化，不依赖其他测试
      counter.doubleValue();
      assertEquals(2, counter.getValue());
  }
- **触发条件**: 测试方法依赖其他测试的执行顺序, 测试共享可变静态变量, 测试方法间有隐式依赖(如@TestMethodOrder)
- **严重程度**: major
  ```

### COM-TEST-004: 禁止在测试中使用sleep

- **检查锚点**: `Thread.sleep()`/`time.sleep()`出现在测试代码中, 测试通过固定延时等待异步结果
- **反例**:
  ```java
  @Test
  void testAsyncCallback() {
      service.processAsync(request);
      Thread.sleep(3000);  // 固定等待，不可靠且拖慢测试
      assertEquals("DONE", service.getStatus());
  }
  ```
- **正例**:
  ```java
  @Test
  void testAsyncCallback() {
      CompletableFuture<String> future = service.processAsync(request);
      String result = future.get(5, TimeUnit.SECONDS);  // 显式等待完成
      assertEquals("DONE", result);
  }
- **触发条件**: `Thread.sleep()`/`time.sleep()`出现在测试代码中, 测试通过固定延时等待异步结果
- **严重程度**: minor
  ```

### COM-TEST-005: 避免不必要的IO操作

- **检查锚点**: 单元测试中读写真实文件/网络/数据库, 测试依赖外部服务地址, 测试因环境问题间歇性失败
- **反例**:
  ```java
  @Test
  void testSendNotification() {
      EmailClient client = new EmailClient("smtp.real-server.com", 25);  // 连接真实邮件服务器
      client.send("test@test.com", "subject", "body");
  }
  ```
- **正例**:
  ```java
  @Test
  void testSendNotification() {
      EmailClient mockClient = mock(EmailClient.class);  // Mock外部依赖
      NotificationService service = new NotificationService(mockClient);
      service.sendNotification("test@test.com", "subject", "body");
      verify(mockClient).send(eq("test@test.com"), eq("subject"), eq("body"));
  }
- **触发条件**: 单元测试中读写真实文件/网络/数据库, 测试依赖外部服务地址, 测试因环境问题间歇性失败
- **严重程度**: minor
  ```

---

## 七、构建、部署与环境配置

### COM-BUILD-001: 服务器配置显式化

- **检查锚点**: 依赖服务器默认值(如默认线程池大小、默认超时时间), 配置项仅在运维文档中说明未纳入代码仓库
- **反例**:
  ```yaml
  server:
    port: 8080
  # 未显式配置线程池、超时、连接数等，依赖应用服务器默认值
  ```
- **正例**:
  ```yaml
  server:
    port: 8080
    tomcat:
      max-threads: 200
      min-spare-threads: 10
      connection-timeout: 5000
  spring:
    datasource:
      hikari:
        maximum-pool-size: 20
        connection-timeout: 30000
  ```
- **触发条件**: 依赖服务器默认值(如默认线程池大小、默认超时时间), 配置项仅在运维文档中说明未纳入代码仓库
- **严重程度**: minor

### COM-BUILD-002: 依赖管理

- **检查锚点**: 版本声明使用`LATEST`/`RELEASE`/`SNAPSHOT`, 依赖版本范围为`[1.0,)`开区间, 无锁文件(lockfile/pom.xml无固定版本)
- **反例**:
  ```xml
  <dependency>
      <groupId>com.example</groupId>
      <artifactId>core-lib</artifactId>
      <version>LATEST</version>  <!-- 版本不固定 -->
  </dependency>
  ```
  ```groovy
  implementation "com.example:core-lib:1.+"  <!-- 版本范围 -->
  ```
- **正例**:
  ```xml
  <dependency>
      <groupId>com.example</groupId>
      <artifactId>core-lib</artifactId>
      <version>2.3.1</version>  <!-- 锁定具体版本 -->
  </dependency>
  ```
  ```groovy
  implementation "com.example:core-lib:2.3.1"  <!-- 锁定具体版本 -->
  ```
- **触发条件**: 版本声明使用`LATEST`/`RELEASE`/`SNAPSHOT`, 依赖版本范围为`[1.0,)`开区间, 无锁文件(lockfile/pom.xml无固定版本)
- **严重程度**: major

### COM-BUILD-003: 容器化配置

- **检查锚点**: Dockerfile中`FROM xxx:latest`, 容器以root用户运行, 未使用多阶段构建导致镜像含构建工具
- **反例**:
  ```dockerfile
  FROM node:latest
  WORKDIR /app
  COPY . .
  RUN npm install && npm run build
  CMD ["node", "server.js"]
  # 问题: latest标签、以root运行、含构建工具(node_modules)
  ```
- **正例**:
  ```dockerfile
  # ---- 构建阶段 ----
  FROM node:18.17.0-alpine AS builder
  WORKDIR /app
  COPY package*.json ./
  RUN npm ci
  COPY . .
  RUN npm run build
  # ---- 运行阶段 ----
  FROM node:18.17.0-alpine
  RUN addgroup -S appgroup && adduser -S appuser -G appgroup
  WORKDIR /app
  COPY --from=builder /app/dist ./dist
  COPY --from=builder /app/node_modules ./node_modules
  USER appuser
  CMD ["node", "dist/server.js"]
  ```
- **触发条件**: Dockerfile中`FROM xxx:latest`, 容器以root用户运行, 未使用多阶段构建导致镜像含构建工具
- **严重程度**: major

---

## 八、业务相关通用规则

### COM-BIZ-001: 性能优化类修改必须验证数据一致性

- **检查锚点**: MR标题/描述包含"性能优化"，或MR修改意图包含性能优化
- **反例**: MR做了性能优化的重构，仅验证了功能正常，数据量一致
- **正例**: 把修改前后的数据导出，使用脚本或工具校验前后数据完全一致
- **触发条件**: MR标题/描述包含"性能优化"，或MR修改意图包含性能优化
- **严重程度**: major

### COM-BIZ-002: 进行除法或模运算前必须判断除数是否为零

- **检查锚点**: 集合.size()作为除数, / 除法运算, % 模运算
- **反例**: `(double) i / actNes.size()`
- **正例**: `actNes.isEmpty() ? 0 : (double) i / actNes.size()`
- **触发条件**: 集合.size()作为除数, / 除法运算, % 模运算
- **严重程度**: fatal

---

## 九、严重级别判定

| 级别 | 判定标准 |
|------|---------|
| **fatal** | 已证实的阻塞问题：安全泄露、数据破坏、确定性崩溃、构建失败，必须阻塞合入 |
| **major** | 已证实会导致行为不正确、结果错误或关键工作流失败的缺陷 |
| **minor** | 已证实的当前低影响缺陷，或有明确修复价值的显式规则违规 |
| **suggestion** | 风格、优化、可读性、命名偏好、上下文不足的推测 |

**判定规则**：
1. 先判断证据确定性，再判断影响范围。证据较弱时降低严重级别。
2. 潜在未来风险、兼容性猜测、扩展性担忧，必须丢弃。
3. 风格/可读性/命名类 finding 的最高级别是 suggestion，除非证明造成了当前运行时/安全/逻辑影响。
