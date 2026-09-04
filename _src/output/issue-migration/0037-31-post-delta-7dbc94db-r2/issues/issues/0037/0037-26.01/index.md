---
schema_version: "1.0"
id: "0037-26.01"
level: "subtask"
parent: "0037-26"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-17"
  - "0037-19"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2436"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-26.01:0037-17, 0037-26.01:0037-19 Extend scrape and extraction reports with the common provenance envelope.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Record source/tool/config commits, exact PDF/text/backend input artifact sets, issue/criterion/campaign/run refs, stable finding IDs, output reports/artifacts, trigger/cause, and evidence/privacy class
- **AC-002** failures and backend disagreement produce linked findings

## Definition of Done

Integration tests trace a report/finding to exact source bytes and trigger and reject path-only, mtime-only, fabricated, or mismatched-run provenance.
