# Claim: Tom-Chapel-0037-10.02-20260826T000200Z

owner_token: agent:tom-chapel:0037-10.02:20260826T000200Z

## Context

Task: **0037-10.02** — claim/renew/release/handoff/recover CAS ops in `_src/tools/issuectl.py`.

This is a **correction claim**, dispatched by `tom` (Dispatcher, Team Voyager) directly
under explicit REJECTION from `gabriel` (Team Enterprise, relaying `jean-luc`'s decision),
agent-inbox thread `feature-0037-delivery-20260826`.

Predecessors on this exact task, in order:
- `Tom-Landry` (`TODO-Tom-Landry-0037-10.02-20260825T230700Z.md`)
- `Tom-Reyes` (`TODO-Tom-Reyes-0037-10.02-20260826T000000Z.md`) — implemented a real
  `git update-ref` CAS in `_cas_promote_claim`/`_update_ref_cas`, but routed the actual
  `update-ref` invocation through the generic `_git(repo, args)` argv-forwarding helper.
  The dispatcher (`tom`) initially endorsed this, citing `runner_transaction.py` precedent
  for the same idiom. **`gabriel`/`jean-luc` rejected it**: the generic wrapper is an
  analyzer blind spot for `automation_safety.py`'s static scanner (`_is_subprocess_invocation`
  only recognizes literal `subprocess.*` call names, and `_git`'s own `*args` forwarding is
  not statically resolvable either) — existing precedent for the same pattern elsewhere does
  not make it a correct security pattern, it may just mean the same blind spot exists twice.

## Capability class

`unprivileged`. Direct Git, tests, commits. No runner queue.

## Marker

Task stays `[p]` — this is corrective work on an already-`[p]` task, not new acquisition.
Not setting `[x]`.

## Write scope

- `_src/tools/issuectl.py`
- `_src/tests/test_issuectl.py`
- This claim file
- `TODO.md` — only the `0037-10.02` block, line-wise appended

## Two corrections required

1. Make the `git update-ref` CAS call statically visible to `automation_safety.py`
   (literal `subprocess.run([...])` call site, not hidden behind `_git()`), paired with a
   scanner-recognized durable-outcome/recovery writer (`_atomic_write` to the CAS journal),
   without any policy suppression/allowlist/disposition entry.
2. Replace the two rejected crash tests (pre-CAS monkeypatch that never executes the real
   crash-point code; post-lifecycle sidecar deletion that doesn't test an actually
   interrupted state) with real subprocess-level fault injection at:
   - pre-CAS boundary (killed after reading current state, before `update-ref` write)
   - post-ref/pre-sidecar boundary (killed after `update-ref` succeeds, before the sidecar
     receipt is written)
   Preserve the valid existing tests (multi-worktree race, offline/remote-unavailable,
   ref-namespace-disjointness).

## Validation interpreter

`/tmp/autodocs-0037-08-venv-julian/bin/python` (not `uv`).

## Progress log

- 2026-08-26T00:02:00Z — claim opened. Investigated `automation_safety.py`'s AUTO001/
  AUTO009/AUTO010 rule implementations (`_is_subprocess_invocation`,
  `_static_command_variants`, `_subprocess_failure_is_propagated`,
  `_scope_has_durable_state`, `_node_postdominates_operation`) to understand exactly what
  the scanner recognizes as (a) a checked mutating subprocess call and (b) a postdominating
  durable-outcome writer.
- Confirmed root cause: `_git()`'s call name (`_git`, not in `_SUBPROCESS_APIS`) and its
  `*args` forwarding (an `ast.Name` the analyzer cannot statically resolve to literal argv)
  make any call routed through it invisible to AUTO001/AUTO008/AUTO009/AUTO010 alike.
- Inlined a literal `subprocess.run(["git", "-C", str(repo), "update-ref", ref, new_blob,
  old_arg], capture_output=True, check=False)` directly in `_update_ref_cas`, replacing the
  `_git(repo, [...])` call. Verified via `automation_safety.py --path _src/tools/issuectl.py
  --json` that the call became visible (AUTO001/AUTO009 initially fired because the original
  intervening-raise structure blocked postdomination of the journal writer — see next step).
- Restructured the success/failure branches so a single unconditional `_atomic_write`
  outcome-journal write directly follows the `subprocess.run` call (no intervening branch),
  then the CAS-loss raise happens after that write. Re-verified: AUTO010 (missing durable
  outcome) cleared. Re-checking AUTO001/AUTO009 (checked-subprocess recognition) after
  switching the branch condition from an intermediate `cas_succeeded` bool back to a direct
  `completed.returncode != 0` test, since `_references_result_returncode` only recognizes
  direct `<result>.returncode` attribute access, not an indirect boolean variable.
- **Interrupted mid-verification by dispatcher `tom`**: session had modified
  `_src/tools/issuectl.py` with no claim committed and no WIP commit, repeating the exact
  process mistake `Tom-Reyes` was corrected for. Committing this claim now, then a WIP
  commit of the current `issuectl.py` state, before continuing verification and before
  starting the test-replacement work (item 2 above, not yet started).

## Remaining work

- Re-run `automation_safety.py --path _src/tools/issuectl.py --json` to confirm the
  `completed.returncode != 0` branch condition change clears AUTO001/AUTO009 as expected
  (last run before interruption still showed both firing on the intermediate-variable
  version, prior to the direct-attribute-access fix).
- Run full `automation_safety.py` (no `--path` restriction) to confirm no regression
  elsewhere and get final verdict/JSON for the report.
- Replace the two rejected crash tests in `_src/tests/test_issuectl.py` with real
  subprocess-level fault injection at the two named boundaries (not started yet).
- Run full `test_issuectl.py` suite; confirm the three preserved valid tests
  (multi-worktree race, offline/remote-unavailable, ref-namespace-disjointness) still pass.
- Report back to `tom` per the dispatch briefing.

## Supersession (additive, 2026-08-26) — not a rewrite of the text above

The **Marker** (`Task stays [p]`) and **Remaining work** list above were current when this claim was opened and when Chapel's correction product `fcaad421216911d5d69ef0a55cb6f330e105cee1` was still in progress. They are **not** the current status.

- Prior rejection (unchanged history): Tom-Reyes routed `git update-ref` through generic `_git(...)`; Jean-Luc/gabriel rejected that as an `automation_safety.py` analyzer blind spot, not a scanner-recognized safe pattern.
- Corrected product REF: `fcaad421216911d5d69ef0a55cb6f330e105cee1`.
- Independent evidence (not this claim's original remaining-work list): focused `_src.tests.test_issuectl` 37/37 PASS; path-scoped `automation_safety.py --path issuectl.py` PASS, `unresolved_critical: 0`.
- Jean-Luc resolution message `1787703872485-ab93bd05` authorized terminal `[x]` with product REF `fcaad4212`.
- Terminal bookkeeping: `54243ba5070983abadb0f2dbde97b7c60c11eb94` marked `TODO.md` `[x]` with that REF. Implementation write scope released. This claim file is provenance, not a live `[p]` lease.
- Feature-reconcile candidate merge that carried this file: `3243c831726469ccec343e5435054719b4529ac1`. This supersession is an additive commit on that isolated branch. Not Acceptance.
