# Requirements — PAM 4.0 applicability matrix (`0020-04`)

**Item:** Task `0020-04` of Feature `0020`
**Role:** Requirements Engineer (`hguh`)
**Claim:** `TODO-hguh-0020-04-20260826T125000Z.md`
**owner_token:** `agent:hguh:0020-04:20260826T125000Z`
**Recorded at:** `2026-08-26T12:51:00Z`

Mailbox `1787748559740-9ee90c1c` is coordination, not authority.

This Task produces a definition/readiness matrix. It does not rate capability, accept work, or include the kernel.

---

## 1. Provenance (preserved)

Task text: complete and approve an applicability matrix for all 32 PAM 4.0 processes, starting with the 14-process ECU software-delivery nucleus and adding each of `SYS.1`–`SYS.5` and `VAL.1` only for its actual owned responsibility; use the 20-process profile only when the complete system lifecycle and intended-use validation are owned. Record assessment disposition (`included/rated` or `out of scope/not rated`) separately from execution responsibility (`internal`, `shared`, or `external`); for every shared process identify the assessed unit's outcomes/activities and internal execution gate plus the external activities and interface/acceptance gate, all justified from supplied-product and responsibility evidence.

`DEC-0020-001` (verbatim Management): exclusively system and application software for a virtualized automotive ECU; kernel later. No complete-system-lifecycle ownership. Starting profile = 14-process nucleus. `SYS.1`–`SYS.5` and `VAL.1` only when `0020-03`/`0020-04` show actual owned responsibility. Kernel, OS, HWE out of this increment.

`0020-03` matrix (`ab2d1d81d`): software above the kernel is `internal`; system is not complete-system owner; hardware and manufacturing `not-this-increment`; `VAL.1` `not-decided`; no named customer, supplier, or shared party.

14-process nucleus (`docs/ASPICE/01-assessment-basis-and-scope.md` §5.1): `SWE.1`–`SWE.6`, `SPL.2`, `SUP.1`, `SUP.8`, `SUP.9`, `SUP.10`, `MAN.3`, `MAN.5`, `MAN.6`.

---

## 2. Problem

Without a 32-row matrix that separates assessment disposition from execution responsibility, later Features cannot tell which processes are in the Level-1 target versus merely adjacent. The 20-process system profile must not be selected while complete-system ownership is absent.

---

## 3. Profile decision

**Selected profile this increment:** the **14-process ECU software-delivery nucleus**.

**Not selected:** the 20-process system-and-software profile (`SYS.1`–`SYS.5` + `VAL.1` added). Justification: `DEC-0020-001` and `0020-03` show no complete ECU system lifecycle ownership and no internal `VAL.1` intended-use validation.

---

## 4. Atomic requirements

### `REQ-0020-04-01` — All 32 PAM 4.0 processes have a row

The matrix SHALL contain exactly one row for each of: `ACQ.4`, `SYS.1`–`SYS.5`, `SWE.1`–`SWE.6`, `HWE.1`–`HWE.4`, `MLE.1`–`MLE.4`, `SUP.1`, `SUP.8`, `SUP.9`, `SUP.10`, `SUP.11`, `MAN.3`, `MAN.5`, `MAN.6`, `SPL.2`, `VAL.1`, `PIM.3`, `REU.2`.

### `REQ-0020-04-02` — Two independent fields

Each row SHALL record **assessment disposition** (`included/rated` or `out of scope/not rated`) **and** **execution responsibility** (`internal`, `shared`, or `external`) separately.

### `REQ-0020-04-03` — Nucleus is included/rated, internal

`SWE.1`–`SWE.6`, `SPL.2`, `SUP.1`, `SUP.8`, `SUP.9`, `SUP.10`, `MAN.3`, `MAN.5`, `MAN.6` SHALL be `included/rated` with execution `internal` for this increment’s software above the kernel.

### `REQ-0020-04-04` — SYS and VAL not added

`SYS.1`–`SYS.5` and `VAL.1` SHALL be `out of scope/not rated` this increment. Execution `external`/`not-this-increment`. They are added only after actual owned responsibility is shown.

### `REQ-0020-04-05` — HWE out of this increment

`HWE.1`–`HWE.4` SHALL be `out of scope/not rated`, execution `external`/`not-this-increment` (`DEC-0020-001`, `0020-03` hardware row).

### `REQ-0020-04-06` — No invented shared party

No process SHALL be recorded as `shared` until a named external party and both gates exist. This increment has **zero** shared rows.

### `REQ-0020-04-07` — Conditional processes stay out until `0020-05` includes them

