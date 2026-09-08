---
schema_version: "1.0"
id: "0018-04"
level: "task"
parent: "0018"
state: "closed"
visibility: "internal"
prerequisites:
  - "0015-10"
  - "0018-02"
  - "0018-03"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2956"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0018-04:0015-10, 0018-04:0018-02, 0018-04:0018-03 Validate and freeze the pre-assessment ECU evidence index, including artifact IDs/revisions, product/project/process/process-instance/baseline and origin metadata, process/outcome/attribute mapping, owners, authenticity, completeness, confidentiality, and unresolved limitations; interview records are added/versioned during assessment.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
