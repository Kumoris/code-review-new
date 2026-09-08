#!/usr/bin/env python3
"""Assertion: check that findings detected enum/constant extensibility issues.

Verifies that when new enum values or int constants are added to an existing
constant group, the review detected that not all if/switch/ternary conditions
were updated to handle the new values (COM-ARCH-007).
"""

import json
import re
from pathlib import Path


def check(session_dir: Path, **kwargs) -> dict:
    store_file = session_dir / "submission" / "review_store.json"
    if not store_file.exists():
        return {"passed": False, "evidence": "review_store.json not found"}

    with open(store_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    if not records:
        return {"passed": False, "evidence": "No records in review_store.json"}

    # Keywords for enum extensibility detection
    extensibility_keywords = [
        "COM-ARCH-007", "枚举扩展", "常量扩展", "新增枚举", "新增常量",
        "条件判断未更新", "switch未更新", "if未更新", "分支未覆盖",
        "新增值未处理", "扩展性", "exhaustive", "穷举",
        "魔法数字", "magic number", "int常量", "枚举类型",
        "POLICY_UPDATE", "策略操作类型",
    ]

    matched = []
    for r in records:
        comment = r.get("comment", "")
        rules = str(r.get("rules", ""))
        fix = r.get("fix_suggestion", "")
        issue = r.get("issue_summary", "")
        combined = f"{comment} {rules} {fix} {issue}"

        # Check for COM-ARCH-007 rule reference directly
        if "COM-ARCH-007" in combined:
            matched.append(r.get("id", "?"))
            continue

        # Check for extensibility keyword patterns in meaningful context
        has_extensibility = any(kw in combined for kw in extensibility_keywords)
        if has_extensibility:
            # Must mention both: new values added AND conditions not updated
            has_new_value = any(kw in combined for kw in [
                "新增枚举", "新增常量", "新增值", "POLICY_UPDATE",
                "新增", "扩展", "新增策略",
            ])
            has_uncovered = any(kw in combined for kw in [
                "条件判断未更新", "switch未更新", "if未更新", "分支未覆盖",
                "新增值未处理", "未覆盖", "未同步更新", "魔法数字",
                "未处理", "穷举", "编译期",
            ])
            if has_new_value and has_uncovered:
                matched.append(r.get("id", "?"))

    if matched:
        return {"passed": True, "evidence": f"{len(matched)} findings detected enum extensibility issues: {matched}"}
    return {"passed": False, "evidence": f"No findings about enum/constant extensibility among {len(records)} records"}
