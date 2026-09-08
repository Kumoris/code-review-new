#!/usr/bin/env python3
"""Deep review analyzer for code-review-new skill.

Analyzes diffs and cloned repository to detect change types,
trace call chains, and assess business impact.

Usage:
    python deep_review_analyzer.py --context <context.json> --diffs <diffs.json> --workspace <repo_path> --output <call_chains.json>
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def load_config() -> dict:
    """Load config.json."""
    config_paths = [
        Path.cwd() / ".code-review-new" / "config.json",
        Path(__file__).parent.parent / "config.json",
    ]
    for p in config_paths:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    return {}


def analyze_file_changes(diffs: list) -> list:
    """Identify the method/interface changes eligible for deep review."""
    results = []

    for diff_entry in diffs:
        file_path = diff_entry.get("file_path", "")
        content = diff_entry.get("content", [])
        file_language = detect_language(file_path)

        marked = []
        for raw in content if isinstance(content, list) else str(content).splitlines():
            match = re.match(r"^\[([NO])(\d+)\](.*)$", str(raw))
            if match:
                marked.append((match.group(1), int(match.group(2)), match.group(3).strip()))
        old = {symbol: (line, code) for marker, line, code in marked if marker == "O"
               if (symbol := extract_symbol_from_code(code, file_language))}
        new = {symbol: (line, code) for marker, line, code in marked if marker == "N"
               if (symbol := extract_symbol_from_code(code, file_language))}
        changes = [
            {"symbol": symbol, "line": line, "code_snippet": code[:160], "change_types": ["METHOD_MODIFY"]}
            for symbol, (line, code) in new.items() if symbol in old
        ]
        changes.extend(
            {"symbol": symbol, "line": None, "old_line": old_line,
             "code_snippet": code[:160], "change_types": ["METHOD_REMOVE"]}
            for symbol, (old_line, code) in old.items() if symbol not in new
        )
        for marker, line, code in marked:
            interface = re.search(r"\binterface\s+(\w+)", code)
            if interface:
                changes.append({"symbol": interface.group(1), "line": line if marker == "N" else None,
                                "old_line": line if marker == "O" else None, "code_snippet": code[:160],
                                "change_types": ["INTERFACE_CHANGE"]})
        if not changes:
            continue
        risk_level = "HIGH" if any(
            set(change["change_types"]) & {"METHOD_REMOVE", "INTERFACE_CHANGE"} for change in changes
        ) else "MEDIUM"
        results.append({"file_path": file_path, "language": file_language,
                        "changes": changes, "risk_level": risk_level})

    return results


def detect_language(file_path: str) -> str:
    """Detect programming language from file extension."""
    ext_map = {
        ".java": "java",
        ".py": "python",
        ".go": "go",
        ".js": "javascript",
        ".ts": "typescript",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
    }
    ext = Path(file_path).suffix.lower()
    return ext_map.get(ext, "unknown")


def classify_change(code: str, language: str) -> list:
    """Compatibility helper for callers that classify one added signature."""
    if re.search(r"\binterface\s+\w+", code):
        return ["INTERFACE_CHANGE"]
    return ["METHOD_MODIFY"] if extract_symbol_from_code(code, language) else ["CODE_CHANGE"]


def grep_in_repo(repo_path: str, pattern: str, file_filter: str = "") -> list:
    """Search source text with stdlib regex and bounded evidence."""
    try:
        compiled = re.compile(pattern)
        matches = []
        scanned = 0
        for path in Path(repo_path).rglob(file_filter or "*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            scanned += 1
            if scanned > 10_000:  # ponytail: use a code index if this measured ceiling is insufficient.
                break
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for number, line in enumerate(lines, 1):
                if compiled.search(line):
                    matches.append({"file": str(path), "line": str(number), "content": line})
                    if len(matches) >= 50:
                        return matches
        return matches
    except (OSError, re.error):
        return []


def trace_call_chain(symbol_name: str, repo_path: str, language: str, max_depth: int = 3) -> list:
    """Trace callers of a symbol using grep-based search.

    Returns list of call chain nodes.
    """
    chain = []
    visited = set()

    def _trace(current_symbol: str, depth: int):
        if depth > max_depth or current_symbol in visited:
            return
        visited.add(current_symbol)

        # Search for callers
        if language == "java":
            # Search for method calls: symbolName(
            pattern = re.escape(current_symbol) + r"\s*\("
            file_filter = "*.java"
        elif language == "python":
            pattern = re.escape(current_symbol) + r"\s*\("
            file_filter = "*.py"
        elif language == "go":
            pattern = r"\." + re.escape(current_symbol) + r"\s*\("
            file_filter = "*.go"
        else:
            pattern = re.escape(current_symbol) + r"\s*\("
            file_filter = ""

        matches = grep_in_repo(repo_path, pattern, file_filter)

        for match in matches[:5]:  # Limit direct callers
            caller_file = match["file"]
            # Try to extract caller method from context
            caller_name = extract_enclosing_symbol(caller_file, int(match["line"]), language)
            if caller_name and caller_name != current_symbol:
                chain.append({
                    "depth": depth,
                    "caller": caller_name,
                    "file": caller_file,
                    "line": match["line"],
                    "caller_type": "direct" if depth == 1 else "indirect",
                })
                _trace(caller_name, depth + 1)

    _trace(symbol_name, 1)
    return chain


def extract_enclosing_symbol(file_path: str, target_line: int, language: str) -> str:
    """Try to determine the enclosing method/function name for a line in a file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        # Search backwards from target_line for method/function definition
        for i in range(target_line - 1, max(0, target_line - 30), -1):
            line = lines[i].strip()
            if language == "java":
                m = re.search(r"(?:public|private|protected)\s+\S+\s+(\w+)\s*\(", line)
                if m:
                    # Try to get class name too
                    class_name = extract_class_name(lines, i, language)
                    return f"{class_name}.{m.group(1)}" if class_name else m.group(1)
            elif language == "python":
                m = re.search(r"def\s+(\w+)\s*\(", line)
                if m:
                    return m.group(1)
            elif language == "go":
                m = re.search(r"func\s+(?:\(\w+\s+\*?\w+\)\s*)?(\w+)\s*\(", line)
                if m:
                    return m.group(1)

        return ""
    except Exception:
        return ""


