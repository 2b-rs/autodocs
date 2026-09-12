# MAN.6 Measurement Information Needs & Metrics (0017-04)

**Status:** Normative
**Reference:** Feature 0017-04 (Prerequisite `0012-08`)

This document defines the Management Information Needs (MIN) for the assessed ECU project and maps them to observable process/product metrics to fulfill ASPICE MAN.6 requirements. These metrics support the process performance strategy (PA 2.1) defined in `docs/pipeline/process-performance-strategy.md`.

## 1. Information Need: Quality & Outcome Conformance
**Goal:** Ensure the software correctly fulfills stated requirements with a high level of code and design quality.
- **Metric M-QUAL-01 (Review Closure Rate)**: Percentage of architectural decisions (`DEC-*`), PRs, and integration steps closed with an explicit `Acceptance: ✓` vs. total raised.
- **Metric M-QUAL-02 (Test Pass Rate)**: Ratio of passing unit/integration tests to total executed tests per CI run (Target: 100%).
- **Metric M-QUAL-03 (Fallback/Reject Count)**: Number of times an item is sent back for rework due to failing Four-Eyes review or automated gates.

## 2. Information Need: Effort & Schedule Predictability
**Goal:** Track execution against the MAN.3 project plan.
- **Metric M-SCH-01 (Effort Variance)**: Deviation between `planned_minutes` estimated in `TODO.md` and actual recorded elapsed time for completed tasks.
- **Metric M-SCH-02 (Milestone Slip)**: Number of days actual milestone completion (Campaign A-D) lags behind the planned target dates.

## 3. Information Need: Resource & Infrastructure Health
**Goal:** Monitor agent availability, quota exhaustion, and infrastructure stability.
- **Metric M-RES-01 (Provider Quota Usage)**: Moving average of API quota consumption (codex, claude, etc.) across 5-hour, weekly, and monthly bands.
- **Metric M-RES-02 (Agent Over-allocation)**: Incidents of agents concurrently assigned more than one `BUSY` task without formal proxy delegation.
- **Metric M-RES-03 (CI Failure Rate)**: Percentage of GitHub Action runs failing due to runner configuration, timeout, or external downtime rather than code defects.

## 4. Information Need: Traceability & Coverage
**Goal:** Prove the unbroken chain of custody from stakeholder need to executing code.
- **Metric M-TRC-01 (Requirement Coverage)**: Percentage of SWE.1 functional and non-functional requirements linked to SWE.2 architectural elements.
- **Metric M-TRC-02 (Test Coverage)**: Percentage of SWE.1 requirements explicitly tested in SWE.6 qualification tests.
- **Metric M-TRC-03 (Orphan Code Ratio)**: Number of SWE.3 software units or SWE.4 tests without an upstream SWE.2 interface definition.

## 5. Information Need: Defect & Change Management
**Goal:** Track system stability and volatility.
- **Metric M-DEF-01 (Defect Density)**: Number of recorded SUP.9 problems (defects) normalized per KLOC or per deployed module.
- **Metric M-DEF-02 (Defect Aging)**: Average time from SUP.9 issue opening to validated closure.
- **Metric M-DEF-03 (CR Volatility)**: Volume of SUP.10 Change Requests originating post-architecture-baseline per campaign.

## 6. Information Need: Release & Delivery Health
**Goal:** Measure readiness for final authorization.
- **Metric M-REL-01 (Known Issues Ratio)**: Count of open/accepted limitations packaged into the SPL.2 release manifest versus closed issues.
- **Metric M-REL-02 (Release Rejection Rate)**: Number of times a finalized release candidate fails Release Authority review or cryptographic integrity checks.

## 7. Information Need: User Validation
**Goal:** Measure success against the intended-use stakeholder requirements (once activated).
- **Metric M-USR-01 (Acceptance Scenario Pass Rate)**: Percentage of defined end-user operational scenarios successfully validated.
- **Metric M-USR-02 (Field Escalations)**: Volume of operations/diagnostics faults reported post-deployment. (Currently blocked pending assignment of operational scope).

## 8. Summary Traceability Matrix

| Information Need | Corresponding Metrics | Affected Processes |
|---|---|---|
| Outcome/Quality | M-QUAL-01, M-QUAL-02, M-QUAL-03 | SWE.4, SWE.5, SUP.1 |
| Schedule/Effort | M-SCH-01, M-SCH-02 | MAN.3 |
| Resources | M-RES-01, M-RES-02, M-RES-03 | MAN.3, SUP.8 |
| Coverage/Trace | M-TRC-01, M-TRC-02, M-TRC-03 | SWE.1, SWE.2, SWE.6 |
| Defects/Changes | M-DEF-01, M-DEF-02, M-DEF-03 | SUP.9, SUP.10 |
| Release Health | M-REL-01, M-REL-02 | SPL.2, SUP.8 |
| User Validation | M-USR-01, M-USR-02 | VAL |
