---
schema_version: "1.0"
id: "0040-01"
level: "task"
parent: "0040"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:494"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Define the restrictive capability-class × process-responsibility model and its role-to-agent-profile mapping, and anchor it consistently in the authority documents. REF: `7437905a6a6c0b7987ab6870f19cc5fc45ff774b`.

## Scope

- **Contract reconciliation (2026-08-18):** This wording records the already implemented trilateral agreement at the historical Task contract. It is not a new architecture and does not alter state or REF. The superseded draft incorrectly called the axes orthogonal, assumed three capability classes, and modeled five responsibilities as assigned roles.
  - **Requirements covered:** `RQ-ROLE-01`, `RQ-ROLE-02`, `RQ-ROLE-03`, `RQ-ROLE-04`; decision `DEC-0040-003`, as refined by the trilateral agreement.
  - **Context:** Capability class describes what a session may execute; process responsibility describes what it is accountable for. The repository has exactly two capability classes, `sandboxed/grunt` and `privileged`. The approved model contains three normative roles (Architect, Implementer, Integrator), two ungated functions (Requirements Engineer, QA Manager), and Management outside the agent role model. The axes are distinct but **not orthogonal**: the mapping is restrictive. `docs/pipeline/roles.md` describes a separate product-domain model and must not be conflated with this one.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** documentation only, with no irreversible migration, external effect, credential/security boundary, or public release. Its consistency is reviewed in aggregate at `0040-09`.

## Acceptance criteria

- **AC-001** `docs/pipeline/process-roles.md` defines the three roles and two functions with responsibilities, authority boundaries, required separation, work products, and one actionable persona for each. Its mapping states the minimum capability class and incompatibilities, including that only a privileged session may be Integrator and that privilege alone never proves independence. Management is the current user or a registered authority, never an agent role. `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`, and `docs/pipeline/roles.md` reference the model without contradiction or a third capability class

## Definition of Done

Committed with the retained real `REF`; no authority document contradicts another on roles, functions, Management, separation, or capability wording; existing marker, acceptance, and merge-authority semantics are unchanged; a reader can determine from the mapping which profile a responsibility requires.
