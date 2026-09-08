#!/usr/bin/env python3
"""Classify a fixed GitHub PR snapshot without making network requests."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


STATES = {"skip", "new_review", "re_review", "review_current", "merge_ready"}


def _load(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _paths(context: dict) -> list[str]:
    result = []
    for item in context.get("changed_files", []):
        path = item if isinstance(item, str) else item.get("filename", item.get("path", item.get("file_path", "")))
        if path and path not in result:
            result.append(str(path))
    return result


def _resolve_file(context_path: Path, value: object) -> Path | None:
    if not value:
        return None
    path = Path(str(value))
    candidates = [path] if path.is_absolute() else [context_path.parent / path, Path.cwd() / path]
    return next((candidate for candidate in candidates if candidate.exists()), None)


def _records(context: dict, context_path: Path, name: str) -> list[dict]:
    aliases = {
        "reviews": ("existing_reviews", "reviews"),
        "comments": ("existing_review_comments", "review_comments", "comments", "review_threads"),
    }[name]
    containers = [context, context.get("metadata", {}), context.get("snapshot", {})]
    for container in containers:
        for key in aliases:
            value = container.get(key) if isinstance(container, dict) else None
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            if isinstance(value, dict):
                for nested in (name, "items", "nodes", "comments", "threads"):
                    if isinstance(value.get(nested), list):
                        return [item for item in value[nested] if isinstance(item, dict)]
        file_keys = list(f"{alias}_file" for alias in aliases)
        file_keys.extend(("existing_review_comments_file", "existing_reviews_file"))
        for key in dict.fromkeys(file_keys):
            file_path = _resolve_file(context_path, container.get(key) if isinstance(container, dict) else None)
            if file_path:
                loaded = _load(file_path)
                if isinstance(loaded, list):
                    return [item for item in loaded if isinstance(item, dict)]
                if isinstance(loaded, dict):
                    for nested in (name, "items", "nodes", "comments", "threads"):
                        if isinstance(loaded.get(nested), list):
                            return [item for item in loaded[nested] if isinstance(item, dict)]
    return []


def _login(value: object) -> str:
    if isinstance(value, dict):
        return str(value.get("login", value.get("username", ""))).casefold()
    return str(value or "").casefold()


def _latest_review_states(reviews: list[dict]) -> dict[str, str]:
    latest: dict[str, str] = {}
    for review in reviews:
        actor = _login(review.get("user", review.get("author", ""))) or f"anonymous-{len(latest)}"
        state = str(review.get("state", review.get("status", ""))).upper()
        if state and state not in {"PENDING"}:
            latest[actor] = state
    return latest


def _is_unresolved(comment: dict) -> bool:
    if "isResolved" in comment:
        return not bool(comment["isResolved"])
    if "resolved" in comment:
        return not bool(comment["resolved"])
    return str(comment.get("state", "")).casefold() in {"open", "unresolved", "pending"}


def _latest_commit_id(records: list[dict]) -> str:
    dated = sorted(
        enumerate(records),
        key=lambda pair: (str(pair[1].get("submitted_at") or pair[1].get("created_at") or ""), pair[0]),
    )
    for _, item in reversed(dated):
        value = item.get("commit_id") or item.get("head_sha") or item.get("original_commit_id")
        if value:
            return str(value)
    return ""


def classify(context: dict, context_path: Path) -> dict:
    changed = _paths(context)
    snapshot = context.get("snapshot", {}) if isinstance(context.get("snapshot"), dict) else {}
    metadata = context.get("metadata", {}) if isinstance(context.get("metadata"), dict) else {}
    pull_request = metadata.get("pull_request", {}) if isinstance(metadata.get("pull_request"), dict) else {}
    state = str(snapshot.get("state", pull_request.get("state", metadata.get("state", context.get("state", "open"))))).casefold()
    head_sha = str(snapshot.get("head_sha", pull_request.get("head_sha", metadata.get("head_sha", ""))))
    author = _login(snapshot.get("author", pull_request.get("author", metadata.get("author", context.get("author", "")))))
    reviews = _records(context, context_path, "reviews")
    comments = _records(context, context_path, "comments")
    latest_states = _latest_review_states(reviews)
    unresolved = [comment for comment in comments if _is_unresolved(comment)]
    explicit_decision = str(snapshot.get("review_decision", pull_request.get("review_decision", metadata.get("review_decision", "")))).upper()
    approved = explicit_decision == "APPROVED" or "APPROVED" in latest_states.values()
    changes_requested = explicit_decision == "CHANGES_REQUESTED" or "CHANGES_REQUESTED" in latest_states.values()
    latest_review_sha = _latest_commit_id(reviews) or _latest_commit_id(comments)
    sha_changed = bool(head_sha and latest_review_sha and latest_review_sha != head_sha)
    author_replied = bool(author and any(_login(item.get("user", item.get("author", ""))) == author for item in comments))
    mergeable = snapshot.get("mergeable", pull_request.get("mergeable"))
    mergeable_state = str(snapshot.get("mergeable_state", pull_request.get("mergeable_state", ""))).casefold()
    platform_mergeable = mergeable is True or mergeable_state == "clean"

    evidence = {
        "pr_state": state,
        "review_count": len(reviews),
        "comment_count": len(comments),
        "unresolved_count": len(unresolved),
        "approved": approved,
        "changes_requested": changes_requested,
        "head_changed_since_review": sha_changed,
        "author_replied": author_replied,
        "platform_mergeable": platform_mergeable,
    }
    if state in {"closed", "merged"} or snapshot.get("merged") is True:
        classification, reason, focus = "skip", "pull request is closed or merged", []
    elif not reviews and not comments and not explicit_decision:
        classification, reason, focus = "new_review", "no prior review activity", changed
    elif sha_changed or (changes_requested and author_replied):
        candidates = metadata.get("delta_files") or snapshot.get("delta_files") or []
        focus_set = {str(path) for path in candidates}
        focus = [path for path in changed if path in focus_set] or changed
        classification, reason = "re_review", "new head or author response after requested changes"
    elif approved and not unresolved and not changes_requested and platform_mergeable:
        classification, reason, focus = "merge_ready", "approved with no unresolved review threads", []
    else:
        focus = []
        classification, reason = "review_current", "existing review activity applies to current head"

    return {
        "schema_version": 1,
        "classification": classification,
        "reason": reason,
        "focus_files": focus,
        "head_sha": head_sha,
        "evidence": evidence,
        "remote_action": "none",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify a GitHub PR context snapshot")
    parser.add_argument("--context", required=True, type=Path, help="context.json")
    parser.add_argument("--output", required=True, type=Path, help="classification output JSON")
    args = parser.parse_args()
    try:
        context = _load(args.context)
        if not isinstance(context, dict):
            raise ValueError("context must be a JSON object")
        result = classify(context, args.context.resolve())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "schema_version": 1,
            "classification": "new_review",
            "reason": "classification failed; fail-safe full review",
            "focus_files": [],
            "evidence": {"error": str(exc)},
            "remote_action": "none",
        }
    if result["classification"] not in STATES:
        raise AssertionError("invalid classifier state")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
