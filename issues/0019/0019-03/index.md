---
schema_version: "1.0"
id: "0019-03"
level: "task"
parent: "0019"
state: "open"
visibility: "internal"
prerequisites:
  - "0019-01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2995"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

PREREQ: 0019-03:0019-01 Define and test the S-Core import profile: source selectors, supported artifact classes, field mapping, status defaults, and explicit non-goals.

## Scope

### Campaign B — Extraction and Normalization

## Acceptance criteria

- **AC-001** A versioned import-profile document/config maps each supported source class to `module`, `component`, `design-doc`, or `process-doc`
- **AC-002** it identifies mandatory fields, source locators, status/traceability defaults, duplicate/conflict behavior, and conditions that must create a review/curation item
- **AC-003** sample artifacts from every in-scope repository demonstrate the mapping

## Definition of Done

Profile is reviewed against `score-identity-scheme.md`, `data-model.md`, `status-model.md`, and `processes.md`; automated fixtures cover every supported class and every defined rejection/queue condition.
