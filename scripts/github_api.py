#!/usr/bin/env python3
"""Small shared helpers for GitHub.com and GitHub Enterprise REST APIs."""

import hashlib
import json
import os
import re
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote, urlencode, urlparse


SCHEMA_VERSION = "1.0"
DEFAULT_API_VERSION = "2022-11-28"
_NAME = r"[A-Za-z0-9_.-]+"


class GitHubAPIError(RuntimeError):
    def __init__(self, message, status_code=None, data=None):
        super().__init__(message)
        self.status_code = status_code
        self.data = data


class GitHubTransportError(RuntimeError):
    pass


def load_config(project_root=None):
    """Load repository-local config first, then the skill default."""
    root = Path(project_root or os.getcwd())
    for path in (root / ".code-review-new" / "config.json", Path(__file__).parent.parent / "config.json"):
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return {}


def parse_pull_identifier(value, default_host="github.com"):
    """Parse a GitHub pull URL or ``owner/repo#number`` reference."""
    value = value.strip().rstrip("/.,;:)]}")
    if value.startswith(("http://", "https://")):
        parsed = urlparse(value)
        match = re.fullmatch(rf"/({_NAME})/({_NAME})/pull/(\d+)/?", parsed.path)
        if not parsed.hostname or not match:
            raise ValueError(f"Invalid GitHub pull request URL: {value}")
        owner, repo, number = match.groups()
        host = parsed.hostname.lower()
    else:
        match = re.fullmatch(rf"({_NAME})/({_NAME})#(\d+)", value)
        if not match:
            raise ValueError(f"Invalid GitHub pull request reference: {value}")
        owner, repo, number = match.groups()
        host = default_host.lower()
    return {
        "host": host,
        "owner": owner,
        "repo": repo,
        "number": int(number),
        "url": f"https://{host}/{owner}/{repo}/pull/{int(number)}",
    }


def github_settings(config, host="github.com"):
    """Resolve API settings without ever reading a token value from config."""
    github = config.get("github", {}) if isinstance(config.get("github", {}), dict) else {}
    host_config = github.get("hosts", {}).get(host, {}) if isinstance(github.get("hosts", {}), dict) else {}
    api_base = (
        host_config.get("api_base_url")
        or github.get("api_base_url")
        or config.get("github_api_base_url")
        or os.environ.get("GITHUB_API_URL")
        or ("https://api.github.com" if host == "github.com" else f"https://{host}/api/v3")
    )
    token_env = host_config.get("token_env") or github.get("token_env") or config.get("github_token_env") or "GITHUB_TOKEN"
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token_env):
        raise ValueError(f"Invalid GitHub token environment variable name: {token_env}")
    return {
        "api_base_url": api_base.rstrip("/"),
        "api_version": host_config.get("api_version") or github.get("api_version") or config.get("github_api_version") or DEFAULT_API_VERSION,
        "token_env": token_env,
        "token": os.environ.get(token_env, ""),
        "verify_ssl": host_config.get("verify_ssl", github.get("verify_ssl", config.get("verify_ssl", True))),
    }


def request_json(settings, method, path, *, params=None, payload=None, expected=(200,), timeout=30):
    """Perform one REST request. Mutating requests are deliberately never retried."""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": settings["api_version"],
        "User-Agent": "code-review-new",
    }
    if settings.get("token"):
        headers["Authorization"] = f"Bearer {settings['token']}"
    url = f"{settings['api_base_url']}{path}"
    if params:
        url += f"?{urlencode(params)}"
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    context = None if settings.get("verify_ssl", True) else ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            status_code = response.getcode()
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, ValueError):
            data = {"message": raw.decode("utf-8", errors="replace")[:500]}
        message = data.get("message", "") if isinstance(data, dict) else ""
        raise GitHubAPIError(f"GitHub API {method} {path} failed: {exc.code} {message}", exc.code, data) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise GitHubTransportError(str(exc)) from exc
    try:
        data = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, ValueError):
        data = {"message": raw.decode("utf-8", errors="replace")[:500]}
    if status_code not in expected:
        message = data.get("message", "") if isinstance(data, dict) else ""
        raise GitHubAPIError(f"GitHub API {method} {path} failed: {status_code} {message}", status_code, data)
    return data


def list_endpoint(settings, path, *, max_pages=None):
    """Read an array endpoint using GitHub's maximum page size."""
    items = []
    page = 1
    while max_pages is None or page <= max_pages:
        batch = request_json(settings, "GET", path, params={"per_page": 100, "page": page})
        if not isinstance(batch, list):
            raise GitHubAPIError(f"GitHub API returned a non-list for {path}")
        items.extend(batch)
        if len(batch) < 100:
            return items, False
        page += 1
    return items, True


def pull_path(info, suffix=""):
    owner = quote(info["owner"], safe="")
    repo = quote(info["repo"], safe="")
    return f"/repos/{owner}/{repo}/pulls/{info['number']}{suffix}"


