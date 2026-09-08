#!/usr/bin/env python3
"""Assertion: check that HTML config findings reference HTML-FILE rules or detect HTML format issues."""

import json
from pathlib import Path


def check(session_dir: Path, **kwargs) -> dict:
    store_file = session_dir / "submission" / "review_store.json"
    if not store_file.exists():
        return {"passed": False, "evidence": "review_store.json not found"}

    with open(store_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    if not records:
        return {"passed": False, "evidence": "No records in review_store.json"}

    matched = []
    for r in records:
        comment = r.get("comment", "")
        rules = r.get("rules", "")
        combined = f"{comment} {rules}".lower()

        # HTML-FILE rule IDs
        if any(pid in combined for pid in [
            "html-file-001", "html-file-002", "html-file-003"
        ]):
            matched.append(r.get("id", "?"))
            continue

        # HTML format issue keywords
        has_html_issue = any(kw in combined for kw in [
            "标签闭合", "tag closure", "闭合标签", "closing tag",
            "嵌套", "nesting", "块级", "block", "内联", "inline",
            "属性值引号", "attribute quote", "html",
        ])
        if has_html_issue:
            matched.append(r.get("id", "?"))

    if matched:
        return {"passed": True, "evidence": f"{len(matched)} findings reference HTML rules: {matched}"}
    return {"passed": False, "evidence": f"No HTML config findings among {len(records)} records"}
