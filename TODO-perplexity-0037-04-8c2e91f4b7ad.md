# TODO-perplexity-0037-04-8c2e91f4b7ad.md — active claim

## Claim identity

- `task_id`: 0037-04
- `feature_id`: 0037 — Git-Native Issue Store, Provenance Graph, and Backlog Migration
- `agent`: perplexity (SANDBOXED AGENT PERPLEXITY)
- `capability_class`: sandboxed/grunt
- `request_id`: 8c2e91f4b7ad
- `owner_token`: agent:perplexity:0037-04:8c2e91f4b7ad
- `base_commit`: 2324732a890f62fdc3d7adff09641269c0b4c344
- `claim_opened`: 2026-08-16 (Europe/Berlin)
- `state`: [x]

## Task scope

- **Task:** `0037-04` — Complete the review-ready typed-reference, provenance-event, run, finding, and artifact-set contract.
- **Prerequisites:** `0037-04.01` and `0037-04.02` are terminal with substantive REFs `9aae0b7a295800478bc8eb0d0df795283b28c2a5` and `b6ebe46faf81cc3cf95def6c7d7e52304fd6a072`.
- **Intended write scope:** this claim file and `TODO.md` bookkeeping. If verification exposes an omission, narrowly scoped provenance documentation/schema/fixture files may be added to the claim before mutation.
- **Runner scope:** Root `run.sh` singleton slot for fixed read-only discovery, validation, and commit requests.
- **External resources:** None.

## Acceptance context

- The two Subtasks must define one non-duplicated causal model that existing campaign/build/AI/version/evidence formats can adapt to without fabricating history.
- Both Subtasks and a complete bidirectional causal-chain fixture must be included in the architecture review package.
- Existing candidate fixture: `provenance/fixtures/valid/provenance-chain.json`.

## Runner history

- **Consumed request:** `8c2e91f4b7ad` — fixed read-only discovery, completed 2026-08-16 13:52 CEST with exit code 0.
- **Returned base commit:** `2324732a890f62fdc3d7adff09641269c0b4c344`.
- **Authority state:** `legacy-todo-authoritative-until-feature-0037-cutover`.
- **Discovery result:** Claim/task identity validation passed; no files, refs, index, or external state were mutated. The runner listed a pre-existing dirty worktree containing many paths outside this claim’s intended write scope; it must remain untouched.
- **Consumed request:** `8c2e91f4b7ad-close01` — validation-only aggregation check, completed 2026-08-16 13:53 CEST with exit code 0.
- **Validation evidence:** Valid JSON; 14/14 required relations; 12/12 endpoint kinds; linked event/finding/run/artifact causal chain; provenance and artifact-storage contract evidence present. No paths changed.

## Failure recovery

- **Consumed request:** `8c2e91f4b7ad-close02` — guarded bookkeeping request, completed 2026-08-16 13:54 CEST with exit code 1 after its first path-limited commit.
- **Partial outcome:** Commit `b6963479` created the parent closure state and claim file, but the follow-up REF-bookkeeping Python invocation incorrectly consumed the heredoc placeholder `-` as a file path and failed before any subsequent commit.
- **Recovery discovery:** Request `8c2e91f4b7ad-recover-discover01` completed 2026-08-16 14:03 CEST with exit code 0. Exact current base is `b69634793352f9ea2ad941fa2ea6ac2b53fb407b`; all eight recovery guards passed. The earlier recovery failure was therefore caused by an unreported shell guard, not an invalid task/claim/marker condition.
- **Remaining repair:** Replace `PENDING_SECOND_COMMIT` in `TODO.md`; replace both pending markers in this claim; preserve the existing completed parent state and commit only the two claim-scope paths. The repair must start from full base `b69634793352f9ea2ad941fa2ea6ac2b53fb407b`.

## Next step

- Allocate and record a fresh request ID. Publish a fail-closed path-limited recovery request that verifies commit `b6963479`, replaces pending REF markers with its returned bookkeeping commit, and commits only `TODO.md` and this claim.

## Closure

- Parent aggregation validated by runner request `8c2e91f4b7ad-close01`: valid JSON, 14/14 relations, 12/12 endpoint kinds, and complete linked causal-chain evidence.
- First bookkeeping commit: b69634793352f9ea2ad941fa2ea6ac2b53fb407b.
- Final REF bookkeeping commit: b69634793352f9ea2ad941fa2ea6ac2b53fb407b.
