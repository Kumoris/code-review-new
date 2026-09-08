#!/usr/bin/env python3
"""Assertion: check that all finding lines are within [N] anchor ranges in the diff."""

import json
import re
from pathlib import Path


def check(session_dir: Path, **kwargs) -> dict:
    # Load diffs to get [N] anchor ranges per file
    diffs_file = session_dir / "context" / "diffs.json"
    store_file = session_dir / "submission" / "review_store.json"

    if not diffs_file.exists():
        return {"passed": False, "evidence": "diffs.json not found"}
    if not store_file.exists():
        return {"passed": True, "evidence": "No review_store.json, skip line scope check"}

    with open(diffs_file, "r", encoding="utf-8") as f:
        diffs = json.load(f)

    with open(store_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    if not records:
        return {"passed": True, "evidence": "No records to check"}

    # Build file -> set of valid [N] line numbers
    valid_lines = {}
    for diff_entry in diffs:
        file_path = diff_entry.get("new_path", diff_entry.get("file_path", ""))
        n_lines = set()
        for line in diff_entry.get("content", []):
            m = re.match(r"\[N(\d+)\]", line)
            if m:
                n_lines.add(int(m.group(1)))
        if n_lines:
            valid_lines[file_path] = n_lines

    violations = []
    for r in records:
        file_path = r.get("file_path", r.get("new_path", ""))
        line = r.get("line", r.get("line_number", 0))
        if not line or not file_path:
            continue
        try:
            line_num = int(line)
        except (ValueError, TypeError):
            continue

        if file_path in valid_lines:
            # Line must be within or near an [N] anchor
            # Allow some tolerance (±2 lines)
            near_anchor = any(abs(line_num - n) <= 2 for n in valid_lines[file_path])
            if not near_anchor:
                violations.append(f"Record {r.get('id', '?')}: line {line_num} in {file_path} not near any [N] anchor")

    if violations:
        return {"passed": False, "evidence": f"{len(violations)} findings with out-of-scope lines: {violations[:5]}"}
    return {"passed": True, "evidence": f"All findings reference lines within [N] anchor ranges"}
