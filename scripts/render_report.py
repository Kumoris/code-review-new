#!/usr/bin/env python3
"""Render Markdown report from review store for local mode.

Usage:
    python render_report.py --context <context.json> --review-store <review_store.json>
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


SEVERITY_ORDER = {"fatal": 0, "major": 1, "minor": 2, "suggestion": 3}
SEVERITY_ICONS = {"fatal": "🔴", "major": "🟠", "minor": "🟡", "suggestion": "🟢"}


def render_report(context: dict, records: list, config: dict) -> str:
    """Render Markdown report from review store records."""
    metadata = context.get("metadata", {})
    enabled = config.get("enabled_severities", ["fatal", "major", "minor", "suggestion"])

    # Filter by enabled severities
    filtered = [r for r in records if r.get("severity") in enabled]
    filtered.sort(key=lambda r: SEVERITY_ORDER.get(r.get("severity", "suggestion"), 99))

    lines = []
    lines.append("## 本地代码检视总结\n")

    # Basic info
    lines.append("### 基本信息\n")
    lines.append(f"| 项目 | 内容 |")
    lines.append(f"|------|------|")
    lines.append(f"| 审查模式 | {metadata.get('review_mode', 'local')} |")
    lines.append(f"| 基线 | {metadata.get('baseline', 'N/A')} |")
    lines.append(f"| 生成时间 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |")
    lines.append(f"| 问题数 | {len(filtered)} 个 |")
    if metadata.get("review_mode") == "whole_repo":
        publishable_count, report_only_count = 0, len(filtered)
    else:
        publishable_count = len([r for r in filtered if r.get("publication_status", "publishable") == "publishable"])
        report_only_count = len([r for r in filtered if r.get("publication_status") == "report_only"])
    lines.append(f"| 可发布 / 仅报告 | {publishable_count} / {report_only_count} |")
    if metadata.get("review_mode") == "whole_repo":
        whole_repo = metadata.get("whole_repo", {})
        lines.append(f"| 纳入文件 | {whole_repo.get('included_file_count', 0)} 个 |")
        lines.append(f"| 排除文件 | {whole_repo.get('excluded_file_count', 0)} 个 |")
    lines.append("")

    # Severity counts
    counts = {}
    for sev in enabled:
        counts[sev] = len([r for r in filtered if r.get("severity") == sev])

    lines.append("### 问题统计\n")
    lines.append(f"| 严重级别 | 数量 |")
    lines.append(f"|---------|------|")
    for sev in enabled:
        icon = SEVERITY_ICONS.get(sev, "")
        lines.append(f"| {icon} {sev} | {counts[sev]} |")
    lines.append("")

    # Issue list
    if filtered:
        lines.append("### 问题列表\n")
        for i, record in enumerate(filtered, 1):
            sev = record.get("severity", "suggestion")
            icon = SEVERITY_ICONS.get(sev, "")
            file_path = record.get("file_path", "")
            line_no = record.get("line", 0)
            comment = record.get("comment", "")
            fix = record.get("fix_suggestion", "")
            summary = record.get("issue_summary", "")

            publication = record.get("publication_status", "publishable")
            lines.append(f"#### {i}. {file_path}:{line_no} ({sev}, {publication}) {icon}\n")
            lines.append(f"**摘要**：{summary}\n")
            if comment:
                lines.append(f"{comment}\n")
            if fix:
                lines.append(f"**修改建议**：{fix}\n")
            lines.append("---\n")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Render local review report")
    parser.add_argument("--context", required=True, help="context.json path")
    parser.add_argument("--review-store", required=True, help="review_store.json path")
    args = parser.parse_args()

    # Load config
    config = {}
    config_paths = [
        Path.cwd() / ".code-review-new" / "config.json",
        Path(__file__).parent.parent / "config.json",
    ]
    for p in config_paths:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                config = json.load(f)
            break

    with open(args.context, "r", encoding="utf-8") as f:
        context = json.load(f)

    with open(args.review_store, "r", encoding="utf-8") as f:
        records = json.load(f)

    report = render_report(context, records, config)

    # Write to local_report_path
    report_path = context.get("metadata", {}).get("local_report_path", "")
    if report_path:
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

    counts = {}
    enabled = config.get("enabled_severities", ["fatal", "major", "minor", "suggestion"])
    for sev in enabled:
        counts[sev] = len([r for r in records if r.get("severity") == sev])

    print(json.dumps({
        "type": "LOCAL_REPORT",
        "status": "SUCCESS",
        "report_path": report_path,
        "issue_count": len(records),
        "counts": counts,
        "skipped_count": 0,
        "enabled_severities": enabled,
        "bytes": len(report.encode("utf-8")),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
