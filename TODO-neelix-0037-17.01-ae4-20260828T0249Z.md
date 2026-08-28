# Claim: 0037-17.01 AE-4 follow-up (named adjacent-case tests)

- **owner_token:** `agent:neelix-0037-17.01-ae4-20260828:0037-17.01-ae4:20260828T0249Z`
- **persona / mailbox:** Neelix / `neelix-0037-17.01-ae4-20260828`
- **capability_class:** `unprivileged`
- **execution_authority:** direct Git/tests in item-owned worktree; not sandboxed-grunt; not privileged
- **item:** 0037-17.01 AE-4 follow-up (additive tests only; not a second product implementer)
- **branch:** `0037-17.01-ae4-neelix-20260828`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/0037-17.01-ae4-neelix-20260828T0249Z`
- **base:** remesured `main@b5cbea435fa057cc6db383f05399953a00f78ed2` (matches dispatch pin; 17.02 already on main)
- **product REF (untouched):** `995c025b1bc4de575473dab95256db0ab61f8b17`
- **Culber claim (not reused):** `agent:gabriel-culber-20260825t081500z:0037-17.01:20260825T081500Z`

## Feature context (drift check)

Feature `0037` provenance writers/readers. Task `0037-17.01` is already `[x]` on main with Culber’s REF. Belanna first-review `73d8b9ddbb4fc6e5de0a9ec77bdbb417c9163fa8` is INCONCLUSIVE: product sound; AE-4 gap (named adjacent cases for ~10 `ProvenanceError` codes). This increment adds those tests only.

## Write scope

- `_src/tests/test_provenance_store.py` (additive tests)
- this claim file
- `_src/tools/provenance_store.py` **only if** a committed test proves a product bug (expected: no)

## Must not

Acceptance stamp; advance `main`; `DONE.md`; lift 0037-16 STOP; take/mutate 0037-28; land 17.02 / 10.01 / 11.02; merge stale `0037-09@063b9c04eb`; spawn agents; impersonate gabriel; Feature DONE; overwrite Culber REF/claim.

## AE-4 cases to add

PV-SCHEMA (missing field run/finding/event/artifact-set), PV-UUID, PV-ENDPOINT (self-edge, wrong-kind), PV-CONTEXT (one per record type), PV-COMMIT, PV-MEMBER (duplicate path, path traversal), PV-RELATION, PV-ENV, PV-DATETIME, PV-PRIVACY.

## Progress

- 2026-08-28T02:49Z: worktree/branch cut from remesured main; implementing tests.
