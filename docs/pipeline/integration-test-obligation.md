# Integration-Test Obligation at Mandatory Checkpoints

**Status:** binding process instruction for integration checkpoints, staged
activation (see section 2). Authored by Task `0044-03` (*architect-elaboration*,
requirement `RQ-IP-07`). Decided by
[`DEC-0044-019`](../dossiers/dec-branching-merging-strategie.md) — *Executable
evidence at mandatory integration checkpoints* — under the independent
pre-mutation Architect scope review
[`0044-03-gate-scope-review.md`](../dossiers/0044-03-gate-scope-review.md)
(verdict `scope-ok-mit-auflagen`). Where this document and the decision record
could ever be read differently, the decision record governs.

## 1. Purpose and boundary

This instruction answers the question the customer intake recorded as
"Integrationstests?": **what must an integrator actually execute — not only
read — at a node marked `Integration review: mandatory`, how is that test
obligation derived from the architecture and interface contracts of the
integrated items, what evidence must the run leave, and what happens when no
automated test exists.**

It **adds a review obligation** to the existing integration-checkpoint
procedure. It does not create a new gate type, a new acceptance authority, or
a new marker. The checkpoint semantics it plugs into are unchanged:

- **Which nodes are checkpoints** is the architect's declared, attribute-driven
  decision, per the `TODO.md` header and
  [`task-acceptance.md`](./task-acceptance.md) → *Integration checkpoints and
  the architect*. This instruction never sets, clears, or moves the attribute.
- **When the review happens and who performs it** follows
  [`branch-workflow.md`](./branch-workflow.md) → *Feature integration and
  sign-off* and *Merge authority and direction*: the privileged integrator
  reviews each flagged node as its boundary is crossed.
- **What the review decides and records** follows
  [`task-acceptance.md`](./task-acceptance.md) → *Privileged review procedure*.
  This instruction specifies the **execution content** of that procedure's step
  4 ("Evaluate and rerun validation") at integration checkpoints.
- **A checkpoint review judges the node it stands at.** Per the Klarstellung of
  2026-08-22 in `task-acceptance.md`, transitive acceptance closure is a
  Feature-closure concern, not an entry gate for the node's checkpoint review.
  This instruction follows that boundary: the obligation below is about
  executing verification against the integrated candidate, not about
  re-reviewing ancestors.

## 2. Activation state (staged, per `DEC-0044-019`)

1. **Bound now:** all Feature-`0044` trial checkpoints. Inventory at decision
   time and re-pinned unchanged at implementation time (2026-08-23):
   `0044-01`, `0044-04`, `0044-05`, `0044-12`, `0044-13`, `0044-14`,
   `0044-15`, `0044-16`, and integrating Task `0044-08`. Historical, already
   accepted reviews (`0044-14`, `0044-15`) are not retroactively invalidated;
   any new execution or re-review at those nodes follows this rule.
2. **Qualification example:** Task `0043-07` is the real pending integration on
   which the derivation is demonstrated. The retained derivation is in
   [`docs/campaign-evidence/0044-03-worked-example/integration-0043-07-derivation.md`](../campaign-evidence/0044-03-worked-example/integration-0043-07-derivation.md);
   its **execution** happens at the `0043-07` checkpoint itself and its record
   must meet the evidence minimum of section 5.
3. **Dormant until confirmed:** the repository-wide obligation for future
   `integration:*` and `feature-closure:*` gates activates **only** when
   `0043-07` has actually been executed and recorded and `0044-08` has
   confirmed that record against this instruction's minimum. If that
   confirmation cannot be made, broad activation does not occur and `0044-08`
   takes the fail/`[u]` path or obtains an additive scope decision.

Widening, narrowing, or removing this obligation is itself a qualifying gate
scope mutation under the `AGENTS.md` *Cross-item gate-scope review exception*
and requires a new decision record and independent Architect scope review.

## 3. What the integrator executes

At a mandatory checkpoint the integrator **executes a checkpoint-specific
verification set against the exact integrated candidate** — the tree that
results from the merge being reviewed, not the implementer's branch before the
merge. A green branch-local run is **insufficient** whenever the candidate tree
differs from the tree that produced it: the trigger defect of Feature `0043`
("every part worked, the chain did not") and the composition rationale of
`0044-08` are precisely the failures branch-local evidence cannot see.

Reading implementation evidence, claims, or prior logs remains required by
`task-acceptance.md` but never substitutes for execution. Prior immutable runs
may **support** the review; reuse without re-execution is permitted only under
the narrow conditions `task-acceptance.md` §4 already states (exact
input/environment/tool match, canary coverage, recorded justification) — and
even then at least the derivation matrix of section 4 must be produced and
each row dispositioned.

## 4. Deriving the test set from the architecture

