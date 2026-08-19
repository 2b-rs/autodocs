# Feature Definition Structural Rules

**Status:** Normative candidate rules. `validate_feature_definition_package.py` checks the evidence manifest shape and rejects incomplete/cyclic candidate data. It is advisory until a separately authorized adoption decision; it never edits backlog state or grants approval.

## Machine-checkable manifest

A contract evidence manifest is JSON with this closed shape:

```json
{
  "schema": "feature-definition-evidence@v1",
  "feature": "0039",
  "criteria": [{"id":"FD-0039-AC-001","implemented_by":["0039-01"],"verified_by":["E-001"]}],
  "tasks": [{"id":"0039-01","primary_result":"process package","capability":"privileged","evidence":["E-001"]}],
  "prerequisites": [{"consumer":"0039-01","producer":"0039-04","type":"producer"}],
  "evidence": [{"id":"E-001","path":"docs/pipeline/feature-definition-and-breakdown.md"}],
  "integration_task": "0039-01"
}
```

## Deterministic rules

| ID | Rule | Failure |
|---|---|---|
| FDB-001 | Schema is exactly `feature-definition-evidence@v1`; IDs are unique and match their grammar. | malformed or ambiguous identity |
| FDB-002 | Every active criterion has non-empty `implemented_by` and `verified_by`; all references resolve. | missing outcome coverage |
| FDB-003 | Every Task has a non-empty primary result, capability, and evidence; evidence paths are repository-relative and exist. | non-executable or unverifiable Task |
| FDB-004 | Prerequisite endpoints resolve, have no self-edge, duplicate edge, or directed cycle. | invalid execution graph |
| FDB-005 | Every prerequisite has an allowed type: `producer`, `decision`, `readiness`, `integration`, or `closure`. | prose-only/unclear dependency |
| FDB-006 | Exactly one declared integration Task resolves to a Task. | missing or ambiguous parent integration |
| FDB-007 | The validator reports, but cannot decide, semantic-deadlock prompts: later-artifact completion, pre-package approval, downstream aggregate, or successor-provided capability. | reviewer action required; no automatic approval |

A passing structural result does not prove architecture correctness, authority, risk acceptance, or semantic feasibility. Those remain human review duties under the main process.
