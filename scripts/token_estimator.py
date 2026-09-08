#!/usr/bin/env python3
"""Conservative byte-based token budget estimator for the review pipeline."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


DEFAULT_BUDGET_LIMIT = 200_000
DEFAULT_TASK_BUDGET = 60_000
DEFAULT_MARGINAL_RATIO = 0.8
DEFAULT_BYTES_PER_TOKEN = 3.0
AGENT_OVERHEAD = 4_000


def _load(path: Path | None, default: object) -> object:
    if not path:
        return default
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _tokens(value: object, bytes_per_token: float) -> int:
    if not value:
        return 0
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
    return math.ceil(len(text.encode("utf-8")) / bytes_per_token)


def _resolve(value: object, anchors: list[Path]) -> Path | None:
    if not value:
        return None
    path = Path(str(value))
    candidates = [path] if path.is_absolute() else [anchor / path for anchor in anchors]
    return next((candidate.resolve() for candidate in candidates if candidate.is_file()), None)


def _diffs(context: dict, context_path: Path) -> list[dict]:
    path = _resolve(context.get("diff_file") or context.get("diffs_file"), [context_path.parent, Path.cwd()])
    data = _load(path, context.get("diffs", []))
    if isinstance(data, dict):
        data = data.get("files", data.get("diffs", []))
    return data if isinstance(data, list) else []


def _path(record: dict) -> str:
    return str(record.get("file_path") or record.get("filename") or record.get("path") or record.get("new_path") or record.get("old_path") or "")


def _file_tokens(path: Path | None, bytes_per_token: float) -> int:
    try:
        return math.ceil(path.stat().st_size / bytes_per_token) if path else 0
    except OSError:
        return 0


def _config() -> dict:
    for path in (Path.cwd() / ".code-review-new" / "config.json", Path(__file__).parent.parent / "config.json"):
        try:
            if path.is_file():
                data = _load(path, {})
                return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def estimate(
    context_path: Path,
    prescan_path: Path | None,
    manifest_path: Path | None,
    *,
    budget_limit: int,
    task_budget: int,
    marginal_ratio: float,
    bytes_per_token: float,
    max_rule_fraction: float,
) -> dict:
    context = _load(context_path, {})
    manifest = _load(manifest_path, {})
    prescan = _load(prescan_path, {})
    if not isinstance(context, dict) or not isinstance(manifest, dict):
        raise ValueError("context and manifest must be JSON objects")
    whole_repo = context.get("metadata", {}).get("review_mode") == "whole_repo"
    records = _diffs(context, context_path)
    diff_by_path = {_path(record): record for record in records if isinstance(record, dict)}
    workspace = context.get("metadata", {}).get("review_workspace", {})
    workspace_path = Path(str(workspace.get("path"))) if isinstance(workspace, dict) and workspace.get("path") else None
    anchors = [path for path in (workspace_path, Path.cwd(), Path(__file__).parent.parent) if path]
    if manifest_path:
        anchors.insert(0, manifest_path.parent)

    tasks = manifest.get("review_tasks", [])
    if not isinstance(tasks, list) or not tasks:
        tasks = [{
            "task_id": "single-review",
            "scope_file_paths": list(diff_by_path),
            "local_rule_paths": manifest.get("local_rule_paths", []),
            "repository_rule_paths": manifest.get("repository_rule_paths", []),
        }]

    context_dir = context_path.parent
    knowledge_paths = [context_dir / "filtered_knowledge.json", context_dir / "filtered_negative_knowledge.json"]
    knowledge_tokens = sum(_file_tokens(path if path.is_file() else None, bytes_per_token) for path in knowledge_paths)
    prescan_tokens = _tokens(prescan, bytes_per_token)
    breakdown = []
    all_rule_paths: set[Path] = set()
    for task in tasks:
        if not isinstance(task, dict):
            continue
        scope = [str(path) for path in task.get("scope_file_paths", [])]
        diff_tokens = sum(_tokens(diff_by_path.get(path, {}), bytes_per_token) for path in scope)
        rule_paths = []
        for raw in list(task.get("local_rule_paths", [])) + list(task.get("repository_rule_paths", [])):
            resolved = _resolve(raw, anchors)
            if resolved and resolved not in rule_paths:
                rule_paths.append(resolved)
                all_rule_paths.add(resolved)
        rules_tokens = sum(_file_tokens(path, bytes_per_token) for path in rule_paths)
        total = diff_tokens + rules_tokens + knowledge_tokens + prescan_tokens + AGENT_OVERHEAD
        if total > task_budget or rules_tokens > task_budget * max_rule_fraction:
            recommendation = "exceeds_task_budget"
        elif total > task_budget * marginal_ratio:
            recommendation = "marginal_task_budget"
        else:
            recommendation = "within_task_budget"
        breakdown.append({
            "task_id": str(task.get("task_id", "")),
            "scope_file_count": len(scope),
            "diff_tokens": diff_tokens,
            "rules_tokens": rules_tokens,
            "knowledge_tokens": knowledge_tokens,
            "prescan_tokens": prescan_tokens,
            "overhead_tokens": AGENT_OVERHEAD,
            "total": total,
            "task_recommendation": recommendation,
        })

    diff_tokens = sum(_tokens(record, bytes_per_token) for record in records)
    rules_tokens = sum(_file_tokens(path, bytes_per_token) for path in all_rule_paths)
    single_total = diff_tokens + rules_tokens + knowledge_tokens + prescan_tokens + AGENT_OVERHEAD
    reviewer_total = sum(item["total"] for item in breakdown)
    peak_concurrent = sum(sorted((item["total"] for item in breakdown), reverse=True)[:5])
    synthesizer = diff_tokens + max(AGENT_OVERHEAD, math.ceil(reviewer_total * 0.15))
    pipeline_total = reviewer_total + synthesizer
    if pipeline_total > budget_limit:
        recommendation = "exceeds_budget"
    elif pipeline_total > budget_limit * marginal_ratio:
        recommendation = "marginal"
    else:
        recommendation = "within_budget"

    suggestions = []
    if any(item["rules_tokens"] > task_budget * max_rule_fraction for item in breakdown):
        suggestions.append(f"remove rules not routed to the task; rule text must stay within {max_rule_fraction:.0%} of task budget")
    if any(item["task_recommendation"] == "exceeds_task_budget" for item in breakdown):
        suggestions.append(
            "adjust whole_repo exclusions or split into explicitly declared module audits; do not silently drop files"
            if whole_repo else "limit oversized tasks to the 10 files with the most changed lines"
        )
    if recommendation != "within_budget":
        suggestions.append(
            "keep exact coverage and rerun after adjusting the declared whole-repository scope"
            if whole_repo else "reduce routed scope and rerun this estimator before dispatch"
        )
    return {
        "schema_version": 1,
        "heuristic": {"bytes_per_token": bytes_per_token, "agent_overhead_tokens": AGENT_OVERHEAD},
        "limits": {
            "budget_limit": budget_limit,
            "single_task_budget": task_budget,
            "marginal_ratio": marginal_ratio,
            "max_rule_fraction": max_rule_fraction,
        },
        "estimated_tokens": {
            "diff": diff_tokens,
            "rules": rules_tokens,
            "knowledge": knowledge_tokens,
            "prescan": prescan_tokens,
            "overhead": AGENT_OVERHEAD,
            "total": single_total,
        },
        "pipeline_estimates": {
            "reviewers_total": reviewer_total,
            "peak_concurrent": peak_concurrent,
            "max_concurrent_reviewers": min(5, len(breakdown)),
            "synthesizer": synthesizer,
            "pipeline_total": pipeline_total,
        },
        "per_task_breakdown": breakdown,
        "recommendation": recommendation,
        "suggestions": suggestions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate review pipeline token use")
    parser.add_argument("--context", required=True, type=Path)
    parser.add_argument("--prescan", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path, help="optional JSON output path")
    parser.add_argument("--budget-limit", type=int)
    parser.add_argument("--task-budget", type=int)
    parser.add_argument("--marginal-ratio", type=float)
    parser.add_argument("--bytes-per-token", type=float)
    parser.add_argument("--max-rule-fraction", type=float)
    args = parser.parse_args()
    config = _config().get("token_budget", {})
    config = config if isinstance(config, dict) else {}
    budget = args.budget_limit or int(config.get("pipeline_limit", config.get("budget_limit", DEFAULT_BUDGET_LIMIT)))
    task_budget = args.task_budget or int(config.get("single_task_limit", config.get("single_task_budget", DEFAULT_TASK_BUDGET)))
    ratio = args.marginal_ratio if args.marginal_ratio is not None else float(config.get("marginal_ratio", DEFAULT_MARGINAL_RATIO))
    bytes_per_token = args.bytes_per_token or float(config.get("bytes_per_token", DEFAULT_BYTES_PER_TOKEN))
    rule_fraction = args.max_rule_fraction if args.max_rule_fraction is not None else float(config.get("max_rule_fraction", 0.3))
    if budget <= 0 or task_budget <= 0 or not 0 < ratio < 1 or bytes_per_token <= 0 or not 0 < rule_fraction <= 1:
        parser.error("budgets and bytes-per-token must be positive; ratios must be in (0, 1]")
    try:
        result = estimate(args.context.resolve(), args.prescan.resolve() if args.prescan else None, args.manifest.resolve() if args.manifest else None,
                          budget_limit=budget, task_budget=task_budget, marginal_ratio=ratio,
                          bytes_per_token=bytes_per_token, max_rule_fraction=rule_fraction)
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"type": "ERROR", "error_type": "TOKEN_ESTIMATE_FAILED", "message": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
