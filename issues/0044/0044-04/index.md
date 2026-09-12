---
schema_version: "1.0"
id: "0044-04"
level: "task"
parent: "0044"
state: "open"
visibility: "internal"
prerequisites:
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1104"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

Write the feature-breakdown process instruction: derivation sources for architecture decisions, task dependencies, and test cases, plus the per-task capability requirement profile and branch instruction. *(architect-elaboration)* **REF:** `e1127ac2f` (corrective authority repair; prior corrective substantive `7ed7d2ab5`, prior substantive `1f9bec7847eef6874cd47815aaea310bcf16659c`, evidence normalization `4c5f5aa0fe8ffcb6e00a3509e752bc16b8680935`; branch `0044-04`). Lore evidence carried unchanged in `654c9cdac`, signed-record SHA-256 `e66a57f660d21703cec4b26b80398210a7afb1ea9cda6c9749ad86decf6fd91e`. The historical Data-Ada-attributed A1 mapping is authority-invalid and superseded; Lore's signed `fits` verdict is operative for policy integrability only. **Uebernommen (2026-08-22, 09:30Z):** `Data-Leah-20260822T092629Z` hat den verwaisten Riker-Claim unter ausdruecklicher User-Autoritaet uebernommen; Uebernahme-Buchhaltung auf Branch `0044-04`, Commit `f81db6287`, neuer unveraenderlicher owner_token, Riker-Historie erhalten. **Current takeover:** `TODO-Data-Ada-0044-04-20260822T214600Z.md`, owner token `agent:data-ada-20260822t214600z:0044-04:20260822T214600Z`. Die Freigabe dieses Markers in `6a688283b` (09:42Z) beruhte auf der inzwischen ueberholten Annahme, die Session sei tot, und wird hiermit zurueckgenommen. Gate-Freigabe: `DEC-0044-017` samt additiver A-02-Korrektur (`d74386e7e`) und Architekten-Scope-Prüfung `scope-ok-mit-auflagen` (`docs/dossiers/0044-04-gate-scope-review.md`); 15 Auflagen bindend, sechs davon vor der ersten Policy-Mutation.

## Scope

- **Implementation completion:** `feature-breakdown.md` linked from `AGENTS.md` and `process-roles.md`; structured A1/A2 evidence and Feature 0043 worked example retained under `docs/campaign-evidence/0044-04/`; corrective ownership, pilot-record, deterministic-profile, retrospective, and EOF handoff findings are resolved and recorded in the Data-Ada claim. No acceptance credit; mandatory integration review remains pending.
  - **Requirements covered:** `RQ-AP-01` … `RQ-AP-03`, `RQ-AP-02`'s data dimension (e.g. PGP keys, non-git data), and `RQ-IP-02` (explicit target-policy ownership at breakdown time).
  - **Successor assessment:** `0044-05`, `0044-06`, and `0044-07` retain their own capability/calibration/role requirements and do not claim ownership of `RQ-IP-02`; `0044-08` consumes this Task's policy-precedence trace through its existing prerequisite and remains the integration/review surface. No successor contract is changed by this ownership correction.
  - **Context:** `process-roles.md` defines *who* decides but not *from what*; the customer cannot currently trace where architecture decisions, dependencies, or test scope come from. This is the prevention point for planning-error cases A1/A2 of `0044-01`.
  - **Integration review:** **mandatory.** **Rationale (architect):** this instruction shapes every future breakdown; a defect here propagates into every feature planned under it.
  - **Acceptance:** ✓
    - **Disposition:** `completed`
    - **Accepted by:** `geordi` (Geordi La Forge, privileged Team Enterprise Integrator)
    - **Authority reference:** `agent-inbox:jean-luc→geordi:1787668111539-12cdc72a` (exact `0044-04` checkpoint/integration assignment, relaying current-user directive)
    - **Accepted at:** `2026-08-25T16:47:21+02:00`
    - **Contract SHA-256:** `7451ccc9b43dcc93ee89a4cf6031ebcb3ec6d46fbdd5f61efd6f08f39468fa83`
    - **Work-product manifest SHA-256:** `48966619f762fab8ef4929e87a000f4fb57849b067cb9313574ad751b6d69abb`
    - **Prerequisite-acceptance SHA-256:** `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570`
    - **Review REF:** `982602e81eacee2dc910db10a843f28f2f32a558`
    - **Review evidence SHA-256:** `1f64881f8519d44b9bc3e53e3ba17b4f9d2e5a56f55dbfb373c7b08e4d048bd2` (`docs/campaign-evidence/0044-04/integration-review-geordi-20260825.md`)

## Acceptance criteria

- **AC-001** A process instruction for the breakdown owner requires each task to record: the inputs its architecture decisions derive from (requirements, decision records, existing architecture, repository evidence), the derivation of its prerequisites (with the planned implementation order where order matters), the derivation of test scope and kind, the capability requirement profile (rights, data, tools, execution needs, cognitive demand class), and how the implementer is to create the branch
- **AC-002** the instruction states how integrability under the target policy is verified at branch time (A1) and how order deviations are recorded (A2)

## Definition of Done

Committed in `docs/pipeline/`; linked from `process-roles.md` and `AGENTS.md`; applied to one new real feature breakdown as a worked example (Feature `0043` or later).
