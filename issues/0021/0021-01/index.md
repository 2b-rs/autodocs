---
schema_version: "1.0"
id: "0021-01"
level: "task"
parent: "0021"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
  - "archived-not-accepted"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:320"
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
---

## Goal

Define the authoritative website “Flag for review” process, role boundaries, lifecycle semantics, and non-bypass rules in `docs/pipeline/`. REF: 42b0b4a1

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** The docs define which published records are eligible and every exclusion
- **AC-002** define who may submit, claim, propose, accept/reject, apply, and close a web-originated request
- **AC-003** distinguish review versus curation routing
- **AC-004** specify the `valid/*` re-review rule
- **AC-005** define stale/duplicate/abuse handling
- **AC-006** and state that the website never mutates records directly

## Definition of Done

`docs/pipeline/` documents are internally consistent with `workflow-lifecycle.md`, `roles.md`, `actions.md`, `status-model.md`, and `curation-item-schema.md`; a validation/testable set of normative requirements is committed.
