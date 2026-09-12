---
schema_version: "1.0"
id: "0044-07"
level: "task"
parent: "0044"
state: "open"
visibility: "internal"
prerequisites:
  - "0044-05"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1210"
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

PREREQ: 0044-07:0044-05 Review the role catalog against the capability model and propose new roles at a workable granularity. *(architect-elaboration)* Prior Architect claim: `TODO-data-0044-07-20260827T115800Z-e2f77b46.md` (owner token `agent:data:0044-07:20260827T115800Z-e2f77b46`; Architect decision packet REF `6539c7c0d`). **Lifecycle repair (2026-08-29):** Management selected option B in `agent-inbox:1787901177228-90a8b1db`; `DEC-0044-030`, its independent Architect scope review, and the privileged integration record are reachable from `main`. The prior claim is terminal and released, so the recorded `[u]` condition no longer exists. Task implementation remains undone and unclaimed; a distinct Implementer must create a fresh exact-scope claim. Coordination REF: `TODO-jean-luc-0044-07-marker-repair-20260829T002500Z.md`.

## Scope

- **Vorbereitungspaket (2026-08-25, `harry`, Dispatcher-Rolle, `unprivileged`, im Auftrag der Feature-Eigentümerin `kathryn`):** Entscheidungs-/Blast-Radius-Paket für den Management-delegierten A-prime-Dreierkonsens (`jean-luc`/`seven`/`geordi`; `data` widerspricht, empfiehlt B, Dissens erhalten) unter `docs/campaign-evidence/0044-07/a-prime-blast-radius-package.md`. Claim: `TODO-Harry-0044-07-20260825T221900Z.md`; owner_token `agent:harry:0044-07:20260825T221900Z`. Reine Vorbereitung — keine Mutation an einem abgenommenen Vertrag, kein `Acceptance: ✓`, kein Checkpoint-Übertritt. Marker unverändert `[ ]`, da keine Implementierung stattfand.
  - **Requirements covered:** `RQ-CB-04`, `RQ-CB-07`.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** role adoption itself is decision-record-gated; this Task produces reviewed proposals, not live authority changes. Re-examined at `0044-08`.

## Acceptance criteria

- **AC-001** Each existing role/persona is expressed as a capability descriptor
- **AC-002** gaps between task profiles and available roles are enumerated
- **AC-003** proposed new roles (e.g. a text-only sandboxed role without the runner protocol for edits that execute nothing) state their capability descriptor, what they save (tokens, runner-slot serialization) and what they must not do
- **AC-004** the interim preference of `RQ-CB-07` (sandboxed agents only for non-executing work) is either confirmed as policy or replaced by the matcher's verdicts
- **AC-005** every proposal preserving/altering runner-protocol obligations is checked against `SANDBOX.md` and recorded as a decision, not silently adopted

## Definition of Done

Committed as an update to `process-roles.md` plus decision records for each adopted role; rejected proposals retained with reasons.
