#!/usr/bin/env python3
"""Session management: cleanup, listing, and maintenance.

Usage:
    python session_manager.py --cleanup --session-dir <session>
    python session_manager.py --cleanup-expired --max-age-hours <hours>
    python session_manager.py --list
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path


def find_sessions_base() -> Path:
    """Find the sessions base directory."""
    return Path(os.getcwd()) / ".ai" / "code-review-new" / "sessions"


def cleanup_session(session_dir: str):
    """Delete an entire session directory."""
    session_path = Path(session_dir)
    if not session_path.exists():
        print(json.dumps({
            "type": "ACTION_RESULT",
            "status": "SUCCESS",
            "method": "cleanup_review_session",
            "cleanup_path": session_dir,
            "message": "Session directory does not exist, already cleaned",
        }))
        return

    shutil.rmtree(session_path, ignore_errors=True)
    print(json.dumps({
        "type": "ACTION_RESULT",
        "status": "SUCCESS",
        "method": "cleanup_review_session",
        "cleanup_path": session_dir,
    }))


def cleanup_expired(max_age_hours: int = 6):
    """Delete session directories older than max_age_hours."""
    sessions_base = find_sessions_base()
    if not sessions_base.exists():
        print(json.dumps({
            "type": "ACTION_RESULT",
            "status": "SUCCESS",
            "method": "cleanup_expired_review_sessions",
            "scanned_count": 0,
            "deleted_count": 0,
        }))
        return

    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    scanned = 0
    deleted = 0

    for entry in sessions_base.iterdir():
        if not entry.is_dir():
            continue
        scanned += 1
        try:
            ctime = datetime.fromtimestamp(entry.stat().st_ctime)
            if ctime < cutoff:
                shutil.rmtree(entry, ignore_errors=True)
                deleted += 1
        except OSError:
            pass

    print(json.dumps({
        "type": "ACTION_RESULT",
        "status": "SUCCESS",
        "method": "cleanup_expired_review_sessions",
        "scanned_count": scanned,
        "deleted_count": deleted,
    }, ensure_ascii=False, indent=2))


def list_sessions():
    """List all sessions."""
    sessions_base = find_sessions_base()
    if not sessions_base.exists():
        print(json.dumps({"sessions": []}))
        return

    sessions = []
    for entry in sorted(sessions_base.iterdir()):
        if entry.is_dir():
            try:
                ctime = datetime.fromtimestamp(entry.stat().st_ctime)
                sessions.append({
                    "name": entry.name,
                    "path": str(entry),
                    "created": ctime.strftime("%Y-%m-%d %H:%M:%S"),
                })
            except OSError:
                pass

    print(json.dumps({"sessions": sessions}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Session management")
    parser.add_argument("--cleanup", action="store_true", help="Delete a specific session")
    parser.add_argument("--session-dir", help="Session directory to delete")
    parser.add_argument("--cleanup-expired", action="store_true", help="Delete expired sessions")
    parser.add_argument("--max-age-hours", type=int, default=6, help="Max session age in hours")
    parser.add_argument("--list", action="store_true", help="List all sessions")
    args = parser.parse_args()

    if args.cleanup and args.session_dir:
        cleanup_session(args.session_dir)
    elif args.cleanup_expired:
        cleanup_expired(args.max_age_hours)
    elif args.list:
        list_sessions()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
