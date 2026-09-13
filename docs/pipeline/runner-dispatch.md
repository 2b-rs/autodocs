# Typed-action runner queue/dispatcher (Task `0037-46.01`)

Status: implemented and tested, **not activated**. This document describes
`_src/tools/runner_dispatch.py`, `_src/runner/actions-v1.json`, and the
`_src/runner/*.schema.json` schema files. Nothing here changes the live
legacy `run.sh` singleton protocol described in `SANDBOX.md`, and no
repository authority changes as a result of this Task. Activation — wiring
this dispatcher into the actual sandboxed-agent execution path and retiring
the corresponding legacy primitives — is Task `0037-46.02`.

## Why this exists

`docs/pipeline/legacy-handoff-manifest-v1.json` (Task `0038-16.01`) already
mapped every surviving legacy action/schema/result/scope/evidence/recovery/
context/validation/approval-readiness primitive to either a specific
`0037-46.01` typed action or an explicit `0037-46.02` retirement trigger —
65 typed-action mappings owning 74 unique IDs. `docs/pipeline/
branch-merge-actions.md` (Task `0038-19`) separately specified the exact
request/result shape for the three branch/merge actions
(`base-branch`, `merge-prereqs`, `integrate-checkpoint`) against the frozen
`runner-request@v1`/`runner-result@v1` contract. This Task is the
**implementation** those two documents both pointed at: a permanent typed
action registry plus the queue/dispatcher engine that enforces it.

## Relationship to `_src/tools/runner_transaction.py`

`runner_transaction.py` (Task `0038-20`, referenced by
`docs/pipeline/runner-transaction.md`) is a **different, narrower** tool: a
single hard-coded `close-task-v1` transaction profile for the legacy
singleton `run.sh` slot. This Task explicitly reuses its proven safety
*patterns* — fail-closed phases, never-the-ambient-index staging, atomic
per-file promotion, write-once results, never-amend commits — rather than
its code. The decision made here is: **duplicate the pattern, not the
implementation.** `runner_dispatch.py` is a general multi-action queue with
its own draft/publish/claim/lease/result lifecycle; `runner_transaction.py`
remains the sole authority for its one `close-task-v1` profile
(`docs/pipeline/legacy-handoff-manifest-v1.json` primitive
`action.runner-transaction.close-task-v1` — mapped here to
`repo.generate@v1` / `repo.validate@v1` / `git.commit-path-limited@v1` /
`bookkeeping.two-commit-ref-closure@v1` / `claim.finalize@v1` as the
future typed-action decomposition of that same profile) until
`0037-46.02` retires it.

## Layout

```
.runner/                      # git-ignored runtime root, never tracked
  drafts/<agent>/<request-id>/
    manifest.json              # draft-manifest@v1
    request.json                # the runner-request@v1 instance being built
  requests/<request-id>/
    request.json                # published (atomic rename from drafts/)
  claims/<request-id>.lease.json    # runner-lease@v1, created O_CREAT|O_EXCL
  claims/_expired/                  # stale leases moved here on reclaim
  results/<request-id>.result.json  # runner-result@v1, write-once
  logs/<request-id>.log             # append-only
  cancel/<request-id>.cancel        # presence = cancellation requested
  idempotence/<sha256(key)>.json    # last known status per idempotence_key
  quarantine/                        # recovery.quarantine@v1 target
```

`drafts/` and `requests/` are separate subtrees of the same `.runner/`
filesystem so publication (`RunnerRoot.publish_draft`) is a single
`os.rename` — atomic, no partial-visibility window. The dispatcher's
`list_ready_requests()` only ever lists `requests/`; a draft is
structurally invisible until published.

## Carrying typed-action arguments inside the frozen envelope

`issues/_schema/runner-request-v1.schema.json` is frozen,
`additionalProperties: false`, with a fixed field set and no generic
"action arguments" property. Exactly as `branch-merge-actions.md` already
does for its three actions (discriminator in `idempotence_key`, structural
facts in `preflight`), this dispatcher carries every other typed action's
arguments as additional `preflight` entries of the form:

```
arg:<name>=<json-or-plain-value>
```

alongside the discriminator entry `typed-action:<action-id>` and any
action-specific structural entries `branch-merge-actions.md` already
defines (`target-branch:...`, `expected-parent-tip:...`, etc.). This is
strictly additive convention on top of a schema-valid instance — never a
schema relaxation — matching that document's own stated design principle.
The dispatcher derives the typed action id from the `idempotence_key`
prefix (`<typed-action-id>:<item-id>:<disambiguator>`), per
`branch-merge-actions.md` §2.

## Action registry (`_src/runner/actions-v1.json`)

