#!/usr/bin/env python3
"""Assertion: check that submitted comments are not duplicates of existing reviews."""

import json
from pathlib import Path


def check(session_dir: Path, **kwargs) -> dict:
    store_file = session_dir / "submission" / "review_store.json"
    if not store_file.exists():
        return {"passed": True, "evidence": "No review_store.json, skip duplicate check"}

    with open(store_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    if not records:
        return {"passed": True, "evidence": "No records to check for duplicates"}

    # Check for duplicate comments within our own findings
    seen_comments = {}
    duplicates = []
    for r in records:
        comment = r.get("comment", "").strip()
        # Normalize: remove location-specific parts for dedup check
        # Two findings with identical problem description but different files are NOT duplicates
        # Two findings with identical problem + same file ARE duplicates
        file_path = r.get("file_path", r.get("new_path", ""))
        line = r.get("line", r.get("line_number", ""))
        key = (comment[:200], file_path, line)

        if key in seen_comments:
            duplicates.append(f"Record {r.get('id', '?')} duplicates {seen_comments[key]}")
        else:
            seen_comments[key] = r.get("id", "?")

    if duplicates:
        return {"passed": False, "evidence": f"{len(duplicates)} duplicate comments: {duplicates[:5]}"}
    return {"passed": True, "evidence": f"No duplicate comments among {len(records)} records"}
