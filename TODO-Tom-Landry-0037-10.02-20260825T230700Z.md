# Claim — Tom-Landry-20260825T230700Z — Task 0037-10.02

- **owner_token:** `agent:tom-landry-20260825t230700z:0037-10.02:20260825T230700Z`
- **Dispatcher:** `tom` (Tom Paris, Team Voyager), under exact assignment from `gabriel` (Team Enterprise coordination, acting for Feature 0037), agent-inbox `1787699122823-078dd9cc`, thread `feature-0037-delivery-20260826`.
- **Capability class:** `unprivileged` (direct Git/tests/commits in own worktree; no runner queue).
- **Item:** `0037-10.02` — "Implement claim, renew, release, handoff, and authorized recovery operations."
- **Feature base:** `118aeb64247dff3023c7904586e04cf523a8626a` (canonical Feature 0037 tip, verified by dispatcher).
- **Branch:** `0037-10.02`, created directly from the Feature base above.
- **Worktree:** `.worktrees/0037-10.02`.
- **Prerequisites (`0037-03.02`, `0037-08`, `0037-09`, `0037-17.01`):** all confirmed `[x]` and reachable as ancestors of the Feature base per `TODO.md` at that commit (lines 815, 1000, 1009, 1037); no additional merge required per dispatcher's pre-check, independently re-verified.

## Write scope

- `_src/tools/issuectl.py` — only the claim, renew, release, handoff, and authorized-recovery surfaces.
- `_src/tests/test_issuectl.py` and any `0037-10.02`-owned fixtures/tests added.
- This claim file.
- `TODO.md` — only the `0037-10.02` Task block, appended for completion bookkeeping.

## Must not

- No `Acceptance: ✓`, no integration-checkpoint merge, no reviewer self-representation.
- No `refs/heads/main` moves, no `DONE.md` edits.
- Must not touch `0037-10.03` surfaces (shares `issuectl.py`; kept unimplemented — no claim/renew/release/handoff/recover scaffolding beyond what this Task itself needs).
- Must not touch `0037-11`, `0037-23.02`, `issue_lists.py`, `issues/_views` product files, page templates.
- `TODO.md`/`DONE.md` treated as governance/bookkeeping only, never as tool-generated data.
- No writes to the shared root checkout `/Users/tobias.anton/devel/autodocs`.
- No `agent-inbox` `memory_append` calls (project-wide safety hold).

## Design notes (recorded before mutation)

Existing `issuectl.py` (at Feature base) already implements query/structural-edit surfaces (`0037-10.01`/`0037-10.04`) and a read-only `enforce_claim_scope`/`_claim_owner` helper. `issue_validate.py` already implements the authoritative claim-record checks this Task must stay consistent with: `_claim_digest` (canonical-JSON sha256 excluding `cas_ref_digest`), `ACTIVE_CLAIM_STATES`, `_scopes_overlap`, `_parse_time`, `COMMIT_SHA`. The `issue-claim-v1.schema.json` schema and `issues/_schema/fixtures/issue-claim/` fixtures define the exact claim record shape and CAS-ref (`refs/autodocs/claims/<item-id>`) semantics from `docs/pipeline/issue-lifecycle.md` §"Claim and Recovery Protocol".

Plan: add `claim`, `renew`, `release`, `handoff`, `recover` subcommands to `issuectl.py`. Each performs local same-clone CAS acquisition via `git update-ref refs/autodocs/claims/<item-id> <new-blob> <old-value-or-empty>` plus an atomic item-local `claim.json` sidecar write, reusing `iv._claim_digest`/`iv._scopes_overlap`/`iv._parse_time`/`iv.COMMIT_SHA` for consistency with the validator. `recover` implements the authority-approved-takeover path (requires `--authority-decision`, target claim must be expired). `handoff` requires either a prior `released` claim or an explicit `--authority-decision`. History/append-only-ness is provided by Git commit history over the sidecar file plus the CAS ref, not a separate event log (matches `docs/pipeline/issue-store.md` §5: "retained state, kein globaler Mutex").

## Status

