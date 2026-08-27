# Claim `0037-26.04`

- **item:** `0037-26.04`
- **owner_token:** `agent:programmer-0037-26-04:0037-26.04:20260827T124500Z-db04r2`
- **agent:** programmer-0037-26-04 (unprivileged Programmer; persona ≠ gabriel dispatcher)
- **capability_class:** unprivileged
- **execution_authority:** Programmer (unprivileged); no Acceptance, checkpoints, `main`, `DONE.md`, push, 0037-16 STOP lift
- **branch:** `0037-26.04`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/0037-26.04`
- **base:** R2 candidate `2064704457f98c66fb6f77ad3c263415864fe2ff` (0037-19 bookkeeping `[x]`, REF `c2f198e19`)
- **prereq merge:** `0037-17` tip `78f1e3fd2` is an ancestor of the pin (`merge-base --is-ancestor` exit 0). `0037-19` is the pin itself (`[x]` remeasured 2026-08-27). Parent Task branch `0037-26` does not exist; sibling Subtask worktrees use the same 0037-19 pin. No sibling 26/27 branches merged.
- **write scope:** `_src/tools/` database rebuild/migration/version/snapshot writers; `_src/tests/` matching fixtures; this claim; `TODO.md` 0037-26.04 block only
- **must not:** Acceptance; `main`; `DONE.md`; 0037-16 STOP lift; sibling 26/27; 16/19/20/38/42; shared root; `memory_append`; push

## Startup review

Remeasured `0037-19` at `2064704457`: marker `[x]`, REF `c2f198e19`. Prerequisites `0037-17` and `0037-19` are terminal on this baseline. Caveat: R2 candidate base as briefed.

## Next step

Complete. Implementation terminal at REF `553232536`. Claim retained (`state: [x]`); no Acceptance.

## Progress

- Claim committed `e32a0c2e7`.
- Substantive REF `553232536a337e30a7b9c6703be8274584f8d0bf`.
- Validation: `python3 -m unittest _src.tests.test_db_snapshot -v` → 5/5 OK.

## Adversarial completion evidence

- **AE-2 baselines:** pre-change `2064704457f98c66fb6f77ad3c263415864fe2ff`; candidate `553232536a337e30a7b9c6703be8274584f8d0bf`.
- **AE-3:** `test_partial_snapshot_is_not_promoted` — baseline has no `_src/tools/db_snapshot.py` (`git cat-file -e 2064704457:_src/tools/db_snapshot.py` exit 128); candidate 5/5 green including crash-before-rename leaving `list_live()==[]`.
- **AE-4 adjacent:** (1) input/config/schema drift → `SNAP-DRIFT`; (2) identical inputs/config → same `semantic_identity`, config digest change → different identity.
- **AE-5:** `test_record_set_identity_is_order_independent_inputs_are_not`; oracle: sorted record-set identity invariant, ordered input sequence is identity-bearing; domain n in 1..5 plus AB/BA pair; executed 5 + 2.

**state:** [x]

## User prompt (verbatim)

```
You are an unprivileged Programmer (persona ≠ gabriel dispatcher). Capability class: unprivileged.

ITEM: 0037-26.04. Worktree `.worktrees/0037-26.04` branch `0037-26.04` at `/Users/tobias.anton/devel/autodocs`. Never write shared root.

Start `2064704457f98c66fb6f77ad3c263415864fe2ff` after remesuring 0037-19 [x]. Claim-first owner_token `agent:<persona>:0037-26.04:<request-id>`.

WRITE: database rebuild/migration/version/snapshot writers + tests + claim + TODO 0037-26.04 block.

MUST NOT: Acceptance; main; DONE; 0037-16 STOP lift; sibling 26/27; 16/19/20/38/42; root; memory_append; push.

CAVEAT: R2 candidate base.

DoD: fixtures detect input/config/schema drift, trace changed records to evidence/trigger, deterministic identity, no partial snapshot promotion.

AGENTS.md, git -C, path-limited commits.
```
