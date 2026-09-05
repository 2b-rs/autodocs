# TODO-perplexity-0037-06.02-5ea27c94b6d1.md — active claim

## Claim identity

- `task_id`: 0037-06.02
- `feature_id`: 0037 — Git-Native Issue Store, Provenance Graph, and Backlog Migration
- `agent`: perplexity (SANDBOXED AGENT PERPLEXITY)
- `capability_class`: sandboxed/grunt
- `request_id`: 5ea27c94b6d1
- `owner_token`: agent:perplexity:0037-06.02:5ea27c94b6d1
- `base_commit`: b23bd6be45c17b0bd5afb0fed5c9a17f553aab65
- `claim_opened`: 2026-08-16 (Europe/Berlin)
- `state`: [p]

## Task scope

- **Task:** `0037-06.02` — Define schema upgrades and independently authored event reconciliation.
- **Prerequisites:** `0037-04` and `0037-06.01` are terminal.
- **Intended write scope:** `docs/pipeline/` reconciliation/upgrade contract documentation and schemas/fixtures narrowly required by this task, this claim, and `TODO.md` bookkeeping.
- **Runner scope:** Root `run.sh` singleton slot for fixed read-only discovery, validation, and path-limited commits.
- **External resources:** None.

## Acceptance context

- Model schema upgrades as pure version-to-version transforms into fresh roots whose output semantically equals a clean import at the target schema.
- Keep post-import provenance outside disposable item trees and replay an immutable event ID only once when independently authorized and identity-compatible.
- Never overwrite imported text/state; conflicts, stale bases, deleted targets, representation drift, and duplicate events become stable blocking findings rather than automatic merges.
- Cover one source change plus upgrade, authorized preservation, collision/deletion conflicts, and clean-import equivalence.

## Runner history

- **Consumed request:** `5ea27c94b6d1` — fixed read-only discovery, completed 2026-08-16 14:15 CEST with exit code 0.
- **Returned base commit:** `b23bd6be45c17b0bd5afb0fed5c9a17f553aab65`.
- **Authority state:** `legacy-todo-authoritative-until-feature-0037-cutover`.
- **Discovery result:** Claim/task identity validation passed; no files, refs, index, or external state were mutated. Existing conventions include the prior shadow-import contract, provenance contract, `migration-state@v1`, and `provenance-event@v1`; the new transform/replay package must compose with them without duplicating their identity, storage, or authority rules. Existing unrelated dirty/untracked paths remain out of scope.

## Next step

- DONE: Inspected `issue-migration-shadow-import.md` (migration-state@v1) and `provenance-contract.md` (provenance-event@v1); drafted `docs/pipeline/schema-upgrade-reconciliation.md` defining `upgrade-record@v1`, post-import provenance placement, single-replay reconciliation, and the 5 blocking finding kinds (upgrade-overwrite-conflict, upgrade-stale-base, upgrade-target-deleted, upgrade-representation-drift, event-replay-duplicate).
- REMAINING: Publish a bounded implementation-and-validation `run.sh` request to: (a) author the `upgrade-record@v1` JSON schema under `issues/_schema/`, (b) author the fixture set `issues/_schema/fixtures/schema-upgrade-reconciliation-v1/` covering the 4 required scenarios, (c) run the fixture validator, (d) commit contract+schema+fixtures with `REF:` and update `TODO.md` marker to `[x]` on success or leave `[p]` with findings recorded on failure. Any mutation request must fail closed unless base, authority, prerequisites, claimed paths, and clean staging conditions match.

## Completion

- Deliverable commit: `0cd6d346e5f8e6a7c8e18e1d13e02ef909ce2b54`.
- Validation: passed (1 valid, 5 blocking-fixture cases).
- Bookkeeping commit follows this record.
