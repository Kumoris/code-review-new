# Dispatch Contract

The controller owns Agent identity. An Agent cannot choose or repair its own
identity metadata.

## Lifecycle

```bash
python scripts/review_core.py init-run \
  --session-dir "$SESSION" --context context.json --manifest review_manifest.json \
  --require-adversary
python scripts/review_core.py bind-agent \
  --session-dir "$SESSION" --assignment-id review:task-1 \
  --sender-handle '<orchestrator sender handle>'
python scripts/review_core.py capture-response \
  --session-dir "$SESSION" --assignment-id review:task-1 \
  --sender-handle '<same sender handle>' --response response.json
python scripts/review_admission.py --preliminary \
  --context context.json --manifest review_manifest.json
# bind/capture the Adversary, then run final Admission
python scripts/review_admission.py --context context.json --manifest review_manifest.json
# bind/capture Synthesizer and write review_store.json + defect-proofs.json
python scripts/review_core.py verify-run --phase final --session-dir "$SESSION"
```

`init-run` freezes the context, manifest, registry, ledger, revision and
30-minute deadline. It preallocates one required Reviewer assignment per
manifest task plus optional Adversary, Synthesizer and zero-finding slots.
There may be at most eight manifest tasks and five concurrent Reviewers.

`bind-agent` is the dispatch boundary. It is rejected after the deadline.
An assignment and a sender handle are both one-to-one; rebinding is allowed
only when it is byte-for-byte equivalent to the existing binding.

`capture-response` verifies the trusted sender before copying the response to
`inbox/raw/`. That copy and its receipt are immutable. Repeating the command
with the same bytes is idempotent; different bytes fail closed. A response
captured after the deadline is retained as `report_only`.

`--preliminary` verifies Reviewer receipts, identities, scope, exact `[N]`
anchors, rule status, confidence and severity. It writes derived candidates
for the Adversary but never opens publication. Final Admission requires the
configured Adversary receipt. Final `verify-run` always requires a captured
Synthesizer wrapper, exact equality between its output and
`submission/review_store.json`, and source-ID coverage in
`submission/defect-proofs.json`.

## Agent wrapper

Every response is one JSON object:

```json
{
  "schema_version": 1,
  "agent_id": "reviewer-1",
  "role": "reviewer",
  "cluster_id": "task-1",
  "revision": "fixed-head-sha",
  "output": []
}
```

`cluster_id` may be spelled `task_id`; if both are present both must exactly
match the ledger task. `output` is an array. Role-specific aliases are
accepted (`findings`, `challenges`, `review_comments`, `records`), but the raw
wrapper is never normalized or rewritten.

Reviewer task, logical Agent ID, role, revision and sender binding must all
match the ledger. Synthesizer and zero-finding Agent IDs must differ from every
Reviewer Agent ID. A missing ledger, binding or receipt is unverified and
closes publication; a mismatch is a structured blocking red flag.
