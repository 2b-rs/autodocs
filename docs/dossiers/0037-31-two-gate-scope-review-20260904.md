# Architect scope review — Task `0037-31` narrow two-gate repair

**Verdict:** `supports-with-binding-conditions`

**Reviewer:**
`agent:data:0037-31-two-gate-architect-review:1788520101148-0c061647`,
privileged Management-instantiated Architect, distinct from Implementer Lore
and the reserved Integrator.

**Authority:** atomic award `1788520101148-0c061647`; resolved Management
decision `decision-1788519617751-91941e27`, selected option
`instantiate_narrow_review`; conforming decision record `DEC-0037-033` in this
two-file candidate.

**Pinned baseline:** `main@7dbc94db262979b41bc225d6571d610123a47814`.
The reviewed tool blobs are `issue_import_legacy.py@e7aeb505ee44b96182f64c54b0316dcf1be77302`
and `issue_integration_policy.py@9676a0f56c6a03d25408a8bbb93a4a0cc7e9d8a3`.
The signed blocker is
`34ede49b3c44f878c0fd3bcbae269d11a72c64f2`; its three evidence blobs are
`7268ad4e3b5c87da0825d81cdcfb5c25832c6bd2`,
`028d94b77bd430dbd3610cc5e047de344e43bb4e`, and
`c844d20bcc0fbe809de4599def2c247492ad234b`.

This is a pre-mutation cross-item gate-scope review. It is not implementation,
Task Acceptance, integration review, migration success, selector activation,
publication, or permission to move any marker or ref.

## Finding and actual gate reach

The blocker proves two independent red gates:

1. `run_migration()` accepts only the exact canonical in-repository history
   root, creates a hidden staging directory below it, and then calls the public
   import path on `staging/issues`. `resolve_disposable_root()` rejects that
   descendant solely because `_src/output` is in its live-root set. Thus the
   production orchestrator requires and prohibits the same destination.
2. Frozen integration permits `0037-31` dossier and provenance path classes
   only when `frozen_authority_proof()` locates a matching top-level
   `TODO-*` owner token. Award `1788519031177-793919ee` is explicitly claimless
   and the frozen selector forbids creation of that proof file. Thus the
   protected gate requires and prohibits the same ownership representation.

These gates control whether Task `0037-31` can produce a candidate, whether
its evidence can integrate, whether `0037-32` may start, and whether Feature
`0037` can close. The cross-item predicate applies. The actual repair scope is
the two tools, their synchronized tests, Lore's fresh run output, and the three
exact evidence files; no ordinary source, issue item, backlog, claim, selector,
Acceptance, ref, or publication path is affected.

## Supported interfaces

### Gate A — contextual importer staging capability

The exception is an internal capability derived by `run_migration()`, not a
new generally writable root. Before it exists, the orchestrator must prove all
of the following:

- the history path is lexically and after resolution exactly
  `<repo>/_src/output/issue-migration`, with no symlink or alias;
- the run ID satisfies the existing grammar and does not already exist;
- the exact per-run lock was created with exclusive semantics;
- the hidden staging directory was freshly created directly below that
  history root for the same run ID; and
- the import destination is lexically and after resolution exactly the
  staging directory's `issues/` child.

The authorization is passed through a typed/contextual internal call or an
equivalent interface that cannot be enabled by an ordinary CLI boolean. It is
valid only for that call and destination. `resolve_disposable_root()` and
direct `import_legacy()` retain their current denial of the repository root,
`issues`, `provenance`, `.runner`, `output`, `_src/output`, generated views,
backlog files, the history root itself, completed run roots, reports, siblings,
ancestors, aliases, symlink escapes, traversal confusion, and every unreserved
or mismatched staging path.

### Gate B — claimless frozen assignment/transaction manifest

For this transaction the canonical authority input is
`provenance/migrations/issue-store/0037-31-final-frozen-candidate.json`. It must
carry one normalized proof object whose effective values include:

- `task_id: 0037-31`;
- `assignment_id: 1788519031177-793919ee` and the atomic-award/item identity;
- `claim_mode: claimless-frozen-transaction`;
- `authority_epoch: legacy-frozen`;
- source commit `7dbc94db262979b41bc225d6571d610123a47814` and its tree;
- closure transaction `f5a806c52a63e00edac5c0aa8bb0793227ae3af1`;
- one fresh canonical run ID/root and resulting candidate/report identities;
- the exact three evidence paths plus the exact run-output subtree allowed by
  the implementation rework award; and
- a stable reference to the atomic assignment transaction, without treating
  mailbox delivery, acknowledgement, prose status, or sender label as proof.

The dossier and Markdown companion repeat Task and assignment identity; every
other effective field is read from or digest-bound by the JSON manifest. The
policy requires exact agreement among changed path, path-class Task ID,
manifest, companions, candidate commit, source boundary, selector epoch, and
transaction. The claimless branch is selected only for this typed `0037-31`
transaction. Existing claim-bound verification remains unchanged where claims
are lawful. A claimless manifest does not create a claim, lease, Task state,
completion, Acceptance, integration, or authority-switch inference.

