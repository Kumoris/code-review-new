#!/usr/bin/env python3
"""Fail-closed admission gate; raw Agent wrappers are never rewritten."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from review_core import (
        IntegrityError,
        atomic_json,
        derive_revision,
        extract_rule_ids,
        find_assignment,
        load_json,
        load_rule_registry,
        manifest_coverage,
        output_field,
        registry_status,
        safe_name,
        session_paths,
        verify_integrity,
    )
    from ensure_adversary import build_fallback
except ModuleNotFoundError:  # Allows import as scripts.review_admission in tests.
    from scripts.review_core import (
        IntegrityError,
        atomic_json,
        derive_revision,
        extract_rule_ids,
        find_assignment,
        load_json,
        load_rule_registry,
        manifest_coverage,
        output_field,
        registry_status,
        safe_name,
        session_paths,
        verify_integrity,
    )
    from scripts.ensure_adversary import build_fallback


VALID_SEVERITIES = {"fatal", "major", "minor", "suggestion"}
VALID_VERDICTS = {"DEFINITE", "LIKELY", "PLAUSIBLE", "SPECULATIVE"}
SEVERITY_ORDER = ["suggestion", "minor", "major", "fatal"]
UNCERTAIN_RE = re.compile(
    r"可能|也许|或许|需要确认|无法确认|假设|未来|不确定|unknown|uncertain|\b(?:may|might|could)\b|if future|tbd",
    re.IGNORECASE,
)


def normalize_finding(finding: dict) -> dict:
    aliases = {
        "file_path": "file",
        "line_number": "line",
        "rule_id": "rules",
        "description": "impact",
        "suggestion": "fix",
        "body": "comment",
    }
    normalized = dict(finding)
    for alternative, canonical in aliases.items():
        if not normalized.get(canonical) and normalized.get(alternative):
            normalized[canonical] = normalized[alternative]
    return normalized


def parse_valid_n_lines(diffs_data: list) -> dict[str, set[int]]:
    valid_lines = {}
    for record in diffs_data:
        path = record.get("file_path") or record.get("new_path") or record.get("path", "")
        lines = set()
        content = record.get("content", [])
        if isinstance(content, str):
            content = content.splitlines()
        for line in content if isinstance(content, list) else []:
            match = re.match(r"^\[N(\d+)\]", str(line))
            if match:
                lines.add(int(match.group(1)))
        valid_lines[path] = lines
    return valid_lines


def cited_rule_ids(finding: dict) -> list[str]:
    ids = extract_rule_ids(finding.get("rules", ""))
    if not ids and str(finding.get("rules", "")).startswith("深度检视："):
        ids = ["DEEP-REVIEW"]
    return ids


def _answered(value) -> bool:
    return bool(str(value or "").strip()) and not UNCERTAIN_RE.search(str(value))


def defect_proof(finding: dict) -> tuple[dict, int, bool]:
    supplied = finding.get("defect_proof")
    explicit = isinstance(supplied, dict)
    if explicit:
        proof = {
            "trigger": supplied.get("trigger") or supplied.get("code_path") or supplied.get("condition"),
            "wrong_result": supplied.get("wrong_result") or supplied.get("actual_result") or supplied.get("impact"),
            "diff_rule_evidence": supplied.get("diff_rule_evidence") or supplied.get("proof") or supplied.get("evidence"),
        }
    else:
        proof = {
            "trigger": finding.get("evidence"),
            "wrong_result": finding.get("impact"),
            "diff_rule_evidence": f"[N{finding.get('line')}] {finding.get('rules', '')}" if finding.get("line") else "",
        }
    return proof, sum(_answered(value) for value in proof.values()), explicit


def validate_finding(
    finding: dict,
    scope_files: set,
    valid_lines: dict,
    workspace_path: str = "",
    allowed_rules: set | None = None,
    registry: dict[str, str] | None = None,
) -> tuple[bool, str]:
    finding = normalize_finding(finding)
    for field in ("id", "file", "line", "severity", "evidence", "impact", "fix"):
        if field not in finding or finding[field] in (None, ""):
            return False, f"Missing required field: {field}"
    rule_ids = cited_rule_ids(finding)
    if not rule_ids:
        return False, "Missing concrete rule ID"
    if allowed_rules and not set(rule_ids).issubset(allowed_rules):
        return False, f"Rule ID is not bound to {finding['file']}"
    if "confidence_score" not in finding:
        return False, "Missing confidence_score field"
    score = finding["confidence_score"]
    if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 10:
        return False, f"Invalid confidence_score: {score}"
    if finding["file"] not in scope_files:
        return False, f"File {finding['file']} not in scope"
    if finding["severity"] not in VALID_SEVERITIES:
        return False, f"Invalid severity: {finding['severity']}"
    if isinstance(finding["line"], bool) or not isinstance(finding["line"], int):
        return False, "Line must be an integer"
    if finding["line"] not in valid_lines.get(finding["file"], set()):
        return False, f"Line {finding['line']} is not an exact [N] anchor in {finding['file']}"
    if registry is not None:
        states = [registry_status(rule_id, registry) for rule_id in rule_ids]
        if any(state is None for state in states):
            return False, "Rule ID has no registry status"
        if "disabled" in states:
            return False, "Finding cites a disabled rule"
    deep = finding.get("deep_review")
    if deep:
        if not str(deep.get("call_chain_path", "")).strip():
            return False, "Deep review finding has empty call_chain_path"
        if deep.get("change_type") not in {"METHOD_MODIFY", "METHOD_REMOVE", "INTERFACE_CHANGE"}:
            return False, "Deep review change_type is not eligible"
        if deep.get("business_impact", {}).get("risk_level") not in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}:
            return False, "Deep review risk_level is invalid"
    return True, ""


def _task_allowed_rules(task: dict, file_path: str) -> set | None:
    by_file = task.get("rule_ids_by_file")
    if isinstance(by_file, dict) and file_path in by_file:
        return set(by_file[file_path])
    rules = task.get("rule_ids")
    return set(rules) if isinstance(rules, list) and rules else None


def _rule_state(rule_ids: list[str], registry: dict[str, str]) -> str:
    states = {registry_status(rule_id, registry) for rule_id in rule_ids}
    for state in ("disabled", "report_only", "review-required", "active"):
        if state in states:
            return state
    return "review-required"


def _downgrade(severity: str) -> str:
    return SEVERITY_ORDER[max(0, SEVERITY_ORDER.index(severity) - 1)]


def _challenge_map(data: dict | list) -> tuple[dict[str, dict], bool]:
    fallback = bool(data.get("fallback")) if isinstance(data, dict) else False
    if isinstance(data, dict) and data.get("role") == "adversary":
        values = data.get("output", data.get("challenges", []))
    elif isinstance(data, dict):
        values = data.get("challenges", data.get("results", data.get("verdicts", [])))
    else:
        values = data
    if not isinstance(values, list):
        raise IntegrityError("invalid-adversary", "Adversary results must contain an array")
    result = {}
    for challenge in values:
        finding_id = challenge.get("finding_id") or challenge.get("source_finding_id") or challenge.get("id")
        verdict = str(challenge.get("verdict", "")).upper()
        if not finding_id or verdict not in VALID_VERDICTS or finding_id in result:
            raise IntegrityError("invalid-adversary", "Adversary IDs must be unique and verdicts must use the four-tier enum")
        result[finding_id] = dict(challenge, verdict=verdict)
    return result, fallback


def _captured_outputs(session: Path, manifest: dict) -> tuple[dict[str, list], dict]:
    paths = session_paths(session)
    run, ledger = load_json(paths["run"]), load_json(paths["ledger"])
    chain = load_json(paths["chain"])
    receipts = {entry["assignment_id"]: load_json(entry["receipt_path"]) for entry in chain.get("receipts", [])}
    outputs = {}
    for task in manifest.get("review_tasks", []):
        task_id = task.get("task_id", "")
        assignment_id = f"review:{task_id}"
        assignment = find_assignment(ledger, assignment_id)
        receipt = receipts.get(assignment_id)
        if not receipt:
            raise IntegrityError("unverified-critical-step", f"missing Reviewer receipt: {assignment_id}")
        wrapper = load_json(receipt["raw_wrapper_path"])
        _, findings = output_field(wrapper, assignment["role"])
        outputs[task_id] = findings
    adversary = {}
    if "adversary" in receipts:
        receipt = receipts["adversary"]
        wrapper = load_json(receipt["raw_wrapper_path"])
        _, challenges = output_field(wrapper, "adversary")
        adversary = {
            "schema_version": 1,
            "revision": run["revision"],
            "fallback": False,
            "trusted_receipt": receipt["receipt_hash"],
            "challenges": challenges,
        }
    return outputs, adversary


def _load_diffs(context: dict) -> list:
    path = Path(context.get("diff_file", ""))
    if not path.exists():
        raise IntegrityError("unverified-critical-step", "fixed diff_file missing")
    data = load_json(path)
    if not isinstance(data, list):
        raise IntegrityError("unverified-critical-step", "diff_file root must be an array")
    return data


def _write_integrity(session: Path, base: dict, admission: dict) -> dict:
    result = dict(base)
    result["admission"] = admission
    if admission.get("blocked"):
        result["state"] = result["public_state"] = "blocked"
        result["publish_allowed"] = False
        result["publication_mode"] = "report_only"
    elif admission.get("fallback_adversary") or admission.get("untrusted_adversary"):
        if result.get("state") == "complete":
            result["state"] = result["public_state"] = "partial"
        result["publish_allowed"] = False
        result["publication_mode"] = "report_only"
    elif admission.get("stage") in {"preflight", "final-admission"}:
        result["state"] = result["public_state"] = "partial"
        result["publish_allowed"] = False
        result["publication_mode"] = "report_only"
    atomic_json(session_paths(session)["integrity"], result)
    return result


def admit_manifest_mode(
    context_path: str,
    manifest_path: str,
    adversary_results: str | None = None,
    registry_path: str | None = None,
    no_adversary: bool = False,
    preflight: bool = False,
) -> dict:
    context, manifest = load_json(context_path), load_json(manifest_path)
    session = Path(manifest_path).resolve().parent.parent
    coverage_errors = manifest_coverage(context, manifest)
    if coverage_errors:
        result = {"state": "blocked", "public_state": "blocked", "publish_allowed": False, "errors": coverage_errors}
        atomic_json(session_paths(session)["integrity"], result)
        raise IntegrityError("scope-drift", coverage_errors[0]["message"])
    # All captured receipts are verified here; requiring an absent Adversary
    # would make the publication-closing fallback unreachable.
    integrity = verify_integrity(session, check_zero=False, phase="reviewers")
    if integrity["state"] != "complete":
        raise IntegrityError("unverified-critical-step", "dispatch integrity is not complete")
    findings_by_task, captured_adversary = _captured_outputs(session, manifest)
    run = load_json(session_paths(session)["run"])
    registry = load_rule_registry(registry_path or run["registry_path"])
    trusted_adversary = False
    if preflight:
        adversary_data = {"fallback": False, "challenges": []}
        trusted_adversary = True
    elif no_adversary:
        adversary_data = {
            "fallback": False,
            "challenges": [
                {"finding_id": f"{task_id}:{finding.get('id', '')}", "verdict": "LIKELY", "rationale": "Adversary disabled by controller"}
                for task_id, findings in findings_by_task.items() for finding in findings
            ],
        }
        trusted_adversary = True
    elif captured_adversary:
        adversary_data = captured_adversary
        trusted_adversary = True
    elif adversary_results:
        adversary_data = load_json(adversary_results)
    else:
        adversary_data = build_fallback(context, findings_by_task, registry)
        atomic_json(session / "inbox" / "adversary_challenges.json", adversary_data)
    if isinstance(adversary_data, dict) and adversary_data.get("revision") not in (None, derive_revision(context)):
        raise IntegrityError("stale-revision", "Adversary revision differs from fixed context")
    challenges, fallback = _challenge_map(adversary_data)
    valid_lines = parse_valid_n_lines(_load_diffs(context))
    workspace = context.get("metadata", {}).get("review_workspace", {}).get("path", "")
    task_by_id = {task.get("task_id"): task for task in manifest.get("review_tasks", [])}
    results, total_accepted, total_rejected = [], 0, 0
    blocked = False
    for task_id, raw_findings in findings_by_task.items():
        task = task_by_id[task_id]
        accepted, rejected = [], []
        for raw in raw_findings:
            if not isinstance(raw, dict):
                rejected.append({"finding": raw, "reason": "finding must be an object"})
                continue
            finding = normalize_finding(raw)
            allowed = _task_allowed_rules(task, finding.get("file", ""))
            valid, reason = validate_finding(
                finding, set(task.get("scope_file_paths", [])), valid_lines, workspace, allowed, registry
            )
            if not valid:
                rejected.append({"finding_id": finding.get("id"), "reason": reason})
                continue
            source_id = f"{task_id}:{finding['id']}"
            rule_ids = cited_rule_ids(finding)
            rule_state = _rule_state(rule_ids, registry)
            if preflight:
                finding["_admission"] = {
                    "stage": "preliminary",
                    "source_id": source_id,
                    "rule_ids": rule_ids,
                    "rule_status": rule_state,
                    "publication_eligibility": "report_only",
                }
                accepted.append(finding)
                continue
            challenge = challenges.get(source_id) or challenges.get(finding["id"])
            if not challenge:
                rejected.append({"finding_id": finding["id"], "reason": "missing Adversary verdict"})
                blocked = blocked or not fallback
                continue
            if challenge["verdict"] == "SPECULATIVE":
                rejected.append({"finding_id": finding["id"], "reason": "Adversary verdict SPECULATIVE"})
                continue
            proof, answer_count, explicit = defect_proof(finding)
            score = finding["confidence_score"]
            if score < 4 or answer_count < 2:
                rejected.append({"finding_id": finding["id"], "reason": "Defect Proof threshold not met"})
                continue
            if rule_state == "review-required" and (not explicit or answer_count < 3):
                rejected.append({"finding_id": finding["id"], "reason": "review-required rule needs explicit 3/3 Defect Proof"})
                continue
            publication = "publish"
            if score < 7:
                finding["severity"] = "suggestion"
                publication = "report_only"
            if challenge["verdict"] == "PLAUSIBLE":
                finding["severity"] = _downgrade(finding["severity"])
            if rule_state == "report_only" or fallback or not trusted_adversary:
                publication = "report_only"
            finding["_admission"] = {
                "source_id": source_id,
                "rule_ids": rule_ids,
                "rule_status": rule_state,
                "adversary_verdict": challenge["verdict"],
                "defect_proof": proof,
                "answered_proof_questions": answer_count,
                "publication_eligibility": publication,
            }
            accepted.append(finding)
        accepted_path = session / "admission" / "reviewers" / f"{safe_name(task_id)}.json"
        rejected_path = session / "admission" / "rejections" / f"{safe_name(task_id)}.json"
        atomic_json(accepted_path, accepted)
        atomic_json(rejected_path, rejected)
        total_accepted += len(accepted)
        total_rejected += len(rejected)
        results.append({
            "task_id": task_id,
            "raw_output_unchanged": True,
            "admitted_path": str(accepted_path),
            "rejected_path": str(rejected_path),
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
        })
    final_integrity = integrity
    admission_summary = {
        "accepted_count": total_accepted,
        "rejected_count": total_rejected,
        "fallback_adversary": fallback,
        "untrusted_adversary": not trusted_adversary and not fallback,
        "blocked": blocked,
        "stage": "preflight" if preflight else "final-admission",
    }
    final_integrity = _write_integrity(session, final_integrity, admission_summary)
    return {
        "file_results": results,
        "integrity_state": final_integrity["state"],
        "public_state": final_integrity["public_state"],
        "publish_allowed": final_integrity["publish_allowed"],
        "publication_mode": final_integrity["publication_mode"],
        "fallback_adversary": fallback,
    }


def admit_review_store_mode(context_path: str, review_store_path: str) -> dict:
    context = load_json(context_path)
    valid_lines = parse_valid_n_lines(_load_diffs(context))
    changed = set(context.get("changed_files", []))
    records = load_json(review_store_path)
    if not isinstance(records, list):
        raise IntegrityError("invalid-wrapper", "review_store root must be an array")
    accepted, rejected = [], []
    for record in records:
        file_path, line = record.get("file_path", ""), record.get("line", 0)
        valid = (
            file_path in changed
            and isinstance(line, int)
            and not isinstance(line, bool)
            and line in valid_lines.get(file_path, set())
            and record.get("severity") in VALID_SEVERITIES
            and isinstance(record.get("confidence_score"), int)
            and not isinstance(record.get("confidence_score"), bool)
            and 0 <= record.get("confidence_score") <= 10
        )
        (accepted if valid else rejected).append(record)
    return {"accepted_records": len(accepted), "rejected_records": len(rejected)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Review admission gate")
    parser.add_argument("--context", required=True)
    parser.add_argument("--manifest")
    parser.add_argument("--review-store")
    parser.add_argument("--adversary-results")
    parser.add_argument("--registry")
    parser.add_argument("--no-adversary", action="store_true")
    parser.add_argument(
        "--preliminary",
        "--preflight",
        dest="preflight",
        action="store_true",
        help="admit Reviewer inputs before dispatching Adversary",
    )
    args = parser.parse_args()
    try:
        if args.manifest:
            result = admit_manifest_mode(
                args.context,
                args.manifest,
                args.adversary_results,
                args.registry,
                args.no_adversary,
                args.preflight,
            )
        elif args.review_store:
            result = admit_review_store_mode(args.context, args.review_store)
        else:
            parser.error("one of --manifest or --review-store is required")
    except (IntegrityError, OSError, json.JSONDecodeError, KeyError, ValueError) as error:
        flag = error.flag if isinstance(error, IntegrityError) else "unverified-critical-step"
        print(json.dumps({"type": "ERROR", "flag": flag, "message": str(error)}, ensure_ascii=False))
        sys.exit(2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
