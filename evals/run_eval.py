#!/usr/bin/env python3
"""Eval runner for code-review-new skill.

Runs assertions against a completed review session directory.

Usage:
    python evals/run_eval.py --session <session_dir> [--eval-id <id>]
    python evals/run_eval.py --session <session_dir> --all
"""

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).parent.parent


def load_evals() -> list:
    """Load eval cases from evals.json."""
    evals_file = SKILL_ROOT / "evals" / "evals.json"
    with open(evals_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("evals", [])


def check_file_exists(session_dir: Path, paths: list) -> dict:
    """Assert that specified files exist in the session directory."""
    missing = [p for p in paths if not (session_dir / p).exists()]
    if missing:
        return {"passed": False, "evidence": f"Missing files: {missing}"}
    return {"passed": True, "evidence": f"All files exist: {paths}"}


def check_json_field(session_dir: Path, path: str, field: str, expected=None, pattern=None) -> dict:
    """Assert JSON file has expected field value or matches pattern."""
    file_path = session_dir / path
    if not file_path.exists():
        return {"passed": False, "evidence": f"File not found: {path}"}

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Navigate nested fields (e.g., "metadata.review_workspace.available")
    value = data
    for key in field.split("."):
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif isinstance(value, list) and key.isdigit():
            value = value[int(key)]
        else:
            return {"passed": False, "evidence": f"Field '{field}' not found in {path}"}

    if expected is not None:
        if value == expected:
            return {"passed": True, "evidence": f"{field} = {value}"}
        else:
            return {"passed": False, "evidence": f"{field} = {value}, expected {expected}"}

    if pattern is not None:
        if re.search(pattern, str(value)):
            return {"passed": True, "evidence": f"{field} matches /{pattern}/"}
        else:
            return {"passed": False, "evidence": f"{field} = '{value}' does not match /{pattern}/"}

    return {"passed": True, "evidence": f"{field} = {value}"}


def run_custom_assertion(session_dir: Path, script_path: str, **kwargs) -> dict:
    """Run a custom assertion script."""
    full_path = SKILL_ROOT / script_path
    if not full_path.exists():
        return {"passed": False, "evidence": f"Script not found: {script_path}"}

    spec = importlib.util.spec_from_file_location("assertion_module", full_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if hasattr(module, "check"):
        return module.check(session_dir, **kwargs)
    return {"passed": False, "evidence": f"No check() function in {script_path}"}


def run_assertion(assertion: dict, session_dir: Path) -> dict:
    """Run a single assertion against the session."""
    check_type = assertion.get("type", "")

    if check_type == "file_exists":
        return check_file_exists(session_dir, assertion.get("paths", []))
    elif check_type == "json_field_equals":
        return check_json_field(
            session_dir, assertion["path"], assertion["field"],
            expected=assertion.get("value")
        )
    elif check_type == "json_field_contains":
        return check_json_field(
            session_dir, assertion["path"], assertion["field"],
            pattern=assertion.get("pattern")
        )
    elif check_type == "file_glob":
        pattern = assertion.get("pattern", "")
        # Search in project root, not session
        matches = list(SKILL_ROOT.glob(pattern))
        if matches:
            return {"passed": True, "evidence": f"Found {len(matches)} files matching {pattern}"}
        return {"passed": False, "evidence": f"No files matching {pattern}"}
    elif check_type == "custom":
        return run_custom_assertion(
            session_dir, assertion["script"],
            **{k: v for k, v in assertion.items() if k not in ("type", "script", "check", "description", "id")}
        )
    else:
        return {"passed": False, "evidence": f"Unknown assertion type: {check_type}"}


def run_eval(eval_case: dict, session_dir: Path) -> dict:
    """Run all assertions for a single eval case."""
    results = []
    for assertion in eval_case.get("assertions", []):
        result = run_assertion(assertion, session_dir)
        results.append({
            "id": assertion.get("id", ""),
            "description": assertion.get("description", ""),
            "passed": result.get("passed", False),
            "evidence": result.get("evidence", ""),
        })

    passed_count = sum(1 for r in results if r["passed"])
    total = len(results)

    return {
        "eval_id": eval_case["id"],
        "eval_name": eval_case.get("name", ""),
        "passed": passed_count,
        "total": total,
        "pass_rate": f"{passed_count}/{total}",
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description="Run evals for code-review-new")
    parser.add_argument("--session", required=True, help="Path to completed review session directory")
    parser.add_argument("--eval-id", type=int, help="Run specific eval by ID")
    parser.add_argument("--all", action="store_true", help="Run all evals")
    args = parser.parse_args()

    session_dir = Path(args.session)
    if not session_dir.exists():
        print(f"Session not found: {session_dir}")
        sys.exit(1)

    evals = load_evals()

    if args.eval_id:
        evals = [e for e in evals if e["id"] == args.eval_id]
    elif not args.all:
        # Default: run all
        pass

    all_results = []
    for eval_case in evals:
        result = run_eval(eval_case, session_dir)
        all_results.append(result)

    # Output
    output = {
        "session": str(session_dir),
        "total_evals": len(all_results),
        "total_assertions": sum(r["total"] for r in all_results),
        "total_passed": sum(r["passed"] for r in all_results),
        "results": all_results,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
