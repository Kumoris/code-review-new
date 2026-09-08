#!/usr/bin/env python3
"""Assertion: check that at least one finding references a rule ID matching a pattern."""

import json
import re
from pathlib import Path


def check(session_dir: Path, **kwargs) -> dict:
    pattern = kwargs.get("pattern", "")

    store_file = session_dir / "submission" / "review_store.json"
    if not store_file.exists():
        return {"passed": False, "evidence": "review_store.json not found"}

    with open(store_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    if not records:
        return {"passed": False, "evidence": "No records in review_store.json"}

    matched = []
    for r in records:
        # Check rules field
        rules = r.get("rules", "")
        if rules and re.search(pattern, str(rules)):
            matched.append(r.get("id", "?"))
            continue
        # Check comment for pattern
        comment = r.get("comment", "")
        if comment and re.search(pattern, comment):
            matched.append(r.get("id", "?"))
            continue
        # Check deep_review
        deep = r.get("deep_review")
        if deep and re.search(pattern, str(deep)):
            matched.append(r.get("id", "?"))

    if matched:
        return {"passed": True, "evidence": f"{len(matched)} findings matching /{pattern}/: {matched[:5]}"}
    return {"passed": False, "evidence": f"No findings matching /{pattern}/"}
