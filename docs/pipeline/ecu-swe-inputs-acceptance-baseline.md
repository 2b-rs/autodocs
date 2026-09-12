# SWE Software Development Inputs Baseline (ECU Profile)

**Status**: baselined
**Scope**: Allocated system requirements and system architecture constraints feeding ECU software development (SWE.1).

## 1. Purpose
This document defines the acceptance gate and baselining mechanism for software-development inputs allocated to the ECU. It handles inputs originating from either internal systems engineering (SYS.2/SYS.3) or external/shared responsibilities, ensuring that the necessary preconditions for SWE.1 are met without inappropriately claiming internal SYS performance when handled externally.

## 2. Internal Systems Engineering (SYS.2 / SYS.3)
When the ECU profile is configured for internal systems engineering:
- **Predecessor Constraints**: The software development inputs MUST be derived from the controlled outputs of the internal `SYS.2` and `SYS.3` baselines.
- **Traceability Link**: The selected-profile register establishes the internal acceptance-gate edges directly to tasks `0029-02` (System Requirements Baseline) and `0030-02` (System Architecture Baseline).
- **Acceptance Criteria**: The internal outputs must be formally approved and under configuration control (SUP.8) before they can be consumed by SWE.1.

## 3. External or Shared Systems Engineering
When system requirements or architectures are provided by an external party or are a shared responsibility:
- **No Internal SYS Performance Claim**: The ECU profile DOES NOT claim internal performance of SYS.2 or SYS.3. Instead, it claims the receipt and validation of the external outputs.
- **Validation of External Inputs**: The incoming artifacts MUST be validated at the acceptance gate for:
  - **Responsible Party**: Explicit identification of the external owner or shared interface responsible for the baseline.
  - **Allocated Requirements**: Complete and unambiguous stakeholder/system requirements allocated to software.
  - **Architecture & Interface Constraints**: Hardware/software boundaries, memory/timing constraints, and network matrix allocations.
  - **Assumptions**: Documented dependencies, assumed preconditions, and operational environment conditions.
  - **Acceptance Criteria**: Defined metrics or thresholds the software must satisfy.
  - **Configuration Identity**: Explicit version, hash, or release identifier from the external source.
- **Bidirectional Interface Evidence**: The boundary must maintain bidirectional traceability between the external system item and the internal ECU software requirement.
- **Change, Problem, and Risk Feedback**: An agreed interface must exist for reporting SUP.9 problems, SUP.10 change requests, and MAN.5 risks back to the external party.

## 4. Selected-Profile Register Materialization
The active project's selected-profile register MUST materialize the actual acceptance-gate edges based on the operating mode:
- **Internal Edge**: `SYS.3 Output (0030-02) -> SWE.1 Input`
- **External Edge**: `External System Baseline Receipt -> Validation Gate -> SWE.1 Input`

This ensures that the ECU SWE pipeline is unblocked only when a validated, configuration-controlled set of system inputs is actively baselined.
