# TODO-perplexity-0037-04.02-a1b2c3d4e5f6.md — active claim

## Claim identity

- `task_id`: 0037-04.02
- `feature_id`: 0037 — Git-Native Issue Store, Provenance Graph, and Backlog Migration
- `agent`: perplexity (SANDBOXED AGENT PERPLEXITY)
- `capability_class`: sandboxed/grunt
request_id: a1b2c3d4e5f6-impl01
owner_token: agent:perplexity:0037-04.02:a1b2c3d4e5f6
base_commit: e913b1b9fd3856c7b3be8d64a9d7d9521bb25675
- `claim_opened`: 2026-08-16 (Europe/Berlin)
- `state`: [x]

## Task scope

- **Task:** `0037-04.02` — Define artifact identity, manifests, storage, indexing inputs, and digest rules.
- **Prerequisite:** `0037-04.01` is terminal (REF: `9aae0b7a295800478bc8eb0d0df795283b28c2a5`, closed in `e913b1b9fd3856c7b3be8d64a9d7d9521bb25675`).
- **Intended write scope:** `provenance/_schema/artifact-set-v1.schema.json`, `docs/pipeline/artifact-identity-and-storage.md`, fixtures under `provenance/fixtures/`, this claim file, and `TODO.md` bookkeeping.
- **Runner scope:** Root `run.sh` singleton slot.
- **External resources:** None.

## Acceptance context

- Schema `provenance/_schema/artifact-set-v1.schema.json` uses SHA-256 over canonical JSON.
- Mutable files require repository-relative path plus byte digest, size, media type, and source commit.
- Trees use sorted member manifests and a tree digest.
- Pin one-file stores and atomic create semantics at `provenance/events/YYYY/MM/`, `provenance/artifact-sets/`, `provenance/runs/`, and `provenance/findings/YYYY/MM/`.
- Indexes under `provenance/_views/` are disposable and never relation authority.
- Fixtures prove file/tree digest changes, member ordering independence, duplicate/collision rejection, redaction, and index reconstruction inputs.

## Closure

- Substantive commit: `b6ebe46faf81cc3cf95def6c7d7e52304fd6a072`.
- Request ID: `a1b2c3d4e5f6-impl01`.
- Schema and valid/invalid fixtures for artifact-set@v1 committed and validated.
- Documented one-file store layout and disposable index reconstruction rules in docs/pipeline/artifact-identity-and-storage.md.
