# External Findings and Curation Integration Rules (0016-15)

**Status:** Normative
**Reference:** Feature `0016-15` (Prerequisite: `0016-03`)

This document defines how domain-specific records—such as external validation findings, extraction residuals, review queues, and AI proposals—are integrated into the canonical ASPICE problem and change management system (SUP.9 / SUP.10) governed by `TODO.md`.

## 1. Principle of Non-Replacement

Domain-specific records contain deep context (e.g., SAST scanner vulnerability trees, AI prompt traces, raw hardware validation telemetry) that cannot be cleanly flattened into a single `TODO.md` line item.
**Rule:** The canonical problem/change record in `TODO.md` MUST NOT replace or duplicate the domain-specific record. Instead, the canonical record acts as the routing and authorization wrapper, linking to the domain record as its primary evidence.

## 2. Integration Mapping Rules

When an external system or curation queue generates an actionable finding, it must be triaged and mapped according to the rules defined in `0016-03`:

### 2.1 Validation Findings (e.g., test failures, SAST/DAST alerts)
- **Classification:** SUP.9 (Problem)
- **Mapping:** Create a `(problem, open)` entry in `TODO.md`.
- **Linking:** Append `REF: <path-to-finding-report>` or `REF: <external-URL>` to the `TODO.md` description. The domain record remains the authoritative source for the technical details of the fault.

### 2.2 Extraction Residuals and Review Queues
- **Classification:** SUP.9 (Problem) if it represents a defect in baselined work; MAN.3 (Task) if it represents unfinished planned work.
- **Mapping:** Create the appropriate entry in `TODO.md`.
- **Linking:** The `TODO.md` item must reference the specific review checklist or extraction log (e.g., `REF: docs/dossiers/review-001-residuals.md`).

### 2.3 AI Proposals and Feature Requests
- **Classification:** SUP.10 (Change Request)
- **Mapping:** Create a `(change, open)` entry in `TODO.md`.
- **Linking:** The proposal must undergo Change Control Board (CCB) authorization (`0016-04`). The `TODO.md` item must reference the AI transcript or proposal document containing the rationale and proposed architecture impact.

## 3. Lifecycle Synchronization

The state of the canonical `TODO.md` item (open, in_progress, done) dictates the project-level execution state.
1. **Implementation:** Work is performed on a dedicated branch tied to the `TODO.md` claim.
2. **Verification:** The integrator verifies the fix against the *domain-specific record* (e.g., re-running the specific SAST scanner).
3. **Closure:** When the `TODO.md` item is marked `DONE` (and Accepted by the Project Lead), the linked domain-specific record is considered conceptually resolved in the project baseline.

By enforcing these rules, the project maintains ASPICE SUP.9/10 compliance and centralized traceability in `TODO.md` without losing the rich context of specialized external tools.
