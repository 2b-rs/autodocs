# Feature Definition Structural Rules

**Status:** Normative candidate rules. `validate_feature_definition_package.py` checks the evidence manifest shape and rejects incomplete/cyclic candidate data. It is advisory until a separately authorized adoption decision; it never edits backlog state or grants approval.

## Machine-checkable manifest

A contract evidence manifest is JSON with this closed shape:

```json
{
  "schema": "feature-definition-evidence@v2",
  "feature": "0039",
  "reconciliation": {"path":"docs/pipeline/evidence/0039-01/study-reconciliation.json","study_path":"docs/dossiers/feature-definition-process-study.docx","study_sha256":"<64 lowercase hexadecimal characters>"},
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
| FDB-001 | Schema is exactly `feature-definition-evidence@v2`; IDs are unique and match their grammar. | malformed or ambiguous identity |
| FDB-002 | Every active criterion has non-empty `implemented_by` and `verified_by`; all references resolve. | missing outcome coverage |
| FDB-003 | Every Task has a non-empty primary result, capability, and evidence; evidence paths are repository-relative and exist. | non-executable or unverifiable Task |
| FDB-004 | Prerequisite endpoints resolve, have no self-edge, duplicate edge, or directed cycle. | invalid execution graph |
| FDB-005 | Every prerequisite has an allowed type: `producer`, `decision`, `readiness`, `integration`, or `closure`. | prose-only/unclear dependency |
| FDB-006 | Exactly one declared integration Task resolves to a Task. | missing or ambiguous parent integration |
| FDB-007 | The validator reports, but cannot decide, semantic-deadlock prompts: later-artifact completion, pre-package approval, downstream aggregate, or successor-provided capability. | reviewer action required; no automatic approval |
| FDB-008 | The reconciliation locator binds the informative study by its SHA-256. The English reconciliation has every `REC-01` through `REC-20` study recommendation in order, a selected/rejected/deferred/superseded disposition, accountable authority, existing authority/process artifacts, and a non-empty post-`0037` owner. | study input, disposition, authority, or cutover ownership is untraceable |

### Declared, not yet enforced

**`FDB-009` — the declared integration Task must carry `Integration review: mandatory`.**
`FDB-006` checks that exactly one integration Task is declared and resolves. It does **not**
check that the node carries the attribute that makes it a review floor. A manifest can
therefore pass `FDB-006` while naming an integration Task that gates nothing — the check is
satisfied and the guarantee is absent.

**This rule is stated and deliberately not yet implemented**, because enforcing it requires the
evidence manifest to carry the attribute at all: it lives in `TODO.md`, not in
`feature-definition-evidence@v2`, so enforcement means a manifest schema revision plus
validator and test changes, and a producer that populates it. That is bounded work, not a
one-line addition.

**Why it is marked rather than quietly added.** A rule written in prose that the validator does
not enforce is a split-brain contract: the document asserts a guarantee the tool does not
provide, and nobody discovers the gap until a case depends on it. `DEC-0041-006` names this
failure directly, and the `0044-12` review record forbids the mirror case — prose requiring a
trailer while the tool still passes commits without one. Adding `FDB-009` to the enforced table
without implementing it would create exactly the state this Task's own findings call
forbidden. It is listed here, outside the enforced set, until it is implemented.

**`FDB-010` — a baseline claim carries its acceptance state.** Where a manifest cites a
governance baseline, the citation records the exact commit **and** whether that baseline held
current Task Acceptance when measured. Same status as `FDB-009`: declared, not yet enforced,
pending the same schema revision.


A passing structural result does not prove architecture correctness, authority, risk acceptance, or semantic feasibility. Those remain human review duties under the main process.
