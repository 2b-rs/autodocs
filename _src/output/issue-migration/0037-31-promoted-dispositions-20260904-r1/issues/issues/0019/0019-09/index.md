---
schema_version: "1.0"
id: "0019-09"
level: "task"
parent: "0019"
state: "open"
visibility: "internal"
prerequisites:
  - "0019-08"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:3023"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

PREREQ: 0019-09:0019-08 Generate and validate the curator-authorized S-Core v0.6.0 views.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Only records authorized by `0019-08` are rendered into the HTML tree with record history, canonical/version identity, provenance/traceability, and review indicators
- **AC-002** invalid/hypothesized/unresolved records remain excluded from factual publication while visible in curation/review reports
- **AC-003** all language-tree, DOM, link, and client-rendered validation checks pass

## Definition of Done

A clean generation is repeatable with zero semantic differences; report counts reconcile exactly with the authorized corpus, campaign validation report, and queue snapshot; screenshots/DOM assertions cover at least one record of every kind and one unresolved case.
