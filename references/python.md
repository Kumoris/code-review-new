# Python 检视规则

> 来源：既有检视规则去重合并；规则与代码托管平台无关

---

## 目录

- [一、架构设计与代码结构](#一架构设计与代码结构)
  - [PY-ARCH-001: SOLID原则](#py-arch-001-solid原则)
  - [PY-ARCH-002: 模块化与目录结构](#py-arch-002-模块化与目录结构)
  - [PY-ARCH-003: 设计模式的应用](#py-arch-003-设计模式的应用)
  - [PY-ARCH-004: 避免全局可变状态](#py-arch-004-避免全局可变状态)
  - [PY-ARCH-005: 禁止循环导入](#py-arch-005-禁止循环导入)
  - [PY-ARCH-006: 必须使用类型标注声明公共API](#py-arch-006-必须使用类型标注声明公共api)
  - [PY-ARCH-007: 禁止硬编码配置值](#py-arch-007-禁止硬编码配置值)
  - [PY-ARCH-008: 禁止过度嵌套（超过3层）](#py-arch-008-禁止过度嵌套超过3层)
  - [PY-ARCH-009: 禁止函数超过50行或参数超过5个](#py-arch-009-禁止函数超过50行或参数超过5个)
- [二、代码实现与可读性](#二代码实现与可读性)
  - [PY-CODE-001: 统一编码规范与自动化工具](#py-code-001-统一编码规范与自动化工具)
  - [PY-CODE-002: 命名规范](#py-code-002-命名规范)
  - [PY-CODE-003: 文档字符串与类型提示](#py-code-003-文档字符串与类型提示)
  - [PY-CODE-004: 代码简洁性（Pythonic Code）](#py-code-004-代码简洁性pythonic-code)
  - [PY-CODE-005: 异常处理](#py-code-005-异常处理)
  - [PY-CODE-006: DRY](#py-code-006-dry)
  - [PY-CODE-007: 禁止空except吞没异常](#py-code-007-禁止空except吞没异常)
  - [PY-CODE-008: 禁止使用可变对象作为函数默认参数](#py-code-008-禁止使用可变对象作为函数默认参数)
  - [PY-CODE-009: 禁止通配符导入](#py-code-009-禁止通配符导入)
  - [PY-CODE-010: 禁止遮蔽内置名称](#py-code-010-禁止遮蔽内置名称)
  - [PY-CODE-011: 必须使用上下文管理器操作资源](#py-code-011-必须使用上下文管理器操作资源)
  - [PY-CODE-012: 禁止保留调试打印和注释掉的代码](#py-code-012-禁止保留调试打印和注释掉的代码)
  - [PY-CODE-013: 必须使用functools.wraps装饰装饰器函数](#py-code-013-必须使用functoolswraps装饰装饰器函数)
  - [PY-CODE-014: 禁止裸类型Any替代具体类型标注](#py-code-014-禁止裸类型any替代具体类型标注)
  - [PY-CODE-015: 禁止未验证的用户输入直接用于文件路径](#py-code-015-禁止未验证的用户输入直接用于文件路径)
- [三、安全编码](#三安全编码)
  - [PY-SEC-001: 禁止字符串拼接构造SQL语句](#py-sec-001-禁止字符串拼接构造sql语句)
  - [PY-SEC-002: 禁止使用shell=True执行系统命令](#py-sec-002-禁止使用shelltrue执行系统命令)
  - [PY-SEC-003: 禁止硬编码凭据和密钥](#py-sec-003-禁止硬编码凭据和密钥)
  - [PY-SEC-004: 禁止使用不安全的反序列化](#py-sec-004-禁止使用不安全的反序列化)
  - [PY-SEC-005: 禁止禁用SSL/TLS证书验证](#py-sec-005-禁止禁用ssltls证书验证)
  - [PY-SEC-006: 禁止在日志中输出敏感数据](#py-sec-006-禁止在日志中输出敏感数据)
  - [PY-SEC-007: 依赖项获取方式审查](#py-sec-007-依赖项获取方式审查)
  - [PY-SEC-008: 依赖审计](#py-sec-008-依赖审计)
  - [PY-SEC-009: 静态与运行时安全检测](#py-sec-009-静态与运行时安全检测)
- [四、性能与资源管理](#四性能与资源管理)
  - [PY-PERF-001: 禁止在循环中使用+拼接字符串](#py-perf-001-禁止在循环中使用拼接字符串)
  - [PY-PERF-002: 禁止在循环中执行数据库查询（N+1问题）](#py-perf-002-禁止在循环中执行数据库查询n1问题)
  - [PY-PERF-003: 禁止对列表头部执行insert或pop(0)](#py-perf-003-禁止对列表头部执行insert或pop0)
  - [PY-PERF-004: 必须对频繁调用的正则表达式预编译](#py-perf-004-必须对频繁调用的正则表达式预编译)
  - [PY-PERF-005: 必须使用生成器处理大规模数据](#py-perf-005-必须使用生成器处理大规模数据)
  - [PY-PERF-006: 并发与异步](#py-perf-006-并发与异步)
  - [PY-PERF-007: 缓存与加速](#py-perf-007-缓存与加速)
  - [PY-PERF-008: 资源使用与内存优化](#py-perf-008-资源使用与内存优化)
- [五、并发安全](#五并发安全)
  - [PY-CON-001: 禁止无锁访问共享可变状态](#py-con-001-禁止无锁访问共享可变状态)
  - [PY-CON-002: 禁止在async函数中调用阻塞IO](#py-con-002-禁止在async函数中调用阻塞io)
  - [PY-CON-003: 必须处理async任务取消和超时](#py-con-003-必须处理async任务取消和超时)
- [六、单元测试与可测试性](#六单元测试与可测试性)
  - [PY-TEST-001: 测试技术栈与意图](#py-test-001-测试技术栈与意图)
  - [PY-TEST-002: 断言的正确性与清晰度](#py-test-002-断言的正确性与清晰度)
  - [PY-TEST-003: 禁止Mock被测对象本身](#py-test-003-禁止mock被测对象本身)
  - [PY-TEST-004: 警惕猴子补丁](#py-test-004-警惕猴子补丁)
  - [PY-TEST-005: 参数化测试](#py-test-005-参数化测试)
  - [PY-TEST-006: 测试性能](#py-test-006-测试性能)
- [七、构建、部署与环境配置](#七构建部署与环境配置)
  - [PY-BUILD-001: 依赖管理](#py-build-001-依赖管理)
  - [PY-BUILD-002: 容器化配置](#py-build-002-容器化配置)
  - [PY-BUILD-003: 服务器配置显式化](#py-build-003-服务器配置显式化)

---

## 一、架构设计与代码结构

### PY-ARCH-001: SOLID原则

- **检查锚点**: 类中有多个不相关方法修改同一属性, if/elif链按类型分支, 子类覆写方法抛出NotImplementedError, 接口类包含不相关方法, 直接实例化具体类而非通过抽象
- **反例**:
  ```python
  # SRP违反: 一个类承担多项职责
  class UserManager:
      def create_user(self, data): ...
      def send_email(self, user): ...
      def generate_report(self, user): ...

  # OCP违反: 新增类型需修改已有函数
  def calculate_area(shape):
      if shape.type == "circle":
          return 3.14 * shape.radius ** 2
      elif shape.type == "rectangle":
          return shape.width * shape.height

  # DIP违反: 直接依赖具体实现
  class OrderService:
      def __init__(self):
          self.repo = MySQLOrderRepo()  # 硬编码具体类
  ```
- **正例**:
  ```python
  # SRP: 每个类单一职责
  class UserManager:
      def create_user(self, data): ...
  class EmailService:
      def send_email(self, user): ...
  class ReportGenerator:
      def generate_report(self, user): ...

  # OCP: 通过抽象和多态扩展
  from abc import ABC, abstractmethod
  class Shape(ABC):
      @abstractmethod
      def area(self) -> float: ...
  class Circle(Shape):
      def area(self) -> float:
          return 3.14 * self.radius ** 2

  # DIP: 依赖注入抽象
  class OrderService:
      def __init__(self, repo: OrderRepoProtocol):
          self.repo = repo
  ```
- **触发条件**: 类含多个不相关方法修改同一属性, if/elif按类型分支, 直接实例化具体类
- **严重程度**: major

### PY-ARCH-002: 模块化与目录结构

- **检查锚点**: 扁平单层目录(all .py在根目录), 多个服务共用requirements.txt, utils.py文件超过500行, TYPE_CHECKING块中导入业务模块
- **反例**:
  ```python
  # 项目根目录扁平堆放
  # /my_project/
  #   main.py, utils.py, db.py, auth.py, api.py  # 所有文件在根目录
  #   requirements.txt  # 多服务共用一个依赖文件

  # 循环依赖用TYPE_CHECKING掩盖而非重构
  # a.py
  from __future__ import annotations
  from typing import TYPE_CHECKING
  if TYPE_CHECKING:
      from b import BService  # 只为解决循环导入,实际运行时仍耦合
  ```
- **正例**:
  ```python
  # 分层目录结构
  # /my_project/
  #   services/
  #     auth/  (auth.py, requirements.txt)
  #     api/   (api.py, requirements.txt)
  #   core/    (models.py, interfaces.py)
  #   shared/  (utils.py)

  # 公共代码抽取为独立模块
  # shared/utils.py  -- 小而专注的工具模块
  def format_timestamp(dt: datetime) -> str: ...
  ```
- **触发条件**: 扁平单层目录结构, utils.py超500行, 多服务共用requirements.txt
- **严重程度**: minor

### PY-ARCH-003: 设计模式的应用

- **检查锚点**: 大量if/elif按类型分支(应使用策略模式), 手动创建一系列相关对象(应使用工厂模式), 多处重复的对象组装逻辑(应使用建造者模式)
- **反例**:
  ```python
  # 大量类型分支判断,应使用策略模式
  def process_payment(method, amount):
      if method == "credit_card":
          charge_credit_card(amount)
      elif method == "paypal":
          charge_paypal(amount)
      elif method == "bank_transfer":
          charge_bank(amount)
  ```
- **正例**:
  ```python
  # 策略模式: 新增支付方式无需修改已有代码
  from abc import ABC, abstractmethod
  class PaymentStrategy(ABC):
      @abstractmethod
      def pay(self, amount: float) -> None: ...

  class CreditCardPayment(PaymentStrategy):
      def pay(self, amount: float) -> None:
          charge_credit_card(amount)

  def process_payment(strategy: PaymentStrategy, amount: float) -> None:
      strategy.pay(amount)
  ```
- **触发条件**: 大量if/elif按类型分支, 手动创建一系列相关对象, 重复对象组装逻辑
- **严重程度**: minor

### PY-ARCH-004: 避免全局可变状态

- **检查锚点**: 模块级dict/list赋值, global关键字, 类属性为可变对象(list/dict)
- **反例**:
  ```python
  # 模块级可变全局状态
  _cache: dict = {}
  _connections: list = []

  def get_connection():
      global _connections
      _connections.append(create_conn())
      return _connections[-1]

  # 类级可变属性被多处修改
  class Config:
      settings = {"debug": True}  # 所有实例共享且可变
  ```
- **正例**:
  ```python
  # 通过类实例管理状态
  class ConnectionManager:
      def __init__(self):
          self._connections: list[Connection] = []

      def get_connection(self) -> Connection:
          conn = create_conn()
          self._connections.append(conn)
          return conn

  # 通过依赖注入传递配置
  class Config:
      def __init__(self, debug: bool = False):
          self._settings = {"debug": debug}  # 实例级别,互不干扰
  ```
- **触发条件**: 模块级dict/list赋值, global关键字, 类属性为可变对象(list/dict)
- **严重程度**: major

### PY-ARCH-005: 禁止循环导入

- **检查锚点**: 模块A导入B且B导入A
- **触发条件**: 模块A导入B且B导入A（循环导入）
- **严重程度**: major

### PY-ARCH-006: 必须使用类型标注声明公共API

- **正例**: `def get_user(user_id: int) -> User:`
- **触发条件**: 公共API函数签名缺少参数或返回值类型标注
- **严重程度**: minor

### PY-ARCH-007: 禁止硬编码配置值

- **检查锚点**: 代码中直接写入IP/端口/路径等配置字面值
- **触发条件**: 代码中直接写入IP/端口/路径等配置字面值
- **严重程度**: minor

### PY-ARCH-008: 禁止过度嵌套（超过3层）

- **检查锚点**: if嵌套超过3层, for嵌套超过3层
- **触发条件**: if/for嵌套超过3层
- **严重程度**: minor

### PY-ARCH-009: 禁止函数超过50行或参数超过5个

- **检查锚点**: def函数体过长, 函数参数列表过长
- **触发条件**: 函数体超过50行或参数超过5个
- **严重程度**: minor

---

## 二、代码实现与可读性

### PY-CODE-001: 统一编码规范与自动化工具

- **检查锚点**: 缺少pyproject.toml中的[tool.black]/[tool.ruff]配置, 缺少flake8/pylint配置, CI流水线无lint步骤
- **反例**:
  ```python
  # 项目无任何格式化/检查工具配置
  # pyproject.toml 中无 [tool.black], [tool.ruff], [tool.flake8] 等段落

  # 代码风格不一致: 有人用双引号,有人用单引号
  name = "Alice"
  role = 'admin'
  ```
- **正例**:
  ```toml
  # pyproject.toml
  [tool.black]
  line-length = 88

  [tool.ruff]
  select = ["E", "F", "W"]
  line-length = 88
  ```
  ```yaml
  # CI中集成检查步骤
  # .github/workflows/lint.yml
  #   - run: black --check .
  #   - run: ruff check .
  ```
- **触发条件**: 缺少pyproject.toml中lint/format工具配置, CI无lint步骤
- **严重程度**: suggestion

### PY-CODE-002: 命名规范

- **检查锚点**: 单字母变量名(非循环计数器), 函数名使用camelCase, 类名不以大写开头, 测试函数名无描述性
- **反例**:
  ```python
  x = get_data()           # 变量名无意义
  def getData(): ...       # 函数名用camelCase
  class user: ...          # 类名未用PascalCase
  def test_1(): ...        # 测试函数名无描述性
  ```
- **正例**:
  ```python
  user_profiles = get_data()              # 变量名表意清晰
  def get_data(): ...                    # 函数名用snake_case
  class UserProfile: ...                 # 类名用PascalCase
  def test_get_user_raises_on_invalid_id(): ...  # 测试函数名描述行为
  ```
- **触发条件**: 单字母变量名(非循环计数器), 函数名camelCase, 类名非PascalCase
- **严重程度**: suggestion

### PY-CODE-003: 文档字符串与类型提示

- **检查锚点**: 公共函数无docstring, 函数签名无类型标注, 缺少mypy配置
- **反例**:
  ```python
  def calculate_total(items, discount):
      return sum(i["price"] for i in items) * (1 - discount)
  ```
- **正例**:
  ```python
  def calculate_total(items: list[dict[str, float]], discount: float) -> float:
      """计算商品列表折后总价.

      Args:
          items: 商品列表,每个商品需包含"price"键.
          discount: 折扣比例,范围0.0~1.0.

      Returns:
          折后总金额.
      """
      return sum(i["price"] for i in items) * (1 - discount)
  ```
- **触发条件**: 公共函数无docstring或函数签名无类型标注
- **严重程度**: minor

### PY-CODE-004: 代码简洁性（Pythonic Code）

- **检查锚点**: for循环append到新列表(可用推导式), 多层if-else嵌套(可Early Return), 硬编码字符串常量(魔法值)
- **反例**:
  ```python
  # 未使用推导式
  result = []
  for item in items:
      if item.is_valid:
          result.append(item.name)

  # 未Early Return,多层嵌套
  def get_status(user):
      if user is not None:
          if user.is_active:
              if user.has_permission("admin"):
                  return "admin"
              else:
                  return "member"
          else:
              return "inactive"
      return "unknown"

  # 魔法值
  if status == 3: ...
  ```
- **正例**:
  ```python
  # 使用推导式
  result = [item.name for item in items if item.is_valid]

  # Early Return减少嵌套
  def get_status(user):
      if user is None:
          return "unknown"
      if not user.is_active:
          return "inactive"
      if user.has_permission("admin"):
          return "admin"
      return "member"

  # 用枚举替代魔法值
  from enum import IntEnum
  class Status(IntEnum):
      PENDING = 1
      ACTIVE = 2
      CLOSED = 3
  if status == Status.CLOSED: ...
  ```
- **触发条件**: for循环append到新列表, 多层if-else嵌套, 硬编码魔法值
- **严重程度**: suggestion

### PY-CODE-005: 异常处理

- **检查锚点**: 裸except: (无异常类型), except Exception后无日志/再抛出, 空except块
- **反例**:
  ```python
  # 裸except捕获所有异常包括KeyboardInterrupt
  try:
      result = do_something()
  except:
      pass

  # 捕获过于宽泛的异常且吞没
  try:
      save_to_db(data)
  except Exception:
      pass  # 吞没异常,难以排查问题
  ```
- **正例**:
  ```python
  # 捕获具体异常类型,记录日志
  try:
      result = do_something()
  except ValueError as e:
      logger.warning(f"Invalid value: {e}")
      result = default_value

  # 需要捕获宽泛异常时,应记录并再抛出或处理
  try:
      save_to_db(data)
  except DatabaseError as e:
      logger.error(f"Database save failed: {e}")
      raise
  ```
- **触发条件**: 裸`except:`或`except Exception:`后无日志/再抛出, 空except块
- **严重程度**: major

### PY-CODE-006: DRY

- **检查锚点**: 相同逻辑块出现2次以上, 相似的try/except结构重复, 相同的数据转换代码分散在多处
- **反例**:
  ```python
  # 重复的用户验证逻辑
  def create_user(data):
      if not data.get("email"):
          raise ValueError("Email required")
      if not data.get("name"):
          raise ValueError("Name required")
      ...

  def update_user(data):
      if not data.get("email"):
          raise ValueError("Email required")
      if not data.get("name"):
          raise ValueError("Name required")
      ...
  ```
- **正例**:
  ```python
  # 抽取公共验证函数
  def _validate_user_data(data: dict) -> None:
      if not data.get("email"):
          raise ValueError("Email required")
      if not data.get("name"):
          raise ValueError("Name required")

  def create_user(data):
      _validate_user_data(data)
      ...

  def update_user(data):
      _validate_user_data(data)
      ...
  ```
- **触发条件**: 相同逻辑块出现2次以上, 重复try/except结构, 相同数据转换代码分散多处
- **严重程度**: minor

### PY-CODE-007: 禁止空except吞没异常

- **反例**: `try: ... except: pass`
- **正例**: `try: ... except ValueError as e: logger.error(e)`
- **触发条件**: `except:`或`except Exception: pass`空except块
- **严重程度**: major

### PY-CODE-008: 禁止使用可变对象作为函数默认参数

- **反例**: `def append(item, lst=[]): lst.append(item)`
- **正例**: `def append(item, lst=None): lst = lst or []; lst.append(item)`
- **触发条件**: 函数参数默认值为可变对象（如`def f(x=[])`)
- **严重程度**: major

### PY-CODE-009: 禁止通配符导入

- **反例**: `from os import *`
- **正例**: `import os`
- **触发条件**: `from xxx import *`通配符导入语句
- **严重程度**: minor

### PY-CODE-010: 禁止遮蔽内置名称

- **反例**: `list = [1, 2, 3]`
- **正例**: `item_list = [1, 2, 3]`
- **触发条件**: 变量名与Python内置名称同名（如list/dict/str/id）
- **严重程度**: minor

### PY-CODE-011: 必须使用上下文管理器操作资源

- **反例**: `f = open("file.txt"); data = f.read(); f.close()`
- **正例**: `with open("file.txt") as f: data = f.read()`
- **触发条件**: `open()`未使用`with`语句, 手动调用`.close()`
- **严重程度**: major

### PY-CODE-012: 禁止保留调试打印和注释掉的代码

- **检查锚点**: print(, breakpoint(), 注释掉的代码块
- **触发条件**: `print()`/`breakpoint()`调用, 注释掉的代码块
- **严重程度**: minor

### PY-CODE-013: 必须使用functools.wraps装饰装饰器函数

- **检查锚点**: def wrapper(*args, **kwargs): 未加@functools.wraps
- **触发条件**: 装饰器内部`def wrapper(*args, **kwargs)`未加`@functools.wraps`
- **严重程度**: minor

### PY-CODE-014: 禁止裸类型Any替代具体类型标注

- **反例**: `def process(data: Any) -> Any:`
- **正例**: `def process(data: list[str]) -> dict[str, int]:`
- **触发条件**: 函数签名使用裸`Any`替代具体类型标注
- **严重程度**: minor

### PY-CODE-015: 禁止未验证的用户输入直接用于文件路径

- **检查锚点**: os.path.join(user_input), open(user_input)
- **触发条件**: `os.path.join(user_input)`或`open(user_input)`用户输入直接用于路径
- **严重程度**: fatal

---

## 三、安全编码

### PY-SEC-001: 禁止字符串拼接构造SQL语句

- **反例**: `cursor.execute("SELECT * FROM user WHERE id=" + user_id)`
- **正例**: `cursor.execute("SELECT * FROM user WHERE id=%s", (user_id,))`
- **触发条件**: SQL语句通过字符串拼接(+)或f-string构造
- **严重程度**: fatal

### PY-SEC-002: 禁止使用shell=True执行系统命令

- **反例**: `subprocess.run("ls " + user_input, shell=True)`
- **正例**: `subprocess.run(["ls", user_input])`
- **触发条件**: `subprocess.run/shell=True`或`os.system()`执行命令
- **严重程度**: fatal

### PY-SEC-003: 禁止硬编码凭据和密钥

- **反例**: `DB_PASSWORD = "admin123"`
- **正例**: `DB_PASSWORD = os.environ["DB_PASSWORD"]`
- **触发条件**: 代码中硬编码密码/API密钥/Token等凭据字面值
- **严重程度**: fatal

### PY-SEC-004: 禁止使用不安全的反序列化

- **反例**: `data = pickle.loads(external_data)`
- **正例**: `data = json.loads(external_data)`
- **触发条件**: `pickle.loads()`/`pickle.load()`处理外部数据
- **严重程度**: fatal

### PY-SEC-005: 禁止禁用SSL/TLS证书验证

- **反例**: `requests.get(url, verify=False)`
- **正例**: `requests.get(url, verify=True)`
- **触发条件**: `verify=False`禁用SSL/TLS证书验证
- **严重程度**: fatal

### PY-SEC-006: 禁止在日志中输出敏感数据

- **反例**: `logger.info(f"User password: {password}")`
- **触发条件**: 日志中输出密码/Token/密钥等敏感数据
- **严重程度**: fatal

### PY-SEC-007: 依赖项获取方式审查

- **检查锚点**: 脚本中使用curl/wget下载二进制文件并执行, pip install从非可信源安装
- **反例**:
  ```python
  # 在脚本中直接下载并执行二进制文件
  import urllib.request
  urllib.request.urlretrieve("https://untrusted.example.com/tool.bin", "/tmp/tool")
  os.system("chmod +x /tmp/tool && /tmp/tool")

  # pip从不受信源安装
  # pip install --index-url https://untrusted.example.com/simple private-pkg
  ```
- **正例**:
  ```python
  # 从受审核的内部源码编译安装
  # 1. 源码经过安全审查
  # 2. 构建过程在受控CI环境完成
  # 3. 产物存入受信制品库
  # pip install --index-url https://internal-pypi.example.com/simple private-pkg
  ```
- **触发条件**: 脚本中curl/wget下载二进制并执行, pip从非可信源安装
- **严重程度**: major

### PY-SEC-008: 依赖审计

- **检查锚点**: 缺少pip-audit/safety配置, CI无依赖扫描步骤, requirements.txt无版本锁定
- **反例**:
  ```txt
  # requirements.txt 无版本锁定且无审计工具
  flask
  requests
  sqlalchemy
  ```
- **正例**:
  ```txt
  # requirements.txt 精确锁定版本
  flask==3.0.0
  requests==2.31.0
  sqlalchemy==2.0.23
  ```
  ```yaml
  # CI中集成依赖审计
  # - run: pip-audit -r requirements.txt
  # - run: safety check -r requirements.txt
  ```
- **触发条件**: requirements.txt无版本锁定, 缺少pip-audit/safety配置
- **严重程度**: major

### PY-SEC-009: 静态与运行时安全检测

- **检查锚点**: 缺少bandit配置, CI无SAST扫描步骤
- **反例**:
  ```yaml
  # CI流水线仅有单元测试,无安全扫描步骤
  # .github/workflows/ci.yml
  # jobs:
  #   test:
  #     steps:
  #       - run: pytest
  ```
- **正例**:
  ```yaml
  # CI中集成Bandit扫描
  # .github/workflows/ci.yml
  # jobs:
  #   security:
  #     steps:
  #       - run: bandit -r src/ -c pyproject.toml
  ```
  ```toml
  # pyproject.toml 中配置bandit
  # [tool.bandit]
  # exclude_dirs = ["tests"]
  # severity_level = "medium"
  ```
- **触发条件**: 缺少bandit配置, CI无SAST扫描步骤
- **严重程度**: major

---

## 四、性能与资源管理

### PY-PERF-001: 禁止在循环中使用+拼接字符串

- **反例**: `result = ""; for s in strings: result += s`
- **正例**: `result = "".join(strings)`
- **触发条件**: 循环中使用`+=`拼接字符串
- **严重程度**: minor

### PY-PERF-002: 禁止在循环中执行数据库查询（N+1问题）

- **反例**: `for id in ids: obj = Model.objects.get(pk=id)`
- **正例**: `objs = Model.objects.filter(pk__in=ids)`
- **触发条件**: 循环内执行`.get()`/`.filter()`等单条数据库查询
- **严重程度**: major

### PY-PERF-003: 禁止对列表头部执行insert或pop(0)

- **反例**: `items.insert(0, new_item)`
- **正例**: `from collections import deque; items = deque(); items.appendleft(new_item)`
- **触发条件**: 列表头部`.insert(0, ...)`或`.pop(0)`
- **严重程度**: minor

### PY-PERF-004: 必须对频繁调用的正则表达式预编译

- **反例**: `for line in lines: m = re.search(pattern, line)`
- **正例**: `compiled = re.compile(pattern); for line in lines: m = compiled.search(line)`
- **触发条件**: 循环内反复调用`re.search()`/`re.match()`同一pattern
- **严重程度**: minor

### PY-PERF-005: 必须使用生成器处理大规模数据

- **反例**: `data = [process(x) for x in large_dataset]`
- **正例**: `data = (process(x) for x in large_dataset)`
- **触发条件**: 列表推导式处理大规模数据集（应使用生成器）
- **严重程度**: minor

### PY-PERF-006: 并发与异步

- **检查锚点**: I/O密集型任务使用同步requests/socket, CPU密集型任务使用threading而非multiprocessing
- **反例**:
  ```python
  # I/O密集型用同步请求,阻塞线程
  import requests
  def fetch_all(urls):
      results = []
      for url in urls:
          resp = requests.get(url)  # 同步阻塞
          results.append(resp.json())
      return results

  # CPU密集型用多线程,受GIL限制无法并行
  from threading import Thread
  def compute(data):
      threads = [Thread(target=heavy_cpu_task, args=(d,)) for d in data]
      for t in threads: t.start()
  ```
- **正例**:
  ```python
  # I/O密集型用asyncio
  import httpx
  async def fetch_all(urls):
      async with httpx.AsyncClient() as client:
          tasks = [client.get(url) for url in urls]
          responses = await asyncio.gather(*tasks)
      return [r.json() for r in responses]

  # CPU密集型用多进程绕开GIL
  from multiprocessing import Pool
  def compute(data):
      with Pool() as pool:
          results = pool.map(heavy_cpu_task, data)
      return results
  ```
- **触发条件**: I/O密集型任务使用同步requests/socket, CPU密集型任务使用threading而非multiprocessing
- **严重程度**: major

### PY-PERF-007: 缓存与加速

- **检查锚点**: 频繁调用纯函数且参数相同(应使用@lru_cache), 重复查询相同数据(应引入Redis缓存)
- **反例**:
  ```python
  # 每次请求都重新计算斐波那契数
  def fibonacci(n):
      if n < 2:
          return n
      return fibonacci(n - 1) + fibonacci(n - 2)

  # 每次请求都查询数据库获取配置
  def get_config(key):
      return db.query("SELECT value FROM config WHERE key=%s", (key,))
  ```
- **正例**:
  ```python
  # 使用lru_cache缓存纯函数结果
  from functools import lru_cache
  @lru_cache(maxsize=256)
  def fibonacci(n):
      if n < 2:
          return n
      return fibonacci(n - 1) + fibonacci(n - 2)

  # 使用Redis缓存频繁查询的配置
  def get_config(key: str) -> str:
      cached = redis_client.get(f"config:{key}")
      if cached:
          return cached
      value = db.query("SELECT value FROM config WHERE key=%s", (key,))
      redis_client.setex(f"config:{key}", 300, value)
      return value
  ```
- **触发条件**: 频繁调用纯函数且参数相同无缓存, 重复查询相同数据无缓存
- **严重程度**: minor

### PY-PERF-008: 资源使用与内存优化

- **检查锚点**: 一次性read()加载大文件到内存, 用list存储可流式处理的数据
- **反例**:
  ```python
  # 一次性加载整个大文件到内存
  with open("large_file.csv") as f:
      all_lines = f.readlines()  # 全部加载到内存
      for line in all_lines:
          process(line)

  # 用列表存储大量中间结果
  results = [transform(row) for row in huge_dataset]  # 全部驻留内存
  ```
- **正例**:
  ```python
  # 逐行读取,内存占用恒定
  with open("large_file.csv") as f:
      for line in f:  # 惰性迭代
          process(line)

  # 使用生成器惰性处理
  results = (transform(row) for row in huge_dataset)  # 生成器,按需产出
  for result in results:
      write(result)
  ```
- **触发条件**: 一次性read()加载大文件到内存, 用list存储可流式处理的数据
- **严重程度**: major

---

## 五、并发安全

### PY-CON-001: 禁止无锁访问共享可变状态

- **反例**: `shared_dict[key] = value  # 多线程无锁`
- **正例**: `with lock: shared_dict[key] = value`
- **触发条件**: 多线程/多进程访问共享dict/list无Lock保护
- **严重程度**: major

### PY-CON-002: 禁止在async函数中调用阻塞IO

- **反例**: `async def handler(): time.sleep(5)`
- **正例**: `async def handler(): await asyncio.sleep(5)`
- **触发条件**: async函数中使用time.sleep()/requests.get()/同步文件IO
- **严重程度**: major

### PY-CON-003: 必须处理async任务取消和超时

- **正例**: `try: await asyncio.wait_for(coro, timeout=30) except asyncio.TimeoutError: ...`
- **触发条件**: async函数中await无timeout保护, 未捕获CancelledError
- **严重程度**: major

---

## 六、单元测试与可测试性

### PY-TEST-001: 测试技术栈与意图

- **检查锚点**: 使用unittest而非pytest, 测试函数只覆盖happy path, 缺少边界条件测试
- **反例**:
  ```python
  # 使用老旧unittest且仅测试正常路径
  import unittest
  class TestUser(unittest.TestCase):
      def test_create(self):
          user = create_user("Alice")
          self.assertEqual(user.name, "Alice")
      # 缺少边界条件和异常路径测试
  ```
- **正例**:
  ```python
  # 使用pytest,覆盖核心逻辑/边界/异常
  import pytest

  def test_create_user_normal():
      user = create_user("Alice")
      assert user.name == "Alice"

  def test_create_user_empty_name_raises():
      with pytest.raises(ValueError, match="name cannot be empty"):
          create_user("")

  def test_create_user_long_name_truncated():
      user = create_user("A" * 300)
      assert len(user.name) <= 255
  ```
- **触发条件**: 使用unittest而非pytest, 测试函数只覆盖happy path
- **严重程度**: minor

### PY-TEST-002: 断言的正确性与清晰度

- **检查锚点**: 使用assertTrue(a == b)而非assert a == b, 使用try/except捕获异常而非pytest.raises
- **反例**:
  ```python
  # 使用assertTrue,失败信息不清晰
  self.assertTrue(result == expected)

  # 手动try/except捕获异常
  try:
      do_something()
  except ValueError:
      pass
  else:
      self.fail("Expected ValueError")
  ```
- **正例**:
  ```python
  # 使用pytest原生assert,失败时自动显示差异
  assert result == expected

  # 使用pytest.raises捕获异常
  with pytest.raises(ValueError, match="invalid input"):
      do_something()
  ```
- **触发条件**: 使用assertTrue(a==b)而非assert a==b, 手动try/except捕获异常
- **严重程度**: minor

### PY-TEST-003: 禁止Mock被测对象本身

- **绝对禁止 Mock 正在被测试的类或函数（SUT）本身**。
- **触发条件**: 测试中Mock了被测试类自身的业务方法
- **严重程度**: major

### PY-TEST-004: 警惕猴子补丁

- **检查锚点**: monkeypatch.setattr修改业务逻辑, 测试中patch被测模块内部方法
- **反例**:
  ```python
  # 过度使用monkeypatch修改业务逻辑
  def test_process(monkeypatch):
      monkeypatch.setattr("myapp.service.calculate_tax", lambda x: 0)
      result = process_order(order)  # Mock了核心逻辑,测试无意义
  ```
- **正例**:
  ```python
  # 通过依赖注入替换依赖
  class OrderService:
      def __init__(self, tax_calculator: TaxCalculator):
          self.tax_calculator = tax_calculator

  def test_process():
      mock_tax = FakeTaxCalculator(tax=0)  # 注入替身
      service = OrderService(mock_tax)
      result = service.process_order(order)
  ```
- **触发条件**: monkeypatch.setattr修改业务逻辑, 测试中patch被测模块内部方法
- **严重程度**: minor

### PY-TEST-005: 参数化测试

- **检查锚点**: 多个测试函数仅输入/输出不同(应使用parametrize), 重复的测试代码结构
- **反例**:
  ```python
  def test_add_positive():
      assert add(1, 2) == 3

  def test_add_negative():
      assert add(-1, -2) == -3

  def test_add_zero():
      assert add(0, 0) == 0
  ```
- **正例**:
  ```python
  @pytest.mark.parametrize("a, b, expected", [
      (1, 2, 3),
      (-1, -2, -3),
      (0, 0, 0),
  ])
  def test_add(a, b, expected):
      assert add(a, b) == expected
  ```
- **触发条件**: 多个测试函数仅输入/输出不同未使用parametrize
- **严重程度**: suggestion

### PY-TEST-006: 测试性能

- **检查锚点**: 测试中使用time.sleep(), 单元测试中有实际I/O操作(文件/网络/数据库)
- **反例**:
  ```python
  # 测试中使用time.sleep等待
  def test_timeout():
      start = time.time()
      do_task()
      time.sleep(5)
      assert time.time() - start >= 5

  # 单元测试直接访问数据库
  def test_save_user():
      db = Database()  # 真实连接
      save_user(db, user)
  ```
- **正例**:
  ```python
  # 使用freezegun控制时间
  from freezegun import freeze_time
  @freeze_time("2024-01-01 12:00:00")
  def test_timeout():
      result = do_task()
      assert result.timestamp == "2024-01-01T12:00:00"

  # 通过Mock模拟数据库
  def test_save_user():
      mock_db = MagicMock(spec=Database)
      save_user(mock_db, user)
      mock_db.insert.assert_called_once_with(user)
  ```
- **触发条件**: 测试中使用time.sleep(), 单元测试中有实际I/O操作
- **严重程度**: minor

---

## 七、构建、部署与环境配置

### PY-BUILD-001: 依赖管理

- **检查锚点**: requirements.txt无版本锁定(无==), 使用范围版本(如>=), 缺少poetry.lock或Pipfile.lock
- **反例**:
  ```txt
  # requirements.txt 使用范围版本,构建不可复现
  flask>=2.0
  requests>=2.28
  sqlalchemy>=2.0
  ```
- **正例**:
  ```txt
  # requirements.txt 精确锁定版本
  flask==3.0.0
  requests==2.31.0
  sqlalchemy==2.0.23
  ```
  ```bash
  # 或使用poetry锁定
  # poetry.lock 文件提交到版本库,确保构建可复现
  ```
- **触发条件**: requirements.txt无版本锁定(无==), 使用范围版本(如>=), 缺少lock文件
- **严重程度**: major

### PY-BUILD-002: 容器化配置

- **检查锚点**: Dockerfile中使用latest标签, Dockerfile中使用root用户运行, 未使用多阶段构建
- **反例**:
  ```dockerfile
  # 使用latest标签且以root运行
  FROM python:latest
  COPY . /app
  RUN pip install -r requirements.txt
  CMD ["python", "app.py"]
  ```
- **正例**:
  ```dockerfile
  # 使用明确版本号,多阶段构建,非root用户
  FROM python:3.11-slim AS builder
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt

  FROM python:3.11-slim
  WORKDIR /app
  COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
  COPY . .
  USER nobody
  CMD ["gunicorn", "-w", "4", "app:app"]
  ```
- **触发条件**: Dockerfile中使用latest标签, 以root用户运行, 未使用多阶段构建
- **严重程度**: major

### PY-BUILD-003: 服务器配置显式化

- **检查锚点**: Gunicorn/Uvicorn启动命令未指定workers/timeout, 服务器参数仅使用默认值
- **反例**:
  ```bash
  # 启动命令未显式声明关键参数,依赖默认值
  gunicorn app:app
  uvicorn app:app
  ```
- **正例**:
  ```bash
  # 显式声明workers, timeout, bind等关键参数
  gunicorn app:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 120 \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile -
  ```
- **触发条件**: Gunicorn/Uvicorn启动命令未指定workers/timeout, 服务器参数仅使用默认值
- **严重程度**: minor
