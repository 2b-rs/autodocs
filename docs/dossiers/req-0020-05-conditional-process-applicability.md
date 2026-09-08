# Requirements — conditional PAM 4.0 process applicability (`0020-05`)

**Item:** Task `0020-05` of Feature `0020`
**Role:** Requirements Engineer (`hguh`)
**Claim:** `TODO-hguh-0020-05-20260826T125500Z.md`
**owner_token:** `agent:hguh:0020-05:20260826T125500Z`
**Recorded at:** `2026-08-26T12:56:00Z`

Mailbox `1787748842643-c77b9353` is coordination, not authority.

This Task decides inclusion of the conditional processes and records interfaces. It does not invent a supplier, include HWE/ML internally, accept work, or create empty execution Features.

---

## 1. Provenance (preserved)

Task text: Decide `ACQ.4`, `HWE.1`–`HWE.4`, `MLE.1`–`MLE.4`, `SUP.11`, `PIM.3`, and `REU.2` applicability; create dependency-linked execution Features/tasks for every **included** process. For every **shared** process register both the assessed unit's execution gate and the external interface gate; for every **fully external** process define controlled inputs, outputs, acceptance, monitoring, escalation, configuration, risk, and evidence interfaces rather than treating it as absent.

`DEC-0020-001`: software above the kernel only; kernel later; no hardware/manufacturing claim; HWE out of this increment.

`0020-03`: hardware and manufacturing `not-this-increment`; ML, suppliers `not-decided`; no named external party.

`0020-04`: these processes already `out of scope/not rated`, execution `external`; shared rows 0.

Survey inclusion rules (`docs/ASPICE/01-assessment-basis-and-scope.md` §5.3): `ACQ.4` when monitoring a contracted supplier; `HWE.*` per actual electronics responsibility; `MLE.*`/`SUP.11` per automotive ML product responsibility (not generative-AI coding assist); `PIM.3` when organizational improvement is to be rated; `REU.2` when reuse products are deliberately managed.

---

## 2. Decision

**None of the named processes is included this increment.**

| Process | Applicability | Execution | Execution Feature created? |
|---|---|---|---|
| `ACQ.4` | not included | fully external | no |
| `HWE.1` | not included | fully external | no |
| `HWE.2` | not included | fully external | no |
| `HWE.3` | not included | fully external | no |
| `HWE.4` | not included | fully external | no |
| `MLE.1` | not included | fully external | no |
| `MLE.2` | not included | fully external | no |
| `MLE.3` | not included | fully external | no |
| `MLE.4` | not included | fully external | no |
| `SUP.11` | not included | fully external | no |
| `PIM.3` | not included | fully external | no |
| `REU.2` | not included | fully external | no |

**Shared processes:** none. No dual execution/interface gates registered.

**Included-process Features/tasks created:** none (empty set is the honest count).

---

## 3. Atomic requirements

### `REQ-0020-05-01` — No silent inclusion

The listed processes SHALL remain not included unless a later Management `DEC-0020-*` or a named supplier/ML/reuse/PIM mandate appears. This Task SHALL NOT create execution Features for a zero-member included set.

### `REQ-0020-05-02` — HWE stays external this increment

`HWE.1`–`HWE.4` SHALL NOT be included. Justification: `DEC-0020-001` and `0020-03` hardware row.

### `REQ-0020-05-03` — ACQ.4 not included without a named supplier

`ACQ.4` SHALL NOT be included on public-tool or open-source use alone.

### `REQ-0020-05-04` — MLE/SUP.11 not included for assistant AI

`MLE.1`–`MLE.4` and `SUP.11` SHALL NOT be included because generative AI assisting documentation or coding is not automotive-product ML responsibility.

### `REQ-0020-05-05` — PIM.3 and REU.2 not selected for rating

`PIM.3` and `REU.2` SHALL NOT be included; no organizational improvement rating and no reuse-product mandate were stated.

### `REQ-0020-05-06` — Fully external processes have interfaces, not absence

For each process in §2, the system SHALL record the interface set in §4 (inputs, outputs, acceptance, monitoring, escalation, configuration, risk, evidence) so the process is not treated as absent.

### `REQ-0020-05-07` — No invented shared party

No process SHALL be recorded as shared until a named party exists.

---

## 4. Fully external interface records

Party on the far side is **unnamed** until Management names one. The assessed unit still has a control duty: do not claim the process, do not ignore the interface.

