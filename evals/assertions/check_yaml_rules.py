#!/usr/bin/env python3
"""Assertion: check that YAML config findings reference YAML-FILE rules or detect YAML format issues."""

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

        # YAML-FILE rule IDs
        if any(pid in combined for pid in [
            "yaml-file-001", "yaml-file-002", "yaml-file-003", "yaml-file-004"
        ]):
            matched.append(r.get("id", "?"))
            continue

        # YAML format issue keywords
        has_yaml_issue = any(kw in combined for kw in [
            "缩进", "indent", "键值对", "key-value", "冒号", "colon",
            "列表", "list", "短横线", "dash", "引号", "quote",
            "yaml", "多行字符串", "multiline",
        ])
        if has_yaml_issue:
            matched.append(r.get("id", "?"))

    if matched:
        return {"passed": True, "evidence": f"{len(matched)} findings reference YAML rules: {matched}"}
    return {"passed": False, "evidence": f"No YAML config findings among {len(records)} records"}
