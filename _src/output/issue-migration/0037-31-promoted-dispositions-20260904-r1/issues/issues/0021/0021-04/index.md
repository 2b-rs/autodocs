---
schema_version: "1.0"
id: "0021-04"
level: "task"
parent: "0021"
state: "open"
visibility: "internal"
prerequisites:
  - "0021-01"
  - "0021-02"
labels:
  - "legacy-terminal-unverified"
  - "archived-not-accepted"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:334"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0021-04:0021-01, 0021-04:0021-02 Design the record-page interaction, confirmation, and accessibility behavior for requesting re-review. REF: 25eef65b

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** The UX defines the action placement for valid and non-valid records, required rationale/category fields, optional evidence references, current record/version/status disclosure, consent/trust disclosure, confirmation behavior, success/error/stale states, keyboard operation, focus management, mobile layout, and the no-JavaScript fallback transport/confirmation/failure behavior
- **AC-002** terminology makes clear that a request does not alter the record immediately

## Definition of Done

Approved UI contract is recorded in authoritative pipeline/UI documentation; testable acceptance scenarios cover standard, valid-curated, stale, duplicate, and submission-failure paths.
