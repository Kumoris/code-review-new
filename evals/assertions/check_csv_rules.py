#!/usr/bin/env python3
"""Assertion: check that CSV config findings reference CSV-FILE rules or detect CSV format issues."""

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

        # CSV-FILE rule IDs
        if any(pid in combined for pid in [
            "csv-file-001", "csv-file-002", "csv-file-003"
        ]):
            matched.append(r.get("id", "?"))
            continue

        # CSV format issue keywords
        has_csv_issue = any(kw in combined for kw in [
            "列数", "column count", "列不一致", "引号成对", "quote",
            "换行符", "line ending", "crlf", "csv", "分隔符", "delimiter",
        ])
        if has_csv_issue:
            matched.append(r.get("id", "?"))

    if matched:
        return {"passed": True, "evidence": f"{len(matched)} findings reference CSV rules: {matched}"}
    return {"passed": False, "evidence": f"No CSV config findings among {len(records)} records"}
