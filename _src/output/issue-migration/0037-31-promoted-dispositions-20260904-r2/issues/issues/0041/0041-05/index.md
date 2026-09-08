---
schema_version: "1.0"
id: "0041-05"
level: "task"
parent: "0041"
state: "open"
visibility: "internal"
prerequisites:
  - "0041-01"
  - "0041-02"
  - "0041-03"
  - "0041-04"
  - "0041-06"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1528"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0041-05:0041-01, 0041-05:0041-02, 0041-05:0041-03, 0041-05:0041-04, 0041-05:0041-06 Integrate the Feature and confirm the pipeline actually runs end to end. **Acceptance: ✓** (2026-09-02, Project Lead jadzia, Integration by obrien REF d1a97ca).

## Scope

- **Lifecycle reconciliation (2026-08-30):** Historical implementation evidence at `5c49801c7eae19b97c4247d28d37214cd3e6badb` and marker-only commit `65e0d24c574123b6600eb3ce50a80ab04cb3bc7f` are preserved, not accepted, erased, or reused. `DEC-0041-007` reopened `0041-02`, `0041-03`, `0041-04`, and `0041-06` for fresh current-main work, making this terminal marker depend on four nonterminal prerequisites; the historical Task line also has no visible authoritative REF and its summary retains no real end-to-end run evidence. Task `0041-05` is therefore reopened pending current completion of its unchanged prerequisite closure and a fresh end-to-end package. Evidence: `docs/campaign-evidence/0041-05/lifecycle-reconciliation-20260830.md`. This correction is not Acceptance, an integration verdict, checkpoint crossing, successor start, or Feature closure.
  - **Integration review: mandatory.** **Rationale (architect):** the Feature's integrating task and its review floor. It is the only point at which provisioning, check-in semantics, `REF` gating and the push path are examined as one workflow — and a workflow that is correct in four documents and broken in composition is exactly the failure this Feature exists to end.

## Acceptance criteria

- **AC-001** One real item is carried end to end: branch and clone provisioned by the host, work performed in the clone, published by push, marker advanced without a separate bookkeeping commit, and the canonical working tree demonstrably untouched throughout. Every requirement ID from the baseline has a disposition. Contradictions between authority documents are reported, not smoothed over

## Definition of Done

Committed; the end-to-end run is retained as evidence; no leftover `.git` symlink or stray non-conforming branch remains.
