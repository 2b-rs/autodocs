# Automotive ECU Pre-Assessment Evidence Catalogue & Index (0018-04)

## 1. Document Control & Governance Metadata
- **Index ID**: `ECU-PREASSESSMENT-INDEX-virtualized-automotive-ecu@software-without-kernel:v0.7.0-pilot1`
- **Schema**: `ecu-preassessment-evidence-index@v1`
- **Product ID**: `virtualized-automotive-ecu`
- **Assessed Baseline**: `virtualized-automotive-ecu@software-without-kernel:v0.7.0-pilot1` (Commit: `8b2c49f`)
- **Reference Standard**: Automotive SPICE PAM 3.1 / PAM 4.0 Capability Level 2 (Managed Process)
- **Lead Assessor**: odo (Lead Assessor, Team DeepSpace9)
- **Project Sponsor**: jadzia (Project Lead, Team DeepSpace9)
- **Dispatcher**: benjamin (Team DeepSpace9)
- **Freeze Date**: 2026-09-19
- **Evidence Index Status**: **`FROZEN_FOR_ASSESSMENT_EXECUTION`**

---

## 2. Pre-Assessment Evidence Catalogue Summary

Under Task `0018-04`, the pre-assessment ECU evidence index has been validated and frozen.
- **Total Scoped Processes**: **17**
- **Total Frozen Work Products**: **34** (2 per process instance)
- **Origin Classifications**: Genuine `ecu-execution` (compiled binaries, unit/integration/qualification/HIL test logs) and `controlled-scenario` (specifications, architecture, plans, records).
- **Interview Records Governance**: In accordance with ISO/IEC 33020 and Automotive SPICE assessment rules, interview session records (`SESS-PILOT-01` through `SESS-PILOT-06`) are generated and versioned dynamically during the assessment interview battery; they are excluded from the static pre-assessment evidence baseline freeze.

---

## 3. Evidence Matrix by Process Instance & Attribute Mapping

