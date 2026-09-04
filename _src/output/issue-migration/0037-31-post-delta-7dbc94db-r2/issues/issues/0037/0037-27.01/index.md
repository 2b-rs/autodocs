---
schema_version: "1.0"
id: "0037-27.01"
level: "subtask"
parent: "0037-27"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-17"
  - "0037-19"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2464"
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

PREREQ: 0037-27.01:0037-17, 0037-27.01:0037-19 Persist AI workflow runs and typed claims with stable claim IDs and common provenance.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Pin record/evidence/policy/prompt/model/config/input versions, issue/criterion/campaign/run, outputs and confidence/invalidation/supersession
- **AC-002** give typed claims their own ID family and one-file persistence
- **AC-003** adapt legacy traces with explicit unknown/legacy confidence and never invented prompts/models/runs

## Definition of Done

Tests trace a claim through source evidence and AI run, invalidate on each governed input change, preserve prior claims/history, and reject fabricated or bare-ID provenance.
