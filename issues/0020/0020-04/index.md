---
schema_version: "1.0"
id: "0020-04"
level: "task"
parent: "0020"
state: "open"
visibility: "internal"
prerequisites:
  - "0020-03"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2644"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0020-04:0020-03 Complete and approve an applicability matrix for all 32 PAM 4.0 processes, starting with the 14-process ECU software-delivery nucleus and adding each of `SYS.1`–`SYS.5` and `VAL.1` only for its actual owned responsibility; use the 20-process profile only when the complete system lifecycle and intended-use validation are owned. Record assessment disposition (`included/rated` or `out of scope/not rated`) separately from execution responsibility (`internal`, `shared`, or `external`); for every shared process identify the assessed unit's outcomes/activities and internal execution gate plus the external activities and interface/acceptance gate, all justified from supplied-product and responsibility evidence. Claim: `TODO-hguh-0020-04-20260826T125000Z.md`; owner_token: `agent:hguh:0020-04:20260826T125000Z`. REF: `51331b71b6ec48fdcc0c517bfd8541009480437f` (`docs/dossiers/req-0020-04-applicability-matrix.md`). No `Acceptance: ✓`.

## Scope

- **Define contract (2026-08-26, hguh):** `docs/dossiers/req-0020-04-applicability-matrix.md`. Profile = 14-process nucleus (`included/rated`, execution `internal`). `SYS.1`–`SYS.5`, `VAL.1`, `HWE.*`, and `0020-05` conditionals `out of scope/not rated`. Shared rows: 0. 20-process profile not selected. No `Acceptance: ✓`.

## Acceptance criteria

- **AC-001** (1) 32 PAM 4.0 processes each have disposition and execution fields. (2) Nucleus 14 are `included/rated` / `internal`. (3) SYS/VAL not added. (4) No invented shared party. (5) Justified from `DEC-0020-001` and `0020-03`

## Definition of Done

Dossier committed on `0020-04` with `0020-03` present; not `Acceptance: ✓`.
