#!/usr/bin/env python3
"""Build or explicitly submit one fixed-head GitHub pull-request review."""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from github_api import (
    GitHubAPIError,
    GitHubTransportError,
    atomic_write_json,
    canonical_json_bytes,
    get_existing_review_data,
    get_pull,
    github_settings,
    load_config,
    parse_pull_identifier,
    pull_path,
    request_json,
    sha256_bytes,
)


EVENTS = ("COMMENT", "APPROVE", "REQUEST_CHANGES")


def format_comment(record):
    body = record.get("comment") or record.get("body") or ""
    suggestion = record.get("fix_suggestion") or record.get("suggestion") or record.get("fix") or ""
    if "**问题描述**" not in body and "**安全类型**" not in body:
        body = f"**问题描述**：\n{body}\n\n**建议**：\n{suggestion or '请按适用规则修复'}"
    skill = "code-review-security" if "**安全类型**" in body or record.get("security") else "code-review"
    return f"检视skill:【{skill}】\n\n{body}\n\n**位置**：\n{record['file_path']}:{int(record['line'])}"


def _normalized(text):
    return re.sub(r"\W+", "", text or "").lower()


def is_duplicate(existing_comments, path, line, body):
    candidate = _normalized(body)
    for comment in existing_comments:
        if comment.get("file_path") != path or int(comment.get("line") or 0) != int(line):
            continue
        existing = _normalized(comment.get("body", ""))
        if candidate and existing and (candidate in existing or existing in candidate):
            return True
    return False


def added_anchors(diffs):
    anchors = {}
    for record in diffs:
        lines = anchors.setdefault(record.get("file_path", ""), set())
        for line in record.get("content", []):
            match = re.match(r"\[N(\d+)\]", line)
            if match:
                lines.add(int(match.group(1)))
    return anchors


def _integrity_artifact(session):
    for path in (
        session / "submission" / "review-integrity.json",
        session / "context" / "review-integrity.json",
        session / "review-integrity.json",
    ):
        if path.exists():
            return path, json.loads(path.read_text(encoding="utf-8"))
    return None, None


def integrity_complete(data):
    if not isinstance(data, dict):
        return False
    status = str(data.get("public_state") or data.get("status") or data.get("integrity_status") or data.get("state") or "").lower()
    if status != "complete" or data.get("red_flags") or data.get("publish_allowed") is not True:
        return False
    gate = data.get("publish_gate", data.get("publish_allowed", True))
    if isinstance(gate, dict):
        gate = gate.get("status") or gate.get("state") or gate.get("open")
    return gate not in (False, "closed", "blocked", "report_only")


def _candidate_records(records, config):
    enabled = set(config.get("enabled_severities", ["fatal", "major", "minor", "suggestion"]))
    minimum = int(config.get("min_reportable_confidence_score", 7))
    selected = []
    for record in records:
        if record.get("severity") not in enabled or int(record.get("confidence_score", 0)) < minimum:
            continue
        if record.get("publication_status", "publishable") != "publishable":
            continue
        if record.get("status", "pending") != "pending":
            continue
        selected.append(record)
    return selected


