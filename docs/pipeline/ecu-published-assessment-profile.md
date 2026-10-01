# Automotive ECU Published Process Capability Assessment Profile (0025-09)

## 1. Executive Management Decision
- **Decision ID**: `DEC-0025-PUBLISH-20260919-01`
- **Title**: Executive Authorization for Publication of Bounded ECU Level-1 Process Capability Profile
- **Approving Authority**: jadzia (Project Lead & Assessment Sponsor, Team DeepSpace9)
- **Date**: `2026-09-19`
- **Decision Disposition**: **`APPROVED_FOR_PUBLICATION`**

> Management formally authorizes the publication of the supported Automotive SPICE Level 1 Process Performance Profile for the Virtualized Automotive ECU Software increment (Baseline v0.6.0-rev1). The published profile accurately reflects the evidence-backed PA 1.1 ratings without asserting blanket organizational maturity or CL2 entry claims.

---

## 2. Assessment Scope & Methodology Metadata
- **Profile ID**: `ECU-PUBLISHED-PROFILE-virtualized-automotive-ecu@software-without-kernel:v0.6.0-rev1`
- **Schema**: `ecu-published-assessment-profile@v1`
- **Organization**: Automotive Systems Division (Team DeepSpace9)
- **Product ID**: `virtualized-automotive-ecu` (Embedded safety-critical control and diagnostic application firmware for virtualized ECU platform.)
- **Release Instance**: `virtualized-automotive-ecu@software-without-kernel:v0.6.0-rev1` (Git Reference `7a1b49e`)
- **Reference Model**: Automotive SPICE PAM 3.1 / PAM 4.0 Reference Model (ISO/IEC 33020)
- **Assessment Standard**: ISO/IEC 33020 Process Assessment Standard
- **Assessment Method**: Class 1 Rigorous Internal Assessment with Independent Readiness Review
- **Assessment Window**: 2026-09-12 to 2026-09-19
- **Validity Period**: **2026-09-19 to 2027-09-19 (12 Months)**
- **Evidence Baseline**: `ECU-EVIDENCE-INDEX-virtualized-automotive-ecu@software-without-kernel:v0.6.0-rev1`
- **Published Profile SHA-256 Digest**: `80b60889733252e09c568fd1e07791c4161635b90d21a57619956042ea4e9569`

---

## 3. Boundary & Claim Governance Policy

> [!IMPORTANT]
> **Policy Enforcement (`NO_BLANKET_LEVEL1_OR_CL2_ENTRY_CLAIM`)**: The published ratings represent specific process performance (PA 1.1) achieved for the declared 15 process instances within the defined virtualized ECU software boundary. This publication does not constitute an organizational maturity rating, nor does it assert entry into Automotive SPICE Level 2 (Managed Process).

### Out-of-Scope & External Process Boundaries
| Process ID | Disposition | Governance Boundary Rationale |
| :---: | :---: | :--- |
| **`HWE.1-4`** | **`OUT_OF_SCOPE_UNRATED`** | Hardware provided as virtualized target platform. |
| **`ACQ.4`** | **`EXTERNAL_INTERFACE_ONLY`** | Kernel binary interface consumed as external contract. |

---

## 4. Published Process Performance Profile (PA 1.1)

