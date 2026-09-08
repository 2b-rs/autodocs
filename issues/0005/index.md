---
schema_version: "1.0"
id: "0005"
level: "feature"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:113"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Review & Feedback

## Scope

Imported Feature body is retained via source locators; child Tasks are separate items.

## Acceptance criteria

- **AC-001** Preserve Feature identity and archive classification from the legacy source.

## Definition of Done

Feature identity, archive class, and locators match the source blobs.
