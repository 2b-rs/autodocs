---
schema_version: "1.0"
id: "0041"
level: "feature"
state: "open"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1310"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Worker Isolation by Clone/Push and Simplified Check-in Semantics

## Scope

Imported Feature body is retained via source locators; child Tasks are separate items.

## Acceptance criteria

- **AC-001** Preserve Feature identity and archive classification from the legacy source.

## Definition of Done

Feature identity, archive class, and locators match the source blobs.
