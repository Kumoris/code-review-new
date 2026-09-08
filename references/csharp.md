# C# 检视规则

> 来源：mr-reviewer 独占（其他skill无C#规则）

---

## 目录

- [一、安全编码](#一安全编码)
  - [CS-SEC-001: 禁止SQL拼接注入](#cs-sec-001-禁止sql拼接注入)
  - [CS-SEC-002: 禁止Process.Start注入未校验输入](#cs-sec-002-禁止processstart注入未校验输入)
  - [CS-SEC-003: 禁止硬编码密钥和凭证](#cs-sec-003-禁止硬编码密钥和凭证)
  - [CS-SEC-004: 禁止使用不安全反序列化器](#cs-sec-004-禁止使用不安全反序列化器)
  - [CS-SEC-005: 必须对用户输入做校验和编码](#cs-sec-005-必须对用户输入做校验和编码)
  - [CS-SEC-006: 禁止禁用TLS/SSL验证](#cs-sec-006-禁止禁用tlsssl验证)
  - [CS-SEC-007: 必须使用安全密码哈希](#cs-sec-007-必须使用安全密码哈希)
  - [CS-SEC-008: 必须防范XXE攻击](#cs-sec-008-必须防范xxe攻击)
  - [CS-SEC-009: 必须设置Cookie安全属性](#cs-sec-009-必须设置cookie安全属性)
- [二、并发安全](#二并发安全)
  - [CS-CON-001: 禁止并发访问非线程安全集合](#cs-con-001-禁止并发访问非线程安全集合)
  - [CS-CON-002: 必须使用lock或Monitor保护共享可变状态](#cs-con-002-必须使用lock或monitor保护共享可变状态)
  - [CS-CON-003: 禁止async/await死锁](#cs-con-003-禁止asyncawait死锁)
  - [CS-CON-004: 必须使用CancellationToken取消长时间异步任务](#cs-con-004-必须使用cancellationtoken取消长时间异步任务)
  - [CS-CON-005: 必须使用using或Dispose释放资源](#cs-con-005-必须使用using或dispose释放资源)
- [三、编码规范](#三编码规范)
  - [CS-CODE-001: 禁止使用==比较浮点数](#cs-code-001-禁止使用比较浮点数)
  - [CS-CODE-002: 禁止忽略Task返回值](#cs-code-002-禁止忽略task返回值)
  - [CS-CODE-003: 必须启用Nullable Reference Types](#cs-code-003-必须启用nullable-reference-types)
  - [CS-CODE-004: 禁止在迭代中修改集合](#cs-code-004-禁止在迭代中修改集合)
  - [CS-CODE-005: 禁止捕获异常后不做任何处理](#cs-code-005-禁止捕获异常后不做任何处理)
  - [CS-CODE-006: 必须使用StringComparison进行字符串比较](#cs-code-006-必须使用stringcomparison进行字符串比较)
- [四、性能优化](#四性能优化)
  - [CS-PERF-001: 禁止在循环中拼接字符串](#cs-perf-001-禁止在循环中拼接字符串)
  - [CS-PERF-002: 禁止N+1数据库查询](#cs-perf-002-禁止n1数据库查询)
  - [CS-PERF-003: 禁止不必要的装箱拆箱](#cs-perf-003-禁止不必要的装箱拆箱)
  - [CS-PERF-004: 必须对只读查询使用AsNoTracking](#cs-perf-004-必须对只读查询使用asnotracking)
- [五、架构设计](#五架构设计)
  - [CS-ARCH-001: 必须使用依赖注入而非直接new依赖](#cs-arch-001-必须使用依赖注入而非直接new依赖)
  - [CS-ARCH-002: 禁止硬编码配置值](#cs-arch-002-禁止硬编码配置值)

---

## 一、安全编码

### CS-SEC-001: 禁止SQL拼接注入

- **检查锚点**: string.Concat, $""+SQL, string.Format+SQL, SqlCommand+拼接字符串
- **反例**: `new SqlCommand("SELECT * FROM Users WHERE Id=" + userId)`
- **正例**: `new SqlCommand("SELECT * FROM Users WHERE Id=@Id")` 配合 Parameters.AddWithValue
- **触发条件**: C#代码中SqlCommand+字符串拼接构造SQL语句
- **严重程度**: fatal

### CS-SEC-002: 禁止Process.Start注入未校验输入

- **检查锚点**: Process.Start, ProcessStartInfo, Arguments=
- **反例**: `Process.Start("cmd", "/c " + userInput)`
- **正例**: 使用参数列表并校验白名单
- **触发条件**: C#代码中Process.Start或ProcessStartInfo使用用户输入拼接参数
- **严重程度**: fatal

### CS-SEC-003: 禁止硬编码密钥和凭证

- **检查锚点**: password=, secret=, apiKey=, token=, 连接字符串含密码
- **触发条件**: C#代码中硬编码password/secret/apiKey/token等凭证字符串
- **严重程度**: fatal

### CS-SEC-004: 禁止使用不安全反序列化器

- **检查锚点**: BinaryFormatter, NetDataContractSerializer, SoapFormatter, LosFormatter
- **反例**: `new BinaryFormatter().Deserialize(stream)`
- **正例**: 使用 System.Text.Json 或 JsonSerializer
- **触发条件**: C#代码中使用BinaryFormatter/SoapFormatter等不安全反序列化器
- **严重程度**: fatal

### CS-SEC-005: 必须对用户输入做校验和编码

- **检查锚点**: Request.Form, Request.QueryString, Razor @Html.Raw
- **反例**: `@Html.Raw(userInput)` — XSS
- **正例**: `@Html.DisplayFor(m => m.UserInput)` — 自动编码
- **触发条件**: C#代码中Request.Form/QueryString未校验或Razor中使用Html.Raw
- **严重程度**: major

### CS-SEC-006: 禁止禁用TLS/SSL验证

- **检查锚点**: ServerCertificateValidationCallback, return true
- **反例**: `ServerCertificateValidationCallback = (s,c,h,e) => true`
- **触发条件**: C#代码中ServerCertificateValidationCallback始终返回true
- **严重程度**: fatal

### CS-SEC-007: 必须使用安全密码哈希

- **检查锚点**: MD5.Create, SHA1.Create, MD5CryptoServiceProvider
- **反例**: `MD5.Create().ComputeHash(passwordBytes)`
- **正例**: 使用 Rfc2898DeriveBytes (PBKDF2) 或 BCrypt
- **触发条件**: C#代码中使用MD5/SHA1等不安全哈希算法处理密码
- **严重程度**: fatal

### CS-SEC-008: 必须防范XXE攻击

- **检查锚点**: XmlReader, XmlTextReader, XmlDocument, XmlSerializer
- **反例**: `new XmlDocument() { ProhibitDtd = false }`
- **正例**: `XmlReaderSettings { DtdProcessing = DtdProcessing.Prohibit }`
- **触发条件**: C#代码中XmlDocument/XmlTextReader未禁用DTD处理
- **严重程度**: major

### CS-SEC-009: 必须设置Cookie安全属性

- **检查锚点**: HttpCookie, CookieOptions, SameSite, HttpOnly, Secure
- **反例**: `new HttpCookie("auth") { Value = token }` 缺少安全属性
- **正例**: `new HttpCookie("auth") { HttpOnly = true, Secure = true, SameSite = SameSiteMode.Strict }`
- **触发条件**: C#代码中创建HttpCookie/CookieOptions未设置HttpOnly/Secure/SameSite
- **严重程度**: major

---

## 二、并发安全

### CS-CON-001: 禁止并发访问非线程安全集合

- **检查锚点**: Dictionary<,>, List<>, HashSet<> 在多线程上下文中使用
- **正例**: ConcurrentDictionary, ConcurrentBag, 或加 lock
- **触发条件**: C#多线程上下文中使用Dictionary/List/HashSet等非线程安全集合
- **严重程度**: major

### CS-CON-002: 必须使用lock或Monitor保护共享可变状态

- **检查锚点**: static可变字段, 共享mutable对象
- **反例**: 多线程直接读写 static List<>
- **正例**: `lock(_syncObj) { sharedList.Add(item); }`
- **触发条件**: C#代码中static可变字段或多线程共享mutable对象无lock/Monitor保护
- **严重程度**: major

### CS-CON-003: 禁止async/await死锁

- **检查锚点**: .Result, .Wait(), Task.GetAwaiter().GetResult() 在ASP.NET非Core上下文
- **反例**: `var result = GetDataAsync().Result` — 死锁
- **正例**: `var result = await GetDataAsync()` — 全链路异步
- **触发条件**: C#代码中在ASP.NET非Core上下文使用.Result/.Wait()阻塞异步方法
- **严重程度**: major

### CS-CON-004: 必须使用CancellationToken取消长时间异步任务

- **检查锚点**: Task.Run, Task.Delay, HttpClient.GetAsync 无CancellationToken参数
- **反例**: `await Task.Delay(Timeout.Infinite)`
- **正例**: `await Task.Delay(timeout, cancellationToken)`
- **触发条件**: C#代码中Task.Run/Task.Delay/HttpClient.GetAsync未传入CancellationToken
- **严重程度**: minor

### CS-CON-005: 必须使用using或Dispose释放资源

- **检查锚点**: IDisposable, Stream, HttpClient, SqlConnection 无using
- **反例**: `var stream = new FileStream(...)` — 无using
- **正例**: `using var stream = new FileStream(...)`
- **触发条件**: C#代码中IDisposable/Stream/HttpClient/SqlConnection未使用using包裹
- **严重程度**: major

---

## 三、编码规范

### CS-CODE-001: 禁止使用==比较浮点数

- **反例**: `if (price == 0.1)`
- **正例**: `if (Math.Abs(price - 0.1) < epsilon)`
- **触发条件**: C#代码中使用==或!=直接比较float/double浮点数
- **严重程度**: minor

### CS-CODE-002: 禁止忽略Task返回值

- **检查锚点**: 方法返回Task但调用处未await, fire-and-forget
- **反例**: `SendEmailAsync();` — 未await
- **正例**: `await SendEmailAsync();` 或 `_ = SendEmailAsync();` 并显式处理异常
- **触发条件**: C#代码中调用返回Task的方法但未await也未丢弃返回值
- **严重程度**: major

### CS-CODE-003: 必须启用Nullable Reference Types

- **正例**: 项目级别 `<Nullable>enable</Nullable>`
- **触发条件**: C#项目csproj文件中未设置<Nullable>enable</Nullable>
- **严重程度**: minor

### CS-CODE-004: 禁止在迭代中修改集合

- **反例**: `foreach(var item in list) { list.Remove(item); }`
- **正例**: `list.RemoveAll(item => condition)`
- **触发条件**: C#代码中foreach迭代内对迭代集合执行Remove/Add等修改操作
- **严重程度**: major

### CS-CODE-005: 禁止捕获异常后不做任何处理

- **反例**: `catch { }`
- **正例**: `catch (Exception ex) { _logger.LogError(ex, "..."); throw; }`
- **触发条件**: C#代码中catch块为空或catch后无任何日志/处理/重抛操作
- **严重程度**: major

### CS-CODE-006: 必须使用StringComparison进行字符串比较

- **反例**: `str1.ToLower() == str2.ToLower()`
- **正例**: `string.Equals(str1, str2, StringComparison.OrdinalIgnoreCase)`
- **触发条件**: C#代码中字符串比较先调用ToLower()/ToUpper()再使用==比较
- **严重程度**: suggestion

---

## 四、性能优化

### CS-PERF-001: 禁止在循环中拼接字符串

- **反例**: `for(...) { result += item; }`
- **正例**: `var sb = new StringBuilder(); for(...) { sb.Append(item); }`
- **触发条件**: C#代码中循环体内使用+=拼接字符串而非StringBuilder
- **严重程度**: minor

### CS-PERF-002: 禁止N+1数据库查询

- **检查锚点**: EF Core: 循环中调用.ToList, .FirstOrDefault, Include缺失
- **反例**: 循环中逐条查询
- **正例**: `_ctx.Orders.Include(o => o.Items).ToList()` 或批量查询
- **触发条件**: C#EF Core代码中循环内调用.ToList/.FirstOrDefault逐条查询
- **严重程度**: major

### CS-PERF-003: 禁止不必要的装箱拆箱

- **检查锚点**: ArrayList, Hashtable, object参数传值类型
- **正例**: 使用泛型集合 List<int>, Dictionary<TKey, TValue>
- **触发条件**: C#代码中使用ArrayList/Hashtable或将值类型赋给object参数
- **严重程度**: minor

### CS-PERF-004: 必须对只读查询使用AsNoTracking

- **反例**: `_ctx.Users.Where(u => u.Active).ToList()` — 无跟踪
- **正例**: `_ctx.Users.AsNoTracking().Where(u => u.Active).ToList()`
- **触发条件**: C#EF Core只读查询未调用AsNoTracking()方法
- **严重程度**: minor

---

## 五、架构设计

### CS-ARCH-001: 必须使用依赖注入而非直接new依赖

- **检查锚点**: new HttpClient(), new SqlConnection() 在业务逻辑中, ServiceLocator
- **正例**: 构造函数注入 `public MyService(IHttpClientFactory clientFactory)`
- **触发条件**: C#业务逻辑中直接new HttpClient/SqlConnection等外部依赖
- **严重程度**: minor

### CS-ARCH-002: 禁止硬编码配置值

- **检查锚点**: 连接字符串硬编码, 超时时间硬编码, URL硬编码
- **正例**: 使用 IOptions<T>, appsettings.json, 环境变量
- **触发条件**: C#代码中硬编码连接字符串/超时时间/URL等配置值
- **严重程度**: minor
