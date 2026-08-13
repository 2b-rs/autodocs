# Confidence Scoring and Invalidation (0006-19)

Status: implemented 2026-08-13 in `_src/tools/confidence.py`, refined
through discussion with the user on the same date.

## Terminology note (important)

This introduces a **new** "feedback" concept: a positive/negative reaction
to an AI-generated fragment, distinct from the existing **"Ingest
Feedback"** action documented in `docs/pipeline/actions.md`, which names
the `curation_ingest.py` tool (curation-decision ingest into the
curation-flag queue). Do not conflate the two: "Ingest Feedback" = accept/
reject a curation decision; "feedback" (this doc) = signed reaction to a
knowledge fragment that nudges its confidence score.

## Formula

```
score = clamp01(base(origin, item_kind) + confirms_bonus + feedback_sum)
```
overridden to a fixed floor of 0.05 if the node is dismissed (never to
exactly 0 -- nothing is ever fully discarded, per the project's
never-delete-only-mark pattern).

### Base score by provenance (origin, item_kind from 0006-03)

| origin | item_kind | base |
|---|---|---|
| curator | record | 0.90 |
| tool / browser | scrape-observation | 0.70 |
| ai | ai-amendment | 0.55 |
| ai | ai-hypothesis | 0.35 |

### Adjustments

- **Confirms bonus**: `+0.25` if a `confirms` edge (0006-18) targets this node.
- **Feedback** (user-defined 2026-08-13): each feedback item has a
  `valence` (`positive`/`negative`) and `strength` in `[0, 1]`,
  contributing `sign(valence) * strength * 0.15` -- i.e. **up to +/-0.15
  per feedback item**, matching the user's explicit instruction that
  feedback "is ultimately able to increase/decrease the confidence value
  by up to 0.15 in either direction." Multiple feedback items sum.
- **Dismissal floor**: fixed `0.05`, overriding the additive formula
  entirely once `dependency_graph.is_dismissed(node_id)` is true.

## Dismissal vs. other causes -- revisit-eligibility rule (user-defined 2026-08-13)

Every confidence recompute is recorded via `record_confidence(..., cause=...)`
with one of: `feedback`, `confirmation`, `dismissal`, `cascade_invalidation`.

- **`cause == "dismissal"`**: does **not** enqueue a revisit task. Rationale
  (user, 2026-08-13): "If a curator dismisses an item, AI will no longer
  be able to 'answer' to that decision" -- this matches 0006-18's
  `can_derive_from()` already returning `False` for a dismissed node, and
  extends the same idea to revisiting: the AI must not treat its own
  dismissed output as something to resynthesize.
- **Any other cause** (`feedback`, `confirmation`, `cascade_invalidation`):
  **does** enqueue a revisit task. Rationale (user, 2026-08-13): "if the
  confidence of an item changes for other reasons, AI may ingest that
  knowledge and revisit its own knowledge."

This is a genuinely different signal from `can_derive_from()`: dismissal
blocks deriving NEW work off a dismissed decision node (0006-18), while
the revisit queue here governs whether the AI should re-examine and
possibly resynthesize its OWN prior artifact given a confidence change.

## Invalidation state

`mark_invalidated()`/`is_invalidated()` add a flag orthogonal to the
curation-item lifecycle (0006-06's discovered -> ... -> superseded
states), set by `cascade_invalidate()` walking `dependency_graph
.find_dependents()` (0006-18). Invalidated nodes remain fully retrievable
-- never deleted, only marked, consistent with the version store (0006-16)
and dependency graph (0006-18).

## Storage

Append-only JSON-Lines under `_src/spec/graph/`: `feedback.jsonl`,
`confidence_history.jsonl`, `pending_revisits.jsonl`, `invalidated.jsonl`.

## Non-goals of this task

Does not implement the supersession-trigger job that actually calls
`cascade_invalidate()` on real pipeline events (**0006-20**), nor the
per-claim structure that will carry `confidence_history[]` on individual
synthesized claims (**0006-21**).
