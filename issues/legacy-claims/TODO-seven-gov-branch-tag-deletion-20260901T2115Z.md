# Architect claim — governance text closing the branch/tag-deletion gap

- **Owner:** `seven` (Architect, Team Voyager); **owner_token:** `agent:seven:gov-branch-tag-deletion:20260901T2115Z`
- **Authority:** atomic AWARD `1788297280427-fdc11ce3` (offer `1788297197355-7c965d81`), under Management `decision-1788290269652-1e9b7e68`, option `tag_and_govern`, resolved 2026-09-01T21:04:08Z
- **Branch/worktree:** `gov-branch-tag-deletion-20260901` / `.worktrees/gov-branch-tag-deletion-20260901`, from `main@73541d9190`
- **Write scope:** `AGENTS.md`, `docs/pipeline/branch-workflow.md`, this claim. Both are governance artifacts, authored on a branch cut from `main` per `DEC-0044-012`/`DEC-0044-015`; the root checkout was not written.

## Why an offer was requested first

`kathryn` directed this by mail citing the resolved decision, but the decision carried `assignment=-` and named "an Architect" generically. Because the deliverable edits `AGENTS.md` and `docs/pipeline/` — main-only shared governance — I asked for an offer to bind the scope before writing rather than proceeding on an unbounded direction. She issued it within minutes; the analysis was already done, so the round-trip cost nothing.

## The gap, measured rather than accepted

- `AGENTS.md` had exactly **one** relevant clause, point 4, whose trigger is literally *"state that exists in no branch"*.
- `docs/pipeline/` mentions deletion in five files, none prohibitive.
- So no broad prohibition on branch/tag deletion or worktree pruning existed.

The purpose mismatch `doctor` identified is the crux: point 4 fires on *no branch holds it*; the loss actually found was *only a branch holds it* — a 170-line customer-authority dossier destroyed by an ordinary branch deletion no rule prohibited (`556216e4b`, `d697930b4`). The triggers point in opposite directions, so the existing text could not be stretched to cover the new case.

## What was written

1. **`AGENTS.md` point 5** — a broad prohibition. Its operative test is **reachability, not merge status**: `git merge-base --is-ancestor <ref> main`. `[x]`, an accepted assignment, a finalized `DONE-*`, and a removed worktree are each named as *insufficient*, because none proves the bytes survive elsewhere. Retention is the default when the answer is no or unknown; clearing anyway requires `preserved/*` capture first, or named-ref authorization from the current user.
2. **A worktree/branch distinction**, added deliberately so this does not contradict the current DAG policy that worktrees are disposable caches. `git worktree remove` and `--reap-only` stay permitted; `git branch -D`, `git tag -d`, `git push --delete`, `git gc --prune` and `git reflog expire` against work refs do not.
3. **`docs/pipeline/branch-workflow.md` → "Two triggers, not one"** — documents the second trigger explicitly and says why the first could not absorb it.

## Claim verified before it entered governance

The draft asserted that accepted work exists whose authoring branch is not an ancestor of `main`. I measured it rather than leaving it as plausible prose: **81 of 120 sampled local branches are not ancestors of `main`** (2026-09-01), and `41762f045` is a concrete case — its dossier is on `main` byte-identical while the commit itself is unreachable from `main`. The vaguer word "several" was replaced by the measured figure.

That example also sharpens the rule in both directions: a merge-status test would call those branches disposable and be right by accident, and would call an unlanded branch disposable and destroy it. Only reachability separates the two.

## Non-actions

- Diff is **additive only**: 48 insertions, 0 deletions, across the two files.
- No merge. Per the award's merge-point condition this branch ends before integration; handed back to `kathryn` for routing.
- No `preserved/*` tag created, none removed, no ref deleted or pruned.
- No `TODO.md` change, no Acceptance, no integration verdict.

## Provenance

No user-authored prompt. Process-triggered by atomic AWARD `1788297280427-fdc11ce3`, delivered 2026-09-01T21:14:40Z, under Management `decision-1788290269652-1e9b7e68`. Authored 2026-09-01 (UTC) against `main@73541d9190`.
