# Periodic Management Review Procedure (0017-07)

**Status:** Normative
**Reference:** Feature `0017-07` (Prerequisites: `0012-06`, `0017-03`, `0017-06`)

This document defines the comprehensive Periodic Management Review process, satisfying the overarching review requirements across ASPICE MAN.3 (Project Management), MAN.5 (Risk), MAN.6 (Measurement), and SUP.1 (QA).

## 1. Scope and Objective
The Management Review is the highest-level governance mechanism in the project. Its objective is to provide the Project Lead and senior stakeholders with a consolidated view of project health, enabling binding decisions on replanning, resource reallocation, and release authorization.

## 2. Review Cadence
- **Mandatory:** At the conclusion of every major project milestone (Campaign A, B, C, D).
- **Ad-Hoc:** Upon critical escalation from a subordinate review (e.g., a Risk Review `0017-03` threshold breach, or an Actual-vs-Plan `0012-06` critical schedule slip).

## 3. Required Input Artifacts
The Integrator / Compliance Officer must prepare the following dossier prior to the review:
1. **Actual-vs-Plan Performance (`0012-06`)**: Burndown, effort variance, and slipped milestones.
2. **Resource & Competence Status**: `roster.json` health and quota usage reports.
3. **Risk Register (`0017-03`)**: High/Critical exposure items and mitigation effectiveness.
4. **Metrics Trend Report (`0017-06`)**: Quality and Outcome metrics (M-QUAL-01, M-QUAL-02).
5. **QA Findings (`SUP.1`)**: Number of non-conformances and audit results.
6. **Problem / Change Status (`SUP.9/10`)**: Defect aging and open critical bugs.
7. **Release Readiness (`SPL.2`)**: Known issues ratio (M-REL-01).

## 4. Execution and Decision Authority
The **Project Lead** chairs the review. The review MUST yield explicit decisions on:
- Continuation vs. Halting of the campaign.
- Acceptance of residual risks.
- Formal approval of replanning (schedule extensions, descoping).
- Assignment of corrective actions with named owners and strict due dates.

## 5. Evidence Contract & Retention Schema

Every Management Review MUST generate an immutable JSON record stored in `docs/dossiers/management-reviews/`.

### 5.1 Schema Definition (`management-review-record-schema.json`)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Periodic Management Review Record",
  "type": "object",
  "required": [
    "review_id", "timestamp", "chairperson", "milestone",
    "inputs_reviewed", "findings", "decisions", "escalations"
  ],
  "properties": {
    "review_id": { "type": "string" },
    "timestamp": { "type": "string", "format": "date-time" },
    "chairperson": { "type": "string" },
    "milestone": { "type": "string", "description": "e.g., Campaign A Closure" },
    "inputs_reviewed": {
      "type": "object",
      "properties": {
        "actual_vs_plan": { "type": "boolean" },
        "resources_competencies": { "type": "boolean" },
        "risks": { "type": "boolean" },
        "metrics_qa_problems": { "type": "boolean" },
        "release_readiness": { "type": "boolean" }
      }
    },
    "findings": {
      "type": "array",
      "items": { "type": "string" }
    },
    "decisions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["decision_type", "description", "owner", "due_date"],
        "properties": {
          "decision_type": { "type": "string", "enum": ["REPLAN", "CORRECTIVE_ACTION", "ACCEPTANCE", "CLOSURE"] },
          "description": { "type": "string" },
          "owner": { "type": "string" },
          "due_date": { "type": "string", "format": "date" },
          "status": { "type": "string", "enum": ["OPEN", "CLOSED"] }
        }
      }
    },
    "escalations": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Items requiring external stakeholder intervention"
    }
  }
}
```

## 6. Closure
The review is considered closed when the JSON record is committed to the `main` branch. Any generated corrective actions must be injected into the active `TODO.md` backlog as discrete tasks blocking the subsequent milestone.
