#!/usr/bin/env python3
"""Read-only audit of planned/submitted comments against captured PR comments."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dedup_utils import deduplicate_findings, is_duplicate_finding


def _read(path: Path, default: object) -> object:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return default


def _records(data: object) -> list[dict]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if not isinstance(data, dict):
        return []
    for key in ("comments", "review_comments", "items", "nodes", "records"):
        if isinstance(data.get(key), list):
            result = []
            for item in data[key]:
                if not isinstance(item, dict):
                    continue
                nested = item.get("comments")
                if isinstance(nested, list):
                    result.extend(comment for comment in nested if isinstance(comment, dict))
                else:
                    result.append(item)
            return result
    return []


def _canonical(record: dict) -> dict:
    return {
        **record,
        "file_path": record.get("file_path") or record.get("file") or record.get("path") or record.get("original_path") or "",
        "line": record.get("line") or record.get("new_line") or record.get("original_line") or 0,
        "body": record.get("body") or record.get("comment") or record.get("content") or "",
    }


def audit(session: Path, line_tolerance: int) -> dict:
    review_store = session / "submission" / "review_store.json"
    planned = [_canonical(item) for item in _records(_read(review_store, []))]
    context_dir = session / "context"
    existing = []
    sources = []
    for name in ("existing_review_comments.json", "review_comments.json", "existing_comments.json"):
        path = context_dir / name
        if path.is_file():
            existing.extend(_canonical(item) for item in _records(_read(path, [])))
            sources.append(str(path))
    duplicate_pairs = []
    for index, candidate in enumerate(planned):
        for old in existing:
            if is_duplicate_finding(old, candidate, line_tolerance=line_tolerance):
                duplicate_pairs.append({
                    "planned_index": index,
                    "file_path": candidate["file_path"],
                    "line": candidate["line"],
                    "existing_comment_id": old.get("id"),
                })
                break
    unique_planned = deduplicate_findings(planned, line_tolerance=line_tolerance)
    return {
        "schema_version": 1,
        "status": "duplicates_found" if duplicate_pairs or len(unique_planned) != len(planned) else "clean",
        "review_store": str(review_store),
        "existing_comment_sources": sources,
        "planned_count": len(planned),
        "existing_count": len(existing),
        "duplicate_with_existing": duplicate_pairs,
        "duplicates_within_planned": len(planned) - len(unique_planned),
        "remote_action": "none",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit review comment duplicates without remote writes")
    parser.add_argument("url", help="GitHub PR URL recorded for audit identity")
    parser.add_argument("--session", required=True, type=Path, help="review session directory")
    parser.add_argument("--line-tolerance", type=int, default=30)
    args = parser.parse_args()
    if args.line_tolerance < 0:
        parser.error("--line-tolerance must be non-negative")
    try:
        result = audit(args.session.resolve(), args.line_tolerance)
        result["url"] = args.url
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"type": "ERROR", "error_type": "DEDUP_AUDIT_FAILED", "message": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
