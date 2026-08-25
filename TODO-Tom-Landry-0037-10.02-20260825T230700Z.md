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

`[p]` — claim committed; implementation starting.
