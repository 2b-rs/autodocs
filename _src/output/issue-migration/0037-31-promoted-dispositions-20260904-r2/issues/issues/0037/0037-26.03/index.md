---
schema_version: "1.0"
id: "0037-26.03"
level: "subtask"
parent: "0037-26"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-17"
  - "0037-19"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2444"
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

PREREQ: 0037-26.03:0037-17, 0037-26.03:0037-19 Extend raw evidence and record-version writers with issue/run/campaign/artifact provenance.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve append-only source evidence/version history
- **AC-002** attach exact input artifact set, source version, producing run/campaign/tool/config, issue/criterion trigger, and evidence/privacy class
- **AC-003** never relabel synthetic fixture data as production or backfill unknown legacy context

## Definition of Done

Integration tests prove immutable raw evidence, exact version linkage, legacy-unknown handling, duplicate prevention, and reverse trace to source bytes and trigger.
