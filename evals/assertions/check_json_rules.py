#!/usr/bin/env python3
"""Assertion: check that JSON config findings reference JSON-FILE rules or detect JSON format issues."""

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

        # JSON-FILE rule IDs
        if any(pid in combined for pid in [
            "json-file-001", "json-file-002", "json-file-003", "json-file-004"
        ]):
            matched.append(r.get("id", "?"))
            continue

        # JSON format issue keywords
        has_json_issue = any(kw in combined for kw in [
            "括号匹配", "bracket", "双引号", "double quote", "单引号", "single quote",
            "末尾逗号", "trailing comma", "值类型", "value type",
            "json", "解析失败", "parse error",
        ])
        if has_json_issue:
            matched.append(r.get("id", "?"))

    if matched:
        return {"passed": True, "evidence": f"{len(matched)} findings reference JSON rules: {matched}"}
    return {"passed": False, "evidence": f"No JSON config findings among {len(records)} records"}
