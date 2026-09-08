---
name: code-review-new
description: Use for GitHub pull request review, local staged or branch diff review, whole-repository baseline audit, security review, deep review, Manifest or bundled PR review, and Chinese requests such as "代码检视", "检视PR", "全仓检视", "深度检视", "安全检视", or "CR". Produces evidence-bound findings and never writes remotely without explicit authorization.
---

# Code Review New

GitHub-native six-phase multi-Agent review. Deterministic scripts own context, snapshots, gates, integrity, and remote I/O; Reviewer, Adversary, and Synthesizer Agents only analyze fixed artifacts.

## Modes

| Mode | Trigger | Context command | Output |
|---|---|---|---|
| GitHub PR | `https://<host>/<owner>/<repo>/pull/<n>` | `python scripts/github_context.py <url>` | dry-run payload or GitHub review |
| Local Git | staged, branch, commit, or range | `python scripts/local_context.py ...` | Markdown report |
| Local whole repository | all Git-tracked current text files | `python scripts/local_context.py --whole-repo` | Markdown baseline-audit report only |
| Manifest PR | parent PR references full PR URLs or `owner/repo#n` | `python scripts/manifest_context.py <url>` | independent sub-PR sessions + summary |

GitHub.com uses `https://api.github.com`; GitHub Enterprise defaults to `https://<host>/api/v3`. Override with `github_api_base_url`. Read the token only from the configured environment variable (`GITHUB_TOKEN` by default).

## Workflow

### 1. Context and immutable snapshot

1. Run the matching context command. Stop when `changed_files` is empty.
2. Context scripts create `.ai/code-review-new/sessions/<run>/` and write:
   - `context/context.json`, `context/diffs.json`, and existing review data;
   - fixed base/head/merge-base SHA plus diff hash. Local mode fixes base/head SHA and diff hash.
   - whole-repository mode additionally writes `context/repository-files.json`, fixes the current tracked-file content hash, and represents every included current line as an exact `[N]` anchor with `status=snapshot`.
3. GitHub PR files are fetched cumulatively with pagination. Missing/truncated patches, API file limits, or incomplete data set the snapshot to `partial`; do not publish.
4. Before any remote write run:
   ```bash
   python scripts/github_context.py --check-revision <context.json>
   ```
   Exit 2 means stale: record `stale-revision` and stop.
5. Clone failure is non-fatal; set `review_workspace.available=false` and skip deep review.
6. `--whole-repo` is Local-only. It excludes configured suffixes/globs, symlinks, binary/non-UTF-8 files, and files above `whole_repo.max_file_bytes`; record every exclusion in `repository-files.json`. It always keeps `publish_allowed=false`.

### 2. Prescan, classification, routing, and budget

1. Run trivial prescan first:
   ```bash
   python scripts/prescan.py --context <context.json> --output <prescan.json> --trivial-check
   ```
   Exit 2 means at most three added lines with no code signal; stop without spawning Agents.
2. GitHub mode only, classify the PR:
   ```bash
   python scripts/pr_classifier.py --context <context.json> --output <pr_classification.json>
   ```
   States: `skip`, `new_review`, `re_review`, `review_current`, `merge_ready`. Classification is advisory and never approves or merges.
3. Run full prescan, optionally passing classification. Read `references/prescan-rules.md` when interpreting its signals.
4. Always load `references/common.md`, `references/false-positive-avoidance.md`, `references/severity-guidelines.md`, and `references/rule-registry.md`. Load language and specialist rules using `references/review-rules-and-routing.md`.
5. Filter positive and negative runtime knowledge from `<project>/.ai/code-review-new/knowledge/` using `scripts/knowledge_manager.py`.
6. Generate `context/review_manifest.json`. Each task contains `task_id`, `dimension_id`, `scope_file_paths`, `focus`, rule paths, per-file rule IDs, `id_prefix`, and `output_path`.
   - At most 8 tasks; at most 5 Reviewer Agents concurrently, then batch.
   - `routed_files` and `unsupported_files` are disjoint and their union exactly equals `changed_files`.
   - Architecture/business tasks load only common, false-positive, registry, and their dimension rule.
   - In whole-repository mode, group the declared snapshot scope by module/language into at most 8 tasks. All included files must remain in exact manifest coverage; never silently drop files to satisfy a token estimate.
7. Run `scripts/token_estimator.py`. Reduce scope before dispatch when pipeline or task limits are exceeded; rules may consume at most 30% of a task budget.

### 3. Reviewer Agents and dispatch identity

1. Read `references/dispatch-contract.md` and initialize the run with `scripts/review_core.py init-run`; pass `--require-adversary` when enabled. This writes immutable `run.json`, the dispatch ledger, and the 30-minute deadline.
2. For every manifest task, create one Reviewer Agent using `agents/reviewer.md`. Bind the returned sender handle before sending work.
3. Reviewer writes a wrapper containing its logical `agent_id`, task/cluster ID, fixed revision, and findings. It cannot read sibling outputs or perform remote writes.
4. Capture every response with `review_core.py capture-response`. Missing/mismatched binding, sender, task, revision, or hash invalidates that assignment.
5. The 30-minute deadline stops new binding/dispatch. Late verified results remain `report_only`; remote publishing stays closed.

