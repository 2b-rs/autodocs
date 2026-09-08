---
schema_version: "1.0"
id: "0015-06"
level: "task"
parent: "0015"
state: "open"
visibility: "internal"
prerequisites:
  - "0015-03"
  - "0015-04"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2909"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0015-06:0015-03, 0015-06:0015-04 Establish a controlled immutable evidence repository for runner scripts/logs, all correlated subreports, test/QA results, decisions, approvals, and release records; replace reliance on ignored transient `output/` evidence.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
