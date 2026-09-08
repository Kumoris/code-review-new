#!/usr/bin/env python3
"""Assertion: check that findings detected call chain impact issues.

Verifies that when new enum values or constants are passed to other methods,
the review detected that the called method may not correctly handle the new
values (COM-ARCH-008).
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

    # Keywords for call chain impact detection
    call_chain_keywords = [
        "COM-ARCH-008", "调用链影响", "调用链", "下游", "被调用方法",
        "传递后", "参数传递", "调用处", "校验被绕过", "逻辑走错",
        "功能缺失", "checkParam", "checkWholeNetworkPolicy",
        "downstream", "callee", "caller",
        "调用方", "三元表达式", "分支", "未覆盖", "绕过",
    ]

    matched = []
    for r in records:
        comment = r.get("comment", "")
        rules = str(r.get("rules", ""))
        fix = r.get("fix_suggestion", "")
        issue = r.get("issue_summary", "")
        combined = f"{comment} {rules} {fix} {issue}"

        # Check for COM-ARCH-008 rule reference directly
        if "COM-ARCH-008" in combined:
            matched.append(r.get("id", "?"))
            continue

        # Check for call chain impact keyword patterns
        has_call_chain = any(kw in combined for kw in call_chain_keywords)
        if has_call_chain:
            # Must mention both: values passed to method AND method doesn't handle correctly
            has_passed_to = any(kw in combined for kw in [
                "传递", "调用", "参数", "checkParam", "checkWholeNetworkPolicy",
                "下游", "被调用", "callee", "调用方", "三元表达式",
            ])
            has_not_handled = any(kw in combined for kw in [
                "绕过", "未处理", "缺失", "逻辑走错", "校验被绕过",
                "不正确", "不匹配", "无法被编译器检测", "未覆盖",
                "分支", "新增值未处理",
            ])
            if has_passed_to and has_not_handled:
                matched.append(r.get("id", "?"))

    if matched:
        return {"passed": True, "evidence": f"{len(matched)} findings detected call chain impact issues: {matched}"}
    return {"passed": False, "evidence": f"No findings about call chain impact among {len(records)} records"}
