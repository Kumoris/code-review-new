#!/usr/bin/env python3
"""Assertion: check that specific rule file is loaded in the manifest."""

import json
from pathlib import Path


def check(session_dir: Path, expected_rule: str = "", **kwargs) -> dict:
    manifest_file = session_dir / "context" / "review_manifest.json"
    if not manifest_file.exists():
        return {"passed": False, "evidence": "review_manifest.json not found"}

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Check local_rule_paths and task-level local_rule_paths
    all_rules = set(manifest.get("local_rule_paths", []))
    for task in manifest.get("review_tasks", []):
        all_rules.update(task.get("local_rule_paths", []))

    matching = [r for r in all_rules if expected_rule in r]
    if matching:
        return {"passed": True, "evidence": f"Rule '{expected_rule}' found in: {matching}"}
    return {"passed": False, "evidence": f"Rule '{expected_rule}' not found. Loaded rules: {sorted(all_rules)}"}
