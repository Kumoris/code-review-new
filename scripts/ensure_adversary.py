#!/usr/bin/env python3
"""Create the minimal, publication-closing Adversary fallback artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from review_core import (
    IntegrityError,
    atomic_json,
    derive_revision,
    extract_rule_ids,
    load_json,
    load_rule_registry,
    registry_status,
)


def _findings_for_task(session: Path, task: dict) -> list:
    admitted = session / "admission" / "reviewers" / f"{task.get('task_id', '')}.json"
    candidates = [admitted, Path(task.get("output_path", ""))]
    for path in candidates:
        if not str(path) or not path.exists() or path.is_dir():
            continue
        value = load_json(path)
        if isinstance(value, dict):
            value = value.get("output", value.get("findings", []))
        if isinstance(value, list):
            return value
    return []


def build_fallback(context: dict, findings_by_task: dict[str, list], registry: dict[str, str]) -> dict:
    challenges = []
    for task_id, findings in findings_by_task.items():
        for finding in findings:
            statuses = [registry_status(rule_id, registry) for rule_id in extract_rule_ids(finding.get("rules", ""))]
            disabled = "disabled" in statuses
            challenges.append({
                "finding_id": f"{task_id}:{finding.get('id', '')}",
                "verdict": "SPECULATIVE" if disabled else "LIKELY",
                "rationale": (
                    "fallback rejected a disabled rule"
                    if disabled
                    else "fallback checked registry status only; independent challenge was unavailable"
                ),
            })
    return {
        "schema_version": 1,
        "revision": derive_revision(context),
        "fallback": True,
        "publish_eligible": False,
        "reason": "adversary response missing; registry-only fallback",
        "challenges": challenges,
    }


def create_fallback(context_path: str, manifest_path: str, output_path: str, registry_path: str) -> dict:
    context, manifest = load_json(context_path), load_json(manifest_path)
    session = Path(manifest_path).resolve().parent.parent
    registry = load_rule_registry(registry_path)
    findings_by_task = {
        task.get("task_id", ""): _findings_for_task(session, task)
        for task in manifest.get("review_tasks", [])
    }
    result = build_fallback(context, findings_by_task, registry)
    target = Path(output_path)
    if target.exists():
        existing = load_json(target)
        if not isinstance(existing, dict) or "challenges" not in existing:
            raise IntegrityError("invalid-adversary", f"existing adversary artifact is invalid: {target}")
        return existing
    atomic_json(target, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Ensure an Adversary result exists without opening publication")
    parser.add_argument("--context", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output")
    parser.add_argument(
        "--registry",
        default=str(Path(__file__).parent.parent / "references" / "rule-registry.md"),
    )
    args = parser.parse_args()
    session = Path(args.manifest).resolve().parent.parent
    output = args.output or str(session / "inbox" / "adversary_challenges.json")
    try:
        result = create_fallback(args.context, args.manifest, output, args.registry)
    except (IntegrityError, OSError, json.JSONDecodeError, ValueError) as error:
        print(json.dumps({"type": "ERROR", "message": str(error)}, ensure_ascii=False))
        sys.exit(2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
