---
schema_version: "1.0"
id: "0015-05"
level: "task"
parent: "0015"
state: "open"
visibility: "internal"
prerequisites:
  - "0015-03"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2908"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0015-05:0015-03 Wire campaign manifests, append-only requirement versions, and lifecycle validation into real extraction/ingest/publication writers; segregate synthetic fixtures from production stores.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
