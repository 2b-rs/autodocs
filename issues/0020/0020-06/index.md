---
schema_version: "1.0"
id: "0020-06"
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
  source: "legacy:TODO.md:2652"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0020-06:0020-03, 0020-06:0020-04 Decide applicable Automotive SPICE for Cybersecurity model/version and ISO/SAE 21434 responsibilities, plus ISO 26262 functional-safety responsibilities; create separate dependency-linked Features for applicable cybersecurity or safety lifecycles, register their completion gates in the selected profile, and do not present generic PAM 4.0 evidence as proof of either framework. Claim: `TODO-hguh-0020-06-20260826T130000Z.md`; owner_token: `agent:hguh:0020-06:20260826T130000Z`. REF: `c11c2a0b94c6d2198086a855f1b295074659db92` (`docs/dossiers/req-0020-06-cybersecurity-safety-applicability.md`). CS/FS Features: 0. No `Acceptance: ✓`.

## Scope

- **Define contract (2026-08-26, hguh):** `docs/dossiers/req-0020-06-cybersecurity-safety-applicability.md`. CS/21434 and 26262 not applicable as owned lifecycles this increment. CS/FS Features: 0. No CS/FS gate in the 14-process profile. PAM 4.0 evidence is not 21434 or 26262 proof. No `Acceptance: ✓`.

## Acceptance criteria

- **AC-001** (1) CS model/version decided (none). (2) 21434 and 26262 owned-responsibility decided (none). (3) Features created only for applicable lifecycles (none). (4) No CS/FS completion gate added to the selected profile. (5) Explicit prohibition on presenting PAM 4.0 as CS/FS proof

## Definition of Done

Dossier committed on `0020-06` with `0020-05` present; not `Acceptance: ✓`.
