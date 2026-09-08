---
schema_version: "1.0"
id: "0037-31"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-20"
  - "0037-25"
  - "0037-28"
  - "0037-29"
  - "0037-30"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2504"
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
  - id: "AC-005"
    status: "active"
  - id: "AC-006"
    status: "active"
  - id: "AC-007"
    status: "active"
  - id: "AC-008"
    status: "active"
---

## Goal

PREREQ: 0037-31:0037-20, 0037-31:0037-25, 0037-31:0037-28, 0037-31:0037-29, 0037-31:0037-30 Produce the final frozen migration candidate and reconciliation evidence without switching authority.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Freeze legacy writes at a named source commit with zero active claims
- **AC-002** clean-import with approved schema/tool
- **AC-003** include final committed Feature `0037`
- **AC-004** replay only authorized provenance events
- **AC-005** regenerate every declared view/graph/i18n/page/HTML artifact and report
- **AC-006** compare IDs/text/states/edges/criteria/refs/counts/hashes and public privacy projection
- **AC-007** any source change outside the predeclared cutover-control evidence refs invalidates the candidate and requires a new run. Record completion evidence on the cutover transaction ref while this Task remains `[p]`
- **AC-008** the authorized patch materializes its closure

## Definition of Done

Immutable candidate/source artifact sets, passing migration report, complete validation/trace bundle, generated diff review, and transaction-ledger entry identify one exact unchanged candidate/source pair; no rollback success is claimed before `0037-35.02`.
