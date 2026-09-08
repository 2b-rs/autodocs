---
schema_version: "1.0"
id: "0037-40"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites: []
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

PREREQ: none (DEC-0037-038 bounded one-sequence waiver) Apply the signed post-cutover closure/activation delta and lift the write freeze.

## Scope

- **DEC-0037-002 verification:** As the single terminal integrating Task, prove direct Programmer/Tester operation and a synthetic Runner long job including progress, cancellation, recovery, and the negative rule that Runner status cannot grant authority.
  - **Integration review: mandatory.** **Rationale (architect):** this is Feature `0037`'s terminal integration and activation checkpoint.

## Acceptance criteria

- **AC-001** For the one sequence authorized by `DEC-0037-038`, bind the activation manifest to the exact base/tree, expected append-only transaction head, authored/generated delta, and Management authority using the configured Git SSH commit signature verified against `issues/_policy/allowed_signers`. Increment the workflow version and bind the `issue-store-writable` epoch, matching write phase, instruction-member hash, and selector digest. Verify exactly one readable issue-store authority, real deterministic regeneration with a second no-op, successful fresh-agent doctor, stale/legacy expectation rejection, and legacy-write rejection with unchanged bytes. Generate only real mapped outputs. `0037-35.01`, `0037-35.02`, `0037-35`, and `0037-36` are not prerequisites for this sequence: retain their findings and outstanding, unpassed/unaccepted assurance without materializing their closures. A separate signed reference commit binds the actual activation OID and results; ordinary writers remain quiescent until both commits are independently reviewed and integrated and the minimum controls pass. The assigned Integrator performs transaction compare-and-swap and integration verification. Neither this sequence nor the waiver grants Task Acceptance or closes Feature `0037`. Preserve all refs, commits, evidence, and new data; use additive correction/re-freeze and the `0037-44` recovery path. The waiver expires on completion, abandonment, or earlier explicit revocation of this sequence; later retries or materially changed candidates require fresh authority.

## Definition of Done

Both activation and follow-up commits match the authorized delta and record the minimum-control results and exact transaction-ref terminal object. Ordinary issue/claim writes remain quiescent until integration of both commits and successful minimum controls. Remaining regeneration, rollback, package, and audit assurance is recorded as subsequent work after writing is enabled, retaining every red finding. Feature `0037` remains open; full assurance and separate Acceptance/Feature closure are not claimed through `DEC-0037-038`.
