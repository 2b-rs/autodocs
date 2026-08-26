# Requirements — Level-1 assessment input and official-outcome worksheets (`0020-07`)

**Item:** Task `0020-07` of Feature `0020`
**Role:** Requirements Engineer (`hguh`)
**Claim:** `TODO-hguh-0020-07-20260826T130400Z.md`
**owner_token:** `agent:hguh:0020-07:20260826T130400Z`
**Recorded at:** `2026-08-26T13:06:00Z`

Mailbox `1787749412922-cb6e182f` is coordination, not authority.

This Task tailors worksheets for the selected 14-process profile. It does not conduct the assessment, assign a competent assessor, or claim CL1.

---

## 1. Provenance (preserved)

Task text: Tailor and approve the Level-1 assessment input and official-outcome worksheets: process instances, evidence/interview validation, sampling/aggregation, assessor competence/independence, outcome and PA 1.1 rationale, report format, confidentiality, and rule that CL1 requires `PA 1.1 = L` or `F` per named process.

Bound inputs: `DEC-0020-001` (software above kernel; kernel later); `0020-02` / `DEC-0020-002` (refuse-at-use for this Task’s assessment input); `0020-04` 14-process nucleus; `0020-05` no HWE/MLE/ACQ inclusion; `0020-06` PAM 4.0 is not 21434 or 26262 proof.

---

## 2. Atomic requirements

### `REQ-0020-07-01` — Process instances

Worksheets SHALL name one process instance per included process: `SWE.1`–`SWE.6`, `SPL.2`, `SUP.1`, `SUP.8`, `SUP.9`, `SUP.10`, `MAN.3`, `MAN.5`, `MAN.6`, for increment `software-without-kernel`, `product_id=virtualized-automotive-ecu`, `project_id=autodocs-ecu-software`. Out-of-scope processes SHALL NOT receive an instance to be rated.

### `REQ-0020-07-02` — Evidence validation uses 0020-02 origins

Evidence offered on a worksheet SHALL carry the `0020-02` metadata and a canonical origin. For ECU outcome/PA 1.1 of this increment, origin SHALL be `ecu-execution`. `documentation-execution`, `controlled-scenario`, `process-definition`, and `implemented-mechanism` SHALL be refused as ECU execution (`DEC-0020-002` refuse-at-use). Interview notes SHALL be recorded separately from artifact evidence and SHALL NOT replace missing `ecu-execution`.

### `REQ-0020-07-03` — Sampling and aggregation

Sampling SHALL be per named process instance, not a fixed count. Aggregation SHALL NOT average ratings across different processes. A process instance SHALL NOT be aggregated from mixed `product_id` / `project_id` / `process_instance_id` / `baseline_id` (`REQ-0020-05`).

### `REQ-0020-07-04` — Assessor competence and independence

Worksheets SHALL record: (a) competence against PAM 4.0 Level 1 for the 14 processes; (b) independence from the implementer of the assessed instance; (c) that `0020-01` Management waiver of competent-assessor countersignature does **not** fill this field. Until a named assessor is assigned, the field SHALL read `not-named` and the worksheet SHALL NOT be treated as a completed assessment.

### `REQ-0020-07-05` — Outcome and PA 1.1 rationale

Each official-outcome worksheet SHALL contain: process ID; instance bound; each official PAM outcome; validated evidence identity (artifact ID, revision, origin, baseline); interview/observation corroboration if any; outcome achievement; strengths, weaknesses, contrary evidence; sampling/aggregation rationale; PA 1.1 rating rationale. Checklist arithmetic and averaging across processes SHALL be forbidden.

### `REQ-0020-07-06` — CL1 rule

CL1 for a named process SHALL require `PA 1.1 = L` or `F` for that process. `N` or `P` SHALL NOT be reported as CL1. Out-of-scope processes SHALL receive no CL1 claim.

### `REQ-0020-07-07` — Report format

The Level-1 report SHALL include: scope (`DEC-0020-001` sentence verbatim); process instances; method; evidence baseline; outcome judgments; per-process PA 1.1 and CL; strengths/weaknesses/risks; assessment disposition vs execution responsibility; findings. It SHALL state that PAM 4.0 results are not ISO/SAE 21434 or ISO 26262 proof (`0020-06`).

### `REQ-0020-07-08` — Confidentiality

Worksheets and the report SHALL be classified at least `internal` for this increment unless Management names a public assessment. Kernel, hardware, and complete-ECU claims SHALL NOT appear.

### `REQ-0020-07-09` — Worksheets are input, not a rating

Completing this Task SHALL produce the tailored blank worksheets and rules. Filling ratings remains a later assessment Task (`0025`). This Task SHALL NOT assign `N/P/L/F`.

---

## 3. Official-outcome worksheet (template)

For each of the 14 included processes:

1. Process ID and instance ID (`<process>-sw-nokernel-1`).
2. Purpose and organizational responsibility: `internal` software above kernel (`0020-03`/`0020-04`).
3. Official PAM outcomes (from PAM 4.0 for that process) — one row each: evidence ID, revision, origin, baseline, owner, location; interview Y/N; outcome judgment (blank until `0025`); contrary evidence.
4. PA 1.1 rationale (blank until `0025`).
5. Resulting CL (blank until `0025`; rule: CL1 only if PA 1.1 = L or F).

---

## 4. Assessment-input worksheet (template)

| Field | This increment |
|---|---|
| Assessed unit | Virtualized automotive ECU software; kernel excluded |
| Permitted claim | Verbatim `DEC-0020-001` sentence |
| Profile | 14-process nucleus |
| Instances | One per included process, §2 |
| Exclusions | SYS.1–SYS.5, VAL.1, HWE.*, ACQ.4, MLE.*, SUP.11, PIM.3, REU.2, CS/FS lifecycles |
| Evidence rule | `ecu-execution` + required metadata; refuse substitution (`DEC-0020-002`) |
| Assessor | `not-named` |
| Confidentiality | internal |
| CL1 rule | PA 1.1 = L or F per named included process |

---

## 5. Open decisions

| ID | Decision |
|---|---|
| `PD-0020-07-01` | Named competent assessor and independence evidence |
| `PD-0020-07-02` | Actual sample of process instances beyond one-per-process default |
| `PD-0020-07-03` | Public vs internal report distribution |

---

## 6. Exclusions

Filled ratings; `Acceptance: ✓`; Feature integration; `main`; Feature `0033`; implementing `0020-08`/`09` or `0025` freeze; presenting PAM as 21434/26262; overwriting prior 0020 tokens.
