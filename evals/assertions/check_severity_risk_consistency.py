#!/usr/bin/env python3
"""Assertion: check severity matches risk_level in deep review findings."""

import json
from pathlib import Path

# Mapping: risk_level → severity
RISK_SEVERITY_MAP = {
    "CRITICAL": "fatal",
    "HIGH": "major",
    "MEDIUM": "minor",
    "LOW": "suggestion",
}


def check(session_dir: Path, **kwargs) -> dict:
    store_file = session_dir / "submission" / "review_store.json"
    if not store_file.exists():
        return {"passed": True, "evidence": "No review_store.json, skip check"}

    with open(store_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    mismatches = []
    for r in records:
        dr = r.get("deep_review")
        if not dr:
            continue
        risk = dr.get("business_impact", {}).get("risk_level", "")
        severity = r.get("severity", "")
        expected_severity = RISK_SEVERITY_MAP.get(risk)
        if expected_severity and severity != expected_severity:
            mismatches.append(f"{r.get('id', '?')}: risk={risk}, severity={severity}, expected={expected_severity}")

    if mismatches:
        return {"passed": False, "evidence": f"Mismatches: {mismatches}"}
    return {"passed": True, "evidence": "All deep review severity/risk_level pairs consistent"}
