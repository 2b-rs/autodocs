# Automotive ECU Managed Pilot Process Selection & Assessment Plan (0018-01)

## 1. Document Control & Governance Metadata
- **Plan ID**: `ECU-PILOT-PLAN-virtualized-automotive-ecu@software-without-kernel:v0.7.0-pilot1`
- **Schema**: `ecu-pilot-assessment-plan@v1`
- **Product ID**: `virtualized-automotive-ecu`
- **Target Release Baseline**: `virtualized-automotive-ecu@software-without-kernel:v0.7.0-pilot1` (Predecessor: `virtualized-automotive-ecu@software-without-kernel:v0.6.0-rev1`)
- **Target Commit**: `8b2c49f`
- **Reference Standard**: Automotive SPICE PAM 3.1 / PAM 4.0 Reference Model (CL2 Managed Process)
- **Project Sponsor**: jadzia (Project Lead, Team DeepSpace9)
- **Lead Assessor**: odo (Lead Assessor, Team DeepSpace9)
- **QA Authority**: jake (QA-Manager, Team DeepSpace9)
- **Architect**: kira (Architect, Team DeepSpace9)
- **Approval Date**: 2026-09-19
- **Plan Status**: **`FORMALLY_APPROVED_FOR_EXECUTION`**
- **Plan SHA-256 Digest**: `db6b6adbc0ae804cf0417a80c1f86e3b96017511112fd031ea9e3f34026b2220`

---

## 2. Executive Pilot Scope Summary

- **Total Selected Process Instances**: **17**
- **Target Capability Level**: **Level 2 (Managed Process)**
- **Target Generic Practices**: GP 2.1 Performance Management, GP 2.2 Work Product Management
- **Planned Interview Sessions**: **6**
- **Sampling & Aggregation Rules**: **3**

---

## 3. Approved Pilot Process Instances

| Process ID | Process Name | Process Instance | Category | Target Level | Primary Owner | SWC Scope |
| :---: | :--- | :--- | :---: | :---: | :--- | :--- |
| **`SWE.1`** | Software Requirements Analysis | `PI-SWE1-202610-PILOT1` | `SOFTWARE_ENGINEERING` | **Level 2** | julian (Requirements Engineer) | SWC-SAFETY, SWC-CRYPTO, SWC-DIAG, SWC-TELEM |
| **`SWE.2`** | Software Architectural Design | `PI-SWE2-202610-PILOT1` | `SOFTWARE_ENGINEERING` | **Level 2** | kira (Architect) | SWC-SAFETY, SWC-CRYPTO, SWC-DIAG, SWC-TELEM |
| **`SWE.3`** | Software Detailed Design & Unit Construction | `PI-SWE3-202610-PILOT1` | `SOFTWARE_ENGINEERING` | **Level 2** | miles (Software Developer) | SWC-SAFETY, SWC-CRYPTO, SWC-DIAG, SWC-TELEM |
| **`SWE.4`** | Software Unit Verification | `PI-SWE4-202610-PILOT1` | `SOFTWARE_ENGINEERING` | **Level 2** | nog (Tester) | SWC-SAFETY, SWC-CRYPTO, SWC-DIAG, SWC-TELEM |
| **`SWE.5`** | Software Integration & Verification | `PI-SWE5-202610-PILOT1` | `SOFTWARE_ENGINEERING` | **Level 2** | obrien (Integrator) | SWC-SAFETY, SWC-CRYPTO, SWC-DIAG, SWC-TELEM |
| **`SWE.6`** | Software Qualification Testing | `PI-SWE6-202610-PILOT1` | `SOFTWARE_ENGINEERING` | **Level 2** | jake (QA-Manager) & nog (Tester) | SWC-SAFETY, SWC-CRYPTO, SWC-DIAG, SWC-TELEM |
| **`SYS.2`** | System Requirements Analysis | `PI-SYS2-202610-PILOT1` | `SYSTEM_ENGINEERING` | **Level 2** | julian (Requirements Engineer) | ECU-SYSTEM |
| **`SYS.3`** | System Architectural Design | `PI-SYS3-202610-PILOT1` | `SYSTEM_ENGINEERING` | **Level 2** | kira (Architect) | ECU-SYSTEM |
| **`VAL.1`** | System & ECU Operational Validation | `PI-VAL1-202610-PILOT1` | `VALIDATION` | **Level 2** | jake (Validation Lead) & odo (Safety) | ECU-SYSTEM |
| **`SPL.2`** | Product Release | `PI-SPL2-202610-PILOT1` | `RELEASE` | **Level 2** | obrien (Integrator) & jadzia (Project Lead) | ECU-SYSTEM |
| **`SUP.1`** | Quality Assurance | `PI-SUP1-202610-PILOT1` | `SUPPORTING` | **Level 2** | jake (QA-Manager) | ALL-PROCESSES |
| **`SUP.8`** | Configuration Management | `PI-SUP8-202610-PILOT1` | `SUPPORTING` | **Level 2** | obrien (Integrator) | ALL-PROCESSES |
| **`SUP.9`** | Problem Resolution Management | `PI-SUP9-202610-PILOT1` | `SUPPORTING` | **Level 2** | benjamin (Dispatcher) | ALL-PROCESSES |
| **`SUP.10`** | Change Request Management | `PI-SUP10-202610-PILOT1` | `SUPPORTING` | **Level 2** | jadzia (Project Lead) & kira (Architect) | ALL-PROCESSES |
| **`MAN.3`** | Project Management | `PI-MAN3-202610-PILOT1` | `MANAGEMENT` | **Level 2** | jadzia (Project Lead) | ALL-PROCESSES |
| **`MAN.5`** | Risk Management | `PI-MAN5-202610-PILOT1` | `MANAGEMENT` | **Level 2** | odo (Safety & Security Officer) | ALL-PROCESSES |
| **`MAN.6`** | Measurement | `PI-MAN6-202610-PILOT1` | `MANAGEMENT` | **Level 2** | jake (QA-Manager) | ALL-PROCESSES |

