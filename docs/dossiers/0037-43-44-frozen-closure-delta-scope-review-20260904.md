# Architect scope review — 0037-43/44 frozen closure delta

**Verdict:** `supports-with-binding-conditions`

**Reviewer:**
`agent:data:0037-cutover-decisions-scope-review:1788510735023-4e984d7d`,
privileged Management-instantiated Architect, distinct from the prior product
implementers, reconciliation authors, and Integrators.

**Authority:** atomic award `1788510735023-4e984d7d` and resolved Management
decision `decision-1788485334668-c71f3fc5`, selected option
`authorize_scoped_closure_delta` at `2026-09-04T08:31:21Z`.

**Decision record dependency:** `DEC-0037-031`, separately allocated against
`main@7a433be950c6e35370e297dffb1a7af861af1f8b` at
`docs/dossiers/dec-0037-031-scoped-closure-delta.md`. This review supports only
a conforming record whose effective content preserves every condition below.
Initial signed candidate `91f105cdd21f2bb3ef5cc62ceb260cd6c0f3c8e9`
required bounded reach correction. Signed successor
`a9e6aa0e7a971e761bf3ba0bfcbd00f7af61ce89` supplies it and is the exact
decision candidate supported by this review.

This is the supporting pre-mutation review required by the cross-item
gate-scope exception. It is not implementation, Task Acceptance, an
integration review or verdict, a closure record, or permission to advance
`main`.

## Evidence and cross-item reach

- `agent-workflow.json` selects `authority_epoch: legacy-frozen` and
  `write_phase: frozen`. `_src/tools/issue_integration_policy.py` therefore
  rejects `TODO.md` and ordinary root `TODO-*` mutations.
- Candidate `6a140653b8c18b1282d5bf93081020345086ec6b` attempted to record
  the already integrated `0037-43` completion in those forbidden paths.
  Independent verdict `adbe68e6974a2abb7699b72bb9d20ea1a34c49dd`
  correctly rejected it. It remains evidence, not a reusable candidate.
- Management recorded that the substantive products and integration receipts
  for both `0037-43` and `0037-44` are already main-reachable while their
  legacy Task markers remain open. The selected remedy deliberately changes
  the active freeze partition instead of restoring and refreezing legacy
  authority.
- The delta can unblock Task completion/Acceptance and the cutover chain, and
  changes the validation contract applied to other work units. The
  `cross-item-blast-radius` predicate therefore applies.

## Exact affected work units and gates

Affected work units are `repository:autodocs`, `feature:0037`,
`task:0037-43`, `task:0037-44`, `task:0037-30`, `task:0037-31`,
`subtask:0037-34.01`, `task:0037-32`, `task:0037-33`, and `task:0037-40`.

Affected gates are `validation:_src/tools/issue_integration_policy.py`,
`validation:_src/tools/agent_bootstrap.py`, `integration:0037-43`,
`integration:0037-44`, `task-start:0037-31`, `task-start:0037-32`,
`task-start:0037-33`, `task-start:0037-34.01`, `task-start:0037-40`, and
`feature-closure:0037`.

The scope also intersects the final-watermark, exactly-one-writable-authority,
no-shadow-write, immutable-candidate, closure-delta, and protected-integration
controls in `docs/pipeline/issue-cutover-rollback.md`, `agent-workflow.json`,
and the `0037-43` gate.

## Decision-record comparison

Candidate `91f105cdd` was structurally complete and preserved the selected
Management option, rejected alternative, frozen prohibitions, and rejected
candidate history. Its `Affected work units` and `Affected gates` blocks are
semantically incomplete for the actual declared behavior. Same-slot rework
`a9e6aa0e7` now:

- add `repository:autodocs` and `feature:0037`;
- replace `task:0037-34.01` with `subtask:0037-34.01`;
- add `validation:_src/tools/agent_bootstrap.py` and
  `task-start:0037-32`, `task-start:0037-33`,
  `task-start:0037-34.01`, and `task-start:0037-40`; and
- bind the operative transaction to the exact assignment/path/blob/receipt
  manifest, atomic compare-and-swap and idempotence, downstream post-delta
  digest revalidation, and the unchanged Acceptance/broader-write exclusions.

The reworked record also adds the exact assignment/path/blob/receipt manifest,
atomic compare-and-swap and idempotence, downstream post-delta digest
revalidation, and unchanged Acceptance/broader-write exclusions. Its SSH
signature verified. The cross-item pre-mutation condition becomes satisfied
only after `a9e6aa0e7` and this review are both main-reachable; neither private
branch supplies operative authority.

## Smallest safe scope

