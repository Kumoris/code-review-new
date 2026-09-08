#!/usr/bin/env python3
"""Assertion: check that no magic number complaints exist for structured config files (STRUCT-FILE-001)."""

import json
from pathlib import Path


def check(session_dir: Path, **kwargs) -> dict:
    store_file = session_dir / "submission" / "review_store.json"
    if not store_file.exists():
        return {"passed": False, "evidence": "review_store.json not found"}

    with open(store_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    if not records:
        return {"passed": True, "evidence": "No records (vacuously no magic number complaints)"}

    violations = []
    magic_keywords = [
        "魔术数字", "magic number", "定义为常量", "define as constant",
        "提取常量", "extract constant", "硬编码数值", "hardcoded value",
    ]

    for r in records:
        comment = r.get("comment", "").lower()
        file_path = r.get("file_path", r.get("path", "")).lower()

        # Only check config file types
        is_config = any(file_path.endswith(ext) for ext in [
            ".yaml", ".yml", ".json", ".csv", ".xml", ".properties"
        ])

        if is_config and any(kw in comment for kw in magic_keywords):
            violations.append({
                "id": r.get("id", "?"),
                "file": r.get("file_path", r.get("path", "")),
                "snippet": comment[:100],
            })

    if violations:
        return {
            "passed": False,
            "evidence": f"{len(violations)} magic number complaints in config files (violates STRUCT-FILE-001): {violations}"
        }
    return {"passed": True, "evidence": f"No magic number complaints in {len(records)} records"}
