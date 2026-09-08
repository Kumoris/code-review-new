#!/usr/bin/env python3
"""Assertion: check that at least one finding has the specified category."""

import json
from pathlib import Path


def check(session_dir: Path, **kwargs) -> dict:
    expected_category = kwargs.get("expected_category", "")

    store_file = session_dir / "submission" / "review_store.json"
    if not store_file.exists():
        return {"passed": False, "evidence": "review_store.json not found"}

    with open(store_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    if not records:
        return {"passed": False, "evidence": "No records in review_store.json"}

    matched = []
    for r in records:
        cat = r.get("category", "")
        if cat == expected_category:
            matched.append(r.get("id", "?"))
        # Also check in comment text for category keywords
        comment = r.get("comment", "")
        if expected_category == "security" and any(kw in comment.lower() for kw in ["安全", "密码", "password", "secret", "token", "硬编码", "sql注入"]):
            matched.append(r.get("id", "?"))

    if matched:
        return {"passed": True, "evidence": f"{len(matched)} findings with category '{expected_category}'"}
    return {"passed": False, "evidence": f"No findings with category '{expected_category}'. Categories found: {list(set(r.get('category', '') for r in records))}"}