def extract_class_name(lines: list, line_index: int, language: str) -> str:
    """Extract class name from lines before the given index."""
    for i in range(line_index, max(0, line_index - 50), -1):
        line = lines[i].strip()
        if language == "java":
            m = re.search(r"(?:public\s+)?class\s+(\w+)", line)
            if m:
                return m.group(1)
    return ""


def resolve_workspace_path(workspace: str, context_path: str = "") -> str:
    """Resolve workspace path for cross-platform compatibility.

    On Windows with Git Bash, /opt/... gets translated to the Git install dir
    before Python receives it. This function reads the actual path from
    context.json (written by repo_manager.py) which contains the correct path.
    """
    p = Path(workspace)
    if p.exists():
        return str(p)

    # Try reading workspace path from context.json (authoritative source)
    if context_path and Path(context_path).exists():
        try:
            with open(context_path, "r", encoding="utf-8") as f:
                context = json.load(f)
            ctx_workspace = context.get("metadata", {}).get("review_workspace", {})
            ctx_path = ctx_workspace.get("path", "")
            if ctx_path and Path(ctx_path).exists():
                return ctx_path
        except Exception:
            pass

    # On Windows, try drive-relative path: /opt/... → C:\opt\...
    import os
    if os.name == "nt":
        drive = os.path.splitdrive(os.getcwd())[0]
        # Strip any Git Bash prefix (e.g., D:/install/git/Git/)
        parts = workspace.replace("\\", "/").split("/")
        # Find /opt/ or similar Unix-style path start
        for i, part in enumerate(parts):
            if part in ("opt", "home", "tmp", "var") and i > 0:
                unix_tail = "/".join(parts[i:])
                windows_path = drive + "\\" + unix_tail.replace("/", "\\")
                if Path(windows_path).exists():
                    return windows_path

    return workspace  # Return as-is, will fail the exists() check


