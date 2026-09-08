# DAG execution and disposable workspaces

Status: normative process simplification, effective 2026-08-31.

## Authority and precedence

This document replaces lifecycle interpretations that make claims, worktrees, assignment status, or backlog markers independent completion authorities. Existing Acceptance, security, and external-release controls remain guards on a DAG transition; they do not become parallel lifecycle state machines.

## Authoritative model

A Feature breakdown is a directed acyclic graph with one start node and one terminal node. Every node is reachable from start and can reach terminal. The only authoritative execution states are:

- `blocked`: at least one predecessor receipt is absent;
- `ready`: all predecessor receipts exist and downstream capacity is available;
- `running`: one bounded worker lease exists;
- `candidate`: an immutable candidate commit and validation receipt exist;
- `integrated`: the exact candidate is an ancestor of the node's declared aggregate target;
- `failed` or `cancelled`: terminal non-success disposition with reason.

A node advances the frontier only on `candidate → integrated`. `[x]`, assignment submission or acceptance, review handoff, equivalent bytes, a branch name, a claim file, or a worktree never advances the frontier by itself.

## Node receipts

A candidate receipt identifies the node, exact candidate commit, predecessor receipts, validation result, and declared target. An integration receipt identifies the repository, candidate, target before and after, and proves:

```text
git merge-base --is-ancestor <candidate> <target-after>
```

A join node consumes the exact candidate commits of every incoming edge. A protected boundary may require integration even with one incoming edge. Review or Acceptance, when required, is bound to the exact candidate and guards the integration transition.

## Partial work

Partially completed implementation is not a durable project state and carries no completion credit.

- Uncommitted edits are disposable and may disappear without recovery.
- Useful partial progress is committed as an explicitly labelled WIP commit on the node branch.
- A WIP commit preserves bytes but does not create a candidate receipt or advance the frontier.
- On lease expiry, a node without a candidate returns to `ready`; a replacement worker may inspect retained WIP commits or start again.
- No preservation tag, acceptance archaeology, or claim transition is required merely because a dirty worktree exists.

## Claims and worktrees

Claims are short-lived scheduling leases. Worktrees are disposable execution caches.

- A claim records node, worker, lease deadline, and optional candidate SHA.
- Claim filename, repository presence, or assignment status is not product authority.
- Expired or explicitly released claims stop blocking scheduling.
- A managed worktree with no live lease may be removed forcibly, including staged, unstaged, and untracked contents.
- Removing a worktree must not remove branches, commits, tags, or other reachable Git objects.
- Existing `preserved/*` tags remain protected until separately retired.
- The canonical root checkout and any worktree with a current live lease remain protected.

Agents therefore follow: **checkpoint useful work or lose it**.

## Flow control

A node becomes `ready` only when its dependency frontier and downstream integration reservation both permit execution. Dispatchers remain accountable until the integration receipt exists. Implementation or review completion without integration does not free the reserved slot or authorize replacement dispatch.

## Terminal composition

The terminal node produces one immutable aggregate receipt naming its result commit and covered node receipts. A parent DAG consumes that terminal receipt, not the child DAG's worktrees, claims, assignment history, or temporary branches.

## Historical reconciliation

Historical assignments and claims are classified read-only:

1. If the exact candidate is already an ancestor of the declared target, mark the scheduling record reconciled; do not merge metadata merely to close the queue.
2. If an exact candidate exists but is not an ancestor, route it through the bounded integration queue.
3. If only WIP commits exist, return the node to `ready` or cancel it.
4. If no durable commit exists, there is no work product to recover.
5. Ambiguous records remain classified as ambiguous; they do not create a worktree-retention obligation.
