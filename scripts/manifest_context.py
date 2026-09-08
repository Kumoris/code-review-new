#!/usr/bin/env python3
"""Create independent GitHub PR sessions referenced by a manifest PR."""

import argparse
import json
import os
import re
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
    github_settings,
    load_config,
    parse_pull_identifier,
    sha256_bytes,
)
from github_context import prepare_pull_context


_FULL_PULL = re.compile(r"https?://[^/\s]+/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/pull/\d+", re.IGNORECASE)
_SHORT_PULL = re.compile(r"(?<![A-Za-z0-9_.-])([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#\d+)")


def create_manifest_session(project_root):
    session = (
        Path(project_root)
        / ".ai"
        / "code-review-new"
        / "sessions"
        / f"manifest-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3)}"
    )
    for name in ("context", "reviewers", "inbox", "admission", "submission", "sub_sessions"):
        (session / name).mkdir(parents=True, exist_ok=True)
    atomic_write_json(session / "submission" / "manifest_review_store.json", [])
    return session


def detect_sub_pulls(text, default_host="github.com"):
    """Extract and canonicalize supported full URLs and owner/repo#N refs."""
    found = []
    seen = set()
    candidates = [match.group(0) for match in _FULL_PULL.finditer(text or "")]
    candidates += [match.group(1) for match in _SHORT_PULL.finditer(text or "")]
    for candidate in candidates:
        try:
            info = parse_pull_identifier(candidate, default_host)
        except ValueError:
            continue
        key = (info["host"], info["owner"].lower(), info["repo"].lower(), info["number"])
        if key not in seen:
            found.append(info)
            seen.add(key)
    return found


def _sub_session(parent, info):
    name = f"{info['owner']}_{info['repo']}-pr-{info['number']}"
    directory = parent / "sub_sessions" / re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    for item in ("context", "reviewers", "inbox", "admission", "submission"):
        (directory / item).mkdir(parents=True, exist_ok=True)
    atomic_write_json(directory / "submission" / "review_store.json", [])
    return directory


def _result_summary(result, info):
    return {
        "status": result["status"],
        "owner": info["owner"],
        "repo": info["repo"],
        "number": info["number"],
        "url": info["url"],
        "session_path": result["review_session"]["path"],
        "context_file": result["context_file"],
        "review_store": result["review_session"]["review_store"],
        "changed_files": result["changed_files"],
        "snapshot": result["snapshot"],
        "integrity": result["integrity"],
        "review_workspace": result["review_workspace"],
    }


def prepare_manifest(url, project_root, config):
    manifest_info = parse_pull_identifier(url)
    manifest_settings = github_settings(config, manifest_info["host"])
    manifest_bundle = fetch_pull_bundle(manifest_info, manifest_settings, include_discussion=False)
    pull = manifest_bundle["pull"]
    searchable = [pull.get("body") or ""]
    searchable.extend(item.get("patch") or "" for item in manifest_bundle["files"])
    refs = detect_sub_pulls("\n".join(searchable), manifest_info["host"])
    self_key = (manifest_info["host"], manifest_info["owner"].lower(), manifest_info["repo"].lower(), manifest_info["number"])
    refs = [item for item in refs if (item["host"], item["owner"].lower(), item["repo"].lower(), item["number"]) != self_key]
    session = create_manifest_session(project_root)
    results = []
    aggregate_diffs = []
    for info in refs:
        try:
            result = prepare_pull_context(info, config, _sub_session(session, info))
            results.append(_result_summary(result, info))
            diffs = json.loads(Path(result["context_file"]).with_name("diffs.json").read_text(encoding="utf-8"))
            aggregate_diffs.extend({**item, "repository": f"{info['owner']}/{info['repo']}", "pull_number": info["number"]} for item in diffs)
        except (GitHubAPIError, GitHubTransportError, RuntimeError, ValueError, OSError, json.JSONDecodeError) as exc:
            results.append({"status": "ERROR", "url": info["url"], "owner": info["owner"], "repo": info["repo"], "number": info["number"], "error": str(exc)})

    parent_diffs = session / "context" / "diffs.json"
    atomic_write_json(parent_diffs, aggregate_diffs)
    reasons = list(manifest_bundle["partial_reasons"])
    if any(item["status"] != "SUCCESS" for item in results):
        reasons.append("sub_pull_context_incomplete")
    if any(item.get("integrity", {}).get("status") != "complete" for item in results if item["status"] == "SUCCESS"):
        reasons.append("sub_pull_diff_partial")
    reasons = sorted(set(reasons))
    complete = not reasons
    changed_files = sorted({path for result in results for path in result.get("changed_files", [])})
    manifest_snapshot = {
        "host": manifest_info["host"],
        "api_base_url": manifest_settings["api_base_url"],
        "api_version": manifest_settings["api_version"],
        "token_env": manifest_settings["token_env"],
        "owner": manifest_info["owner"],
        "repo": manifest_info["repo"],
        "pull_number": manifest_info["number"],
        "state": pull.get("state", ""),
        "merged": bool(pull.get("merged")),
        "base_sha": pull.get("base", {}).get("sha", ""),
        "head_sha": pull.get("head", {}).get("sha", ""),
        "merge_base_sha": manifest_bundle["merge_base_sha"],
        "diff_sha256": sha256_bytes(canonical_json_bytes(manifest_bundle["diffs"])),
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }
    context = {
        "schema_version": SCHEMA_VERSION,
        "platform": "github_manifest",
        "changed_files": changed_files,
        "diff_file": str(parent_diffs),
        "snapshot": manifest_snapshot,
        "sub_pull_snapshots": [item["snapshot"] for item in results if item["status"] == "SUCCESS"],
        "integrity": {"status": "complete" if complete else "partial", "reasons": reasons, "publish_allowed": False},
        "manifest_pull": {
            "url": manifest_info["url"],
            "owner": manifest_info["owner"],
            "repo": manifest_info["repo"],
            "number": manifest_info["number"],
            "title": pull.get("title", ""),
            "description": pull.get("body") or "",
            "author": pull.get("user", {}).get("login", ""),
        },
        "sub_pulls": results,
        "metadata": {"mode": "manifest", "session_dir": str(session), "review_workspace": {"available": False, "path": ""}},
    }
    context_file = session / "context" / "context.json"
    atomic_write_json(context_file, context)
    return {
        "type": "MANIFEST_CONTEXT",
        "status": "SUCCESS" if complete else "PARTIAL",
        "context_file": str(context_file),
        "review_session": {"path": str(session), "cleanup_path": str(session), "review_store": str(session / "submission" / "manifest_review_store.json")},
        "sub_pulls": results,
        "changed_files": changed_files,
        "integrity": context["integrity"],
    }


def main():
    parser = argparse.ArgumentParser(description="GitHub Manifest pull request context preparation")
    parser.add_argument("url", help="GitHub manifest pull request URL")
    parser.add_argument("--project-root", default=os.getcwd(), help="Project root directory")
    args = parser.parse_args()
    try:
        print(json.dumps(prepare_manifest(args.url, args.project_root, load_config(args.project_root)), ensure_ascii=False, indent=2))
    except (GitHubAPIError, GitHubTransportError, RuntimeError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"type": "ERROR", "error_type": type(exc).__name__, "message": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