Common tokens: `assessed-unit` = virtualized automotive ECU software increment (`DEC-0020-001`).

### 4.1 `HWE.1`–`HWE.4` (electronics, fully external)

| Field | Record |
|---|---|
| Inputs to assessed unit | Hardware/virtualization constraints, MCU/board interface descriptions, and exclusion of kernel/HWE work products when supplied |
| Outputs from assessed unit | Software interface requirements and integration constraints allocated *to* hardware, not HWE process performance |
| Acceptance | Software does not accept hardware as its own HWE outcome; incoming hardware descriptions are labeled `external` / not `ecu-execution` of this unit |
| Monitoring | Watch for a later Management kernel/hardware inclusion (`DEC-0020-*`); no HWE capability claim meanwhile |
| Escalation | If a party asks this unit to perform HWE, escalate to Management; do not silently include |
| Configuration | Hardware identity, if received, is configuration input to `SUP.8` of *software*, not an HWE baseline owned here |
| Risk | Residual: unnamed hardware owner; software/hardware mismatch is a `MAN.5` risk of this increment, not HWE.3 performance |
| Evidence | Retain received hardware/interface artifacts with origin not `ecu-execution` of this unit; do not freeze them as HWE outcomes (`0020-02` / `0025-03`) |

### 4.2 `ACQ.4` (supplier monitoring, fully external)

| Field | Record |
|---|---|
| Inputs | None until a contracted supplier is named |
| Outputs | None until a supplier is named |
| Acceptance | No supplier work-product acceptance by this unit as `ACQ.4` |
| Monitoring | Detect appearance of a contracted supplier; public OSS/tools do not start `ACQ.4` |
| Escalation | Naming a supplier is Management / later `0020-03` revision |
| Configuration | No supplier CI owned |
| Risk | Unnamed-supplier gap recorded as residual, not as `ACQ.4` performance |
| Evidence | Absence of a named supplier is retained as this decision’s justification, not as supplier-monitoring evidence |

### 4.3 `MLE.1`–`MLE.4` and `SUP.11` (ML product / ML data, fully external)

| Field | Record |
|---|---|
| Inputs | None as ML training/data product; assistant-AI use in documentation is not MLE input |
| Outputs | No ML model/data product from this increment |
| Acceptance | No ML-model acceptance |
| Monitoring | If an automotive ML function is later in scope, `0020-05` is revised; assistant AI remains excluded |
| Escalation | Product-ML inclusion is Management |
| Configuration | No ML-data baseline owned |
| Risk | Mislabeling assistant AI as MLE; this record forbids that |
| Evidence | This decision; no MLE/SUP.11 execution evidence |

### 4.4 `PIM.3` (process improvement rating, fully external)

| Field | Record |
|---|---|
| Inputs | None as rated organizational improvement |
| Outputs | None as PIM.3 outcomes |
| Acceptance | No PIM.3 rating claimed |
| Monitoring | Optional later selection does not block the 14-process nucleus |
| Escalation | Selecting PIM.3 for rating is Management / later `0020-05` |
| Configuration | No PIM.3 register owned |
| Risk | Treating backlog hygiene as PIM.3 |
| Evidence | This exclusion; pipeline process docs remain `documentation-execution` (`0020-02`) |

### 4.5 `REU.2` (reuse products, fully external)

| Field | Record |
|---|---|
| Inputs | None as managed reuse-product intake |
| Outputs | This increment’s software is not offered as a `REU.2` reuse product |
| Acceptance | No reuse-product acceptance |
| Monitoring | Deliberate reuse-product management would reopen `0020-05` |
| Escalation | Management |
| Configuration | No reuse catalog owned |
| Risk | Counting generic libraries as `REU.2` |
| Evidence | This exclusion |

---

## 5. Included-process Features

**None.** The Task requires execution Features only for included processes. Creating placeholder Features for excluded processes would fake inclusion.

---

## 6. Open decisions

| ID | Decision |
|---|---|
| `PD-0020-05-01` | Name a supplier and include `ACQ.4` |
| `PD-0020-05-02` | Include kernel/HWE via new Management `DEC-0020-*` |
| `PD-0020-05-03` | Include product ML / `SUP.11` |
| `PD-0020-05-04` | Select `PIM.3` or `REU.2` for rating |

---

## 7. Exclusions

`Acceptance: ✓`; Feature integration; `main`; Feature `0033`; overwriting prior 0020 tokens; inventing a supplier; creating empty execution Features; treating assistant AI as MLE.