`ACQ.4`, `MLE.1`–`MLE.4`, `SUP.11`, `PIM.3`, `REU.2` SHALL be `out of scope/not rated` on current evidence (no named supplier, no ML product responsibility, no rated organizational PIM, no reuse-product mandate). Task `0020-05` may later include any of them with a new row change; this matrix does not pre-include them.

### `REQ-0020-04-08` — Inspectable work product

This dossier is the `0020-04` deliverable. It does not add start-gates beyond existing `0020-05:0020-04` / `0020-06:0020-04` / `0020-07:0020-04`.

---

## 5. Applicability matrix (32 processes)

| Process | Assessment disposition | Execution responsibility | Justification |
|---|---|---|---|
| `SWE.1` | included/rated | internal | Nucleus; software requirements above kernel (`0020-03` software `internal`) |
| `SWE.2` | included/rated | internal | Nucleus; software architecture |
| `SWE.3` | included/rated | internal | Nucleus; detailed design / unit construction |
| `SWE.4` | included/rated | internal | Nucleus; unit verification |
| `SWE.5` | included/rated | internal | Nucleus; software integration / integration verification |
| `SWE.6` | included/rated | internal | Nucleus; software qualification test |
| `SPL.2` | included/rated | internal | Nucleus; owned software-package release only (`0020-03`) |
| `SUP.1` | included/rated | internal | Nucleus; QA of owned software processes/products |
| `SUP.8` | included/rated | internal | Nucleus; configuration of owned software items |
| `SUP.9` | included/rated | internal | Nucleus; problem resolution for owned software |
| `SUP.10` | included/rated | internal | Nucleus; change requests for owned software |
| `MAN.3` | included/rated | internal | Nucleus; project management of this increment |
| `MAN.5` | included/rated | internal | Nucleus; risk management of this increment |
| `MAN.6` | included/rated | internal | Nucleus; measurement of this increment |
| `SYS.1` | out of scope/not rated | external | No complete-system owner; no internal SYS.1 (`0020-03` system row) |
| `SYS.2` | out of scope/not rated | external | Same |
| `SYS.3` | out of scope/not rated | external | Same |
| `SYS.4` | out of scope/not rated | external | Same; complete-ECU integration not this increment |
| `SYS.5` | out of scope/not rated | external | Same |
| `VAL.1` | out of scope/not rated | external | Intended-use validation not shown as owned (`0020-03` VAL.1 `not-decided`; 20-process profile not selected) |
| `HWE.1` | out of scope/not rated | external | Hardware not this increment (`DEC-0020-001`) |
| `HWE.2` | out of scope/not rated | external | Same |
| `HWE.3` | out of scope/not rated | external | Same |
| `HWE.4` | out of scope/not rated | external | Same |
| `ACQ.4` | out of scope/not rated | external | No named contracted supplier (`0020-03` suppliers `not-decided`; `0020-05`) |
| `MLE.1` | out of scope/not rated | external | ML product responsibility not decided (`0020-03` / `0020-05`) |
| `MLE.2` | out of scope/not rated | external | Same |
| `MLE.3` | out of scope/not rated | external | Same |
| `MLE.4` | out of scope/not rated | external | Same |
| `SUP.11` | out of scope/not rated | external | No ML-data/machine-learning support process claimed (`0020-05`) |
| `PIM.3` | out of scope/not rated | external | Organizational process improvement not selected for rating (`0020-05`) |
| `REU.2` | out of scope/not rated | external | No reuse-product mandate stated (`0020-05`) |

**Included/rated count:** 14. **Out of scope/not rated:** 18. **Shared rows:** 0.

No shared-process internal execution gate or external interface/acceptance gate is registered, because no process is `shared`.

Cybersecurity (`SEC` / ISO/SAE 21434) and ISO 26262 are **not** among the 32 PAM 4.0 processes; they remain Task `0020-06`.

---

## 6. Open decisions (not filled)

| ID | Decision | Owner |
|---|---|---|
| `PD-0020-04-01` | Later add any SYS/VAL if ownership appears | `0020-04` revision after new Management/`0020-03` change |
| `PD-0020-04-02` | Include any of `ACQ.4` / `MLE.*` / `SUP.11` / `PIM.3` / `REU.2` | Task `0020-05` |
| `PD-0020-04-03` | Named shared party | Management / `0020-03` revision |

---

## 7. Exclusions

Architecture of tools; `Acceptance: ✓`; Feature integration; `main`; Feature `0033`; overwriting `0020-02`/`0020-03` claims; inventing a customer, kernel inclusion, or 20-process profile.
