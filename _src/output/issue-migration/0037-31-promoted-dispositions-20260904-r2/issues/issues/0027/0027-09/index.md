---
schema_version: "1.0"
id: "0027-09"
level: "task"
parent: "0027"
state: "open"
visibility: "internal"
prerequisites:
  - "0027-07"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2692"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0027-09:0027-07 Operate `SUP.9` on representative real ECU problems through verified closure and status/trend reporting. A scenario may qualify the mechanism but cannot satisfy ECU execution; if no representative problem exists in the approved observation period, keep the execution gate open and obtain an assessor-approved sampling/observation extension.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
