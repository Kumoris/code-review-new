#!/usr/bin/env python3
"""Assertion: check that call_chains.json contains METHOD_MODIFY or INTERFACE_CHANGE."""

import json
from pathlib import Path


def check(session_dir: Path, **kwargs) -> dict:
    chains_file = session_dir / "context" / "call_chains.json"
    if not chains_file.exists():
        return {"passed": False, "evidence": "call_chains.json not found"}

    with open(chains_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        return {"passed": False, "evidence": "call_chains.json is empty"}

    target_types = {"METHOD_MODIFY", "METHOD_REMOVE", "INTERFACE_CHANGE", "METHOD_ADD"}

    # Handle both list and dict formats
    entries = data if isinstance(data, list) else data.get("chains", data.get("changes", []))
    if isinstance(entries, dict):
        entries = [entries]

    found_types = set()
    for entry in entries:
        change_type = entry.get("change_type", entry.get("type", ""))
        if change_type in target_types:
            found_types.add(change_type)

    if found_types:
        return {"passed": True, "evidence": f"Change types found: {found_types}"}
    return {"passed": False, "evidence": f"No METHOD_MODIFY/INTERFACE_CHANGE found. Types: {set(e.get('change_type', e.get('type', '')) for e in entries)}"}
