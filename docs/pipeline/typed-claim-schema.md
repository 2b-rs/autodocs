# Typed-Claim Schema (Feature 0006-21)

Status: implemented 2026-08-13. Module: `_src/tools/typed_claim.py`.
Schema id: `typed-claim@v1`.

## Purpose

A synthesized description must not be a single opaque blob. Each atomic
claim/section in an AI-produced artifact must stay inspectable and
re-runnable with explicit claim type, evidence/dependency refs, confidence,
invalidation, and supersession history.

## Required fields

| Field | Type | Meaning |
|---|---|---|
| `schema` | string | Always `typed-claim@v1`. |
| `claim_id` | string | Stable claim id. Minted with `version_id.hypothesis_id()` (0006-15). |
| `parent_artifact_id` | string | The synthesis/artifact this claim belongs to. |
| `claim_type` | enum | One of `hard_fact`, `curated_fact`, `user_comment`, `ai_inferred`. |
| `content` | string | Human-readable claim text. |
| `evidence_refs` | list[string] | Direct evidence/version/curation ids the claim cites. |
| `dependency_refs` | list[string] | Broader graph dependencies used during synthesis. |
| `current_confidence` | float | Current score in `[0,1]`. |
| `confidence_history` | list[object] | Append-only entries `{score, cause, inputs, computed_at}`. |
| `invalidation` | object | `{invalidated, reason, invalidated_at}`. Orthogonal to confidence history. |
| `dismissed_from_future_synthesis` | bool | Curator chose not to propagate this claim into future syntheses, while preserving audit history. |
| `supersedes_claim_ids` | list[string] | Earlier claims this claim revisits/replaces. |
| `superseded_by_claim_ids` | list[string] | Later claims known to supersede this one. |
| `created` / `updated` | ISO 8601 strings | Audit timestamps. |

## Worked examples

### Hard fact

```json
{
  "schema": "typed-claim@v1",
  "claim_id": "hypothesis:0198...",
  "parent_artifact_id": "artifact:release-note-1",
  "claim_type": "hard_fact",
  "content": "The namespace contains 15 API elements.",
  "evidence_refs": ["AUTOSAR/AP/record/XYZ@rel:R25-11#deadbeef"],
  "dependency_refs": [],
  "current_confidence": 1.0,
  "confidence_history": [],
  "invalidation": {"invalidated": false, "reason": null, "invalidated_at": null},
  "dismissed_from_future_synthesis": false,
  "supersedes_claim_ids": [],
  "superseded_by_claim_ids": [],
  "created": "2026-08-13T12:00:00+00:00",
  "updated": "2026-08-13T12:00:00+00:00"
}
```

### AI revisiting prior text

A later AI synthesis can supersede an older AI-inferred claim without losing
the original text or confidence trail: create a new `typed-claim@v1` with
`claim_type = ai_inferred`, keep the old claim intact, put the old
`claim_id` into the new claim's `supersedes_claim_ids`, and add the new
`claim_id` to the old claim's `superseded_by_claim_ids`.

### Curator dismissal

Dismissal is represented by setting `dismissed_from_future_synthesis = true`
ON THE CLAIM while keeping the claim, evidence refs, and confidence history
intact. This matches the broader 0006-18/19 rule that dismissal halts future
propagation, not audit history.

## Provided helpers

- `new_claim(...)`
- `validate_claim(claim)`
- `append_confidence(claim, score, cause, inputs=None)`
- `mark_invalidated(claim, reason)`
- `dismiss_from_future_synthesis(claim)`
- `link_supersession(old_claim, new_claim)`

## Non-goals of this task

Does not create persistent storage or wire claims into HTML/rendering. Does
not update the broader data-model docs yet -- that is 0006-22's job.
