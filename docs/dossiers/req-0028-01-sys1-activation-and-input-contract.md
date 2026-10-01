# `REQ-0028-01` — Fail-Closed SYS.1 Activation and Input-Authority Contract

- **Record format:** `requirement-contract@v1`
- **Feature / Task:** `0028-01`
- **Governing Architecture:** `DEC-0028-001`, `DEC-0022-001`, `DEC-0020-002`
- **Status:** `DRAFT-ACTIVATED-FAIL-CLOSED`

---

## 1. Activation & Governance Rules
1. **Append-Only Disposition**: `SYS.1` process execution may only occur if an explicit Management disposition in `_src/spec/projects.json` or `TODO.md` marks `SYS.1` as `included/rated` and `internal` or `shared`.
2. **Current Baseline State**: Under the current 14-process ECU nucleus (`DEC-0020-001`), `SYS.1` is **`out of scope / not rated`** and `external`.
3. **Fail-Closed Refusal**: Any attempt to ingest external stakeholder inputs without named performer, explicit acceptance authority, and verified configuration baseline must be rejected.

---

## 2. Six Validation Cases (Positive & Negative Matrices)
| Case ID | Type | Condition / Description | Expected Verdict | Reason |
|---|---|---|---|---|
| `VAL-SYS1-01` | Positive | Approved profile + named performer + acceptance authority + valid baseline | **PASS** | Conforms to all activation criteria |
| `VAL-SYS1-02` | Negative | Selected profile is `out of scope / not rated` | **REFUSED** | Profile excludes internal SYS.1 performance |
| `VAL-SYS1-03` | Negative | Unnamed / `not-decided` performer | **REFUSED** | Missing performer responsibility identity |
| `VAL-SYS1-04` | Negative | Unnamed / `not-decided` acceptance authority | **REFUSED** | Missing acceptance authority token |
| `VAL-SYS1-05` | Negative | Stale or unpinned baseline digest | **REFUSED** | Baseline integrity cannot be verified |
| `VAL-SYS1-06` | Negative | Undefined assessed-unit outcomes | **REFUSED** | Shared boundary outcomes not specified |
