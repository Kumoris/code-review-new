#!/usr/bin/env python3
"""Assertion: check that no findings have empty fix_suggestion."""

import json
from pathlib import Path


def check(session_dir: Path, **kwargs) -> dict:
    store_file = session_dir / "submission" / "review_store.json"
    if not store_file.exists():
        return {"passed": True, "evidence": "No review_store.json, skip check"}

    with open(store_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    violations = []
    for r in records:
        fix = r.get("fix_suggestion", "").strip()
        if not fix or fix in ("无", "暂无", "N/A", "none"):
            violations.append(r.get("id", "?"))

    if violations:
        return {"passed": False, "evidence": f"{len(violations)} records with empty fix_suggestion: {violations}"}
    return {"passed": True, "evidence": f"All {len(records)} records have non-empty fix_suggestion"}
