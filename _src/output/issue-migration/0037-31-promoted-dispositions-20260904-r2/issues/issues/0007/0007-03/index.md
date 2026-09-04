---
schema_version: "1.0"
id: "0007-03"
level: "task"
parent: "0007"
state: "open"
visibility: "internal"
prerequisites:
  - "0007-01"
  - "0007-02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:3072"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
  - id: "AC-004"
    status: "active"
---

## Goal

PREREQ: 0007-03:0007-01, 0007-03:0007-02 Conduct an independent review of the candidate truth set, source evidence, completeness/exclusion dispositions, shape coverage, known limits, and reproducibility, and obtain approval for its use as a regression oracle without allowing the preparer to self-approve.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** The reviewer is identified and sufficiently independent/competent
- **AC-002** every material finding is closed with an owner/disposition
- **AC-003** the approving decision identifies the exact candidate version/hash and accepted limitations. A rejection or returned finding keeps this task `[p]` and triggers remediation/re-review
- **AC-004** it does not unblock `0007-04`

## Definition of Done

A signed or otherwise authenticated approval record and closed-finding report are committed. Set this task to `[u]` only when the candidate is ready and the independent human decision is the next action.
