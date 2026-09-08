---
schema_version: "1.0"
id: "0037-24"
level: "task"
parent: "0037"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-24.01"
  - "0037-24.02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2399"
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

PREREQ: 0037-24:0037-24.01, 0037-24:0037-24.02 Complete issue-title and graph-UI internationalization under the approved policy.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Translation records are keyed by stable issue/UI identity plus source hash
- **AC-002** no identity-bearing token is translated
- **AC-003** all language requirements derive dynamically from `_src/site.json`

## Definition of Done

Both Subtasks pass fixture-level completeness, stale-source, protected-token, LTR/RTL, and language-local-link tests and may report production translations incomplete; only `0037-38` may make the repository-wide all-language completeness gate pass.
