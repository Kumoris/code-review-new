#!/usr/bin/env python3
"""Local Git context preparation script.

Creates session from a local git diff or a full tracked-repository snapshot.

Usage:
    python local_context.py [--base-branch <branch> | --base-commit <sha> | --range <base>..<head> | --whole-repo]
    python local_context.py --render-report --context <context.json> --review-store <review_store.json>
"""

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path


DEFAULT_WHOLE_REPO_MAX_FILE_BYTES = 1_000_000
DEFAULT_WHOLE_REPO_EXCLUDE_GLOBS = (
    ".ai/**", ".code-review/**", "node_modules/**", "**/node_modules/**",
    "vendor/**", "**/vendor/**", "dist/**", "**/dist/**",
    "build/**", "**/build/**", "target/**", "**/target/**",
    "*.min.js", "*.min.css", "*.map",
)


def find_git_root() -> str:
    """Find git repository root from current directory."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(json.dumps({
            "type": "ERROR",
            "error_type": "NOT_A_GIT_REPO",
            "message": "Current directory is not a git repository",
        }))
        sys.exit(1)
    return result.stdout.strip()


def load_config() -> dict:
    """Load config.json from skill directory."""
    config_paths = [
        Path(os.getcwd()) / ".code-review-new" / "config.json",
        Path(__file__).parent.parent / "config.json",
    ]
    for p in config_paths:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    return {}


def create_session(project_root: str) -> Path:
    """Create session directory structure."""
    sessions_base = Path(project_root) / ".ai" / "code-review-new" / "sessions"
    sessions_base.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    token = os.urandom(3).hex()
    session_name = f"local-{timestamp}-{token}"
    session_dir = sessions_base / session_name

    for subdir in ["context", "reviewers", "inbox", "admission", "submission"]:
        (session_dir / subdir).mkdir(parents=True, exist_ok=True)

    review_store = session_dir / "submission" / "review_store.json"
    review_store.write_text("[]", encoding="utf-8")

    return session_dir


def diff_args(args) -> list:
    if args.base_branch:
        return [f"origin/{args.base_branch}...HEAD"]
    elif args.base_commit:
        return [f"{args.base_commit}...HEAD"]
    elif args.range:
        return [args.range]
    return ["--cached"]


def run_git(git_root: str, command: list, error_type="GIT_COMMAND_FAILED") -> str:
    result = subprocess.run(["git", *command], capture_output=True, text=True, cwd=git_root)
    if result.returncode != 0:
        print(json.dumps({"type": "ERROR", "error_type": error_type, "message": result.stderr.strip()}))
        sys.exit(1)
    return result.stdout.strip()


def get_diff(git_root: str, args) -> str:
    """Get git diff based on mode."""
    result = subprocess.run(["git", "-c", "core.quotePath=false", "diff", *diff_args(args)], capture_output=True, text=True, cwd=git_root)
    if result.returncode != 0:
        print(json.dumps({"type": "ERROR", "error_type": "GIT_DIFF_FAILED", "message": result.stderr.strip()}))
        sys.exit(1)
    return result.stdout


def get_changed_files(git_root: str, args) -> list:
    result = subprocess.run(
        ["git", "diff", "--name-only", "-z", *diff_args(args)],
        capture_output=True,
        cwd=git_root,
    )
    if result.returncode != 0:
        print(json.dumps({"type": "ERROR", "error_type": "GIT_DIFF_FAILED", "message": result.stderr.decode(errors="replace").strip()}))
        sys.exit(1)
    return [item.decode("utf-8", errors="surrogateescape") for item in result.stdout.split(b"\0") if item]


def _string_list(value) -> list[str]:
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [str(item) for item in value] if isinstance(value, list) else []


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def tracked_files(git_root: str) -> list[str]:
    """Return Git-tracked paths without interpreting quoting or whitespace."""
    result = subprocess.run(["git", "ls-files", "-z"], capture_output=True, cwd=git_root)
    if result.returncode != 0:
        print(json.dumps({
            "type": "ERROR",
            "error_type": "GIT_LS_FILES_FAILED",
            "message": result.stderr.decode(errors="replace").strip(),
        }))
        sys.exit(1)
    return sorted(item.decode("utf-8", errors="surrogateescape") for item in result.stdout.split(b"\0") if item)


def whole_repo_snapshot(git_root: str, config: dict) -> tuple[list[dict], dict]:
    """Build review records where every included current line has an exact [N] anchor."""
    options = config.get("whole_repo", {})
    options = options if isinstance(options, dict) else {}
    max_bytes = int(options.get("max_file_bytes", DEFAULT_WHOLE_REPO_MAX_FILE_BYTES))
    if max_bytes <= 0:
        print(json.dumps({
            "type": "ERROR",
            "error_type": "INVALID_WHOLE_REPO_CONFIG",
            "message": "whole_repo.max_file_bytes must be positive",
        }))
        sys.exit(1)
    exclude_globs = options.get("exclude_globs", list(DEFAULT_WHOLE_REPO_EXCLUDE_GLOBS))
    exclude_globs = _string_list(exclude_globs)
    exclude_suffixes = _string_list(config.get("exclude_file_suffix", ""))

    records, included, excluded = [], [], []
    root = Path(git_root)
    for relative in tracked_files(git_root):
        path = root.joinpath(*Path(relative).parts)
        reason = ""
        if any(relative.endswith(suffix) for suffix in exclude_suffixes):
            reason = "excluded_suffix"
        elif any(fnmatch.fnmatchcase(relative, pattern) for pattern in exclude_globs):
            reason = "excluded_glob"
        elif path.is_symlink():
            reason = "symlink"
        elif not path.is_file():
            reason = "not_regular_file"

        raw = b""
        if not reason:
            try:
                size = path.stat().st_size
                if size > max_bytes:
                    reason = "too_large"
                else:
                    raw = path.read_bytes()
            except OSError:
                reason = "unreadable"
        if not reason and b"\0" in raw:
            reason = "binary"
        if not reason:
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                reason = "non_utf8"
        if reason:
            excluded.append({"path": relative, "reason": reason})
            continue

        lines = text.splitlines()
        digest = hashlib.sha256(raw).hexdigest()
        included.append({
            "path": relative,
            "bytes": len(raw),
            "line_count": len(lines),
            "sha256": digest,
        })
        header = f"@@ -0,0 +1,{len(lines)} @@" if lines else "@@ -0,0 +0,0 @@"
        records.append({
            "file_path": relative,
            "old_path": relative,
            "new_path": relative,
            "status": "snapshot",
            "patch_missing": False,
            "content": [header, *(f"[N{number}]{line}" for number, line in enumerate(lines, 1))],
        })

    repository_sha = hashlib.sha256(_canonical_bytes(included)).hexdigest()
    return records, {
        "schema_version": "1.0",
        "mode": "whole_repo",
        "repository_sha256": repository_sha,
        "policy": {
            "max_file_bytes": max_bytes,
            "exclude_globs": exclude_globs,
            "exclude_suffixes": exclude_suffixes,
        },
        "included_files": included,
        "excluded_files": excluded,
    }


def snapshot_revisions(git_root: str, args) -> tuple:
    head = run_git(git_root, ["rev-parse", "HEAD"])
    if args.base_branch:
        base = run_git(git_root, ["rev-parse", f"origin/{args.base_branch}"])
        selected_head = head
    elif args.base_commit:
        base = run_git(git_root, ["rev-parse", args.base_commit])
        selected_head = head
    elif args.range:
        match = re.fullmatch(r"(.+?)(\.\.\.?)(.+)", args.range)
        if not match:
            print(json.dumps({"type": "ERROR", "error_type": "INVALID_RANGE", "message": "--range must be BASE..HEAD or BASE...HEAD"}))
            sys.exit(1)
        base = run_git(git_root, ["rev-parse", match.group(1)])
        selected_head = run_git(git_root, ["rev-parse", match.group(3)])
    else:
        base = selected_head = head
    merge = subprocess.run(["git", "merge-base", base, selected_head], capture_output=True, text=True, cwd=git_root)
    return base, selected_head, merge.stdout.strip() if merge.returncode == 0 else base


def parse_diff_to_changed_files(diff_text: str) -> list:
    """Parse unified diff to extract changed file paths."""
    changed = []
    old_path = ""
    for line in diff_text.splitlines():
        if line.startswith("--- a/"):
            old_path = line[6:]
        elif line.startswith("+++ b/"):
            path = line[6:]
            if path not in changed:
                changed.append(path)
        elif line == "+++ /dev/null" and old_path and old_path not in changed:
            changed.append(old_path)
    return changed


def format_diff_with_anchors(diff_text: str) -> list:
    """Convert unified diff to diffs.json format with [N]/[C]/[O] anchors.

    Returns a list of diff records, one per changed file.
    Uses the unified GitHub/local context schema.
    """
    import re

    records = []
    current_file = None
    current_old_path = None
    current_new_path = None
    current_content = []

    in_hunk = False
    line_num_old = 0
    line_num_new = 0
    current_status = "modified"
    patch_missing = False

    for line in diff_text.splitlines():
        if line.startswith("diff --git"):
            # Save previous file
            if current_file:
                records.append({
                    "file_path": current_file,
                    "old_path": current_old_path or current_file,
                    "new_path": current_new_path,
                    "status": current_status,
                    "patch_missing": patch_missing,
                    "content": current_content,
                })
            current_content = []
            parts = shlex.split(line)
            current_old_path = parts[2][2:] if len(parts) >= 4 and parts[2].startswith("a/") else None
            current_new_path = parts[3][2:] if len(parts) >= 4 and parts[3].startswith("b/") else None
            current_file = current_new_path or current_old_path
            in_hunk = False
            current_status = "modified"
            patch_missing = False
        elif line.startswith("new file mode"):
            current_status = "added"
        elif line.startswith("deleted file mode"):
            current_status = "removed"
        elif line.startswith("rename from "):
            current_old_path = line[len("rename from "):]
            current_status = "renamed"
        elif line.startswith("rename to "):
            current_new_path = line[len("rename to "):]
            current_file = current_new_path
            current_status = "renamed"
        elif not in_hunk and line.startswith("--- "):
            if line == "--- /dev/null":
                current_old_path = None
            else:
                current_old_path = line[4:].strip()
                if current_old_path.startswith("a/"):
                    current_old_path = current_old_path[2:]
        elif not in_hunk and line.startswith("+++ "):
            if line == "+++ /dev/null":
                current_new_path = None
                current_file = current_old_path
            else:
                current_new_path = line[4:].strip()
                if current_new_path.startswith("b/"):
                    current_new_path = current_new_path[2:]
                current_file = current_new_path
        elif line.startswith("@@"):
            in_hunk = True
            patch_missing = False
            # Parse hunk header: @@ -start,count +start,count @@
            m = re.search(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if m:
                line_num_old = int(m.group(1)) - 1
                line_num_new = int(m.group(2)) - 1
            current_content.append(line)
        elif in_hunk and current_file:
            if line.startswith("-"):
                line_num_old += 1
                current_content.append(f"[O{line_num_old}]{line[1:]}")
            elif line.startswith("+"):
                line_num_new += 1
                current_content.append(f"[N{line_num_new}]{line[1:]}")
            elif line.startswith(" "):
                line_num_old += 1
                line_num_new += 1
                current_content.append(f"[C{line_num_new}]{line[1:]}")
            else:
                current_content.append(line)
        elif not in_hunk and current_file:
            # Lines before first hunk (e.g., binary file indicator)
            if line.startswith("Binary files ") or line == "GIT binary patch":
                patch_missing = True
            current_content.append(line)

    # Save last file
    if current_file:
        records.append({
            "file_path": current_file,
            "old_path": current_old_path or current_file,
            "new_path": current_new_path,
            "status": current_status,
            "patch_missing": patch_missing,
            "content": current_content,
        })

    return records


def context_mode(args):
    """Create local git review context."""
    git_root = find_git_root()
    session_dir = create_session(git_root)
    config = load_config()

    repository_manifest = None
    if args.whole_repo:
        diffs_records, repository_manifest = whole_repo_snapshot(git_root, config)
        changed_files = [record["file_path"] for record in diffs_records]
        diff_hash = hashlib.sha256(_canonical_bytes(diffs_records)).hexdigest()
        partial_reasons = []
    else:
        diff_text = get_diff(git_root, args)
        changed_files = get_changed_files(git_root, args)
        diffs_records = format_diff_with_anchors(diff_text)
        present = {record["file_path"] for record in diffs_records}
        diffs_records.extend({"file_path": path, "old_path": path, "new_path": path, "status": "modified", "patch_missing": True, "content": []} for path in changed_files if path not in present)
        diff_hash = hashlib.sha256(diff_text.encode("utf-8", errors="surrogateescape")).hexdigest()
        partial_reasons = sorted(f"missing_patch:{record['file_path']}" for record in diffs_records if record.get("patch_missing"))
    base_sha, head_sha, merge_base_sha = snapshot_revisions(git_root, args)

    # Write diffs.json
    diffs_file = session_dir / "context" / "diffs.json"
    with open(diffs_file, "w", encoding="utf-8") as f:
        json.dump(diffs_records, f, ensure_ascii=False, indent=2)

    repository_manifest_file = None
    if repository_manifest is not None:
        repository_manifest["head_sha"] = head_sha
        repository_manifest_file = session_dir / "context" / "repository-files.json"
        repository_manifest_file.write_text(
            json.dumps(repository_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    # Determine review mode and baseline
    if args.whole_repo:
        review_mode = "whole_repo"
        baseline = "tracked-working-tree"
    elif args.base_branch:
        review_mode = "branch"
        baseline = f"origin/{args.base_branch}"
    elif args.base_commit:
        review_mode = "commit"
        baseline = args.base_commit
    elif args.range:
        review_mode = "range"
        baseline = args.range
    else:
        review_mode = "staged"
        baseline = "HEAD"

    report_name = "whole_repo_review" if args.whole_repo else "review_comments"
    report_path = Path(git_root) / ".code-review" / f"{report_name}_{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"

    snapshot = {
        "base_sha": base_sha,
        "head_sha": head_sha,
        "merge_base_sha": merge_base_sha,
        "diff_sha256": diff_hash,
        "captured_at": datetime.now().astimezone().isoformat(),
    }
    if repository_manifest is not None:
        snapshot["repository_sha256"] = repository_manifest["repository_sha256"]

    context = {
        "schema_version": "1.0",
        "platform": "local",
        "changed_files": changed_files,
        "diff_file": str(diffs_file),
        "snapshot": snapshot,
        "integrity": {"status": "partial" if partial_reasons else "complete", "reasons": partial_reasons, "publish_allowed": False},
        "metadata": {
            "mode": "local",
            "review_mode": review_mode,
            "baseline": baseline,
            "local_report_path": str(report_path),
            "review_workspace": {
                "available": True,
                "path": git_root,
            },
            "session_dir": str(session_dir),
        },
    }
    if repository_manifest_file is not None:
        context["repository_manifest_file"] = str(repository_manifest_file)
        context["metadata"]["whole_repo"] = {
            "included_file_count": len(repository_manifest["included_files"]),
            "excluded_file_count": len(repository_manifest["excluded_files"]),
            "repository_manifest_file": str(repository_manifest_file),
        }

    context_file = session_dir / "context" / "context.json"
    with open(context_file, "w", encoding="utf-8") as f:
        json.dump(context, f, ensure_ascii=False, indent=2)

    result = {
        "type": "LOCAL_CONTEXT",
        "status": "PARTIAL" if partial_reasons else "SUCCESS",
        "context_file": str(context_file),
        "review_session": {
            "path": str(session_dir),
            "cleanup_path": str(session_dir),
            "review_store": str(session_dir / "submission" / "review_store.json"),
        },
        "review_workspace": context["metadata"]["review_workspace"],
        "changed_files": changed_files,
        "integrity": context["integrity"],
    }
    if repository_manifest is not None:
        result["whole_repo"] = context["metadata"]["whole_repo"]
    print(json.dumps(result, ensure_ascii=False, indent=2))


def validate_record(record: dict) -> tuple:
    """Validate a review record has required fields.

    Returns (is_valid, error_msg).
    """
    required = ["file_path", "line", "severity", "comment", "fix_suggestion"]
    for field in required:
        if field not in record:
            return False, f"Missing required field: {field}"

    if record.get("severity") not in ["fatal", "major", "minor", "suggestion"]:
        return False, f"Invalid severity: {record.get('severity')}"

    try:
        line = int(record.get("line", 0))
        if line < 1:
            return False, f"Invalid line number: {line}"
    except (ValueError, TypeError):
        return False, f"Line must be an integer: {record.get('line')}"

    return True, ""


def severity_to_risk(severity: str) -> str:
    """Convert severity to risk level for report."""
    mapping = {
        "fatal": "CRITICAL",
        "major": "HIGH",
        "minor": "MEDIUM",
        "suggestion": "LOW",
    }
    return mapping.get(severity, "LOW")


def render_report_mode(args):
    """Render Markdown report from review store."""
    config = load_config()

    # Load context
    if not args.context:
        print(json.dumps({
            "type": "ERROR",
            "error_type": "MISSING_CONTEXT",
            "message": "--context required for render-report mode",
        }))
        sys.exit(1)

    if not args.review_store:
        print(json.dumps({
            "type": "ERROR",
            "error_type": "MISSING_REVIEW_STORE",
            "message": "--review-store required for render-report mode",
        }))
        sys.exit(1)

    with open(args.context, "r", encoding="utf-8") as f:
        context = json.load(f)

    with open(args.review_store, "r", encoding="utf-8") as f:
        records = json.load(f)

    enabled_severities = config.get("enabled_severities", ["fatal", "major", "minor", "suggestion"])
    metadata = context.get("metadata", {})

    # Validate and filter records
    valid_records = []
    invalid_count = 0
    skipped_count = 0

    for record in records:
        is_valid, error = validate_record(record)
        if not is_valid:
            invalid_count += 1
            continue

        if record.get("severity") not in enabled_severities:
            skipped_count += 1
            continue

        valid_records.append(record)

    # Sort by severity then by file_path
    severity_order = {"fatal": 0, "major": 1, "minor": 2, "suggestion": 3}
    valid_records.sort(key=lambda r: (severity_order.get(r.get("severity"), 9), r.get("file_path", ""), r.get("line", 0)))

    # Count by severity
    counts = {"fatal": 0, "major": 0, "minor": 0, "suggestion": 0}
    for record in valid_records:
        sev = record.get("severity")
        if sev in counts:
            counts[sev] += 1

    # Generate report
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report_lines = [
        "# 本地代码检视报告",
        "",
        "## 基本信息",
        "| 项目 | 内容 |",
        "|------|---------|",
        f"| 检视时间 | {now} |",
        f"| 变更模式 | {metadata.get('review_mode', 'unknown')} |",
        f"| 基准 | {metadata.get('baseline', 'unknown')} |",
        f"| 工作区 | {metadata.get('review_workspace', {}).get('path', 'unknown')} |",
        "",
        "## 完整性校验",
        "| 校验项 | 结果 |",
        "|--------|------|",
        f"| 变更文件覆盖率 | {len(context.get('changed_files', []))} 个文件 |",
        f"| 检视意见数 | {len(valid_records)} 个 |",
        f"| 无效记录数 | {invalid_count} 个 |",
        "",
        "## 检视结果汇总",
        f"- 🔴 **严重 (fatal)**: {counts['fatal']} 个",
        f"- 🟠 **主要 (major)**: {counts['major']} 个",
        f"- 🟡 **次要 (minor)**: {counts['minor']} 个",
        f"- 🟢 **建议 (suggestion)**: {counts['suggestion']} 个",
        "",
        "## 检视意见详情",
        "",
        "| # | 问题描述 | 文件:行号 | 风险等级 |",
        "|---|---------|-----------|---------|",
    ]
    if metadata.get("review_mode") == "whole_repo":
        whole_repo = metadata.get("whole_repo", {})
        report_lines[8:8] = [
            f"| 纳入文件 | {whole_repo.get('included_file_count', 0)} 个 |",
            f"| 排除文件 | {whole_repo.get('excluded_file_count', 0)} 个 |",
        ]

    for i, record in enumerate(valid_records, 1):
        file_path = record.get("file_path", "")
        line = record.get("line", "")
        severity = record.get("severity", "")
        risk = severity_to_risk(severity)
        comment_text = record.get("comment", "")
        comment = comment_text[:60] + ("..." if len(comment_text) > 60 else "")
        report_lines.append(f"| {i} | {comment} | {file_path}:{line} | {risk} |")

    if not valid_records:
        report_lines.append("| - | 无检视意见 | - | - |")

    report_lines.extend([
        "",
        "## 详细问题列表",
    ])

    for i, record in enumerate(valid_records, 1):
        file_path = record.get("file_path", "")
        line = record.get("line", "")
        severity = record.get("severity", "")
        risk = severity_to_risk(severity)
        comment = record.get("comment", "")
        fix_suggestion = record.get("fix_suggestion", "")
        rules = record.get("rules", "")

        severity_icon = {"fatal": "🔴", "major": "🟠", "minor": "🟡", "suggestion": "🟢"}.get(severity, "")

        report_lines.extend([
            f"### {i}. {severity_icon} {severity_to_risk(severity)}",
            "",
            f"**文件位置**: {file_path}:{line}",
            "",
            f"**问题描述**：",
            comment,
            "",
            f"**修复建议**：",
            fix_suggestion if fix_suggestion else "无",
            "",
        ])

        if rules:
            report_lines.extend([
                f"**适用规则**：",
                rules,
                "",
            ])

        report_lines.append("---")
        report_lines.append("")

    # Write report
    report_path = metadata.get("local_report_path", "")
    if not report_path:
        report_path = str(Path(args.context).parent.parent / "submission" / "review_report.md")

    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    report_content = "\n".join(report_lines)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(json.dumps({
        "type": "LOCAL_REPORT",
        "status": "SUCCESS",
        "report_path": report_path,
        "issue_count": len(valid_records),
        "counts": counts,
        "skipped_count": skipped_count,
        "invalid_count": invalid_count,
        "enabled_severities": enabled_severities,
        "bytes": len(report_content.encode("utf-8")),
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Local Git code review context")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--base-branch", help="Base branch for diff")
    group.add_argument("--base-commit", help="Base commit SHA for diff")
    group.add_argument("--range", help="Commit range (base..head)")
    group.add_argument("--whole-repo", action="store_true", help="Review all Git-tracked text files (local report only)")
    parser.add_argument("--render-report", action="store_true", help="Render Markdown report")
    parser.add_argument("--context", help="context.json path (for render-report)")
    parser.add_argument("--review-store", help="review_store.json path (for render-report)")
    args = parser.parse_args()

    if args.render_report:
        render_report_mode(args)
    else:
        context_mode(args)


if __name__ == "__main__":
    main()