The permitted behavior is one assignment-bound, compare-and-swap closure
transaction for exactly Tasks `0037-43` and `0037-44`. It may update only:

1. the two exact Task records inside `TODO.md`;
2. the exact already-existing implementation claims canonically bound to
   those two Tasks; and
3. append-only transaction evidence needed to bind and validate that exact
   set.

The transaction manifest must pin the authority epoch, selector digest,
current `main` base, original freeze/source watermark, every before/after blob,
the exact product and integration receipt for each Task, assignment identity,
policy/tool digests, and one idempotence key. A changed base, path set, blob,
receipt, epoch, selector, or repeated key with different content fails before
write. Partial visibility or partial promotion fails closed and leaves the
authoritative tree unchanged.

The resulting evidence must describe the original frozen source plus this
named closure delta; it must not relabel the original watermark or claim that
the post-delta tree was the original quiescence observation. Every later
candidate, audit, approval, or activation input that consumes Task state or
source digests must bind the post-delta aggregate or be regenerated. Prior
evidence remains immutable history and receives no current gate credit when
its inputs differ.

## Binding conditions

1. **Exact two-Task set.** No pattern, Feature-wide exception, generic
   `TODO-*` allowance, or discretionary operator path is permitted. Missing,
   duplicate, ambiguous, foreign-owned, or extra claims reject the whole
   transaction.
2. **Evidence-only completion.** The delta may record only completion already
   proven by main-ancestral substantive products and canonical integration
   receipts. It may not change product bytes, acceptance criteria,
   prerequisites, checkpoint classification, or substantive Task text.
3. **No Acceptance inference.** `[x]` and terminal claim state record
   implementation completion only. `Acceptance: ✓`, accepted-claim rename,
   checkpoint crossing, and Feature closure remain separate authorized acts.
4. **Freeze preserved elsewhere.** All other legacy backlog, claim, issue-item,
   generated-view, and ordinary pickup writes remain rejected. The issue store
   does not become writable and no second backlog authority is created.
5. **Target-policy enforcement.** The protected integration check and local
   validator must recognize the same exact transaction proof. A branch-local
   bypass, stale client, direct push, administrator role, omitted check, or
   unproved transaction remains rejected.
6. **Order and invalidation.** The conforming `DEC-0037-031` and this review
   must both be main-reachable before implementation. Integration of the delta
   precedes any downstream gate credit, and every dependent artifact is
   revalidated against its exact aggregate digest.
7. **Separation.** The implementer, independent reviewer/Integrator, Task
   Acceptance reviewer, and this Architect retain their ordinary distinct
   authorities. This review grants none of those roles.
8. **Recovery.** Before promotion, abandoning the candidate is sufficient.
   After source integration, recovery uses an explicitly authorized additive
   compensating transaction; it never deletes the decision, review, original
   freeze evidence, receipts, branch, or preserved candidate.

## Required falsification and verification

Implementation and independent review must retain red/green fixtures proving:

- the exact `0037-43` and `0037-44` closure transaction passes only with both
  main-ancestral product/receipt pairs and exact before/after blobs;
- either Task alone, a third Task, an extra/missing claim, altered Task prose,
  an Acceptance insertion, a prerequisite/checkpoint edit, and a product
  change each fail atomically;
- an ordinary `TODO.md`, `DONE.md`, root claim, issue item, or generated-view
  mutation remains rejected with the existing stable diagnostics;
- stale epoch, selector, base, watermark, digest, assignment, transaction ID,
  and policy/tool version each fail before mutation;
- interruption at every commit point produces no partial authoritative state,
  and exact replay is idempotent while changed replay fails;
- downstream `0037-31`, `0037-34.01`, `0037-32`, `0037-33`, and `0037-40`
  evidence cannot receive gate credit when still bound to a pre-delta digest;
- direct push, skipped check, force push, deletion, and privileged/admin bypass
  attempts remain non-landable under the protected gate.

## Explicit exclusions

Excluded are rollback/refreeze authority; any write for a Task other than
`0037-43` and `0037-44`; a generic frozen-state repair mechanism; issue-store
activation; generated-view editing; product or requirement mutation; new
Acceptance; reopening or closing another Task; changing the authority selector
outside the exact transaction proof; weakening branch protection; push,
publication, ref deletion, or Feature closure.

## Conclusion

The selected option is supportable only with conditions 1–8 and the complete
negative matrix above. No qualifying mutation may begin until the conforming
`DEC-0037-031` and this exact review are current on the implementation target.
Any broader path set, weaker proof, or reuse of pre-delta gate evidence requires
a new Management decision and distinct Architect review.
