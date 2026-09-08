# Requirements — cybersecurity and functional-safety applicability (`0020-06`)

**Item:** Task `0020-06` of Feature `0020`
**Role:** Requirements Engineer (`hguh`)
**Claim:** `TODO-hguh-0020-06-20260826T130000Z.md`
**owner_token:** `agent:hguh:0020-06:20260826T130000Z`
**Recorded at:** `2026-08-26T13:01:00Z`

Mailbox `1787749147569-0bf53762` is coordination, not authority.

This Task decides whether CS/FS lifecycles are applicable as *owned* work this increment. It does not invent an ASIL, a CS process profile, or a named TARA/HARA owner.

---

## 1. Provenance (preserved)

Task text: Decide applicable Automotive SPICE for Cybersecurity model/version and ISO/SAE 21434 responsibilities, plus ISO 26262 functional-safety responsibilities; create separate dependency-linked Features for applicable cybersecurity or safety lifecycles, register their completion gates in the selected profile, and do not present generic PAM 4.0 evidence as proof of either framework.

`DEC-0020-001` (verbatim): exclusively system and application software for a virtualized automotive ECU; kernel later. No complete-system-lifecycle ownership. No CS or FS ownership stated.

`0020-03`: cybersecurity and functional-safety rows `not-decided` pending this Task; no named party.

`0020-04`: 14-process PAM 4.0 nucleus only; no CS `SEC` processes in that 32-process catalog.

Survey (`docs/ASPICE/01-assessment-basis-and-scope.md` §6): PAM 4.0 does not contain cybersecurity-specific `SEC` processes. Where applicable, this Task must select Automotive SPICE for Cybersecurity and ISO/SAE 21434 allocation. Functional safety requires a separate ISO 26262 lifecycle. Automotive SPICE process capability does not establish ASIL suitability or functional-safety compliance.

---

## 2. Decision

**This increment does not own a cybersecurity lifecycle or a functional-safety lifecycle.**

| Framework | Applicable as owned lifecycle this increment? | Model/version selected | Dependency-linked Features created | Gate in 14-process profile |
|---|---|---|---|---|
| Automotive SPICE for Cybersecurity | no | none | none | none |
| ISO/SAE 21434 | no | none | none | none |
| ISO 26262 | no | none (no ASIL claimed) | none | none |

**Included CS/FS Features:** 0.

Generic PAM 4.0 Level-1 evidence of the 14-process nucleus **is not** proof of 21434 or 26262.

---

## 3. Atomic requirements

### `REQ-0020-06-01` — No CS model selected this increment

No Automotive SPICE for Cybersecurity model/version SHALL be recorded as applicable for owned performance this increment. Justification: `DEC-0020-001` and `0020-03` show no CS ownership.

### `REQ-0020-06-02` — No 21434 owned responsibilities this increment

ISO/SAE 21434 activities SHALL NOT be claimed as internally performed. Unnamed CS risk/TARA ownership SHALL stay `not-decided` as a party name, and `not-included` as a lifecycle.

### `REQ-0020-06-03` — No 26262 owned lifecycle this increment

ISO 26262 SHALL NOT be claimed. No ASIL SHALL be assigned. ASPICE CL1 of PAM processes SHALL NOT be presented as functional-safety compliance.

### `REQ-0020-06-04` — Features only for applicable lifecycles

Separate CS/FS Features SHALL be created only if a lifecycle is applicable. This increment’s applicable set is empty, so **no** CS/FS Features are created.

### `REQ-0020-06-05` — No CS/FS completion gate in the selected profile

The selected 14-process profile (`0020-04`) SHALL NOT gain a CS or FS completion gate from this Task.

### `REQ-0020-06-06` — PAM 4.0 is not CS or FS evidence

Evidence produced under PAM 4.0 processes (`SWE.*`, `SUP.*`, `MAN.*`, `SPL.2`) SHALL NOT be offered as 21434 cybersecurity or 26262 functional-safety proof. That prohibition holds even if those processes are `included/rated`.

### `REQ-0020-06-07` — Later inclusion needs new Management

Selecting a CS model, 21434 allocation, or 26262 ASIL/lifecycle SHALL require a later Management `DEC-0020-*`. This Task does not pre-include them.

---

## 4. Interface (not absence)

CS and FS are **not included**, not “forgotten”:

| Field | Cybersecurity (21434 / ASPICE CS) | Functional safety (26262) |
|---|---|---|
| Inputs | None as owned CS work products | None as owned safety work products |
| Outputs | No CS case, TARA, or CS validation report from this unit | No safety case, HARA, or ASIL rating from this unit |
| Acceptance | This unit does not accept CS process performance | This unit does not accept FS process performance |
| Monitoring | Watch for a later Management CS inclusion | Watch for a later Management FS inclusion |
| Escalation | Request to perform CS → Management | Request to claim ASIL → Management |
| Configuration | No CS baseline owned | No safety baseline owned |
| Risk | Residual: unnamed CS owner; software still has ordinary `MAN.5` technical risk, which is not 21434 | Residual: unnamed FS owner; ASPICE ≠ ASIL |
| Evidence | This decision; PAM 4.0 items labeled not-CS | This decision; PAM 4.0 items labeled not-26262 |

---

## 5. Open decisions

| ID | Decision |
|---|---|
| `PD-0020-06-01` | Select ASPICE for Cybersecurity version and 21434 allocation |
| `PD-0020-06-02` | Select ISO 26262 edition, ASIL, and item definition |
| `PD-0020-06-03` | Name CS/FS responsible party |

All require new Management, not this record.

---

## 6. Exclusions

`Acceptance: ✓`; Feature integration; `main`; Feature `0033`; overwriting prior 0020 tokens; inventing an ASIL; treating the 14-process nucleus as a CS or FS profile.
