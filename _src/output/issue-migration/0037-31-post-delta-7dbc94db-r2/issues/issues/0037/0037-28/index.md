---
schema_version: "1.0"
id: "0037-28"
level: "task"
parent: "0037"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-16"
  - "0037-25"
  - "0037-26"
  - "0037-27"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2484"
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
---

## Goal

PREREQ: 0037-28:0037-16, 0037-28:0037-25, 0037-28:0037-26, 0037-28:0037-27 Demonstrate the complete causal graph with a hermetic replay of the real Feature `0034-03` Persistency-label defect fixed by commit `7b2b572ab18ecab29e7e6fd9704b9b85e7b806ab`.

## Scope

### Campaign E — Shadow Migration, Cutover, Regeneration, and Closure

## Acceptance criteria

- **AC-001** Materialize pre-fix and fix Git blobs plus the `RS_PER_00010`/`RS_PER_00021` test source into temporary record/version/queue/output roots
- **AC-002** replay the migrated `0034-03` issue/criterion, scrape/report stable finding, real fix commit, re-scrape/database rebuild, evidence/version change, dependent AI/diagram/guide/i18n/HTML invalidation/regeneration, validation, and release evidence. Mark every fixture artifact `development-test`
- **AC-003** use no production root, network, current working-tree mutation, or fake Git commit
- **AC-004** query every edge in both directions and retain source/finding/fix/rebuild/regeneration relations

## Definition of Done

Clean-checkout test retains machine/Markdown trace reports, pre/post artifact sets, graph assertions, and production-root mutation guards; it verifies the real commit object and exact fixture inputs without relying on free-form commit-message text.
