# Automotive ECU Pilot Finding Triage & Remediation Governance (0018-06)

## 1. Document Control & Governance Metadata
- **Document ID**: `ECU-PILOT-TRIAGE-virtualized-automotive-ecu@software-without-kernel:v0.7.0-pilot1`
- **Schema**: `ecu-pilot-finding-triage-record@v1`
- **Product ID**: `virtualized-automotive-ecu`
- **Assessed Baseline**: `virtualized-automotive-ecu@software-without-kernel:v0.7.0-pilot1` (Commit: `8b2c49f`)
- **Reference Standard**: Automotive SPICE PAM 3.1 / PAM 4.0 (SUP.9 Problem Resolution & SUP.10 Change Management)
- **Triage Committee Chair**: jadzia (Project Lead, Team DeepSpace9)
- **Lead Assessor**: odo (Lead Assessor, Team DeepSpace9)
- **Problem Dispatcher**: benjamin (Dispatcher, Team DeepSpace9)
- **QA Manager**: jake (QA-Manager, Team DeepSpace9)
- **Date**: 2026-09-19
- **Triage Verdict**: **`ALL 5 FINDINGS TRIAGED, BOUNDED, AND ASSIGNED (3 APPROVED CORRECTIONS, 2 ACCEPTED RESIDUALS)`**

---

## 2. Executive Triage Summary

Under Task `0018-06`, all 5 findings and Opportunities for Improvement (OFI) identified during the Level-2 internal assessment (`0018-05`) were formally triaged under SUP.9 problem resolution and SUP.10 change control governance.

### Governance Rules Applied:
1. **Root Cause & Impact Rigor**: Every finding includes a technical root-cause investigation and quantified impact assessment.
2. **Binding Ownership & Due Dates**: Assigned directly to qualified process owners with firm delivery dates.
3. **Dispositions**:
   - **Approved Corrections (3)**: Bounded remediation tasks created with traceable Problem Reports (PR) and Change Requests (CR) requiring re-verification.
   - **Accepted Residuals (2)**: Formally documented with risk rationale and roadmap milestone tracking.
4. **Cross-Campaign Boundary Safeguards**: Zero Feature 0019/documentation campaign execution ratings imported.

---

## 3. Finding Triage & Remediation Task Matrix

| Finding ID | Process | Category | Title | Owner | Disposition | Governance Ref | Child Remediation Task | Due Date |
| :---: | :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| **`FIND-0018-01`** | `SWE.1` | `OBSERVATION` | Automated JSON Schema Linting in Pre-Commit Hooks | julian | `APPROVED_CORRECTION` | `DEC-0018-TRIAGE-01` | **`TASK-REM-0018-01`** | `2026-11-15` |
| **`FIND-0018-02`** | `SWE.3` | `OFI` | Automated MISRA Inline Suppression Scraper | miles | `APPROVED_CORRECTION` | `DEC-0018-TRIAGE-02` | **`TASK-REM-0018-02`** | `2026-11-30` |
| **`FIND-0018-03`** | `SWE.5` | `OFI` | Virtual QEMU Peripheral Emulation Expansion | obrien | `ACCEPTED_RESIDUAL` | `DEC-0018-TRIAGE-03` | **`TASK-REM-0018-03`** | `2026-12-01` |
| **`FIND-0018-04`** | `MAN.3` | `OBSERVATION` | Sprint Earned Value ASCII Sparkline in CLI | jadzia | `APPROVED_CORRECTION` | `DEC-0018-TRIAGE-04` | **`TASK-REM-0018-04`** | `2026-11-15` |
| **`FIND-0018-05`** | `MAN.6` | `OFI` | Defect Density Forecasting using ARIMA Models | jake | `ACCEPTED_RESIDUAL` | `DEC-0018-TRIAGE-05` | **`TASK-REM-0018-05`** | `2026-12-15` |

---

## 4. Re-Verification Protocols for Approved Corrections

### 1. `TASK-REM-0018-01` (`SWE.1` Pre-Commit JSON Linting)
- **Re-verification Protocol**:
  1. Trigger local git pre-commit hook against invalid JSON payloads in `docs/pipeline/` and `docs/dossiers/`; verify hook blocks commit with line/column diagnostic.
  2. Verify clean JSON commits complete in <= 150ms.
  3. Verify 0 regressions on CI pytest suite.

### 2. `TASK-REM-0018-02` (`SWE.3` MISRA Suppression Scraper)
- **Re-verification Protocol**:
  1. Parse C source units containing inline PRQA/Cppcheck comments.
  2. Confirm 100% parity between extracted annotations and generated MISRA audit appendix.
  3. Verify 0 unreferenced suppression tags.

### 3. `TASK-REM-0018-04` (`MAN.3` Terminal Sparkline EV Curves)
- **Re-verification Protocol**:
  1. Execute `ecu_pilot_execution.py --summary`.
  2. Verify deterministic terminal ASCII sparkline rendering across Linux/macOS environments.
  3. Verify unit test pass in `test_ecu_pilot_execution.py`.
