#!/usr/bin/env python3
"""Filter and update project-local review knowledge with integrity gating."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from dedup_utils import bigram_overlap, normalize_text


DEFAULT_PER_CATEGORY = 10
DEFAULT_TOTAL = 50
DEFAULT_THRESHOLD = 0.4


def _read(path: Path, default: object) -> object:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return default


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _context_project_root(context: dict, context_path: Path) -> Path:
    metadata = context.get("metadata", {})
    workspace = metadata.get("review_workspace", {}) if isinstance(metadata, dict) else {}
    if isinstance(workspace, dict) and workspace.get("path"):
        return Path(str(workspace["path"])).resolve()
    for parent in context_path.resolve().parents:
        if parent.name == ".ai":
            return parent.parent
    return Path.cwd().resolve()


def _knowledge_dir(explicit: Path | None, context: dict, context_path: Path) -> Path:
    return explicit.resolve() if explicit else _context_project_root(context, context_path) / ".ai" / "code-review-new" / "knowledge"


def _entries(data: object) -> list[dict]:
    if isinstance(data, list):
        return [entry for entry in data if isinstance(entry, dict)]
    if isinstance(data, dict):
        value = data.get("entries", [])
        if isinstance(value, list):
            return [entry for entry in value if isinstance(entry, dict)]
        categories = data.get("categories", {})
        if isinstance(categories, dict):
            return [entry for items in categories.values() if isinstance(items, list) for entry in items if isinstance(entry, dict)]
    return []


def _changed_paths(context: dict) -> list[str]:
    result = []
    for item in context.get("changed_files", []):
        path = item if isinstance(item, str) else item.get("filename", item.get("path", item.get("file_path", "")))
        if path and path not in result:
            result.append(str(path))
    return result


def _resolve(context_path: Path, value: object) -> Path | None:
    if not value:
        return None
    path = Path(str(value))
    candidates = [path] if path.is_absolute() else [context_path.parent / path, Path.cwd() / path]
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def _diff_text_by_path(context: dict, context_path: Path) -> dict[str, str]:
    diff_path = _resolve(context_path, context.get("diff_file") or context.get("diffs_file"))
    data = _read(diff_path, []) if diff_path else context.get("diffs", [])
    if isinstance(data, dict):
        data = data.get("files", data.get("diffs", []))
    result: dict[str, str] = {}
    for record in data if isinstance(data, list) else []:
        if not isinstance(record, dict):
            continue
        path = str(record.get("file_path") or record.get("filename") or record.get("path") or record.get("new_path") or record.get("old_path") or "")
        content = record.get("content", record.get("patch", ""))
        result[path] = "\n".join(map(str, content)) if isinstance(content, list) else str(content or "")
    return result


def _entry_paths(entry: dict) -> list[str]:
    value = entry.get("source_files", entry.get("source_file", entry.get("file_path", entry.get("file", []))))
    if isinstance(value, str):
        return [value]
    return [str(path) for path in value] if isinstance(value, list) else []


def _entry_pattern(entry: dict) -> str:
    return str(entry.get("pattern") or entry.get("root_cause") or entry.get("evidence") or entry.get("comment") or entry.get("body") or "")


def _path_matches(source: str, changed: str, _threshold: float) -> bool:
    left, right = source.replace("\\", "/").casefold(), changed.replace("\\", "/").casefold()
    return left == right or left.endswith("/" + right) or right.endswith("/" + left)


def filter_entries(context: dict, context_path: Path, entries: list[dict], threshold: float) -> list[dict]:
    changed = _changed_paths(context)
    diffs = _diff_text_by_path(context, context_path)
    matches = []
    for entry in entries:
        pattern = _entry_pattern(entry)
        if not pattern:
            continue
        candidate_paths = [path for path in changed if any(_path_matches(source, path, threshold) for source in _entry_paths(entry))]
        if candidate_paths and any(bigram_overlap(pattern, diffs.get(path, "")) >= threshold for path in candidate_paths):
            matches.append(entry)
    return sorted(matches, key=lambda entry: (str(entry.get("category", "")), str(entry.get("id", ""))))


def _find(session: Path, names: tuple[str, ...], directories: tuple[str, ...]) -> Path | None:
    for directory in directories:
        for name in names:
            candidate = session / directory / name if directory else session / name
            if candidate.is_file():
                return candidate
    return None


def _integrity_complete(session: Path) -> tuple[bool, Path | None, object]:
    path = _find(session, ("review-integrity.json", "review_integrity.json"), ("submission", "context", ""))
    data = _read(path, {}) if path else {}
    status = ""
    if isinstance(data, dict):
        status = str(data.get("status") or data.get("integrity_status") or data.get("overall_status") or data.get("state") or data.get("public_status") or "")
        if isinstance(data.get("integrity"), dict):
            status = status or str(data["integrity"].get("status", ""))
    return status.casefold() == "complete", path, data


def _proof_records(data: object) -> list[dict]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("proofs", "defect_proofs", "records", "confirmed_findings"):
            if isinstance(data.get(key), list):
                return [item for item in data[key] if isinstance(item, dict)]
    return []


def _unwrap(item: dict) -> dict:
    for key in ("finding", "source_finding", "original_finding", "record"):
        if isinstance(item.get(key), dict):
            return item[key]
    return item


def _confirmed(item: dict) -> bool:
    decision = str(item.get("decision", item.get("status", ""))).casefold().replace("-", "_")
    return decision in {"confirmed", "publish", "publishable", "published", "retained", "accepted", "keep", "pass", "passed"}


def _failed(item: dict) -> bool:
    decision = str(item.get("decision", item.get("status", ""))).casefold().replace("-", "_")
    return decision in {"failed", "fail", "rejected", "discarded", "drop", "dropped"}


def _attach_finding(item: dict, findings_by_id: dict[str, dict]) -> dict:
    if _unwrap(item).get("file") or _unwrap(item).get("file_path"):
        return item
    finding_id = str(item.get("finding_id") or item.get("source_finding_id") or item.get("id") or "")
    return {**item, "finding": findings_by_id[finding_id]} if finding_id in findings_by_id else item


def _new_entry(item: dict, kind: str, run_id: str, now: str) -> dict | None:
    finding = _unwrap(item)
    source_file = str(finding.get("file_path") or finding.get("file") or finding.get("source_file") or "")
    pattern = str(finding.get("root_cause") or finding.get("evidence") or finding.get("comment") or finding.get("body") or finding.get("impact") or "")
    if not source_file or not normalize_text(pattern):
        return None
    category = str(finding.get("category") or finding.get("severity") or "uncategorized")
    identity = json.dumps([kind, category, source_file, normalize_text(pattern)], ensure_ascii=False, separators=(",", ":"))
    return {
        "id": hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20],
        "kind": kind,
        "category": category,
        "source_file": source_file,
        "pattern": pattern,
        "finding_id": str(finding.get("id", "")),
        "rule_ids": finding.get("rules", finding.get("rule_ids", [])),
        "source_run": run_id,
        "created_at": now,
        "last_used_at": now,
    }


def _merge_lru(old: list[dict], new: list[dict], per_category: int, total: int) -> list[dict]:
    merged = {str(entry.get("id", "")): entry for entry in old if entry.get("id")}
    for entry in new:
        prior = merged.get(entry["id"], {})
        merged[entry["id"]] = {**prior, **entry, "created_at": prior.get("created_at", entry["created_at"])}
    ordered = sorted(merged.values(), key=lambda entry: (str(entry.get("last_used_at", "")), str(entry.get("id", ""))), reverse=True)
    kept, counts = [], {}
    for entry in ordered:
        category = str(entry.get("category", "uncategorized"))
        if counts.get(category, 0) >= per_category:
            continue
        counts[category] = counts.get(category, 0) + 1
        kept.append(entry)
    return kept[:total]


def _config_limits() -> tuple[int, int, float]:
    for path in (Path.cwd() / ".code-review-new" / "config.json", Path(__file__).parent.parent / "config.json"):
        data = _read(path, {}) if path.is_file() else {}
        knowledge = data.get("knowledge", {}) if isinstance(data, dict) else {}
        if isinstance(knowledge, dict) and knowledge:
            return (
                int(knowledge.get("per_category", knowledge.get("max_per_category", DEFAULT_PER_CATEGORY))),
                int(knowledge.get("total", knowledge.get("max_total", DEFAULT_TOTAL))),
                float(knowledge.get("similarity_threshold", DEFAULT_THRESHOLD)),
            )
    return DEFAULT_PER_CATEGORY, DEFAULT_TOTAL, DEFAULT_THRESHOLD


def command_filter(args: argparse.Namespace, kind: str) -> int:
    context_path = args.context.resolve()
    context = _read(context_path, {})
    if not isinstance(context, dict):
        raise ValueError("context must be a JSON object")
    knowledge_dir = _knowledge_dir(args.knowledge_dir, context, context_path)
    name = "positive_knowledge.json" if kind == "positive" else "negative_knowledge.json"
    selected = filter_entries(context, context_path, _entries(_read(knowledge_dir / name, {})), args.threshold)
    result = {"schema_version": 1, "kind": kind, "source": str(knowledge_dir / name), "entries": selected, "matched_count": len(selected)}
    _atomic_json(args.output, result)
    print(json.dumps({"output": str(args.output), "matched_count": len(selected)}, ensure_ascii=False))
    return 0


def command_update(args: argparse.Namespace) -> int:
    session = args.session.resolve()
    complete, integrity_path, integrity = _integrity_complete(session)
    if not complete:
        print(json.dumps({"type": "ERROR", "error_type": "INTEGRITY_NOT_COMPLETE", "integrity_file": str(integrity_path or ""), "updated": False}, ensure_ascii=False))
        return 1
    context_path = _find(session, ("context.json",), ("context", ""))
    if not context_path:
        raise ValueError("session context.json not found")
    context = _read(context_path, {})
    if not isinstance(context, dict):
        raise ValueError("context must be a JSON object")
    knowledge_dir = _knowledge_dir(args.knowledge_dir, context, context_path)
    proofs_path = _find(session, ("defect-proofs.json", "defect_proofs.json"), ("submission", "inbox", ""))
    adversary_path = _find(session, ("adversary_challenges.json",), ("inbox", "submission", ""))
    proofs_data = _read(proofs_path, {}) if proofs_path else {}
    adversary_data = _read(adversary_path, {}) if adversary_path else {}
    proofs = _proof_records(proofs_data)
    review_store = _read(session / "submission" / "review_store.json", [])
    review_store = review_store if isinstance(review_store, list) else []
    findings_by_id = {
        str(item.get("id")): item
        for item in review_store if isinstance(item, dict) and item.get("id")
    }
    proofs = [_attach_finding(item, findings_by_id) for item in proofs]
    explicit_confirmed = proofs_data.get("confirmed_findings", []) if isinstance(proofs_data, dict) else []
    positive_items = [item for item in proofs if _confirmed(item)]
    positive_items.extend(_attach_finding(item, findings_by_id) for item in explicit_confirmed if isinstance(item, dict) and item not in positive_items)
    failed_items = [item for item in proofs if _failed(item)]
    if isinstance(proofs_data, dict) and isinstance(proofs_data.get("failed_proofs"), list):
        failed_items.extend(item for item in proofs_data["failed_proofs"] if isinstance(item, dict))
    discarded = adversary_data.get("discarded_findings", []) if isinstance(adversary_data, dict) else []
    negative_items = [item for item in discarded if isinstance(item, dict)] + failed_items
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    run_id = str(integrity.get("run_id", context.get("run_id", session.name))) if isinstance(integrity, dict) else session.name
    positive = [entry for item in positive_items if (entry := _new_entry(item, "positive", run_id, now))]
    negative = [entry for item in negative_items if (entry := _new_entry(item, "negative", run_id, now))]
    merged_by_kind = {}
    for kind, incoming in (("positive", positive), ("negative", negative)):
        path = knowledge_dir / f"{kind}_knowledge.json"
        merged_by_kind[kind] = _merge_lru(
            _entries(_read(path, {})), incoming, args.per_category, args.total
        )
    combined = sorted(
        ((kind, entry) for kind, entries in merged_by_kind.items() for entry in entries),
        key=lambda item: (str(item[1].get("last_used_at", "")), str(item[1].get("id", ""))),
        reverse=True,
    )[:args.total]
    kept_by_kind = {
        kind: [entry for entry_kind, entry in combined if entry_kind == kind]
        for kind in ("positive", "negative")
    }
    counts = {}
    for kind, incoming in (("positive", positive), ("negative", negative)):
        path = knowledge_dir / f"{kind}_knowledge.json"
        _atomic_json(path, {"schema_version": 1, "kind": kind, "entries": kept_by_kind[kind]})
        counts[kind] = {"added_or_refreshed": len(incoming), "stored": len(kept_by_kind[kind])}
    print(json.dumps({"updated": True, "knowledge_dir": str(knowledge_dir), "counts": counts}, ensure_ascii=False, indent=2))
    return 0


def command_stats(args: argparse.Namespace) -> int:
    context = _read(args.context.resolve(), {}) if args.context else {}
    context_path = args.context.resolve() if args.context else Path.cwd() / "context.json"
    knowledge_dir = _knowledge_dir(args.knowledge_dir, context if isinstance(context, dict) else {}, context_path)
    result = {}
    for kind in ("positive", "negative"):
        entries = _entries(_read(knowledge_dir / f"{kind}_knowledge.json", {}))
        categories = {}
        for entry in entries:
            category = str(entry.get("category", "uncategorized"))
            categories[category] = categories.get(category, 0) + 1
        result[kind] = {"total": len(entries), "categories": dict(sorted(categories.items()))}
    print(json.dumps({"knowledge_dir": str(knowledge_dir), **result}, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    configured_per_category, configured_total, configured_threshold = _config_limits()
    parser = argparse.ArgumentParser(description="Manage project-local review knowledge")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("filter", "filter-negative"):
        child = subparsers.add_parser(command, help=f"filter {'positive' if command == 'filter' else 'negative'} knowledge")
        child.add_argument("--context", required=True, type=Path)
        child.add_argument("--knowledge-dir", type=Path)
        child.add_argument("--output", required=True, type=Path)
        child.add_argument("--threshold", type=float, default=configured_threshold)
    update = subparsers.add_parser("update", help="update knowledge from a complete review session")
    update.add_argument("--session", required=True, type=Path)
    update.add_argument("--knowledge-dir", type=Path)
    update.add_argument("--per-category", type=int, default=configured_per_category)
    update.add_argument("--total", type=int, default=configured_total)
    stats = subparsers.add_parser("stats", help="show knowledge counts")
    stats.add_argument("--context", type=Path)
    stats.add_argument("--knowledge-dir", type=Path)
    args = parser.parse_args()
    try:
        if getattr(args, "threshold", DEFAULT_THRESHOLD) < 0 or getattr(args, "threshold", DEFAULT_THRESHOLD) > 1:
            parser.error("--threshold must be in [0, 1]")
        if getattr(args, "per_category", 1) <= 0 or getattr(args, "total", 1) <= 0:
            parser.error("knowledge limits must be positive")
        if args.command == "filter":
            return command_filter(args, "positive")
        if args.command == "filter-negative":
            return command_filter(args, "negative")
        if args.command == "update":
            return command_update(args)
        return command_stats(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"type": "ERROR", "error_type": "KNOWLEDGE_OPERATION_FAILED", "message": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
