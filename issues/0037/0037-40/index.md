---
schema_version: "1.0"
id: "0037-40"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-36"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2549"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0037-40:0037-36 Apply the signed post-cutover closure/activation delta and lift the write freeze.

## Scope

- **DEC-0037-002 verification:** As the single terminal integrating Task, prove direct Programmer/Tester operation and a synthetic Runner long job including progress, cancellation, recovery, and the negative rule that Runner status cannot grant authority.
  - **Integration review: mandatory.** **Rationale (architect):** this is Feature `0037`'s terminal integration and activation checkpoint.

## Acceptance criteria

- **AC-001** Verify the append-only transaction-ref head by compare-and-swap, exact cutover/reference/clean-run/rollback/audit artifact digests, independent quality signature/role, and unchanged frozen issue tree. The activation commit materializes closures for `0037-35.01`, `0037-35.02`, `0037-35`, and `0037-36` and regenerates all derived views. A required follow-up reference commit records the activation hash, closes `0037-40` and Feature `0037`, regenerates `TODO.md`/`DONE.md`/catalog/graph outputs, verifies one authority, a newly incremented `issue-store-writable` instruction epoch/capability set, successful fresh-agent doctor, rejected legacy commands and all pre-activation epochs, and zero unexplained diff, and only then lifts the issue/claim write freeze. The signed authorization explicitly accepts that this is the routine legacy-rollback point of no return and names `0037-44` as the post-activation recovery path. Any mismatch leaves the freeze active and triggers frozen-window rollback/remediation

## Definition of Done

Both activation and follow-up commits match the signed delta, pass the full issue/regeneration validator from clean checkouts, move the Feature to generated `DONE.md` with real refs, and record the exact transaction-ref terminal object; no ordinary issue mutation occurs before the freeze is lifted.
