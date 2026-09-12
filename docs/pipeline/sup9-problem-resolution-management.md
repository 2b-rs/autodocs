# SUP.9 Problem Resolution Management

## 1. Purpose and Scope
This document defines the lifecycle for problem resolution management (ASPICE SUP.9) in the ECU project. It ensures all defects, deviations, and non-conformances are reproducibly logged, analyzed, resolved, verified, and communicated.

## 2. Problem Definition vs. Other Backlog Items
- **Problem (SUP.9)**: An observed deviation between actual behavior and expected/specified behavior (e.g., a bug, crash, or test failure).
- **Work Package (MAN.3)**: Planned engineering activity (e.g., implementing a new feature).
- **Change Request (SUP.10)**: A request to modify the baselined requirements or architecture, not fixing a deviation but changing the expectation.
- **Rehearsals/Spikes**: Exploratory work not intended for production baselines.

## 3. Problem Lifecycle

### 3.1. Reproducible Intake
Any team member can raise a Problem Record. It must include:
- **Title & Description**: Clear summary of the deviation.
- **Environment**: Hardware, software baseline (commit/tag), tools used.
- **Reproduction Steps**: Step-by-step instructions to reproduce.
- **Expected vs. Actual Result**: Clear comparison.
- **Evidence**: Logs, memory dumps, or screenshots.

### 3.2. Classification, Severity, and Priority
- **Severity**:
  - `S1 (Critical)`: Safety, cybersecurity, or system unbootable.
  - `S2 (High)`: Major function broken, no workaround.
  - `S3 (Medium)`: Function degraded, workaround exists.
  - `S4 (Low)`: Cosmetic or minor deviation.
- **Priority**: Determines scheduling (P1 Immediate, P2 Next Sprint, P3 Backlog).

### 3.3. High-Impact Alerts and Urgent Action
If a problem is classified as `S1 (Critical)`, an automated alert (or immediate manual escalation) is sent to the Project Lead, Architect, and Safety Manager.
**Urgent-Action Authorization**: The Project Lead may authorize an immediate hotfix branch, bypassing standard sprint planning, but never bypassing peer review or CI/CD gates.

### 3.4. Cause and Impact Analysis
Before implementation, the assigned owner must document:
- **Root Cause**: Why did the deviation occur? (e.g., 5 Whys).
- **Impact**: What other modules or systems might be affected by the defect or the proposed fix?

### 3.5. Durable Resolution and Verification
- **Resolution**: Code or configuration changes are made on a dedicated bugfix branch. The fix must be linked to the Problem ID (e.g., `fix: #123 memory leak`).
- **Verification**: The original reporter (or an independent tester) must verify the fix against the reproduction steps on the integrated baseline. Automated regression tests must be added if missing.

### 3.6. Linkage to Controlled Changes (SUP.10)
If fixing the problem requires modifying baselined requirements, interfaces, or architecture, a linked SUP.10 Change Request must be raised and approved by the CCB (Change Control Board) before the fix is merged.

### 3.7. Communication, Status/Trends, and Closure
- **Status Updates**: The problem state moves from `Open` -> `In Analysis` -> `In Progress` -> `In Review` -> `In Verification` -> `Closed`.
- **Trends**: The Quality Assurance (SUP.1) team generates monthly metrics on defect arrival rate, escape rate, and time-to-resolution.
- **Closure**: A problem is closed only after successful independent verification in the target environment.

## 4. Mechanism Validation (Fixtures)
- **Positive Fixture**: A properly formatted defect report with full reproduction steps, environmental data, and root-cause analysis is successfully routed through the lifecycle.
- **Negative Fixture**: A defect report lacking reproduction steps or misclassified as a "Work Package" is rejected during triage and routed back to the submitter for correction.
