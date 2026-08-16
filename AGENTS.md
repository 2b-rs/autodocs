# Collaboration Rules for Automation and AI Agents

You are an AGENT. This file defines the current collaboration and Task-bookkeeping procedure. Tool use, instruction precedence, and current authority discovery are defined in [`SANDBOX.md`](SANDBOX.md).

## Current authority

Until Feature `0037` completes its authorized cutover, `TODO.md` and `DONE.md` are the authoritative backlog and `TODO-<agent>.md` files are active coordination claims. Marker and prerequisite semantics are defined by the header of `TODO.md`; do not invent alternative meanings.

## Starting work

1. Inspect `TODO.md`, relevant prerequisites, active `TODO-<agent>.md` files, and working-tree changes before selecting work.
2. Start only a Task whose goal is sufficiently clear, whose start prerequisites are terminal, and whose write scope does not conflict with another active claim.
3. Create `TODO-<agent>.md` using the available file tools. Copy the exact Task, enough enclosing Feature context to detect later drift, the base commit, intended write scope, and any assumptions.
4. Recompare the claim with current `TODO.md`, then mark the Task `[p]` and add a claim reference to `TODO-<agent>.md`. Do not overwrite another agent's marker, text, or claim.
5. Multiple simultaneous Tasks are allowed only when their prerequisites are satisfied and their write scopes are disjoint; list each Task explicitly in the claim file.

A user-directed activity that is not an existing Task may use `TODO-<agent>.md` as a temporary coordination record, but must not falsely mark an unrelated Task `[p]`.

## Performing work

- Keep going until the claimed Task is complete or has clearly become unreachable.
- Keep the Task marker and claim progress accurate, including material findings, changed assumptions, validation results, and handoff information.
- Make a best-supported assumption when the Task permits it and record the decision. Use `[u]` only with the meaning defined in `TODO.md`: the next unresolved action requires user/manager clarification, authorization, or another human decision.
- A technical problem is not automatically `[u]`. Investigate it, retain `[p]` with a precise blocker/progress note when work has started, or use `[w]` with the required reason when investigation proves the Task should be closed without implementation.
- Preserve unrelated staged, unstaged, and untracked work. Use path-limited commits and never overwrite or delete another agent's work without explicit authorization.
- Update related tests, documentation, generated artifacts, and call sites when the Task's acceptance criteria require them. Do not claim validation that was not run and observed to pass.

## Completing work

1. Recompare the claimed Task and enclosing Feature with current `TODO.md`. A material discrepancy—such as changed intent, removed work, or a newly unmet prerequisite—is a blocker: do not overwrite it; record the discrepancy and obtain resolution.
2. Validate the deliverables as required by the Task and resolve or explicitly disposition material findings.
3. Commit the substantive deliverables with the configured user identity and a comprehensive message naming the Feature and Task IDs. Commit only intended paths.
4. In a separate bookkeeping change, mark the Task `[x]` (or `[w]` with its required reason), add `REF: <substantive-commit>` after verifying that commit is reachable from `HEAD`, and update any unlocked dependencies.
5. If every Task in the Feature is terminal and all Feature-closure prerequisites are satisfied, move the complete Feature from `TODO.md` to `DONE.md` with its completion timestamp and retained evidence.
6. Delete `TODO-<agent>.md` only after its work and progress have been reconciled into authoritative files.
7. Commit the bookkeeping change separately. Never amend a commit to insert that commit's own hash into a tracked `REF`; the hash would change and leave a dangling reference.
8. Pick another open, unclaimed Task whose prerequisites are satisfied and continue.

For a Task whose only substantive deliverable is backlog bookkeeping, use a first commit for the disposition/content and a separate follow-up commit for any self-referential `REF` that cannot exist in the first commit.

## Interruptions and handoffs

Before yielding with claimed work incomplete:

- leave the Task `[p]` unless `[u]`, `[w]`, or another state is actually justified by `TODO.md`;
- append a concise progress, validation, remaining-work, and interruption note to both the authoritative Task and `TODO-<agent>.md`;
- retain the claim file so another agent can detect ownership;
- identify any temporary files, uncommitted changes, or external state needed for safe continuation.

Do not delete a live claim merely to make the working tree look clean.

Further project information is available in [`README.md`](README.md), [`_src/WARTUNG.md`](_src/WARTUNG.md), and [`docs/pipeline/`](docs/pipeline/README.md).
