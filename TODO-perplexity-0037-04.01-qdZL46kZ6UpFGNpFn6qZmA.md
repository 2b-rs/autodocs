# TODO-perplexity-0037-04.01-qdZL46kZ6UpFGNpFn6qZmA.md — active claim

## Claim identity

- `task_id`: 0037-04.01
- `feature_id`: 0037 — Git-Native Issue Store, Provenance Graph, and Backlog Migration
- `agent`: perplexity (SANDBOXED AGENT PERPLEXITY)
- `capability_class`: sandboxed/grunt
request_id: qdZL46kZ6UpFGNpFn6qZmA-validate01
owner_token: agent:perplexity:0037-04.01:qdZL46kZ6UpFGNpFn6qZmA
base_commit: cf5af6335b018bd78af0a1502a69343de078197c
- `claim_opened`: 2026-08-16 (Europe/Berlin)
- `state`: [x]

## Task scope

- **Task:** `0037-04.01` — Define typed references, relation semantics, IDs, immutable events, runs, findings, and evidence/privacy classes.
- **Prerequisite:** `0037-02` is terminal per the authoritative backlog.
- **Intended write scope:** `provenance/_schema/typed-reference-v1.schema.json`, `provenance/_schema/provenance-event-v1.schema.json`, `provenance/_schema/run-v1.schema.json`, `provenance/_schema/finding-v1.schema.json`, supporting provenance documentation and fixtures only, plus this claim and authoritative task bookkeeping.
- **Runner scope:** Root `run.sh` singleton only after read-only base discovery, subject to the active-claim and runner-slot guards in `SANDBOX.md`.
- **External resources:** None expected.

## Acceptance context

The deliverable must cover typed endpoints, directional/cardinality relation rules, UUIDv7 identifiers for events/runs/findings, canonical typed URIs, and explicit environment/privacy classifications. It must include review-ready schemas, relation and redaction rules, collision/replay handling, complete examples, and invalid fixtures for endpoint, relation, and classification rules.

## Discovery evidence

- `request_id`: `qdZL46kZ6UpFGNpFn6qZmA` (consumed 2026-08-16)
- `result`: read-only discovery succeeded; runner slot was removed and is free.
- `base_commit`: `cf5af6335b018bd78af0a1502a69343de078197c`
- `pre-existing unrelated changes`: `docs/pipeline/reports.md`, `docs/pipeline/tools.md`, and `docs/pipeline/website-review-flag.md`; they remain outside this task's write scope.

## Implementation request

- `request_id`: `qdZL46kZ6UpFGNpFn6qZmA-impl01` (consumed 2026-08-16; implementation request succeeded)
- `expected_base`: `cf5af6335b018bd78af0a1502a69343de078197c`
- `allowed paths`: `provenance/**`, `docs/pipeline/provenance-contract.md`, this claim, and `TODO.md` only.
- `validation`: strict Draft-7 schema and valid/invalid fixture checks, followed by a scoped Git status assertion that preserves unrelated edits.

## Closure

- Substantive commit: `9aae0b7a295800478bc8eb0d0df795283b28c2a5`.
- Validation: JSON syntax, enum coverage, URI-kind constraints, relation endpoint matrices, and invalid-fixture coverage passed.
- Bookkeeping request: `qdZL46kZ6UpFGNpFn6qZmA-bookkeeping03`.
- Unrelated pre-existing work was not staged or modified.