`[p]` — substantial implementation complete and committed (`f32a4179239ea2d73fbb86ba474b2e6881ce49ff`): `claim`/`renew`/`release`/`handoff`/`recover` subcommands in `_src/tools/issuectl.py`, 12 new tests in `_src/tests/test_issuectl.py`, full suite 30/30 PASS, `automation_safety.py` clean against this Task's changes.

Not marked `[x]`: two open items recorded in the `TODO.md` `0037-10.02` block —

1. **Deviation from stated acceptance criteria.** The acceptance text specifies same-clone acquisition via Git-ref compare-and-swap (`refs/autodocs/claims/<item-id>`). After `git update-ref`'s static-analysis classification as a "publication" git subcommand made `automation_safety.py`'s AUTO010 check unsatisfiable without contorting the code around its heuristics, I substituted the file's existing `--expected-digest` CAS pattern (same mechanism `edit`/`criterion-*` already use) against the `claim.json` sidecar. Functionally equivalent same-clone serialization, but not literally what the criterion names. Needs review/decision before this can count as satisfied — flagging rather than self-certifying.
2. **Definition of Done gaps.** No multi-worktree/simulated-multi-clone race tests, no protected-branch integration/rejection path (only same-clone acquisition implemented — cross-clone integration is out of this increment), no crash-point fault-injection tests specific to claim.json, no "remote unavailable" scenario coverage.

Next step if resumed: either get explicit sign-off that the expected-digest CAS substitution is acceptable (possibly updating the acceptance-criteria text to match, which would need architect/decision authority since it changes a recorded acceptance criterion), or find a different way to satisfy `automation_safety.py` while keeping literal Git-ref CAS; then add the missing race/crash/remote-unavailable test coverage.

## `uv.lock` provenance (untracked, not committed, not in write scope)

An untracked `uv.lock` (4826 bytes, `version = 1`, `revision = 3`, `requires-python == 3.9.6`) sits in this worktree as of 2026-08-26 01:12. **I generated it**, during this session's own validation work: this worktree's `pyproject.toml` declares `dependencies = ["ruamel.yaml==0.18.14"]`, which is not installed under a bare `python3`/`pip` here, so I ran `uv run python3 _src/tools/automation_safety.py ...` and `uv run python3 _src/tests/test_issuectl.py` repeatedly (first at roughly 2026-08-26 00:5x–01:1x local, across the automation_safety iteration and the final full-suite runs) to get a real dependency-satisfied interpreter rather than a false `ModuleNotFoundError: No module named 'ruamel'` result from a bare interpreter. `uv run` transparently creates `.venv` and, on first use, writes `uv.lock` pinning the resolved dependency graph from `pyproject.toml` — that lockfile write is a side effect of `uv run`/`uv sync`, not something I invoked directly or intended as a deliverable. I did not run `uv add`/`uv remove`/`uv lock` myself, and I made no changes to `pyproject.toml`.

I am not aware of any other process in this worktree that would have generated it — no other agent's claim references this worktree, and `.worktrees/0037-10.02` was created fresh for this Task by me. I have high confidence it is this session's own generated validation artifact, but I have not independently proven no other process touched this worktree, so I am stating my confidence level explicitly rather than asserting certainty. Per instruction: **not committed** (outside write scope: `_src/tools/issuectl.py`, `_src/tests/test_issuectl.py` + fixtures, this claim, the `0037-10.02` `TODO.md` block only), **not deleted, not cleaned**. Going forward, per dispatcher `tom`'s relayed instruction from `gabriel`, validation in this worktree uses `/tmp/autodocs-0037-08-venv-julian/bin/python` instead of `uv run`; I re-verified with it: `/tmp/autodocs-0037-08-venv-julian/bin/python _src/tests/test_issuectl.py` → 30/30 PASS, same result as my earlier `uv run` check. `uv`/`uv.lock` are validation tooling only in this worktree, never a product dependency and never referenced from `issuectl.py` itself.

## Historical status only (additive, 2026-08-26)

The **Status `[p]`** and open-items list above were current for this Landry increment. They are **not** current Task status. Terminal implementation `[x]` REF `fcaad421216911d5d69ef0a55cb6f330e105cee1`. This file is predecessor provenance, not a live claim lease.
