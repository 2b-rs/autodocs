# Architect scope review — `0041-02` atomic-cutover graph repair

## Review identity and baseline

- **Reviewer:** `agent:data:0041-02:20260830`
- **Role:** Management-instantiated Architect, Team Enterprise
- **Authority:** Management decision `decision-1788047962210-6bdc03d2`, option A; atomic award `1788070303437-da755a3f`
- **Baseline:** `main@4022945cb123d4d619da5dd60527ab3e7bd61428`
- **Decision reviewed:** `DEC-0041-007`
- **Review type:** supporting cross-item gate-scope review; not Task Acceptance, implementation, integration review, checkpoint verdict, or activation
- **Independence:** Data is distinct from every future Implementer and Integrator. This review is not independent of the architecture decision author and does not claim to satisfy later implementation-review independence.

## Verdict

**Supported within the exact graph and activation boundary recorded by
`DEC-0041-007`.** The current graph cannot legally dispatch the synchronous
cutover: `0041-02` is asked to remove the operative two-commit rule, while
`0041-06`, which aligns the editor/runner/doctor, cannot start before
`0041-02` is terminal. The smallest intent-preserving correction is to make
`0041-02` a non-operative shared-contract producer, keep `0041-03` as bounded
Acceptance-transition preparation, detach the direct push path `0041-04` from
completion semantics, and make `0041-06` the single checkpointed activation
owner. `0041-05` remains unchanged as terminal end-to-end integration.

No qualifying gate behavior may change merely because this review or the
decision lands. Activation occurs only at the reviewed `0041-06` main-ref
advance containing the complete manifest-bound consumer set.

## Evidence and derivation

| Input | Finding used |
| --- | --- |
| `DEC-0041-006` with C001-C005 | CON-05 requires one synchronous governance/editor/runner/doctor/hygiene/guidance cutover; CON-06 prohibits stale-lineage reuse. |
| Saru review `8ba8521b02c3e9c4674347a5731676365f331131` | Bounded non-activating re-derivation may start; early authority mutation and historical candidate `8b1afb933f` remain prohibited. |
| Beverly re-derivation `861d87b721c9b3dbb57612e1d84234c8575c2c3e` | Six stable atomic-check-in requirements, complete consumer matrix, eighteen conjunctive activation blockers, and an activation-safe contract packet. |
| Accepted `0037-51` / `f3522aaaa80d851f3ba28744b08956a52eb63275` | `0041-04` and `0041-06` must be rewritten for direct execution and depend on `0037-51`; host-runner transport is not restored. |
| `TODO.md` at the pinned baseline | `0041-06` depends on terminal `0041-02`, creating the split-brain/deadlock; historical `[x]` markers contradict required current-main re-derivation. |

## Blast radius and exact gate effects

The canonical `cross-item-blast-radius` predicate applies because the change
alters start gates for `0041-03`, `0041-04`, and `0041-06`, checkpoint placement
for `0041-02`/`0041-06`, and the Feature-closure prerequisite graph.

- **Mutated Task contracts:** `0041-02`, `0041-03`, `0041-04`, `0041-06` only.
- **Downstream consumer, not mutated:** `0041-05`; its prerequisite closure and
  terminal mandatory checkpoint remain unchanged.
- **Gate changes:** `0041-04` starts after `0041-01` plus accepted `0037-51`;
  `0041-03` starts only from the checkpoint-reviewed `0041-02` contract;
  `0041-06` starts after `0041-02`, `0041-03`, `0037-51`, and `0038-02` and
  owns activation; its mandatory checkpoint blocks main integration.
- **Repository-wide reach after activation:** implementation/disposition
  completion, editor transitions, transaction execution, diagnostics,
  integration hygiene, Acceptance inputs, and Feature closure.

No additional work unit is silently grandfathered. Existing terminal and
accepted history remains under its original contract; materially reopened or
new post-activation work uses the new contract only after the activation gate.

### Existing `0041-05` lifecycle impact

