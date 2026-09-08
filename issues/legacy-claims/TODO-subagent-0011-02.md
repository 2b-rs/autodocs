# Claim — Task 0011-02 (`req-0011-02-cl2-worksheets`)

**Item:** Task `0011-02` of Feature `0011`
**PREREQ:** `0011-02:0011-01`, `0011-02:0020-07`
**Recorded at:** `2026-08-28T21:54:00+02:00`
**Branch:** `chain-0020-benjamin-v2`
**Capability class:** `unprivileged`

---

## 1. Summary of Changes

Extended the single approved Level-1 assessment method and worksheets (`docs/dossiers/req-0020-07-level-1-worksheets.md` and `docs/pipeline/aspice-cl2-assessment-input.md`) for Automotive SPICE Capability Level 2 (CL2):
1. Created `docs/dossiers/req-0011-02-cl2-worksheets.md` establishing the normative requirements `REQ-0011-02-01` through `REQ-0011-02-08` for CL2 assessments across the 14 included processes (`SWE.1`–`SWE.6`, `MAN.3`, `MAN.5`, `MAN.6`, `SUP.1`, `SUP.8`, `SUP.9`, `SUP.10`, `SPL.2`).
2. Defined generic practices and evaluation criteria for **PA 2.1 (Performance Management)** and **PA 2.2 (Work Product Management)** without duplicating Level-1 outcome worksheets.
3. Specified strict aggregation and rating rules: CL2 requires `PA 1.1 >= L`, `PA 2.1 >= L`, and `PA 2.2 >= L` per process instance; prohibited cross-process averaging and opportunistic aggregation (`REQ-0020-05`).
4. Integrated refusal-at-use for substituted origins (`documentation-execution`, `controlled-scenario`, out-of-scope non-ECU origins) per `DEC-0020-002` and `REQ-0020-02-01..09`.
5. Updated `docs/pipeline/aspice-cl2-assessment-input.md` to reflect the complete 14-process scope, PA 2.1/2.2 attributes, assessor competence/independence rules, evidence validation rules, and report content structure.

---

## 2. Validation & Inspection

- Verified alignment with `DEC-0020-001` (virtualized automotive ECU software without kernel) and `DEC-0020-002` (refuse-at-use evidence boundary).
- Ensured no duplicate parallel assessment methods or premature capability level ratings are introduced.
- Verified that all 14 nucleus processes are systematically covered.

---

## 3. Exclusions & Unprivileged Status

- No privileged actions (`Acceptance: ✓`, Feature integration, moving to `DONE.md`, or main branch updates) performed.
- Rating values (`N/P/L/F`) are left blank as scaffolding for subsequent assessment tasks (`0025`).
