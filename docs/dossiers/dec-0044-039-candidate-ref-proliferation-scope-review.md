# DEC-0044-039 scope review — candidate-ref proliferation control

- **Review identity:** `agent:data:architect:dec-0044-039:1788521332129-24414d5e`
- **Role:** management-instantiated Architect, Process Architecture
- **Reviewed baseline:** `main@31049b45c0cfea0fbbabe2d1741d32d6274bdbf7`
- **Reviewed proposal:** `DEC-0044-039`, candidate-ref proliferation control
- **Review type:** independent pre-mutation cross-item gate-scope review; not implementation authority, Task Acceptance, integration review, integration verdict, publication approval, or Feature closure

## Verdict

**Supported with a six-path activation boundary.** The smallest coherent rule is
one active candidate ref per assignment or item, linear correction on that ref,
and one narrow escape hatch for explicit atomic same-slot supersession. The four
named normative process documents are necessary but not sufficient: because the
current `legacy-frozen` bootstrap selects
`docs/pipeline/agent-instructions/current/index.md`, activation also requires a
synchronized index update and the matching member and selector digests in
`agent-workflow.json`.

This proposal meets the canonical `cross-item-blast-radius` predicate. Candidate
admission and same-slot rework can block task start, review, integration, and
closure across work units. The decision record and this distinct-identity scope
review therefore must be reachable from `main` before an Implementer mutates
the qualifying gate behavior.

## Evidence and failure classification

Jean-Luc's R3 `db89a61c35103396c5203a724078789566801aed` and R4
`7067c07c2faf70087ad4cdc2434b6866a121047f` resolve to the same tree,
`05c80e44d6e95b9ff8544a51b725f7d41e09dd80`. They are distinct correction
refs without distinct work-product bytes. R6
`8081c9a5099faed07d46dcee6174862af41ab3ba`, tree
`6473ec4fc3f485e491aa0a45fe612167d2fc0469`, is the attempt that carries the
formal coordination evidence. This is sufficient red-on-baseline evidence for
the proliferation failure: ref count grew before evidence value did.

The correction must not turn that finding into permission to discard history.
Existing no-force, no-delete, unique-content retention, preserved-snapshot, and
worktree-isolation rules remain controlling. Tree identity is useful evidence of
redundant attempts, but it is not reachability proof and does not authorize ref
removal. Existing refs require separate inventory and authorized disposition.

## Required lifecycle

The implementation must establish all of these rules together:

1. An assignment or backlog item has one active candidate ref and one associated
   candidate worktree at a time.
2. Review corrections, validation repairs, and same-slot rework append commits
   linearly to that ref. A correction does not mint a sibling branch, worktree,
   claim, or integration candidate.
3. Replacement is allowed only through explicit atomic same-slot supersession.
   The transaction names and preserves the displaced ref, carries the assignment
   history and reservation, and designates exactly one replacement as active.
4. An immutable evidence ref is exceptional. A named decision, review, or
   incident artifact cites its exact commit and records a retention purpose.
   Ordinary failed attempts, red fixtures, or review iterations use commit IDs
   on the active ref and do not each receive an evidence ref.
5. Uncommitted local work is acceptable only while safely recoverable. On an
   interruption that leaves useful work, the contractor commits WIP to the same
   active ref; interruption does not create a new candidate surface.
6. Review and integration pin an exact commit. Final source integration proves
   that exact candidate is an ancestor of canonical `main`; byte-equivalent
   reconstruction, patch replay, or a similar sibling commit is insufficient.

## Normative implementation scope

The behavioral rule must be expressed consistently in:

- `AGENTS.md` — startup, dispatch, correction, and interruption duties;
- `docs/pipeline/branch-workflow.md` — the one-ref lifecycle, worktree handling,
  WIP, supersession, evidence-ref exception, and retained-ref boundary;
- `docs/pipeline/process-roles.md` — dispatcher, contractor, reviewer, and
  Integrator responsibilities without adding authority;
- `docs/pipeline/integration-flow-control.md` — reservation, same-slot repair,
  review-ready candidate identity, and exact ancestry;
- `docs/pipeline/agent-instructions/current/index.md` — the concise directive
  consumed by the current frozen bootstrap; and
- `agent-workflow.json` — only the corresponding bundle-member and selector
  digest changes needed to keep the selected bundle valid.

The index **does need synchronized update**. Omitting it would leave the active
agent description without the new constraint; editing it without the selector
digest would cause a required fail-closed mismatch. The implementation may not
use synchronization to select a different epoch or profile, change capability
or execution authority, add runner actions, or alter selector semantics.

## Authority and safety boundary

This review authorizes no implementation by itself. It does not permit ref
deletion, force update, garbage collection, root-checkout mutation, `main`
integration, Acceptance, publication, Task-marker changes, selector cutover, or
Feature closure. It does not make the Architect the Implementer or Integrator.
The future Implementer remains bounded to an item-owned `/tmp` worktree; the
independent Integrator retains hygiene and canonical-ancestry responsibility.

Same-slot supersession is a lifecycle transition, not cleanup authority. The
displaced ref remains until its bytes are proven reachable from an integrated
ref or the current user explicitly authorizes the exact ref's disposition under
the established preservation contract.

## Required validation and falsification

Before review, the implementation candidate must demonstrate:

- a red baseline in which a second correction candidate for one assignment is
  admitted, using the R3/R4 identical-tree incident as the concrete fixture;
- green rejection of that second active ref and green continuation by another
  commit on the awarded ref;
- green explicit atomic supersession with one resulting active candidate and a
  preserved displaced ref;
- green interruption recovery by WIP commit on the active ref;
- green exceptional evidence-ref handling only when a named durable artifact
  cites the commit and retention purpose;
- unchanged rejection of deletion, force update, implicit authority expansion,
  a second active claim, and byte-equivalent ancestry substitution;
- exact index/member/selector digest coherence without selector-field drift;
- `process_doc_doctor.py --root . --json`, relevant selector validation, and
  ordinary document/link validation; and
- integration evidence proving the reviewed exact candidate commit is an
  ancestor of canonical `main`.

## Rollback and residual risk

Rollback is one coherent reversal of the later six-path implementation, not a
partial rollback that leaves the instruction index or selector digest out of
sync. Durable decisions, reviews, incident evidence, WIP commits, refs, and
receipts remain append-only evidence.

The rule prevents new proliferation; it deliberately does not classify or
remove the existing branch inventory. Legacy cleanup remains a separate,
explicitly authorized and reachability-proven activity. The evidence-ref
exception also requires disciplined review: a vague “keep for evidence” label
is insufficient without a named artifact, exact commit, and retention purpose.
