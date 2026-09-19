# Automotive ECU Pilot Published Process Capability Assessment Profile (0018-09)

## 1. Executive Management Decision
- **Decision ID**: `DEC-0018-PUBLISH-20260919-01`
- **Title**: Executive Authorization for Publication of Bounded ECU Level-2 Process Capability Profile
- **Approving Authority**: jadzia (Project Lead & Assessment Sponsor, Team DeepSpace9)
- **Date**: `2026-09-19`
- **Decision Disposition**: **`APPROVED_FOR_PUBLICATION`**

> Management formally authorizes the publication of the supported Automotive SPICE Level 2 Process Capability Profile for the Virtualized Automotive ECU Software increment (Baseline v0.7.0-pilot1-rev1). The published profile accurately reflects the evidence-backed PA 1.1, PA 2.1, and PA 2.2 ratings across all 17 evaluated process instances without asserting blanket organizational maturity claims.

---

## 2. Assessment Scope & Methodology Metadata
- **Profile ID**: `ECU-PILOT-PUBLISHED-PROFILE-virtualized-automotive-ecu@software-without-kernel:v0.7.0-pilot1-rev1`
- **Schema**: `ecu-pilot-published-assessment-profile@v1`
- **Organization**: Automotive Systems Division (Team DeepSpace9)
- **Product ID**: `virtualized-automotive-ecu` (Embedded safety-critical control and diagnostic application firmware for virtualized ECU platform.)
- **Release Instance**: `virtualized-automotive-ecu@software-without-kernel:v0.7.0-pilot1-rev1` (Git Reference `9d3e81a`)
- **Reference Model**: Automotive SPICE PAM 3.1 / PAM 4.0 Reference Model (ISO/IEC 33020)
- **Assessment Standard**: ISO/IEC 33020 Process Assessment Standard
- **Assessment Method**: Class 1 Rigorous Internal Assessment with Independent Readiness Review
- **Assessment Window**: 2026-10-05 to 2026-10-20
- **Validity Period**: **2026-09-19 to 2027-09-19 (12 Months)**
- **Evidence Baseline**: `ECU-EVIDENCE-INDEX-virtualized-automotive-ecu@software-without-kernel:v0.7.0-pilot1-rev1`
- **Published Profile SHA-256 Digest**: `b458a49b504e003fe4058a6a689b2c7ceca797d909039f6830dac413cb093cbd`

---

## 3. Boundary & Claim Governance Policy

> [!IMPORTANT]
> **Policy Enforcement (`NO_BLANKET_ORGANIZATIONAL_CL2_CLAIM`)**: The published ratings represent specific process capability (Level 2: PA 1.1 = F, PA 2.1 = F, PA 2.2 = F) achieved for the declared 17 process instances within the defined virtualized ECU software boundary. This publication does not constitute an organizational maturity rating, nor does it claim capability for unrated platform hardware or third-party operating system components.

### Out-of-Scope & External Process Boundaries
| Process ID | Disposition | Governance Boundary Rationale |
| :---: | :---: | :--- |
| **`HWE.1-4`** | **`OUT_OF_SCOPE_UNRATED`** | Hardware provided as virtualized target platform; no internal hardware engineering. |
| **`ACQ.4`** | **`EXTERNAL_INTERFACE_ONLY`** | Kernel binary interface consumed as external contract; supplier relationship managed at enterprise level. |

---

## 4. Published Process Capability Profile (Level 2: PA 1.1, PA 2.1, PA 2.2)

