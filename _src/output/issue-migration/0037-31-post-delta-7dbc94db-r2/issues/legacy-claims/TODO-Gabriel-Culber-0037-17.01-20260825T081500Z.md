# Claim `0037-17.01`

- **item:** `0037-17.01`
- **owner_token:** `agent:gabriel-culber-20260825t081500z:0037-17.01:20260825T081500Z`
- **agent:** Gabriel-Culber-20260825T081500Z
- **capability_class:** unprivileged
- **execution_authority:** Programmer (unprivileged); no Acceptance, checkpoints, `main`, `DONE.md`, push
- **branch:** `0037-17.01`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/0037-17.01`
- **base:** Feature `0037` pin `063b9c04eb68e770ef7b2f9b7d7ea3aeff5c984a` (`0037-09` parent package consistency)
- **prereq merge:** `0037-07` and `0037-09` are ancestors of the pin. Branch `0037-04` is not a named ref; contracts from `0037-04` are already in-tree at the pin (`provenance/_schema/*`, `docs/pipeline/provenance-contract.md`, `docs/pipeline/artifact-identity-and-storage.md`).
- **write scope:** `_src/tools/provenance_store.py`; `_src/tests/test_provenance_store.py`; this claim; `TODO.md` 0037-17.01 block only
- **must not:** Acceptance, checkpoints, `main`, `DONE.md`, push, `0037-11.*`, `0037-13`, `0041-02`, `0011-0018`, `0033`, `uv.lock`, hop

## Startup review

Pinned Feature `0037` at `063b9c04eb68e770ef7b2f9b7d7ea3aeff5c984a`. `0037-09` and its Subtasks are `[x]` on this baseline; the stale successor-recheck note under `0037-17.01` is superseded by that parent-package close. Implementation start prerequisites `0037-04`, `0037-07`, `0037-09` are terminal on this branch.

## Deliverables

- Atomic exclusive-create writers/readers for events, runs, findings, and content-addressed artifact-sets.
- Canonical JSON + SHA-256; replay vs collision; dangling/fabricated/redaction/digest-change rejection.
- Legacy-confidence adapter (`unknown`/`legacy`, no invented scores).
- Tests for concurrent create, replay, collision, crash-before-link, digest changes, redaction, adapters, no partial file.

## User prompt (verbatim)

```
You are Gabriel-Culber-20260825T081500Z, unprivileged Programmer. Work in English. Stay until [x] or blocker. owner_token agent:gabriel-culber-20260825t081500z:0037-17.01:20260825T081500Z. Item 0037-17.01. Branch 0037-17.01. Worktree /Users/tobias.anton/devel/autodocs/.worktrees/0037-17.01. NEVER write shared root. Feature base pin 063b9c04eb68e770ef7b2f9b7d7ea3aeff5c984a. Base Task/Subtask off Feature 0037 at that pin; merge done-unintegrated prereq branches 0037-04, 0037-07, 0037-09 if not already ancestors. Write scope: approved provenance/ event/run/finding/artifact-set paths and their writers/readers under _src/tools/; matching tests/fixtures; claim TODO-Gabriel-Culber-0037-17.01-20260825T081500Z.md; 0037-17.01 TODO.md block only. Implement atomic exclusive-create JSON writers/readers; canonicalize/digest artifact sets; typed endpoints; reject duplicates/collisions/dangling/fabricated/overwrite. DoD: concurrent create, replay, collision, crash-before-rename, digest changes, redaction, no partial file. MUST NOT: Acceptance, checkpoints, main, DONE, push, 0037-11.*, 0037-13, 0041-02, 0011-0018, 0033, uv.lock, hop. Report SHAs or blocker.
```
