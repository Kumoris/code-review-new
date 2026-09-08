"""Assert that a fixture contains no remotely submitted GitHub records."""

import json


def check(session_dir, **kwargs):
    receipt = session_dir / "submission" / "github_submission_receipt.json"
    if receipt.exists():
        return {"passed": False, "evidence": "GitHub submission receipt exists"}
    store = session_dir / "submission" / "review_store.json"
    if not store.exists():
        return {"passed": True, "evidence": "No review store and no remote write"}
    records = json.loads(store.read_text(encoding="utf-8"))
    submitted = [record for record in records if record.get("status") == "submitted"]
    return {
        "passed": not submitted,
        "evidence": f"{len(submitted)} submitted record(s)",
    }
