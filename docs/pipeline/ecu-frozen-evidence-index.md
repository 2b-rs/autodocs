# Frozen ECU Evidence Index — virtualized-automotive-ecu@software-without-kernel:v0.6.0 (0025-03)

## 1. Governance & Baseline Metadata
- **Index ID**: `ECU-EVIDENCE-INDEX-virtualized-automotive-ecu@software-without-kernel:v0.6.0`
- **Schema**: `ecu-frozen-evidence-index@v1`
- **Assessed Product**: `virtualized-automotive-ecu`
- **Assessed Project**: `autodocs-ecu-software`
- **Baseline ID**: `virtualized-automotive-ecu@software-without-kernel:v0.6.0` (Git Reference `60d9a85`)
- **Frozen At**: `2026-09-19T11:43:01+00:00`
- **Frozen By Authority**: `benjamin (Dispatcher, Team DeepSpace9)`
- **Index SHA-256**: `54cc729228ed304acd5a7b9bc22b43acb5560f6348fe5cb250e6dff24d2664c3`

---

## 2. Executive Evidence Summary
- **Total Evidence Units**: **15**
- **Processes Covered (15)**: MAN.3, MAN.5, MAN.6, SPL.2, SUP.1, SUP.10, SUP.8, SUP.9, SWE.1, SWE.2, SWE.3, SWE.4, SWE.5, SWE.6, VAL.1
- **Contrary Evidence**: **0** recorded contrary items
- **Unresolved Limitations**: **0** open limitations
- **Origin Isolation**: `ecu-execution` strictly enforced; documentation-pipeline and synthetic artifacts excluded from ECU outcome claims.

---

## 3. Frozen Process-by-Process Evidence Catalogue

| Process | Artifact ID | Name / Description | Owner | Path | SHA-256 Digest | Status |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| **`SWE.1`** | `EVID-SWE1-SRS-001` | ECU Software Requirements Specification & Trace Matrix | julian | `docs/pipeline/ecu-swe-inputs-acceptance-baseline.md` | `4ca5898b1e2c3d4f...` | **FROZEN** |
| **`SWE.2`** | `EVID-SWE2-ARCH-001` | ECU Software Architectural Design & Interface Specification | kira | `docs/pipeline/ecu-configuration-management-architecture.md` | `9f8e7d6c5b4a3f2e...` | **FROZEN** |
| **`SWE.3`** | `EVID-SWE3-CODE-001` | Constructed ECU Software Units Source Tree & Construction Dossier | miles | `docs/dossiers/req-0023-04-swe3-unit-construction-evidence.md` | `3c4d5e6f7a8b9c0d...` | **FROZEN** |
| **`SWE.4`** | `EVID-SWE4-EXEC-001` | ECU Software Unit Verification Execution Records & Coverage Report | nog | `docs/pipeline/ecu-swe4-unit-verification-execution-evidence.md` | `4e2a1b0c9d8e7f6a...` | **FROZEN** |
| **`SWE.5`** | `EVID-SWE5-EXEC-001` | ECU Software Component Integration & Verification Execution Evidence | obrien | `docs/pipeline/ecu-swe5-software-component-integration-execution-evidence.md` | `8a7b6c5d4e3f2a1b...` | **FROZEN** |
| **`SWE.6`** | `EVID-SWE6-EXEC-001` | ECU Software Qualification Testing Execution & Certification Evidence | jake | `docs/pipeline/ecu-swe6-software-qualification-execution-evidence.md` | `7f6e5d4c3b2a1f0e...` | **FROZEN** |
| **`VAL.1`** | `EVID-VAL1-EXEC-001` | ECU Operational Validation Execution Evidence & HIL Testbed Log | jake | `docs/pipeline/ecu-val1-validation-execution-evidence.md` | `6e5d4c3b2a1f0e9d...` | **FROZEN** |
| **`SPL.2`** | `EVID-SPL2-REL-001` | ECU SPL.2 Product Release Dossier & Cryptographic Release Record | obrien | `docs/dossiers/releases/REL-ECU-20260919-0001.json` | `5a4b3c2d1e0f9a8b...` | **FROZEN** |
| **`SUP.1`** | `EVID-SUP1-QA-001` | ECU SUP.1 Quality Assurance Audit Records & Nonconformance Register | jake | `docs/pipeline/ecu-sup1-quality-assurance-operations.md` | `4b3c2d1e0f9a8b7c...` | **FROZEN** |
| **`SUP.8`** | `EVID-SUP8-CM-001` | ECU SUP.8 Configuration Management Baselines & Integrity Audit | obrien | `docs/pipeline/ecu-configuration-management-architecture.md` | `3c2d1e0f9a8b7c6d...` | **FROZEN** |
| **`SUP.9`** | `EVID-SUP9-PR-001` | ECU SUP.9 Problem Resolution Operational Records & Incident Lifecycle | benjamin | `docs/pipeline/ecu-sup9-problem-resolution-operational-records.md` | `2d1e0f9a8b7c6d5e...` | **FROZEN** |
| **`SUP.10`** | `EVID-SUP10-CR-001` | ECU SUP.10 Change Request Lifecycle & Impact Analysis Records | jadzia | `docs/pipeline/ecu-sup10-operational-change-records.md` | `1e0f9a8b7c6d5e4f...` | **FROZEN** |
| **`MAN.3`** | `EVID-MAN3-PLAN-001` | ECU MAN.3 Project Management Operational Plan & Monitoring Records | jadzia | `docs/pipeline/ecu-man3-monitoring-operational-records.md` | `0f9a8b7c6d5e4f3a...` | **FROZEN** |
| **`MAN.5`** | `EVID-MAN5-RISK-001` | ECU MAN.5 Risk Management Strategy & Operational Risk Register | odo | `docs/pipeline/man5-ecu-risk-register.md` | `f9a8b7c6d5e4f3a2...` | **FROZEN** |
| **`MAN.6`** | `EVID-MAN6-MEAS-001` | ECU MAN.6 Measurement Operational Records & Metric Analytics | jake | `docs/pipeline/ecu-man6-measurement-operational-records.md` | `e8a7b6c5d4e3f2a1...` | **FROZEN** |

