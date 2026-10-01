# Requirements — ECU responsibility/authority matrix (`0020-03`)

**Item:** Task `0020-03` of Feature `0020`
**Role:** Requirements Engineer (`hguh`)
**Claim:** `TODO-hguh-0020-03-20260826T124500Z.md`
**owner_token:** `agent:hguh:0020-03:20260826T124500Z`
**Recorded at:** `2026-08-26T12:46:00Z`
**Capability class:** `unprivileged`

This document defines observable responsibility and authority. It does not choose architecture, accept work, rate PAM processes (`0020-04`), or include the kernel.

Mailbox assignment `1787748243064-de99f85e` is coordination, not authority.

---

## 1. Provenance (requester wording, preserved)

### 1.1 Task text

> Define the ECU responsibility/authority matrix across customer, system, software, hardware, ML, cybersecurity, functional safety, calibration, manufacturing/service, integration, validation, release, operations, and suppliers; record who performs, reviews, approves, accepts, monitors, communicates, and retains evidence at every lifecycle interface.

### 1.2 Management scope (`DEC-0020-001`), verbatim

> Wir entwickeln ausschließlich System- und Applikationssoftware für ein virtualisiertes Automotive-Steuergerät. Der Kernel befindet sich noch in Entwicklung und wird später hinzugefügt.

Working identifiers: `product_id=virtualized-automotive-ecu`, `project_id=autodocs-ecu-software`, `increment=software-without-kernel`.

`DEC-0020-001` already records: the unit does **not** own a complete ECU system lifecycle in this increment; it owns software at and above the kernel interface; kernel, OS, and HWE processes are out of this increment; no kernel, complete-ECU-system, or hardware/manufacturing capability may be claimed; `SYS.1`–`SYS.5` and `VAL.1` are added only when later `0020-03`/`0020-04` show actual owned responsibility.

### 1.3 Feature envelope (execution vs assessment)

Assessment disposition (`included/rated` or `out of scope/not rated`) is recorded **separately** from execution responsibility (`internal`, `shared`, or `external`). This Task records execution responsibility and authority. Task `0020-04` records assessment disposition.

---

## 2. Problem (not solution)

Feature `0020` cannot select processes by actual responsibility, and later SYS/VAL/HWE/ML/safety Features cannot start honestly, until each lifecycle interface names who performs, reviews, approves, accepts, monitors, communicates, and retains evidence. Management named the supplied-product bound; it did not name a customer, a kernel owner, or a 20-process system profile. The matrix must show that bound and leave unnamed facts open.

---

## 3. Terms used in the matrix

| Token | Meaning |
|---|---|
| `internal` | The assessed unit performs this role for this increment |
| `external` | Another party performs this role; the assessed unit does not claim it |
| `shared` | Both the assessed unit and an external party have named portions (requires both sides named) |
| `not-this-increment` | Excluded by `DEC-0020-001` until a later Management `DEC-0020-*` |
| `not-decided` | Management has not stated this fact; this Task does not invent it |

Authority columns (requester wording): **performs**, **reviews**, **approves**, **accepts**, **monitors**, **communicates**, **retains evidence**.

---

## 4. Atomic requirements

### `REQ-0020-03-01` — Matrix covers every named interface

- **Title:** Closed interface set
- **Description:** The system SHALL record a responsibility/authority row for each of: customer, system, software, hardware, ML, cybersecurity, functional safety, calibration, manufacturing/service, integration, validation, release, operations, and suppliers.
- **Acceptance intent:** Given this dossier, when the interface list is compared to the Task text, then each named interface has a row. A missing row fails.
- **Exclusions:** PAM process IDs (`SWE.1`, `SYS.2`, …) belong to `0020-04`.

### `REQ-0020-03-02` — Each row records the seven authority columns

- **Title:** Authority columns
- **Description:** For every interface row, the system SHALL record who performs, reviews, approves, accepts, monitors, communicates, and retains evidence, using the tokens in §3 or an explicit `not-decided` / `not-this-increment`.
- **Acceptance intent:** Given a row, when any of the seven columns is empty, that row fails.
- **Exclusions:** Named human identities; Management did not name them.

