#!/usr/bin/env python3
"""Assertion: check that findings detected JSX prop completeness issues.

Verifies that when a component has display props (hasXxxBtn, xxxSrc) but
missing handler props (handleXxxBtn, onXxxClick), at least one finding
was reported about the incomplete prop set.
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

    # Look for findings about prop completeness / accidental deletion
    prop_keywords = [
        "prop", "handle", "onclick", "handler", "遗漏", "缺失", "删除",
        "不完整", "incomplete", "missing", "deleted", "accidental",
        "JSTS-REACT-009", "按钮", "button", "点击", "click", "无响应",
        "handleFirstBtn", "handleSecondBtn", "handleXxxBtn",
    ]

    matched = []
    for r in records:
        comment = r.get("comment", "").lower()
        rules = r.get("rules", "").lower()
        evidence = str(r.get("evidence", "")).lower()
        combined = f"{comment} {rules} {evidence}"

        # Check for JSTS-REACT-009 specifically
        if "jsts-react-009" in combined:
            matched.append(r.get("id", "?"))
            continue

        # Check for prop completeness keywords in a meaningful context
        has_prop_keyword = any(kw.lower() in combined for kw in prop_keywords)
        if has_prop_keyword:
            # Must mention both sides: something exists but something is missing
            has_missing = any(kw in combined for kw in ["遗漏", "缺失", "missing", "deleted", "删除", "不完整", "incomplete", "无响应"])
            has_exists = any(kw in combined for kw in ["has", "btn", "button", "src", "prop", "按钮"])
            if has_missing and has_exists:
                matched.append(r.get("id", "?"))

    if matched:
        return {"passed": True, "evidence": f"{len(matched)} findings detected prop completeness issues: {matched}"}
    return {"passed": False, "evidence": f"No findings about prop completeness/deletion among {len(records)} records"}
