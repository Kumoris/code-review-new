#!/usr/bin/env python3
"""Assertion: check that at least one finding has specified severity level(s)."""

import json
from pathlib import Path


def check(session_dir: Path, **kwargs) -> dict:
    expected = kwargs.get("expected_severities", [])
    if isinstance(expected, str):
        expected = [expected]

    store_file = session_dir / "submission" / "review_store.json"
    if not store_file.exists():
        return {"passed": False, "evidence": "review_store.json not found"}

    with open(store_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    if not records:
        return {"passed": False, "evidence": "No records in review_store.json"}

    # Map Chinese severity to English
    severity_map = {
        "致命": "fatal", "严重": "major", "一般": "minor", "建议": "suggestion",
        "fatal": "fatal", "major": "major", "minor": "minor", "suggestion": "suggestion",
    }

    matched = []
    for r in records:
        sev = r.get("severity", r.get("severity_level", ""))
        sev_en = severity_map.get(sev, sev.lower() if isinstance(sev, str) else "")
        if sev_en in expected:
            matched.append(r.get("id", f"sev={sev}"))

    if matched:
        return {"passed": True, "evidence": f"{len(matched)} findings with severity in {expected}: {matched[:5]}"}
    return {"passed": False, "evidence": f"No findings with severity in {expected}. Found: {[r.get('severity', '?') for r in records[:10]]}"}
