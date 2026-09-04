# TODO-perplexity-0037-05-ef6b49a27c81.md — active claim

## Claim identity

- `task_id`: 0037-05
- `feature_id`: 0037 — Git-Native Issue Store, Provenance Graph, and Backlog Migration
- `agent`: perplexity (SANDBOXED AGENT PERPLEXITY)
- `capability_class`: sandboxed/grunt
- `request_id`: ef6b49a27c81
- `owner_token`: agent:perplexity:0037-05:ef6b49a27c81
- `base_commit`: 975da3bd31bde0e3bf9752f536b2ce8376262880
- `claim_opened`: 2026-08-16 (Europe/Berlin)
- `state`: [x]

## Task scope

- **Task:** `0037-05` — Define the source/derived matrix and executable regeneration DAG in `docs/pipeline/issue-derived-artifacts.md` and `docs/pipeline/issue-derived-artifacts-v1.json`.
- **Prerequisites:** `0037-01`, `0037-02`, and `0037-04` are terminal.
- **Intended write scope:** `docs/pipeline/issue-derived-artifacts.md`, `docs/pipeline/issue-derived-artifacts-v1.json`, any narrowly required schemas/fixtures under `issues/` or `docs/pipeline/`, this claim, and `TODO.md` bookkeeping.
- **Runner scope:** Root `run.sh` singleton slot for fixed read-only discovery, validation, and path-limited commits.
- **External resources:** None.

## Acceptance context

- Define `issue-regeneration-dag@v1` with stable stage IDs, argv arrays, dependencies, typed input globs, exact outputs, sole writers, retention, privacy, determinism, promotion, cleanup, and validation.
- Classify canonical source inputs and all required derived artifacts; do not introduce SQLite in v1.
- Provide JSON Schema, complete manifest, human matrix, and cycle/writer/staleness fixtures with exactly one generating stage and validation rule per derived path.

## Runner history

- **Consumed request:** `ef6b49a27c81` — fixed read-only discovery, completed 2026-08-16 14:07 CEST with exit code 0.
- **Returned base commit:** `975da3bd31bde0e3bf9752f536b2ce8376262880`.
- **Authority state:** `legacy-todo-authoritative-until-feature-0037-cutover`.
- **Discovery result:** Claim/task identity validation passed; no files, refs, index, or external state were mutated. Candidate pipeline schema documents are present, but no existing derived-artifact/DAG document or manifest was identified by the requested filename scan. Existing unrelated dirty/untracked paths remain out of scope.
- **Consumed request:** `ef6b49a27c81-impl01` — bounded implementation and semantic validation, completed 2026-08-16 14:10 CEST with exit code 0.
- **Implementation evidence:** Wrote the DAG schema, complete manifest, human source/derived matrix, and valid plus five invalid fixtures. Schema JSON and manifest semantic validation passed; no commit was made.

## Next step

- Allocate and record a fresh request ID. Publish a fail-closed path-limited bookkeeping/commit request that rechecks the base, prerequisites, generated package, and validation evidence; then stages only this task’s deliverables, claim, and `TODO.md`, commits the package, and returns the REF for closure bookkeeping.

## Closure

- Task package committed with REF: f05ce02a7c69e9b3d1eafb66ac815183dcc3b13e.
