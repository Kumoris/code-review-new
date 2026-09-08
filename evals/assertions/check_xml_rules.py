#!/usr/bin/env python3
"""Assertion: check that XML config findings reference XML-SYNTAX or XML-ERRCODE rules."""

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

        # XML-SYNTAX or XML-ERRCODE rule IDs
        if any(pid in combined for pid in ["xml-syntax-001", "xml-syntax-002", "xml-errcode-001", "xml-errcode-002"]):
            matched.append(r.get("id", "?"))
            continue

        # XML structural issues keywords
        has_xml_issue = any(kw in combined for kw in [
            "闭合标签", "重复", "closing tag", "duplicate", "</",
            "解析失败", "parse error", "xml", "paras",
        ])
        if has_xml_issue:
            matched.append(r.get("id", "?"))

    if matched:
        return {"passed": True, "evidence": f"{len(matched)} findings reference XML rules: {matched}"}
    return {"passed": False, "evidence": f"No XML config findings among {len(records)} records"}
