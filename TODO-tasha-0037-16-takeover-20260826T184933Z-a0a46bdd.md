# Claim 0037-16 takeover — Tasha 20260826T184933Z

- item: `0037-16`
- owner_token: `agent:tasha:0037-16:20260826T184933Z-a0a46bdd`
- agent/persona: `tasha`, Programmer / Implementer for this Task, Team Enterprise
- capability_class: `unprivileged`
- branch: `0037-16` (`refs/heads/0037-16`)
- worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/0037-16`
- base/HEAD at claim: `525e8f96427e69c049d32cf1d6729d099b4a98c9`
- dispatcher: `jean-luc`, direct e4 assignment `1787770011623-30ddfa63`
- allocation epoch: `0037-16/20260826T184500Z/e4`
- status: `[x]`, implementation committed; awaiting independent Acceptance/integration routing

Mailbox coordination identifies the assignment and exact scope but does not create Acceptance, independence, specialist approval, release authority, or permission beyond this claim.

## Briefing and authority limits

1. `capability_class: unprivileged`; Programmer / Implementer persona for ordinary Task `0037-16`. Direct local Git/Python execution is limited to the named item worktree; no runner.
2. Item `0037-16`; branch `refs/heads/0037-16`; worktree `/Users/tobias.anton/devel/autodocs/.worktrees/0037-16`; exact verified pre-claim HEAD `525e8f96427e69c049d32cf1d6729d099b4a98c9`.
3. First-commit write scope is only this new claim and the exact additive `0037-16` line in `TODO.md`.
4. Product scope after a separately delivered explicit GO is limited to:
   - `_src/tools/issue_migration_report.py`
   - `provenance/_schema/issue-migration-report-v1.schema.json`
   - `_src/tests/test_issue_migration_report.py`
   - this claim and the exact `0037-16` bookkeeping block in `TODO.md`

Tasha must not push; perform Acceptance or acceptance review; add, alter, invalidate, or remove `Acceptance: ✓`; cross a mandatory checkpoint; merge Task→Feature or Feature→`main`; move `main`; edit `DONE.md`; close the Feature; use `memory_append`; delegate; widen scope; or touch the shared root checkout.

## Preserved claim lineage

The following records and tokens remain byte-for-byte unchanged:

- `TODO-worf-ezri-0037-16-20260826T182000Z.md` — `agent:worf-ezri-20260826T182000Z:0037-16:20260826T182000Z`
- `TODO-nog-0037-16-handoff-20260826T183400Z.md` — `agent:nog-20260826t183400z:0037-16:20260826T183400Z-7f1a3c5e`
- `TODO-hguh-0037-16-takeover-20260826T184400Z.md` — `agent:hguh:0037-16:20260826T184400Z`

Superseding coordination basis:

- DeepSpace9 formal return: `agent-inbox:1787769340612-f18b71c7`
- yrevocsiD Lastabwurf: `agent-inbox:1787769886631-11e83605`
- Enterprise direct e4 assignment: `agent-inbox:1787770011623-30ddfa63`

Hguh's exact prior tip is claim-only. `git diff f1f5b9c96888a92f25165db3cd2793f076551b9f..525e8f96427e69c049d32cf1d6729d099b4a98c9` names only `TODO-hguh-0037-16-takeover-20260826T184400Z.md` and `TODO.md`; no product work is appropriated or represented as Tasha's.

## Independently verified before first mutation

- worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/0037-16`
- branch: `0037-16`
- HEAD: `525e8f96427e69c049d32cf1d6729d099b4a98c9`
- porcelain: empty
- Task marker: `[p]`
- prerequisites `0037-04`, `0037-11`, `0037-13`, `0037-14`, `0037-15`, and `0037-17.01`: all `[x]` on this branch
- existing product paths: unchanged by the e4 takeover claim

## Product authorization and next step

- claim-only commit: `d7f6b87ca0b32f8538c3954bdfdca181e1fabfc1`
- independent verification and explicit PRODUCT GO: `agent-inbox:1787770294260-506be28e`
- verified parent: `525e8f96427e69c049d32cf1d6729d099b4a98c9`
- verified scope: only the three product paths, this claim, and the exact `0037-16` block in `TODO.md`

Implement the migration-report gate, exercise the required positive and adversarial cases, commit the bounded work product and evidence, then report the exact SHA and validation. The original prohibitions remain in force.

## Implementation completion

- implementation REF: `eb9533fe34bb326dded53333b3100f77eaf209d1`
- validation: `python3 -m unittest _src.tests.test_issue_migration_report` — 15 tests, OK
- validation: `python3 -m py_compile _src/tools/issue_migration_report.py _src/tests/test_issue_migration_report.py` — pass
- validation: `git show --check --oneline --stat eb9533fe34bb326dded53333b3100f77eaf209d1` — pass
- worktree after implementation commit: clean
- lifecycle boundary: implementation only; no Acceptance, integration checkpoint, Feature closure, or `main` action performed
