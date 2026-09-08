# CodeGuard 安全规则

> 来源：code-review skill 独占（23条安全规则 + 3条始终应用规则）

---

## 目录

- [一、加密安全（Cryptographic Security）](#一加密安全cryptographic-security)
  - [CG-CRYPTO-001: 密码学算法与后量子就绪](#cg-crypto-001-密码学算法与后量子就绪)
  - [CG-CRYPTO-002: 数字证书最佳实践](#cg-crypto-002-数字证书最佳实践)
  - [CG-CRYPTO-003: 硬编码凭证禁止](#cg-crypto-003-硬编码凭证禁止)
  - [CG-CRYPTO-004: 附加密码学与TLS](#cg-crypto-004-附加密码学与tls)
- [二、认证与MFA](#二认证与mfa)
  - [CG-AUTH-001: 认证与多因素认证](#cg-auth-001-认证与多因素认证)
- [三、授权与访问控制](#三授权与访问控制)
  - [CG-AUTHZ-001: 授权与访问控制](#cg-authz-001-授权与访问控制)
- [四、输入验证与注入防御](#四输入验证与注入防御)
  - [CG-INJECT-001: 输入验证与注入防御](#cg-inject-001-输入验证与注入防御)
- [五、客户端Web安全](#五客户端web安全)
  - [CG-WEB-001: 客户端Web安全](#cg-web-001-客户端web安全)
- [六、会话管理与Cookie](#六会话管理与cookie)
  - [CG-SESS-001: 会话管理与Cookie](#cg-sess-001-会话管理与cookie)
- [七、数据存储安全](#七数据存储安全)
  - [CG-DATA-001: 数据库与存储安全](#cg-data-001-数据库与存储安全)
- [八、文件处理与上传](#八文件处理与上传)
  - [CG-FILE-001: 文件上传安全](#cg-file-001-文件上传安全)
- [九、XML与序列化](#九xml与序列化)
  - [CG-XML-001: XML与序列化加固](#cg-xml-001-xml与序列化加固)
- [十、日志与监控](#十日志与监控)
  - [CG-LOG-001: 日志与监控](#cg-log-001-日志与监控)
- [十一、隐私与数据保护](#十一隐私与数据保护)
  - [CG-PRIV-001: 隐私与数据保护](#cg-priv-001-隐私与数据保护)
- [十二、供应链安全](#十二供应链安全)
  - [CG-SUPPLY-001: 依赖与供应链安全](#cg-supply-001-依赖与供应链安全)
- [十三、DevOps与容器](#十三devops与容器)
  - [CG-DEVOPS-001: DevOps、CI/CD与容器](#cg-devops-001-devopscicd与容器)
- [十四、Kubernetes安全](#十四kubernetes安全)
  - [CG-K8S-001: Kubernetes加固](#cg-k8s-001-kubernetes加固)
- [十五、基础设施即代码](#十五基础设施即代码)
  - [CG-IAC-001: 基础设施即代码安全](#cg-iac-001-基础设施即代码安全)
- [十六、MCP安全](#十六mcp安全)
  - [CG-MCP-001: MCP (Model Context Protocol) 安全](#cg-mcp-001-mcp-model-context-protocol-安全)
- [十七、移动应用安全](#十七移动应用安全)
  - [CG-MOBILE-001: 移动应用安全](#cg-mobile-001-移动应用安全)
- [十八、框架与语言指南](#十八框架与语言指南)
  - [CG-FRAMEWORK-001: 框架与语言安全指南](#cg-framework-001-框架与语言安全指南)

---

## 一、加密安全（Cryptographic Security）

### CG-CRYPTO-001: 密码学算法与后量子就绪

- **适用语言**: 全语言
- **检查锚点**: MD5, SHA-0, SHA-1, RC2, RC4, Blowfish, DES, 3DES, AES-ECB, AES-CBC, Vigenere, 静态RSA, 匿名Diffie-Hellman, PKCS#1 v1.5, AES_encrypt, AES_decrypt, RSA_new, SHA1_Init, HMAC()
- **反例**: `MD5(data)`, `new DESCryptoServiceProvider()`, `AES.new(key, AES.MODE_ECB)`, `AES_encrypt()`, `RSA_new()`, `SHA1_Init()`, SSL 3.0, TLS 1.0
- **正例**: AES-GCM/ChaCha20-Poly1305加密, SHA-256+哈希, RSA-2048+/ECDHE密钥交换, TLS 1.3, EVP_EncryptInit_ex()+EVP_aes_256_gcm(), X25519MLKEM768混合KEM
- **触发条件**: 代码中包含`MD5`/`SHA1`/`DES`/`RC4`/`AES_ECB`/`Blowfish`等不安全加密算法调用
- **严重程度**: fatal

---

### CG-CRYPTO-002: 数字证书最佳实践

- **适用语言**: 全语言
- **检查锚点**: BEGIN CERTIFICATE, .pem, .crt, .cer, .der, PEM_read_X509, load_pem_x509_certificate, CertificateFactory, notAfter, notBefore, 自签名证书
- **反例**: 使用已过期证书(notAfter已过), RSA<2048位公钥, EC<256位公钥, MD5/SHA-1签名算法, 自签名证书用于生产
- **正例**: 验证notAfter未过期, RSA>=2048位/EC>=256位, SHA-256+签名算法, `openssl x509 -text -noout -in <cert>`验证证书属性
- **触发条件**: 代码中引用`.pem`/`.crt`/`.cer`证书文件或使用`PEM_read_X509`/`CertificateFactory`等证书API
- **严重程度**: major

---

### CG-CRYPTO-003: 硬编码凭证禁止

- **适用语言**: 全语言
- **检查锚点**: AKIA, AGPA, AIDA, AROA, sk_live_, pk_live_, AIza, ghp_, gho_, ghu_, ghs_, ghr_, eyJ, BEGIN PRIVATE KEY, mongodb://user:pass@, password=, api_key=
- **反例**: `String dbPass = "mySecret123"`, `AWS_SECRET_ACCESS_KEY="AKIA..."`, `mongodb://admin:password@host`, `-----BEGIN RSA PRIVATE KEY-----`
- **正例**: 从环境变量/密钥管理服务获取凭证, `process.env.DB_PASSWORD`, `os.environ.get('API_KEY')`, 使用Vault/KMS管理密钥
- **触发条件**: 检测到硬编码的`password=`/`api_key=`/`AKIA`/`BEGIN PRIVATE KEY`等凭证字符串
- **严重程度**: fatal

---

### CG-CRYPTO-004: 附加密码学与TLS

- **适用语言**: C, Go, Java, JavaScript, Kotlin, MATLAB, PHP, Python, Ruby, Swift, TypeScript, XML, YAML
- **检查锚点**: AES-ECB, AES-CBC, MD5, SHA-1, SSL, TLS 1.0, TLS 1.1, Random(), Math.random(), HPKP
- **反例**: `AES.new(key, AES.MODE_ECB)`, `hashlib.md5()`, `new Random()`, `ssl.TLSv1`, `Math.random()`用于安全场景
- **正例**: AES-GCM/ChaCha20-Poly1305加密, SHA-256+哈希, SecureRandom/crypto.randomBytes/secrets模块, TLS 1.3优先(允许1.2兼容), HSTS分阶段部署(max-age>=1年)
- **触发条件**: 代码中使用`AES-ECB`/`AES-CBC`/`MD5`/`SHA-1`/`SSL`/`TLS 1.0`/`Math.random()`等不安全加密或协议
- **严重程度**: fatal

---

## 二、认证与MFA

### CG-AUTH-001: 认证与多因素认证

- **适用语言**: C, Go, Java, JavaScript, Kotlin, MATLAB, PHP, Python, Ruby, Swift, TypeScript
- **检查锚点**: login, authenticate, password, session, MFA, 2FA, OAuth, SAML, JWT, cookie, token, bcrypt, scrypt, PBKDF2, Argon2
- **反例**: `"用户名不存在"`(泄露账户信息), `MD5(password)`存储密码, SMS验证码作为唯一MFA, Implicit/OAuth ROPC流程, `alg: "none"`JWT, 永久锁定账户
- **正例**: 通用错误消息"用户名或密码无效", Argon2id哈希存储密码(m=19-46MiB,t=2-1,p=1), FIDO2/WebAuthn多因素认证, Authorization Code+PKCE流程, 不透明服务端令牌, 渐进退避节流
- **触发条件**: 代码中包含`login`/`authenticate`/`password`/`MFA`/`JWT`/`OAuth`等认证相关逻辑
- **严重程度**: fatal

---

## 三、授权与访问控制

### CG-AUTHZ-001: 授权与访问控制

- **适用语言**: C, Go, Java, JavaScript, PHP, Python, Ruby, TypeScript, YAML
- **检查锚点**: authorize, permission, role, access, admin, @RequestBody, request.body, IDOR, 403, 404
- **反例**: `if (user.role == 'admin')`仅做粗粒度RBAC, `Object.assign(record, req.body)`直接绑定请求体, `return res.status(404).json({error: 'Resource not found for user X'})`泄露资源存在性
- **正例**: ABAC/ReBAC细粒度授权, DTO显式暴露安全可编辑字段, 通用403/404响应, 每个请求验证对象实例权限, 敏感操作Step-Up认证, 记录所有拒绝操作
- **触发条件**: 代码中包含`authorize`/`permission`/`role`/`access`/`@RequestBody`/`req.body`等授权或批量绑定模式
- **严重程度**: major

---

## 四、输入验证与注入防御

### CG-INJECT-001: 输入验证与注入防御

- **适用语言**: Apex, C, Go, HTML, Java, JavaScript, PHP, PowerShell, Python, Ruby, Shell, SQL, TypeScript
- **检查锚点**: execute, query, exec, eval, system, shell, __proto__, constructor, prototype, innerHTML, document.write, String.format,拼接SQL
- **反例**: `"SELECT * FROM users WHERE id=" + userId`, `eval(userInput)`, `Runtime.getRuntime().exec(cmd + userInput)`, `obj[userKey] = value`允许原型污染, `innerHTML = userData`
- **正例**: `PreparedStatement.executeQuery()`, 参数化查询/命令, ProcessBuilder分离命令和参数, `Object.create(null)`防原型污染, 允许列表验证输入, `new Set()`/`new Map()`代替对象字面量
- **触发条件**: 代码中包含`eval`/`exec`/`system`/`innerHTML`/`拼接SQL`/`__proto__`等注入风险模式
- **严重程度**: fatal

---

## 五、客户端Web安全

### CG-WEB-001: 客户端Web安全

- **适用语言**: C, HTML, JavaScript, PHP, TypeScript, Vlang
- **检查锚点**: innerHTML, outerHTML, document.write, eval, new Function, setTimeout(string), setInterval(string), javascript:, data:, __proto__, DOMPurify, CSP, CSRF, SameSite, frame-ancestors
- **反例**: `element.innerHTML = userInput`, `eval(jsonStr)`, `setTimeout("func()", 1000)`, `href = userInput`(未验证协议), `document.write(data)`, Cookie无SameSite/Secure/HttpOnly
- **正例**: `element.textContent = userInput`, DOMPurify消毒HTML, nonce/hash基础CSP, `SameSite=Lax`+`Secure`+`HttpOnly`, `Content-Security-Policy: frame-ancestors 'none'`, SRI校验外部脚本, 沙箱iframe隔离第三方JS
- **触发条件**: 代码中使用`innerHTML`/`document.write`/`eval`/`javascript:`协议/无`SameSite`的Cookie等XSS风险模式
- **严重程度**: fatal

---

## 六、会话管理与Cookie

### CG-SESS-001: 会话管理与Cookie

- **适用语言**: C, Go, HTML, Java, JavaScript, PHP, Python, Ruby, TypeScript
- **检查锚点**: session, cookie, sessionId, localStorage, sessionStorage, HttpOnly, Secure, SameSite, Cache-Control, logout
- **反例**: 会话ID可预测/有含义, `localStorage.setItem('sessionToken', token)`, Cookie缺少HttpOnly/Secure/SameSite, 无空闲/绝对超时, `Cache-Control: public`
- **正例**: CSPRNG生成会话ID(>=64位熵), Cookie:`Secure`+`HttpOnly`+`SameSite=Strict`, 认证/权限变更时重新生成会话ID, 空闲超时2-30分钟+绝对超时4-8小时, `Cache-Control: no-store`, 服务端强制超时+可见注销按钮
- **触发条件**: 代码中包含`session`/`cookie`/`sessionId`/`localStorage`等会话管理相关逻辑
- **严重程度**: major

---

## 七、数据存储安全

### CG-DATA-001: 数据库与存储安全

- **适用语言**: C, JavaScript, SQL, YAML
- **检查锚点**: root, sa, SYS, admin, password, 0.0.0.0, skip-networking, tls, ssl, bind-address
- **反例**: 使用root/sa/SYS内置账户, 数据库硬编码凭证, `bind-address = 0.0.0.0`暴露TCP端口, 无TLS数据库连接, 应用账户拥有管理权限
- **正例**: 每个应用专用账户+最小权限, 凭证存入配置文件/KMS, TLS 1.2+加密连接+受信证书, 禁用TCP时使用本地socket, 隔离数据库服务器
- **触发条件**: 数据库配置中使用`root`/`sa`/`admin`账户或`0.0.0.0`绑定地址或无TLS连接
- **严重程度**: major

---

## 八、文件处理与上传

### CG-FILE-001: 文件上传安全

- **适用语言**: C, Go, Java, JavaScript, PHP, Python, Ruby, TypeScript
- **检查锚点**: upload, file, multipart, Content-Type, filename, extension, magic number, webroot, CSRF
- **反例**: 信任客户端Content-Type, 使用原始文件名存储, 双扩展名`file.php.jpg`, 上传目录在webroot内, 无文件大小限制, 无认证的上传端点
- **正例**: 允许列表验证扩展名+magic number验证文件签名, UUID随机文件名+限制字符集, 图片重写技术销毁恶意内容, 存储在webroot外的独立服务器, 文件大小+解压后大小限制, CSRF保护+杀毒扫描
- **触发条件**: 代码中包含`upload`/`multipart`/`filename`/`Content-Type`等文件上传相关逻辑
- **严重程度**: major

---

## 九、XML与序列化

### CG-XML-001: XML与序列化加固

- **适用语言**: C, Go, Java, PHP, Python, Ruby, XML
- **检查锚点**: DOCTYPE, DTD, ENTITY, XXE, deserialize, unserialize, pickle, BinaryFormatter, ObjectInputStream, resolve_entities, XmlResolver
- **反例**: `<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>`, `pickle.loads(user_data)`, `new BinaryFormatter().Deserialize(stream)`, `unserialize($_GET['data'])`, 未禁用DTD的XML解析
- **正例**: 禁用DTD和外部实体+拒绝DOCTYPE声明, Java:`setFeature("disallow-doctype-decl",true)`, .NET:`DtdProcessing.Prohibit`+`XmlResolver=null`, Python:`defusedxml`或`resolve_entities=False`, 优先JSON+schema验证, 反序列化使用允许列表
- **触发条件**: 代码中包含`DOCTYPE`/`ENTITY`/`XXE`/`deserialize`/`pickle`/`BinaryFormatter`等XML解析或反序列化操作
- **严重程度**: fatal

---

## 十、日志与监控

### CG-LOG-001: 日志与监控

- **适用语言**: C, JavaScript, YAML
- **检查锚点**: log, logger, print, password, token, secret, credential, sessionId, PII, audit, auth, access
- **反例**: `log.info("User password: " + password)`, `console.log(sessionToken)`, 日志中包含原始会话ID/凭证, 无日志注入净化, 无认证/授权事件日志
- **正例**: 记录认证/授权/管理/配置变更/敏感数据访问事件, 结构化日志(JSON)+关联ID+时间戳(UTC/RFC3339), 修订/令牌化敏感字段, 仅追加/WORM存储+篡改检测, 净化日志输入防注入
- **触发条件**: 代码中使用`log`/`logger`/`print`输出包含`password`/`token`/`secret`/`sessionId`等敏感信息
- **严重程度**: major

---

## 十一、隐私与数据保护

### CG-PRIV-001: 隐私与数据保护

- **适用语言**: JavaScript, MATLAB, YAML
- **检查锚点**: IP, privacy, PII, GDPR, encrypt, HTTPS, HSTS, certificate pinning, Argon2, bcrypt, salt, session
- **反例**: 明文存储PII, HTTP传输敏感数据, 返回"用户名不存在"(泄露账户), `MD5(password)`无盐哈希, 客户端存储会话
- **正例**: 强加密存储+HTTPS+HSTS传输, 通用错误消息防账户枚举, Argon2/bcrypt+每用户唯一盐哈希, 服务端存储会话+密码学随机ID, 隐私审计追踪+访问日志, 最小化IP泄露
- **触发条件**: 代码中处理`PII`/`IP`/隐私数据时未加密存储或使用HTTP传输或`MD5`无盐哈希
- **严重程度**: major

---

## 十二、供应链安全

### CG-SUPPLY-001: 依赖与供应链安全

- **适用语言**: Docker, JavaScript, YAML
- **检查锚点**: npm install, npm ci, audit, lockfile, package-lock, SBOM, SLSA, Sigstore, registry, 2FA, SCA, SAST
- **反例**: `npm install`(非`npm ci`), 无lockfile版本锁定, 从不可信源直接安装, 发布未启用2FA, 严重漏洞未在门禁阻止
- **正例**: 允许列表注册表+`npm ci`, lockfile+摘要锁定, 生成SBOM+SLSA/Sigstore证明来源, `npm audit`定期审计修补, 发布启用2FA, CI/CD门禁SCA/SAST/IaC阻止严重问题, 签名制品+部署前验证
- **触发条件**: 构建脚本中使用`npm install`而非`npm ci`或无lockfile或从不可信源安装依赖
- **严重程度**: major

---

## 十三、DevOps与容器

### CG-DEVOPS-001: DevOps、CI/CD与容器

- **适用语言**: Docker, JavaScript, PowerShell, Shell, XML, YAML
- **检查锚点**: privileged, cap-add, root, docker.sock, no-new-privileges, HEALTHCHECK, distroless, alpine, RELRO, PIE, FORTIFY_SOURCE, vault, KMS, secret
- **反例**: `--privileged`运行容器, `USER root`, 挂载`/var/run/docker.sock`, 无TLS启用Docker TCP daemon, 硬编码CI/CD秘密, `cap-add ALL`
- **正例**: `USER`指定非root+`--security-opt=no-new-privileges`, `--cap-drop all`+仅添加所需能力, 只读根文件系统+tmpfs+资源限制, distroless/alpine最小镜像+锁定标签摘要, 密钥通过Docker/K8s secrets挂载, CI/CD秘密从vault/KMS运行时获取+日志屏蔽, 编译加固:`-fstack-protector-all`+PIE+RELRO
- **触发条件**: Dockerfile/CI配置中使用`--privileged`/`USER root`/挂载`docker.sock`/硬编码密钥
- **严重程度**: fatal

---

## 十四、Kubernetes安全

### CG-K8S-001: Kubernetes加固

- **适用语言**: JavaScript, YAML
- **检查锚点**: RBAC, namespace, OPA, Gatekeeper, Kyverno, NetworkPolicy, mTLS, KMS, secret, image, SLSA, Sigstore, podSecurity
- **反例**: cluster-admin角色过度授权, 无网络策略(默认允许), Manifest中明文密钥, 无镜像签名验证, 共享命名空间
- **正例**: 最小权限RBAC+独立命名空间, 准入控制(OPA/Gatekeeper/Kyverno)限制镜像来源/能力/root, 默认拒绝NetworkPolicy+显式出站允许+mTLS, KMS提供者管理密钥+定期轮换, 验证镜像签名+准入时强制来源(SLSA/Sigstore)
- **触发条件**: K8s Manifest中包含`cluster-admin`/无`NetworkPolicy`/明文密钥/无镜像签名验证
- **严重程度**: major

---

## 十五、基础设施即代码

### CG-IAC-001: 基础设施即代码安全

- **适用语言**: C, D, JavaScript, PowerShell, Ruby, Shell, YAML
- **检查锚点**: 0.0.0.0/0, SSH(22), RDP(3389), security_group, ingress, encryption, TLS, anonymous, IAM, wildcard, sensitive, distroless
- **反例**: `ingress 0.0.0.0/0`到SSH(22)/RDP(3389)/数据库端口, 无静态加密, 无传输加密(TLS), 匿名访问, `IAM: "*"`, API密钥代替工作负载身份, IMDSv1
- **正例**: 私有网络(VPC/VNET/VPN)+默认拒绝规则+VPC流日志, 始终配置静态加密+TLS 1.2+传输加密+数据分类, 无匿名访问+无IAM通配符+工作负载身份, distroless最小镜像, Terraform标记`sensitive = true`, 加密数据备份
- **触发条件**: IaC中包含`0.0.0.0/0`入站/`IAM: "*"`/匿名访问/无加密配置/API密钥代替工作负载身份
- **严重程度**: major

---

## 十六、MCP安全

### CG-MCP-001: MCP (Model Context Protocol) 安全

- **适用语言**: Python, JavaScript, TypeScript, Go, Rust, Java
- **检查锚点**: SPIFFE, SPIRE, sandbox, gVisor, Kata, SELinux, SBOM, TLS, prompt injection, PII, LLM, tool, confirm
- **反例**: LLM生成代码以完整用户权限运行, 信任LLM做验证/授权决策, 工具返回全部字段含PII, 无TLS传输, 单一用途工具混用多个职责
- **正例**: SPIFFE/SPIRE工作负载身份验证, 允许列表验证所有输入+净化文件路径+参数化查询, MCP服务器最小权限+gVisor/Kata/SELinux沙箱, 密码学签名+SBOM+客户端签名验证+TLS, 单一用途工具+显式边界, 两阶段提交(草稿+确认)+人在环确认
- **触发条件**: MCP/LLM工具代码中无沙箱隔离/无输入验证/信任LLM做授权决策/工具返回PII
- **严重程度**: major

---

## 十七、移动应用安全

### CG-MOBILE-001: 移动应用安全

- **适用语言**: Java, JavaScript, Kotlin, MATLAB, Perl, Swift, XML
- **检查锚点**: Keychain, Keystore, SharedPreferences, debug, ProGuard, certificate, HTTPS, pinning, root, jailbreak, DeviceCheck, App Attest
- **反例**: 设备上存储用户密码, SharedPreferences存敏感数据, 覆盖自签名证书验证, 生产构建启用调试, 客户端做安全决策, HTTP传输
- **正例**: 平台安全存储(iOS Keychain/Android Keystore)+可撤销令牌, 服务端认证/授权+会话超时+远程注销, HTTPS+证书固定, 静态分析+生产禁用调试+混淆, 运行时防篡改+检测root/越狱/hooking, Android:ProGuard+禁用备份+Google Play Integrity, iOS:App Attest+DeviceCheck+requiresUserAuthentication
- **触发条件**: 移动应用代码中使用`SharedPreferences`存敏感数据/覆盖证书验证/生产启用调试/HTTP传输
- **严重程度**: major

---

## 十八、框架与语言指南

### CG-FRAMEWORK-001: 框架与语言安全指南

- **适用语言**: C, Java, JavaScript, Kotlin, PHP, Python, Ruby, TypeScript, XML, YAML
- **检查锚点**: DEBUG, CsrfViewMiddleware, mark_safe, csrf_token, APP_DEBUG, $request->all(), |raw, eval, html_safe, PreparedStatement, child_process.exec, helmet, NODE_ENV, expose_php, allow_url_fopen
- **反例**: Django:`DEBUG=True`生产环境, `mark_safe(userInput)`, Laravel:`$request->all()`批量赋值, `{!! $var !!}`未转义输出, Rails:`eval(user_input)`, `raw`/`html_safe`跳过转义, Node:`eval()`/`child_process.exec()`, PHP:`allow_url_fopen=On`
- **正例**: Django:`SECURE_SSL_REDIRECT`+HSTS+`CsrfViewMiddleware`+模板自动转义, DRF:显式`fields=[...]`+节流, Laravel:`$request->validated()`+Blade转义+Cookie加密, Symfony:Twig自动转义+Doctrine参数化, Rails:参数化SQL+`protect_from_forgery`+`force_ssl`, .NET:`[Authorize]`+AES-GCM+HTTPS重定向+CSP/HSTS, Java:`PreparedStatement`+参数化日志, Node:`helmet`+速率限制+`NODE_ENV=production`, PHP:`expose_php=Off`+禁用危险函数+会话Cookie标志
- **触发条件**: 框架代码中包含`DEBUG=True`/`mark_safe`/`$request->all()`/`eval`/`child_process.exec`/`allow_url_fopen`等危险模式
- **严重程度**: major
