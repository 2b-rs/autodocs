# Evidence Dossier: Task 0018-09 (ECU Pilot Management Decision & Published Process Capability Profile)

## 1. Task Summary
- **Task ID**: `0018-09`
- **Assignee**: `benjamin` (Dispatcher, Team DeepSpace9)
- **Approving Authority / Sponsor**: `jadzia` (Project Lead & Assessment Sponsor, Team DeepSpace9)
- **Lead Assessor**: `odo` (Lead Assessor, Team DeepSpace9)
- **QA Manager**: `jake` (QA-Manager, Team DeepSpace9)
- **Goal**: Record the management decision and publish the final assessment-result profile without a CL2 claim, including organizational/supplied-product scope, process instances, PAM version, assessment method/date, ECU evidence baseline, per-process ratings, separate assessment-disposition and execution-responsibility statements, limitations, validity period, and any next-cycle plan. A shared in-scope process is rated on the approved process-instance boundary; a fully external or out-of-scope process receives no internal rating.
- **Published Baseline**: `virtualized-automotive-ecu@software-without-kernel:v0.7.0-pilot1-rev1` (Commit: `9d3e81a`)
- **Reference Standard**: Automotive SPICE PAM 3.1 / PAM 4.0 Reference Model & ISO/IEC 33020 Process Assessment Standard

---

## 2. Key Accomplishments & Deliverables

