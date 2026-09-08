# Rule Registry

This registry is the publication status source of truth. `review_admission.py`
uses the most-specific matching selector; an exact rule ID wins over a
wildcard. A finding that cites a `disabled` rule is rejected.

| Rule selector | Status | Publication requirement |
|---|---|---|
| `ARCH-COMPLIANCE-001` | active | Defect Proof 2/3 |
| `ARCH-BOUNDARY-001` | review-required | Explicit Defect Proof 3/3 |
| `ARCH-COMPAT-001` | review-required | Explicit Defect Proof 3/3 |
| `BIZ-DESIGN-001` | active | Defect Proof 2/3 |
| `BIZ-SCENARIO-001` | review-required | Explicit Defect Proof 3/3 |
| `BIZ-DATA-001` | review-required | Explicit Defect Proof 3/3 |
| `DEEP-*` | review-required | Explicit Defect Proof 3/3 |
| `*` | active | Defect Proof 2/3 |

Valid statuses are:

- `active`: eligible after the ordinary Defect Proof gate.
- `review-required`: eligible only with three explicit proof answers.
- `disabled`: negative guard; it cannot create a finding.
- `report_only`: retained in local artifacts but never remotely published.

Changing a status changes behavior immediately and therefore requires a new
`init-run`; the run pins this file's SHA-256 digest.