def get_pull(settings, info):
    return request_json(settings, "GET", pull_path(info))


def get_merge_base(settings, info, pull):
    base_sha = pull.get("base", {}).get("sha", "")
    head_sha = pull.get("head", {}).get("sha", "")
    owner = quote(info["owner"], safe="")
    repo = quote(info["repo"], safe="")
    comparison = request_json(settings, "GET", f"/repos/{owner}/{repo}/compare/{quote(base_sha, safe='')}...{quote(head_sha, safe='')}")
    return comparison.get("merge_base_commit", {}).get("sha", "")


def get_pull_files(settings, info):
    files, capped = list_endpoint(settings, pull_path(info, "/files"), max_pages=30)
    reasons = ["github_3000_file_limit"] if capped else []
    reasons.extend(f"missing_patch:{item.get('filename', '')}" for item in files if item.get("patch") is None)
    return files, sorted(set(reasons))


def get_existing_review_data(settings, info):
    reviews, _ = list_endpoint(settings, pull_path(info, "/reviews"))
    comments, _ = list_endpoint(settings, pull_path(info, "/comments"))
    return {
        "schema_version": SCHEMA_VERSION,
        "platform": "github",
        "status": "SUCCESS",
        "review_count": len(reviews),
        "comment_count": len(comments),
        "reviews": [
            {
                "id": item.get("id"),
                "author": item.get("user", {}).get("login", ""),
                "state": item.get("state", ""),
                "body": item.get("body") or "",
                "commit_id": item.get("commit_id", ""),
                "submitted_at": item.get("submitted_at", ""),
            }
            for item in reviews
        ],
        "comments": [
            {
                "id": item.get("id"),
                "review_id": item.get("pull_request_review_id"),
                "author": item.get("user", {}).get("login", ""),
                "body": item.get("body") or "",
                "file_path": item.get("path", ""),
                "line": item.get("line") or item.get("original_line") or 0,
                "side": item.get("side") or item.get("original_side") or "",
                "commit_id": item.get("commit_id", ""),
                "in_reply_to_id": item.get("in_reply_to_id"),
                "created_at": item.get("created_at", ""),
            }
            for item in comments
        ],
    }


def anchor_patch(patch):
    """Add exact old/new line anchors to a GitHub unified patch."""
    lines = []
    old_line = new_line = 0
    for raw in (patch or "").splitlines():
        if raw.startswith("@@"):
            match = re.search(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", raw)
            if match:
                old_line, new_line = int(match.group(1)) - 1, int(match.group(2)) - 1
            lines.append(raw)
        elif raw.startswith("+") and not raw.startswith("+++"):
            new_line += 1
            lines.append(f"[N{new_line}]{raw[1:]}")
        elif raw.startswith("-") and not raw.startswith("---"):
            old_line += 1
            lines.append(f"[O{old_line}]{raw[1:]}")
        elif raw.startswith(" "):
            old_line += 1
            new_line += 1
            lines.append(f"[C{new_line}]{raw[1:]}")
        else:
            lines.append(raw)
    return lines


def files_to_diffs(files):
    records = []
    for item in files:
        status = item.get("status", "modified")
        filename = item.get("filename", "")
        old_path = item.get("previous_filename") or filename
        records.append({
            "file_path": filename,
            "old_path": old_path,
            "new_path": None if status == "removed" else filename,
            "status": status,
            "sha": item.get("sha", ""),
            "additions": item.get("additions", 0),
            "deletions": item.get("deletions", 0),
            "changes": item.get("changes", 0),
            "patch_missing": item.get("patch") is None,
            "content": anchor_patch(item.get("patch")),
        })
    return records


def canonical_json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def atomic_write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_bytes(json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
    os.replace(temporary, path)


def fetch_pull_bundle(info, settings, include_discussion=True):
    """Fetch one immutable PR input bundle and its completeness reasons."""
    pull = get_pull(settings, info)
    files, reasons = get_pull_files(settings, info)
    try:
        merge_base_sha = get_merge_base(settings, info, pull)
        if not merge_base_sha:
            reasons.append("merge_base_unavailable")
    except (GitHubAPIError, GitHubTransportError):
        merge_base_sha = ""
        reasons.append("merge_base_unavailable")
    discussion = None
    if include_discussion:
        try:
            discussion = get_existing_review_data(settings, info)
        except (GitHubAPIError, GitHubTransportError) as exc:
            discussion = {
                "schema_version": SCHEMA_VERSION,
                "platform": "github",
                "status": "ERROR",
                "review_count": 0,
                "comment_count": 0,
                "reviews": [],
                "comments": [],
                "message": str(exc),
            }
            reasons.append("existing_reviews_unavailable")
    return {
        "pull": pull,
        "files": files,
        "diffs": files_to_diffs(files),
        "merge_base_sha": merge_base_sha,
        "discussion": discussion,
        "partial_reasons": sorted(set(reasons)),
    }
