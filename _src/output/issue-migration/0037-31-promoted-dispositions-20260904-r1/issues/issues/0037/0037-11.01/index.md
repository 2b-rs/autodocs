---
schema_version: "1.0"
id: "0037-11.01"
level: "subtask"
parent: "0037-11"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-05"
  - "0037-08"
  - "0037-09"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2306"
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
---

## Goal

PREREQ: 0037-11.01:0037-05, 0037-11.01:0037-08, 0037-11.01:0037-09 Implement generated `TODO.md`, `DONE.md`, and open/blocked/unclear/owner summaries. **REF:** `beb2564331279bfdc29ae357cded9571b7416e9c`.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Render every lifecycle/archive disposition truthfully, including superseded/not-accepted
- **AC-002** preserve normative text and criterion IDs
- **AC-003** include an unambiguous generated warning plus source/schema/tool/config hashes and content-derived generation ID while linking the volatile execution run only from its external manifest
- **AC-004** use deterministic ordering
- **AC-005** and make manual divergence, omission, duplicated item, or false completion fail validation

## Definition of Done

Golden and repeated clean runs prove byte determinism and exact counts/IDs/state/text reconciliation for open, terminal, and anomalous fixtures.
