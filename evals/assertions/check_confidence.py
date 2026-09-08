#!/usr/bin/env python3
"""Assertion: check confidence scores above threshold."""

import json
from pathlib import Path


def check(session_dir: Path, min_score: int = 7, **kwargs) -> dict:
    store_file = session_dir / "submission" / "review_store.json"
    if not store_file.exists():
        return {"passed": True, "evidence": "No review_store.json, skip check"}

    with open(store_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    violations = [r for r in records if r.get("confidence_score", 0) < min_score]

    if violations:
        ids = [r.get("id", "?") for r in violations]
        return {"passed": False, "evidence": f"{len(violations)} records below threshold {min_score}: {ids}"}
    return {"passed": True, "evidence": f"All {len(records)} records have confidence >= {min_score}"}
