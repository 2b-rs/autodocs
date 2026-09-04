---
schema_version: "1.0"
id: "0028-04"
level: "task"
parent: "0028"
state: "open"
visibility: "internal"
prerequisites:
  - "0028-03"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2737"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0028-04:0028-03 Produce and agree `SYS1-stakeholder-baseline-interface@v1`: versioned atomic stakeholder requirements with controlled sources, rationale, priority, status, binary acceptance criteria, validation method, intended-use/environment coverage, assumptions/exclusions, conflict disposition, named stakeholder agreement/acceptance authority, bidirectional source/downstream trace, communication, changes/impacts/risks, supersession and open findings. Reject candidate/unapproved, stale, cross-product, anonymous, unresolved-conflict and wrong-origin content. Write only `docs/dossiers/req-0028-04-stakeholder-requirements-baseline.md`, own claim and bookkeeping. DoD: exact version/digests, whole-baseline validation, current agreement records, consumer handoff, recovery, findings disposition and REF.

## Scope

- **Implements:** `DEC-0028-001` `CON-03`/`CON-04`. `0029-01` consumes this output only on the internal/shared SYS.1 path; no unconditional TODO prerequisite is added and the external path remains separately validated.
  - **Capability/cognitive profile:** `unprivileged`, direct Git/stdlib, cognitive `critical` (depth/context/verification critical; breadth/ambiguity high), Implementer distinct from Data and mandatory-checkpoint Integrator; 90–180 minutes, CPU <5 minutes, no network/credentials, uncertainty ±45%, risk critical.
  - **Test derivation:** schema, trace, coverage, authority, agreement and consumer-selection risks; deterministic whole-baseline integration checks, negative fixtures and manual agreement-record inspection.
  - **Integration review: mandatory.** **Rationale (architect):** this is the shared cross-Feature output interface conditionally consumed by `0029-01`; false agreement or origin can propagate invalid system requirements.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