| Process ID | Process Name | Process Instance | PA 1.1 | PA 2.1 | PA 2.2 | Level | Evidence Units | Disposition |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`SWE.1`** | Software Requirements Analysis | `PI-SWE1-202610-PILOT1` | **`F`** | **`F`** | **`F`** | **Level 2** | 2 | **`ACHIEVED_LEVEL_2`** |
| **`SWE.2`** | Software Architectural Design | `PI-SWE2-202610-PILOT1` | **`F`** | **`F`** | **`F`** | **Level 2** | 2 | **`ACHIEVED_LEVEL_2`** |
| **`SWE.3`** | Software Detailed Design & Unit Construction | `PI-SWE3-202610-PILOT1` | **`F`** | **`F`** | **`F`** | **Level 2** | 2 | **`ACHIEVED_LEVEL_2`** |
| **`SWE.4`** | Software Unit Verification | `PI-SWE4-202610-PILOT1` | **`F`** | **`F`** | **`F`** | **Level 2** | 2 | **`ACHIEVED_LEVEL_2`** |
| **`SWE.5`** | Software Integration & Verification | `PI-SWE5-202610-PILOT1` | **`F`** | **`F`** | **`F`** | **Level 2** | 2 | **`ACHIEVED_LEVEL_2`** |
| **`SWE.6`** | Software Qualification Testing | `PI-SWE6-202610-PILOT1` | **`F`** | **`F`** | **`F`** | **Level 2** | 2 | **`ACHIEVED_LEVEL_2`** |
| **`SYS.2`** | System Requirements Analysis | `PI-SYS2-202610-PILOT1` | **`F`** | **`F`** | **`F`** | **Level 2** | 2 | **`ACHIEVED_LEVEL_2`** |
| **`SYS.3`** | System Architectural Design | `PI-SYS3-202610-PILOT1` | **`F`** | **`F`** | **`F`** | **Level 2** | 2 | **`ACHIEVED_LEVEL_2`** |
| **`VAL.1`** | System & ECU Operational Validation | `PI-VAL1-202610-PILOT1` | **`F`** | **`F`** | **`F`** | **Level 2** | 2 | **`ACHIEVED_LEVEL_2`** |
| **`SPL.2`** | Product Release | `PI-SPL2-202610-PILOT1` | **`F`** | **`F`** | **`F`** | **Level 2** | 2 | **`ACHIEVED_LEVEL_2`** |
| **`SUP.1`** | Quality Assurance | `PI-SUP1-202610-PILOT1` | **`F`** | **`F`** | **`F`** | **Level 2** | 2 | **`ACHIEVED_LEVEL_2`** |
| **`SUP.8`** | Configuration Management | `PI-SUP8-202610-PILOT1` | **`F`** | **`F`** | **`F`** | **Level 2** | 2 | **`ACHIEVED_LEVEL_2`** |
| **`SUP.9`** | Problem Resolution Management | `PI-SUP9-202610-PILOT1` | **`F`** | **`F`** | **`F`** | **Level 2** | 2 | **`ACHIEVED_LEVEL_2`** |
| **`SUP.10`** | Change Request Management | `PI-SUP10-202610-PILOT1` | **`F`** | **`F`** | **`F`** | **Level 2** | 2 | **`ACHIEVED_LEVEL_2`** |
| **`MAN.3`** | Project Management | `PI-MAN3-202610-PILOT1` | **`F`** | **`F`** | **`F`** | **Level 2** | 2 | **`ACHIEVED_LEVEL_2`** |
| **`MAN.5`** | Risk Management | `PI-MAN5-202610-PILOT1` | **`F`** | **`F`** | **`F`** | **Level 2** | 2 | **`ACHIEVED_LEVEL_2`** |
| **`MAN.6`** | Measurement | `PI-MAN6-202610-PILOT1` | **`F`** | **`F`** | **`F`** | **Level 2** | 2 | **`ACHIEVED_LEVEL_2`** |

---

## 5. Separate Governance Statements

### 5.1 Assessment Disposition Statement
- **Author**: odo (Lead Assessor, Team DeepSpace9)
- **Date**: `2026-09-19`
> The assessment team confirms that the 17 evaluated software engineering, system, validation, release, supporting, and project management process instances meet the requirements of Capability Level 2 (PA 1.1 = F, PA 2.1 = F, PA 2.2 = F). Zero CL2-blocking nonconformances remain.

### 5.2 Execution Responsibility Statement
- **Author**: jadzia (Project Lead & Assessment Sponsor, Team DeepSpace9)
- **Date**: `2026-09-19`
> Project management bears full execution responsibility for maintaining process adherence, managing accepted residual risks, and executing the defined next-cycle improvement roadmap.

---

## 6. Accepted Limitations

| Limitation ID | Boundary Scope | Title & Description |
| :---: | :---: | :--- |
| **`LIMIT-PILOT-01`** | `Hardware Platform / Silicon Platform` | **Virtualized Target Hardware Execution Environment**: Software verification and qualification were executed on virtualized ARM Cortex-M7 emulator targets (QEMU); physical dyno/EMC validation scheduled for v0.8.0. |
| **`LIMIT-PILOT-02`** | `OS Kernel / Runtime Platform` | **External Operating System Kernel Boundary**: POSIX/AUTOSAR kernel binary runtime interface verified via ABI contract tests; internal kernel processes are external. |
| **`LIMIT-PILOT-03`** | `Assessment Accreditation` | **Internal Assessment Scope & Accredited External Audit Recommendation**: Internal Class 1 assessment qualifies baseline readiness; accredited VDA/iNTACS third-party certification recommended for customer OEM freeze. |

---

## 7. Next-Cycle Roadmap & Improvement Plan

| Plan ID | Title | Target Milestone | Target Date | Owner | Description |
| :---: | :--- | :---: | :---: | :--- | :--- |
| **`PLAN-PILOT-01`** | Commission Accredited Third-Party Class 1 Certification Assessment | `Milestone v0.8.0 Freeze` | `2026-11-30` | jadzia (Project Lead & Assessment Sponsor) | Engage an accredited external VDA / iNTACS auditing body to perform formal third-party certification assessment for commercial OEM delivery. |
| **`PLAN-PILOT-02`** | Physical HIL Dyno Bench Testing & Real Peripheral Integration | `Release v0.8.0-RC1` | `2026-11-15` | jake (Validation Lead) | Transition from virtual QEMU microcontroller emulation to physical hardware-in-the-loop dyno testbed with SPI flash and hardware cryptographic accelerator emulation. |
| **`PLAN-PILOT-03`** | Predictive ARIMA Statistical Measurement Analytics Deployment | `Milestone v0.8.0` | `2026-11-01` | jake (QA-Manager) | Deploy automated predictive defect density and effort forecasting algorithms into executive reporting dashboard for multi-project capability management. |
