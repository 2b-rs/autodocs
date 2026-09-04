# Architect scope review — noncanonical terminal coordination-claim lifecycle

**Verdict:** `supports-selected-scope; decision-record-required`

**Reviewer:**
`agent:data:0037-cutover-decisions-scope-review:1788510735023-4e984d7d`,
privileged Management-instantiated Architect, distinct from the claim authors,
R6 implementer, and independent Integrator.

**Authority:** atomic award `1788510735023-4e984d7d` and resolved Management
decision `decision-1788508678045-f8f7c94e`, selected option
`separate_claim_lifecycle` at `2026-09-04T08:31:21Z`.

**Decision-record dependency:** the structured request and resolution are not
the conforming additive `decision-record@v1` required by the cross-item gate.
A separately authorized recorder must allocate an unused ID against current
`main`, record the selected semantics below, and integrate that record with
this review before implementation. This three-path award does not allocate or
author that record.

This review is a pre-mutation scope and authority check. It is not Task
Acceptance, an integration review or verdict, assignment acceptance, cleanup
authority, or permission to merge `8081c9a5099faed07d46dcee6174862af41ab3ba`.

## Evidence and cross-item reach

- `docs/pipeline/terminal-claim-lifecycle.md` requires noncanonical chain,
  review, award, and coordination claims to carry explicit lease state, while
  exact Task Acceptance and accepted claim finalization remain separate.
- Rejected R6 candidate `8081c9a5099faed07d46dcee6174862af41ab3ba`
  wrote `lease_active: false` plus `state: terminal` to nine claims.
  `legacy_task_doctor.py` interprets `state` as a Task marker and rejects
  `terminal`; `frontier_query.py` textually treats `state: terminal` as lease
  release and ignores `lease_active`. Integrating R6 unchanged would therefore
  give two gate consumers conflicting meanings.
- The selected model reserves `state: [x]/[w]/...` for authoritative Task
  markers and assigns `claim_state: terminal` to the noncanonical coordination
  lifecycle. Because frontier eligibility and legacy validation can start,
  block, or release other work units, `cross-item-blast-radius` applies.

## Exact affected work units and gates

Affected work units are `repository:autodocs`, the nine noncanonical Jean-Luc
coordination/integration claim paths named by cancelled assignment
`1788508448831-d06899cd`, `path:docs/pipeline/terminal-claim-lifecycle.md`,
`path:_src/tools/legacy_task_doctor.py`,
`path:_src/tools/frontier_query.py`,
`path:_src/tools/test_frontier_query.py`, and
`path:_src/tests/test_legacy_task_doctor.py`.

`path:TODO-jean-luc-0037-51-20260824T072000Z.md` is an explicitly excluded
adjacent exact Task claim and is named here only so its unchanged semantics are
mechanically tested.

Affected gates are `validation:_src/tools/legacy_task_doctor.py`,
`validation:_src/tools/frontier_query.py`, repository-wide `task-start:*`
frontier decisions, the integration gates for successor claims consuming the
nine released coordination records, and the corresponding Feature-closure
gates. No Task marker or Acceptance gate is redefined.

## Smallest safe schema and behavior

For a claim already classified as noncanonical coordination provenance, the
machine terminal tuple is exactly:

```text
lease_active: false
claim_state: terminal
```

`claim_state` has a coordination-claim namespace separate from Task `state`.
It does not accept `[x]`, `[w]`, `accepted`, or free text as synonyms.
`lease_active` is a boolean and does not become false by age, branch reach,
assignment state, status prose, or missing worktree. Both fields must be
present and consistent for a terminal coordination lease. Partial, duplicate,
contradictory, malformed, or unclassified tuples fail closed.

The implementation must use one shared parser/classifier contract in both
consumers, or prove byte-equivalent behavior from one exhaustive fixture set.
Classification as noncanonical must be structural and explicit; filename,
title, actor, age, role prose, `integration` substring, or current nine-path
allowlisting is insufficient. An exact Task claim cannot opt out of Task
semantics merely by adding `claim_state`; that combination is invalid and
remains blocking until an authorized reconciliation.

## Binding conditions

