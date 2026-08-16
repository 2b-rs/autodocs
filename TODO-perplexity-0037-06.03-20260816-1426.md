# TODO-perplexity-0037-06.03-20260816-1426.md — active claim

## Claim identity

- `task_id`: 0037-06.03
- `feature_id`: 0037 — Git-Native Issue Store, Provenance Graph, and Backlog Migration
- `agent`: perplexity (SANDBOXED AGENT PERPLEXITY)
- `capability_class`: sandboxed/grunt
- `request_id`: 0037-06.03-20260816-1426
- `owner_token`: agent:perplexity:0037-06.03:0037-06.03-20260816-1426
- `base_commit`: 93009145b0bad6fbaace851cdff12d1a45f2c53f
- `claim_opened`: 2026-08-16 (Europe/Berlin)
- `state`: [p]

## Task scope

- **Task:** `0037-06.03` — Define freeze, candidate promotion, atomic authority switch, and rollback without event loss.
- **Prerequisites:** `0037-03`, `0037-05`, and `0037-06.02` are terminal.
- **Intended write scope:** `docs/pipeline/` cutover/rollback contract documentation, narrowly required issue schemas/fixtures, this claim, and `TODO.md` bookkeeping.
- **Runner scope:** Root `run.sh` singleton slot for fixed read-only discovery, validation, and path-limited commits.
- **External resources:** None.

## Acceptance context

- Define source/candidate/decision/cutover watermarks, freeze enforcement, candidate immutability, prepared patch checks, one-commit switch, generated legacy headers, entry-point updates, and detached-worktree rollback rehearsal.
- Retain control/audit evidence in append-only, fast-forward-only compare-and-swap cutover refs; maintain `[p]` markers for designated post-watermark tasks until `0037-40` materializes closure.
- Enforce a digest-bound quiescence barrier, a `legacy-frozen` epoch through the post-cutover audit window, and rollback to matching `legacy-restored` instructions with provenance-only control/audit events.
- Include state machine, ref topology, control-ledger schema, rehearsal plan, abort criteria, and no-issue-write rollback fixtures.

## Runner history

- **Consumed request:** `0037-06.03-20260816-1426` — fixed read-only discovery, completed 2026-08-16 14:27 CEST with exit code 0.
- **Returned base commit:** `93009145b0bad6fbaace851cdff12d1a45f2c53f`.
- **Authority state:** `legacy-todo-authoritative-until-feature-0037-cutover`.
- **Discovery result:** Claim/task identity validation passed; no files, refs, index, or external state were mutated. Existing unrelated dirty/untracked paths remain out of scope.
- **Consumed request:** `0037-06.03-impl-20260816-1429` — schema/fixture implementation and focused validation, completed 2026-08-16 14:30 CEST with exit code 0. Created `issues/_schema/cutover-control-ledger-v1.schema.json` and `issues/_schema/fixtures/cutover-control-ledger-v1/`; validation passed: `OK: 1 valid + 7 invalid cutover-control-ledger fixtures checked`. No commit or TODO bookkeeping mutation was performed.

## Next step

- Publish a fresh, guarded path-limited commit/bookkeeping runner request: revalidate contract/schema/fixtures, stage only the claimed deliverables, commit them, update `TODO.md` to `[x]` with the actual deliverable `REF`, record completion in this claim, and commit the bookkeeping. Fail closed if base, authority, prerequisites, ownership, or staged-path scope changes.

## Completion

- Deliverable commit: `4e05155775c86192686153db52e036635dfadba6`.
- Validation: passed (1 valid, 7 invalid control-ledger fixtures).
- Bookkeeping commit follows this record.
