# Integrity Artifacts

All paths below are relative to a review session.

| Artifact | Owner | Mutability |
|---|---|---|
| `run.json` | controller | immutable |
| `integrity/dispatch-ledger.json` | controller | immutable |
| `integrity/dispatch-bindings.json` | controller | append by binding command |
| `inbox/raw/<assignment>.json` | capture command | immutable |
| `integrity/receipts/<assignment>.json` | capture command | immutable |
| `integrity/receipt-chain.json` | capture command | append-only logical chain |
| `admission/reviewers/<task>.json` | admission gate | derived, replaceable |
| `admission/rejections/<task>.json` | admission gate | derived, replaceable |
| `submission/defect-proofs.json` | Synthesizer | derived |
| `submission/review-integrity.json` | controller/admission | derived public status |
| `context/repository-files.json` | Local whole-repo context | immutable after `init-run` |

`run.json` pins SHA-256 digests for the context, referenced diff, manifest,
rule registry and dispatch ledger. Each receipt pins the exact raw response bytes, trusted
sender handle, assignment and previous receipt hash. Any mismatch raises
`integrity-artifact-mismatch` and blocks remote output.

For Local whole-repository runs, `run.json` also pins `repository-files.json`.
The run revision is the repository content-manifest SHA-256 rather than only the Git HEAD,
so dirty tracked working-tree content remains bound to the captured snapshot.

## Public states

- `complete`: required artifacts, identities, coverage and hashes verify.
- `partial`: an artifact/receipt is missing, input is partial, or the
  Adversary fallback was needed.
- `blocked`: a structured mismatch, spoof, scope drift or stale revision was
  confirmed.

Only `complete` can publish. Expiry does not destroy verified work: it changes
`publication_mode` to `report_only` and closes `publish_allowed`.

## Defect Proof and zero findings

The proof keys are `trigger`, `wrong_result`, and `diff_rule_evidence`.
High-confidence findings (7-10) need two answered keys. Medium confidence
(4-6) also needs two but becomes `suggestion/report_only`; lower scores are
discarded. A `review-required` rule needs all three keys explicitly supplied.

If Reviewer/Admission output is empty for a scope of three or more changed
files, capture a `zero-finding-second-pass` wrapper and receipt. Its Agent and
sender must be independent of the first-pass Reviewers. Missing independent
evidence leaves the run `partial`. A non-empty second-pass output also remains
`partial`; start a new Admission, Adversary and Synthesis cycle for those
findings before a new final verification.
