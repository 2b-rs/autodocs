---
schema_version: "1.0"
id: "0020-03"
level: "task"
parent: "0020"
state: "open"
visibility: "internal"
prerequisites:
  - "0020-01"
  - "2026"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2640"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0020-03:0020-01 Define the ECU responsibility/authority matrix across customer, system, software, hardware, ML, cybersecurity, functional safety, calibration, manufacturing/service, integration, validation, release, operations, and suppliers; record who performs, reviews, approves, accepts, monitors, communicates, and retains evidence at every lifecycle interface. Claim: `TODO-hguh-0020-03-20260826T124500Z.md`; owner_token: `agent:hguh:0020-03:20260826T124500Z`. REF: `ab2d1d81ddf56e8cf1b7219715bfc0ecf02da6b4` (`docs/dossiers/req-0020-03-responsibility-authority-matrix.md`). No `Acceptance: ✓`.

## Scope

- **Define contract (2026-08-26, hguh):** `docs/dossiers/req-0020-03-responsibility-authority-matrix.md` (`REQ-0020-03-01`–`REQ-0020-03-10`). Bound by `DEC-0020-001` (software above kernel internal; kernel/hardware/manufacturing not this increment; no complete-system owner). Open rows stay `not-decided`. No `Acceptance: ✓`. No `0020-02` claim overwrite. No Feature `0033`.

## Acceptance criteria

- **AC-001** (1) Every Task-named interface has a matrix row. (2) Each row has the seven authority columns. (3) Software / owned-software integration / software verification / owned-software release are `internal`. (4) Kernel, hardware, manufacturing, complete-system, and complete-ECU integration/release are not `internal`. (5) Customer, ML, cybersecurity, functional safety, calibration, operations, suppliers, and `VAL.1` are not invented as named internal parties

## Definition of Done

The matrix dossier is committed on branch `0020-03`; `0020-01` is present; no shared `validate.py` gate; not `Acceptance: ✓`.
