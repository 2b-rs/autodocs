# DEC-EMERGENCY-DAG-LIFECYCLE-SIMPLIFICATION-20260831

- **Status:** decided — simplify lifecycle to DAG transitions
- **Date:** 2026-08-31
- **Authority:** current repository owner, interactive direction and standing recovery authorization
- **Executor:** `mancons`

## Decision

The Feature/Task DAG is the lifecycle authority. A node advances only when its exact candidate commit is proven an ancestor of its declared aggregate target. Claims are ephemeral scheduling leases; worktrees are disposable caches; partial implementation has no durable status unless committed as WIP, and WIP does not advance the frontier. Review and Acceptance remain candidate-bound transition guards rather than parallel completion state machines.

A worktree without a live lease may be removed forcibly without preserving dirty contents. This never authorizes deletion of commits, branches, tags, the canonical root checkout, existing `preserved/*` tags, or a live leased workspace.

## Reason

The repository accumulated independent state in DAG markers, claims, assignments, branches, worktrees, reviews, Acceptance, integration prose, and publication. These projections disagreed and generated a large false integration queue. During recovery, sampled submitted-for-review chains were already canonical ancestors of `main`; only stale scheduling metadata remained.

## Verbatim user direction

> Yeah I mean - grill me on the idea of having partially completed impl tasks at all. With all the bookkeeping, which almost killed the project today. Is that really needed? Let's thing this through.. In my book, the feature breakdown creates a DAG. that has one start node and one terminal node, all flows through the graph are routed through start and terminal node. Whenever a node has two incoming vertices, some kind of integration needs to happen, and eventually, the terminal node will flow into a larger DAG. So, in theory the impl process is quite straightforward: Just propagate a frontier through the DAG and once every node is covered, you're done. I tried to map this idea onto the project, but it failed miserably. Where's my mistake?

> Continue where you left off
