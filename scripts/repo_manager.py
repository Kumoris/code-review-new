#!/usr/bin/env python3
"""Repository Manager for GitHub pull-request deep review.

Manages persistent local repository cloning for deep review.

Usage:
    python repo_manager.py --project-path <path> --branch <branch> --ssh-url <url> --http-url <url>
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def load_config() -> dict:
    """Load config.json."""
    config_paths = [
        Path.cwd() / ".code-review-new" / "config.json",
        Path(__file__).parent.parent / "config.json",
    ]
    for p in config_paths:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    return {}


class RepoManager:
    """Manage persistent local repository for deep review."""

    def __init__(self, config: dict):
        self.config = config
        self.clone_repo_path = config.get("clone_repo_path", "")

    def is_git_repo(self, directory: str) -> bool:
        """Check if directory is a git repository."""
        try:
            return (Path(directory) / ".git").is_dir()
        except Exception:
            return False

    def get_current_branch(self, repo_dir: str) -> str:
        """Get current branch name of a git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_dir,
                capture_output=True, text=True, timeout=10,
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except Exception:
            return ""

    def _run_git(self, args: list, cwd: str = None, timeout: int = 300) -> subprocess.CompletedProcess:
        """Run a git command."""
        return subprocess.run(
            args, cwd=cwd, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )

    def clone_or_update(self, project_path: str, branch: str,
                        ssh_url: str = "", http_url: str = "",
                        expected_sha: str = "") -> dict:
        """Clone or update a repository for deep review.

        Returns dict with: available, path, message, errors.
        """
        if not self.clone_repo_path:
            return {
                "available": False,
                "path": "",
                "message": "clone_repo_path not configured",
                "errors": [],
            }

        if not project_path or not branch:
            return {"available": False, "path": "", "message": "Missing repository or branch", "errors": []}
        if expected_sha and not re.fullmatch(r"[0-9a-fA-F]{40,64}", expected_sha):
            return {"available": False, "path": "", "message": "Invalid expected commit SHA", "errors": []}
        repo_name_flat = re.sub(r"[^A-Za-z0-9_.-]", "_", project_path)
        branch_dir = re.sub(r"[^A-Za-z0-9_.-]", "_", branch)
        target_dir = Path(self.clone_repo_path) / branch_dir / repo_name_flat
        errors = []

        # Check if repo already exists
        if target_dir.exists() and self.is_git_repo(str(target_dir)):
            if expected_sha:
                result = self._run_git(["git", "fetch", "origin", branch], cwd=str(target_dir))
                if result.returncode == 0:
                    result = self._run_git(["git", "checkout", "--detach", expected_sha], cwd=str(target_dir))
                actual = self._run_git(["git", "rev-parse", "HEAD"], cwd=str(target_dir))
                if result.returncode != 0 or actual.returncode != 0 or actual.stdout.strip() != expected_sha:
                    errors.append(f"Cannot checkout fixed head {expected_sha}: {(result.stderr or result.stdout)[:200]}")
                    return {"available": False, "path": "", "message": "Fixed-head checkout failed", "errors": errors}
                return {"available": True, "path": str(target_dir), "message": "Repo fixed at snapshot head", "errors": []}

            current_branch = self.get_current_branch(str(target_dir))
            if current_branch != branch:
                errors.append(f"Branch mismatch: expected {branch}, got {current_branch}")
                return {
                    "available": False,
                    "path": "",
                    "message": f"Branch mismatch: {current_branch} != {branch}",
                    "errors": errors,
                }
            result = self._run_git(["git", "pull", "origin", branch], cwd=str(target_dir))
            if result.returncode != 0:
                errors.append(f"git pull warning: {(result.stderr + result.stdout)[:200]}")
            return {"available": True, "path": str(target_dir), "message": "Repo updated via git pull", "errors": errors}

        # Clone the repository
        target_dir.parent.mkdir(parents=True, exist_ok=True)

        # Try SSH first, then HTTP fallback
        clone_url = ssh_url or http_url
        if not clone_url:
            return {"available": False, "path": "", "message": "No clone URL available", "errors": []}
        result = self._run_git(["git", "clone", "-b", branch, clone_url, str(target_dir)])

        if result.returncode != 0:
            # Try HTTP fallback
            fallback_url = http_url
            if fallback_url != clone_url:
                result = self._run_git(["git", "clone", "-b", branch, fallback_url, str(target_dir)])
            if result.returncode != 0:
                errors.append(f"git clone failed (SSH+HTTP): {result.stderr[:200]}")
                return {
                    "available": False,
                    "path": "",
                    "message": "Clone failed",
                    "errors": errors,
                }

        if expected_sha:
            result = self._run_git(["git", "checkout", "--detach", expected_sha], cwd=str(target_dir))
            actual = self._run_git(["git", "rev-parse", "HEAD"], cwd=str(target_dir))
            if result.returncode != 0 or actual.returncode != 0 or actual.stdout.strip() != expected_sha:
                errors.append(f"Cannot checkout fixed head {expected_sha}: {(result.stderr or result.stdout)[:200]}")
                return {"available": False, "path": "", "message": "Fixed-head checkout failed", "errors": errors}

        return {
            "available": True,
            "path": str(target_dir),
            "message": "Repo cloned successfully",
            "errors": [],
        }


def main():
    parser = argparse.ArgumentParser(description="Repository Manager for code-review-new")
    parser.add_argument("--project-path", required=True, help="GitHub repository (owner/repo)")
    parser.add_argument("--branch", required=True, help="Branch name")
    parser.add_argument("--ssh-url", default="", help="SSH clone URL")
    parser.add_argument("--http-url", default="", help="HTTP clone URL")
    parser.add_argument("--expected-sha", default="", help="Exact commit SHA to check out")
    args = parser.parse_args()

    config = load_config()
    manager = RepoManager(config)
    result = manager.clone_or_update(args.project_path, args.branch, args.ssh_url, args.http_url, args.expected_sha)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if not result["available"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
