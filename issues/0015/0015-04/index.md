---
schema_version: "1.0"
id: "0015-04"
level: "task"
parent: "0015"
state: "open"
visibility: "internal"
prerequisites:
  - "0015-02"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2907"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0015-04:0015-02 Pin and record Python/Node/system-tool dependencies and external input/source identities with content hashes; verify deterministic clean-checkout restoration without moving references or undeclared environment state.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