| Process ID | Process Name | Process Instance | PA 1.1 Rating | Rating Scale | Evidence Units | Disposition |
| :---: | :--- | :--- | :---: | :--- | :---: | :---: |
| **`SWE.1`** | Software Requirements Analysis | `PI-SWE1-20260912-001` | **`F`** | ISO/IEC 33020 N-P-L-F (F = Fully Achieved / >= 85%) | 1 | **`FULLY_ACHIEVED`** |
| **`SWE.2`** | Software Architectural Design | `PI-SWE2-20260912-001` | **`F`** | ISO/IEC 33020 N-P-L-F (F = Fully Achieved / >= 85%) | 1 | **`FULLY_ACHIEVED`** |
| **`SWE.3`** | Software Detailed Design & Unit Construction | `PI-SWE3-20260913-001` | **`F`** | ISO/IEC 33020 N-P-L-F (F = Fully Achieved / >= 85%) | 1 | **`FULLY_ACHIEVED`** |
| **`SWE.4`** | Software Unit Verification | `RUN-SWE4-20260913-001` | **`F`** | ISO/IEC 33020 N-P-L-F (F = Fully Achieved / >= 85%) | 1 | **`FULLY_ACHIEVED`** |
| **`SWE.5`** | Software Integration & Verification | `RUN-SWE5-20260913-001` | **`F`** | ISO/IEC 33020 N-P-L-F (F = Fully Achieved / >= 85%) | 1 | **`FULLY_ACHIEVED`** |
| **`SWE.6`** | Software Qualification Testing | `RUN-SWE6-20260913-001` | **`F`** | ISO/IEC 33020 N-P-L-F (F = Fully Achieved / >= 85%) | 1 | **`FULLY_ACHIEVED`** |
| **`VAL.1`** | System & ECU Operational Validation | `RUN-VAL1-20260913-001` | **`F`** | ISO/IEC 33020 N-P-L-F (F = Fully Achieved / >= 85%) | 1 | **`FULLY_ACHIEVED`** |
| **`SPL.2`** | Product Release | `PI-SPL2-20260919-001` | **`F`** | ISO/IEC 33020 N-P-L-F (F = Fully Achieved / >= 85%) | 1 | **`FULLY_ACHIEVED`** |
| **`SUP.1`** | Quality Assurance | `PI-SUP1-20260919-001` | **`F`** | ISO/IEC 33020 N-P-L-F (F = Fully Achieved / >= 85%) | 1 | **`FULLY_ACHIEVED`** |
| **`SUP.8`** | Configuration Management | `PI-SUP8-20260919-001` | **`F`** | ISO/IEC 33020 N-P-L-F (F = Fully Achieved / >= 85%) | 1 | **`FULLY_ACHIEVED`** |
| **`SUP.9`** | Problem Resolution Management | `PI-SUP9-20260919-001` | **`F`** | ISO/IEC 33020 N-P-L-F (F = Fully Achieved / >= 85%) | 1 | **`FULLY_ACHIEVED`** |
| **`SUP.10`** | Change Request Management | `PI-SUP10-20260919-001` | **`F`** | ISO/IEC 33020 N-P-L-F (F = Fully Achieved / >= 85%) | 1 | **`FULLY_ACHIEVED`** |
| **`MAN.3`** | Project Management | `PI-MAN3-20260919-001` | **`F`** | ISO/IEC 33020 N-P-L-F (F = Fully Achieved / >= 85%) | 1 | **`FULLY_ACHIEVED`** |
| **`MAN.5`** | Risk Management | `PI-MAN5-20260919-001` | **`F`** | ISO/IEC 33020 N-P-L-F (F = Fully Achieved / >= 85%) | 1 | **`FULLY_ACHIEVED`** |
| **`MAN.6`** | Measurement | `PI-MAN6-20260919-001` | **`F`** | ISO/IEC 33020 N-P-L-F (F = Fully Achieved / >= 85%) | 1 | **`FULLY_ACHIEVED`** |

---

## 5. Separate Governance Statements

### 5.1 Assessment Disposition Statement
- **Author**: odo (Lead Assessor)
- **Date**: `2026-09-19`
> The assessment team confirms that the 15 evaluated software engineering, supporting, and project management process instances meet the performance requirements of PA 1.1 (Fully Achieved / F). Zero blocking nonconformances remain.

### 5.2 Execution Responsibility Statement
- **Author**: jadzia (Project Lead & Assessment Sponsor)
- **Date**: `2026-09-19`
> Project management bears full execution responsibility for maintaining process adherence, tracking accepted residual risks, and executing the defined next-cycle improvements.

---

## 6. Accepted Limitations

| Limitation ID | Boundary Scope | Title & Description |
| :---: | :---: | :--- |
| **`LIMIT-0025-01`** | `Hardware Platform` | **Virtualized Target Hardware Execution Environment**: Emulated ARM Cortex-R52 target used for software qualification; physical EMC/dyno validation scheduled for v0.7.0. |
| **`LIMIT-0025-02`** | `Runtime Kernel` | **External OS Kernel Boundary**: POSIX/AUTOSAR kernel binary interface audited via ABI contract tests; internal kernel processes are external. |
| **`LIMIT-0025-03`** | `Accreditation` | **Internal Assessment Scope**: Internal Class 1 assessment; formal third-party accredited audit recommended for OEM customer delivery. |

---

## 7. Next-Cycle Roadmap & Improvement Plan

| Plan ID | Title | Target Milestone | Target Date | Owner | Description |
| :---: | :--- | :---: | :---: | :--- | :--- |
| **`PLAN-0025-01`** | Commission Accredited Third-Party Class 1 Certification Assessment | `Milestone v0.7.0 Freeze` | `2026-11-30` | jadzia (Project Lead) | Engage an accredited external VDA / iNTACS auditing body to perform formal third-party certification assessment for commercial OEM delivery. |
| **`PLAN-0025-02`** | Physical HIL Dyno Bench Testing & High-Frequency Noise Profiles | `Release v0.7.0-RC1` | `2026-11-15` | jake (Validation Lead) | Transition from virtual CAN transceiver emulation to physical hardware-in-the-loop dyno testbed with expanded capacitive noise injection patterns. |
| **`PLAN-0025-03`** | Interactive Real-Time Web Dashboard for Measurement Metric Trends | `Milestone v0.7.0` | `2026-11-01` | jake (QA-Manager) | Deploy interactive web reporting UI visualizing automated coverage, defect turnaround, and complexity metrics for executive stakeholders. |