### 3.5. Adversarial challenge

1. Run preliminary Admission on regular Reviewer outputs:
   ```bash
   python scripts/review_admission.py --preliminary --context <context.json> --manifest <review_manifest.json>
   ```
   Admission writes separate admitted copies and never mutates raw wrappers.
2. If `adversary_enabled`, create one independent Agent using `agents/adversary.md`.
3. Verdicts are `DEFINITE`, `LIKELY`, `PLAUSIBLE`, `SPECULATIVE`: speculative is removed; plausible is downgraded one severity; the others remain.
4. A missing Adversary response may be materialized by `ensure_adversary.py` for audit continuity, but it sets `unverified-critical-step` and blocks publishing.

### 4. Deep review

Skip when no workspace. For change-based modes, run:

```bash
python scripts/deep_review_analyzer.py --context <context.json> --diffs <diffs.json> --workspace <repo> --output <call_chains.json>
```

Create deep Reviewer tasks only for `METHOD_MODIFY`, `METHOD_REMOVE`, and `INTERFACE_CHANGE`. Trace core business up to 5 levels, general business 3, infrastructure 2. Every finding still anchors to an exact `[N]` line and passes Admission.

Whole-repository mode is a baseline audit, not a change classification. Do not label snapshot symbols as `METHOD_MODIFY`. Route architecture/business/security tasks over the fixed module scope and use the workspace only to verify current reachability and call relationships; findings still anchor to snapshot `[N]` lines.

### 5. Synthesis, proof, and integrity

1. Run final `review_admission.py --context <context.json> --manifest <review_manifest.json>` after capturing the Adversary (`--no-adversary` only when the controller deliberately disabled that role). Fail closed on identity, receipt, hash, scope, rule status, severity, confidence, or `[N]` mismatch.
2. Create an independent Synthesizer using `agents/synthesizer.md`. It reads admitted outputs, verifies facts, suppresses known false positives, deduplicates by file/line/root cause, and writes `submission/review_store.json` plus `submission/defect-proofs.json`.
3. Defect Proof answers: trigger path/input/condition; actual wrong result; exact diff line plus rule.
   - Confidence 7-10 and at least 2/3 answers: `publishable`.
   - Confidence 4-6 and at least 2/3: downgrade to suggestion and `report_only`.
   - Lower confidence or fewer answers: discard.
4. If retained findings are zero and at least three files were reviewed, create an independent Agent using `agents/zero-finding-second-pass.md` and capture its receipt. Non-empty second-pass findings re-enter Admission/Adversary/Synthesis.
5. Capture the Synthesizer wrapper, then run `review_core.py verify-run --phase final` to write `submission/review-integrity.json`. Public states:
   - `complete`: fixed snapshot, complete scope, valid identities/receipts/hashes/proofs;
   - `partial`: recoverable missing/incomplete evidence; report only;
   - `blocked`: protocol violation; no output publication.

### 6. Output and feedback

GitHub submission is dry-run by default:

```bash
python scripts/submit_reviews.py <url> --review-session-dir <session>
python scripts/submit_reviews.py <url> --review-session-dir <session> --apply
```

- `--apply` requires explicit user authorization, `complete` integrity, and a current head SHA.
- Default event is `COMMENT`. `APPROVE`, `REQUEST_CHANGES`, and `--merge` require the user to explicitly request that action.
- Inline comments use fixed `commit_id`, `path`, `line`, and `side=RIGHT`.
- Never blindly retry an uncertain write. Re-read reviews/comments first and recover the receipt or deduplicate.
- Local mode renders through `render_report.py`; it never calls GitHub.
- Whole-repository mode is always `report_only`, even when integrity is `complete`.
- Update knowledge only after a `complete` run. Positive entries come from confirmed proofs; negative entries come from adversary discards and failed proofs. Defaults: 10 per category, 50 total.

## Hard boundaries

- Never invent or estimate a line; only `[N]` anchors are publishable.
- Never modify a raw Agent wrapper after capture.
- Never skip Admission, fixed-revision verification, Defect Proof, or integrity verification.
- Never publish duplicate, disabled-rule, low-confidence, diff-external, or speculative findings.
- Never let Reviewer, Adversary, or Synthesizer call GitHub write APIs.
- Never approve, request changes, or merge from classification alone.
- Never write secrets to config or session artifacts.

## Supporting references

- Routing and schemas: `references/review-rules-and-routing.md`
- Prescan behavior: `references/prescan-rules.md`
- Dispatch identity: `references/dispatch-contract.md`
- Integrity and proof: `references/integrity-artifacts.md`
- Rule status: `references/rule-registry.md`
- Comment formatting: `assets/code-review-templates.md`
