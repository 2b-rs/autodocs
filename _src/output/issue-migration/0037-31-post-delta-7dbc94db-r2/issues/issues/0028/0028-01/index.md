---
schema_version: "1.0"
id: "0028-01"
level: "task"
parent: "0028"
state: "closed"
visibility: "internal"
prerequisites:
  - "0020-08"
  - "0020-09"
  - "0022-01"
  - "0027-01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2724"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0028-01:0020-08, 0028-01:0020-09, 0028-01:0022-01, 0028-01:0027-01 Establish the fail-closed `SYS.1` activation and input-authority baseline: require an append-only selected-profile/responsibility disposition, named performer and agreement/acceptance authorities, exact product/project/process-instance/baseline/revision/variant identity, controlled stakeholder-input boundary, and explicit assessed-unit outcomes before any SYS.1 evidence is produced or credited. Reject `out of scope/not rated`, `not-decided`, stale, wrong-origin, or unapproved inputs; retain negative-case validation, recovery and findings. Write only `docs/dossiers/req-0028-01-sys1-activation-and-input-contract.md`, the canonical own claim, and own bookkeeping. DoD: complete controlled record, six-case validation evidence, digests and REF; no external-source adoption, process performance, rating, Acceptance, or activation by authorship.

## Scope

- **Implements:** `DEC-0028-001` `CON-01`/`CON-02`; `DEC-0022-001`; selected-profile authority in `0020-09`.
  - **Capability/cognitive profile:** `unprivileged`, direct Git/stdlib, no network/credentials, cognitive `critical` (breadth high, depth critical, context high, ambiguity high, verification high), distinct from Architect Data and the Integrator; 60–120 minutes, CPU <2 minutes, uncertainty ±40%, risk critical.
  - **Test derivation:** activation-authority, selected-profile, input-origin and false-credit risks; manual inspection of one complete positive record and five negative records (not-rated, unnamed performer, unnamed authority, stale baseline, undefined assessed-unit outcomes).
  - **Integration review: mandatory.** **Rationale (architect):** this is the authority/security-of-claim boundary; a false pass activates a currently excluded process and changes the `0029-01` internal/shared input path.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
