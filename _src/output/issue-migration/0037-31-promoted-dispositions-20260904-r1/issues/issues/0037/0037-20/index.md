---
schema_version: "1.0"
id: "0037-20"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-06"
  - "0037-14"
  - "0037-15"
  - "0037-16"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2371"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-20:0037-06, 0037-20:0037-14, 0037-20:0037-15, 0037-20:0037-16 Prepare `docs/pipeline/issue-migration-record.md` as a bounded rationale/record, not a permanent canonical migration procedure.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Explain why monolithic lists/copied claims are replaced, selected paths and rejected alternatives, source/candidate/cutover authority conditions, moving-database strategy, report/approval/rollback evidence, known limitations, and retained history. Required pre-cutover fields are conspicuous placeholders and never presented as actual values
- **AC-002** future maintainers are directed to lifecycle/regeneration docs rather than obsolete one-time commands

## Definition of Done

Review-ready record contains no unsupported success claim; `0037-34.02` fills source/candidate/approval/patch identities and actual UTC time in the authority-switch commit, while the resulting cutover commit hash is added only by the required follow-up reference commit.
