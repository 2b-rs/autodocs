# ECU Profile Process-by-Process Evidence Coverage (Feature 0011-06)

## Purpose
This document establishes the architecture for capturing process-by-process evidence coverage for the approved ECU profile in accordance with ASPICE / safety compliance requirements. It ensures evidence mapping remains factual without falsely assigning unsupported capability levels, keeps documentation execution decoupled from evidence facts, and maintains full traceability of findings.

## 1. Process-by-Process Coverage Baseline

For each process required by the ECU profile (e.g., SWE.1, SWE.2, SWE.3, SUP.1, SUP.8, SUP.9, SUP.10), the system must map actual artifact and execution records to the base practices (BPs) and work products (WPs) of the process.

**Constraint:** The mapping logic records the *presence and validity of evidence*. It strictly **must not** synthesize, calculate, or assign an overall Process Attribute (PA) or Capability Level (CL). Capability assessment remains an external/human auditing function; the system only records coverage.

## 2. Required Data Model for Evidence Records

Each mapped evidence unit must capture:
- **Product Identity:** Which specific ECU product variant and baseline the evidence applies to.
- **Process Instance / Origin:** The execution run, pull request, manual review, or automated script that generated the evidence.
- **Evidence Revision & Validity:** The exact SHA-256 hash or version string of the artifact. Validity periods or conditions (e.g., test valid only for branch X) must be tracked.
- **Contrary Evidence:** If subsequent runs or reviews invalidate or contradict the original evidence (e.g., a failed test following a passing test), the contrary evidence must be linked and the coverage state marked as disputed.

## 3. Separation of Documentation and Execution

Documentation output (e.g., Doxygen, generated reports, traceability matrices) is a read-side projection.
The execution of documentation generators **must remain separate** from the actual execution of the process (e.g., compilation, testing, static analysis). A failure in documentation formatting must not invalidate the evidence of a successful test run, and conversely, the generation of a document does not constitute process evidence unless the document itself is the required work product.

## 4. Traceable Findings for Unsupported Outcomes

Any gap in the required ECU profile coverage (an unsupported outcome or missing attribute achievement) cannot simply be ignored.
- The evidence coverage scanner must generate a **Traceable Finding** for every missing, invalid, or contrary piece of evidence relative to the profile's expected base practices.
- Findings must be recorded using the `finding-v1.schema.json` schema and linked to the missing capability requirement.
- These findings feed directly into the issue/problem resolution lifecycle (SUP.9).
