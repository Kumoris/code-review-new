#!/usr/bin/env python3
"""Verify portable evidence bytes and original receipts without rewriting paths."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main():
    checksums = read(ROOT / "checksums.json")
    for relative, expected in checksums.items():
        path = (ROOT / relative).resolve()
        assert ROOT in path.parents, "Package path must stay inside its root"
        assert digest(path) == expected, f"Hash mismatch: {relative}"
    paths = read(ROOT / "artifact-map.json")

    def relocated(original):
        path = (ROOT / paths[original]).resolve()
        assert ROOT in path.parents
        return path

    run = read(ROOT / "audit/run.json")
    for stem in ("context", "manifest", "registry", "diff", "repository_manifest"):
        assert digest(relocated(run[stem + "_path"])) == run[stem + "_hash"]
    assert digest(ROOT / "audit/integrity/dispatch-ledger.json") == run["ledger_hash"]
    ledger = read(ROOT / "audit/integrity/dispatch-ledger.json")
    bindings = read(ROOT / "audit/integrity/dispatch-bindings.json")["bindings"]
    assert len({item["sender_handle"] for item in bindings}) == len(bindings)
    chain = read(ROOT / "audit/integrity/receipt-chain.json")["receipts"]
    prior, wrappers = None, {}
    for sequence, entry in enumerate(chain, 1):
        receipt = read(relocated(entry["receipt_path"]))
        unsigned = dict(receipt)
        stated = unsigned.pop("receipt_hash")
        assert hashlib.sha256(canonical(unsigned)).hexdigest() == stated == entry["receipt_hash"]
        assert receipt["sequence"] == sequence
        assert receipt["previous_receipt_hash"] == prior
        raw = relocated(receipt["raw_wrapper_path"])
        assert digest(raw) == receipt["response_hash"]
        wrapper = read(raw)
        assignment = next(a for a in ledger["assignments"] if a["assignment_id"] == receipt["assignment_id"])
        binding = next(b for b in bindings if b["assignment_id"] == receipt["assignment_id"])
        assert binding["sender_handle"] == receipt["sender_handle"]
        assert wrapper["agent_id"] == assignment["agent_id"]
        assert wrapper["role"] == assignment["role"]
        assert wrapper.get("task_id", wrapper.get("cluster_id")) == assignment["task_id"]
        assert wrapper["revision"] == run["revision"]
        wrappers[wrapper["role"]] = wrapper
        prior = stated
    assert {"reviewer", "adversary", "synthesizer"} <= wrappers.keys()
    records = read(ROOT / "audit/submission/review_store.json")
    assert wrappers["synthesizer"]["output"] == records
    assert len(records) == 1
    integrity = read(ROOT / "audit/submission/review-integrity.json")
    assert integrity["state"] == "complete" and integrity["publish_allowed"] is False
    versions = read(ROOT / "versions.json")
    assert digest(ROOT / "versions/observed/local_context.py") == versions["source_sha256"]
    assert digest(ROOT / "versions/proposed/local_context.py") == versions["proposed_sha256"]
    context = read(relocated(run["context_path"]))
    manifest = read(relocated(run["manifest_path"]))
    changed = set(context["changed_files"])
    routed = set(manifest["coverage"]["routed_files"])
    unsupported = set(manifest["coverage"]["unsupported_files"])
    assert not routed & unsupported and routed | unsupported == changed
    assert {p for task in manifest["review_tasks"] for p in task["scope_file_paths"]} == routed
    repository = read(relocated(run["repository_manifest_path"]))
    assert hashlib.sha256(canonical(repository["included_files"])).hexdigest() == run["revision"]
    assert repository["included_files"][0]["sha256"] == versions["source_sha256"]
    proofs = read(ROOT / "audit/submission/defect-proofs.json")
    proofs = proofs.get("proofs", []) if isinstance(proofs, dict) else proofs
    proof_ids = {p.get("source_id") or p.get("finding_id") or p.get("id") for p in proofs}
    assert all(set(record["source_ids"]) & proof_ids for record in records)
    print(json.dumps({"verified_files": len(checksums), "verified_receipts": len(chain),
                      "publication": "report_only", "hashes_valid": True}))


if __name__ == "__main__":
    main()
