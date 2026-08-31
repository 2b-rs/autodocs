# Integration flow control and canonical receipts

Status: normative emergency recovery process, effective 2026-08-31.

## Problem addressed

Implementation capacity exceeded integration capacity. Dispatchers could open work without downstream reservation, leave responsibility at review handoff, and immediately open replacement work. The result was a growing review queue, hundreds of branches and worktrees, and no feedback pressure to finish integration. A separate publication job then reset `main` onto an unrelated orphan history, making normal integration structurally impossible while reconstructed commits were incorrectly described as integrated.

Sequencing implementation, unit testing, and integration in prose is insufficient. Flow requires admission control, bounded WIP, one accountable owner through the terminal postcondition, and a machine-checkable canonical receipt.

## Admission and WIP limits

1. Before offering implementation, the dispatcher obtains a reservation from a named available Integrator. The reservation names one chain and one expected source-history baseline.
2. An Integrator holds at most one active reservation. A team holds at most two implementation-complete but not canonically integrated chains.
3. No reservation means no new implementation offer. At the limit, dispatchers and available workers drain review, repair rejected candidates, reconcile terminal claims, or remain available; they do not manufacture more queue entries.
4. The Integrator pulls a review-ready chain. Submission for review does not push work past the capacity gate.
5. Rejection, conflict, stale baseline, failed hygiene, missing evidence, or failed ancestry keeps the same slot occupied until repair or explicit cancellation.
6. A fleet freeze blocks new offers and all source or publication ref movement until the authority that issued it explicitly releases it.

## End-to-end accountability

The dispatcher owns flow, not technical approval. Its obligation ends only when the canonical receipt below exists and the chain's active claims are reconciled. The Implementer still owns implementation and correction. The independent Integrator still owns review, hygiene, Acceptance where assigned, and the source integration. These duties may not be collapsed merely to improve throughput.

Implementation completion, `[x]`, assignment acceptance, review submission, branch-local Acceptance, and byte-equivalent reconstruction are intermediate states. None is canonical integration.

## Canonical source integration receipt

Every successful integration records, durably:

- repository common-dir identity (canonical absolute path or stable digest);
- candidate commit SHA;
- `main` SHA immediately before integration;
- `main` SHA immediately after integration;
- successful command and result for `git merge-base --is-ancestor <candidate> <main-after>`;
- hygiene and root-preflight results required by `branch-workflow.md`;
- remote `main` SHA observed after push when push is in scope;
- Integrator identity, reservation identifier, and timestamp.

The receipt fails closed if the candidate is not an ancestor of `main-after`, if the repository identity differs from the reservation, or if `main` has no merge base with the expected source-history baseline. Recreating equivalent bytes does not satisfy ancestry.

## Source and publication separation

`main` is source history rooted in the repository's original source root. Generated websites, exports, bundles, reports, or deployment trees publish only to `published`, `gh-pages`, or a separate deployment repository. Publication automation must refuse a target named `main` and must not reset, force-update, or orphan any source branch.

A publication receipt records its source commit and destination branch/repository, but never claims that the publication commit integrated the source candidate.

## Recovery and queue drain

After a lineage incident:

1. freeze dispatch and ref movement;
2. preserve the displaced lineage under named branch and tag refs;
3. restore `main` from the last trustworthy reflog/source tip;
4. replay only independently verified emergency fixes;
5. validate original root, expected merge bases, and candidate ancestry;
6. restart Integrators and Project Leads;
7. drain reserved review-ready work oldest-first, except that blockers and prerequisite order may change the safe order;
8. reconcile accepted claims and run the conservative worktree reaper;
9. release dispatch only when queue depth is below the WIP limit and each new chain has a reservation.

Historical branches are evidence, not an automatic integration backlog. Each is classified as already canonical, review-ready, superseded, rejected, ambiguous, or publication-only before any merge or cleanup.
