# Claim — 0038-22.01 worktree reaper performance correction

item_id: 0038-22.01
feature_id: 0038
owner_token: agent:zed-daybreak:0038-22.01:20260830T220000Z
capability_class: unprivileged
execution_authority: direct Git and local validation in the item-owned worktree; no Acceptance or main-integration authority
startup_review: current user explicitly requested the fix, branch check-in, and Jadzia integration handoff
branch: 0038-22.01
worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0038-22.01
base_commit: 49275b203e
status: implementation_complete_awaiting_review

## Scope

- `_src/tools/provision_tmp_worktree.sh`
- `_src/tools/test_provision_tmp_worktree.py`
- this claim file

## Problem and intended correction

`ref_has_item_claim` launches one `git show` and one `awk` for every root claim on every numeric worktree. At the observed baseline (35 numeric worktrees, 365 TODO claims), guarded cleanup exceeded ten minutes. Replace the per-claim loop with one anchored root-path `git grep` per lookup without changing conservative eligibility semantics.

## Authority boundaries

This correction does not alter Acceptance, claim-finalization policy, eligible branch grammar, or integration checkpoints. It must not move `main`, create `Acceptance: ✓`, delete branches, or broaden which worktrees may be removed. Jadzia receives a separate review/integration handoff after implementation.

## Validation plan

- `bash -n _src/tools/provision_tmp_worktree.sh`
- hermetic `_src/tools/test_provision_tmp_worktree.py`
- red/green regression instrumenting Git to prove no per-claim `git show` calls
- bounded live `--reap-only` run after unit validation
- `git diff --check`

## Progress

- 2026-08-30 — branch/worktree created from `main@49275b203e`; claim initialized.
- 2026-08-30 — replaced the `ls-tree` + per-claim `git show`/`awk` loop with one anchored root-path `git grep`; exact `task_id`/`item_id` matching and TODO-before-DONE safety semantics are unchanged.
- 2026-08-30 — validation passed on final bytes: `bash -n`; full hermetic provisioner suite 33/33 in 28.467s; `git diff --check`; three live guarded `--reap-only` measurements completed in 9.73–33.90s rather than exceeding 600s. The policy-aware repository-wide automation-safety scan exceeded its 180s bound and was killed, so no global pass is claimed; the focused scan reported zero policy errors but, by its documented path-only behavior, surfaced seven pre-existing undispositioned findings. The replacement preserves the function's original line count, avoiding drift in downstream line-bound dispositions.

## Adversarial completion evidence

- **Exact baseline/candidate:** pre-change `main@49275b203e`; candidate branch `0038-22.01` before commit.
- **Falsification case:** `test_reap_claim_lookup_does_not_show_each_unrelated_claim` instruments the actual Git executable. Against `49275b203e`, it fails after observing 65 individual `git show main:TODO-*.md` calls (64 unrelated valid IDs plus the punctuation neighbor); against the candidate it passes with zero such calls while still reaping the accepted exact-item worktree.
- **Adjacent case 1 — exact live claim:** `test_keeps_exact_item_todo_claim`; neighboring dimension is matching prefix/identity (`TODO` for the exact item); expected and observed result is retained worktree.
- **Adjacent case 2 — unrelated historical claim:** `test_historical_prerequisite_claim_does_not_block_terminal_item`; neighboring dimension is unrelated TODO identity beside the exact DONE identity; expected and observed result is reaped worktree.
- **Set/property evidence:** finite exhaustive fixture domain of 64 distinct unrelated valid Task identities, one punctuation-neighbor identity (`0200-11x01` versus exact `0200-11.01`), and one exact accepted DONE identity. Oracle: unrelated and punctuation-neighbor identities never satisfy exact-item membership, the exact DONE identity does, and lookup performs zero per-claim blob reads. Executed case count: 66 claim identities in the new regression, within the 33-test hermetic suite.

## Handoff

Implementation is committed only after final diff inspection. Jadzia must independently review the exact commit, rerun focused validation, run integration hygiene with the exact candidate, and integrate only if her current assignment and privilege authorize the target transition. This claim grants no Acceptance or integration authority.
