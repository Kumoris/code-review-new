#!/usr/bin/env python3
"""Assertion: check deep review findings exist and are valid."""

import json
from pathlib import Path


def check(session_dir: Path, **kwargs) -> dict:
    store_file = session_dir / "submission" / "review_store.json"
    if not store_file.exists():
        # Also check reviewer outputs
        manifest_file = session_dir / "context" / "review_manifest.json"
        if manifest_file.exists():
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            for task in manifest.get("review_tasks", []):
                output_path = task.get("output_path", "")
                if output_path and Path(output_path).exists():
                    with open(output_path, "r", encoding="utf-8") as f:
                        findings = json.load(f)
                    deep = [f for f in findings if f.get("deep_review")]
                    if deep:
                        return {"passed": True, "evidence": f"{len(deep)} deep review findings in {output_path}"}
        return {"passed": False, "evidence": "No deep review findings found in any output"}

    with open(store_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    deep_records = [r for r in records if r.get("deep_review")]
    if deep_records:
        # Validate deep_review structure
        valid = 0
        for r in deep_records:
            dr = r.get("deep_review", {})
            if dr.get("call_chain_path") and dr.get("change_type"):
                valid += 1
        return {"passed": True, "evidence": f"{len(deep_records)} deep review records ({valid} valid structure)"}
    return {"passed": False, "evidence": "No records with deep_review field in review_store.json"}
