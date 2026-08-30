# Terminal claim lifecycle

Status: emergency operative process rule, effective immediately.

## Purpose

Completed work must stop holding an active worktree lease. This rule separates assignment bookkeeping from repository Task Acceptance and supplies a deterministic, auditable transition from an active `TODO-*` claim to a terminal `DONE-*` claim.

## Authoritative states

1. Mailbox assignment `accepted` means only that the coordinator accepted the contractor's delivered assignment. It is not repository Task Acceptance and does not authorize worktree deletion.
2. Repository Task Acceptance exists only when the applicable Task has one unique current `Acceptance: ✓` recorded by a separately authorized acceptance reviewer.
3. A root-level exact-item `TODO-*` claim is an active worktree lease. An exact-item `DONE-*` claim is terminal evidence and is not an active lease.
4. `[x]`, `state: [x]`, inactivity, age, branch naming, integration, or assignment status alone never substitute for Task Acceptance or claim finalization.

## Required acceptance transition

For an accepted exact numeric item (`XXXX`, `XXXX-YY`, or `XXXX-YY.ZZ`), the authorized acceptance reviewer must, in the acceptance worktree:

1. verify the current Task Acceptance evidence and independence authority;
2. run `_src/tools/provision_tmp_worktree.sh --finalize-accepted <item> <acceptance-worktree>`;
3. inspect the staged exact-item `TODO-*` to `DONE-*` renames and update any claim-path references;
4. commit the Acceptance record and claim renames together;
5. integrate that commit into `main` and report the exact accepted ref to the owner.

The implementer must not self-record Task Acceptance or self-finalize claims unless a current Management waiver explicitly authorizes that bounded exception. Assignment acceptance never supplies such a waiver.

After integration, explicit removal or `_src/tools/provision_tmp_worktree.sh --reap-only <root>` may remove only worktrees that still pass all conservative cleanliness, lock, live-CWD, branch-pin, exact-claim, Acceptance, and `main`-reachability checks. Branches and commits remain retained.

## Chain and coordination claims

Chain, review, award, and other noncanonical claims must carry an explicit lease state. `lease_active: false` plus a terminal state ends that coordination lease, but does not create Task Acceptance. Such claims must not be heuristically treated as exact numeric Task claims and must not block cleanup of a separately accepted exact numeric Task.

## Historical reconciliation

Historical claims are migrated only through a dry-run-first reconciler that emits a durable manifest containing the source path, proposed destination, item, classification, evidence ref, and blob hash. Each claim must be classified as active, accepted-and-finalizable, terminal non-Task, or ambiguous. A privileged reviewer approves deterministic changes. Ambiguous claims remain untouched. No inference from age, inactivity, `[x]`, assignment state, or branch reachability is permitted.

## Recovery and audit

Every migration or finalization preserves Git history and records approving identity and accepted ref. Worktree removal never deletes the branch. A mistaken rename is recovered by reverting the bookkeeping commit; a mistaken worktree removal is recovered by recreating the worktree from its retained branch.
