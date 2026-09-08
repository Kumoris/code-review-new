# Code Review New

Codex 原生多 Agent 代码检视 Skill，支持 GitHub PR、本地 Git diff、全仓基线审计，以及聚合多个子 PR 的 Manifest 模式。

Codex 调度 Reviewer、Adversary 和 Synthesizer；Python 脚本负责固定源码快照、精确行号、身份绑定、准入门控和输出完整性。完整规范见 [SKILL.md](SKILL.md)，设计说明见 [project_introduction.txt](project_introduction.txt)。

```text
Context → Routing → Reviewer → Adversary → Deep Review
        → Synthesizer / Admission → Output
```

## 安装与使用

需要 Codex、Python 3.10+ 和 Git。运行脚本使用 Python 标准库，无需安装独立 LLM SDK。当前实现使用 `fcntl`，适用于 macOS/Linux。

将仓库克隆到本地后，把仓库目录链接到用户级 Skill 目录：

```bash
git clone https://github.com/Kumoris/code-review-new.git
cd code-review-new
mkdir -p "$HOME/.agents/skills"
ln -s "$PWD" "$HOME/.agents/skills/code-review-new"
```

如果目标 Skill 已存在，应先检查原有安装位置，避免覆盖。刷新 Codex 后，在目标项目任务中输入：

```text
$code-review-new 请检视当前暂存区的代码变更。
$code-review-new 请对当前仓库进行全仓基线审查，仅生成本地报告。
$code-review-new 请检视 https://github.com/OWNER/REPO/pull/NUMBER，仅生成报告。
```

完整多 Agent 流程由 Codex 按 Skill 规范执行。单独运行下面的上下文命令只会准备审查输入，不会自动完成语义审查：

```bash
# 将 /path/to/code-review-new 替换为 Skill 仓库的实际路径。
# 本地模式需要在被审查的 Git 仓库中运行。
python3 /path/to/code-review-new/scripts/local_context.py
python3 /path/to/code-review-new/scripts/local_context.py --range BASE..HEAD
python3 /path/to/code-review-new/scripts/local_context.py --whole-repo
python3 /path/to/code-review-new/scripts/github_context.py https://github.com/OWNER/REPO/pull/NUMBER
```

全仓模式读取 Git 已跟踪的当前文本文件，记录排除项，始终仅输出本地报告。最多 8 个审查 task，Reviewer 最多 5 个并发。

## 配置与发布

按 [config.json.example](config.json.example) 创建本地配置。凭证只从 `GITHUB_TOKEN` 或指定环境变量读取，不写入配置文件。GitHub Enterprise 可配置 API base URL。

GitHub review 默认为 dry-run；显式 `--apply` 才能写入，且必须通过完整性与当前 SHA 校验。批准、请求修改和合并需要额外明确授权。本地会话和个性化配置已由 `.gitignore` 排除。

## 验证与脱敏案例

在本仓库目录运行离线单测：

```bash
python3 -B -m unittest discover -s tests -v
python3 -B artifacts/sanitized-review-case-20260907/verify_package.py
python3 -B artifacts/sanitized-review-case-20260907/reproduce.py
```

[脱敏案例说明](artifacts/sanitized-review-case-20260907/README.md)提供代码差异、版本哈希、审查报告、三角色原始回执及可重跑检查；包含一个确认缺陷和一个明确标注的误报负对照。案例是单模块本地基线审查，不代表全仓审计或真实 GitHub 写入验证。

已知限制：案例记录了 `local_context.py` 对特定 `+++ ` / `--- ` hunk 正文的解析缺陷，修复目前仅在案例副本验证，尚未应用到运行脚本。详情及两行修复建议见[案例报告](artifacts/sanitized-review-case-20260907/review-report.md)。

## 目录

| 目录 | 内容 |
|---|---|
| `agents/` | Reviewer、Adversary、Synthesizer 与零发现复核角色 |
| `scripts/` | 上下文、路由、准入、回执和发布脚本 |
| `references/` | 语言规则、误报规避与完整性契约 |
| `tests/`、`evals/` | 离线测试和制品断言 |
| `artifacts/` | 已脱敏的可复核案例 |
