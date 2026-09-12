# MAN.3 Actual-Versus-Plan Review Mechanism (0012-06)

**Status:** Normative
**Reference:** Feature `0012-06` (Prerequisite: `0012-02`)

This document defines the process for monitoring project execution against the MAN.3 Integrated Project Plan (`docs/pipeline/man3-project-management-plan.md`) and establishes the formal mechanism for analyzing deviations, applying corrective actions, and retaining immutable review evidence, satisfying ASPICE MAN.3 requirements.

## 1. Review Cadence and Authority

Monitoring actual progress against the plan ensures that schedule, effort, and scope deviations are detected before they compromise milestone delivery.

- **Cadence:** Reviews occur at the completion of each defined project Campaign (Campaign A, B, C, D) or whenever an escalated schedule/resource deviation breaches defined thresholds (e.g., >20% effort variance per M-SCH-01).
- **Authority:**
  - **Project Lead:** Authorized to initiate the review, analyze variances, decide on replanning, and approve corrective actions.
  - **Integrator:** Provides the raw data metrics and verifiable task completion (`TODO.md`) states.

## 2. Review Execution

During the review, the Project Lead assesses the following inputs:
1. State of `TODO.md` (Planned tasks vs. `DONE` tasks).
2. MAN.6 Metric Reports (Effort variance, Defect aging, Resource quota usage).
3. Risk Register (`man5-risk-register.md`) exposure changes.

### 2.1 Escalation of Deviations
If a deviation exceeds acceptable bounds (e.g., a critical SWE.2 architectural milestone slips by more than 2 days):
1. The blocking item is formally tagged `BLOCKED` in `TODO.md`.
2. A formal `decision_request` is sent via `agent-inbox` to the Project Lead outlining the root cause.
3. The Project Lead must respond with a documented replanning directive (e.g., reassigning tasks, extending the milestone date, or descoping non-critical features).

## 3. Evidence Contract for Corrective Actions

Any deviation that results in replanning or corrective action MUST be recorded as an immutable JSON log within the campaign's evidence dossier (`docs/dossiers/`).

### 3.1 Review Evidence Schema (`man3-review-record-schema.json`)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Actual-vs-Plan Review Record",
  "type": "object",
  "required": [
    "review_id", "campaign", "timestamp", "reviewer", "deviations", "decision", "replanning_required"
  ],
  "properties": {
    "review_id": { "type": "string" },
    "campaign": { "type": "string", "description": "e.g., Campaign B" },
    "timestamp": { "type": "string", "format": "date-time" },
    "reviewer": { "type": "string", "description": "Project Lead identity" },
    "deviations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["cause", "impact_assessment"],
        "properties": {
          "task_id": { "type": "string" },
          "cause": { "type": "string" },
          "impact_assessment": { "type": "string" },
          "corrective_action": {
            "type": "object",
            "properties": {
              "description": { "type": "string" },
              "owner": { "type": "string" },
              "due_date": { "type": "string", "format": "date" }
            }
          }
        }
      }
    },
    "decision": { "type": "string", "enum": ["PROCEED", "REPLAN", "HALT"] },
    "replanning_required": { "type": "boolean" },
    "closure_confirmed": { "type": "boolean", "description": "True when corrective actions are verified effective" }
  }
}
```

## 4. Operation and Effectiveness Verification

This document specifies the *readiness* for the review process. The *actual operation* and retention of these review records will be executed during the managed ECU pilot and collected under feature `0018-02`. Effectiveness of corrective actions is evaluated in the subsequent milestone review.
