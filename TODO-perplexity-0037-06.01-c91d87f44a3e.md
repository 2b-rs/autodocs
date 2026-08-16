# TODO-perplexity-0037-06.01-c91d87f44a3e.md — active claim

## Claim identity

- `task_id`: 0037-06.01
- `feature_id`: 0037 — Git-Native Issue Store, Provenance Graph, and Backlog Migration
- `agent`: perplexity (SANDBOXED AGENT PERPLEXITY)
- `capability_class`: sandboxed/grunt
- `request_id`: c91d87f44a3e
- `owner_token`: agent:perplexity:0037-06.01:c91d87f44a3e
- `base_commit`: eade8f536142cc98fb352a18c4e86bf5576167b2
- `claim_opened`: 2026-08-16 (Europe/Berlin)
- `state`: [x]

## Task scope

- **Task:** `0037-06.01` — Define immutable legacy-source watermarks and disposable full shadow imports.
- **Prerequisites:** `0037-01` and `0037-02` are terminal.
- **Intended write scope:** `docs/pipeline/` migration/import contract documentation and schemas/fixtures narrowly required by this task, this claim, and `TODO.md` bookkeeping.
- **Runner scope:** Root `run.sh` singleton slot for fixed read-only discovery, validation, and path-limited commits.
- **External resources:** None.

## Acceptance context

- Import only `TODO.md`, `DONE.md`, and claim blobs from an exact committed Git tree, not the working tree.
- Record source/importer commit and digest, schema versions, and baseline/latest-source/candidate watermarks.
- Require a fresh run-specific candidate root and reports root; promote only a validated immutable Git tree object; block dirty/staged backlog source watermarks.
- Cover first import, source changes, deletions/reused IDs, moved tasks, changed prerequisites, malformed input, interruption, and stale-candidate rejection.

## Runner history

- **Consumed request:** `c91d87f44a3e` — fixed read-only discovery, completed 2026-08-16 14:12 CEST with exit code 0.
- **Returned base commit:** `eade8f536142cc98fb352a18c4e86bf5576167b2`.
- **Authority state:** `legacy-todo-authoritative-until-feature-0037-cutover`.
- **Discovery result:** Claim/task identity validation passed; no files, refs, index, or external state were mutated. The only filename-matched migration convention was `docs/pipeline/aspice-level1-score-import.md`; the review-ready migration-state package must therefore establish the required task-specific contract without relying on an existing Feature 0037 migration schema. Existing unrelated dirty/untracked paths remain out of scope.
- **Consumed request:** `c91d87f44a3e-impl01` — bounded implementation and migration-semantic validation, completed 2026-08-16 14:13 CEST with exit code 0.
- **Implementation evidence:** Wrote `migration-state@v1` schema, immutable-source/shadow-import contract with sequence diagram and scenario table, plus a valid fixture, six invalid fixtures, and an interrupted-run fixture. Schema JSON and migration semantic validation passed; no commit was made.

## Next step

- Allocate and record a fresh request ID. Publish a fail-closed path-limited bookkeeping/commit request that rechecks the base, prerequisites, generated package, and validation evidence; then stages only this task’s deliverables, claim, and `TODO.md`, commits the package, and returns the REF for closure bookkeeping.

## Closure

- Task package committed with REF: 1e761bcc388e637cb516934770ce9299713bc233.
