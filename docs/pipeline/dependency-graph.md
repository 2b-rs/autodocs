# Evidence/Dependency Graph (0006-18)

Status: implemented 2026-08-13 in `_src/tools/dependency_graph.py`.

## Node kinds

`requirement-version` (0006-15/0006-16), `curation-decision`,
`evidence-snippet`, `artifact` (AI synthesis/amendment/hypothesis, per
0006-03's `item_kind` values), `human-comment`.

## Edge kinds

`derived_from`, `quotes`, `supersedes`, `revisits`, `comments_on`,
`dismisses`, `confirms`.

Artifact -> artifact edges are explicitly supported (and may cycle: AI can
resynthesize its own prior text together with newly changed facts or
comments). `find_dependents()` is cycle-safe (visited-set, fixed-point
termination), not a fixed hop count.

## Dismissal semantics -- Option B (decided 2026-08-13, user-confirmed)

**Dismissing a node halts future propagation only; it never severs
existing edges.**

- `can_derive_from(node_id)` returns `False` once a node is dismissed --
  this is meant to gate NEW edge creation (don't let new artifacts derive
  from a dismissed node going forward).
- `find_dependents()` traverses ALL existing edges regardless of
  dismissal. A dismissed node's downstream dependents remain fully
  discoverable.
- Audit is served by the node-level `dismissed_at`/`reason` record in
  `dismissed.jsonl`, not by cutting graph edges.

Rationale (discussed and agreed 2026-08-13): severing edges on dismissal
would force 0006-19/0006-20's invalidation-cascade traversal to special-
case "severed-but-still-followed-for-invalidation" edges, undermining the
point of severing. Halt-only keeps the traversal a single, simple
fixed-point walk over intact edges, and matches this project's blanket
"never delete, only mark" pattern already used for queues, the version
store, and the curation-item lifecycle.

## Storage

Append-only JSON-Lines under `_src/spec/graph/`: `edges.jsonl` (one edge
per line, idempotent adds) and `dismissed.jsonl` (one dismissal record per
line). Matches the never-rewrite pattern from `version_store.py`.

## Non-goals of this task

Does not implement invalidation state / confidence history (**0006-19**,
blocked on a separate manager decision: the confidence-scoring formula)
or the supersession-trigger job (**0006-20**). Does not yet wire
`add_edge()` calls into `review_flags.py`/`curation_flags.py`/`spec_scrape.py`
write paths -- callers must invoke it explicitly for now.
