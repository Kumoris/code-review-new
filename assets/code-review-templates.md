# Code Review 输出模板

Synthesizer 只写评论正文；`submit_reviews.py` 负责生成 GitHub review payload。模板中不得包含内部 proof、receipt、reachability、token 或私有反馈地址。

## 标准问题

```markdown
**问题描述**：
[当前可复现的具体错误]

**原因**：
[触发路径或输入，以及实际错误结果]

**违反规则**：
[references/file.md：RULE-ID 规则名称]

**建议**：
[最小可执行修复]
```

## 深度检视

```markdown
**问题描述**：
[变更及当前调用方错误]

**业务影响分析**：
- **影响范围**：[模块或调用方]
- **风险等级**：[CRITICAL/HIGH/MEDIUM/LOW]
- **实际后果**：[已由当前调用链证明的后果]

**检测路径**：
[Caller → Changed symbol]

**建议**：
[最小修复或兼容方案]
```

## 安全问题

```markdown
**安全类型**：
[凭证泄露/弱密码学/注入/认证/授权/其他]

**问题描述**：
[攻击输入和可达代码路径]

**安全影响**：
[当前可证明的机密性、完整性或可用性影响]

**违反规则**：
[references/codeguard.md：CG-...]

**修复建议**：
[具体修复]
```

## 本地报告摘要

```markdown
## 代码检视总结

| 项目 | 内容 |
|---|---|
| revision | [base..head] |
| 变更文件 | N |
| routed / unsupported | X / Y |
| integrity | complete / partial / blocked |
| publishable / report-only | A / B |
```

## 提交前过滤

1. 缺少具体问题、实际后果或可执行建议：丢弃。
2. 建议与当前代码等价或会降低正确性：丢弃。
3. 只针对配置数值抱怨“魔术数字”：丢弃，除非规则定义了可证明范围。
4. 删除死代码是正确行为；只有当前 `[N]` 行仍暴露完整性缺陷时才报告。
5. 文件和行必须属于固定 diff，且行必须是 `[N]`。
6. 当前 head 已修复的问题：丢弃。
7. 与已有 GitHub review/comment 同文件、相近行和同根因：去重。

## Review Store

```json
[
  {
    "status": "pending",
    "publication_status": "publishable",
    "comment": "**问题描述**：...",
    "file_path": "src/app.py",
    "line": 42,
    "severity": "major",
    "confidence_score": 8,
    "fix_suggestion": "...",
    "issue_summary": "空值输入导致请求失败",
    "category": "correctness"
  }
]
```

内部 severity 使用 `fatal|major|minor|suggestion`。GitHub review event 与 severity 解耦；默认 event 始终为 `COMMENT`。

## GitHub payload

Dry-run 输出由脚本生成，行内评论使用固定 revision：

```json
{
  "commit_id": "fixed-head-sha",
  "event": "COMMENT",
  "comments": [
    {
      "path": "src/app.py",
      "line": 42,
      "side": "RIGHT",
      "body": "..."
    }
  ]
}
```

没有 `--apply` 时不得发送该 payload；APPROVE、REQUEST_CHANGES 和 merge 必须来自用户明确授权。
