#!/usr/bin/env python3
"""Assertion: check that Spark pipeline config findings reference SPARK-PIPE rules."""

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

    # Look for findings referencing SPARK-PIPE or retention/granularity issues
    matched = []
    for r in records:
        comment = r.get("comment", "")
        rules = r.get("rules", "")
        combined = f"{comment} {rules}".lower()

        # SPARK-PIPE rule IDs
        if any(pid in combined for pid in ["spark-pipe-001", "spark-pipe-002", "spark-pipe-003", "spark-pipe-004"]):
            matched.append(r.get("id", "?"))
            continue

        # Retention/granularity in dataset context
        has_retention = "retention" in combined
        has_granularity = "granularity" in combined
        has_dataset = "dataset" in combined or ".yaml" in combined
        if (has_retention or has_granularity) and has_dataset:
            matched.append(r.get("id", "?"))

    if matched:
        return {"passed": True, "evidence": f"{len(matched)} findings reference Spark pipeline rules: {matched}"}
    return {"passed": False, "evidence": f"No Spark pipeline findings among {len(records)} records"}
