---
schema_version: "1.0"
id: "0037-25.02"
level: "subtask"
parent: "0037-25"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-25.01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2424"
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
---

## Goal

PREREQ: 0037-25.02:0037-25.01 Implement run-scoped staging and realizable immutable-tree promotion.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Build every declared output below a run-specific temporary root
- **AC-002** validate the complete artifact set
- **AC-003** write one immutable Git tree object/index for repository outputs and one versioned release-directory tree for deployed HTML/assets. Repository publication is one reviewed commit/tree switch
- **AC-004** deployment publication is one atomic `current` pointer switch within a filesystem after full validation. Readers verify one content-generation ID and reject mixed/stale trees
- **AC-005** no sequence of unrelated destination renames is described as multi-path atomicity. Preserve modes, retain the prior tree/pointer for rollback, and clean staging only after recorded success

## Definition of Done

Injected failures at every stage/tree-write/pointer boundary leave the prior published tree selected or the complete new tree selected, with deterministic recovery, reader rejection of forced mixed fixtures, and no authoritative-source mutation.
