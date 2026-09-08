---
schema_version: "1.0"
id: "0037-26"
level: "task"
parent: "0037"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-26.01"
  - "0037-26.02"
  - "0037-26.03"
  - "0037-26.04"
  - "0037-26.05"
  - "0037-26.06"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2432"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-26:0037-26.01, 0037-26:0037-26.02, 0037-26:0037-26.03, 0037-26:0037-26.04, 0037-26:0037-26.05, 0037-26:0037-26.06 Complete provenance-envelope integration for extraction, campaign, evidence/database, curation, and build producers.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Every producer in the exact file/call-site/schema inventory approved by `0037-37` records issue/criterion/run/campaign inputs and output artifact sets without inventing legacy history
- **AC-002** each Subtask changes only its enumerated producer family and all adapters use the shared schemas and query indexes

## Definition of Done

All six Subtasks pass cross-producer reverse-trace and backward-disposition tests.
