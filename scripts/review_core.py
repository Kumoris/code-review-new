#!/usr/bin/env python3
"""Small, stdlib-only dispatch and integrity controller for review Agents."""

from __future__ import annotations

import argparse
import fcntl
import fnmatch
import hashlib
import json
import os
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path


SCHEMA_VERSION = 1
DEFAULT_BUDGET_MINUTES = 30
RULE_ID_RE = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b")
VALID_RULE_STATES = {"active", "review-required", "disabled", "report_only"}
BLOCKING_FLAGS = {
    "identity-spoof",
    "integrity-artifact-mismatch",
    "scope-drift",
    "stale-revision",
    "invalid-wrapper",
}


class IntegrityError(RuntimeError):
    """A fail-closed integrity contract violation."""

    def __init__(self, flag: str, message: str):
        super().__init__(message)
        self.flag = flag


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def load_json(path: str | Path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def canonical_bytes(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: str | Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def atomic_json(path: str | Path, value) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, target)


def immutable_bytes(path: str | Path, value: bytes) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        if target.read_bytes() != value:
            raise IntegrityError("integrity-artifact-mismatch", f"immutable artifact differs: {target}")
        return
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(value)


def session_paths(session_dir: str | Path) -> dict[str, Path]:
    root = Path(session_dir).resolve()
    return {
        "root": root,
        "run": root / "run.json",
        "ledger": root / "integrity" / "dispatch-ledger.json",
        "bindings": root / "integrity" / "dispatch-bindings.json",
        "receipts": root / "integrity" / "receipts",
        "chain": root / "integrity" / "receipt-chain.json",
        "lock": root / "integrity" / ".receipt.lock",
        "raw": root / "inbox" / "raw",
        "admission": root / "admission" / "reviewers",
        "integrity": root / "submission" / "review-integrity.json",
    }


def derive_revision(context: dict):
    snapshot = context.get("snapshot") or {}
    if isinstance(snapshot, dict):
        for key in ("repository_sha256", "head_sha", "head", "source_sha", "diff_sha256"):
            if snapshot.get(key):
                return snapshot[key]
    for key in ("head_sha", "source_sha", "revision"):
        if context.get(key):
            return context[key]
    if snapshot:
        return snapshot
    raise IntegrityError("unverified-critical-step", "context has no fixed revision")


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def manifest_coverage(context: dict, manifest: dict) -> list[dict]:
    changed = set(context.get("changed_files", []))
    tasks = manifest.get("review_tasks", [])
    routed_from_tasks = {path for task in tasks for path in task.get("scope_file_paths", [])}
    coverage = manifest.get("coverage")
    errors = []
    if not isinstance(coverage, dict):
        return [{"flag": "scope-drift", "message": "manifest.coverage is required"}]
    routed = set(coverage.get("routed_files", []))
    unsupported = set(coverage.get("unsupported_files", []))
    if routed & unsupported:
        errors.append({"flag": "scope-drift", "message": "routed_files and unsupported_files overlap"})
    if routed | unsupported != changed:
        errors.append({"flag": "scope-drift", "message": "coverage does not exactly match changed_files"})
    if routed_from_tasks != routed:
        errors.append({"flag": "scope-drift", "message": "task scope union does not match routed_files"})
    if len(tasks) > 8:
        errors.append({"flag": "scope-drift", "message": "manifest exceeds the 8-task limit"})
    return errors


def extract_rule_ids(value: str) -> list[str]:
    return list(dict.fromkeys(RULE_ID_RE.findall(str(value))))


def load_rule_registry(path: str | Path) -> dict[str, str]:
    target = Path(path)
    if not target.exists():
        raise IntegrityError("unverified-critical-step", f"rule registry missing: {target}")
    if target.suffix.lower() == ".json":
        data = load_json(target)
        data = data.get("rules", data) if isinstance(data, dict) else {}
        registry = {
            str(rule): (entry.get("status") if isinstance(entry, dict) else str(entry))
            for rule, entry in data.items()
        }
    else:
        registry = {}
        for line in target.read_text(encoding="utf-8").splitlines():
            if not line.lstrip().startswith("|"):
                continue
            cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
            if len(cells) >= 2 and cells[1] in VALID_RULE_STATES:
                registry[cells[0]] = cells[1]
    invalid = {key: value for key, value in registry.items() if value not in VALID_RULE_STATES}
    if invalid or not registry:
        raise IntegrityError("unverified-critical-step", "rule registry is empty or has invalid states")
    return registry


def registry_status(rule_id: str, registry: dict[str, str]) -> str | None:
    if rule_id in registry:
        return registry[rule_id]
    matches = [(pattern, state) for pattern, state in registry.items() if fnmatch.fnmatchcase(rule_id, pattern)]
    if not matches:
        return None
    return max(matches, key=lambda item: len(item[0].replace("*", "")))[1]


def output_field(wrapper: dict, role: str) -> tuple[str, list]:
    candidates = {
        "reviewer": ("output", "findings"),
        "deep-reviewer": ("output", "findings"),
        "adversary": ("output", "challenges"),
        "synthesizer": ("output", "review_comments", "records"),
        "zero-finding-second-pass": ("output", "findings", "verification"),
    }.get(role, ("output",))
    for key in candidates:
        if key in wrapper:
            value = wrapper[key]
            if not isinstance(value, list):
                raise IntegrityError("invalid-wrapper", f"wrapper.{key} must be an array")
            return key, value
    raise IntegrityError("invalid-wrapper", f"wrapper has no output field for role {role}")


def find_assignment(ledger: dict, assignment_id: str) -> dict:
    for assignment in ledger.get("assignments", []):
        if assignment.get("assignment_id") == assignment_id:
            return assignment
    raise IntegrityError("unverified-critical-step", f"unknown assignment: {assignment_id}")


def find_binding(bindings: dict, assignment_id: str) -> dict | None:
    return next((item for item in bindings.get("bindings", []) if item.get("assignment_id") == assignment_id), None)


def validate_wrapper(wrapper: dict, assignment: dict, run: dict) -> str:
    if not isinstance(wrapper, dict) or wrapper.get("schema_version") != SCHEMA_VERSION:
        raise IntegrityError("invalid-wrapper", "wrapper schema_version must be 1")
    if wrapper.get("agent_id") != assignment.get("agent_id"):
        raise IntegrityError("identity-spoof", "wrapper agent_id does not match dispatch ledger")
    if wrapper.get("role") != assignment.get("role"):
        raise IntegrityError("identity-spoof", "wrapper role does not match dispatch ledger")
    expected_task = assignment.get("task_id") or assignment.get("cluster_id")
    supplied = [wrapper[key] for key in ("cluster_id", "task_id") if key in wrapper]
    if not supplied or any(value != expected_task for value in supplied):
        raise IntegrityError("identity-spoof", "wrapper cluster_id/task_id does not match assignment")
    if wrapper.get("revision") != run.get("revision"):
        raise IntegrityError("stale-revision", "wrapper revision does not match fixed run revision")
    field, _ = output_field(wrapper, assignment["role"])
    return field


def init_run(args) -> dict:
    paths = session_paths(args.session_dir)
    if not 1 <= args.budget_minutes <= DEFAULT_BUDGET_MINUTES:
        raise IntegrityError("unverified-critical-step", "--budget-minutes must be between 1 and 30")
    if paths["run"].exists() or paths["ledger"].exists():
        raise IntegrityError("integrity-artifact-mismatch", "run already initialized")
    context_path = Path(args.context).resolve()
    manifest_path = Path(args.manifest).resolve()
    registry_path = Path(args.registry).resolve()
    context, manifest = load_json(context_path), load_json(manifest_path)
    coverage_errors = manifest_coverage(context, manifest)
    if coverage_errors:
        raise IntegrityError(coverage_errors[0]["flag"], coverage_errors[0]["message"])
    revision = derive_revision(context)
    diff_path = Path(context.get("diff_file", "")).resolve()
    if not diff_path.exists():
        raise IntegrityError("unverified-critical-step", "context.diff_file is missing")
    repository_manifest_path = None
    if context.get("repository_manifest_file"):
        repository_manifest_path = Path(context["repository_manifest_file"]).resolve()
        if not repository_manifest_path.exists():
            raise IntegrityError("unverified-critical-step", "context.repository_manifest_file is missing")
    created = utc_now()
    assignments = []
    seen = set()
    for index, task in enumerate(manifest.get("review_tasks", []), 1):
        task_id = str(task.get("task_id", "")).strip()
        if not task_id or task_id in seen:
            raise IntegrityError("scope-drift", "review task_id values must be non-empty and unique")
        seen.add(task_id)
        assignments.append({
            "assignment_id": f"review:{task_id}",
            "agent_id": task.get("agent_id") or f"reviewer-{index}",
            "role": "reviewer",
            "task_id": task_id,
            "cluster_id": task_id,
            "input_path": str(manifest_path),
            "declared_output_path": task.get("output_path", ""),
            "required": True,
        })
    reserved = (
        ("adversary", args.require_adversary),
        ("synthesizer", args.require_synthesizer),
        ("zero-finding-second-pass", False),
    )
    for role, required in reserved:
        assignments.append({
            "assignment_id": role,
            "agent_id": role,
            "role": role,
            "task_id": role,
            "cluster_id": role,
            "input_path": str(manifest_path),
            "required": required,
        })
    ledger = {
        "schema_version": SCHEMA_VERSION,
        "run_id": args.run_id or str(uuid.uuid4()),
        "revision": revision,
        "max_concurrent_reviewers": 5,
        "assignments": assignments,
    }
    for directory in (paths["receipts"], paths["raw"], paths["admission"], paths["integrity"].parent):
        directory.mkdir(parents=True, exist_ok=True)
    immutable_bytes(paths["ledger"], json.dumps(ledger, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
    atomic_json(paths["bindings"], {"schema_version": SCHEMA_VERSION, "bindings": []})
    atomic_json(paths["chain"], {"schema_version": SCHEMA_VERSION, "receipts": []})
    run = {
        "schema_version": SCHEMA_VERSION,
        "run_id": ledger["run_id"],
        "created_at": iso_time(created),
        "deadline_at": iso_time(created + timedelta(minutes=args.budget_minutes)),
        "revision": revision,
        "context_path": str(context_path),
        "manifest_path": str(manifest_path),
        "registry_path": str(registry_path),
        "diff_path": str(diff_path),
        "context_hash": sha256_file(context_path),
        "manifest_hash": sha256_file(manifest_path),
        "registry_hash": sha256_file(registry_path),
        "diff_hash": sha256_file(diff_path),
        "ledger_hash": sha256_file(paths["ledger"]),
        "state": "partial",
        "public_state": "partial",
        "publish_allowed": False,
        "publication_mode": "blocked",
    }
    if repository_manifest_path:
        run["repository_manifest_path"] = str(repository_manifest_path)
        run["repository_manifest_hash"] = sha256_file(repository_manifest_path)
    immutable_bytes(paths["run"], json.dumps(run, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
    return run


def verify_root(paths: dict[str, Path]) -> tuple[dict, dict]:
    if not paths["run"].exists() or not paths["ledger"].exists():
        raise IntegrityError("unverified-critical-step", "run.json or dispatch-ledger.json missing")
    run, ledger = load_json(paths["run"]), load_json(paths["ledger"])
    fixed_artifacts = [
        ("context_hash", "context_path"),
        ("manifest_hash", "manifest_path"),
        ("registry_hash", "registry_path"),
        ("diff_hash", "diff_path"),
    ]
    if run.get("repository_manifest_path"):
        fixed_artifacts.append(("repository_manifest_hash", "repository_manifest_path"))
    for key, path_key in fixed_artifacts:
        target = Path(run.get(path_key, ""))
        if not target.exists() or sha256_file(target) != run.get(key):
            raise IntegrityError("integrity-artifact-mismatch", f"{path_key} hash mismatch")
    if sha256_file(paths["ledger"]) != run.get("ledger_hash"):
        raise IntegrityError("integrity-artifact-mismatch", "dispatch ledger hash mismatch")
    if ledger.get("run_id") != run.get("run_id") or ledger.get("revision") != run.get("revision"):
        raise IntegrityError("integrity-artifact-mismatch", "run and ledger identity differ")
    return run, ledger


def bind_agent(args) -> dict:
    paths = session_paths(args.session_dir)
    run, ledger = verify_root(paths)
    if utc_now() > parse_time(run["deadline_at"]):
        raise IntegrityError("deadline-exceeded", "30-minute dispatch deadline has passed")
    assignment = find_assignment(ledger, args.assignment_id)
    if args.agent_id and args.agent_id != assignment["agent_id"]:
        raise IntegrityError("identity-spoof", "logical agent_id does not match ledger")
    bindings = load_json(paths["bindings"])
    existing = find_binding(bindings, args.assignment_id)
    candidate = {
        "assignment_id": args.assignment_id,
        "agent_id": assignment["agent_id"],
        "sender_handle": args.sender_handle,
        "bound_at": iso_time(utc_now()),
    }
    if existing:
        if existing["agent_id"] != candidate["agent_id"] or existing["sender_handle"] != candidate["sender_handle"]:
            raise IntegrityError("identity-spoof", "assignment already has a different binding")
        return existing
    if any(item.get("sender_handle") == args.sender_handle for item in bindings.get("bindings", [])):
        raise IntegrityError("identity-spoof", "sender_handle is already bound to another assignment")
    bindings.setdefault("bindings", []).append(candidate)
    atomic_json(paths["bindings"], bindings)
    return candidate


def capture_response(args) -> dict:
    paths = session_paths(args.session_dir)
    run, ledger = verify_root(paths)
    assignment = find_assignment(ledger, args.assignment_id)
    bindings = load_json(paths["bindings"])
    binding = find_binding(bindings, args.assignment_id)
    if not binding:
        raise IntegrityError("unverified-critical-step", "assignment has no sender binding")
    if binding.get("sender_handle") != args.sender_handle:
        raise IntegrityError("identity-spoof", "capture sender_handle does not match binding")
    response_bytes = Path(args.response).read_bytes()
    try:
        wrapper = json.loads(response_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise IntegrityError("invalid-wrapper", f"response is not valid UTF-8 JSON: {error}") from error
    field = validate_wrapper(wrapper, assignment, run)
    response_hash = sha256_bytes(response_bytes)
    raw_path = paths["raw"] / f"{safe_name(args.assignment_id)}.json"
    receipt_path = paths["receipts"] / f"{safe_name(args.assignment_id)}.json"
    paths["lock"].parent.mkdir(parents=True, exist_ok=True)
    with paths["lock"].open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        if receipt_path.exists():
            receipt = load_json(receipt_path)
            if receipt.get("response_hash") != response_hash or receipt.get("sender_handle") != args.sender_handle:
                raise IntegrityError("integrity-artifact-mismatch", "assignment already captured with different content")
            return receipt
        immutable_bytes(raw_path, response_bytes)
        chain = load_json(paths["chain"])
        prior = chain.get("receipts", [])[-1]["receipt_hash"] if chain.get("receipts") else None
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "run_id": run["run_id"],
            "sequence": len(chain.get("receipts", [])) + 1,
            "assignment_id": args.assignment_id,
            "agent_id": assignment["agent_id"],
            "role": assignment["role"],
            "task_id": assignment["task_id"],
            "sender_handle": args.sender_handle,
            "input_path": str(Path(args.response).resolve()),
            "raw_wrapper_path": str(raw_path),
            "response_hash": response_hash,
            "output_field": field,
            "previous_receipt_hash": prior,
            "captured_at": iso_time(utc_now()),
            "publication_eligibility": (
                "report_only" if utc_now() > parse_time(run["deadline_at"]) else "eligible"
            ),
        }
        receipt["receipt_hash"] = sha256_bytes(canonical_bytes(receipt))
        immutable_bytes(receipt_path, json.dumps(receipt, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
        chain.setdefault("receipts", []).append({
            "sequence": receipt["sequence"],
            "assignment_id": args.assignment_id,
            "receipt_path": str(receipt_path),
            "receipt_hash": receipt["receipt_hash"],
        })
        atomic_json(paths["chain"], chain)
    return receipt


def _error(errors: list, flag: str, message: str) -> None:
    errors.append({"flag": flag, "message": message})


def verify_integrity(session_dir: str | Path, check_zero: bool = True, phase: str = "final") -> dict:
    paths = session_paths(session_dir)
    errors, warnings = [], []
    try:
        run, ledger = verify_root(paths)
    except IntegrityError as error:
        run, ledger = {}, {"assignments": []}
        _error(errors, error.flag, str(error))
    context = manifest = {}
    if run:
        try:
            context, manifest = load_json(run["context_path"]), load_json(run["manifest_path"])
            errors.extend(manifest_coverage(context, manifest))
        except (OSError, json.JSONDecodeError, KeyError) as error:
            _error(errors, "integrity-artifact-mismatch", f"cannot read fixed context/manifest: {error}")
    try:
        bindings = load_json(paths["bindings"])
    except (OSError, json.JSONDecodeError):
        bindings = {"bindings": []}
        _error(errors, "unverified-critical-step", "dispatch-bindings.json missing or invalid")
    sender_handles = [item.get("sender_handle") for item in bindings.get("bindings", [])]
    if len(sender_handles) != len(set(sender_handles)):
        _error(errors, "identity-spoof", "sender_handle is bound more than once")
    try:
        chain = load_json(paths["chain"])
    except (OSError, json.JSONDecodeError):
        chain = {"receipts": []}
        _error(errors, "unverified-critical-step", "receipt-chain.json missing or invalid")
    assignments = {item.get("assignment_id"): item for item in ledger.get("assignments", [])}
    captured = {}
    prior = None
    for expected_sequence, entry in enumerate(chain.get("receipts", []), 1):
        try:
            receipt = load_json(entry["receipt_path"])
            unsigned = dict(receipt)
            stated_hash = unsigned.pop("receipt_hash", None)
            if sha256_bytes(canonical_bytes(unsigned)) != stated_hash or entry.get("receipt_hash") != stated_hash:
                raise IntegrityError("integrity-artifact-mismatch", "receipt hash mismatch")
            if receipt.get("sequence") != expected_sequence or receipt.get("previous_receipt_hash") != prior:
                raise IntegrityError("integrity-artifact-mismatch", "receipt chain order mismatch")
            assignment = assignments.get(receipt.get("assignment_id"))
            binding = find_binding(bindings, receipt.get("assignment_id"))
            if not assignment or not binding:
                raise IntegrityError("unverified-critical-step", "receipt has no assignment/binding")
            if binding.get("sender_handle") != receipt.get("sender_handle"):
                raise IntegrityError("identity-spoof", "receipt sender_handle differs from binding")
            raw_path = Path(receipt["raw_wrapper_path"])
            if not raw_path.exists() or sha256_file(raw_path) != receipt.get("response_hash"):
                raise IntegrityError("integrity-artifact-mismatch", "raw wrapper hash mismatch")
            wrapper = load_json(raw_path)
            validate_wrapper(wrapper, assignment, run)
            captured[receipt["assignment_id"]] = (receipt, wrapper)
            prior = stated_hash
        except (OSError, json.JSONDecodeError, KeyError, IntegrityError) as error:
            flag = error.flag if isinstance(error, IntegrityError) else "integrity-artifact-mismatch"
            _error(errors, flag, str(error))
    for assignment in assignments.values():
        binding = find_binding(bindings, assignment["assignment_id"])
        role = assignment.get("role")
        required_now = role == "reviewer"
        if phase in {"adversary", "final"} and role == "adversary" and assignment.get("required"):
            required_now = True
        if phase == "final" and role == "synthesizer":
            required_now = True
        if required_now and not binding:
            _error(errors, "unverified-critical-step", f"missing binding: {assignment['assignment_id']}")
        if required_now and assignment["assignment_id"] not in captured:
            _error(errors, "unverified-critical-step", f"missing receipt: {assignment['assignment_id']}")
    reviewer_ids = {
        assignment["agent_id"] for assignment in assignments.values() if assignment.get("role") == "reviewer"
    }
    for role in ("synthesizer", "zero-finding-second-pass"):
        if role in captured and captured[role][0].get("agent_id") in reviewer_ids:
            _error(errors, "identity-spoof", f"{role} must use an independent agent_id")
    reviewer_outputs = []
    for assignment_id, (receipt, wrapper) in captured.items():
        if receipt.get("role") == "reviewer":
            _, output = output_field(wrapper, "reviewer")
            reviewer_outputs.extend(output)
    retained_outputs = reviewer_outputs
    synthesizer_expected = phase == "final"
    if "synthesizer" in captured:
        _, retained_outputs = output_field(captured["synthesizer"][1], "synthesizer")
        synthesizer_expected = True
    if synthesizer_expected:
        review_store = paths["root"] / "submission" / "review_store.json"
        proof_file = paths["root"] / "submission" / "defect-proofs.json"
        try:
            stored_records = load_json(review_store)
            proofs = load_json(proof_file)
            proof_records = proofs.get("proofs", proofs.get("confirmed_findings", [])) if isinstance(proofs, dict) else proofs
            if not isinstance(stored_records, list) or not isinstance(proof_records, list):
                raise ValueError("synthesizer artifacts must contain arrays")
            if canonical_bytes(retained_outputs) != canonical_bytes(stored_records):
                raise ValueError("captured Synthesizer output differs from review_store.json")
            def artifact_ids(record):
                values = record.get("sources") or record.get("source_ids") or []
                if isinstance(values, str):
                    values = [values]
                direct = record.get("finding_id") or record.get("source_id") or record.get("id")
                admitted = record.get("_admission", {}).get("source_id")
                return {str(value) for value in [direct, admitted, *values] if value}
            proof_ids = {value for proof in proof_records for value in artifact_ids(proof)}
            for record in stored_records:
                record_ids = artifact_ids(record)
                if not record_ids or not record_ids & proof_ids:
                    raise ValueError("defect-proofs do not identify every retained record")
            retained_outputs = stored_records
        except (OSError, json.JSONDecodeError, ValueError) as error:
            _error(errors, "unverified-critical-step", f"missing/invalid Synthesizer output or defect proofs: {error}")
    if phase == "final" and check_zero and captured and not retained_outputs and len(context.get("changed_files", [])) >= 3:
        if "zero-finding-second-pass" not in captured:
            _error(errors, "unverified-critical-step", "independent zero-finding second-pass receipt required")
    if phase == "final" and "zero-finding-second-pass" in captured:
        _, zero_outputs = output_field(captured["zero-finding-second-pass"][1], "zero-finding-second-pass")
        if zero_outputs:
            _error(errors, "unverified-critical-step", "zero-finding second pass found issues; start a new admission/synthesis cycle")
    fallback_path = paths["root"] / "inbox" / "adversary_challenges.json"
    if phase == "final" and fallback_path.exists():
        try:
            if load_json(fallback_path).get("fallback"):
                _error(errors, "adversary-fallback", "Adversary fallback closes remote publication")
        except (AttributeError, OSError, json.JSONDecodeError):
            _error(errors, "unverified-critical-step", "Adversary artifact is invalid")
    context_integrity = context.get("integrity", {})
    if (
        context.get("partial")
        or context.get("metadata", {}).get("partial")
        or context_integrity.get("status") == "partial"
        or context_integrity.get("public_state") == "partial"
    ):
        _error(errors, "partial-context", "context is marked partial")
    deadline_exceeded = bool(run) and utc_now() > parse_time(run["deadline_at"])
    if deadline_exceeded:
        warnings.append({"flag": "deadline-exceeded", "message": "remote publication closed after 30 minutes"})
    flags = {item["flag"] for item in errors}
    state = "blocked" if flags & BLOCKING_FLAGS else ("partial" if errors else "complete")
    context_publish_allowed = context_integrity.get("publish_allowed") is not False
    publish_allowed = state == "complete" and not deadline_exceeded and context_publish_allowed
    result = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run.get("run_id"),
        "checked_at": iso_time(utc_now()),
        "phase": phase,
        "state": state,
        "public_state": state,
        "publish_allowed": publish_allowed,
        "publication_mode": "publish" if publish_allowed else "report_only",
        "errors": errors,
        "warnings": warnings,
        "assignments": {
            "declared": len(assignments),
            "captured": len(captured),
            "required": sum(bool(item.get("required")) for item in assignments.values()),
        },
    }
    atomic_json(paths["integrity"], result)
    return result


def command_verify(args) -> dict:
    return verify_integrity(args.session_dir, check_zero=not args.skip_zero_check, phase=args.phase)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review Agent dispatch and integrity controller")
    subparsers = parser.add_subparsers(dest="command", required=True)
    init = subparsers.add_parser("init-run", help="freeze run hashes and preallocate Agent assignments")
    init.add_argument("--session-dir", required=True)
    init.add_argument("--context", required=True)
    init.add_argument("--manifest", required=True)
    init.add_argument("--registry", default=str(Path(__file__).parent.parent / "references" / "rule-registry.md"))
    init.add_argument("--run-id")
    init.add_argument("--budget-minutes", type=int, default=DEFAULT_BUDGET_MINUTES)
    init.add_argument("--require-adversary", action="store_true")
    init.add_argument("--require-synthesizer", action="store_true")
    init.set_defaults(function=init_run)
    bind = subparsers.add_parser("bind-agent", help="bind one logical assignment to a trusted sender handle")
    bind.add_argument("--session-dir", required=True)
    bind.add_argument("--assignment-id", required=True)
    bind.add_argument("--sender-handle", required=True)
    bind.add_argument("--agent-id")
    bind.set_defaults(function=bind_agent)
    capture = subparsers.add_parser("capture-response", help="verify and immutably capture an Agent wrapper")
    capture.add_argument("--session-dir", required=True)
    capture.add_argument("--assignment-id", required=True)
    capture.add_argument("--sender-handle", required=True)
    capture.add_argument("--response", "--wrapper", dest="response", required=True)
    capture.set_defaults(function=capture_response)
    verify = subparsers.add_parser("verify-run", help="verify hashes, identities, coverage, and receipts")
    verify.add_argument("--session-dir", required=True)
    verify.add_argument("--phase", choices=("reviewers", "adversary", "final"), default="final")
    verify.add_argument("--skip-zero-check", action="store_true", help=argparse.SUPPRESS)
    verify.set_defaults(function=command_verify)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = args.function(args)
    except (IntegrityError, OSError, json.JSONDecodeError, KeyError, ValueError) as error:
        flag = error.flag if isinstance(error, IntegrityError) else "unverified-critical-step"
        print(json.dumps({"type": "ERROR", "flag": flag, "message": str(error)}, ensure_ascii=False))
        sys.exit(2)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.command == "verify-run" and result["state"] != "complete":
        sys.exit(2)


if __name__ == "__main__":
    main()
