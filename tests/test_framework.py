#!/usr/bin/env python3
"""Offline contract checks for the GitHub-native review framework."""

from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import dedup_utils
import deep_review_analyzer
import ensure_adversary
import github_api
import github_context
import knowledge_manager
import local_context
import manifest_context
import pr_classifier
import prescan
import render_report
import review_admission
import review_core
import submit_reviews
import token_estimator


def write_json(path: Path, value: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return path


class GitHubPlatformTests(unittest.TestCase):
    def test_pull_identifiers_and_enterprise_settings(self):
        full = github_api.parse_pull_identifier("https://ghe.example/acme/widget/pull/7")
        short = github_api.parse_pull_identifier("acme/widget#7")
        self.assertEqual((full["host"], full["owner"], full["repo"], full["number"]),
                         ("ghe.example", "acme", "widget", 7))
        self.assertEqual(short["url"], "https://github.com/acme/widget/pull/7")
        settings = github_api.github_settings({"github_token_env": "TEST_GH_TOKEN"}, "ghe.example")
        self.assertEqual(settings["api_base_url"], "https://ghe.example/api/v3")
        self.assertEqual(settings["token"], "")

    def test_paginated_files_and_partial_reasons(self):
        first = [{"filename": f"src/f{i}.py", "patch": "@@ -0,0 +1 @@\n+x"} for i in range(100)]
        second = [{"filename": "bin.dat", "patch": None}]
        with mock.patch.object(github_api, "request_json", side_effect=[first, second]):
            files, reasons = github_api.get_pull_files({}, {"owner": "o", "repo": "r", "number": 1})
        self.assertEqual(len(files), 101)
        self.assertEqual(reasons, ["missing_patch:bin.dat"])
        with mock.patch.object(github_api, "request_json", return_value=first):
            files, reasons = github_api.get_pull_files({}, {"owner": "o", "repo": "r", "number": 1})
        self.assertEqual(len(files), 3000)
        self.assertIn("github_3000_file_limit", reasons)

    def test_diff_anchors_and_special_statuses(self):
        files = [
            {"filename": "new.py", "status": "renamed", "previous_filename": "old.py", "patch": "@@ -1 +1 @@\n-old\n+new"},
            {"filename": "gone.py", "status": "removed", "patch": "@@ -2 +1,0 @@\n-old"},
            {"filename": "image.png", "status": "modified", "patch": None},
        ]
        records = github_api.files_to_diffs(files)
        self.assertEqual(records[0]["old_path"], "old.py")
        self.assertIn("[N1]new", records[0]["content"])
        self.assertIsNone(records[1]["new_path"])
        self.assertTrue(records[2]["patch_missing"])

    def test_http_403_and_422_are_not_retried(self):
        for status in (403, 422):
            with self.subTest(status=status):
                error = urllib.error.HTTPError(
                    "https://api.github.com/x", status, "rejected", {}, io.BytesIO(b'{"message":"rejected"}')
                )
                with mock.patch("urllib.request.urlopen", side_effect=error) as urlopen:
                    with self.assertRaises(github_api.GitHubAPIError) as caught:
                        github_api.request_json(
                            {"api_base_url": "https://api.github.com", "api_version": "2022-11-28", "verify_ssl": True},
                            "POST", "/x", payload={"x": 1}, expected=(200,),
                        )
                self.assertEqual(caught.exception.status_code, status)
                urlopen.assert_called_once()

    def test_revision_check_detects_stale_head(self):
        with tempfile.TemporaryDirectory() as directory:
            context = write_json(Path(directory) / "context.json", {
                "platform": "github",
                "snapshot": {"host": "github.com", "owner": "o", "repo": "r", "pull_number": 1,
                             "head_sha": "old", "state": "open", "merged": False},
            })
            with mock.patch.object(github_context, "get_pull", return_value={
                "head": {"sha": "new"}, "state": "open", "merged": False,
            }):
                result = github_context.check_revision(context, {})
        self.assertEqual(result["status"], "STALE")
        self.assertIn("head_sha", result["differences"])

    def test_manifest_reference_dedup_and_limit_input(self):
        refs = manifest_context.detect_sub_pulls(
            "https://github.com/A/R/pull/2 A/R#2 b/r#3 https://ghe.test/c/r/pull/4"
        )
        self.assertEqual(len(refs), 3)
        self.assertEqual({(item["host"], item["number"]) for item in refs},
                         {("github.com", 2), ("github.com", 3), ("ghe.test", 4)})


class RoutingTests(unittest.TestCase):
    def _context(self, root: Path, content: list[str], changed=None) -> Path:
        diffs = write_json(root / "diffs.json", [{"file_path": "src/app.py", "content": content}])
        return write_json(root / "context.json", {
            "changed_files": changed or ["src/app.py"],
            "diff_file": str(diffs),
            "snapshot": {"head_sha": "abc"},
            "metadata": {"review_workspace": {"available": False, "path": ""}},
        })

    def test_prescan_trivial_and_security_signal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            trivial = prescan.run(self._context(root, ["[N1]# note"]))
            risky = prescan.run(self._context(root, ["[N1]password = 'secret'", "[N2]requests.get(url, verify=False)"]))
        self.assertTrue(trivial["trivial"])
        checks = risky["files"][0]["always_check"]
        self.assertEqual(checks["hardcoded-credentials"], "signal")
        self.assertEqual(checks["digital-certificates"], "signal")
        self.assertEqual(risky["finding_candidates"], [])

    def test_classifier_five_state_boundaries(self):
        base = {"changed_files": ["a.py"], "snapshot": {"state": "open", "head_sha": "h"}, "metadata": {}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "context.json"
            self.assertEqual(pr_classifier.classify(base, path)["classification"], "new_review")
            closed = {**base, "snapshot": {**base["snapshot"], "state": "closed"}}
            self.assertEqual(pr_classifier.classify(closed, path)["classification"], "skip")
            current = {**base, "existing_reviews": [{"author": "r", "state": "COMMENTED", "commit_id": "h"}]}
            self.assertEqual(pr_classifier.classify(current, path)["classification"], "review_current")
            stale = {**base, "existing_reviews": [{"author": "r", "state": "COMMENTED", "commit_id": "old"}]}
            self.assertEqual(pr_classifier.classify(stale, path)["classification"], "re_review")
            ready = {**base, "snapshot": {**base["snapshot"], "mergeable": True},
                     "existing_reviews": [{"author": "r", "state": "APPROVED", "commit_id": "h"}]}
            self.assertEqual(pr_classifier.classify(ready, path)["classification"], "merge_ready")

    def test_token_limits_and_five_concurrent_cap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = self._context(root, ["[N1]x = 1"], changed=["src/app.py"])
            manifest = write_json(root / "manifest.json", {
                "review_tasks": [{"task_id": f"t{i}", "scope_file_paths": ["src/app.py"]} for i in range(8)]
            })
            result = token_estimator.estimate(
                context, None, manifest, budget_limit=1, task_budget=1, marginal_ratio=.8,
                bytes_per_token=3, max_rule_fraction=.3,
            )
        self.assertEqual(result["recommendation"], "exceeds_budget")
        self.assertEqual(result["pipeline_estimates"]["max_concurrent_reviewers"], 5)
        self.assertTrue(all(item["task_recommendation"] == "exceeds_task_budget"
                            for item in result["per_task_breakdown"]))

    def test_dedup_and_knowledge_lru(self):
        finding = {"file_path": "a.py", "line": 10, "evidence": "user_id reaches unsafe_query"}
        duplicate = {"file_path": "a.py", "line": 11, "evidence": "unsafe_query receives user_id"}
        self.assertTrue(dedup_utils.is_duplicate_finding(finding, duplicate, min_identifier_overlap=2))
        entries = [
            {"id": str(i), "category": "security", "last_used_at": f"2026-01-{i + 1:02d}"}
            for i in range(12)
        ]
        kept = knowledge_manager._merge_lru(entries, [], per_category=10, total=50)
        self.assertEqual(len(kept), 10)
        self.assertEqual(kept[0]["id"], "11")


class IntegrityAdmissionTests(unittest.TestCase):
    def _run_fixture(self, root: Path):
        session = root / "session"
        diffs = write_json(session / "context" / "diffs.json", [
            {"file_path": "a.py", "content": ["@@ -0,0 +1 @@", "[N1]dangerous(user)"]}
        ])
        context = write_json(session / "context" / "context.json", {
            "platform": "local", "changed_files": ["a.py"], "diff_file": str(diffs),
            "snapshot": {"head_sha": "fixed"},
            "integrity": {"status": "complete", "publish_allowed": False},
            "metadata": {"review_workspace": {"available": False, "path": ""}},
        })
        manifest = write_json(session / "context" / "review_manifest.json", {
            "review_tasks": [{"task_id": "t1", "agent_id": "reviewer-1", "scope_file_paths": ["a.py"],
                              "rule_ids_by_file": {"a.py": ["PY-SEC-001"]}}],
            "coverage": {"routed_files": ["a.py"], "unsupported_files": []},
        })
        args = argparse.Namespace(
            session_dir=str(session), context=str(context), manifest=str(manifest),
            registry=str(ROOT / "references" / "rule-registry.md"), run_id="test-run",
            budget_minutes=30, require_adversary=False, require_synthesizer=False,
        )
        review_core.init_run(args)
        return session

    def test_sender_binding_revision_and_tamper_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            session = self._run_fixture(Path(directory))
            bind = argparse.Namespace(session_dir=str(session), assignment_id="review:t1",
                                      sender_handle="agent/real", agent_id="reviewer-1")
            review_core.bind_agent(bind)
            bad = write_json(Path(directory) / "bad.json", {
                "schema_version": 1, "role": "reviewer", "agent_id": "reviewer-1",
                "task_id": "t1", "revision": "stale", "findings": [],
            })
            with self.assertRaises(review_core.IntegrityError):
                review_core.capture_response(argparse.Namespace(
                    session_dir=str(session), assignment_id="review:t1", sender_handle="agent/real", response=str(bad)
                ))
            good = write_json(Path(directory) / "good.json", {
                "schema_version": 1, "role": "reviewer", "agent_id": "reviewer-1",
                "task_id": "t1", "revision": "fixed", "findings": [],
            })
            receipt = review_core.capture_response(argparse.Namespace(
                session_dir=str(session), assignment_id="review:t1", sender_handle="agent/real", response=str(good)
            ))
            Path(receipt["raw_wrapper_path"]).write_text("{}", encoding="utf-8")
            result = review_core.verify_integrity(session, check_zero=False)
        self.assertEqual(result["public_state"], "blocked")
        self.assertIn("integrity-artifact-mismatch", {item["flag"] for item in result["errors"]})

    def test_admission_exact_anchor_rules_proof_and_verdicts(self):
        registry = review_core.load_rule_registry(ROOT / "references" / "rule-registry.md")
        finding = {
            "id": "F1", "file": "a.py", "line": 1, "severity": "major",
            "evidence": "用户输入直接进入危险调用", "impact": "当前请求执行失败", "fix": "校验输入",
            "rules": "references/python.md: PY-SEC-001", "confidence_score": 8,
        }
        ok, reason = review_admission.validate_finding(
            finding, {"a.py"}, {"a.py": {1}}, allowed_rules={"PY-SEC-001"}, registry=registry
        )
        self.assertTrue(ok, reason)
        bad = {**finding, "line": 2}
        self.assertFalse(review_admission.validate_finding(
            bad, {"a.py"}, {"a.py": {1}}, allowed_rules={"PY-SEC-001"}, registry=registry
        )[0])
        challenges, fallback = review_admission._challenge_map({"challenges": [
            {"finding_id": verdict, "verdict": verdict, "rationale": "x"}
            for verdict in ("DEFINITE", "LIKELY", "PLAUSIBLE", "SPECULATIVE")
        ]})
        self.assertFalse(fallback)
        self.assertEqual(set(challenges), {"DEFINITE", "LIKELY", "PLAUSIBLE", "SPECULATIVE"})
        self.assertEqual(review_admission._downgrade("major"), "minor")

    def test_manifest_coverage_is_exact_and_task_limited(self):
        context = {"changed_files": ["a.py", "asset.bin"]}
        valid = {
            "review_tasks": [{"task_id": "t", "scope_file_paths": ["a.py"]}],
            "coverage": {"routed_files": ["a.py"], "unsupported_files": ["asset.bin"]},
        }
        self.assertEqual(review_core.manifest_coverage(context, valid), [])
        overlap = {**valid, "coverage": {"routed_files": ["a.py"], "unsupported_files": ["a.py", "asset.bin"]}}
        self.assertTrue(review_core.manifest_coverage(context, overlap))
        too_many = {
            "review_tasks": [{"task_id": str(i), "scope_file_paths": ["a.py"]} for i in range(9)],
            "coverage": {"routed_files": ["a.py"], "unsupported_files": ["asset.bin"]},
        }
        self.assertTrue(any("8-task" in error["message"] for error in review_core.manifest_coverage(context, too_many)))

    def test_fallback_is_report_only(self):
        fallback = ensure_adversary.build_fallback(
            {"snapshot": {"head_sha": "fixed"}}, {"t1": []},
            review_core.load_rule_registry(ROOT / "references" / "rule-registry.md"),
        )
        self.assertTrue(fallback["fallback"])
        self.assertFalse(fallback["publish_eligible"])

    def test_deep_review_only_routes_modify_remove_and_interface(self):
        analyses = deep_review_analyzer.analyze_file_changes([{
            "file_path": "service.py",
            "content": [
                "[O2]def changed(value):",
                "[N2]def changed(value, strict=False):",
                "[O8]def removed(value):",
                "[N20]def added(value):",
            ],
        }])
        types = {kind for change in analyses[0]["changes"] for kind in change["change_types"]}
        self.assertEqual(types, {"METHOD_MODIFY", "METHOD_REMOVE"})

    def test_zero_finding_second_pass_closes_then_completes_local_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session = root / "session"
            files = ["a.py", "b.py", "c.py"]
            diffs = write_json(session / "context" / "diffs.json", [
                {"file_path": path, "content": ["@@ -0,0 +1 @@", "[N1]value = 1"]} for path in files
            ])
            context = write_json(session / "context" / "context.json", {
                "platform": "local", "changed_files": files, "diff_file": str(diffs),
                "snapshot": {"head_sha": "fixed"},
                "integrity": {"status": "complete", "publish_allowed": False},
                "metadata": {"review_workspace": {"available": False, "path": ""}},
            })
            manifest = write_json(session / "context" / "review_manifest.json", {
                "review_tasks": [{"task_id": "t1", "agent_id": "reviewer-1", "scope_file_paths": files}],
                "coverage": {"routed_files": files, "unsupported_files": []},
            })
            review_core.init_run(argparse.Namespace(
                session_dir=str(session), context=str(context), manifest=str(manifest),
                registry=str(ROOT / "references" / "rule-registry.md"), run_id="zero-run",
                budget_minutes=30, require_adversary=False, require_synthesizer=False,
            ))

            def capture(assignment, sender, wrapper):
                review_core.bind_agent(argparse.Namespace(
                    session_dir=str(session), assignment_id=assignment, sender_handle=sender, agent_id=wrapper["agent_id"]
                ))
                source = write_json(root / f"{assignment.replace(':', '_')}.json", wrapper)
                return review_core.capture_response(argparse.Namespace(
                    session_dir=str(session), assignment_id=assignment, sender_handle=sender, response=str(source)
                ))

            capture("review:t1", "agent/reviewer", {
                "schema_version": 1, "role": "reviewer", "agent_id": "reviewer-1",
                "task_id": "t1", "revision": "fixed", "findings": [],
            })
            review_admission.admit_manifest_mode(str(context), str(manifest), preflight=True)
            review_admission.admit_manifest_mode(str(context), str(manifest), no_adversary=True)
            write_json(session / "submission" / "review_store.json", [])
            write_json(session / "submission" / "defect-proofs.json", [])
            capture("synthesizer", "agent/synth", {
                "schema_version": 1, "role": "synthesizer", "agent_id": "synthesizer",
                "task_id": "synthesizer", "revision": "fixed", "output": [],
            })
            missing = review_core.verify_integrity(session, phase="final")
            capture("zero-finding-second-pass", "agent/zero", {
                "schema_version": 1, "role": "zero-finding-second-pass", "agent_id": "zero-finding-second-pass",
                "task_id": "zero-finding-second-pass", "revision": "fixed", "findings": [],
            })
            complete = review_core.verify_integrity(session, phase="final")
        self.assertEqual(missing["public_state"], "partial")
        self.assertEqual(complete["public_state"], "complete")
        self.assertFalse(complete["publish_allowed"])


class OutputAndLocalTests(unittest.TestCase):
    def test_dry_run_payload_exact_right_side_and_recovery(self):
        records = [{"file_path": "a.py", "line": 4, "comment": "bad", "fix_suggestion": "fix"}]
        payload, marker, skipped = submit_reviews.build_review_payload(records, {"comments": []}, "head", "COMMENT")
        self.assertEqual(payload["commit_id"], "head")
        self.assertEqual(payload["comments"][0]["side"], "RIGHT")
        self.assertEqual(skipped, 0)
        with mock.patch.object(submit_reviews, "request_json", side_effect=github_api.GitHubTransportError("timeout")), \
             mock.patch.object(submit_reviews, "get_existing_review_data", return_value={
                 "reviews": [{"id": 9, "state": "COMMENTED", "body": f"<!-- code-review-new:{marker} -->"}],
                 "comments": [],
             }):
            receipt, recovered = submit_reviews.submit_review_with_recovery(
                {}, {"owner": "o", "repo": "r", "number": 1}, payload, marker
            )
        self.assertTrue(recovered)
        self.assertEqual(receipt["id"], 9)

    def test_stale_head_blocks_apply(self):
        with mock.patch.object(submit_reviews, "get_pull", return_value={
            "head": {"sha": "new"}, "state": "open", "merged": False,
        }):
            with self.assertRaisesRegex(ValueError, "stale head SHA"):
                submit_reviews._fresh_pull({}, {"owner": "o", "repo": "r", "number": 1}, {"head_sha": "old"})

    def test_merge_timeout_recovers_without_retry(self):
        with mock.patch.object(submit_reviews, "request_json", side_effect=github_api.GitHubTransportError("timeout")) as request, \
             mock.patch.object(submit_reviews, "get_pull", return_value={"merged": True, "head": {"sha": "fixed"}}):
            receipt, recovered = submit_reviews.merge_with_recovery(
                {}, {"owner": "o", "repo": "r", "number": 1}, {"sha": "fixed"}, "fixed"
            )
        self.assertTrue(recovered)
        self.assertTrue(receipt["merged"])
        request.assert_called_once()

    def test_local_rename_delete_and_binary_records(self):
        diff = """diff --git a/old.py b/new.py
similarity index 100%
rename from old.py
rename to new.py
diff --git a/gone.py b/gone.py
deleted file mode 100644
--- a/gone.py
+++ /dev/null
@@ -1 +0,0 @@
-gone
diff --git a/image.png b/image.png
index 1..2 100644
Binary files a/image.png and b/image.png differ
"""
        records = local_context.format_diff_with_anchors(diff)
        by_path = {record["file_path"]: record for record in records}
        self.assertEqual(by_path["new.py"]["status"], "renamed")
        self.assertEqual(by_path["new.py"]["old_path"], "old.py")
        self.assertEqual(by_path["gone.py"]["status"], "removed")
        self.assertIsNone(by_path["gone.py"]["new_path"])
        self.assertTrue(by_path["image.png"]["patch_missing"])

    def test_local_git_staged_and_range_context(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            (repo / "app.py").write_text("x = 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "app.py"], cwd=repo, check=True)
            subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-qm", "base"], cwd=repo, check=True)
            base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            (repo / "app.py").write_text("x = 1\ny = 2\n", encoding="utf-8")
            subprocess.run(["git", "add", "app.py"], cwd=repo, check=True)
            staged = subprocess.run(
                [sys.executable, str(SCRIPTS / "local_context.py")], cwd=repo, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
            )
            staged_result = json.loads(staged.stdout)
            staged_context = json.loads(Path(staged_result["context_file"]).read_text(encoding="utf-8"))
            self.assertEqual(staged_context["metadata"]["review_mode"], "staged")
            self.assertTrue(staged_context["snapshot"]["diff_sha256"])
            subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-qm", "head"], cwd=repo, check=True)
            head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            ranged = subprocess.run(
                [sys.executable, str(SCRIPTS / "local_context.py"), "--range", f"{base}..{head}"], cwd=repo,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
            )
            ranged_result = json.loads(ranged.stdout)
            ranged_context = json.loads(Path(ranged_result["context_file"]).read_text(encoding="utf-8"))
        self.assertEqual(ranged_context["snapshot"]["base_sha"], base)
        self.assertEqual(ranged_context["snapshot"]["head_sha"], head)

    def test_local_whole_repo_snapshot_filters_and_freezes_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            (repo / "vendor").mkdir()
            (repo / "app.py").write_text("value = 1\n", encoding="utf-8")
            (repo / "README.md").write_text("# docs\n", encoding="utf-8")
            (repo / "vendor" / "lib.py").write_text("vendored = True\n", encoding="utf-8")
            (repo / "large.txt").write_text("x" * 100, encoding="utf-8")
            (repo / "binary.bin").write_bytes(b"a\0b")
            subprocess.run(["git", "add", "app.py", "README.md", "vendor/lib.py", "large.txt", "binary.bin"], cwd=repo, check=True)
            subprocess.run([
                "git", "-c", "user.name=Test", "-c", "user.email=test@example.com",
                "commit", "-qm", "base",
            ], cwd=repo, check=True)
            head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            (repo / "app.py").write_text("value = 1\nvalue += 1\n", encoding="utf-8")
            config_dir = repo / ".code-review-new"
            config_dir.mkdir()
            write_json(config_dir / "config.json", {
                "exclude_file_suffix": ".md",
                "whole_repo": {"max_file_bytes": 64, "exclude_globs": ["vendor/**"]},
            })

            completed = subprocess.run(
                [sys.executable, str(SCRIPTS / "local_context.py"), "--whole-repo"], cwd=repo,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
            )
            result = json.loads(completed.stdout)
            context = json.loads(Path(result["context_file"]).read_text(encoding="utf-8"))
            diffs = json.loads(Path(context["diff_file"]).read_text(encoding="utf-8"))
            repository_manifest = json.loads(Path(context["repository_manifest_file"]).read_text(encoding="utf-8"))

            self.assertEqual(context["metadata"]["review_mode"], "whole_repo")
            self.assertEqual(context["metadata"]["baseline"], "tracked-working-tree")
            self.assertEqual(context["changed_files"], ["app.py"])
            self.assertEqual(context["snapshot"]["head_sha"], head)
            self.assertEqual(context["snapshot"]["repository_sha256"], repository_manifest["repository_sha256"])
            self.assertFalse(context["integrity"]["publish_allowed"])
            self.assertEqual(diffs[0]["status"], "snapshot")
            self.assertIn("[N2]value += 1", diffs[0]["content"])
            scan = prescan.run(Path(result["context_file"]))
            self.assertEqual(scan["files"][0]["always_check"]["hardcoded-credentials"], "checked-no-signal")
            excluded = {item["path"]: item["reason"] for item in repository_manifest["excluded_files"]}
            self.assertEqual(excluded, {
                "README.md": "excluded_suffix",
                "binary.bin": "binary",
                "large.txt": "too_large",
                "vendor/lib.py": "excluded_glob",
            })
            self.assertEqual(repository_manifest["policy"]["max_file_bytes"], 64)
            report = render_report.render_report(context, [], {})
            self.assertIn("| 纳入文件 | 1 个 |", report)
            self.assertIn("| 排除文件 | 4 个 |", report)

            session = Path(result["review_session"]["path"])
            manifest = write_json(session / "context" / "review_manifest.json", {
                "review_tasks": [{"task_id": "whole", "scope_file_paths": ["app.py"]}],
                "coverage": {"routed_files": ["app.py"], "unsupported_files": []},
            })
            estimate = token_estimator.estimate(
                Path(result["context_file"]), None, manifest, budget_limit=1, task_budget=1,
                marginal_ratio=.8, bytes_per_token=3, max_rule_fraction=.3,
            )
            self.assertTrue(any("do not silently drop files" in item for item in estimate["suggestions"]))
            run = review_core.init_run(argparse.Namespace(
                session_dir=str(session), context=result["context_file"], manifest=str(manifest),
                registry=str(ROOT / "references" / "rule-registry.md"), run_id="whole-run",
                budget_minutes=30, require_adversary=False, require_synthesizer=False,
            ))
            self.assertEqual(run["revision"], context["snapshot"]["repository_sha256"])
            Path(context["repository_manifest_file"]).write_text("{}", encoding="utf-8")
            with self.assertRaises(review_core.IntegrityError):
                review_core.verify_root(review_core.session_paths(session))


if __name__ == "__main__":
    unittest.main(verbosity=2)