37 typed actions across 8 categories (`context`, `action`,
`approval-readiness`, `evidence`, `recovery`, `validation`, plus the
`preflight_checks` and `forbidden` sections), each with a fixed argument
schema (`required`/`optional` names only — no free-form argv), an
`envelope_action` (one of the seven frozen `runner-request@v1` values), and
an `authority` block (`capability_class`, `network`, `credentials`,
`mutates`). Every action id and its `manifest_primitive` cross-reference is
drawn verbatim from `docs/pipeline/legacy-handoff-manifest-v1.json`'s
typed-action dispositions, so no second, competing ID is minted here.
`forbidden` explicitly rejects any `shell.*`/`exec.*` action id — there is
no generic/shell action, ever, matching this Task's acceptance criteria.

## Dispatcher behavior (`_src/tools/runner_dispatch.py`)

- **Preflight** (`preflight()`): schema validity, secret-value rejection,
  action registration (unknown/generic-forbidden), stale
  base/epoch/pinned-ref, scope shape (no wildcard/absolute/traversal
  paths), scope collision against every other currently-claimed
  (unresolved) request, dependency/credential/network availability against
  the caller-supplied `PreflightContext`, `capability_class` authority
  (privileged-only actions), governance-path write guard, and required
  argument presence — all fail-closed, all findings collected as
  `RD-*` codes before any mutation is attempted.
- **Claiming**: `RunnerRoot.claim()` uses `os.open(..., O_CREAT|O_EXCL)` for
  atomicity; exactly one of N concurrent claimants wins. A lease past its
  `lease_expires_at` with no recorded result is reclaimable
  (`reclaim_stale_leases()`) — this is the crash/restart recovery path.
- **Execution**: each typed action has either a real handler (the six Git/
  ref/claim actions below) or the generic simulated-success handler used
  for actions that wrap external scripts this Task does not activate
  (bootstrap, provisioning, publish, approval-readiness, evidence,
  recovery planning, validation runners) — those still run through the
  full preflight gate, so failure-category tests exercise the real gate,
  not a stub. Execution runs in a daemon thread joined against the
  request's `limits.timeout_seconds`; a hung handler is treated as failed
  with `RD-TIMEOUT` (the thread is abandoned, never left able to touch
  declared state after the join — the six real handlers only ever mutate
  the real repository via a single atomic `git update-ref` compare-and-swap
  at the very end, after all conflict-prone work happened in an isolated
  detached worktree).
- **Real Git/ref handlers**: `git.base-branch@v1`, `git.merge-prereqs@v1`
  (sequential 2-parent merges in an isolated detached worktree, one
  `git merge --no-ff` per source, `git merge --abort` on any conflict,
  final compare-and-swap `git update-ref`), `git.integrate-checkpoint@v1`
  (privileged-only, same isolated-worktree/CAS pattern),
  `git.rollback-ref-cleanup@v1`, `approval.ref-create-append-cas@v1`,
  `claim.finalize@v1` (foreign-`owner_token` rejection).
- **Results**: write-once (`O_CREAT|O_EXCL`), schema-validated, with a
  `result_digest` (`sha256:` over the canonical-JSON result minus the
  digest field itself) any later reader can recompute to detect tampering
  (`RunnerRoot.verify_result_untampered()`).
- **Idempotence/retry**: `idempotence/<sha256(key)>.json` records the last
  status per `idempotence_key`. A new request sharing a key with a prior
  **succeeded** result is rejected (`RD-DUPLICATE-IDEMPOTENCE`); a new
  request sharing a key with a prior **failed/rejected/cancelled** result
  is allowed and its result carries `retry_of: <prior-request-id>`.

## Test coverage

`_src/tests/test_runner_dispatch.py` (44 tests) covers every Definition-of-
Done category: draft visibility; concurrent publication/claiming; stale
base/epoch/ref; scope collision; unknown/generic action; unavailable
dependency/credential; network denial; timeout/cancel; partial mutation
(crashing handler leaves no branch/ref residue); crash/restart (stale lease
reclaim); tampered result; retry; every Git/ref action's rollback
(`base-branch` stale-tip rejection, `merge-prereqs` conflict-abort,
`integrate-checkpoint` authority-violation and success paths,
`rollback-ref-cleanup`, `approval.ref-create-append-cas` CAS rejection and
success); and claim retention. Run:

```bash
python3 -m unittest _src.tests.test_runner_dispatch -v
```

## Deliberately not done here

No activation: nothing wires `runner_dispatch.py` into the live sandboxed-
agent execution path, no legacy primitive is removed, and no authority
epoch changes. `.runner/` is exercised only inside test-owned temporary
directories; this worktree's own `.runner/` (if created ad hoc during
manual testing) is git-ignored and never committed.
