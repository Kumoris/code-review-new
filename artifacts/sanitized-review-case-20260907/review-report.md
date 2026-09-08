# 本地差异解析模块审查报告

审查日期：2026-09-07。对象：当前 `scripts/local_context.py` 的固定副本。范围：一个模块的基线审查。输出仅供本地报告。

本案例包含一个已复现的有效发现，以及一个被排除的命令注入误报假设。原项目没有 Git 仓库元数据，因此没有可提供的原始 commit 或 PR base/head。下列文件 SHA-256 是对应源码版本的标识。

| 版本 | SHA-256 |
|---|---|
| 审查时原版 | `4c680f657a457be1de4d217fe4df72797251213cde23ba16c40cada760136b4f` |
| 修复建议副本 | `f8d879d2e7bc66b79136b9e08445d9893b62f01cc44f896a1352a9c3feee8157` |

完整版本和运行指纹见 `versions.json`。匿名快照提交仅为本次审查创建，不代表项目发布版本。

## 有效发现：差异内容被当成文件头，造成路径和锚点损坏

位置：原版 `local_context.py:315` 与 `:322`，对应固定快照 `[N315]`、`[N322]`。严重程度：`major`，置信度 `10/10`，独立 Adversary 裁定 `DEFINITE`。规则：`BIZ-DATA-001`（数据映射语义）及 `BIZ-SCENARIO-001`（当前可达场景）。

触发路径为 `context_mode → get_diff → format_diff_with_anchors`。解析器在处理 hunk 内容之前，先判断一行是否以 `--- ` 或 `+++ ` 开头，却没有限制该分支只能出现在 hunk 之外。

例如匿名 C++ 样例将第 2 行 `counter += 1;` 改为合法语句 `++ counter;`。Git 为新增行加上一个 `+` 后，得到：

```diff
@@ -1,4 +1,4 @@
 int step(int counter) {
-counter += 1;
+++ counter;
 return counter;
 }
```

原版把 `+++ counter;` 当成新文件头，设置文件路径为 `counter;`，丢失 `[N2]++ counter;`，后续 `return counter;` 也从正确的 `[C3]` 错标成 `[C2]`。真实 staged CLI 随后产生 `PARTIAL` 和 `missing_patch:counter.cpp`，使这份本可正常审查的文本差异无法完整进入流程。

这是数据归属和行号解析缺陷。已验证的后果是审查输入不完整；本案例没有证明实际远程发布了错误评论。原有发布门仍保持关闭。

这两条规则在注册表中均为 `review-required`，本例满足明确的 3/3 缺陷证明：

- 当前输入与路径：真实 Git 生成的 `fixtures/input.diff`，以及 staged CLI 运行。
- 实际错误结果：`verification.json` 中错误的 `counter;`、缺失的 `[N2]` 和 `PARTIAL` 状态。
- 精确位置与规则：固定源码 `[N315]`、`[N322]`，违反 `BIZ-DATA-001` 的数据映射约束。

修复建议仅增加 `not in_hunk` 条件，使 `--- ` / `+++ ` 文件头分支只在 hunk 外生效，详见 `fix.diff`。相同条件也修复删除 `-- counter;` 时 `[O]` 行丢失及旧侧行号偏移。修改只放在包内的 proposed 副本，项目源码仍保持原版。

## 已排除误报：版本字符串含 Shell 分隔符就会执行命令

假设位置：原版 `local_context.py:92`，辅助证据 `:101`。假设规则：`COM-SEC-007`。

候选说法是“用户可传入版本字符串，所以 `subprocess.run` 会执行其中的 Shell 命令”。这一项是控制器为本案例提供的负对照，已要求独立 Reviewer 和 Adversary 判断；不是历史 Reviewer 自发产生的 finding。

独立 Adversary 将这一假设裁定为 `SPECULATIVE / refuted`，单独保存在 `audit/inbox/raw/adversary.json` 的 `rejected_hypotheses`。源码实际调用形式为：

```python
subprocess.run(["git", *command], capture_output=True, text=True, cwd=git_root)
```

验证输入为单个参数 `HEAD; touch review_case_marker`，只在临时仓库执行。对真实子进程调用的观测表明参数列表原样保留，未启用 `shell=True`。Git 拒绝该字面量 revision，标记文件没有生成。因此，当前所述的 Shell 命令注入路径不成立，该假设不进入最终 finding。

这个反证只排除上述 Shell 注入说法，不能外推为所有 Git 参数、配置、hook 或外部程序调用均已通过安全审查。

## 验证与证据范围

`verification.json` 记录六项通过的案例检查：新增内容归属、新增及上下文行号、删除内容和旧侧行号、普通 diff 兼容性、命令注入负对照、真实 staged 上下文入口。原版出现预期缺陷，修复副本通过相同输入。

本次使用真实独立 Reviewer、Adversary、Synthesizer，并保存捕获后的原始响应。固定范围、身份绑定、回执、最终准入和缺陷证明的结果见 `audit/`。误报负对照在独立字段中留痕，不计入 Reviewer 的有效 finding，也不伪装成 Admission 拒绝数量。

最终完整性校验结果为 `complete`：三份必需 Agent 回执均已捕获，错误与警告均为空；`publish_allowed=false`，`publication_mode=report_only`。`run.json` 保存不可修改的初始化状态，最终状态以 `audit/submission/review-integrity.json` 为准。

本次为模块基线审查，未执行 change-based Deep Review；保留结果非零，因此不触发零发现 second pass。这里的流程完整性只适用于已声明的单模块范围，不表示全仓覆盖、完整框架 E2E 评测或真实 GitHub 写入验证。
