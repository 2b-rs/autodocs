# Requirements — controlled process/work-product/evidence catalogue (`0020-08`)

**Item:** Task `0020-08` of Feature `0020`
**Role:** Requirements Engineer (`hguh`)
**Claim:** `TODO-hguh-0020-08-20260826T131100Z.md`
**owner_token:** `agent:hguh:0020-08:20260826T131100Z`
**Recorded at:** `2026-08-26T13:12:00Z`

Mailbox `1787749837023-bc15ffe0` is coordination, not authority.

This catalogue instantiates work products for the 14-process nucleus. It does **not** assign a capability rating.

---

## 1. Provenance (preserved)

Task text: Instantiate the controlled process/work-product/evidence catalogue for the selected ECU profile, assigning ECU-specific work products, owners, repositories, review/approval criteria, lifecycle interfaces, baseline/retention controls, and evidence obligations; baseline initial gaps without assigning a capability rating.

Selected profile: 14-process nucleus (`0020-04`). Evidence metadata: `0020-02` / `DEC-0020-002`. Owner: assessed unit (`0020-03` software `internal`). Assessor worksheets: `0020-07`. No CS/FS WPs (`0020-06`).

---

## 2. Catalogue rules

| Field | Rule |
|---|---|
| Owner | Assessed unit (virtualized automotive ECU software increment); no invented named person |
| Repository | This Git repository for software WPs; path named per row |
| Review/approval | Internal review then internal approve (`0020-03` software columns) |
| Evidence | Required `0020-02` metadata; ECU outcomes require origin `ecu-execution` |
| Retention | Assessment cycle, `internal` confidentiality (`0020-07`) |
| Rating | **None** — gaps only |
| Initial gap (all rows) | No `ecu-execution` evidence yet; current tree is documentation-product / `documentation-execution` |

---

## 3. Atomic requirements

### `REQ-0020-08-01` — Nucleus only

The catalogue SHALL list work products only for `SWE.1`–`SWE.6`, `SPL.2`, `SUP.1`, `SUP.8`, `SUP.9`, `SUP.10`, `MAN.3`, `MAN.5`, `MAN.6`. Out-of-scope processes SHALL NOT appear as rated WPs.

### `REQ-0020-08-02` — Each WP has control fields

Each work product SHALL name owner, repository, review/approval criterion, lifecycle interface, baseline/retention, and evidence obligation.

### `REQ-0020-08-03` — Gaps without ratings

Initial gaps SHALL be recorded. No `N/P/L/F` or CL SHALL be assigned.

### `REQ-0020-08-04` — Evidence obligation

Outcome evidence SHALL be `ecu-execution` with required metadata. Templates and this catalogue itself are `process-definition`, not outcome evidence.

---

## 4. Catalogue (14 processes)

Common owner: assessed unit. Common repo: `autodocs` Git. Common retention: assessment-cycle / internal. Common gap: no `ecu-execution` baseline yet.

| Process | Work products | Lifecycle interface | Review/approval | Evidence obligation | Initial gap |
|---|---|---|---|---|---|
| `SWE.1` | Software requirements specification; allocation from kernel interface; status/trace | Software / received system constraints (`external` input) | Internal review and approve | `ecu-execution` SRS baseline | No approved software-requirement baseline |
| `SWE.2` | Software architecture; interface description above kernel | Software | Internal | `ecu-execution` architecture baseline | No approved architecture |
| `SWE.3` | Detailed design; source baseline for units | Software | Internal | `ecu-execution` design/source baseline | No ECU unit construction baseline (docs tree is not that) |
| `SWE.4` | Unit verification spec/results | Software verification | Internal | `ecu-execution` unit results | No ECU unit-test results |
| `SWE.5` | Software integration plan/results | Owned-software integration | Internal | `ecu-execution` integration results | No ECU integration results |
| `SWE.6` | Software qualification test spec/results | Software verification | Internal | `ecu-execution` SWE.6 results | No ECU SWE.6 results |
| `SPL.2` | Software release package, notes, identity | Owned-software release | Internal approve/accept | `ecu-execution` release record | No ECU software release package |
| `SUP.1` | QA plan, nonconformance records | Software QA | Independent-as-possible internal QA vs implementer (`0020-07` independence field still `not-named`) | `ecu-execution` QA records | No ECU QA execution |
| `SUP.8` | CI list, baselines, status, backup/restore | Software configuration | Internal | `ecu-execution` CM records; Git is `implemented-mechanism` until used as ECU CM | Git exists; ECU CI catalogue/baselines not operated |
| `SUP.9` | Problem records, cause, resolution, closure | Software problems | Internal | `ecu-execution` problem records | No ECU problem lifecycle execution |
| `SUP.10` | Change requests, impact, authorize, implement, verify | Software changes | Internal approve | `ecu-execution` CR records | No ECU change-request execution |
| `MAN.3` | Project plan, assignments, actual-vs-plan | Software project | Internal | `ecu-execution` plan/status | No ECU MAN.3 plan/execution |
| `MAN.5` | Risk strategy/register (incl. unnamed HW/kernel residual from `0020-05`) | Software project risk | Internal | `ecu-execution` risk records | No ECU risk register execution |
| `MAN.6` | Information needs, metrics, values, decisions | Software project measurement | Internal | `ecu-execution` measurement records | No ECU measurement execution |

---

## 5. Out of this catalogue

SYS, VAL, HWE, ACQ.4, MLE, SUP.11, PIM.3, REU.2, CS/FS: not included (`0020-04`/`05`/`06`). External interfaces remain those records, not WPs here.

---

## 6. Open decisions

| ID | Decision |
|---|---|
| `PD-0020-08-01` | Named WP owners beyond “assessed unit” |
| `PD-0020-08-02` | Alternate evidence repository if Git is insufficient for binaries/calibration |

---

## 7. Exclusions

Capability ratings; `Acceptance: ✓`; `0020-09` register implementation; `0025` freeze; `main`; Feature `0033`; overwriting prior tokens.
