#!/usr/bin/env python3
"""Deterministic, dependency-free review finding deduplication."""

from __future__ import annotations

import re
from typing import Iterable


_IDENTIFIER = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*(?:[.:/#][A-Za-z_$][A-Za-z0-9_$]*)*")
_MARKUP = re.compile(r"\*\*|`+|#+|\[[NCO]\d+\]")
_NOISE_WORDS = {
    "and", "are", "but", "for", "from", "into", "that", "the", "this", "with",
    "issue", "problem", "suggestion", "问题描述", "建议", "位置", "严重性",
}


def normalize_text(text: object) -> str:
    """Return stable text for comparison without presentation markup."""
    value = _MARKUP.sub(" ", str(text or "")).casefold()
    return " ".join(value.split())


def character_bigrams(text: object) -> set[str]:
    """Return Unicode character bigrams after whitespace/punctuation removal."""
    compact = "".join(ch for ch in normalize_text(text) if ch.isalnum() or ch in "_$")
    if not compact:
        return set()
    return {compact} if len(compact) == 1 else {compact[i:i + 2] for i in range(len(compact) - 1)}


def bigram_overlap(left: object, right: object) -> float:
    """Overlap coefficient in [0, 1], suitable for short review descriptions."""
    a, b = character_bigrams(left), character_bigrams(right)
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


bigram_similarity = bigram_overlap


def extract_identifiers(text: object) -> set[str]:
    """Extract code-like identifiers, excluding prose boilerplate."""
    return {
        token.casefold()
        for token in _IDENTIFIER.findall(str(text or ""))
        if token.casefold() not in _NOISE_WORDS and (len(token) > 2 or any(ch in token for ch in "_$.:/#"))
    }


def is_similar_content(
    left: object,
    right: object,
    threshold: float = 0.4,
    min_identifier_overlap: int = 2,
    *,
    bigram_threshold: float | None = None,
) -> bool:
    """Conservatively match the same root cause, not merely the same topic."""
    a, b = normalize_text(left), normalize_text(right)
    if not a or not b:
        return False
    if a == b:
        return True
    threshold = threshold if bigram_threshold is None else bigram_threshold
    identifiers = extract_identifiers(left) & extract_identifiers(right)
    return len(identifiers) >= min_identifier_overlap and bigram_overlap(a, b) >= threshold


def finding_text(finding: dict) -> str:
    """Collect only root-cause-bearing fields from a finding/comment record."""
    return "\n".join(
        str(finding.get(key, ""))
        for key in ("root_cause", "evidence", "comment", "body", "impact", "fix", "fix_suggestion")
        if finding.get(key)
    )


def is_duplicate_finding(
    existing: dict,
    candidate: dict,
    *,
    line_tolerance: int = 30,
    bigram_threshold: float = 0.4,
    min_identifier_overlap: int = 2,
) -> bool:
    """Match findings only within one file and a nearby added-line anchor."""
    old_path = existing.get("file_path", existing.get("file", ""))
    new_path = candidate.get("file_path", candidate.get("file", ""))
    if not old_path or old_path != new_path:
        return False
    try:
        if abs(int(existing.get("line", 0)) - int(candidate.get("line", 0))) > line_tolerance:
            return False
    except (TypeError, ValueError):
        return False
    return is_similar_content(
        finding_text(existing),
        finding_text(candidate),
        bigram_threshold,
        min_identifier_overlap,
    )


def deduplicate_findings(findings: Iterable[dict], **kwargs: object) -> list[dict]:
    """Keep the first item from each deterministic duplicate group."""
    kept: list[dict] = []
    for finding in findings:
        if not any(is_duplicate_finding(old, finding, **kwargs) for old in kept):
            kept.append(finding)
    return kept


__all__ = [
    "bigram_overlap",
    "bigram_similarity",
    "character_bigrams",
    "deduplicate_findings",
    "extract_identifiers",
    "finding_text",
    "is_duplicate_finding",
    "is_similar_content",
    "normalize_text",
]