### `REQ-0020-03-03` — Software above the kernel is internal this increment

- **Title:** Software performance
- **Description:** For the **software** interface this increment, the assessed unit SHALL be recorded as `internal` for perform / review / approve / accept / monitor / communicate / retain of system and application software above the kernel interface.
- **Acceptance intent:** Matches `DEC-0020-001` “System- und Applikationssoftware”.
- **Exclusions:** Kernel and OS software.

### `REQ-0020-03-04` — Kernel is not this increment

- **Title:** Kernel exclusion
- **Description:** Kernel (and OS below the kernel interface) SHALL be `not-this-increment` for all seven columns until a later Management `DEC-0020-*`.
- **Acceptance intent:** The matrix does not assign `internal` kernel performance.
- **Exclusions:** None.

### `REQ-0020-03-05` — Hardware and manufacturing are not claimed

- **Title:** Hardware and manufacturing
- **Description:** **Hardware** and **manufacturing/service** SHALL be `not-this-increment` (or `external` if a later named supplier is recorded) for perform of HWE and manufacturing capability. This increment SHALL NOT claim hardware or manufacturing capability.
- **Acceptance intent:** Matches `DEC-0020-001` CON-03.
- **Exclusions:** Software-side interfaces to hardware (requirements/constraints received) may be recorded as `external` inputs without claiming HWE performance.

### `REQ-0020-03-06` — No complete system-lifecycle ownership

- **Title:** System interface
- **Description:** The **system** interface SHALL record that the assessed unit does **not** own a complete ECU system lifecycle this increment. `SYS.1`–`SYS.5` internal performance is therefore **not** claimed here. Whether any SYS process is later added for *actual owned responsibility* is Task `0020-04`.
- **Acceptance intent:** System row is not `internal` complete-system owner.
- **Exclusions:** Allocated software requirements received at the kernel interface remain `internal` software work (`REQ-0020-03-03`).

### `REQ-0020-03-07` — Validation intended-use is not assumed internal

- **Title:** Validation interface
- **Description:** **Validation** (intended-use `VAL.1`) SHALL NOT be recorded as `internal` complete-product validation this increment unless Management later assigns it. This dossier records it as `not-decided` pending `0020-04` actual-owned-responsibility.
- **Acceptance intent:** No `VAL.1` internal claim is invented here.
- **Exclusions:** Software verification against software requirements is software-interface work, not `VAL.1`.

### `REQ-0020-03-08` — Open interfaces stay open

- **Title:** Do not invent customer, ML, safety, calibration, operations, suppliers
- **Description:** **Customer**, **ML**, **cybersecurity**, **functional safety**, **calibration**, **operations**, and **suppliers** SHALL be `not-decided` where Management did not name a party or an internal performance duty. Cybersecurity and functional-safety model choice remains Task `0020-06`. ML/HWE/ACQ applicability remains Task `0020-05`.
- **Acceptance intent:** Those rows are not silently filled with a named customer, OEM, or internal safety/cyber org.
- **Exclusions:** Recording that no claim is made.

### `REQ-0020-03-09` — Integration and release of owned software

- **Title:** Software integration and release
- **Description:** **Integration** and **release** of the assessed unit’s *own software* (system and application software above the kernel) SHALL be `internal` for perform / review / approve / accept / retain of that software package. Integration or release of kernel, hardware, or the complete ECU product SHALL be `not-this-increment`.
- **Acceptance intent:** Distinguishes software-package integration/release from complete-ECU integration/release.
- **Exclusions:** Vehicle-level release.

### `REQ-0020-03-10` — Inspectable matrix work product

- **Title:** Contract exists
- **Description:** Task `0020-03` SHALL produce this inspectable matrix. It does not by itself add TODO start-gates beyond the existing `0020-04:0020-03` edge.
- **Acceptance intent:** This file on branch `0020-03` contains §5 table and §4 SHALLs.
- **Exclusions:** Mechanical enforcer.

---

## 5. Responsibility/authority matrix (this increment)

Party “assessed unit” = the virtualized automotive ECU software increment of `DEC-0020-001`. No other party is named.

