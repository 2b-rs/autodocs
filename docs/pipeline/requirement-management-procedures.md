# Requirement Management Procedures (0013-08)

**Status:** Normative
**Reference:** Task `0013-08`

This document defines the formal procedures for agreeing, communicating, analyzing, and superseding requirements (both stakeholder and software) within the `virtualized-automotive-ecu` product lifecycle. It supports ASPICE SWE.1 (Software Requirements Analysis).

## 1. Requirement Agreement & Review
Requirements are not operative until explicitly agreed.

### 1.1 Draft State (`candidate-unapproved`)
When a requirement or a requirement baseline candidate is created (e.g., `req-0013-02-stakeholder-requirements-baseline.md`), it is classified as `candidate-unapproved`. At this stage, the Requirements Engineer formulates the structure and content based on available sources (or gaps in sources).

### 1.2 Agreement Process
1. **Four-Eyes Review**: The candidate file is reviewed by the designated Reviewer (typically an Architect or the Project Lead if no specific authority is assigned). The Reviewer checks for verifiability, traceability, and atomic structure.
2. **Management / Stakeholder Approval**: Functional content (or blocked-source content) requires the explicit disposition of the assigned product authority via a `DEC-*` record or a Management/Integrator review.
3. **Acceptance Signature**: Agreement is codified by changing the baseline status to `approved` and capturing the `Acceptance: ✓` marker alongside the exact commit hash of the document.

## 2. Status Communication
Requirement status and baseline validity must be proactively communicated to all downstream stakeholders (e.g., Architecture, QA, Implementation).

- **Mailbox Broadcast**: Whenever a requirements baseline transitions to `approved`, or undergoes an authorized change, the Requirements Engineer MUST broadcast a message via `agent-inbox` to all affected roles.
- **Message Format**: The broadcast must contain:
  - Subject: `DECISION <Baseline ID> approved/updated`
  - Body: The exact commit hash, the scope of the change, and the implications for downstream SWE.2/SWE.3 activities.

## 3. Change-Impact Analysis & Consistency Review
Changes to an approved requirements baseline trigger an obligatory impact analysis (SUP.10 dependency).

### 3.1 Impact Analysis Triggers
- Addition of new stakeholder/system sources.
- Modification or supersession of an existing `approved` requirement.
- Deletion/obsoletion of a requirement.

### 3.2 Analysis Procedure
1. **Traceability Sweep**: The Requirements Engineer queries the automated trace schema (from `0013-06`) to identify all downstream artifacts linked to the modified requirement ID(s):
   - Software Requirements (SWE.1)
   - Architecture Elements (SWE.2)
   - Test Cases (SWE.6)
2. **Impact Dossier**: The findings are documented in a Change Request (CR) dossier. The dossier must explicitly state the estimated effort to update the linked architecture and tests.
3. **Consistency Verification**: After the downstream changes are implemented, a consistency review is conducted to ensure no orphan traces remain and the updated requirement is fully verified.

## 4. Baseline Supersession
When a requirements baseline is updated, history must never be rewritten.

1. **Append-Only History**: Changes must be recorded in the document's "Change history" table.
2. **Version Increment**: The document version (e.g., `v1.0.0` to `v1.1.0`) and change ID (`CHG-XXX`) must be incremented.
3. **Superseded Records**: Requirements that are no longer valid must be marked `superseded` or `rejected`, retaining the prior text and rationale for the change. They must *not* be deleted from the file.
4. **Retention**: The repository commit history and the inline change log serve as the retained decision record.

## 5. Retained Decisions
Decisions to agree on, reject, or supersede a requirement must be retained durably.
- **Method**: Decisions are either recorded in a dedicated `docs/dossiers/dec-*.md` file (for major scope changes) or inline in the requirement's `Change history` section alongside the deciding authority's identity and the exact date.
