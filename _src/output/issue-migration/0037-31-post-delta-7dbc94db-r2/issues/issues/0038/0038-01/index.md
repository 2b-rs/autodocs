---
schema_version: "1.0"
id: "0038-01"
level: "task"
parent: "0038"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1622"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
  - id: "AC-004"
    status: "active"
  - id: "AC-005"
    status: "active"
  - id: "AC-006"
    status: "active"
  - id: "AC-007"
    status: "active"
  - id: "AC-008"
    status: "active"
  - id: "AC-009"
    status: "active"
  - id: "AC-010"
    status: "active"
  - id: "AC-011"
    status: "active"
  - id: "AC-012"
    status: "active"
---

## Goal

Implement and document a fail-closed legacy close-Task transaction coordinator. REF: b55913571f63f42f974e37ed794626f2a10174a0 **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `tobias.anton (0038-01-Commit)`). Abgenommene Baseline `b55913571f63f42f974e37ed794626f2a10174a0`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). 23/23 Tests am eigenen REF (isolierter Scratch-Worktree) bestätigt; die 7 am gemeinsamen Tip beobachteten Fehlschläge sind nachweislich fremd (5 der 7 Tests existierten bei diesem REF noch nicht).

## Scope

- **Closed (2026-08-16):** The stdlib-only coordinator, canonical envelope renderer/linter, operator documentation, and failure-injection suite are committed. Syntax checks and all 23 focused tests passed; `python3 _src/validate.py` passed for the canonical plus ten language trees, internal links/anchors, and orphan checks.

## Acceptance criteria

- **AC-001** Add stdlib-only `_src/tools/runner_transaction.py`, hermetic tests, and `docs/pipeline/runner-transaction.md`. The versioned `close-task-v1` manifest uses fixed action IDs and exact files
- **AC-002** binds Task/request/owner/base, exact loaded manifest bytes, authority, full action/report/timeout controls, commit provenance, bookkeeping, and read/write scope to one exact claim
- **AC-003** rejects shell strings, globs, pathspecs, symlinks, role aliases, dirty shared TODO state, stale authority/base/branch/index, and runtime-evidence overlap
- **AC-004** executes generation and validation in a detached candidate
- **AC-005** fails on child nonzero or fresh structured error findings
- **AC-006** forbids generator input and validator tree mutation
- **AC-007** promotes with a durable rollback journal
- **AC-008** prepares exact no-filter blobs plus separate substantive/REF commits without the ambient index
- **AC-009** validates the final bookkeeping tree
- **AC-010** publishes once by expected-ref CAS
- **AC-011** retains the claim through durable non-passing recovery evidence
- **AC-012** and emits PASS only after exact claim archival and final verification. The canonical `run.sh` envelope contains only strict mode, fixed root, and one `exec` of this tool

## Definition of Done

Focused fixtures cover unsafe manifests/envelopes, generator/validator/structured-report failures, input/tree mutation, partial promotion rollback, dirty TODO, unrelated staged work, two-commit REF closure, post-publication interruption, CAS loss, result persistence failure, runtime alias, candidate symlink escape, dry-run, exact Task boundaries, and successful claim finalization. Syntax, focused tests, project validation, path-limited substantive commit with verbatim provenance, and separate real REF bookkeeping commit pass.
