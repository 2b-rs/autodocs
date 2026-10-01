# MAN.3 Project Management & Execution Plan (0012-01)

## 1. Project Goals, Motivation & Scope
- **Strategic Goal**: Establish a deterministic, multi-agent software engineering pipeline capable of delivering automotive-grade embedded software artifacts with complete bidirectional traceability.
- **Motivation**: Enforce rigorous compliance with Automotive SPICE (ASPICE 3.1) and ISO 26262 functional safety baselines while maximizing agent execution parallelism and throughput.
- **Core Deliverables**: Controlled requirements repository, architectural decision records, deterministic tooling, test suites, immutable release packages, and verified provenance journals.

## 2. Project Boundaries & External Interfaces
- **In-Scope**:
  * Definition and implementation of software development lifecycle (SWE.1 through SWE.6).
  * Supporting processes including Quality Assurance (SUP.1), Configuration Management (SUP.8), Problem Resolution (SUP.9), and Change Request Management (SUP.10).
  * Priority offer orchestration, mailbox asynchronous messaging, and worktree isolation.
- **Out-of-Scope**:
  * Direct execution of live production vehicle flashing.
  * Uncertified external organizational capability claims without an accredited assessor audit.
- **Interfaces**:
  * Agent mailbox MCP interface (`agent-inbox`).
  * Provider API boundaries (`codex`, `claude`, `agy`, `cursor`).

## 3. Project Lifecycle Model & Phase Gates
The pipeline adopts an iterative, gated V-Model architecture:

1. **Gate G-REQ (Requirements Baseline)**: Formal review and sign-off on stakeholder and system/software requirements (`REQ-*`).
2. **Gate G-ARCH (Architecture Baseline)**: Architecture decomposition and ADR recording (`DEC-*`).
3. **Gate G-DEV (Implementation & Unit Test)**: Direct local execution on item branches, unit tests passing (100% target).
4. **Gate G-INT (Integration Baseline)**: Fast-forward merge preflight verification and integration test suite execution.
5. **Gate G-QUAL (Qualification & Verification)**: System-level regression testing and independent QA audit verdict.
6. **Gate G-REL (Release Baseline)**: BOM generation, immutable tree digest calculation, and release authority sign-off.

## 4. Release Scope & Packaging
- **Release Versioning**: Semantic Versioning (`vMAJOR.MINOR.PATCH`).
- **Release Package Artifacts**:
  * Source code tree with verified tree digest.
  * Bill of Materials (BOM) inventory JSON and human-readable manifest.
  * Test execution logs and coverage reports.
  * Four-Eyes review records and QA deviation closure logs.

## 5. Feasibility Evaluation & Risk Management
- **Provider Quota & Load Shedding**: Monitor five-hour, weekly, and monthly quota consumption. When remaining quota falls below 10%, initiate load-shedding and hand over active claims to healthy peer runtimes.
- **Concurrency & Worktree Isolation**: Prevent concurrent write collisions via strict item-owned branch and worktree scoping.
- **Technical Risk Assessment**: Mitigate drift and stale branch issues through continuous integration preflight checks and fast-forward-only merge constraints.

## 6. Consistency Rules for Planning & Commitments
- **WBS & Estimation Consistency**: Every task estimate (`planned_minutes`) must reflect realistic execution time plus a 20% contingency buffer for review rounds.
- **Resource Allocation**: No agent may be assigned more than one concurrent active task execution without explicit deputy delegation.
- **Schedule Synchronization**: When an assignee's `until` timestamp expires, Dispatcher must review progress, re-announce `until`, or initiate reassignment.
- **Commitment Integrity**: Work commitments are sealed upon atomic priority offer `ACCEPT` (AWARD) and can only be renegotiated through formal rework/hold transitions.

## 7. Integrated Project Schedule & Milestones
The project is divided into iterative campaigns (increments), each with predefined schedules and deliverables.

