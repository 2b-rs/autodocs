# Architect claim — `0044-20` terminal claim lifecycle

item_id: 0044-20-terminal-claim-lifecycle-architecture
task_id: 0044-20
feature_id: 0044
request_id: 1788038395542-d19fafda
assignment_id: 1788038395542-d19fafda
owner_token: agent:data:0044-20:1788038395542-d19fafda
base_commit: 2ffc0d2a26eea939b74ceb4754309ff2de22e5fb
capability_class: privileged
execution_authority: direct
state: [p]
coordination_state: in_progress
lease_active: true
write_scope: ["TODO.md", "TODO-data-0044-20-terminal-claim-lifecycle-architecture-20260829.md", "docs/dossiers/dec-0044-033-terminal-claim-lifecycle.md", "docs/dossiers/0044-20-terminal-claim-lifecycle-scope-review.md"]

## Award and boundary

Atomic award `1788038395542-d19fafda` assigns Architect Data to define the
cross-item terminal-claim lifecycle decision and its distinct Architect
gate-scope review in the supplied worktree. The branch and worktree started
clean at exact `main@2ffc0d2a26eea939b74ceb4754309ff2de22e5fb`.
`DEC-0044-033` was absent from that exact current `main` before allocation.

This award does not authorize implementation, mutation of pipeline policy or
code, changes to Feature `0020` products or claims, Acceptance, checkpoint
crossing, integration, `main` advance, Feature closure, waiver, release, or
external effect.

## Architecture inputs and finding

- `TODO.md` and `docs/pipeline/task-acceptance.md` require implementation
  claims to finalize at `[x]`/`[w]` while remaining `TODO-*` until current
  Acceptance renames them byte-identically to `DONE-*`.
- Feature `0044-17` already removed the obsolete
  `LTD-CLAIM-TERMINAL-RETAINED` emission on current `main`, but older item
  branches can still execute the pre-`0044-17` doctor and reject the required
  awaiting-Acceptance state.
- `0020-10` has a complete substantive package at
  `b4c1874678798353bcbdbf5ad2d08ce5e3c9ad7d`; terminal bookkeeping is held
  because its worker and chain claims cannot be made consistent with the stale
  branch-local doctor under the existing bounded scopes.

## Structured planning

- **A1 target-policy check:** `fits`. The candidate changes only governance
  records and Feature `0044` backlog architecture; implementation is deferred
  to a distinct identity and the separately assigned Integrator.
- **A2 order:** decision and scope review first; governance integration second;
  bounded implementation or legacy-branch continuation only after the decision
  is reachable from `main`.
- **Prerequisite derivation:** `0044-20:0044-17`; `0044-17` supplies the
  accepted-item rename and current-main Doctor baseline this decision
  regularizes. No dependency on `0020-10` is added because that Task is an
  affected consumer, not an architecture prerequisite.
- **Test derivation:** exact fixtures must cover active `TODO-*`, terminal
  awaiting-Acceptance `TODO-*`, accepted `DONE-*`, premature `DONE-*`,
  multi-claim atomic finalization, active-award/lease rejection, and a
  pre-`0044-17` compatibility case.
- **Capability profile:** privileged Architect for this decision; later
  implementation is unprivileged/direct, stdlib Python/Git, cognitive high,
  no network, credentials, external mutation, Acceptance, or integration.
- **Advisory bounds:** architecture 20 minutes; later implementation 45–90
  minutes, CPU under 5 minutes focused tests, memory under 1 GiB; uncertainty
  medium because branch-local validator selection and multi-claim atomicity
  interact; reach/risk high because every unaccepted terminal Task can be
  blocked by the wrong interpretation.

## Recovery

Before commit, discard only this branch's declared-path edits. After commit,
revert by a new commit; never rewrite the decision history, touch Feature
`0020`, or advance `main`.

## Next step

Author `DEC-0044-033`, the separate Architect scope review, and the smallest
bounded `0044-20` implementation contract needed for consistent automation;
validate exact scope and return the committed candidate to Jean-Luc.
