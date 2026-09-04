---
schema_version: "1.0"
id: "0033-07.03"
level: "subtask"
parent: "0033-07"
state: "open"
visibility: "internal"
prerequisites:
  - "0033-07.02"
  - "0033-07.04"
  - "0033-08"
  - "0033-13"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:853"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0033-07.03:0033-07.02, 0033-07.03:0033-07.04, 0033-07.03:0033-08, 0033-07.03:0033-13 Obtain authorized privacy/records approval of local and external-GitHub retention, redaction, disposal, public projection, consent, and residual limitations. <!-- REF: decision-1788270436895-e324902f -->

## Scope

- **Baseline findings:** `RRB-PRIV-001`, `RRB-RELEASE-001`.

## Acceptance criteria

- **AC-001** The reviewer checks field/location classifications, public GitHub Issue/comment/attachment limitations, controller responsibilities, consent wording, retention clocks, holds, backups/exports, deletion/redaction feasibility, public reports/history, logs, migration, and test evidence against the approved contract
- **AC-002** every finding is closed or explicitly blocks approval

## Definition of Done

An authenticated approval names exact policy/implementation/test versions and accepted residual limitations. Keep this subtask `[p]` during rework and set it `[u]` only when the authorized reviewer decision is the next action.
