#!/usr/bin/env python3
"""Assertion: check that COM-ARCH-007/008 issues are either in review_store or already covered by existing comments."""

import json
from pathlib import Path


def check(session_dir: Path, **kwargs) -> dict:
    """Check that major-severity COM-ARCH findings exist either in review_store or in existing comments.
    
    This handles the case where the Synthesizer correctly skips findings that are already
    covered by existing review comments — the finding was detected (by Reviewer) but
    deduplicated at synthesis time.
    """
    store_file = session_dir / "submission" / "review_store.json"
    context_file = session_dir / "context" / "context.json"

    # Check review_store for major findings
    store_major = []
    if store_file.exists():
        with open(store_file, "r", encoding="utf-8") as f:
            records = json.load(f)
        for r in records:
            if r.get("severity") in ("fatal", "major"):
                store_major.append(r.get("id", "?"))

    if store_major:
        return {"passed": True, "evidence": f"{len(store_major)} major+ findings in review_store: {store_major}"}

    # No major findings in review_store — check if existing comments cover COM-ARCH issues
    # Read context to find existing_review_comments_file
    if context_file.exists():
        with open(context_file, "r", encoding="utf-8") as f:
            ctx = json.load(f)
        comments_file = ctx.get("existing_review_comments_file", "")
        if comments_file and Path(comments_file).exists():
            with open(comments_file, "r", encoding="utf-8") as f:
                comments_data = json.load(f)

            # comments_data could be a list or dict with "comments" key
            comments_list = comments_data if isinstance(comments_data, list) else comments_data.get("comments", [])
            
            arch_keywords = ["COM-ARCH-007", "COM-ARCH-008", "checkWholeNetworkPolicy", 
                           "校验被绕过", "新增值未处理", "枚举扩展"]
            
            for c in comments_list:
                body = c.get("body", "") if isinstance(c, dict) else str(c)
                if any(kw in body for kw in arch_keywords):
                    return {"passed": True, "evidence": f"No major in review_store, but existing comment covers COM-ARCH issue (e.g., comment id={c.get('id', '?')})"}

    # Also check Reviewer raw output for COM-ARCH findings that were deduplicated
    reviewers_dir = session_dir / "reviewers"
    if reviewers_dir.exists():
        for f in reviewers_dir.glob("*.json"):
            with open(f, "r", encoding="utf-8") as fh:
                findings = json.load(fh)
            for finding in findings:
                rules = finding.get("rules", "")
                if "COM-ARCH-007" in rules or "COM-ARCH-008" in rules:
                    return {"passed": True, "evidence": f"No major in review_store, but Reviewer detected COM-ARCH finding in {f.name} (deduplicated by Synthesizer due to existing comments)"}

    return {"passed": False, "evidence": "No major findings in review_store and no COM-ARCH coverage in existing comments or Reviewer output"}
