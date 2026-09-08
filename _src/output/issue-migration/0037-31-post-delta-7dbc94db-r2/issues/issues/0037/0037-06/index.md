---
schema_version: "1.0"
id: "0037-06"
level: "task"
parent: "0037"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-06.01"
  - "0037-06.02"
  - "0037-06.03"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2059"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0037-06:0037-06.01, 0037-06:0037-06.02, 0037-06:0037-06.03 Complete the review-ready moving-database, cutover, and rollback strategy. REF: aa885257d0ce9dda9833c708ed37647404308464

## Scope

- **Acceptance:** ✓ (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `tobias.anton (0037-06-Commit)`). Abgenommene Baseline `aa885257d`; Teil der durch Checkpoint `0038-30` induzierten prerequisite-closed Batch. Review-REF `a995f9047`. doc-only, drei referenzierte Quelldateien real vorhanden.
  - **Claim (2026-08-16):** Claimed by sandboxed agent `perplexity` via `TODO-perplexity-0037-06-20260816-1431.md`, `owner_token: agent:perplexity:0037-06:0037-06-20260816-1431`, request ID `0037-06-20260816-1431`, `base_commit: pending-discovery`. All three subtasks are terminal.

## Acceptance criteria

- **AC-001** Full re-import, schema transformation, authorized event replay, authority switch, and rollback have disjoint inputs/outputs and no last-writer-wins behavior

## Definition of Done

All three Subtasks are complete and included in the architecture review package.