1. **Orthogonal fields.** `state` remains limited to the existing authoritative
   Task marker grammar. `claim_state` is parsed separately and never enters
   `VALID_MARKERS`, Task completion, Acceptance, prerequisite, or Feature
   closure calculations.
2. **Conjunctive release.** Frontier suppression occurs only for an explicitly
   classified noncanonical coordination claim carrying both
   `claim_state: terminal` and `lease_active: false`. Either field alone,
   `lease_active: true`, or conflicting duplicates remains active or
   indeterminate; it never silently releases work.
3. **Explicit classification.** The conforming decision record and
   implementation must define one stable noncanonical claim discriminator.
   If existing fields cannot classify the nine records without heuristic
   inference, an explicit typed discriminator must be separately recorded
   before use; the implementer may not invent one ad hoc.
4. **Exact Task boundary.** The accepted exact Task claim
   `TODO-jean-luc-0037-51-20260824T072000Z.md` is unchanged. Exact Task claims
   retain their marker, Task-bookkeeping, Acceptance, and `TODO-*`/`DONE-*`
   lifecycle; coordination terminalization supplies no completion credit.
5. **Nine-path rework.** R6 is not integrated unchanged. A fresh candidate may
   replace `state: terminal` only in the nine named noncanonical records after
   the shared semantics are implemented and tested. Unrelated claims do not
   migrate in this transaction.
6. **No cleanup inference.** Released coordination leases cease to block the
   ready frontier, but worktree removal still requires the independent
   cleanliness, live-CWD, branch/ref preservation, Acceptance, and
   reachability rules. No branch, tag, reflog, object, or claim is deleted.
7. **Target-policy provenance.** Independent review validates the fresh
   candidate with the target versions and digests of both consumers. A stale
   branch-local doctor or frontier result supplies no gate credit.
8. **Activation and separation.** A conforming additive decision record and
   this review must be main-reachable before tool or claim mutation. The later
   implementer and Integrator remain distinct from this Architect; Acceptance
   and Feature closure retain their existing authorities.

## Required falsification and verification

The two consumer suites must share or mirror fixtures proving:

- a noncanonical claim with the exact terminal tuple leaves the frontier and
  produces no invalid Task-marker finding;
- each partial tuple, `lease_active: true`, duplicate/conflicting keys,
  unknown `claim_state`, malformed boolean, and unclassified claim fails
  closed in both consumers;
- `state: terminal`, `status: accepted`, status prose, age, missing worktree,
  main ancestry, and mailbox assignment acceptance do not substitute for the
  tuple;
- an exact Task claim carrying `claim_state: terminal` is rejected and remains
  governed by its Task marker and Acceptance state;
- exact Task `[ ]`, `[p]`, `[x]`, and `[w]` behavior is unchanged, including
  the excluded `0037-51` claim; no terminal coordination tuple creates Task
  completion, prerequisite satisfaction, Acceptance, or Feature closure;
- all nine selected records are released together in the fresh candidate,
  while an omitted, extra, or unrelated changed claim fails exact-scope
  validation;
- deterministic repeated runs produce identical findings/frontier output, and
  target-policy provenance identifies both exact tool blobs.

At least one property or exhaustive table must cover every combination of
claim classification, `lease_active`, `claim_state`, and Task `state`, proving
that no invalid combination is interpreted as both inactive and valid.

## Explicit exclusions

Excluded are extending the Task marker grammar with `terminal`; treating
`claim_state` as Task completion or Acceptance; generic textual terminal
heuristics; changing marker, prerequisite, checkpoint, Acceptance, or Feature
closure semantics; editing the exact `0037-51` Task claim; bulk claim
migration; automatic claim rename/deletion; worktree/ref deletion; accepting
R6 retroactively; push, publication, or `main` advance.

## Conclusion

The selected separate lifecycle is supportable only under conditions 1–8.
The main unresolved implementation prerequisite is a stable structural
noncanonical discriminator: it must be present in the conforming decision
record or returned to Management if the existing schema cannot express it
without heuristics. Until that record and this review are main-reachable,
`8081c9a509` stays rejected and no consumer or claim mutation is authorized.