| Interface | Performs | Reviews | Approves | Accepts | Monitors | Communicates | Retains evidence |
|---|---|---|---|---|---|---|---|
| customer | `not-decided` | `not-decided` | `not-decided` | `not-decided` | `not-decided` | `not-decided` | `not-decided` |
| system | `not-this-increment` (no complete-system owner) | `not-this-increment` | `not-this-increment` | `not-this-increment` | `not-this-increment` | `not-this-increment` | `not-this-increment` |
| software | `internal` | `internal` | `internal` | `internal` | `internal` | `internal` | `internal` |
| hardware | `not-this-increment` | `not-this-increment` | `not-this-increment` | `not-this-increment` | `not-this-increment` | `not-this-increment` | `not-this-increment` |
| ML | `not-decided` | `not-decided` | `not-decided` | `not-decided` | `not-decided` | `not-decided` | `not-decided` |
| cybersecurity | `not-decided` (`0020-06`) | `not-decided` | `not-decided` | `not-decided` | `not-decided` | `not-decided` | `not-decided` |
| functional safety | `not-decided` (`0020-06`) | `not-decided` | `not-decided` | `not-decided` | `not-decided` | `not-decided` | `not-decided` |
| calibration | `not-decided` | `not-decided` | `not-decided` | `not-decided` | `not-decided` | `not-decided` | `not-decided` |
| manufacturing/service | `not-this-increment` | `not-this-increment` | `not-this-increment` | `not-this-increment` | `not-this-increment` | `not-this-increment` | `not-this-increment` |
| integration (owned software) | `internal` | `internal` | `internal` | `internal` | `internal` | `internal` | `internal` |
| integration (kernel/hardware/complete ECU) | `not-this-increment` | `not-this-increment` | `not-this-increment` | `not-this-increment` | `not-this-increment` | `not-this-increment` | `not-this-increment` |
| validation (software verification) | `internal` | `internal` | `internal` | `internal` | `internal` | `internal` | `internal` |
| validation (intended-use `VAL.1`) | `not-decided` (`0020-04`) | `not-decided` | `not-decided` | `not-decided` | `not-decided` | `not-decided` | `not-decided` |
| release (owned software package) | `internal` | `internal` | `internal` | `internal` | `internal` | `internal` | `internal` |
| release (complete ECU product) | `not-this-increment` | `not-this-increment` | `not-this-increment` | `not-this-increment` | `not-this-increment` | `not-this-increment` | `not-this-increment` |
| operations | `not-decided` | `not-decided` | `not-decided` | `not-decided` | `not-decided` | `not-decided` | `not-decided` |
| suppliers | `not-decided` | `not-decided` | `not-decided` | `not-decided` | `not-decided` | `not-decided` | `not-decided` |

Kernel/OS is not a Task-listed interface name; it is bound by `REQ-0020-03-04` and `DEC-0020-001`.

---

## 6. Open product decisions (not filled)

| ID | Decision | Why open |
|---|---|---|
| `PD-0020-03-01` | Named customer / intended-use actor | Management did not name one |
| `PD-0020-03-02` | Kernel owner and when kernel is added | Later Management `DEC-0020-*` |
| `PD-0020-03-03` | Whether any `SYS.1`–`SYS.5` / `VAL.1` is actual owned responsibility | Task `0020-04` |
| `PD-0020-03-04` | ML internal vs external | Task `0020-05` |
| `PD-0020-03-05` | Cybersecurity and ISO 26262 internal vs external | Task `0020-06` |
| `PD-0020-03-06` | Named suppliers, calibration owner, operations owner | Not stated |

---

## 7. Affected interfaces (identified, not gated here)

Consumers of this matrix: `0020-04` (applicability), `0020-05`, `0020-06`, Features `0022`–`0032`. Existing start edge: `0020-04:0020-03`. This dossier does not add start-gates.

---

## 8. Assumptions and exclusions

**Assumptions:** `DEC-0020-001` is correct and current; `I`/`M`/`O`/`S` and evidence origins remain `0020-02`.

**Exclusions:** Architecture of tools; `Acceptance: ✓`; Feature `0020` integration; `main`; Feature `0033`; Task `0020-02` claim overwrite; consumer freeze gates; inventing a customer or kernel inclusion.
