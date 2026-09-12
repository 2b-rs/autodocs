# Process Performance Strategy (PA 2.1)

**Status:** Normative
**Reference:** Feature 0012-08

This document defines the process performance strategy for the assessed ECU scope, covering the 14-process nucleus (`SWE.1`–`SWE.6`, `SPL.2`, `SUP.1`, `SUP.8`, `SUP.9`, `SUP.10`, `MAN.3`, `MAN.5`, `MAN.6`). It establishes the measurable objectives, criteria, assumptions, constraints, and measurement methods required by ASPICE CL2 (PA 2.1).

## 1. Global Performance Strategy
Our overarching strategy is to achieve process performance through **automation-assisted enforcement** (via continuous integration, typed schemas, and strict checkpoint/approval mechanics) supplemented by **human-in-the-loop governance** where qualitative judgment is required (e.g., capability rating, architectural breakdown). 

We do not generate documentation retrospectively; instead, all process artifacts are retained directly in their natural `ecu-execution` format as immutable records (e.g., git commits, decision records, integration reviews).

### 1.1 Global Assumptions & Constraints
- **Assumptions**: 
  - Git repository structure (`autodocs`) serves as the single source of truth for both code and process records.
  - CI infrastructure consistently executes configured checks before allowing integration.
- **Constraints**: 
  - We operate under resource limits governed by the current agent roster and their assigned capability classes (`sandboxed-grunt`, `unprivileged`, `privileged`).
  - Separation of concerns (TK-1 rule) MUST be enforced structurally; exceptions require an explicit, bounded waiver.

## 2. Process-Specific Objectives, Criteria & Methods

### 2.1 SWE.1: Software Requirement Analysis
- **Objective**: Establish a complete, unambiguous, and testable software requirement specification.
- **Criteria**: 100% of functional requirements have an associated validation criteria (test case or manual step). 
- **Method**: Schema validation on requirement markdown artifacts (`_src/validate.py`); mandatory manual review by a designated Requirements Engineer.

### 2.2 SWE.2: Software Architectural Design
- **Objective**: Translate requirements into an architectural design that assigns all requirements to elements and defines interfaces.
- **Criteria**: 100% trace coverage from SWE.1 requirements to SWE.2 components. Zero unresolved technical dependencies before integration.
- **Method**: Feature breakdown analysis (`feature-breakdown.md` records); independent Architect review and approval of the design topology.

### 2.3 SWE.3: Software Detailed Design and Unit Construction
- **Objective**: Develop software units that conform precisely to the SWE.2 architectural design.
- **Criteria**: Zero lint/compiler errors. Every commit ties back to an approved claim/task.
- **Method**: Direct implementation via local execution, tracked by `TODO.md` claims. Static analysis in CI.

### 2.4 SWE.4: Software Unit Verification
- **Objective**: Verify that every constructed software unit satisfies its detailed design and non-functional constraints.
- **Criteria**: 100% of automated unit tests pass (zero regressions). 
- **Method**: Automated test execution via GitHub Actions / CI run-loops.

### 2.5 SWE.5: Software Integration and Integration Testing
- **Objective**: Assemble software units into an integrated item and verify interfaces.
- **Criteria**: All component interfaces resolve and link correctly. Integration tests (testing multiple units) pass 100%.
- **Method**: Integrator-driven merges (via `integration-plan.schema.json`).

### 2.6 SWE.6: Software Qualification Testing
- **Objective**: Verify that the integrated software satisfies all SWE.1 software requirements.
- **Criteria**: 100% traceability from SWE.1 requirements to passing end-to-end qualification tests.
- **Method**: Automated system-level suites (e.g., `pytest` on the integrated product baseline).

### 2.7 SPL.2: Product Release
- **Objective**: Package and deliver the software with correct versioning, notes, and known limitations.
- **Criteria**: Final release package contains all constituent items, release notes, and explicit approval by the Release Authority.
- **Method**: Release packaging scripts; explicit `Acceptance: ✓` gate in `TODO.md` by the Release Authority.

### 2.8 SUP.1: Quality Assurance
- **Objective**: Independently assure that processes and work products comply with this repository's ASPICE baseline.
- **Criteria**: All deviations are formally recorded as non-conformances and resolved or escalated.
- **Method**: Scheduled QA audits; process findings logged by the QA Manager (`docs/pipeline/issue-store-findings.md`).

### 2.9 SUP.8: Configuration Management
- **Objective**: Establish and maintain the integrity of all work products.
- **Criteria**: 100% of items are version-controlled, uniquely identifiable, and retrievable. 
- **Method**: Git version control; schema-driven configuration metadata (e.g., `0020-02` metadata fields).

### 2.10 SUP.9: Problem Resolution Management
- **Objective**: Identify, track, analyze, and close problems systematically.
- **Criteria**: 100% of reported problems are assigned a severity, investigated, and closed with verification.
- **Method**: Issue tracking workflow via `TODO.md` and dedicated problem-incident dossiers.

### 2.11 SUP.10: Change Request Management
- **Objective**: Ensure all changes are analyzed, approved, and tracked to implementation.
- **Criteria**: Every code mutation (outside sandboxed development) traces to an approved CR or Feature.
- **Method**: Mandatory `decision-record.md` generation for impactful scope changes (TK-2 rule); integration pull requests.

### 2.12 MAN.3: Project Management
- **Objective**: Establish and monitor a project plan reflecting estimates, assignments, and schedule.
- **Criteria**: Deviations >15% of estimated effort are escalated. Every task has a named assignee and explicit acceptance.
- **Method**: `TODO.md` serves as the live integrated plan; periodic actual-vs-plan checks.

### 2.13 MAN.5: Risk Management
- **Objective**: Identify and mitigate technical, process, and external risks.
- **Criteria**: All identified high-severity risks have an active mitigation strategy. 
- **Method**: Risk register updates at project milestones; `[u]` flagging during integration if residual risk is unacceptable.

### 2.14 MAN.6: Measurement
- **Objective**: Collect and analyze process and product data to support management decisions.
- **Criteria**: Core metrics (test pass rate, defect density, integration success rate) are available for all process milestones.
- **Method**: Build artifacts (e.g., `build-report-schema.md`) generated by CI pipelines to provide objective measurement data.
