# SYS.2 Stakeholder Requirement Input Baseline

## 1. Purpose
This document establishes the accepted stakeholder-requirement baseline for internal ECU System Requirements Analysis (ASPICE SYS.2). It defines the source, validity, configuration identity, and acceptance criteria for stakeholder inputs, explicitly distinguishing whether the Requirements Elicitation (SYS.1) was performed internally (via Feature 0028 output) or provided externally by a shared responsible party (e.g., OEM).

## 2. Source and Responsible Party
- **Internal SYS.1 (Default)**: If the ECU project claims internal SYS.1 performance, the stakeholder-requirement input is the accepted output of Feature 0028.
- **External/Shared SYS.1**: If the OEM or a third party provides the requirements, the ECU project explicitly disclaims internal SYS.1 performance. The responsible party must be identified and documented per release cycle.

## 3. Configuration Identity and Baseline
Stakeholder requirements must be uniquely identified and version-controlled before SYS.2 analysis can begin.
- **Input Artifact**: The specific requirement document, database export, or model.
- **Identity**: The document version, commit SHA, or baseline tag.
- **Status**: The input must be marked as `Released` or `Approved` by the originating party. Drafts are not acceptable for formal SYS.2 baselining.

## 4. Assumptions and Constraints
- External requirements often contain implicit assumptions regarding operating environment or vehicle-level integration. These must be explicitly extracted and tracked during SYS.2.
- Any conflicting or ambiguous stakeholder requirements identified during SYS.2 must be routed through the defined feedback interface.

## 5. Acceptance and Feedback Interface
Before internal SYS.2 begins, the Project Lead and Requirements Engineer must formally accept the stakeholder input.
- **Acceptance Gate**: The input is verifiable, versioned, and sourced from the authorized party.
- **Feedback Interface**: Deficiencies, ambiguities, or unfeasible requests found during SYS.2 are logged as SUP.9 problems or SUP.10 change requests and returned to the SYS.1 responsible party via the MAN.3 communication matrix.

## 6. Record of Accepted Baseline
The current operative stakeholder requirement input baseline for the ECU project is recorded here or linked to the active project manifest. No internal SYS.2 work may derive from un-baselined or un-accepted stakeholder inputs.
