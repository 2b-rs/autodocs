---
schema_version: "1.0"
id: "0020-05"
level: "task"
parent: "0020"
state: "open"
visibility: "internal"
prerequisites:
  - "0020-03"
  - "0020-04"
  - "2026"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2648"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0020-05:0020-03, 0020-05:0020-04 Decide `ACQ.4`, `HWE.1`–`HWE.4`, `MLE.1`–`MLE.4`, `SUP.11`, `PIM.3`, and `REU.2` applicability; create dependency-linked execution Features/tasks for every included process. For every shared process register both the assessed unit's execution gate and the external interface gate; for every fully external process define controlled inputs, outputs, acceptance, monitoring, escalation, configuration, risk, and evidence interfaces rather than treating it as absent. Claim: `TODO-hguh-0020-05-20260826T125500Z.md`; owner_token: `agent:hguh:0020-05:20260826T125500Z`. REF: `504a8c4483f5c7f25e71ccd088ffc5f51780ac85` (`docs/dossiers/req-0020-05-conditional-process-applicability.md`). Included execution Features: 0. No `Acceptance: ✓`.

## Scope

- **Define contract (2026-08-26, hguh):** `docs/dossiers/req-0020-05-conditional-process-applicability.md`. None of the named processes is included. Shared: 0. Included execution Features: 0. Fully external interface records for HWE, ACQ.4, MLE/SUP.11, PIM.3, REU.2 so they are not treated as absent. No `Acceptance: ✓`.

## Acceptance criteria

- **AC-001** (1) Each named process is decided included or not. (2) Included processes have execution Features — vacuously 0. (3) Shared processes have both gates — vacuously 0. (4) Each fully external process has inputs, outputs, acceptance, monitoring, escalation, configuration, risk, and evidence interfaces. (5) HWE not included (`DEC-0020-001`). Assistant AI is not MLE

## Definition of Done

Dossier committed on `0020-05` with `0020-03`/`0020-04` present; not `Acceptance: ✓`.
