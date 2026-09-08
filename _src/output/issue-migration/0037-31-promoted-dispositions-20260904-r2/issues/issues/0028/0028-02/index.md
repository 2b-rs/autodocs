---
schema_version: "1.0"
id: "0028-02"
level: "task"
parent: "0028"
state: "open"
visibility: "internal"
prerequisites:
  - "0028-01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2729"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0028-02:0028-01 Create the controlled stakeholder and source register for customer, user, regulatory, operational, manufacturing/service, safety, cybersecurity, supplier, and internal sources. Record stable stakeholder/source identity, role/remit, originator, authority, revision, date, confidentiality, applicability, communication route and append-only change history; distinguish missing/unknown from accepted and reject duplicates, anonymous authority and cross-product substitution. Write only `docs/dossiers/req-0028-02-stakeholder-source-register.md`, own claim and bookkeeping. DoD: whole-population manifest, completeness/duplicate results, missing-source findings, digests and REF; no agreement or process credit.

## Scope

- **Capability/cognitive profile:** `unprivileged`, direct Git/stdlib, cognitive `high` (all five estimator dimensions high except ambiguity medium), distinct from Data/Integrator; 45–90 minutes, CPU <2 minutes, no network, uncertainty ±30%, risk high.
  - **Test derivation:** source-control and authority risks; deterministic table completeness/duplicate scan plus bounded manual provenance inspection.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** reversible evidence-register work with no external effect; `0028-04` rejects unauthorized/missing sources and terminal `0028-05` reviews composition.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