| Process ID | Process Name | Artifact ID | Work Product Name | Owner | Origin | Process Attributes |
| :---: | :--- | :---: | :--- | :--- | :---: | :---: |
| **`SWE.1`** | Software Requirements Analysis | `ART-SWE1-REQ-01` | `swe1-software-requirements.json` | julian | `controlled-scenario` | PA 1.1, PA 2.1, PA 2.2 |
| **`SWE.1`** | Software Requirements Analysis | `ART-SWE1-TRACE-01` | `swe1-requirements-verification-matrix.json` | julian | `controlled-scenario` | PA 1.1, PA 2.2 |
| **`SWE.2`** | Software Architectural Design | `ART-SWE2-ARCH-01` | `swe2-software-architecture.json` | kira | `controlled-scenario` | PA 1.1, PA 2.1, PA 2.2 |
| **`SWE.2`** | Software Architectural Design | `ART-SWE2-ICD-01` | `swe2-interface-control-document.json` | kira | `controlled-scenario` | PA 1.1, PA 2.1, PA 2.2 |
| **`SWE.3`** | Software Detailed Design & Unit Construction | `ART-SWE3-CODE-01` | `swc_safety.c` | miles | `ecu-execution` | PA 1.1, PA 2.1, PA 2.2 |
| **`SWE.3`** | Software Detailed Design & Unit Construction | `ART-SWE3-MISRA-01` | `swe3-misra-compliance-report.json` | miles | `controlled-scenario` | PA 1.1, PA 2.2 |
| **`SWE.4`** | Software Unit Verification | `ART-SWE4-REPORT-01` | `swe4-unit-verification-report.json` | nog | `ecu-execution` | PA 1.1, PA 2.1, PA 2.2 |
| **`SWE.4`** | Software Unit Verification | `ART-SWE4-COVERAGE-01` | `swe4-mcdc-coverage-summary.json` | nog | `ecu-execution` | PA 1.1, PA 2.2 |
| **`SWE.5`** | Software Integration & Verification | `ART-SWE5-REPORT-01` | `swe5-integration-report.json` | obrien | `ecu-execution` | PA 1.1, PA 2.1, PA 2.2 |
| **`SWE.5`** | Software Integration & Verification | `ART-SWE5-BINARY-01` | `swe5-integrated-binary-manifest.json` | obrien | `ecu-execution` | PA 1.1, PA 2.2 |
| **`SWE.6`** | Software Qualification Testing | `ART-SWE6-REPORT-01` | `swe6-qualification-report.json` | jake & nog | `ecu-execution` | PA 1.1, PA 2.1, PA 2.2 |
| **`SWE.6`** | Software Qualification Testing | `ART-SWE6-VERDICT-01` | `swe6-release-candidate-verdict.json` | jake | `controlled-scenario` | PA 1.1, PA 2.2 |
| **`SYS.2`** | System Requirements Analysis | `ART-SYS2-REQ-01` | `sys2-system-requirements.json` | julian | `controlled-scenario` | PA 1.1, PA 2.1, PA 2.2 |
| **`SYS.2`** | System Requirements Analysis | `ART-SYS2-TRACE-01` | `sys2-to-swe1-allocation-matrix.json` | julian | `controlled-scenario` | PA 1.1, PA 2.2 |
| **`SYS.3`** | System Architectural Design | `ART-SYS3-ARCH-01` | `sys3-system-architecture.json` | kira | `controlled-scenario` | PA 1.1, PA 2.1, PA 2.2 |
| **`SYS.3`** | System Architectural Design | `ART-SYS3-HSI-01` | `sys3-hsi-specification.json` | kira | `controlled-scenario` | PA 1.1, PA 2.1, PA 2.2 |
| **`VAL.1`** | System & ECU Operational Validation | `ART-VAL1-REPORT-01` | `val1-validation-report.json` | jake | `ecu-execution` | PA 1.1, PA 2.1, PA 2.2 |
| **`VAL.1`** | System & ECU Operational Validation | `ART-VAL1-SAFETY-01` | `val1-safety-validation-signoff.json` | odo | `controlled-scenario` | PA 1.1, PA 2.2 |
| **`SPL.2`** | Product Release | `ART-SPL2-DOSSIER-01` | `spl2-release-dossier.json` | obrien & jadzia | `controlled-scenario` | PA 1.1, PA 2.1, PA 2.2 |
| **`SPL.2`** | Product Release | `ART-SPL2-MANIFEST-01` | `spl2-release-manifest.json` | obrien | `controlled-scenario` | PA 1.1, PA 2.2 |
| **`SUP.1`** | Quality Assurance | `ART-SUP1-AUDIT-01` | `sup1-qa-audit-summary.json` | jake | `controlled-scenario` | PA 1.1, PA 2.1, PA 2.2 |
| **`SUP.1`** | Quality Assurance | `ART-SUP1-LOG-01` | `sup1-nonconformance-log.json` | jake | `controlled-scenario` | PA 1.1, PA 2.1, PA 2.2 |
| **`SUP.8`** | Configuration Management | `ART-SUP8-AUDIT-01` | `sup8-baseline-audit-report.json` | obrien | `controlled-scenario` | PA 1.1, PA 2.1, PA 2.2 |
| **`SUP.8`** | Configuration Management | `ART-SUP8-INV-01` | `sup8-configuration-item-inventory.json` | obrien | `controlled-scenario` | PA 1.1, PA 2.2 |
| **`SUP.9`** | Problem Resolution Management | `ART-SUP9-LOG-01` | `sup9-problem-resolution-log.json` | benjamin | `controlled-scenario` | PA 1.1, PA 2.1, PA 2.2 |
| **`SUP.9`** | Problem Resolution Management | `ART-SUP9-METRIC-01` | `sup9-defect-aging-metrics.json` | benjamin | `controlled-scenario` | PA 1.1, PA 2.1 |
| **`SUP.10`** | Change Request Management | `ART-SUP10-CCB-01` | `sup10-ccb-decision-records.json` | jadzia & kira | `controlled-scenario` | PA 1.1, PA 2.1, PA 2.2 |
| **`SUP.10`** | Change Request Management | `ART-SUP10-IMPACT-01` | `sup10-change-impact-analysis.json` | kira | `controlled-scenario` | PA 1.1, PA 2.1, PA 2.2 |
| **`MAN.3`** | Project Management | `ART-MAN3-PLAN-01` | `man3-project-management-plan.md` | jadzia | `controlled-scenario` | PA 1.1, PA 2.1 |
| **`MAN.3`** | Project Management | `ART-MAN3-SIGNOFF-01` | `man3-milestone-signoff-summary.json` | jadzia | `controlled-scenario` | PA 1.1, PA 2.1, PA 2.2 |
| **`MAN.5`** | Risk Management | `ART-MAN5-RISK-01` | `man5-risk-register.json` | odo | `controlled-scenario` | PA 1.1, PA 2.1, PA 2.2 |
| **`MAN.5`** | Risk Management | `ART-MAN5-MITIG-01` | `man5-risk-mitigation-verification.json` | odo | `controlled-scenario` | PA 1.1, PA 2.1, PA 2.2 |
| **`MAN.6`** | Measurement | `ART-MAN6-REPORT-01` | `man6-measurement-report.json` | jake | `controlled-scenario` | PA 1.1, PA 2.1, PA 2.2 |
| **`MAN.6`** | Measurement | `ART-MAN6-DASHBOARD-01` | `man6-metric-trends-dashboard.json` | jake | `controlled-scenario` | PA 1.1, PA 2.1, PA 2.2 |

---

## 4. Isolation & Authenticity Safeguards

- [x] **Zero Documentation Campaign Evidence**: Zero execution evidence or synthetic ratings from Feature 0019/documentation campaigns imported into the ECU pre-assessment baseline.
- [x] **100% Authenticity Verification**: 34/34 work products cryptographically verified and frozen under baseline `virtualized-automotive-ecu@software-without-kernel:v0.7.0-pilot1`.
- [x] **Unresolved Limitations**: 0 blocking limitations identified.
- [x] **Canonical Evidence Index**: Frozen at [`docs/dossiers/assessment/ECU-PREASSESSMENT-EVIDENCE-INDEX-v0.7.0.json`](file:///Users/tobias.anton/devel/autodocs/docs/dossiers/assessment/ECU-PREASSESSMENT-EVIDENCE-INDEX-v0.7.0.json).
