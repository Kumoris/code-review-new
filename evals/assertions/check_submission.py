#!/usr/bin/env python3
"""Assertion: check that at least one review record was submitted remotely."""

import json
from pathlib import Path


def check(session_dir: Path, **kwargs) -> dict:
    # Check review_store.json for submitted records (status != "pending")
    store_file = session_dir / "submission" / "review_store.json"
    if not store_file.exists():
        return {"passed": False, "evidence": "review_store.json not found"}

    with open(store_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    submitted = [r for r in records if r.get("status") != "pending"]
    if submitted:
        return {"passed": True, "evidence": f"{len(submitted)} records submitted"}

    # If all are pending, submission might not have run yet
    if records:
        return {"passed": False, "evidence": f"{len(records)} records exist but all still pending"}

    return {"passed": False, "evidence": "No records in review_store.json"}
