#!/usr/bin/env python3
"""Assertion: check language coverage in task scope_file_paths."""

import json
from pathlib import Path

EXT_MAP = {
    "java": ".java",
    "python": ".py",
    "go": ".go",
    "javascript": ".js",
    "typescript": ".ts",
    "c": ".c",
    "cpp": ".cpp",
}


def check(session_dir: Path, lang: str = "", **kwargs) -> dict:
    context_file = session_dir / "context" / "context.json"
    manifest_file = session_dir / "context" / "review_manifest.json"

    if not context_file.exists():
        return {"passed": False, "evidence": "context.json not found"}

    with open(context_file, "r", encoding="utf-8") as f:
        context = json.load(f)

    ext = EXT_MAP.get(lang, f".{lang}")
    changed_files = [f for f in context.get("changed_files", []) if f.endswith(ext)]

    if not changed_files:
        return {"passed": True, "evidence": f"No {ext} files in changed_files, skip check"}

    # Check manifest scope
    scoped = set()
    if manifest_file.exists():
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        for task in manifest.get("review_tasks", []):
            scoped.update(task.get("scope_file_paths", []))

    uncovered = [f for f in changed_files if f not in scoped]

    if uncovered:
        return {"passed": False, "evidence": f"{len(uncovered)} {lang} files not in scope: {uncovered[:5]}"}
    return {"passed": True, "evidence": f"All {len(changed_files)} {lang} files covered in scope"}
