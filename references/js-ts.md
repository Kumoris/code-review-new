# JavaScript / TypeScript 检视规则

> 来源：既有检视规则去重合并；规则与代码托管平台无关

---

## 目录

- [一、代码风格、可读性与自文档化](#一代码风格可读性与自文档化)
  - [JSTS-CODE-001: 命名](#jsts-code-001-命名)
  - [JSTS-CODE-002: 注释](#jsts-code-002-注释)
  - [JSTS-CODE-003: 声明与初始化](#jsts-code-003-声明与初始化)
  - [JSTS-CODE-004: 数据类型](#jsts-code-004-数据类型)
  - [JSTS-CODE-005: 运算与表达式](#jsts-code-005-运算与表达式)
  - [JSTS-CODE-006: TypeScript规范](#jsts-code-006-typescript规范)
- [二、架构与函数设计](#二架构与函数设计)
  - [JSTS-ARCH-001: 控制语句](#jsts-arch-001-控制语句)
  - [JSTS-ARCH-002: 函数](#jsts-arch-002-函数)
  - [JSTS-ARCH-003: 类与对象](#jsts-arch-003-类与对象)
  - [JSTS-ARCH-004: 作用域与模块](#jsts-arch-004-作用域与模块)
  - [JSTS-ARCH-005: 必须使用依赖注入而非硬编码import具体实现](#jsts-arch-005-必须使用依赖注入而非硬编码import具体实现)
  - [JSTS-ARCH-006: 禁止Prop Drilling超过3层](#jsts-arch-006-禁止prop-drilling超过3层)
- [三、安全编码](#三安全编码)
  - [JSTS-SEC-001: 禁止innerHTML/dangerouslySetInnerHTML渲染用户输入](#jsts-sec-001-禁止innerhtmldangerouslysetinnerhtml渲染用户输入)
  - [JSTS-SEC-002: 禁止eval/Function/setTimeout字符串参数](#jsts-sec-002-禁止evalfunctionsettimeout字符串参数)
  - [JSTS-SEC-003: 禁止child_process注入用户输入](#jsts-sec-003-禁止child_process注入用户输入)
  - [JSTS-SEC-004: 禁止硬编码密钥和凭证到前端代码](#jsts-sec-004-禁止硬编码密钥和凭证到前端代码)
  - [JSTS-SEC-005: 必须对Cookie设置安全属性](#jsts-sec-005-必须对cookie设置安全属性)
  - [JSTS-SEC-006: 禁止原型污染](#jsts-sec-006-禁止原型污染)
  - [JSTS-SEC-007: 禁止fs路径拼接未校验用户输入](#jsts-sec-007-禁止fs路径拼接未校验用户输入)
  - [JSTS-SEC-008: 其他安全规则](#jsts-sec-008-其他安全规则)
- [四、并发与资源管理](#四并发与资源管理)
  - [JSTS-CON-001: 禁止未处理的Promise拒绝](#jsts-con-001-禁止未处理的promise拒绝)
  - [JSTS-CON-002: 必须在useEffect中清理副作用](#jsts-con-002-必须在useeffect中清理副作用)
  - [JSTS-CON-003: 禁止RxJS订阅泄漏](#jsts-con-003-禁止rxjs订阅泄漏)
- [五、React/TS 特有规则](#五reactts-特有规则)
  - [JSTS-REACT-001: 禁止useEffect依赖数组不完整](#jsts-react-001-禁止useeffect依赖数组不完整)
  - [JSTS-REACT-002: 禁止保留console.log/debugger语句](#jsts-react-002-禁止保留consolelogdebugger语句)
  - [JSTS-REACT-003: 必须为React列表提供稳定key](#jsts-react-003-必须为react列表提供稳定key)
  - [JSTS-REACT-004: 禁止使用var声明变量](#jsts-react-004-禁止使用var声明变量)
  - [JSTS-REACT-005: 必须处理null/undefined使用可选链](#jsts-react-005-必须处理nullundefined使用可选链)
  - [JSTS-REACT-006: 禁止使用==做隐式类型转换比较](#jsts-react-006-禁止使用做隐式类型转换比较)
  - [JSTS-REACT-007: 禁止在TypeScript中使用any类型](#jsts-react-007-禁止在typescript中使用any类型)
  - [JSTS-REACT-008: 必须启用TypeScript严格模式](#jsts-react-008-必须启用typescript严格模式)
  - [JSTS-REACT-009: JSX组件新增prop时必须检查原有prop是否遗漏](#jsts-react-009-jsx组件新增prop时必须检查原有prop是否遗漏)
- [六、性能优化](#六性能优化)
  - [JSTS-PERF-001: 禁止在循环中进行DOM操作](#jsts-perf-001-禁止在循环中进行dom操作)
  - [JSTS-PERF-002: 禁止同步文件系统操作](#jsts-perf-002-禁止同步文件系统操作)
  - [JSTS-PERF-003: 必须对高频事件使用防抖或节流](#jsts-perf-003-必须对高频事件使用防抖或节流)
  - [JSTS-PERF-004: 禁止N+1数据库/API查询](#jsts-perf-004-禁止n1数据库api查询)
  - [JSTS-PERF-005: 必须对React纯组件使用memo/useMemo/useCallback](#jsts-perf-005-必须对react纯组件使用memousememousecallback)
- [七、检测要求与忽略规则](#七检测要求与忽略规则)

---

## 一、代码风格、可读性与自文档化

### JSTS-CODE-001: 命名

- **检查锚点**: 类名非大驼峰, 变量/函数非小驼峰, 布尔变量缺少is/has/can前缀, 常量非全大写下划线分隔, 类属性缺少访问修饰符, 保留字作变量名
- **反例**:
  - `const myclass = class {}` — 类名非大驼峰
  - `let disabled = true` — 布尔变量用否定词且无前缀
  - `let class = 'foo'` — 保留字作变量名
  - `const count = 5` — 常量非全大写
  - `class Foo { name: string }` — 属性未加访问修饰符
- **正例**:
  - `const MyClass = class {}` — 类名大驼峰
  - `let isDisabled = true` — 布尔变量加is/has/can前缀
  - `let className = 'foo'` — 避免保留字
  - `const MAX_COUNT = 5` — 常量全大写下划线分隔
  - `class Foo { public name: string }` — 属性添加访问修饰符
- **触发条件**: 类名非大驼峰/变量非小驼峰/布尔变量无is/has/can前缀/常量非全大写
- **严重程度**: suggestion

### JSTS-CODE-002: 注释

- **检查锚点**: TODO/FIXME注释, 注释掉的代码块, 注释中含员工个人信息(工号/姓名/邮箱)
- **反例**:
  - `// TODO: 后续优化性能` — 保留TODO注释
  - `// const oldLogic = computeOld()` — 注释无用代码
  - `// 作者: z30012345 张三` — 注释含员工个人信息
- **正例**:
  - 将待办事项记录到任务管理系统而非代码注释中
  - 删除无用代码，需要时通过Git历史找回
  - 通过版本控制系统记录作者信息，不在注释中标注
- **触发条件**: TODO/FIXME注释/注释掉的代码块/注释含员工个人信息
- **严重程度**: minor

### JSTS-CODE-003: 声明与初始化

- **检查锚点**: var声明, 连续赋值, undefined初始化, 变量遮蔽外层同名变量, 变量声明远离首次使用
- **反例**:
  - `var count = 0` — 使用var声明
  - `const a = b = c = 1` — 连续赋值
  - `let name = undefined` — 用undefined初始化
  - `let x = 1; function foo() { let x = 2 }` — 内层变量遮蔽外层
- **正例**:
  - `const count = 0` — 使用const/let声明
  - `const a = 1; const b = 1; const c = 1` — 每个语句单独声明
  - `let name: string` — 不用undefined初始化
  - `function foo() { const innerX = 2 }` — 避免变量遮蔽
- **触发条件**: var声明/连续赋值/undefined初始化/变量遮蔽外层同名变量
- **严重程度**: minor

### JSTS-CODE-004: 数据类型

- **检查锚点**: 浮点数省略前导0或小数点后0, 用===判断NaN, 浮点数直接===比较, 双引号字符串, 字符串用+拼接, 查找表用Object代替Map/Set, 隐式类型转换
- **反例**:
  - `const num = .5` — 浮点数省略前导0
  - `if (value === NaN)` — 用===判断NaN
  - `if (0.1 + 0.2 === 0.3)` — 浮点数直接比较
  - `const str = "hello"` — 双引号字符串
  - `const msg = "Hello " + name` — 用+拼接字符串
  - `const lookup = { a: 1, b: 2 }` — 用Object做查找表
  - `const num = +str` — 隐式类型转换
- **正例**:
  - `const num = 0.5` — 浮点数不省略前导0
  - `if (Number.isNaN(value))` — 用isNaN()判断NaN
  - `if (Math.abs(0.1 + 0.2 - 0.3) < Number.EPSILON)` — 浮点数比较用差值阈值
  - `const str = 'hello'` — 单引号字符串
  - `` const msg = `Hello ${name}` `` — 模板字符串拼接
  - `const lookup = new Map([['a', 1], ['b', 2]])` — 用Map做查找表
  - `const num = Number(str)` — 显式类型转换
- **触发条件**: ==或!=比较/隐式类型转换/双引号字符串/字符串+拼接/查找表用Object
- **严重程度**: minor

### JSTS-CODE-005: 运算与表达式

- **检查锚点**: ==或!=比较, 嵌套三元表达式, 混合运算符缺少括号, 正则中空白字符未显式指定重复次数, 正则未使用命名捕获组
- **反例**:
  - `if (a == b)` — 使用==比较
  - `const x = a ? b : c ? d : e` — 嵌套三元表达式
  - `const result = a + b * c` — 混合运算符无括号
  - `/\s+/` — 正则空白字符未指定次数
  - `/(\d{4})-(\d{2})/` — 正则未使用命名捕获组
- **正例**:
  - `if (a === b)` — 使用===比较
  - `const x = a ? b : (c ? d : e)` — 拆解或括号明确嵌套三元
  - `const result = a + (b * c)` — 括号明确优先级
  - `/\s{1,}/` — 正则显式指定重复次数
  - `/(?<year>\d{4})-(?<month>\d{2})/` — 正则使用命名捕获组
- **触发条件**: 嵌套三元表达式/混合运算符缺括号/正则未用命名捕获组
- **严重程度**: minor

### JSTS-CODE-006: TypeScript规范

- **检查锚点**: any类型, interface与type混用定义对象, 类成员声明顺序不一致, 用type定义对象类型而非interface, 简单数组用T[]而非Array<T>, 可选成员用undefined而非?, 函数缺少返回值类型, 枚举属性名非大写, 枚举值未显式定义, 非空断言!, 非空判断而非可选链/空值合并, 布尔表达式依赖隐式转换
- **反例**:
  - `function process(data: any) {}` — 使用any
  - `type User = { name: string }` — 用type定义对象类型
  - `let ids: number[]` — 复杂数组类型用T[]
  - `interface User { name?: string; age: number | undefined }` — 用undefined定义可选
  - `function add(a: number, b: number) { return a + b }` — 缺少返回值类型
  - `enum Color { red, green }` — 枚举属性名非大写且值未显式定义
  - `const name = user!.name` — 非空断言
  - `const val = input !== null && input !== undefined ? input : 'default'` — 非空判断而非空值合并
  - `if (obj.prop)` — 布尔表达式依赖隐式转换
- **正例**:
  - `function process(data: UserData) {}` — 使用具体类型
  - `interface User { name: string }` — 用interface定义对象类型
  - `let ids: Array<number>` — 复杂数组类型用Array<T>
  - `interface User { name?: string; age: number }` — 用?定义可选成员
  - `function add(a: number, b: number): number { return a + b }` — 显式返回值类型
  - `enum Color { RED = 'RED', GREEN = 'GREEN' }` — 枚举属性名大写且显式定义值
  - `const name = user?.name` — 可选链替代非空断言
  - `const val = input ?? 'default'` — 空值合并运算符
  - `if (obj.prop !== undefined)` — 布尔表达式显式判断
- **触发条件**: any类型/type定义对象类型/非空断言!/函数缺返回值类型/枚举属性名非大写
- **严重程度**: major

---

## 二、架构与函数设计

### JSTS-ARCH-001: 控制语句

- **检查锚点**: switch无default分支, case无break, case中词法声明无大括号, if-else if无else收尾, 逻辑运算符代替if语句, 条件/循环中条件过多
- **反例**:
  - `switch (x) { case 1: fn1() }` — switch无default
  - `switch (x) { case 1: fn1(); case 2: fn2() }` — case缺少break
  - `switch (x) { case 1: let a = 1; break }` — case中词法声明无大括号
  - `if (a) {} else if (b) {}` — 无else收尾
  - `condition && doSomething()` — 逻辑运算符代替控制语句
  - `if (a && b || c && d || e) {}` — 条件过多
- **正例**:
  - `switch (x) { case 1: fn1(); break; default: break }` — switch含default
  - `switch (x) { case 1: fn1(); break; case 2: fn2(); break; default: break }` — 每个case有break
  - `switch (x) { case 1: { let a = 1; break } }` — case中词法声明加大括号
  - `if (a) {} else if (b) {} else {}` — else if链以else收尾
  - `if (condition) { doSomething() }` — 使用if语句
  - 拆分为多个条件判断或提取为命名函数降低复杂度
- **触发条件**: switch无default/case无break/if-else if无else/逻辑运算符代替if
- **严重程度**: minor

### JSTS-ARCH-002: 函数

- **检查锚点**: 函数超过40行, 嵌套深度超过4层, 回调嵌套超过4层, 参数超过5个, new Function()动态创建函数, 重新赋值函数入参, 使用arguments对象, 匿名函数使用function关键字
- **反例**:
  - 超过40行的函数 — 违反单一职责和单一抽象层次
  - `if (a) { if (b) { if (c) { if (d) { if (e) {} } } } }` — 嵌套超过4层
  - `fn(a, function(b) { fn2(b, function(c) { fn3(c, function(d) {}) }) })` — 回调嵌套超过4层
  - `function configure(host, port, user, pass, db, timeout, retry)` — 参数超过5个
  - `const fn = new Function('x', 'return x + 1')` — 动态创建函数
  - `function process(input) { input = transform(input) }` — 重新赋值入参
  - `function sum() { return Array.from(arguments).reduce(...) }` — 使用arguments
  - `arr.map(function(item) { return item * 2 })` — 匿名函数用function关键字
- **正例**:
  - 拆分为多个职责单一的小函数，每层抽象一致
  - 提前return、提取子函数降低嵌套深度
  - 使用async/await或Promise链替代深层回调嵌套
  - 使用参数对象: `function configure(options: ConfigOptions)`
  - 使用函数声明或箭头函数: `const fn = (x: number) => x + 1`
  - 使用新变量: `function process(input) { const transformed = transform(input) }`
  - 使用rest语法: `function sum(...nums: number[]) { return nums.reduce(...) }`
  - `arr.map((item) => item * 2)` — 匿名函数用箭头函数
- **触发条件**: 函数超过40行/嵌套超4层/参数超5个/new Function()/重赋值入参
- **严重程度**: major

### JSTS-ARCH-003: 类与对象

- **检查锚点**: 对象属性分散定义, 对象方法未使用简写, 使用方括号访问静态属性名, 实例上直接调用hasOwnProperty, 修改内置对象原型
- **反例**:
  - `const obj = {}; obj.a = 1; obj.b = 2` — 属性分散定义
  - `const obj = { method: function() {} }` — 方法未简写
  - `obj['property']` — 方括号访问静态属性名
  - `obj.hasOwnProperty('key')` — 实例上直接调用hasOwnProperty
  - `Array.prototype.custom = function() {}` — 修改内置对象原型
- **正例**:
  - `const obj = { a: 1, b: 2 }` — 在一处定义所有属性
  - `const obj = { method() {} }` — 使用方法简写
  - `obj.property` — 使用点号访问
  - `Object.prototype.hasOwnProperty.call(obj, 'key')` — 使用原型方法
  - 使用工具函数或子类扩展，不修改内置原型
- **触发条件**: 对象属性分散定义/方法未简写/修改内置对象原型/实例直调hasOwnProperty
- **严重程度**: minor

### JSTS-ARCH-004: 作用域与模块

- **检查锚点**: 全局作用域var/function声明, import顺序混乱, 导出变量被重新赋值, 重复导入同一模块, 导入未使用模块
- **反例**:
  - `var globalVar = 1` — 全局作用域声明变量
  - `import _ from 'lodash'; import fs from 'fs'; import myUtil from './util'` — import顺序混乱
  - `export let config = { host: 'localhost' }; config = { host: 'prod' }` — 导出变量被重新赋值
  - `import { a } from './mod'; import { b } from './mod'` — 重复导入
  - `import { unused } from './mod'` — 导入未使用
- **正例**:
  - 使用模块作用域: `const globalVar = 1` 在模块顶层声明
  - 按内置模块、外部模块、内部模块顺序导入: `import fs from 'fs'; import _ from 'lodash'; import myUtil from './util'`
  - `export const config = Object.freeze({ host: 'localhost' })` — 导出不可变值
  - `import { a, b } from './mod'` — 合并导入
  - 只导入实际使用的标识符
- **触发条件**: 全局var/function声明/import顺序混乱/导出变量被重赋值/导入未使用
- **严重程度**: minor

### JSTS-ARCH-005: 必须使用依赖注入而非硬编码import具体实现

- **检查锚点**: 直接import数据库实现, new具体类在业务逻辑中
- **正例**: 接口定义 + Context/Provider注入实现
- **触发条件**: 业务逻辑中直接import数据库实现或new具体类
- **严重程度**: major

### JSTS-ARCH-006: 禁止Prop Drilling超过3层

- **检查锚点**: 连续3+层组件透传props
- **正例**: 使用 Context, Zustand, Jotai 等状态管理
- **触发条件**: 连续3+层组件透传props
- **严重程度**: major

---

## 三、安全编码

### JSTS-SEC-001: 禁止innerHTML/dangerouslySetInnerHTML渲染用户输入

- **反例**: `element.innerHTML = userInput`
- **正例**: `element.textContent = userInput` 或 DOMPurify.sanitize
- **触发条件**: innerHTML/dangerouslySetInnerHTML赋值为用户输入或外部数据
- **严重程度**: fatal

### JSTS-SEC-002: 禁止eval/Function/setTimeout字符串参数

- **反例**: `eval("var x = " + userInput)`
- **正例**: 使用 JSON.parse 解析数据，函数引用替代字符串
- **触发条件**: `.js`/`.ts`文件中使用eval()/new Function()/setTimeout(字符串)
- **严重程度**: fatal

### JSTS-SEC-003: 禁止child_process注入用户输入

- **反例**: `exec("ls " + userDir)`
- **正例**: `execFile("ls", [userDir])` — 参数分离
- **触发条件**: child_process.exec/spawn拼接用户输入作为命令参数
- **严重程度**: fatal

### JSTS-SEC-004: 禁止硬编码密钥和凭证到前端代码

- **检查锚点**: apiKey=, secret=, password=, Bearer+硬编码
- **触发条件**: 前端代码中出现apiKey=/secret=/password=/Bearer+硬编码字面量
- **严重程度**: fatal

### JSTS-SEC-005: 必须对Cookie设置安全属性

- **反例**: `document.cookie = "token=" + jwt` — 无安全属性
- **正例**: 服务端设置 HttpOnly; Secure; SameSite=Strict
- **触发条件**: document.cookie赋值缺少HttpOnly/Secure/SameSite属性
- **严重程度**: major

### JSTS-SEC-006: 禁止原型污染

- **反例**: `Object.assign(target, JSON.parse(userInput))`
- **正例**: 使用 Map 或 `Object.create(null)` + 白名单字段
- **触发条件**: Object.assign/merge将用户输入合并到对象原型链
- **严重程度**: fatal

### JSTS-SEC-007: 禁止fs路径拼接未校验用户输入

- **反例**: `fs.readFile(path.join(baseDir, userInput))`
- **正例**: `path.resolve(baseDir, userInput).startsWith(baseDir)` — 校验逃逸
- **触发条件**: fs.readFile/path.join拼接用户输入未校验路径逃逸
- **严重程度**: fatal

### JSTS-SEC-008: 其他安全规则

- **检查锚点**: catch块中返回敏感数据, innerHTML未配合DomSanitizer, 复杂正则(嵌套量词/回溯), 代码中含公网IP/URL, 对不可信对象直接JSON.stringify, 外部输入未校验, window.location赋值未校验, Math.random()用于安全场景, postMessage未校验origin, localStorage/sessionStorage存敏感数据
- **反例**:
  - `catch(e) { return e.stack }` — 异常泄露敏感数据
  - `element.innerHTML = data` — 未使用DomSanitizer
  - `/(a+)+$/` — 正则存在ReDos风险
  - `const url = 'http://10.0.0.1/api'` — 代码含公网地址
  - `JSON.stringify(untrustedObj)` — 直接序列化不可信对象
  - `function handle(input) { process(input) }` — 外部数据未校验
  - `window.location.href = userInput` — 跳转未校验地址
  - `const token = Math.random().toString(36)` — 安全场景用Math.random
  - `window.addEventListener('message', handler)` — postMessage未校验origin
  - `localStorage.setItem('token', jwt)` — 敏感数据存入localStorage
- **正例**:
  - `catch(e) { logger.error('操作失败'); return null }` — 异常不泄露内部信息
  - `element.innerHTML = DomSanitizer.sanitize(data)` — 配合DomSanitizer
  - 正则尽量简单，避免嵌套量词，设置匹配超时
  - 敏感地址通过环境变量或配置中心获取
  - 对不可信对象白名单字段提取后再序列化
  - `function handle(input: string) { const validated = validate(input); process(validated) }` — 外部数据先校验
  - `const allowed = ['/home', '/about']; if (allowed.includes(userInput)) window.location.href = userInput` — 校验跳转地址
  - `const token = crypto.getRandomValues(new Uint32Array(1))` — 安全场景用密码学安全随机数
  - `window.addEventListener('message', (e) => { if (e.origin === 'https://trusted.com') handler(e) })` — 校验origin
  - 敏感数据仅存于内存或服务端session中
- **触发条件**: catch返回敏感数据/复杂正则ReDos/代码含公网IP/Math.random()用于安全场景
- **严重程度**: fatal

---

## 四、并发与资源管理

### JSTS-CON-001: 禁止未处理的Promise拒绝

- **反例**: `fetch(url).then(r => r.json())` — 无catch
- **正例**: `fetch(url).then(r => r.json()).catch(handleError)` 或 try-catch
- **触发条件**: Promise/.then()链无.catch()或await无try-catch
- **严重程度**: major

### JSTS-CON-002: 必须在useEffect中清理副作用

- **反例**: `useEffect(() => { timer = setInterval(fn, 1000) }, [])` — 不清理
- **正例**: `useEffect(() => { const id = setInterval(fn, 1000); return () => clearInterval(id) }, [])`
- **触发条件**: useEffect中创建定时器/订阅/事件监听但无return清理函数
- **严重程度**: major

### JSTS-CON-003: 禁止RxJS订阅泄漏

- **反例**: `this.service.getData().subscribe(data => ...)` — 不取消
- **正例**: `this.service.getData().pipe(takeUntil(this.destroy$)).subscribe(...)`
- **触发条件**: .subscribe()调用未配对takeUntil/takeWhile等取消逻辑
- **严重程度**: major

---

## 五、React/TS 特有规则

### JSTS-REACT-001: 禁止useEffect依赖数组不完整

- **反例**: `useEffect(() => { fetchData(id) }, [])` — 缺id依赖
- **正例**: `useEffect(() => { fetchData(id) }, [id])`
- **触发条件**: useEffect闭包引用外部变量但依赖数组未包含该变量
- **严重程度**: major

### JSTS-REACT-002: 禁止保留console.log/debugger语句

- **正例**: 使用日志库，生产构建自动去除
- **触发条件**: 源码中存在console.log/console.warn/debugger语句
- **严重程度**: minor

### JSTS-REACT-003: 必须为React列表提供稳定key

- **反例**: `<li key={index}>`
- **正例**: `<li key={item.id}>`
- **触发条件**: JSX列表中使用index作为key或无key属性
- **严重程度**: minor

### JSTS-REACT-004: 禁止使用var声明变量

- **正例**: `const` 不可变，`let` 可变，禁止 `var`
- **触发条件**: 使用var关键字声明变量
- **严重程度**: minor

### JSTS-REACT-005: 必须处理null/undefined使用可选链

- **反例**: `user && user.address && user.address.city`
- **正例**: `user?.address?.city`
- **触发条件**: 多层&&链式访问嵌套属性而非使用可选链?.
- **严重程度**: minor

### JSTS-REACT-006: 禁止使用==做隐式类型转换比较

- **反例**: `if (value == "1")`
- **正例**: `if (value === "1")`
- **触发条件**: 使用==或!=进行比较而非===或!==
- **严重程度**: minor

### JSTS-REACT-007: 禁止在TypeScript中使用any类型

- **反例**: `function process(data: any) { ... }`
- **正例**: `function process(data: UserData) { ... }`
- **触发条件**: TypeScript代码中变量/参数类型声明为any
- **严重程度**: major

### JSTS-REACT-008: 必须启用TypeScript严格模式

- **正例**: `tsconfig.json: { "compilerOptions": { "strict": true } }`
- **触发条件**: tsconfig.json中compilerOptions.strict未设为true
- **严重程度**: major

### JSTS-REACT-009: JSX组件新增prop时必须检查原有prop是否遗漏

- **检查锚点**: `.jsx`/`.tsx`文件diff中同一个组件标签`<Xxx`有新增prop，且相邻的旧行(`[O]`)中有prop被删除
- **触发条件**: diff中同一组件标签出现prop新增时，必须检查是否有prop被误删。以下prop组合必须成对出现：
  - `hasXxxBtn`/`showXxx` + 对应的 `handleXxxBtn`/`onXxxClick`（显示控制 + 事件处理）
  - `firstSrc`/`secondSrc` + 对应的 `handleFirstBtn`/`handleSecondBtn`（图标 + 点击处理）
  - `disabled`/`loading` + 对应的 `onClick`/`handleSubmit`（状态 + 行为）
- **检测方法**: 逐行对比同一组件标签的 [O] 行和 [N] 行，如果 [O] 行有 `handleXxx`/`onXxx` 类prop被删除，而 [N] 行中该组件仍保留 `hasXxxBtn`/`xxxSrc` 等显示prop，则报出
- **严重程度**: major（功能丢失——按钮存在但点击无响应）
- **反例**:
  - 删除 `handleFirstBtn={this.openHistory}` 后只添加了 `hasSecondBtn`/`handleSecondBtn`，但 `hasFirBtn` 和 `firstSrc` 仍在 → 历史按钮可见但点击无响应
  - 删除 `onClick={this.handleSubmit}` 但保留 `disabled={false}` 和按钮文本 → 提交按钮无法点击
  - 删除 `onChange={this.handleChange}` 但保留 `value={this.state.val}` → 输入框显示但无法编辑
- **正例**:
  - 新增 `hasSecondBtn`/`handleSecondBtn` 时保留原有 `handleFirstBtn`（两行并存）
  - 删除 `handleFirstBtn` 的同时删除 `hasFirBtn` 和 `firstSrc`（功能整体移除）
  - 重构 prop 名但保持功能完整：`handleFirstBtn` → `onFirstClick`（有对应替换）

---

## 六、性能优化

### JSTS-PERF-001: 禁止在循环中进行DOM操作

- **反例**: `items.forEach(i => { container.innerHTML += `<div>${i}</div>` })`
- **正例**: `container.innerHTML = items.map(i => `<div>${i}</div>`).join('')`
- **触发条件**: 循环体内操作DOM(innerHTML+=/appendChild)
- **严重程度**: major

### JSTS-PERF-002: 禁止同步文件系统操作

- **反例**: `const data = fs.readFileSync(path)` — 阻塞事件循环
- **正例**: `const data = await fs.promises.readFile(path)`
- **触发条件**: 使用fs.readFileSync/fs.readdirSync等同步文件系统方法
- **严重程度**: major

### JSTS-PERF-003: 必须对高频事件使用防抖或节流

- **反例**: `window.addEventListener('scroll', handleScroll)` — 无debounce
- **正例**: `window.addEventListener('scroll', debounce(handleScroll, 100))`
- **触发条件**: scroll/resize/input等高频事件监听无debounce/throttle包装
- **严重程度**: minor

### JSTS-PERF-004: 禁止N+1数据库/API查询

- **反例**: `for (const id of ids) { await fetch(`/api/item/${id}`) }`
- **正例**: `await Promise.all(ids.map(id => fetch(`/api/item/${id}`)))` 或批量接口
- **触发条件**: 循环中逐个await数据库查询或API请求
- **严重程度**: major

### JSTS-PERF-005: 必须对React纯组件使用memo/useMemo/useCallback

- **反例**: `<Child onClick={() => handleClick()} items={[1,2,3]} />`
- **正例**: `const onClick = useCallback(handleClick, []); const items = useMemo(() => [1,2,3], [])`
- **触发条件**: React纯组件props传入内联箭头函数或每次渲染新建对象/数组
- **严重程度**: minor

---

## 七、检测要求与忽略规则

### 检测要求

- 结合整个代码片段上下文分析，不要孤立看待单行代码
- 自动跳过测试代码（.test.ts / .spec.ts 结尾）
- 自动跳过 demo 代码（demo/ 目录下）
- 相同代码问题只提一次
- finding 严重程度不超过"一般"
- 对每个发现的问题分别复查是否真实存在，避免误报

### 忽略规则

- `SomeClass.staticMethod()` 形式调用的代码，完全跳过分析
- 属性被赋值为 Observable 是正确的，不要报告类型错误
- MCP 工具名称等嵌入装饰器的字符串，不是"硬编码"问题
- 仅对类中未被装饰的普通变量/方法/私有属性进行命名审查
- 仅当明确存在新的 `.subscribe()` 调用且缺失销毁逻辑时，才报告内存泄漏
- i18n 国际化取值时，忽略键的硬编码字符串检查
- 当变量已被类型守卫或 API 保证非空时，跳过空值检查建议