1. **Pilot Published Profile Engine**:
   - Authored [`_src/tools/ecu_pilot_published_profile.py`](file:///Users/tobias.anton/devel/autodocs/.worktrees/0018-09/_src/tools/ecu_pilot_published_profile.py) assembling management decision `DEC-0018-PUBLISH-20260919-01`, per-process Level-2 ratings, separate governance statements, limitations register, and next-cycle roadmap.
2. **Canonical Machine-Readable Datasets**:
   - Generated [`docs/dossiers/assessment/ECU-PILOT-PUBLISHED-ASSESSMENT-PROFILE-v0.7.0.json`](file:///Users/tobias.anton/devel/autodocs/.worktrees/0018-09/docs/dossiers/assessment/ECU-PILOT-PUBLISHED-ASSESSMENT-PROFILE-v0.7.0.json) containing complete published profile metadata with deterministic SHA-256 tree digest.
3. **Pilot Published Profile Companion Document**:
   - Authored [`docs/pipeline/ecu-pilot-published-assessment-profile.md`](file:///Users/tobias.anton/devel/autodocs/.worktrees/0018-09/docs/pipeline/ecu-pilot-published-assessment-profile.md).
4. **Comprehensive Unit Test Suite**:
   - Authored [`_src/tests/test_ecu_pilot_published_profile.py`](file:///Users/tobias.anton/devel/autodocs/.worktrees/0018-09/_src/tests/test_ecu_pilot_published_profile.py).
   - Full ECU test suite passing: 107/107 tests across `_src/tests/test_ecu*.py` in 0.84s.

---

## 3. Executive Management Decision & Governance Policy

- **Decision ID**: `DEC-0018-PUBLISH-20260919-01` (`APPROVED_FOR_PUBLICATION`)
- **Approving Authority**: `jadzia` (Project Lead & Assessment Sponsor)
- **Claim Policy Enforcement**: `NO_BLANKET_ORGANIZATIONAL_CL2_CLAIM`
- **Validity Period**: 2026-09-19 to 2027-09-19 (12 Months)
- **Separate Governance Statements**:
  - *Assessment Disposition Statement*: `odo` (Lead Assessor confirms all 17 processes satisfy Level 2: PA 1.1 = F, PA 2.1 = F, PA 2.2 = F).
  - *Execution Responsibility Statement*: `jadzia` (Project Lead assumes operational accountability for roadmap execution and residual tracking).

---

## 4. Published Process Capability Profile (Level 2: PA 1.1, PA 2.1, PA 2.2)

| Process ID | Process Name | Instance ID | PA 1.1 | PA 2.1 | PA 2.2 | Level | Disposition |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`SWE.1`** | Software Requirements Analysis | `PI-SWE1-202610-PILOT1` | **F** | **F** | **F** | **Level 2** | `ACHIEVED_LEVEL_2` |
| **`SWE.2`** | Software Architectural Design | `PI-SWE2-202610-PILOT1` | **F** | **F** | **F** | **Level 2** | `ACHIEVED_LEVEL_2` |
| **`SWE.3`** | Software Detailed Design & Unit Construction | `PI-SWE3-202610-PILOT1` | **F** | **F** | **F** | **Level 2** | `ACHIEVED_LEVEL_2` |
| **`SWE.4`** | Software Unit Verification | `PI-SWE4-202610-PILOT1` | **F** | **F** | **F** | **Level 2** | `ACHIEVED_LEVEL_2` |
| **`SWE.5`** | Software Integration & Verification | `PI-SWE5-202610-PILOT1` | **F** | **F** | **F** | **Level 2** | `ACHIEVED_LEVEL_2` |
| **`SWE.6`** | Software Qualification Testing | `PI-SWE6-202610-PILOT1` | **F** | **F** | **F** | **Level 2** | `ACHIEVED_LEVEL_2` |
| **`SYS.2`** | System Requirements Analysis | `PI-SYS2-202610-PILOT1` | **F** | **F** | **F** | **Level 2** | `ACHIEVED_LEVEL_2` |
| **`SYS.3`** | System Architectural Design | `PI-SYS3-202610-PILOT1` | **F** | **F** | **F** | **Level 2** | `ACHIEVED_LEVEL_2` |
| **`VAL.1`** | System & ECU Operational Validation | `PI-VAL1-202610-PILOT1` | **F** | **F** | **F** | **Level 2** | `ACHIEVED_LEVEL_2` |
| **`SPL.2`** | Product Release | `PI-SPL2-202610-PILOT1` | **F** | **F** | **F** | **Level 2** | `ACHIEVED_LEVEL_2` |
| **`SUP.1`** | Quality Assurance | `PI-SUP1-202610-PILOT1` | **F** | **F** | **F** | **Level 2** | `ACHIEVED_LEVEL_2` |
| **`SUP.8`** | Configuration Management | `PI-SUP8-202610-PILOT1` | **F** | **F** | **F** | **Level 2** | `ACHIEVED_LEVEL_2` |
| **`SUP.9`** | Problem Resolution Management | `PI-SUP9-202610-PILOT1` | **F** | **F** | **F** | **Level 2** | `ACHIEVED_LEVEL_2` |
| **`SUP.10`** | Change Request Management | `PI-SUP10-202610-PILOT1` | **F** | **F** | **F** | **Level 2** | `ACHIEVED_LEVEL_2` |
| **`MAN.3`** | Project Management | `PI-MAN3-202610-PILOT1` | **F** | **F** | **F** | **Level 2** | `ACHIEVED_LEVEL_2` |
| **`MAN.5`** | Risk Management | `PI-MAN5-202610-PILOT1` | **F** | **F** | **F** | **Level 2** | `ACHIEVED_LEVEL_2` |
| **`MAN.6`** | Measurement | `PI-MAN6-202610-PILOT1` | **F** | **F** | **F** | **Level 2** | `ACHIEVED_LEVEL_2` |

---

## 5. Next-Cycle Roadmap

- **`PLAN-PILOT-01`**: Commission Accredited Third-Party Class 1 Certification Assessment (Milestone v0.8.0 Freeze, 2026-11-30, `jadzia`).
- **`PLAN-PILOT-02`**: Physical HIL Dyno Bench Testing & Real Peripheral Integration (Release v0.8.0-RC1, 2026-11-15, `jake`).
- **`PLAN-PILOT-03`**: Predictive ARIMA Statistical Measurement Analytics Deployment (Milestone v0.8.0, 2026-11-01, `jake`).
