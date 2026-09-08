# Business behavior review

Apply this document only to a `BUSINESS` task. Review the changed behavior against evidence in the fixed workspace or supplied design material. Do not invent product requirements.

## BIZ-DESIGN-001: Implement explicit design requirements completely

- **Status:** active
- **Default severity:** major
- Report only when an applicable design/specification states a concrete requirement and the changed path omits or contradicts it.
- Cite the requirement, the exact added-line anchor, and the observable mismatch. Stale or unrelated documents are not evidence.

## BIZ-SCENARIO-001: Preserve reachable business scenarios

- **Status:** active
- **Default severity:** major
- Report when a changed branch leaves a supported, reachable scenario with a wrong result, missing transition, or unhandled failure.
- Prove the triggering input/state and resulting behavior. A hypothetical scenario without a current caller or contract is `report_only` at most.

## BIZ-DATA-001: Preserve business data semantics

- **Status:** active
- **Default severity:** major
- Report when filtering, mapping, aggregation, ordering, deduplication, or persistence changes demonstrably lose, duplicate, corrupt, or misattribute business data.
- Show the before/after data path and the affected invariant; performance preference without correctness impact belongs elsewhere.

## Review boundary

Business review does not restate general code quality or architecture advice. Every finding must identify the current scenario, concrete impact, and a minimally scoped fix or verification step. When design evidence and code disagree ambiguously, request clarification without publishing a defect.
