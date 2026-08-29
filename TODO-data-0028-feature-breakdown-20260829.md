# Architect claim — Feature `0028` breakdown

request_id: 1788046717031-ed4daf2d
assignment_id: 1788046717031-ed4daf2d
task_id: 0028-feature-breakdown-current-main-candidate
feature_id: 0028
owner: data
owner_token: agent:data:0028-feature-breakdown-current-main-candidate:1788046717031-ed4daf2d
state: [x]
coordination_state: review
lease_active: false
capability_class: privileged
execution_authority: direct
branch: 0028-feature-breakdown-current-main-candidate-data-20260830
worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0028-feature-breakdown-current-main-candidate-data-20260830
base_commit: 21bea51f3ff340e8125dfb6530430df388f7a5ba
startup_review: AGENTS.md; SANDBOX.md; TODO.md; docs/pipeline/feature-breakdown.md; docs/pipeline/roles/architect.md; docs/pipeline/core-rules.md; docs/pipeline/decision-record.md; decision-1788029989734-71b1345c option A
write_scope: ["TODO.md", "docs/dossiers/dec-0028-001-feature-breakdown.md", "docs/dossiers/0028-feature-breakdown-scope-review.md", "docs/campaign-evidence/0028/architect-feature-breakdown-data-20260829.md", "TODO-data-0028-feature-breakdown-20260829.md"]

## Intended write scope

- `TODO.md`
- `docs/dossiers/dec-0028-001-feature-breakdown.md`
- `docs/dossiers/0028-feature-breakdown-scope-review.md`
- `docs/campaign-evidence/0028/architect-feature-breakdown-data-20260829.md`
- `TODO-data-0028-feature-breakdown-20260829.md`

## Award and boundary

Atomic award `1788046717031-ed4daf2d` assigns management-instantiated Architect
Data to reconstruct the accepted source candidate from
`8aff32728d427e65342345a5a0e7d881583722a6` on exact current
`main@21bea51f3ff340e8125dfb6530430df388f7a5ba`. The coordinator-created branch
and worktree were clean at that base. The corrected `PART-01 Participation`
closed value is `reviewed`.

This claim permits only architecture, the conforming decision, supporting
cross-item scope review, the Feature `0028` backlog block, and this claim. It
does not authorize SYS.1 activation or performance, implementation, external
source adoption or agreement, ratings, Acceptance, checkpoint crossing,
integration, Feature closure, `main` advance, network, credentials, external
effects, or Memory.

## Recovery and next step

Before governance integration, recovery is to withhold or revert only this
candidate while retaining append-only decision history. After integration,
changes require additive impact analysis and renewed review when the canonical
cross-item predicate applies. Return the committed current-main governance
candidate to Jean-Luc; distinct future Implementers and Integrators own all
later work.

## Next step

Validate the reconstructed five-path diff, commit it, and return the exact REF
to Jean-Luc for separate governance integration. Distinct Implementers may be
dispatched only after the candidate reaches their implementation baseline and
all declared start gates are satisfied.

## Source validation retained

- Pre-mutation architecture REF: `8acbcedc6`.
- Feature graph: five unique Tasks, eight prerequisite edges, no missing target
  endpoint/cycle/marker/checkpoint findings; exactly one terminal integrating
  Task (`0028-05`), three mandatory checkpoints and two explicit no-checkpoint
  justifications.
- `0029` block is byte-identical to the pre-mutation baseline; no unconditional
  consumer prerequisite was added.
- `git diff --check`: pass. `process_doc_doctor.py --root . --json`: `ok: true`,
  zero `0028` findings; two inherited unrelated `DOC001` errors.
- `legacy_task_doctor.py --root . --json`: zero Feature/Task `0028-*` findings;
  only the two disclosed temporary-claim findings remain because the exact
  awarded architecture item/filename is not a backlog Task and may not be
  renamed or falsely projected onto `0028-01`.
- No implementation, Acceptance, checkpoint crossing, integration, external
  adoption/effect, rating, Feature closure, `main` advance, or Memory occurred.

## Current-main reconstruction

- Source tip: `8aff32728d427e65342345a5a0e7d881583722a6`.
- Reconstruction base: `main@21bea51f3ff340e8125dfb6530430df388f7a5ba`.
- Candidate is limited to the five declared paths and preserves unrelated
  current-main bytes.
- Exact changed-path set is the five declared paths; `git diff --check` passes.
- `0029` block SHA-256 is identical before/after:
  `389fe5c445f82379f7439551c1b9821054896c8e35d80b4c116b0759ee9757b4`.
- `process_doc_doctor.py --root . --json`: `ok: true`, zero target findings;
  two inherited unrelated `DOC001` errors.
- `legacy_task_doctor.py --root . --json`: zero Feature/Task `0028-*`
  findings; the two expected temporary-claim identity findings remain because
  the awarded reconstruction item is not a backlog Task.
- No implementation, Acceptance, checkpoint crossing, integration, external
  effect, `main` mutation, push, or Memory occurred.
- Final candidate REF is supplied after the path-limited commit.
