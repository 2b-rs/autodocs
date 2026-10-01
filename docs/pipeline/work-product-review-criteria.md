# Work-Product Review Criteria & Evidence Schema (0015-07)

**Status:** Normative
**Reference:** Feature `0015-07` (Prerequisite: `0015-02`)

This document defines the quality criteria, explicit review requirements, and the evidence schema for each controlled Configuration Item (CI) / Work Product type in the `virtualized-automotive-ecu` project. It fulfills ASPICE SUP.8 / SUP.1 for review mechanisms and PA 2.2 for work-product adjustments.

## 1. Quality Criteria per Work Product Type

Every mutated CI is subject to review prior to integration.

### 1.1 Requirements Records (`req-*.md`)
- **Reviewer Authority:** Requirements Engineer (peer review) and Project Lead (or Architect if authorized).
- **Quality Criteria:**
  - Complete traceability to system/upstream context.
  - Testable and atomic (one `SHALL` statement per record).
  - Explicit rationale for non-functional or bounded scope decisions.
  - Zero unresolved syntax/schema violations.

### 1.2 Architecture & Design Decisions (`DEC-*` / `dec-*.md`)
- **Reviewer Authority:** Architect.
- **Quality Criteria:**
  - Evaluates explicitly stated alternative designs.
  - Lists the concrete impact on downstream implementation / SWE.3.
  - All interfaces strictly typed and mathematically bounded.

### 1.3 Implementation (Source Code)
- **Reviewer Authority:** Developer / Integrator (must be a different agent than the author).
- **Quality Criteria:**
  - 100% unit test coverage.
  - Zero lint/compiler errors.
  - Fulfills the Adversarial Completion Evidence requirement (`AE-1` through `AE-8`).

### 1.4 Test & Verification Records (Logs, Test Cases)
- **Reviewer Authority:** QA / Integrator.
- **Quality Criteria:**
  - Test results correspond exactly to the pinned git commit hash of the implementation.
  - Red-then-green baseline boundary is explicitly documented.

## 2. Review Enforcement Mechanism

### 2.1 The "Four-Eyes" Principle
No CI is accepted into a baseline (`main` branch) without passing a documented review from an agent who is distinct from the authoring agent.

### 2.2 The `Acceptance: ✓` Contract
The review decision is recorded durably using the literal string `Acceptance: ✓` either in the `TODO.md` artifact claim, or within the CI header itself.

## 3. Review Evidence Schema

When a review is completed, the following schema MUST be satisfied in the retained review log / commit message (or `agent-inbox` thread resolution):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Work Product Review Evidence",
  "type": "object",
  "required": ["artifact_id", "version_hash", "author", "reviewer", "reviewer_role", "criteria_checked", "findings", "decision", "timestamp"],
  "properties": {
    "artifact_id": {
      "type": "string",
      "description": "The exact ID of the CI or task (e.g., 0013-05)"
    },
    "version_hash": {
      "type": "string",
      "description": "Git commit hash of the exact version reviewed"
    },
    "author": {
      "type": "string",
      "description": "Identity of the agent who authored the CI"
    },
    "reviewer": {
      "type": "string",
      "description": "Identity of the authenticated reviewing agent"
    },
    "reviewer_role": {
      "type": "string",
      "description": "Formal role authorizing the review (e.g., Integrator)"
    },
    "criteria_checked": {
      "type": "array",
      "items": { "type": "string" },
      "description": "List of quality criteria verified (e.g., ['AE-3 Falsification Case', 'Traceability'])"
    },
    "findings": {
      "type": "array",
      "items": { "type": "string" },
      "description": "List of deviations or issues found. Must be empty if decision is ACCEPT."
    },
    "decision": {
      "type": "string",
      "enum": ["ACCEPT", "REWORK", "REJECT"],
      "description": "Final review decision"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO-8601 UTC timestamp of the review conclusion"
    }
  }
}
```

### 3.1 Issue Closure
If the `decision` is `REWORK`, the `findings` array must explicitly state the deviations. The artifact must re-enter the implementation loop. A subsequent review must explicitly link to the prior findings and confirm issue closure before issuing an `ACCEPT`.