## Binding conditions for Lore's same-slot rework

1. **Governance first.** `DEC-0037-033` and this review must both be reachable
   from current `main` before any tool, test, output, or evidence mutation.
2. **Fresh exact award.** Rework must remain atomic assignment
   `1788519031177-793919ee` or a same-slot successor that explicitly preserves
   its task, source, transaction, claimless mode, paths, and Integrator
   reservation. Governance integration alone does not grant the rework.
3. **No path-prefix permission.** Gate A requires all contextual predicates;
   Gate B requires all manifest predicates. A string prefix, filename, branch,
   author, signature, assignment ID, or transaction ID alone never passes.
4. **CAS and invalidation.** Immediately before reservation, import, evidence
   commit, and policy evaluation, re-read the selector and exact source ref.
   Any epoch, source, tree, tool, policy, closure transaction, prior-run,
   allowed-path, or candidate-identity drift invalidates the run and requires
   a new run ID after a fresh authorization check.
5. **Atomic tool behavior.** The importer contextual exception and integration
   manifest support land together with synchronized tests. Partial deployment
   must remain red; neither consumer may interpret proof the other rejects.
6. **Immutable output.** A failed or interrupted run is retained or disposed
   only under its existing recovery contract. A successful or promoted run is
   never reopened, refreshed, or edited in place.
7. **Target-policy verification.** Independent integration runs both exact
   target versions from a clean worktree against the exact candidate and
   records tool/test blobs, selector digest, source, transaction, manifest,
   changed-path set, and command results.
8. **Separation.** Lore implements; an independently assigned Integrator
   reviews. This Architect does not implement, accept, integrate, advance
   `main`, or approve Feature closure.

## Required red, green, adjacent, and property evidence

The retained blocker is the mandatory red baseline:

- the exact importer command reports `IMP-LIVE-ROOT` with zero writes; and
- policy evaluation of its signed three-path evidence reports three
  `POLICY-FROZEN-AUTHORITY-PROOF-REQUIRED` violations.

The green candidate must use a new run ID and prove:

- the canonical orchestrator alone imports into its freshly reserved staging
  `issues/`, completes comparison/reporting, and promotes by the existing
  atomic rename only when all existing checks pass; and
- the exact three evidence paths pass frozen policy without a `TODO-*` claim
  only when the complete assignment/source/transaction/path manifest agrees.

Adjacent importer negatives cover every live root, the canonical history root
itself, completed and interrupted run roots, `reports/`, sibling/ancestor
destinations, wrong or absent lock, wrong run ID, pre-existing staging, direct
import calls, lexical `..`, in-repository and external aliases to the canonical
root, internal symlinks, and post-check path replacement. Existing safe
external disposable-root behavior remains unchanged.

Adjacent policy negatives cover ordinary and cutover `TODO-*` claims,
non-`0037-31` evidence, missing/duplicate/unknown proof fields, malformed IDs,
wrong claim mode, epoch, source commit/tree, transaction, run ID/root,
assignment/item, changed-path set, companion identity/digest, candidate blob,
and stale or extra output. Claim-bound proof remains green for its existing
lawful cases; unrelated frozen paths retain their current classifications.

At least one exhaustive/property table crosses importer history classification,
reservation state, staging relation, and destination class, and another
crosses evidence path class, Task, claim mode, assignment, epoch, source,
transaction, allowed-path membership, and companion agreement. Exactly the
single fully valid row in each applicable claimless domain passes. Repeat runs
produce identical normalized results and stable diagnostic codes.

## Recovery and exclusions

Before implementation integration, recovery abandons the unintegrated branch
while retaining blocker and governance history. After integration, revert both
tool/test changes together if the production red/green proof fails; retain any
run evidence and use a fresh ID for retry. Never delete or rewrite a prior run,
decision, review, claim, branch, tag, ref, reflog, or object through this work.

Explicitly excluded are broad `_src/output` or history-root writability;
general claimless transactions; new `TODO-*`/`DONE-*` files; Task marker,
prerequisite, Acceptance, or Feature-closure changes; issue-store activation;
selector or policy-profile changes; provenance replay outside the awarded
import; source-watermark substitution; external-root copying; unsigned or
unbound authority assertions; integration, `main` advance, push, publication,
release, or cleanup.

## Conclusion

The repair is supportable only as the conjunction of Gate A, Gate B, conditions
1–8, and the full falsification matrix. It preserves `IMP-LIVE-ROOT` outside
one orchestrator-created staging child and preserves frozen authority outside
one exact assignment-bound `0037-31` manifest. No operative mutation is lawful
until this two-file governance candidate is independently integrated and Lore
receives role-valid same-slot rework.
