# SYS.4 System Architecture Integration and Input Baseline (Feature 0031-01)

## Purpose
This document specifies the controlled baseline integration points and input authority for `SYS.4` (System Integration and Integration Testing). It establishes how the system architecture and element inputs are explicitly verified against the approved profiles before internal SYS.4 process performance begins.

## 1. System Architecture Inputs
The input baseline must explicitly define the source and identity of the system architecture model:
- **Internal Sourcing:** Where the architecture is developed internally (e.g., via `0030-02` SYS.3 outputs), the canonical release digest of the internal architecture model must be specified.
- **External/Shared Sourcing:** If the architecture is provided by a customer or supplier, the baseline must identify the validated external owner, the immutable interface baseline, configuration version, open findings, and established feedback path.

## 2. System Element Inputs
The input baseline must identify the set of integrated system elements:
- Software releases, firmware modules, hardware configuration baselines, calibration profiles, and mechanical/electrical interface specifications.
- **Strict Profile Conformance:** The selected-profile register must physically materialize these element sources. A hard-coded, software-only prerequisite graph cannot stand in for a composite, multi-disciplinary system element integration set unless the exact scope is restricted to software-only by the authorized profile.

## 3. Acceptance and Baseline Rules
1. **Verification of Authority:** Before integration begins, each system element must be explicitly accepted through its defined process gate (e.g., SWE.6 release for software, external delivery acceptance for supplier parts).
2. **Configuration Pinning:** The SYS.4 baseline must record the exact cryptographic hashes or immutable version identifiers for every integrated element.
3. **Rejection of Unknowns:** Any system element lacking an explicit acceptance signature or a verifiable trace to the approved project profile must be rejected from the integration build.
