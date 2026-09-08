#!/usr/bin/env python3
"""Assertion: check all findings have non-empty rule IDs."""

import json
from pathlib import Path


def check(session_dir: Path, **kwargs) -> dict:
    # Check both reviewer outputs and review_store
    files_to_check = []

    # Reviewer outputs
    manifest_file = session_dir / "context" / "review_manifest.json"
    if manifest_file.exists():
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        for task in manifest.get("review_tasks", []):
            output_path = task.get("output_path", "")
            if output_path and Path(output_path).exists():
                files_to_check.append(("reviewer", Path(output_path)))

    # Review store
    store_file = session_dir / "submission" / "review_store.json"
    if store_file.exists():
        files_to_check.append(("store", store_file))

    if not files_to_check:
        return {"passed": True, "evidence": "No findings to check (no reviewer outputs or store)"}

    violations = []
    checked = 0
    for source, fpath in files_to_check:
        with open(fpath, "r", encoding="utf-8") as f:
            findings = json.load(f)
        if isinstance(findings, dict):
            findings = findings.get("findings", [])
        if not isinstance(findings, list):
            continue
        for finding in findings:
            checked += 1
            # Check "rules" field (reviewer output format)
            rules = finding.get("rules", "")
            # Check "comment" field for rule reference (review_store format)
            comment = finding.get("comment", "")

            has_rule = False
            if rules and rules.strip():
                has_rule = True
            elif comment and ("**违反规则**" in comment or "references/" in comment or "深度检视：" in comment or "deep_review" in str(finding.get("deep_review")) or finding.get("category") == "deep_review"):
                has_rule = True

            if not has_rule:
                fid = finding.get("id", finding.get("issue_summary", "?"))
                violations.append(f"[{source}] {fid}: no rule reference found")

    if violations:
        return {"passed": False, "evidence": f"{len(violations)}/{checked} findings missing rule IDs: {violations[:5]}"}
    return {"passed": True, "evidence": f"All {checked} findings have rule IDs"}
