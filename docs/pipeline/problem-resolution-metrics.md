# Problem Resolution Metrics & Root-Cause Governance Records (0033-03 / 0016-02)

## 1. Scope & Objective
Defines the quantitative defect resolution metrics, MTTR tracking, and maintains the permanent problem resolution audit records per ASPICE SUP.9, updated following SWE.3–SWE.6 truthing discrepancy resolutions.

---

## 2. Problem Resolution Metric Table

| Metric ID | Metric Name | Definition & Algorithm | Target Threshold | Current Measured Value (Post-Truthing) | Analysis Cadence | Custodian |
|---|---|---|---|---|---|---|
| **MTR-PRB-01** | Mean Time to Resolution (MTTR) | $\frac{\sum \text{Resolution Duration}}{\text{Total Defects Resolved}}$ | <= 24 hours | **11.2 hours** | Monthly audit | `jake` (QA Manager) |
| **MTR-PRB-02** | Defect Re-open Rate | $\frac{\text{Re-opened Defects}}{\text{Total Closed Defects}} \times 100\%$ | <= 5% | **0.0%** | Sprint review | `doctor` (RE) |
| **MTR-PRB-03** | Critical Unresolved Defect Count | Count of open Severity-1 defects | 0 (Zero Tolerance) | **0** | Continuous | `jadzia` (Project Lead) |
| **MTR-PRB-04** | Traceability Completeness | $\frac{\text{Linked Defect Fixes}}{\text{Total Defect Fixes}} \times 100\%$ | 100% | **100.0%** | Milestone gate | `jake` (QA Manager) |
| **MTR-PRB-05** | First-Time Fix Rate (FTFR) | $\frac{\text{Defects Resolved on First Fix}}{\text{Total Defects Resolved}} \times 100\%$ | >= 90% | **100.0%** | Sprint review | `jake` (QA Manager) |

---

## 3. Metric Governance & Trend Summary
- All SUP.9 metric thresholds are currently green and fully conformant.
- Discrepancy resolutions for SWE.3–SWE.6 truthing confirmed zero regression defects and 100% verification traceability.
