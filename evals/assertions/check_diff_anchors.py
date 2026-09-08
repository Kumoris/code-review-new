#!/usr/bin/env python3
"""Assertion: check that diffs.json contains [N]/[C]/[O] anchors."""

import json
import re
from pathlib import Path


def check(session_dir: Path, **kwargs) -> dict:
    diffs_file = session_dir / "context" / "diffs.json"
    if not diffs_file.exists():
        return {"passed": False, "evidence": "diffs.json not found"}

    with open(diffs_file, "r", encoding="utf-8") as f:
        diffs = json.load(f)

    n_count = 0
    c_count = 0
    o_count = 0

    for diff_entry in diffs:
        for line in diff_entry.get("content", []):
            if re.match(r"\[N\d+\]", line):
                n_count += 1
            elif re.match(r"\[C\d+\]", line):
                c_count += 1
            elif re.match(r"\[O\d+\]", line):
                o_count += 1

    if n_count > 0:
        return {"passed": True, "evidence": f"Anchors found: [N]={n_count}, [C]={c_count}, [O]={o_count}"}
    return {"passed": False, "evidence": "No [N] anchors found in diffs.json"}
