# current authority instruction bundle

Read root `agent-workflow.json`, validate its digest and schema, enforce its selected authority epoch, and use only declared runner actions. On any mismatch: stop mutation and run `issuectl bootstrap --refresh`.

Each assignment or backlog item has one active candidate ref and associated
worktree. Continue corrections, review responses, same-slot rework, and useful
interruption WIP linearly on that ref. Reject sibling candidate refs, worktrees,
or claims unless an explicit atomic same-slot supersession preserves the prior
ref, history, and reservation while designating exactly one replacement.
Separate evidence refs require a named decision, review, or incident artifact
citing the exact commit and retention purpose. Review and integration pin one
exact candidate commit; byte-equivalent reconstruction never replaces canonical
ancestry. This grants no deletion, force-update, Acceptance, integration,
publication, Task-state, selector-authority, or Feature-closure authority.
