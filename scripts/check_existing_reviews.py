#!/usr/bin/env python3
"""Check existing review comments on a GitHub PR snapshot.

Reads existing_review_comments.json and checks for duplicates
against new findings.

Usage:
    python check_existing_reviews.py --existing <existing_review_comments.json> --finding <finding_json>
"""

import argparse
import json
import sys


def is_duplicate(existing_comments: list, file_path: str, line: int, comment_body: str) -> bool:
    """Check if a finding duplicates an existing review comment.

    Checks same file + same line + similar content.
    """
    for comment in existing_comments:
        if (comment.get("file_path") == file_path and
                comment.get("line") == line):
            # Same file and line — check content similarity
            existing_body = comment.get("body", "")
            # Simple substring check for key phrases
            # Extract the 问题描述 section from both
            if _content_overlaps(existing_body, comment_body):
                return True
    return False


def _content_overlaps(existing: str, new: str) -> bool:
    """Check if two comment bodies overlap significantly.

    Simple heuristic: extract 问题描述 sections and compare.
    """
    def extract_issue(body: str) -> str:
        if "**问题描述**" in body:
            start = body.index("**问题描述**") + len("**问题描述**")
            end = body.find("**", start + 2)
            if end > start:
                return body[start:end].strip()
        return body[:100]

    existing_issue = extract_issue(existing)
    new_issue = extract_issue(new)

    # If either is empty, be conservative
    if not existing_issue or not new_issue:
        return False

    # Check if one contains the other
    return existing_issue in new_issue or new_issue in existing_issue


def main():
    parser = argparse.ArgumentParser(description="Check existing reviews for duplicates")
    parser.add_argument("--existing", required=True, help="existing_review_comments.json path")
    parser.add_argument("--file", required=True, help="Finding file path")
    parser.add_argument("--line", type=int, required=True, help="Finding line number")
    parser.add_argument("--comment", required=True, help="Finding comment body")
    args = parser.parse_args()

    with open(args.existing, "r", encoding="utf-8") as f:
        data = json.load(f)

    comments = data.get("comments", [])
    is_dup = is_duplicate(comments, args.file, args.line, args.comment)

    print(json.dumps({
        "is_duplicate": is_dup,
        "file_path": args.file,
        "line": args.line,
        "existing_comment_count": len(comments),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
