# TODO-perplexity-0037-03.02-7f2a9c4e1b68.md — active claim

## Claim identity

- `task_id`: 0037-03.02
- `feature_id`: 0037 — Git-Native Issue Store, Provenance Graph, and Backlog Migration
- `agent`: perplexity (SANDBOXED AGENT PERPLEXITY)
- `capability_class`: sandboxed/grunt — execution only through the singleton root `run.sh` runner slot
- `request_id`: 7f2a9c4e1b68
- `owner_token`: agent:perplexity:0037-03.02:7f2a9c4e1b68
- `base_commit`: cd6d8db17341cf2616b016c7a0b80f5912e96673
- `claim_opened`: 2026-08-16 (Europe/Berlin)
- `state`: [p]

## Task

- [p] **0037-03.02** PREREQ: 0037-03.02:0037-02 Define the cross-worktree/cross-clone claim and recovery protocol in `docs/pipeline/issue-lifecycle.md`.
  - **Acceptance criteria:** `issues/_schema/issue-claim-v1.schema.json` requires item, owner identity, worktree/clone ID, base commit, claimed write scopes, issued/expiry times, lease nonce, and CAS-ref digest. Same-clone acquisition uses atomic `git update-ref refs/autodocs/claims/<item-id>`; independent clones serialize by promptly integrating `claim.json` to a protected branch. Integration rejects stale bases, duplicate/overlapping active scopes, and unmerged competing claims. Expiry blocks new work until explicit release or authority-approved takeover; takeover never deletes history. Document fetch/recheck, renewal, handoff, crash recovery, unavailable-remote behavior, and the limitation that no repository-only mechanism guarantees pre-merge exclusivity across disconnected clones.
  - **Definition of Done:** Review-ready schema, state table, compare-and-swap pseudocode, merge-time rules, and race fixtures cover two worktrees, two clones, expiry, takeover, stale base, overlapping scopes, and failed integration.

## Intended scope

- `TODO.md` — only `0037-03.02` marker and claim/closure records
- `TODO-perplexity-0037-03.02-7f2a9c4e1b68.md` — this claim
- `docs/pipeline/issue-lifecycle.md` — append claim/recovery protocol only
- `issues/_schema/issue-claim-v1.schema.json`
- `issues/_schema/fixtures/issue-claim/`
- root `run.sh` — one-use runner envelopes for this claim only

## Runner scope

Initial request is fixed read-only discovery: obtain current base, scoped worktree status, existing claim/schema/fixture materials, and competing active claim records. It must not mutate repository, refs, index, or external state.

## Progress log

- 2026-08-16 — Claimed after `0037-02` closed and after the separate `0037-03.02` marker was restored in `cd6d8db17341cf2616b016c7a0b80f5912e96673`. Publishing required read-only discovery request.
- 2026-08-16 — Retry request `5d1a8e3c7f49` corrected the rejected overlapping-scope fixture and committed `536c824f095f1563b9c565378afecabb4ff07bf1` after earlier assertion-only failures. Task marked [x]; closure REF recorded.