def main():
    parser = argparse.ArgumentParser(description="Deep review analyzer")
    parser.add_argument("--context", required=True, help="Path to context.json")
    parser.add_argument("--diffs", required=True, help="Path to diffs.json")
    parser.add_argument("--workspace", required=True, help="Path to cloned repository")
    parser.add_argument("--output", required=True, help="Output path for call_chains.json")
    args = parser.parse_args()

    config = load_config()
    deep_review_config = config.get("deep_review_call_chain_depth", {
        "core_business": 5, "general_business": 3, "infrastructure": 2
    })

    # Resolve workspace path for cross-platform compatibility
    workspace = resolve_workspace_path(args.workspace, args.context)

    # Check workspace exists
    if not Path(workspace).exists():
        print(json.dumps({
            "status": "ERROR",
            "message": f"Workspace not found: {workspace} (original: {args.workspace})",
            "results": [],
        }))
        sys.exit(1)

    # Load diffs
    with open(args.diffs, "r", encoding="utf-8") as f:
        diffs = json.load(f)

    # Analyze change types
    file_analyses = analyze_file_changes(diffs)

    # For high-risk changes, trace call chains
    results = []
    for analysis in file_analyses:
        file_path = analysis["file_path"]
        language = analysis["language"]
        risk_level = analysis["risk_level"]

        # Determine max depth based on risk level
        if risk_level == "HIGH":
            max_depth = deep_review_config.get("core_business", 5)
        elif risk_level == "MEDIUM":
            max_depth = deep_review_config.get("general_business", 3)
        else:
            max_depth = deep_review_config.get("infrastructure", 2)

        # Extract changed symbols and trace call chains
        call_chains = []
        for change in analysis["changes"]:
            line_num = change["line"]
            code = change["code_snippet"]

            symbol = change.get("symbol") or extract_symbol_from_code(code, language)
            if not symbol:
                continue

            chain = trace_call_chain(symbol, workspace, language, max_depth)
            call_chains.append({
                "changed_symbol": symbol,
                "line": line_num,
                "change_types": change["change_types"],
                "call_chain": chain,
            })

        # Business impact assessment
        business_impact = assess_business_impact(call_chains, risk_level)

        results.append({
            "file_path": file_path,
            "language": language,
            "risk_level": risk_level,
            "call_chains": call_chains,
            "business_impact": business_impact,
        })

    # Write output
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(json.dumps({
        "status": "SUCCESS",
        "files_analyzed": len(results),
        "high_risk_count": sum(1 for r in results if r["risk_level"] == "HIGH"),
        "output": args.output,
    }, ensure_ascii=False, indent=2))


def extract_symbol_from_code(code: str, language: str) -> str:
    """Extract the primary symbol (method/function name) from a code line."""
    if language == "java":
        m = re.search(
            r"(?:(?:public|private|protected|static|final|abstract|synchronized|native)\s+)+"
            r"[\w<>\[\],.?]+\s+(\w+)\s*\(",
            code,
        )
        if m:
            return m.group(1)
    elif language == "python":
        m = re.search(r"def\s+(\w+)\s*\(", code)
        if m:
            return m.group(1)
    elif language == "go":
        m = re.search(r"func\s+(?:\(\w+\s+\*?\w+\)\s*)?(\w+)\s*\(", code)
        if m:
            return m.group(1)
    elif language in {"javascript", "typescript"}:
        m = re.search(r"(?:function\s+|(?:async\s+)?)([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*(?:\{|=>)", code)
        if m:
            return m.group(1)
    elif language in {"c", "cpp"}:
        m = re.search(r"[\w:*&<>]+\s+(\w+)\s*\([^;]*\)\s*(?:\{|$)", code)
        if m:
            return m.group(1)
    return ""


def assess_business_impact(call_chains: list, risk_level: str) -> dict:
    """Assess business impact based on call chain analysis."""
    affected_modules = set()
    for chain in call_chains:
        for node in chain.get("call_chain", []):
            # Extract module from file path
            parts = Path(node["file"]).parts
            if "src" in parts:
                src_idx = parts.index("src")
                if src_idx + 1 < len(parts):
                    affected_modules.add(parts[src_idx + 1])

    consequences = []
    if risk_level == "HIGH":
        consequences.append("核心业务流程可能受影响，需重点关注调用链上所有节点的兼容性")
    elif risk_level == "MEDIUM":
        consequences.append("部分业务功能可能受影响，需验证调用方的适配情况")
    else:
        consequences.append("影响范围有限，建议确认变更无副作用")

    return {
        "affected_modules": list(affected_modules),
        "risk_level": risk_level,
        "potential_consequences": consequences,
    }


if __name__ == "__main__":
    main()