---

## 4. Planned Assessment Interview Battery & Schedule

| Session ID | Target Processes | Focus & Topics | Interviewees | Lead Assessor | Planned Date |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **`SESS-PILOT-01`** | MAN.3, SPL.2, SUP.10 | Project Governance, Scope Definition, Release Authorization, Change Management | jadzia (Project Lead), obrien (Integrator) | odo (Lead Assessor) | `2026-10-05` |
| **`SESS-PILOT-02`** | SYS.2, SWE.1 | Requirements Elicitation, Allocation, Testability & Traceability | julian (Requirements Engineer), kira (Architect) | odo (Lead Assessor) | `2026-10-06` |
| **`SESS-PILOT-03`** | SYS.3, SWE.2, SWE.3 | Architecture, MPU Partitioning, Detailed Design & MISRA Construction | kira (Architect), miles (Software Developer) | odo (Lead Assessor) | `2026-10-07` |
| **`SESS-PILOT-04`** | SWE.4, SWE.5, SWE.6 | Unit MC-DC Verification, Integration Testing & Software Qualification | nog (Tester), obrien (Integrator), jake (QA-Manager) | odo (Lead Assessor) | `2026-10-08` |
| **`SESS-PILOT-05`** | VAL.1, MAN.5 | HIL Operational Validation, CAN Fault Injection & Risk Mitigation | jake (Validation Lead), odo (Safety Officer) | kira (Independent Assessor) | `2026-10-09` |
| **`SESS-PILOT-06`** | SUP.1, SUP.8, SUP.9, MAN.6 | Quality Assurance Audits, CM Baseline Governance, Defect Lifecycle, Metrics | jake (QA-Manager), obrien (Integrator), benjamin (Dispatcher) | odo (Lead Assessor) | `2026-10-10` |

---

## 5. Risk-Informed Adaptive Sampling & Aggregation Rules

### SAMP-RULE-01: Safety-Critical Software Components (SWC-SAFETY, SWC-CRYPTO)
- **Methodology**: 100% Census Audit (Exhaustive Verification)

#### Governance Criteria
- [x] 100% Statement, 100% Branch, 100% MC-DC structural unit coverage required.
- [x] Zero MISRA C:2012 violations allowed.
- [x] 100% bidirectional traceability to safety/security requirements.

#### Prohibited Practices
- [x] **PROHIBITED**: No statistical down-sampling of safety-critical functions.
- [x] **PROHIBITED**: No exclusion of fault-injection or boundary cases.

---

### SAMP-RULE-02: General Diagnostic & Telemetry Components (SWC-DIAG, SWC-TELEM)
- **Methodology**: Risk-Informed Representative Sampling

#### Governance Criteria
- [x] Exhaustive testing of state machine transitions and UDS service handlers.
- [x] Coverage sampling representative of all operational communication modes.

#### Prohibited Practices
- [x] **PROHIBITED**: No arbitrary fixed count sampling (must be risk-justified).
- [x] **PROHIBITED**: No averaging of pass rates across heterogeneous components.

---

### SAMP-RULE-03: Cross-Campaign Evidence Isolation Policy
- **Methodology**: Strict Boundary Segregation for Execution Evidence

#### Governance Criteria
- [x] ECU execution evidence must originate exclusively from genuine compiled C code running on virtual/target hardware.
- [x] Documentation campaigns (such as Feature 0019) may provide reusable definitions, schemas, and governance templates only.

#### Prohibited Practices
- [x] **PROHIBITED**: Zero importation of ratings from documentation campaigns.
- [x] **PROHIBITED**: Zero inclusion of documentation or synthetic artifacts as ECU execution proof.

---

## 6. Evidence Baseline & Cross-Campaign Isolation Policy

> [!IMPORTANT]
> **Mandatory Origin Filter**: `ecu-execution exclusively`
> **Documentation Isolation Rule**: Documentation campaigns (including Feature 0019) may contribute reusable definitions, schemas, and procedural mechanisms ONLY. Under NO circumstances may documentation artifacts or synthetic fixtures enter as ECU execution evidence or imported process ratings.

---

## 7. Assessor Independence & Governance Approvals

- **Separation of Duties**: Assessors and QA Authorities maintain complete independence from software development and integration tasks. Lead Assessor (odo) and QA Manager (jake) report directly to Executive Leadership.
- **4-Eyes Authorization**: All assessment ratings, gate clearance decisions, and finding closures require independent 4-eyes review and approval.

### Formal Plan Signatures
- **Project Sponsor**: jadzia (Project Lead, Team DeepSpace9)
- **Lead Assessor**: odo (Lead Assessor, Team DeepSpace9)
- **QA Authority**: jake (QA-Manager, Team DeepSpace9)
- **Architect**: kira (Architect, Team DeepSpace9)
- **Date**: 2026-09-19
