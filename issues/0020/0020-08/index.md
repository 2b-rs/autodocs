---
schema_version: "1.0"
id: "0020-08"
level: "task"
parent: "0020"
state: "open"
visibility: "internal"
prerequisites:
  - "0020-02"
  - "0020-03"
  - "0020-04"
  - "0020-05"
  - "0020-06"
  - "0020-07"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2660"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0020-08:0020-02, 0020-08:0020-03, 0020-08:0020-04, 0020-08:0020-05, 0020-08:0020-06, 0020-08:0020-07 Instantiate the controlled process/work-product/evidence catalogue for the selected ECU profile, assigning ECU-specific work products, owners, repositories, review/approval criteria, lifecycle interfaces, baseline/retention controls, and evidence obligations; baseline initial gaps without assigning a capability rating. Claim: `TODO-hguh-0020-08-20260826T131100Z.md`; owner_token: `agent:hguh:0020-08:20260826T131100Z`. REF: `40b2f9eb42ce26f1b212132631af26cfd6514595` (`docs/dossiers/req-0020-08-evidence-catalogue.md`). No capability rating. No `Acceptance: ✓`.

## Scope

- **Define contract (2026-08-26, hguh):** `docs/dossiers/req-0020-08-evidence-catalogue.md`. 14-process nucleus WPs. No capability rating. Initial gap: no `ecu-execution` yet. No `Acceptance: ✓`.

## Acceptance criteria

- **AC-001** (1) Catalogue covers the 14 included processes. (2) Each WP has owner, repository, review/approval, interface, retention, evidence obligation. (3) Gaps recorded. (4) No N/P/L/F assigned

## Definition of Done

Dossier committed on `0020-08` with `0020-07` present; not `Acceptance: ✓`.
