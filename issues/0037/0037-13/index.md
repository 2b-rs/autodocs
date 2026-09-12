---
schema_version: "1.0"
id: "0037-13"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-06"
  - "0037-08"
  - "0037-09"
  - "0037-17.01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2331"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-13:0037-06, 0037-13:0037-08, 0037-13:0037-09, 0037-13:0037-17.01 Inventory the legacy backlog at an exact source commit and define the importer fidelity/anomaly baseline. **Claim:** `TODO-Gabriel-Saru-0037-13-20260825T082600Z.md` (`agent:gabriel-saru-20260825t082600z:0037-13:20260825T082600Z`). **REF:** `f08c4d30cfe9812fa7f80df23dd4c3703927cbf3`.

## Scope

- **Acceptance: ✓** (2026-08-28T20:35Z, Integrator `obrien`, independent of Implementer `Gabriel-Saru-20260825T082600Z` / `agent:gabriel-saru-20260825t082600z:0037-13:20260825T082600Z`). Abgenommene Baseline `f08c4d30cfe9812fa7f80df23dd4c3703927cbf3` (integrated on main as `7ad79143058196b472fbc3ff133bf7123223d575`); 8/8 legacy inventory tests OK, automation_safety PASS/0; AWARD `1787949142011-93335a96`. No checkpoint crossed or upward Feature integration performed.

## Acceptance criteria

- **AC-001** Inventory every Feature/Task/Subtask, marker, prerequisite, criterion/DoD, decision/history/closure note, real `REF`, `local-*`/pending placeholder, archive exception, duplicate/malformed construct, and `TODO-<agent-id>.md` claim from Git blobs
- **AC-002** classify lossless mappings, stable migration findings, and authority-required dispositions. Explicitly retain Feature `0021` as archived-not-accepted and give no evidence credit to `local-20260815-0021-06` through `-08`

## Definition of Done

`provenance/migrations/issue-store/<run-id>/legacy-inventory.json` and `.md`, source artifact set, and frozen fixtures cover `TODO.md`, `DONE.md`, current Feature `0037`, active claims, and representative anomalies without modifying either database.
