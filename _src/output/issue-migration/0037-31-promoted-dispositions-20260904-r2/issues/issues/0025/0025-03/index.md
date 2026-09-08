---
schema_version: "1.0"
id: "0025-03"
level: "task"
parent: "0025"
state: "open"
visibility: "internal"
prerequisites:
  - "0025-02"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2812"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0025-03:0025-02 Validate and freeze the ECU evidence index with artifact IDs/revisions, product/project/process/process-instance/baseline metadata, official outcome/indicator mapping, owners, authenticity, completeness, validity, confidentiality, contrary evidence, and unresolved limitations; exclude documentation-pipeline and synthetic execution evidence from ECU outcome claims.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
