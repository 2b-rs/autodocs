# MAN.5 Recurring Risk Review Procedure (0017-03)

**Status:** Normative
**Reference:** Feature `0017-03` (Prerequisite `0017-02`)

This document defines the operating procedure, escalation thresholds, and evidence retention schema for conducting recurring reviews of the project risk register (`man5-risk-register.md`), satisfying ASPICE MAN.5 requirements for monitoring risk exposure and action effectiveness.

## 1. Operating Procedure for Recurring Risk Reviews

Risk reviews are conducted by the Project Lead and QA Manager to ensure that mitigation actions are effective and residual risks remain within acceptable thresholds.

### 1.1 Review Triggers and Cadence
- **Scheduled Cadence:** Weekly during active campaign execution, and mandatory before any formal Milestone Release (e.g., Campaign A completion).
- **Event-Driven Triggers:** 
  - Identification of a new High/Critical risk ($RPN \ge 15$).
  - A mitigation action misses its defined `due_date`.
  - Occurrence of a tracked risk event (e.g., API quota exhaustion incident).

### 1.2 Review Steps
1. **Identify New Risks:** Scan project mailboxes, metrics dashboards (`0017-06`), and `TODO.md` defect logs for emerging threats.
2. **Evaluate Mitigation Effectiveness:** For each risk marked `ACTIVE` or `CONTROLLED`, verify that the assigned mitigation action (`Tracking Ref`) is functioning. If a mitigation fails, the residual RPN must be reset to the initial RPN.
3. **Escalate Threshold Breaches:** Any risk where the Residual RPN climbs back to $\ge 15$ must be escalated immediately to the Project Lead for a `decision_request` (Replanning or Resource Allocation).
4. **Update Risk Register:** Mutate `man5-risk-register.md` with updated status, residual RPN, and closure dates.
5. **Retain Review Evidence:** Commit the updated register alongside a JSON risk review record (see Section 2) into the project evidence dossier.

## 2. Risk Review Evidence Schema

To prove that the reviews were actually operated and that decisions were retained, each review MUST generate a JSON record conforming to the following schema.

### 2.1 Schema Definition (`man5-risk-review-record-schema.json`)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Risk Review Record",
  "type": "object",
  "required": ["review_id", "timestamp", "reviewers", "risks_evaluated", "threshold_breaches", "decisions_retained"],
  "properties": {
    "review_id": { "type": "string" },
    "timestamp": { "type": "string", "format": "date-time" },
    "reviewers": {
      "type": "array",
      "items": { "type": "string", "description": "Agent identities conducting the review" }
    },
    "risks_evaluated": {
      "type": "array",
      "items": { "type": "string", "description": "List of Risk IDs reviewed" }
    },
    "threshold_breaches": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "risk_id": { "type": "string" },
          "breach_description": { "type": "string" },
          "escalation_target": { "type": "string" }
        }
      }
    },
    "decisions_retained": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "risk_id": { "type": "string" },
          "decision": { "type": "string", "enum": ["CONTINUE_MITIGATION", "CLOSE_RISK", "ESCALATE", "ACCEPT_RESIDUAL"] },
          "justification": { "type": "string" }
        }
      }
    }
  }
}
```

## 3. Action Effectiveness and Closure

A risk may only be transitioned to `MITIGATED` or `CLOSED` when:
1. The defined mitigation action is verified complete (e.g., via a merged PR or test case pass).
2. The Risk Review explicitly documents the `ACCEPT_RESIDUAL` or `CLOSE_RISK` decision in the `decisions_retained` array of the review record.
3. The closure is approved by the Risk Custodian (Project Lead).