The test obligation is **derived, not fixed**: the architecture determines what
can fail at the integration seam, so a universal suite would be simultaneously
excessive and incomplete (`DEC-0044-019`, technical justification). The
integrator builds a **derivation matrix** over the five closed categories
below, drawing on the derivation sources the feature-breakdown process
instruction (Task `0044-04`, pending at the time of writing; until it lands,
the Task contracts in `TODO.md` are the source) requires each task to record —
requirements, decision records, declared interfaces, and repository evidence:

| # | Derivation category | What to look at for the integrated items | Typical test kind |
|---|---|---|---|
| 1 | **Architecture risks and changed integration seams** | The architect's checkpoint rationale on the node; the Feature goal; which components newly touch each other in the candidate | End-to-end or composition test across the changed seam, on the candidate tree |
| 2 | **Interfaces, schemas, protocols, compatibility contracts** | Declared interface/schema documents of the integrated items (e.g. `docs/pipeline/*-schema.md`, tool contracts, environment-variable contracts, file formats) | Contract/schema validation, consumer-producer round-trip, backward-compatibility check |
| 3 | **Invariants and data/state transitions** | Stated invariants (append-only, idempotence, determinism, byte-identity, fail-closed behavior) of the integrated items | Invariant assertion against real state, before/after comparison across the merge base |
| 4 | **Negative, failure, recovery, and rollback modes** | The failure modes the items' tests and acceptance criteria name; the recovery/rollback boundaries of the Task contracts | Negative fixtures, fault injection, refusal cases, recovery replay |
| 5 | **External effects** | Anything leaving the isolated worktree: publication, network, credentials, host services, irreversible migration | Safe fixture or dry run; a bounded manual procedure where real execution is unsafe; never the real external effect as a "test" |

Rules for the matrix:

- **Every applicable row names an executable test kind and its oracle** (the
  observable expected result that would falsify the integration).
- **A row may be non-applicable only with a concrete reason** tied to the
  integrated items ("no external effect: all writes are inside the worktree"),
  never with a bare "n/a". An unexaminable row is a gap, not a non-applicable
  row.
- **Proportionality:** the matrix does not require every test kind at every
  checkpoint; it requires an explicit decision per category.
- The matrix and its dispositions are part of the review evidence and are
  retained with it.

## 5. Evidence the run must leave

The retained evidence must let an independent reviewer **reproduce or falsify**
the result. Minimum content (per `DEC-0044-019`):

1. checkpoint identity and the integration boundary being crossed;
2. exact candidate and target refs/trees (commit hashes; for merges, both
   parents and the resulting tree);
3. inputs and fixtures used;
4. material environment and tool identities (versions where they matter);
5. the command executed, or the typed manual procedure followed;
6. expected oracle and actual result, with exit status;
7. digest-bound logs/artifacts (SHA-256 of anything the verdict rests on that
   is not itself committed);
8. exclusions, known gaps, and residual risk, stated honestly;
9. replay instructions.

Evidence is committed with the review findings on the integration branch, as
`branch-workflow.md` → *Feature integration and sign-off* already requires for
review records. Git-ignored raw output may be referenced by digest but the
verdict-bearing summary must be tracked.

## 6. When no automated test exists

Missing automation is **never a silent pass**:

1. If a **reproducible, falsifiable manual procedure** can establish the
   criterion, the integrator may execute it as bounded evidence. The procedure
   is typed into the evidence step by step, its oracle is stated in advance,
   and its limits and the automation gap are recorded. A manual fallback is an
   evidence method, not a waiver, and it must not claim stronger assurance
   than it provides.
2. If **neither automated nor manual** evidence can safely or credibly
   establish the criterion, the result is not "not applicable" and not a pass:
   **the checkpoint fails**, and the integrator records the existing `[u]`
   integration verdict per `branch-workflow.md` → *Integration rejection: the
   `[u]` verdict*, handing the decision to the user. An unavailable
   environment, unsafe external effect, missing oracle, or irreproducible
   manual step is recorded as a gap and escalated the same way.

## 7. Separation from acceptance authority

No test exit status grants `Acceptance: ✓`, supplies a missing specialist
decision, waives a criterion, or permits crossing the checkpoint by itself.
The execution obligation produces **evidence**; the checkpoint outcome remains
the separate review decision that `task-acceptance.md` defines, made by the
separately required authority. Integrator, implementer, and architect role
separation (`process-roles.md`) is unchanged, as are capability-class rules:
performing this execution never upgrades a session's class or independence.

## 8. Worked example

The rule applied to the real pending integration `0043-07` (Feature `0043`
integrating task, `Integration review: mandatory`):
[`docs/campaign-evidence/0044-03-worked-example/integration-0043-07-derivation.md`](../campaign-evidence/0044-03-worked-example/integration-0043-07-derivation.md).
It demonstrates the derivation matrix, oracles, evidence plan, and the
no-automation dispositions for that checkpoint. Per section 2 it is the
activation qualification: `0043-07`'s integrator executes it (adjusted to the
then-current candidate), and `0044-08` confirms the record.
