#!/usr/bin/env python3
"""Prepare immutable GitHub pull-request review context."""

import argparse
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

from github_api import (
    GitHubAPIError,
    GitHubTransportError,
    SCHEMA_VERSION,
    atomic_write_json,
    canonical_json_bytes,
    fetch_pull_bundle,
    get_merge_base,
    get_pull,
    github_settings,
    load_config,
    parse_pull_identifier,
    sha256_bytes,
)


def create_session(project_root, prefix="pr"):
    session = (
        Path(project_root)
        / ".ai"
        / "code-review-new"
        / "sessions"
        / f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3)}"
    )
    for name in ("context", "reviewers", "inbox", "admission", "submission"):
        (session / name).mkdir(parents=True, exist_ok=True)
    atomic_write_json(session / "submission" / "review_store.json", [])
    return session


def _review_workspace(config, pull, expected_sha):
    head = pull.get("head", {})
    repo = head.get("repo") or {}
    result = {"available": False, "path": "", "message": "clone_repo_path not configured", "errors": []}
    try:
        from repo_manager import RepoManager

        result = RepoManager(config).clone_or_update(
            project_path=repo.get("full_name", ""),
            branch=head.get("ref", ""),
            ssh_url=repo.get("ssh_url", ""),
            http_url=repo.get("clone_url", ""),
            expected_sha=expected_sha,
        )
    except Exception as exc:  # Clone is optional; preserve API-only review.
        result = {"available": False, "path": "", "message": f"Clone error: {exc}", "errors": [str(exc)]}
    return result


def prepare_pull_context(info, config, session_dir):
    """Fetch and write one independent PR session."""
    session_dir = Path(session_dir)
    settings = github_settings(config, info["host"])
    bundle = fetch_pull_bundle(info, settings)
    pull = bundle["pull"]
    diffs = bundle["diffs"]
    diff_hash = sha256_bytes(canonical_json_bytes(diffs))
    reasons = bundle["partial_reasons"]
    complete = not reasons
    head_sha = pull.get("head", {}).get("sha", "")
    base_sha = pull.get("base", {}).get("sha", "")
    state = pull.get("state", "")
    merged = bool(pull.get("merged"))
    workspace = _review_workspace(config, pull, head_sha)

    diffs_file = session_dir / "context" / "diffs.json"
    comments_file = session_dir / "context" / "existing_review_comments.json"
    atomic_write_json(diffs_file, diffs)
    atomic_write_json(comments_file, bundle["discussion"])

    snapshot = {
        "host": info["host"],
        "api_base_url": settings["api_base_url"],
        "api_version": settings["api_version"],
        "token_env": settings["token_env"],
        "owner": info["owner"],
        "repo": info["repo"],
        "pull_number": info["number"],
        "state": state,
        "merged": merged,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "merge_base_sha": bundle["merge_base_sha"],
        "diff_sha256": diff_hash,
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }
    pull_metadata = {
        "url": info["url"],
        "owner": info["owner"],
        "repo": info["repo"],
        "number": info["number"],
        "title": pull.get("title", ""),
        "description": pull.get("body") or "",
        "author": pull.get("user", {}).get("login", ""),
        "draft": bool(pull.get("draft")),
        "mergeable": pull.get("mergeable"),
        "mergeable_state": pull.get("mergeable_state", "unknown"),
        "state": state,
        "merged": merged,
        "source_branch": pull.get("head", {}).get("ref", ""),
        "target_branch": pull.get("base", {}).get("ref", ""),
        "labels": [item.get("name", "") for item in pull.get("labels", [])],
    }
    context = {
        "schema_version": SCHEMA_VERSION,
        "platform": "github",
        "changed_files": [item.get("filename", "") for item in bundle["files"] if item.get("filename")],
        "diff_file": str(diffs_file),
        "existing_review_comments_file": str(comments_file),
        "snapshot": snapshot,
        "integrity": {
            "status": "complete" if complete else "partial",
            "reasons": reasons,
            "publish_allowed": complete and state == "open" and not merged,
        },
        "metadata": {
            "mode": "github_pr",
            "pull_request": pull_metadata,
            "review_workspace": workspace,
            "session_dir": str(session_dir),
        },
    }
    context_file = session_dir / "context" / "context.json"
    atomic_write_json(context_file, context)
    return {
        "type": "CONTEXT",
        "status": "SUCCESS" if complete else "PARTIAL",
        "context_file": str(context_file),
        "review_session": {
            "path": str(session_dir),
            "cleanup_path": str(session_dir),
            "review_store": str(session_dir / "submission" / "review_store.json"),
        },
        "review_workspace": workspace,
        "changed_files": context["changed_files"],
        "integrity": context["integrity"],
        "snapshot": snapshot,
    }


def _settings_for_snapshot(context, config):
    snapshot = context.get("snapshot", {})
    settings = github_settings(config, snapshot.get("host", "github.com"))
    for key in ("api_base_url", "api_version", "token_env"):
        if snapshot.get(key):
            settings[key] = snapshot[key]
    settings["token"] = os.environ.get(settings["token_env"], "")
    return settings


def check_revision(context_file, config=None):
    """Return a machine-readable fixed-head/status comparison."""
    context = json.loads(Path(context_file).read_text(encoding="utf-8"))
    snapshot = context.get("snapshot", {})
    required = ("owner", "repo", "pull_number", "head_sha", "state")
    missing = [key for key in required if key not in snapshot]
    if context.get("platform") != "github" or missing:
        raise ValueError(f"Invalid GitHub context snapshot; missing: {', '.join(missing)}")
    info = {
        "host": snapshot.get("host", "github.com"),
        "owner": snapshot["owner"],
        "repo": snapshot["repo"],
        "number": snapshot["pull_number"],
    }
    pull = get_pull(_settings_for_snapshot(context, config or load_config()), info)
    current = {
        "head_sha": pull.get("head", {}).get("sha", ""),
        "base_sha": pull.get("base", {}).get("sha", ""),
        "state": pull.get("state", ""),
        "merged": bool(pull.get("merged")),
    }
    if snapshot.get("merge_base_sha"):
        current["merge_base_sha"] = get_merge_base(_settings_for_snapshot(context, config or load_config()), info, pull)
    expected = {key: snapshot.get(key) for key in current}
    differences = {key: {"expected": expected[key], "current": current[key]} for key in expected if expected[key] != current[key]}
    return {
        "type": "REVISION_CHECK",
        "status": "STALE" if differences else "CURRENT",
        "current": not differences,
        "differences": differences,
        "expected": expected,
        "actual": current,
    }


def _error(exc):
    print(json.dumps({"type": "ERROR", "error_type": type(exc).__name__, "message": str(exc)}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="GitHub pull request context preparation")
    parser.add_argument("url", nargs="?", help="GitHub pull request URL")
    parser.add_argument("--check-revision", metavar="CONTEXT", help="Check a fixed context snapshot")
    parser.add_argument("--project-root", default=os.getcwd(), help="Project root directory")
    args = parser.parse_args()
    try:
        config = load_config(args.project_root)
        if args.check_revision:
            result = check_revision(args.check_revision, config)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            raise SystemExit(0 if result["current"] else 2)
        if not args.url:
            parser.error("url is required unless --check-revision is used")
        info = parse_pull_identifier(args.url)
        result = prepare_pull_context(info, config, create_session(args.project_root))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, json.JSONDecodeError, GitHubAPIError, GitHubTransportError, RuntimeError) as exc:
        _error(exc)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
