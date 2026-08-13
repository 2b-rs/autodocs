# Decision-Outcome Classes and Post-Decision Hooks (Feature 0006-07)

Status: implemented 2026-08-13 as a design/primitives task, matching how
0006-05 (hypothesis store) and 0006-06 (lifecycle) were scoped: this ships
the generalized mechanism and its tests, but does not force-wire every
existing caller or invent concrete automation for each outcome class.

## Problem

`extraction_report.py`'s `RESIDUAL` list already proves that not every
curation decision is a plain data overwrite -- some require a code change
instead. But `RESIDUAL` is a flat, hand-maintained Python list with no
machine-readable link back to the decision that motivated each entry, and
no generalized way to express other follow-up kinds (a migration, a parser
change, a new fixture). This does not scale past a handful of entries.

## What this adds

`_src/tools/decision_outcome.py`:

- `OUTCOME_CLASSES`: `db_value_update`, `migration`, `parser_change`,
  `allowlist_exception`, `new_fixture`, `no_action`. The first five are the
  exact five named in the 0006-07 task text; `no_action` covers a decision
  that legitimately needs nothing beyond closing the flag (e.g. "reject,
  already correct").
- `register_hook(outcome_class, fn)` / `run_hooks(outcome_class, payload)`:
  an in-process hook registry. A hook's exception never blocks completing a
  decision -- errors are collected and returned/recorded instead, never
  raised out of `run_hooks()` itself except for a genuinely unknown
  `outcome_class` (a programming error, not a runtime condition).

`curation_flags.complete_flag()` gained two optional, backward-compatible
kwargs: `outcome_class` (defaults to `"no_action"` when omitted, so every
existing caller keeps working unchanged) and `outcome_detail` (free-form).
On completion it runs any hooks registered for that outcome class against
the completed payload; any hook errors are recorded on the flag itself as
`_outcome_hook_errors` rather than raised, so a broken future hook can never
make a curator's decision un-completable.

## Non-goals of this task

Does not implement any real hook (one that actually writes a migration
script, edits `spec_scrape.py`, or adds a `RESIDUAL` entry automatically) --
no such automation exists yet, and this task's own wording is "design", not
"automate". Does not touch `review_flags.py` (review decisions are
requirement-text judgments, not the DB-correction/parser-logic feedback this
task is about) or `extraction_report.py`'s `RESIDUAL` list itself.
