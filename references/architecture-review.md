# Architecture review

Apply this document only to an `ARCHITECTURE` task. Findings require an exact added-line `[N]` anchor plus repository evidence; names, directory layout, or stylistic preference alone are insufficient.

## ARCH-COMPLIANCE-001: Repository instructions remain satisfied

- **Status:** active
- **Default severity:** major
- Report only when an applicable `AGENTS.md` or repository contract states a concrete invariant and the change demonstrably violates it.
- Quote the instruction and show the changed path to which it applies. Do not infer requirements from unrelated parent or sibling directories.

## ARCH-BOUNDARY-001: Preserve dependency direction and ownership

- **Status:** active
- **Default severity:** major
- Report a new dependency only when it crosses a documented layer/module boundary and creates a concrete cycle, forbidden direction, or bypass of the owning API.
- Prove both endpoints and the repository boundary. Similar names, imports alone, or a preferred design pattern are not proof.

## ARCH-COMPAT-001: Preserve externally consumed contracts

- **Status:** active
- **Default severity:** major
- Report a removed or narrowed public contract only when a reachable caller, schema consumer, persisted representation, or compatibility promise is shown to break.
- Include the changed contract and at least one affected consumer. If consumers cannot be inspected, emit `report_only` or no finding.

## Review boundary

This dimension does not repeat language style, security, test, or business-rule checks. Architecture findings describe the violated boundary, reachable consequence, and smallest compatible repair; speculative redesign advice is discarded.