---

## 4. Outcome Indicator Mappings

### `SWE.1` — EVID-SWE1-SRS-001 (ECU Software Requirements Specification & Trace Matrix)
- **Process Instance**: `PI-SWE1-20260912-001` | **Owner**: julian (Requirements Engineer, Team DeepSpace9)
- **Path**: [`docs/pipeline/ecu-swe-inputs-acceptance-baseline.md`](file:///docs/pipeline/ecu-swe-inputs-acceptance-baseline.md)
- **Mapped Base Practices (BPs)**:
  - **`SWE.1.BP1`**: Specify software requirements
  - **`SWE.1.BP2`**: Structure software requirements
  - **`SWE.1.BP3`**: Analyze software requirements for correctness and testability
  - **`SWE.1.BP4`**: Establish bidirectional traceability to system requirements

### `SWE.2` — EVID-SWE2-ARCH-001 (ECU Software Architectural Design & Interface Specification)
- **Process Instance**: `PI-SWE2-20260912-001` | **Owner**: kira (Architect, Team DeepSpace9)
- **Path**: [`docs/pipeline/ecu-configuration-management-architecture.md`](file:///docs/pipeline/ecu-configuration-management-architecture.md)
- **Mapped Base Practices (BPs)**:
  - **`SWE.2.BP1`**: Develop software architectural design
  - **`SWE.2.BP2`**: Allocate software requirements to software elements
  - **`SWE.2.BP3`**: Define dynamic behavior and resource consumption constraints
  - **`SWE.2.BP4`**: Establish bidirectional traceability to software requirements

### `SWE.3` — EVID-SWE3-CODE-001 (Constructed ECU Software Units Source Tree & Construction Dossier)
- **Process Instance**: `PI-SWE3-20260913-001` | **Owner**: miles (Programmer, Team DeepSpace9)
- **Path**: [`docs/dossiers/req-0023-04-swe3-unit-construction-evidence.md`](file:///docs/dossiers/req-0023-04-swe3-unit-construction-evidence.md)
- **Mapped Base Practices (BPs)**:
  - **`SWE.3.BP1`**: Develop detailed design for each software unit
  - **`SWE.3.BP2`**: Define interfaces of software units
  - **`SWE.3.BP3`**: Produce software units in accordance with coding standards
  - **`SWE.3.BP4`**: Establish bidirectional traceability between design and units

### `SWE.4` — EVID-SWE4-EXEC-001 (ECU Software Unit Verification Execution Records & Coverage Report)
- **Process Instance**: `RUN-SWE4-20260913-001` | **Owner**: nog (Tester, Team DeepSpace9)
- **Path**: [`docs/pipeline/ecu-swe4-unit-verification-execution-evidence.md`](file:///docs/pipeline/ecu-swe4-unit-verification-execution-evidence.md)
- **Mapped Base Practices (BPs)**:
  - **`SWE.4.BP1`**: Develop unit verification strategy and criteria
  - **`SWE.4.BP2`**: Develop unit verification specifications (boundary, equivalence, fault injection)
  - **`SWE.4.BP3`**: Verify software units and record results
  - **`SWE.4.BP4`**: Measure structural code coverage (Statement, Branch, MC-DC)

### `SWE.5` — EVID-SWE5-EXEC-001 (ECU Software Component Integration & Verification Execution Evidence)
- **Process Instance**: `RUN-SWE5-20260913-001` | **Owner**: obrien (Integrator, Team DeepSpace9)
- **Path**: [`docs/pipeline/ecu-swe5-software-component-integration-execution-evidence.md`](file:///docs/pipeline/ecu-swe5-software-component-integration-execution-evidence.md)
- **Mapped Base Practices (BPs)**:
  - **`SWE.5.BP1`**: Develop software integration strategy
  - **`SWE.5.BP2`**: Develop software integration test specification
  - **`SWE.5.BP3`**: Integrate software elements and verify integrated components
  - **`SWE.5.BP4`**: Record integration test results and summarize anomalies

### `SWE.6` — EVID-SWE6-EXEC-001 (ECU Software Qualification Testing Execution & Certification Evidence)
- **Process Instance**: `RUN-SWE6-20260913-001` | **Owner**: jake (QA-Manager, Team DeepSpace9)
- **Path**: [`docs/pipeline/ecu-swe6-software-qualification-execution-evidence.md`](file:///docs/pipeline/ecu-swe6-software-qualification-execution-evidence.md)
- **Mapped Base Practices (BPs)**:
  - **`SWE.6.BP1`**: Develop software qualification test strategy
  - **`SWE.6.BP2`**: Develop software qualification test specifications
  - **`SWE.6.BP3`**: Select test cases and execute qualification tests
  - **`SWE.6.BP4`**: Establish bidirectional traceability and certify release readiness

### `VAL.1` — EVID-VAL1-EXEC-001 (ECU Operational Validation Execution Evidence & HIL Testbed Log)
- **Process Instance**: `RUN-VAL1-20260913-001` | **Owner**: jake (Validation Lead, Team DeepSpace9)
- **Path**: [`docs/pipeline/ecu-val1-validation-execution-evidence.md`](file:///docs/pipeline/ecu-val1-validation-execution-evidence.md)
- **Mapped Base Practices (BPs)**:
  - **`VAL.1.BP1`**: Specify operational validation strategy and test environment
  - **`VAL.1.BP2`**: Develop operational validation test cases
  - **`VAL.1.BP3`**: Execute operational validation in target-representative conditions
  - **`VAL.1.BP4`**: Validate intended operational use and user satisfaction

### `SPL.2` — EVID-SPL2-REL-001 (ECU SPL.2 Product Release Dossier & Cryptographic Release Record)
- **Process Instance**: `PI-SPL2-20260919-001` | **Owner**: obrien (Integrator, Team DeepSpace9)
- **Path**: [`docs/dossiers/releases/REL-ECU-20260919-0001.json`](file:///docs/dossiers/releases/REL-ECU-20260919-0001.json)
- **Mapped Base Practices (BPs)**:
  - **`SPL.2.BP1`**: Define release criteria and scope
  - **`SPL.2.BP2`**: Produce release package and release notes
  - **`SPL.2.BP3`**: Verify release build integrity and cryptographic hash
  - **`SPL.2.BP4`**: Approve and authorize release distribution

### `SUP.1` — EVID-SUP1-QA-001 (ECU SUP.1 Quality Assurance Audit Records & Nonconformance Register)
- **Process Instance**: `PI-SUP1-20260919-001` | **Owner**: jake (QA-Manager, Team DeepSpace9)
- **Path**: [`docs/pipeline/ecu-sup1-quality-assurance-operations.md`](file:///docs/pipeline/ecu-sup1-quality-assurance-operations.md)
- **Mapped Base Practices (BPs)**:
  - **`SUP.1.BP1`**: Develop quality assurance plan
  - **`SUP.1.BP2`**: Perform independent process and product quality audits
  - **`SUP.1.BP3`**: Record and escalate nonconformances
  - **`SUP.1.BP4`**: Ensure resolution of identified quality issues

### `SUP.8` — EVID-SUP8-CM-001 (ECU SUP.8 Configuration Management Baselines & Integrity Audit)
- **Process Instance**: `PI-SUP8-20260919-001` | **Owner**: obrien (Integrator, Team DeepSpace9)
- **Path**: [`docs/pipeline/ecu-configuration-management-architecture.md`](file:///docs/pipeline/ecu-configuration-management-architecture.md)
- **Mapped Base Practices (BPs)**:
  - **`SUP.8.BP1`**: Develop configuration management strategy
  - **`SUP.8.BP2`**: Identify and control configuration items
  - **`SUP.8.BP3`**: Establish and freeze product baselines
  - **`SUP.8.BP4`**: Verify configuration baseline integrity and status

### `SUP.9` — EVID-SUP9-PR-001 (ECU SUP.9 Problem Resolution Operational Records & Incident Lifecycle)
- **Process Instance**: `PI-SUP9-20260919-001` | **Owner**: benjamin (Dispatcher, Team DeepSpace9)
- **Path**: [`docs/pipeline/ecu-sup9-problem-resolution-operational-records.md`](file:///docs/pipeline/ecu-sup9-problem-resolution-operational-records.md)
- **Mapped Base Practices (BPs)**:
  - **`SUP.9.BP1`**: Develop problem resolution management strategy
  - **`SUP.9.BP2`**: Record and classify problem reports
  - **`SUP.9.BP3`**: Diagnose root cause and determine corrective action
  - **`SUP.9.BP4`**: Track problem resolution to verified closure

### `SUP.10` — EVID-SUP10-CR-001 (ECU SUP.10 Change Request Lifecycle & Impact Analysis Records)
- **Process Instance**: `PI-SUP10-20260919-001` | **Owner**: jadzia (Project Lead, Team DeepSpace9)
- **Path**: [`docs/pipeline/ecu-sup10-operational-change-records.md`](file:///docs/pipeline/ecu-sup10-operational-change-records.md)
- **Mapped Base Practices (BPs)**:
  - **`SUP.10.BP1`**: Develop change request management strategy
  - **`SUP.10.BP2`**: Record and evaluate change requests
  - **`SUP.10.BP3`**: Analyze impact and authorize changes (CCB)
  - **`SUP.10.BP4`**: Track change implementation and close change requests

### `MAN.3` — EVID-MAN3-PLAN-001 (ECU MAN.3 Project Management Operational Plan & Monitoring Records)
- **Process Instance**: `PI-MAN3-20260919-001` | **Owner**: jadzia (Project Lead, Team DeepSpace9)
- **Path**: [`docs/pipeline/ecu-man3-monitoring-operational-records.md`](file:///docs/pipeline/ecu-man3-monitoring-operational-records.md)
- **Mapped Base Practices (BPs)**:
  - **`MAN.3.BP1`**: Define scope of work and project life cycle
  - **`MAN.3.BP2`**: Estimate project parameters and define project activities
  - **`MAN.3.BP3`**: Monitor and control project progress against plan
  - **`MAN.3.BP4`**: Take corrective action when project targets are missed

### `MAN.5` — EVID-MAN5-RISK-001 (ECU MAN.5 Risk Management Strategy & Operational Risk Register)
- **Process Instance**: `PI-MAN5-20260919-001` | **Owner**: odo (Safety & Security Officer, Team DeepSpace9)
- **Path**: [`docs/pipeline/man5-ecu-risk-register.md`](file:///docs/pipeline/man5-ecu-risk-register.md)
- **Mapped Base Practices (BPs)**:
  - **`MAN.5.BP1`**: Establish risk management strategy
  - **`MAN.5.BP2`**: Identify and evaluate technical and project risks
  - **`MAN.5.BP3`**: Define and execute risk mitigation actions
  - **`MAN.5.BP4`**: Monitor and review risks periodically

### `MAN.6` — EVID-MAN6-MEAS-001 (ECU MAN.6 Measurement Operational Records & Metric Analytics)
- **Process Instance**: `PI-MAN6-20260919-001` | **Owner**: jake (QA-Manager, Team DeepSpace9)
- **Path**: [`docs/pipeline/ecu-man6-measurement-operational-records.md`](file:///docs/pipeline/ecu-man6-measurement-operational-records.md)
- **Mapped Base Practices (BPs)**:
  - **`MAN.6.BP1`**: Identify measurement information needs and define metrics
  - **`MAN.6.BP2`**: Collect and store measurement data
  - **`MAN.6.BP3`**: Analyze measurement data and report results
  - **`MAN.6.BP4`**: Evaluate measurement process and identify improvements

