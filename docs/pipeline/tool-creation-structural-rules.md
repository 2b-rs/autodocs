# Reusable Tool Process Structural Rules

**Status:** Candidate normative rules. `validate_tool_creation_package.py` is read-only and advisory until independent review and an explicit baseline decision. It never registers, deploys, executes, or promotes a tool.

## Evidence manifest

The closed JSON shape is:

```json
{
  "schema": "tool-creation-evidence@v1",
  "feature": "0039",
  "reconciliation": {"path":".../study-reconciliation.json","study_path":"docs/dossiers/tool-creation-improvement-process-study.docx","study_sha256":"<64 hex>"},
  "controls": [{"id":"TCP-001","artifact":"docs/pipeline/tool-creation-and-improvement.md"}],
  "pilots": [{"id":"P-001","shape":"new-capability","evidence":"...","decision":"rejected-pending-independent-review"}],
  "evidence": [{"id":"E-001","path":"docs/pipeline/tool-creation-and-improvement.md"}]
}
```

| ID | Deterministic rule | Failure meaning |
|---|---|---|
| TCP-001 | Exact schema, Feature ID, unique IDs, repository-relative existing paths. | Ambiguous or untraceable package. |
| TCP-002 | The informative study digest and reconciliation locator match; reconciliation has ordered `REC-01` through `REC-20`, disposition, authority, artifacts, and post-cutover owner. | Study adoption or ownership is untraceable. |
| TCP-003 | Controls cover discovery, candidate isolation, typed execution boundary, qualification, ownership, pilots/metrics, and retirement. | Lifecycle has a missing mandatory control. |
| TCP-004 | Exactly two pilot shapes exist: `new-capability` and `extension-or-consolidation`; their evidence resolves. | Paired pilot evidence is incomplete. |
| TCP-005 | Pilot decisions are candidate-only/reject/revise/suspend/retire; `registered` and `deployed` are prohibited in this candidate package. | Documentation silently promotes a tool. |

A pass proves only structural completeness of this evidence package. It does not prove tool quality, execution confinement, independence, approval, risk acceptance, registry registration, deployment, or capability.
