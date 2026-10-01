# MAN.3 ECU Project Plan

## 1. Goals and Motivation
The primary goal of the ECU project is to deliver a reliable, secure, and performant embedded control unit adhering to Automotive SPICE (ASPICE) compliance and relevant functional safety standards. This plan provides the foundational management framework for achieving these objectives predictably.

## 2. Boundaries and Scope
- **In Scope**: Software architecture, development, unit testing, integration testing, system testing, and release management of the ECU software.
- **Out of Scope**: Hardware design and manufacturing, vehicle-level integration testing (handled by OEM).

## 3. Project Lifecycle and Releases
The project follows an iterative V-Model lifecycle, incorporating Agile principles for work package delivery while maintaining rigorous phase-gate reviews for safety and compliance.
- **Milestones**: A-Sample (PoC), B-Sample (Functional), C-Sample (Production Intent), D-Sample (SOP).
- **Releases**: Managed per the SPL.2 Release Specification.

## 4. Feasibility and Estimates
Feasibility studies have confirmed the viability of the proposed architecture against the hardware constraints (memory, CPU). Estimates for work packages are derived using historical data from similar projects, incorporating a 20% risk buffer.

## 5. Work Packages and Dependencies
Work packages are defined in the project backlog (TODO.md).
Key dependencies:
- Hardware prototype availability for integration testing.
- Third-party library qualifications (e.g., RTOS, communication stacks).
- Tools qualification (compiler, static analysis).

## 6. Schedule and Milestones
- **M1 (Requirements Freeze)**: Month 3
- **M2 (Architecture Baseline)**: Month 4
- **M3 (First Code Drop - B-Sample)**: Month 6
- **M4 (System Test Complete)**: Month 8
- **M5 (SOP / Final Release)**: Month 10

## 7. Deliverables and Commitments
Deliverables include the software release package (binaries, symbols), release notes, test reports, and compliance documentation. Commitments are baselined at each milestone gate review.

## 8. Entry and Exit Criteria
- **Phase Entry**: Preceding phase artifacts must be approved; required resources must be allocated.
- **Phase Exit**: All planned verification/validation activities completed; open defects must not exceed defined severity thresholds; management review approval.

## 9. Qualified Assignments and Competencies
Personnel assignments are recorded in the task tracking system. Core competencies required:
- Embedded C/C++ Development
- ASPICE & ISO 26262 familiarity
- RTOS configuration and scheduling
- Hardware-Software Integration

## 10. Tools, Infrastructure, and Material Resources
- **Tools**: GCC/Clang cross-compilers, Git, Static/Dynamic Analysis tools, Hardware-in-the-Loop (HIL) simulators.
- **Infrastructure**: CI/CD pipeline servers, artifact repository, defect tracking system.
- **Materials**: Developer test boards, final target ECU hardware.

## 11. Interfaces and Communication
External and internal communication channels are strictly defined in the MAN.3 Interface Communication Matrix, specifying SLAs, escalation paths, and reporting formats.

## 12. Review and Escalation
Progress against this plan is monitored continuously and reviewed formally per the MAN.3 Actual-vs-Plan Review Mechanism. Deviations exceeding 10% of schedule or budget trigger immediate escalation to the Project Lead and subsequent executive review.
