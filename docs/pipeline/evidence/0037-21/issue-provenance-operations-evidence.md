# Task 0037-21: Issue and Provenance Operations Documentation Evidence

## Overview

Task `0037-21` updates maintainer and agent guidance across the repository authority and documentation suite (`SANDBOX.md`, `AGENTS.md`, `PRIVILEGED.md`, `agent-workflow.json`, `docs/pipeline/agent-workflow.md`, `docs/pipeline/tools.md`, `docs/pipeline/reports.md`, `docs/pipeline/README.md`) for issue-store and provenance operations under the direct execution model (`DEC-0037-002`).

## Criteria Verification

- **AC-001 (Capability & Runner Models):**
  - Documented exact separation between privileged direct local execution and sandboxed execution.
  - Specified Runner role for long-running Task-ID-bound jobs with progress, cancellation, and recovery.
  - Defined clean-checkout invariants, dry-run/staged behavior, error codes, and audit locations.

- **AC-002 (Pre/Post-Cutover Boundary):**
  - Clarified that until the controlled Feature 0037 cutover, `TODO.md` and `DONE.md` remain operative for runtime session management.
  - Post-cutover `issues/` commands and schemas (`issuectl`, `issue_store`, `issue_validate`) are documented as shadow/pre-cutover contracts.

- **AC-003 (Policy Semantic Continuity):**
  - Mapped legacy queue operations (claims, handoffs, escalations, acceptances) into issue-native equivalents (`claim.json`, `closure.json`, `decision-*.json`).
  - Preserved autonomous intent-preserving backlog repair, suggestion capture, and one-use request semantics without runner escalation.

- **AC-004 (Agent Entry Point Parity):**
  - Standardized capability detection and first-read/recovery sequences across agent-facing instructions.

## Validation

All documentation paths, links, and schemas verified consistent and free of contradictions.
