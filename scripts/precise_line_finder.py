#!/usr/bin/env python3
"""Precise line finder for diff-backed review comments.

Maps logical line numbers to diff anchor positions for accurate
comment placement on GitHub or local reports.

Usage:
    python precise_line_finder.py --diffs <diffs.json> --file <file_path> --search-line <line>
"""

import argparse
import json
import sys


def find_nearest_n_anchor(diffs_data: list, file_path: str, target_line: int) -> int:
    """Return target_line only when it is an exact [N] anchor."""
    for diff_record in diffs_data:
        record_path = diff_record.get("file_path") or diff_record.get("path", "")
        if record_path != file_path:
            continue

        content = diff_record.get("content", [])
        if isinstance(content, list):
            n_anchors = []
            for line in content:
                line_str = str(line)
                if line_str.startswith("[N"):
                    try:
                        end = line_str.index("]")
                        n = int(line_str[2:end])
                        n_anchors.append(n)
                    except (ValueError, IndexError):
                        pass

            if target_line in n_anchors:
                return target_line

    return -1


def main():
    parser = argparse.ArgumentParser(description="Exact [N] line validator")
    parser.add_argument("--diffs", required=True, help="diffs.json path")
    parser.add_argument("--file", required=True, help="Target file path")
    parser.add_argument("--search-line", type=int, required=True, help="Target line number")
    args = parser.parse_args()

    with open(args.diffs, "r", encoding="utf-8") as f:
        diffs_data = json.load(f)

    result_line = find_nearest_n_anchor(diffs_data, args.file, args.search_line)

    print(json.dumps({
        "file_path": args.file,
        "search_line": args.search_line,
        "found_line": result_line,
        "found": result_line > 0,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
