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
