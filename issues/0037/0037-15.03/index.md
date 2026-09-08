---
schema_version: "1.0"
id: "0037-15.03"
level: "subtask"
parent: "0037-15"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-06.02"
  - "0037-14"
  - "0037-17.01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2352"
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

PREREQ: 0037-15.03:0037-06.02, 0037-15.03:0037-14, 0037-15.03:0037-17.01 Implement exactly-once authorized event replay and conflict reporting over fresh shadow candidates.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Replay immutable IDs only after base/source/item compatibility and authority validation
- **AC-002** preserve independent provenance outside shadow items
- **AC-003** reject collisions, stale bases, deleted targets, concurrent claims, and events that mutate imported text/state
- **AC-004** emit stable findings with explicit disposition rather than last-writer-wins

## Definition of Done

Tests cover compatible replay, duplicate replay, collision, deletion, stale base, unauthorized event, changed item, and zero loss after full re-import.
