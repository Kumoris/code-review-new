#!/usr/bin/env python3
"""Offline evidence checks: real Git diffs and real parser executions."""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent


def load_parser(path):
    spec = importlib.util.spec_from_file_location("case_parser", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git_diff(before, after):
    with tempfile.TemporaryDirectory(prefix="review-evidence-") as directory:
        repo = Path(directory)
        subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
        path = repo / "counter.cpp"
        path.write_text(before)
        subprocess.run(["git", "-C", str(repo), "add", "counter.cpp"], check=True, capture_output=True)
        path.write_text(after)
        result = subprocess.run(["git", "-C", str(repo), "diff", "--no-ext-diff", "--no-textconv"],
                                check=True, capture_output=True, text=True)
        return result.stdout


def observe(module, diff):
    records = module.format_diff_with_anchors(diff)
    return {"paths": [record["file_path"] for record in records],
            "anchors": [line for record in records for line in record["content"]
                        if line.startswith(("[N", "[O", "[C"))]}


def no_shell_execution(module):
    """Spy on the real subprocess boundary; do not mock the parser or Git."""
    with tempfile.TemporaryDirectory(prefix="review-negative-control-") as directory:
        subprocess.run(["git", "init", "-q", directory], check=True, capture_output=True)
        marker = Path(directory) / "review_case_marker"
        literal = "HEAD; touch review_case_marker"
        with patch.object(module.subprocess, "run", wraps=subprocess.run) as invocation:
            with contextlib.redirect_stdout(io.StringIO()):
                try:
                    module.run_git(directory, ["rev-parse", literal])
                except SystemExit as error:
                    exit_code = error.code
                else:
                    raise AssertionError("Invalid literal revision should be rejected by Git")
        argv = invocation.call_args.args[0]
        assert argv == ["git", "rev-parse", literal]
        assert invocation.call_args.kwargs.get("shell", False) is False
        assert not marker.exists()
        assert exit_code != 0
        return {"hypothesis_origin": "controller_supplied_negative_control",
                "literal_argument_preserved": True, "shell_enabled": False,
                "marker_created": False, "git_rejected_literal_revision": True,
                "conclusion": "Excluded: this argument is not interpreted by a shell."}


def staged_context(before, after):
    with tempfile.TemporaryDirectory(prefix="review-staged-context-") as directory:
        repo = Path(directory)
        env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null",
                   PYTHONDONTWRITEBYTECODE="1")
        subprocess.run(["git", "init", "-q", directory], check=True, capture_output=True, env=env)
        (repo / "counter.cpp").write_text(before)
        subprocess.run(["git", "add", "counter.cpp"], cwd=repo, check=True, capture_output=True, env=env)
        subprocess.run(["git", "-c", "user.name=Review Example", "-c", "user.email=review@example.invalid",
                        "-c", "commit.gpgsign=false", "commit", "-qm", "Anonymous test input"],
                       cwd=repo, check=True, capture_output=True, env=env)
        (repo / "counter.cpp").write_text(after)
        subprocess.run(["git", "add", "counter.cpp"], cwd=repo, check=True, capture_output=True, env=env)
        results = {}
        for label in ("observed", "proposed"):
            process = subprocess.run([__import__("sys").executable,
                                      str(ROOT / "versions" / label / "local_context.py")],
                                     cwd=repo, env=env, check=True, capture_output=True, text=True)
            context_result = json.loads(process.stdout)
            results[label] = {"status": context_result["status"], "integrity": context_result["integrity"]}
        assert results["observed"]["status"] == "PARTIAL"
        assert results["observed"]["integrity"]["reasons"] == ["missing_patch:counter.cpp"]
        assert results["proposed"]["status"] == "SUCCESS"
        assert results["proposed"]["integrity"]["publish_allowed"] is False
        return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fixtures", action="store_true", help="Write the anonymous input fixtures")
    args = parser.parse_args()
    before = "int step(int counter) {\ncounter += 1;\nreturn counter;\n}\n"
    after = "int step(int counter) {\n++ counter;\nreturn counter;\n}\n"
    diff = git_diff(before, after)
    observed = load_parser(ROOT / "versions/observed/local_context.py")
    proposed = load_parser(ROOT / "versions/proposed/local_context.py")
    old_result, new_result = observe(observed, diff), observe(proposed, diff)
    assert old_result["paths"] == ["counter;"]
    assert "[N2]++ counter;" not in old_result["anchors"]
    assert new_result["paths"] == ["counter.cpp"]
    assert "[N2]++ counter;" in new_result["anchors"]
    assert "[C3]return counter;" in new_result["anchors"]

    removed_before = "int step(int counter) {\n-- counter;\nreturn counter + 1;\n}\n"
    removed_after = "int step(int counter) {\ncounter -= 1;\nreturn counter;\n}\n"
    removed_diff = git_diff(removed_before, removed_after)
    removed_old, removed_new = observe(observed, removed_diff), observe(proposed, removed_diff)
    assert "[O2]-- counter;" not in removed_old["anchors"]
    assert "[O2]-- counter;" in removed_new["anchors"]
    assert "[O3]return counter + 1;" in removed_new["anchors"]
    normal_diff = git_diff(before, before.replace("+= 1", "+= 2"))
    assert observe(observed, normal_diff) == observe(proposed, normal_diff)

    result = {
        "schema_version": 1, "scope": "Local parser evidence; no network or PR publication",
        "python_version": __import__("sys").version.split()[0],
        "git_version": subprocess.check_output(["git", "--version"], text=True).strip(),
        "valid_finding": {"input_diff_sha256": hashlib.sha256(diff.encode()).hexdigest(),
                          "observed": old_result, "proposed": new_result,
                          "confirmed": True, "proposed_fix_passed": True},
        "removed_payload": {"observed": removed_old, "proposed": removed_new},
        "ordinary_diff_unchanged": True,
        "staged_cli": staged_context(before, after),
        "excluded_hypothesis": no_shell_execution(observed),
        "checks_passed": 6,
        "checks": ["added payload stays in its file", "added and context line numbers",
                   "removed payload and old line numbers", "ordinary diff compatibility",
                   "shell injection negative control", "real staged context CLI"],
    }
    if args.fixtures:
        for name, content in {"before.cpp": before, "after.cpp": after, "input.diff": diff}.items():
            path = ROOT / "fixtures" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