def _load_inputs(session, info, config):
    context_path = session / "context" / "context.json"
    store_path = session / "submission" / "review_store.json"
    if not context_path.exists() or not store_path.exists():
        raise ValueError("context.json and submission/review_store.json are required")
    context = json.loads(context_path.read_text(encoding="utf-8"))
    records = json.loads(store_path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("review_store.json must contain an array")
    diffs_path = Path(context.get("diff_file", ""))
    if not diffs_path.exists():
        raise ValueError("context diff_file is missing")
    diffs = json.loads(diffs_path.read_text(encoding="utf-8"))
    snapshot = context.get("snapshot", {})
    errors = []
    if context.get("platform") != "github":
        errors.append("context platform is not github")
    identity = (snapshot.get("owner", "").lower(), snapshot.get("repo", "").lower(), snapshot.get("pull_number"))
    requested = (info["owner"].lower(), info["repo"].lower(), info["number"])
    if identity != requested:
        errors.append("URL does not match the fixed context snapshot")
    if context.get("integrity", {}).get("status") != "complete" or not context.get("integrity", {}).get("publish_allowed", False):
        errors.append("context integrity is not complete/publishable")
    if sha256_bytes(canonical_json_bytes(diffs)) != snapshot.get("diff_sha256"):
        errors.append("fixed diff hash mismatch")
    integrity_path, integrity = _integrity_artifact(session)
    if not integrity_complete(integrity):
        errors.append("review-integrity.json is missing or incomplete")

    anchors = added_anchors(diffs)
    selected = _candidate_records(records, config)
    valid = []
    for index, record in enumerate(selected):
        try:
            path, line = record["file_path"], int(record["line"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"record {index} has an invalid path/line")
            continue
        if line not in anchors.get(path, set()):
            errors.append(f"record {index} is not anchored to an exact added line: {path}:{line}")
            continue
        if not (record.get("comment") or record.get("body")):
            errors.append(f"record {index} has an empty comment")
            continue
        valid.append(record)
    existing_path = Path(context.get("existing_review_comments_file", ""))
    existing = json.loads(existing_path.read_text(encoding="utf-8")) if existing_path.exists() else {"reviews": [], "comments": []}
    return context, snapshot, valid, existing, errors, integrity_path


def build_review_payload(records, existing, head_sha, event):
    comments = []
    skipped = 0
    for record in records:
        body = format_comment(record)
        if is_duplicate(existing.get("comments", []), record["file_path"], record["line"], body):
            skipped += 1
            continue
        comments.append({"path": record["file_path"], "line": int(record["line"]), "side": "RIGHT", "body": body})
    base = {
        "commit_id": head_sha,
        "event": event,
        "body": f"code-review-new: {len(comments)} 条检视意见",
        "comments": comments,
    }
    marker = sha256_bytes(canonical_json_bytes(base))[:20]
    base["body"] += f"\n\n<!-- code-review-new:{marker} -->"
    return base, marker, skipped


def _settings(context, config, host):
    settings = github_settings(config, host)
    snapshot = context.get("snapshot", {})
    for key in ("api_base_url", "api_version", "token_env"):
        if snapshot.get(key):
            settings[key] = snapshot[key]
    settings["token"] = os.environ.get(settings["token_env"], "")
    return settings


def _fresh_pull(settings, info, snapshot):
    pull = get_pull(settings, info)
    current_sha = pull.get("head", {}).get("sha", "")
    if current_sha != snapshot.get("head_sha"):
        raise ValueError(f"stale head SHA: expected {snapshot.get('head_sha')}, got {current_sha}")
    if pull.get("state") != "open" or pull.get("merged"):
        raise ValueError("pull request is no longer open")
    return pull


def submit_review_with_recovery(settings, info, payload, marker):
    try:
        return request_json(settings, "POST", pull_path(info, "/reviews"), payload=payload, expected=(200,), timeout=30), False
    except GitHubTransportError as original:
        # Unknown write result: recover by deterministic marker, never retry POST.
        try:
            existing = get_existing_review_data(settings, info)
        except (GitHubAPIError, GitHubTransportError):
            raise original
        needle = f"<!-- code-review-new:{marker} -->"
        for review in existing.get("reviews", []):
            if needle in review.get("body", ""):
                return {"id": review.get("id"), "state": review.get("state"), "recovered": True}, True
        raise original


def merge_with_recovery(settings, info, payload, expected_sha):
    try:
        result = request_json(settings, "PUT", pull_path(info, "/merge"), payload=payload, expected=(200,), timeout=30)
        if not result.get("merged"):
            raise GitHubAPIError(f"GitHub did not merge the pull request: {result.get('message', 'unknown error')}")
        return result, False
    except GitHubTransportError as original:
        # Unknown PUT result: one read determines whether the expected head was merged.
        try:
            pull = get_pull(settings, info)
        except (GitHubAPIError, GitHubTransportError):
            raise original
        if pull.get("merged") and pull.get("head", {}).get("sha") == expected_sha:
            return {"merged": True, "sha": expected_sha, "recovered": True}, True
        raise original


def run(args):
    session = Path(args.review_session_dir).resolve()
    info = parse_pull_identifier(args.url)
    config = load_config()
    context, snapshot, records, existing, gate_errors, integrity_path = _load_inputs(session, info, config)
    payload, marker, skipped = build_review_payload(records, existing, snapshot.get("head_sha", ""), args.event)
    merge_payload = {"sha": snapshot.get("head_sha", "")} if args.merge else None
    payload_artifact = {
        "schema_version": "1.0",
        "platform": "github",
        "pull_request": info,
        "review_payload": payload,
        "merge_payload": merge_payload,
        "publish_gate": {"status": "open" if not gate_errors else "closed", "errors": gate_errors},
        "dry_run": not args.apply,
    }
    payload_path = session / "submission" / "github_review_payload.json"
    atomic_write_json(payload_path, payload_artifact)
    if not args.apply:
        return {
            "type": "ACTION_RESULT",
            "status": "DRY_RUN",
            "method": "submit_reviews",
            "payload_path": str(payload_path),
            "comment_count": len(payload["comments"]),
            "skipped_count": skipped,
            "publish_gate": payload_artifact["publish_gate"],
        }, 0
    if gate_errors:
        return {"type": "ACTION_RESULT", "status": "BLOCKED", "method": "submit_reviews", "errors": gate_errors, "payload_path": str(payload_path)}, 1

    settings = _settings(context, config, info["host"])
    if not settings.get("token"):
        return {"type": "ACTION_RESULT", "status": "BLOCKED", "method": "submit_reviews", "errors": [f"Missing token in {settings['token_env']}"]}, 1
    _fresh_pull(settings, info, snapshot)
    fresh_existing = get_existing_review_data(settings, info)
    payload, marker, fresh_skipped = build_review_payload(records, fresh_existing, snapshot["head_sha"], args.event)
    skipped += fresh_skipped
    review_receipt = None
    recovered = False
    if payload["comments"] or args.event != "COMMENT":
        review_receipt, recovered = submit_review_with_recovery(settings, info, payload, marker)

    merge_receipt = None
    merge_recovered = False
    if args.merge:
        _fresh_pull(settings, info, snapshot)
        merge_receipt, merge_recovered = merge_with_recovery(settings, info, merge_payload, snapshot["head_sha"])

    receipt = {
        "schema_version": "1.0",
        "platform": "github",
        "head_sha": snapshot["head_sha"],
        "review": review_receipt,
        "review_recovered": recovered,
        "merge": merge_receipt,
        "merge_recovered": merge_recovered,
        "reported_count": len(payload["comments"]),
        "skipped_count": skipped,
        "integrity_artifact": str(integrity_path),
    }
    receipt_path = session / "submission" / "github_submission_receipt.json"
    atomic_write_json(receipt_path, receipt)
    return {
        "type": "ACTION_RESULT",
        "status": "SUCCESS",
        "method": "submit_reviews",
        "reported_count": len(payload["comments"]),
        "skipped_count": skipped,
        "merged": bool(merge_receipt),
        "receipt_path": str(receipt_path),
    }, 0


def main():
    parser = argparse.ArgumentParser(description="Dry-run or submit a fixed-head GitHub pull request review")
    parser.add_argument("url", help="GitHub pull request URL")
    parser.add_argument("--review-session-dir", required=True, help="Review session directory")
    parser.add_argument("--apply", action="store_true", help="Perform the remote GitHub write")
    parser.add_argument("--event", choices=EVENTS, default="COMMENT", help="GitHub review event (default: COMMENT)")
    parser.add_argument("--merge", action="store_true", help="Also merge using the fixed expected head SHA")
    args = parser.parse_args()
    try:
        result, code = run(args)
    except (GitHubAPIError, GitHubTransportError, RuntimeError, ValueError, OSError, json.JSONDecodeError) as exc:
        result, code = {"type": "ACTION_RESULT", "status": "FAILED", "method": "submit_reviews", "message": str(exc)}, 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
