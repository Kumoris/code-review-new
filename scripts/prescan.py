#!/usr/bin/env python3
"""Deterministic lexical prescan for rule routing; never emits findings."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath


LANGUAGES = {
    ".java": "java", ".c": "c-cpp", ".cc": "c-cpp", ".cpp": "c-cpp",
    ".cxx": "c-cpp", ".h": "c-cpp", ".hpp": "c-cpp", ".hxx": "c-cpp",
    ".go": "go", ".py": "python", ".pyi": "python", ".js": "js-ts",
    ".jsx": "js-ts", ".ts": "js-ts", ".tsx": "js-ts", ".mjs": "js-ts",
    ".sh": "shell", ".bash": "shell", ".zsh": "shell", ".cs": "csharp",
    ".rs": "rust", ".xml": "xml", ".yaml": "structured", ".yml": "structured",
    ".json": "structured", ".csv": "structured", ".html": "structured",
    ".htm": "structured", ".properties": "structured", ".less": "structured",
    ".scss": "structured", ".sass": "structured",
}
ALWAYS_CHECKS = {
    "hardcoded-credentials": re.compile(
        r"(?i)\b(?:password|passwd|secret|api[_-]?key|access[_-]?token|credential)\b"
        r"\s*[:=]\s*[\"'][^\"'\n$]{3,}[\"']"
    ),
    "weak-cryptography": re.compile(r"(?i)\b(?:md5|sha[-_]?1|des|3des|rc4|ecb)\b"),
    "digital-certificates": re.compile(
        r"(?i)(?:trust[_-]?all|allow[_-]?all[_-]?hostname|ssl[_-]?verify\s*[:=]\s*false|"
        r"verify\s*[:=]\s*false|关闭.{0,8}(?:证书|tls|ssl).{0,8}验证)"
    ),
}
SECURITY_SIGNALS = {
    "input-validation-injection": re.compile(
        r"(?i)\b(?:eval|exec|system|popen|shell\s*=\s*true|innerhtml|"
        r"executequery|executestatement|rawquery|sqlquery)\b"
    ),
    "authentication-authorization": re.compile(
        r"(?i)(?:^|[/_.-])(?:auth|login|oauth|permission|acl|rbac|session)(?:[/_.-]|$)"
    ),
    "sensitive-data-logging": re.compile(
        r"(?i)\b(?:log|logger|print|printf)\w*\s*\([^\n]*(?:password|secret|token|credential|pii)"
    ),
    "unsafe-deserialization": re.compile(r"(?i)\b(?:pickle\.loads?|yaml\.load|readobject|deserialize)\b"),
}
SPARK_CODE = re.compile(r"\b(?:SparkSession|DataFrame|RDD|Dataset)\b")
JSX_PROP = re.compile(r"\b([A-Za-z_$][\w$]*(?:Handler|Callback)?|on[A-Z]\w*|handle[A-Z]\w*)\s*=")
TRIVIAL_LINE = re.compile(r"^(?:[{}()[\],;]+|//.*|#.*|/\*.*|\*.*|<!--.*|-->.*)?$")


def _read_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _resolve(reference: object, context_path: Path) -> Path | None:
    if not reference:
        return None
    path = Path(str(reference))
    candidates = [path] if path.is_absolute() else [context_path.parent / path, Path.cwd() / path]
    return next((candidate.resolve() for candidate in candidates if candidate.exists()), candidates[0])


def _changed_paths(context: dict) -> list[str]:
    paths = []
    for item in context.get("changed_files", []):
        value = item if isinstance(item, str) else item.get("filename", item.get("path", item.get("file_path", "")))
        if value and value not in paths:
            paths.append(str(value))
    return paths


def _diff_records(context: dict, context_path: Path) -> list[dict]:
    reference = context.get("diff_file") or context.get("diffs_file")
    path = _resolve(reference, context_path)
    if path and path.exists():
        data = _read_json(path)
        if isinstance(data, dict):
            data = data.get("files", data.get("diffs", []))
        return data if isinstance(data, list) else []
    inline = context.get("diffs", [])
    return inline if isinstance(inline, list) else []


def _record_path(record: dict) -> str:
    return str(record.get("file_path") or record.get("filename") or record.get("path") or record.get("new_path") or record.get("old_path") or "")


def _marked_lines(record: dict) -> list[tuple[str, str]]:
    content = record.get("content", record.get("patch", []))
    lines = content if isinstance(content, list) else str(content or "").splitlines()
    result: list[tuple[str, str]] = []
    for raw in lines:
        line = str(raw)
        match = re.match(r"^\[([NCO])\d+\](.*)$", line)
        if match:
            result.append((match.group(1), match.group(2)))
        elif line.startswith("+") and not line.startswith("+++"):
            result.append(("N", line[1:]))
        elif line.startswith("-") and not line.startswith("---"):
            result.append(("O", line[1:]))
        elif line.startswith(" "):
            result.append(("C", line[1:]))
    return result


def _language(path: str) -> str:
    name = PurePosixPath(path).name.casefold()
    if name in {"dockerfile", "makefile"}:
        return "build-ops"
    return LANGUAGES.get(PurePosixPath(path).suffix.casefold(), "unsupported")


def _focus_paths(all_paths: list[str], classification: dict | None) -> tuple[list[str], str]:
    if not classification:
        return all_paths, "new_review"
    state = str(classification.get("classification", classification.get("state", "new_review")))
    if state in {"skip", "merge_ready"}:
        return [], state
    focus = next(
        (classification[key] for key in ("focus_files", "review_files", "delta_files") if isinstance(classification.get(key), list)),
        None,
    )
    if state in {"re_review", "review_current"} and isinstance(focus, list):
        allowed = {str(path) for path in focus}
        return [path for path in all_paths if path in allowed], state
    return all_paths, state


def _workspace(context: dict) -> Path | None:
    workspace = context.get("metadata", {}).get("review_workspace", {})
    if workspace.get("available") and workspace.get("path"):
        path = Path(workspace["path"])
        return path.resolve() if path.exists() else None
    return None


def _agents_file(workspace: Path | None, file_path: str) -> str | None:
    if not workspace:
        return None
    current = (workspace / file_path).parent
    try:
        current.relative_to(workspace)
    except ValueError:
        return None
    while True:
        candidate = current / "AGENTS.md"
        if candidate.is_file():
            return candidate.relative_to(workspace).as_posix()
        if current == workspace:
            return None
        current = current.parent


def _business_docs(workspace: Path | None, paths: list[str]) -> bool:
    if any(PurePosixPath(path).suffix.casefold() == ".md" for path in paths):
        return True
    return bool(workspace and any((workspace / name).is_dir() for name in ("docs", "design")))


def _scan_file(path: str, record: dict | None, workspace: Path | None, has_business_docs: bool) -> dict:
    language = _language(path)
    supported = language != "unsupported"
    marked = _marked_lines(record or {})
    added = "\n".join(text for marker, text in marked if marker == "N")
    scan_text = f"{path}\n{added}"
    if not supported:
        always = {name: "skipped-unsupported" for name in ALWAYS_CHECKS}
    elif record is None or record.get("patch_missing") is True:
        always = {name: "error" for name in ALWAYS_CHECKS}
    else:
        always = {name: ("signal" if pattern.search(added) else "checked-no-signal") for name, pattern in ALWAYS_CHECKS.items()}

    security = [name for name, pattern in SECURITY_SIGNALS.items() if pattern.search(scan_text)]
    spark = []
    if path.casefold().endswith((".dataset.yaml", ".dataset.yml", ".pipeline.yaml", ".pipeline.yml")):
        spark.append("spark-config")
    if SPARK_CODE.search(added):
        spark.append("spark-code")

    jsx = None
    if PurePosixPath(path).suffix.casefold() in {".jsx", ".tsx"}:
        old_props = {name for marker, text in marked if marker == "O" for name in JSX_PROP.findall(text)}
        new_props = {name for marker, text in marked if marker == "N" for name in JSX_PROP.findall(text)}
        jsx = [f"jsx-prop-removed:{name}" for name in sorted(old_props - new_props)]

    agents_path = _agents_file(workspace, path)
    return {
        "path": path,
        "language": language,
        "always_check": always,
        "security_signals": security,
        "spark_signals": spark,
        "jsx_signals": jsx,
        "agents_md_signal": "found" if agents_path else "not-found",
        "agents_md_path": agents_path,
        "business_doc_signal": "found" if has_business_docs else "not-found",
    }


def _is_trivial(records: list[dict], focus: set[str]) -> tuple[bool, int]:
    selected = [record for record in records if _record_path(record) in focus]
    added = [text.strip() for record in selected for marker, text in _marked_lines(record) if marker == "N"]
    changed = [text.strip() for record in selected for marker, text in _marked_lines(record) if marker in {"N", "O"}]
    complete = not focus or ({_record_path(record) for record in selected} == focus and not any(record.get("patch_missing") for record in selected))
    return complete and len(added) <= 3 and all(TRIVIAL_LINE.fullmatch(line) for line in changed), len(added)


def run(context_path: Path, classification_path: Path | None = None) -> dict:
    context = _read_json(context_path)
    if not isinstance(context, dict):
        raise ValueError("context must be a JSON object")
    classification = _read_json(classification_path) if classification_path else None
    if classification is not None and not isinstance(classification, dict):
        raise ValueError("classification must be a JSON object")
    paths, state = _focus_paths(_changed_paths(context), classification)
    records = _diff_records(context, context_path)
    by_path = {_record_path(record): record for record in records if isinstance(record, dict)}
    workspace = _workspace(context)
    business = _business_docs(workspace, paths)
    trivial, added_count = _is_trivial(records, set(paths))
    snapshot = context.get("snapshot", {})
    source_sha = snapshot.get("head_sha") or snapshot.get("source_sha") or context.get("source_sha") or ""
    return {
        "schema_version": 1,
        "source_sha": source_sha,
        "classification": state,
        "review_scope": paths,
        "files": [_scan_file(path, by_path.get(path), workspace, business) for path in paths],
        "finding_candidates": [],
        "trivial": trivial,
        "added_line_count": added_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Lexically prescan a fixed review context")
    parser.add_argument("--context", required=True, type=Path, help="context.json")
    parser.add_argument("--output", required=True, type=Path, help="prescan.json")
    parser.add_argument("--classification", type=Path, help="optional PR classification JSON")
    parser.add_argument("--trivial-check", action="store_true", help="exit 2 for <=3 non-code added lines")
    args = parser.parse_args()
    try:
        result = run(args.context.resolve(), args.classification.resolve() if args.classification else None)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"output": str(args.output), "files": len(result["files"]), "trivial": result["trivial"]}, ensure_ascii=False))
        return 2 if args.trivial_check and result["trivial"] else 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"type": "ERROR", "error_type": "PRESCAN_FAILED", "message": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
