---
schema_version: "1.0"
id: "0018-10"
level: "task"
parent: "0018"
state: "closed"
visibility: "internal"
prerequisites:
  - "0018-09"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2962"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0018-10:0018-09 Confirm the CL2 claim gate separately for every declared target process and authorize/publish the exact bounded claim only when `PA 1.1 = F`, `PA 2.1 = L` or `F`, and `PA 2.2 = L` or `F`, with no averaging across attributes or processes. Closing or publishing an unsuccessful pilot without a CL2 claim does not satisfy this task, and the claim must not imply safety, cybersecurity, regulatory, or product certification.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** The gate uses the approved scope, process instances, evidence baseline, assessment method, and authorized ratings
- **AC-002** any missing process/attribute result, unsupported aggregation, invalid evidence, or blocking limitation fails it

## Definition of Done

A versioned independent-readiness and management-authorization record supports the exact bounded claim, and the authorized claim/profile is published and committed with its evidence references.
