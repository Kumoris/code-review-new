# 脱敏代码审查案例

本包以 `code-review-new` 当前本地源码为依据，提供一个实测有效发现和一个被排除的误报假设，供演示和复核。审查范围是 `local_context.py` 模块；不是全框架审计，也不是某个历史业务 PR 的导出。

先读 [审查报告](review-report.md)，再看 [修复建议差异](fix.diff) 和 [对应版本](versions.json)。

| 材料 | 用途 |
|---|---|
| `review-report.md` | 有效发现、误报排除理由、证据边界 |
| `fix.diff` | 两行修复建议；仅作用于包内副本 |
| `versions/observed/local_context.py` | 审查时源码，字节与原项目一致 |
| `versions/proposed/local_context.py` | 已经过本案例验证的修复副本 |
| `versions.json` | 两个版本的 SHA-256、审查 revision、框架文件指纹 |
| `fixtures/input.diff` | 匿名 C++ 输入，由真实 Git 生成，用于复现解析错误 |
| `fixtures/before.cpp` / `after.cpp` | 上述输入的前后版本；人工构造的最小样例 |
| `verification.json` / `reproduce.py` | 六项离线检查结果及重跑入口 |
| `audit/` | 本次真实独立 Agent 的原始输出、准入结果、绑定和回执 |
| `artifact-map.json` / `verify_package.py` | 搬移后复核原始哈希链，不改写被捕获文件 |
| `checksums.json` | 包内文件 SHA-256 清单（不包含清单自身） |

在解压目录执行，需要 Python 3.9+ 和 Git，无额外依赖、无网络访问：

```bash
python3 -B verify_package.py
python3 -B reproduce.py
```

`reproduce.py` 会在临时目录运行真实 Git、执行原版和修复副本，并验证错误及误报排除条件。检测到预期错误是案例通过的条件，不代表原版实现正确。脚本不会修改安装中的 Skill。

脱敏采用最小提取：只包含框架通用源码、匿名样例和本次新建会话；未包含旧业务 MR、组织仓库、个人目录、访问凭证或原始聊天记录。原始 Agent 输出从生成时就使用匿名路径，捕获后保持字节不变。`/private/tmp/review-case-*` 是本次匿名临时目录；复核器通过映射读取包内文件。

原项目目录没有 Git 历史，因此真实源码版本用 SHA-256 标识。`anonymous_fixture_commit` 是本次匿名副本的提交，不能当作项目历史提交。误报项是控制器明确提供的负对照，并经独立复核排除，不能宣传为生产环境误报率或历史命中率。
