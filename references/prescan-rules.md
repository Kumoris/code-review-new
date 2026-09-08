# Prescan contract

`scripts/prescan.py` is a deterministic lexical router. It does not diagnose defects and `finding_candidates` MUST remain an empty array.

## Invocation and exit codes

```bash
python scripts/prescan.py --context context.json --output prescan.json [--classification pr_classification.json] [--trivial-check]
```

- `0`: scan completed.
- `1`: input or output error.
- `2`: scan completed, found at most three added lines, and every added or removed line is blank, delimiters, or comments. Missing patches are never trivial. The output file is still written.

Classification controls scope only: `new_review` scans every changed file; `re_review` and `review_current` use `focus_files` when supplied; `skip` and `merge_ready` scan no files. It never approves, merges, comments, or changes the snapshot.

## Output schema

```json
{
  "schema_version": 1,
  "source_sha": "fixed head SHA",
  "classification": "new_review",
  "review_scope": ["src/app.py"],
  "files": [
    {
      "path": "src/app.py",
      "language": "python",
      "always_check": {
        "hardcoded-credentials": "checked-no-signal",
        "weak-cryptography": "checked-no-signal",
        "digital-certificates": "checked-no-signal"
      },
      "security_signals": [],
      "spark_signals": [],
      "jsx_signals": null,
      "agents_md_signal": "not-found",
      "agents_md_path": null,
      "business_doc_signal": "not-found"
    }
  ],
  "finding_candidates": [],
  "trivial": false,
  "added_line_count": 1
}
```

Always-check status is exactly one of `signal`, `checked-no-signal`, `skipped-unsupported`, or `error`. Only `signal` requires the corresponding security rules. `checked-no-signal` takes precedence over broad keyword routing. `error` is fail-safe: the controller records incomplete coverage and must not publish.

## Signals

- `hardcoded-credentials`: an added literal assignment to password, secret, token, API-key, or credential names.
- `weak-cryptography`: an added use of MD5, SHA-1, DES/3DES, RC4, or ECB.
- `digital-certificates`: an added trust-all verifier or explicit TLS/certificate verification disablement.
- `security_signals`: injection/execution, authentication/authorization paths, sensitive logging, or unsafe deserialization.
- `spark_signals`: `spark-code` for Spark APIs and `spark-config` for dataset/pipeline YAML.
- `jsx_signals`: `jsx-prop-removed:<prop>` based on removed-versus-added prop names; `null` for non-JSX/TSX files.
- `agents_md_signal`: searches from the changed file's directory up to the fixed workspace root only.
- `business_doc_signal`: set when Markdown changed or the fixed workspace has `docs/` or `design/`.

Prescan examines fixed diff additions for routing. A signal is a request to load and apply the relevant rule document, not evidence for a finding.
