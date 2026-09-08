---
schema_version: "1.0"
id: "0015-02"
level: "task"
parent: "0015"
state: "open"
visibility: "internal"
prerequisites:
  - "0015-01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2905"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0015-02:0015-01 Define per-type content/metadata/quality requirements and review/approval, identification, status, access, storage, distribution, versioning, baselining, backup/recovery, retention, archival, disposal, license, and sensitivity controls.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
