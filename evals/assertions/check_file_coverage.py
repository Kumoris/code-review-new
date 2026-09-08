#!/usr/bin/env python3
"""Assertion: check all changed files are covered by at least one task's scope_file_paths."""

import json
from pathlib import Path


def check(session_dir: Path, **kwargs) -> dict:
    context_file = session_dir / "context" / "context.json"
    manifest_file = session_dir / "context" / "review_manifest.json"

    if not context_file.exists():
        return {"passed": False, "evidence": "context.json not found"}

    with open(context_file, "r", encoding="utf-8") as f:
        context = json.load(f)

    changed_files = set(context.get("changed_files", []))

    # Collect routed and explicitly unsupported files from manifest.
    scoped_files = set()
    unsupported_files = set()
    if manifest_file.exists():
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        for task in manifest.get("review_tasks", []):
            scoped_files.update(task.get("scope_file_paths", []))
        coverage = manifest.get("coverage", {})
        unsupported_files.update(coverage.get("unsupported_files", manifest.get("unsupported_files", [])))

    overlap = scoped_files & unsupported_files
    uncovered = changed_files - scoped_files - unsupported_files
    extra = (scoped_files | unsupported_files) - changed_files

    if not uncovered and not overlap and not extra:
        return {"passed": True, "evidence": f"All {len(changed_files)} files routed or unsupported"}
    else:
        return {"passed": False, "evidence": f"uncovered={sorted(uncovered)}, overlap={sorted(overlap)}, extra={sorted(extra)}"}
