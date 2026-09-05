---
schema_version: "1.0"
id: "0040-02"
level: "task"
parent: "0040"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:502"
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
  - id: "AC-007"
    status: "active"
---

## Goal

Write one briefing per process role under `docs/pipeline/agent-instructions/`, such that a session assigned that role can actually perform it. REF: `7437905a6a6c0b7987ab6870f19cc5fc45ff774b`.

## Scope

- **Reason (2026-08-18, trilateral agreement round 2 and 5):** Superseded, not cancelled. Five separate normative briefing documents were struck; the substance now lives as five **personas** in section 6 of `docs/pipeline/process-roles.md`, each with stance, reading order, output, prohibitions, typical failure mode and a worked case from this repository. Project management's objection was that five further normative documents in a corpus of 71 are "paper for a reader who already wrote the content"; the architect's requirement that the material be briefing-capable is met by the persona sections. `RQ-ROLE-03` is therefore satisfied by `0040-01`.
  - **Requirements covered:** `RQ-ROLE-03`.
  - **Context:** The customer's point is that roles without briefings are decoration ("Die Agenten müssen ja alle für ihre Rolle entsprechend gebrieft werden"). The existing directory `docs/pipeline/agent-instructions/` is the established location for this kind of instruction artifact and must be reused rather than duplicated.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** documentation only; reviewed in aggregate at `0040-09` and checked for authority drift by `0040-07`.

### Campaign B — Decision records and traceability

## Acceptance criteria

- **AC-001** One briefing per role defined in `0040-01`. Each briefing names: the role's purpose
- **AC-002** its concrete work products
- **AC-003** what it must inspect before acting
- **AC-004** what it must record
- **AC-005** the decisions it may and may not take alone
- **AC-006** its escalation path
- **AC-007** and its handover point to the next role. Each briefing is written so it is actionable without reading the whole authority corpus, and each links back to `process-roles.md` as the normative source rather than restating authority. The Requirements Engineer briefing explicitly covers questioning the customer's premise, because doing so produced findings A and C of this very Feature

## Definition of Done

Committed with real `REF`; every role from `0040-01` has exactly one briefing and no briefing describes a role that does not exist; no briefing grants authority beyond `process-roles.md`.