The pinned backlog already renders `0041-05` as historical `[x]` without a
visible authoritative REF. Reopening its four affected prerequisites causes
the legacy Doctor additionally to report terminal-unsatisfied-prerequisite
findings for `0041-05`. The award permits contract/marker changes only to
`0041-02`, `0041-03`, `0041-04`, and `0041-06`; this review therefore does not
silently reopen or rewrite `0041-05`. Before this graph candidate is integrated,
the coordinator must route a separately scoped lifecycle reconciliation for
the `0041-05` marker/claim evidence or expand the integration candidate under
current authority. Feature closure remains blocked meanwhile. This is a
recorded downstream consequence, not a waiver or acceptance of an invalid
terminal state.

## Interface baseline and package boundaries

1. **`atomic-checkin-contract@v1` (`0041-02` output):** exact `Task-ID` and
   `Base-Ref` grammar; carrying-tree invariants; error taxonomy; historical/
   reopened-work rules; Acceptance boundary; consumer manifest with pinned
   blobs, candidate refs, validation commands, rollback set, and digest.
2. **`acceptance-ref-transition@v1` (`0041-03` output):** exact wording and
   fixtures that remove implementation-header `REF` while retaining Acceptance
   ownership of implementation/review commit IDs and prerequisite/digest proof.
3. **`direct-item-push@v1` (`0041-04` output):** assigned item/branch binding,
   protected-ref and force-update refusal, CAS expectation, result evidence,
   recovery, and canonical-worktree non-mutation under direct execution.
4. **`atomic-cutover-manifest@v1` (`0041-06` input/activation product):** exact
   union of normative, editor, transaction, diagnostic, hygiene, tests, and
   matching-guidance candidates; required predecessor digests; one activation
   tree; pre/post validation; old-writer absence proof; rollback tree.

Consumers must bind the producer version and digest. Local reinterpretation,
parallel trailer grammars, or path ownership outside these boundaries blocks
the activation checkpoint.

## Checkpoint rationale

- **`0041-02` mandatory retained:** its contract and manifest are shared by
  multiple independently authored consumers; an ambiguity would multiply
  before activation. This checkpoint reviews the contract, not an operative
  rule change.
- **`0041-06` mandatory added:** it is the repository-wide activation point.
  Partial scope or an old writer can make valid work fail closed or let invalid
  completion pass. Independent review must pin the exact combined tree and
  run the complete negative/recovery matrix before the main-ref advance.
- **`0041-03` no checkpoint:** its bounded candidate is non-operative and is
  checked through `0041-06`; it grants no authority.
- **`0041-04` no checkpoint:** it has a refusing item/protected-ref guard and
  is independently exercised by terminal `0041-05`; it is not part of the
  completion-rule activation.
- **`0041-05` unchanged mandatory:** sole terminal integrating Task and Feature
  review floor; it proves the real composed workflow after activation.

## Activation, verification, rollback, and migration

- **Activation instant:** the separately assigned privileged Integrator's one
  reviewed main-ref advance of the complete `0041-06` activation tree. Candidate
  commits and architecture landing are non-operative.
- **Pre-activation verification:** exact current-main pin; predecessor/digest
  match; whole-consumer discovery; decision/manifest conformance; focused unit,
  integration, negative, CAS, crash, dirty-state, ancestry, and old-manifest
  tests; no reachable old writer; integration hygiene and root preflight.
- **Post-activation verification:** repeat the same authoritative gates against
  the new root tree, prove the old two-commit entry points reject or are absent,
  and retain exact result evidence.
- **Pre-activation rollback:** abandon the candidate without changing `main`;
  the two-commit rule remains operative.
- **Post-activation rollback:** revert the manifest's complete consumer set in
  one reviewed ref advance to the pinned coherent prior tree; preserve all
  atomic-era evidence and perform impact analysis before resuming new work.
- **Migration/backward compatibility:** no history rewrite. Existing terminal
  and accepted records remain valid under their contemporaneous contract. New
  or materially reopened work after activation uses the atomic contract; no
  implicit grandfathering.

## Dispatch and separation verdict

The repaired graph is dispatchable only after this architecture package is
reviewed and integrated by an authorized Integrator. Implementers receive
separate exact-scope awards/worktrees and may not accept, cross checkpoints,
activate `main`, or move the Feature to `DONE.md`. `0041-06` checkpoint review
and `0041-05` terminal review require independent Integrator authority. No
waiver is present or inferred.