### 7.1 Campaign A: Foundation & Process Baseline
- **Milestone A.1 (M1)**: Core Process Definition.
  - *Schedule*: Weeks 1-2.
  - *Deliverables*: Approved ASPICE CL2 process strategies, process-roles, evidence catalogues.
  - *Entry Criteria*: Project initiation approved.
  - *Exit Criteria*: Independent QA review passed for process assets.
- **Milestone A.2 (M2)**: Toolchain & CI Automation.
  - *Schedule*: Weeks 3-4.
  - *Deliverables*: Agent mailbox, worktree isolation scripts, validation schemas.
  - *Entry Criteria*: M1 completed.
  - *Exit Criteria*: 100% automated schema validation passing on core docs.

### 7.2 Campaign B: Requirements & Architecture
- **Milestone B.1 (M3)**: Software Requirements Baseline.
  - *Schedule*: Weeks 5-6.
  - *Deliverables*: Versioned `req-*.md` documents, stakeholder traces.
  - *Entry Criteria*: Process baseline (Campaign A) operative.
  - *Exit Criteria*: Requirements Engineer and Stakeholders sign off.
- **Milestone B.2 (M4)**: Architectural Design Baseline.
  - *Schedule*: Weeks 7-8.
  - *Deliverables*: `feature-breakdown.md`, component interfaces.
  - *Entry Criteria*: M3 completed.
  - *Exit Criteria*: Architecture approved by Architect role.

### 7.3 Campaign C: Execution & Verification
- **Milestone C.1 (M5)**: Unit Construction & Verification.
  - *Schedule*: Weeks 9-14.
  - *Deliverables*: Source code (`_src`), unit tests, code-review logs.
  - *Entry Criteria*: M4 completed.
  - *Exit Criteria*: Zero lint errors, 100% unit tests passing.
- **Milestone C.2 (M6)**: Integration & Qualification.
  - *Schedule*: Weeks 15-18.
  - *Deliverables*: Integration test results, qualification test reports.
  - *Entry Criteria*: M5 completed.
  - *Exit Criteria*: 100% traceability from requirements to passing qualification tests.

### 7.4 Campaign D: Release & Assessment
- **Milestone D.1 (M7)**: Release Candidate.
  - *Schedule*: Weeks 19-20.
  - *Deliverables*: Release package, known issues list, SPL.2 manifest.
  - *Entry Criteria*: M6 completed.
  - *Exit Criteria*: Release Authority approval (`Acceptance: ✓`).

## 8. Work Packages & Dependencies
Work packages are managed as granular atomic tasks in `TODO.md` linked via strict `PREREQ` chains.
- **WP Type: Requirements Engineering (SWE.1)**.
  - *Dependencies*: Precedes SWE.2; relies on Stakeholder inputs.
  - *Estimates*: 1-2 hours per `00XX-XX` feature task.
- **WP Type: Architecture & Design (SWE.2, SWE.3)**.
  - *Dependencies*: Follows SWE.1, precedes Implementation.
  - *Estimates*: 2-4 hours per component task.
- **WP Type: Implementation & Unit Testing (SWE.3, SWE.4)**.
  - *Dependencies*: Follows SWE.2/SWE.3 design.
  - *Estimates*: 4-8 hours per code module task.
- **WP Type: Verification & QA (SWE.5, SWE.6, SUP.1)**.
  - *Dependencies*: Follows Implementation.
  - *Estimates*: 1-3 hours per test suite/audit task.

## 9. Infrastructure & Resource Commitments
- **Infrastructure**: `autodocs` GitHub repository, GitHub Actions (CI/CD pipeline), isolated agent execution environments.
- **Skills/Competencies**: Agent roster defined by capability classes (`sandboxed-grunt`, `unprivileged`, `privileged`), matched to tasks via the Coordinator's evaluation of the required engineering roles (e.g., Architect, Requirements Engineer).
- **Commitments**: The Project Lead commits to the schedule and resource provisioning. The internal execution team commits to the granular `planned_minutes` during task acceptance.
