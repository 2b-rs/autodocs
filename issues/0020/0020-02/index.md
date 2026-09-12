---
schema_version: "1.0"
id: "0020-02"
level: "task"
parent: "0020"
state: "open"
visibility: "internal"
prerequisites:
  - "0020-01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2633"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0020-02:0020-01 Define and enforce the evidence boundary among canonical origins `process-definition`, `implemented-mechanism`, `documentation-execution`, `ecu-execution`, and `controlled-scenario`; require `product_id`, `project_id`, `process_id`, `process_instance_id`, `baseline_id`, revision, owner, origin, validity, retention, and confidentiality metadata and prohibit cross-product evidence substitution or opportunistic aggregation. Claim: `TODO-hguh-0020-02-20260826T120900Z.md`; owner_token: `agent:hguh:0020-02:20260826T120900Z`. REF: `de8608961819bee9fc283d8f773161b5b2e543cc` (CON-01 local contract + optional helper/fixtures). `DEC-0020-002` reachable. No `_src/validate.py` registration. Consumer use/freeze gates remain `0020-07`/`0020-08`/`0020-09`/`0025-02`/`0025-03`. No `Acceptance: ✓`.

## Scope

- **Define contract (2026-08-26, hguh):** `docs/dossiers/req-0020-02-evidence-boundary.md` (`REQ-0020-01`–`REQ-0020-09`). Enforcement not activated. Cross-item gate preparation pending Architect `uras` + `decision-record@v1`. No `0020-03`, no Feature `0033`, no `Acceptance: ✓`.
  - **Architect gate-scope review (2026-08-26, uras):** `docs/dossiers/0020-02-gate-scope-review.md` (verdict `scope-ok-mit-auflagen`); `DEC-0020-002` in `docs/dossiers/dec-0020-02-evidence-boundary-enforcement.md`. Claim: `TODO-uras-0020-02-scope-20260826T121659Z-30d0c5d1.md`; owner_token: `agent:uras:0020-02-scope:20260826T121659Z-30d0c5d1`. Implementer claim unchanged. Not `Acceptance: ✓`. Enforcement still not activated.
  - **Carry review onto 0020-02 (2026-08-26, hguh):** fast-forward merged Architect tip `d116bf68a0db7ab123d490670235fd11dc02f54e` (substantive `c90b7b677ff57bae9e05a31bce7531930674210d`). `DEC-0020-002` reachable on `0020-02`. Operational “enforce” = refuse-at-use/freeze for named consumers. No `_src/validate.py` registration. No extra start-gates. Still `[p]`. Not `Acceptance: ✓`.
  - **CON-01 local helper (2026-08-26, hguh):** `_src/tools/check_0020_02_evidence_boundary.py` and `docs/dossiers/0020-02-evidence-boundary-fixtures/` (8 fixtures + 6 aggregation property cases, helper exit 0). Not registered in `_src/validate.py`. Consumer freeze/use gates not implemented here. Substantive REF `de8608961819bee9fc283d8f773161b5b2e543cc`.

## Acceptance criteria

- **AC-001** (1) The inspectable contract `docs/dossiers/req-0020-02-evidence-boundary.md` states SHALLs for the five canonical origins, the named metadata fields, and both prohibitions. (2) `DEC-0020-002` is reachable on branch `0020-02` and names refuse-at-use/freeze for `0020-07`/`0020-08`/`0020-09`/`0025-02`/`0025-03`. (3) Optional CON-01 helper `_src/tools/check_0020_02_evidence_boundary.py` classifies committed fixtures without being invoked from `_src/validate.py`. (4) No extra TODO start-gates and no live `docs/ASPICE` gate are added by this Task

## Definition of Done

Contract, `DEC-0020-002`, optional helper/fixtures, and this history are committed; helper run against those fixtures exits 0; `_src/validate.py` is unchanged; consumer refusal gates are not implemented here. Not `Acceptance: ✓`.
