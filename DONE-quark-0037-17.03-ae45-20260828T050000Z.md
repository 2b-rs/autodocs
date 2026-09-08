# Claim: 0037-17.03 AE-4 + AE-5 `_add_unique` follow-up

- **owner_token:** `agent:quark-0037-17.03-ae45-20260828:0037-17.03-ae45:20260828T050000Z`
- **persona / mailbox:** Quark / `quark-0037-17.03-ae45-20260828`
- **git author leak:** host `user.name`/`user.email` is `gabriel` / `gabriel@discovery.starfleet.network` (Cursor user). Persona is Quark — same leak class as Neelix/Odo AE follow-ups.
- **capability_class:** `unprivileged`
- **execution_authority:** direct Git/tests in item-owned worktree; not sandboxed-grunt; not privileged
- **item:** 0037-17.03 AE-4 (+ AE-5 `_add_unique`) follow-up (additive tests; not a second product implementer)
- **branch:** `0037-17.03-ae45-quark-20260828`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/0037-17.03-ae45-quark-20260828`
- **base:** remesured `main@4edee5ddbd9121b662f86589ddb2c89962ac6724` (matches AWARD pin)
- **landed product on main (untouched):** `32b50e502`
- **Rhys REF (untouched; not overwritten on TODO.md heading):** `91b848933fb055d4c51ee62ceba0a1d6e2b8e619`
- **Rhys token (not reused):** `agent:gabriel-rhys-20260825t085000z:0037-17.03:20260825T085000Z`
- **review inspected (read-only, not merged):** `6ed2d756624efca86c8c4d2e9b7e4293ea311657` INCONCLUSIVE
- **not merged:** `refs/heads/0037-17.03` tip `1e281456a`

## Feature context (drift check)

Feature `0037` provenance query. Task `0037-17.03` is already `[x]` on main with Rhys REF. Belanna first-review `6ed2d7566` is INCONCLUSIVE: product sound; AE-4 gap (record-version, curation-item, unresolvable); AE-5 recommendation (`_add_unique` never exercised by a real duplicate). This increment adds those tests only.

## Write scope

- `_src/tests/test_provenance_query.py` (additive tests)
- this claim file
- `_src/tools/provenance_query.py` **only if** a committed failing test in that file proves a product bug (expected: no)

## Must not

Land; request Acceptance; stamp `Acceptance: ✓`; first-review or stamp 17.03; advance `main`; batch with 17.01/17.02 AE; merge 11.02 / 10.01 / 17 parent / 0037-13; lift 0037-16 STOP; Feature DONE.md; treat INCONCLUSIVE as rejected; treat AUTO007 FAIL as a product defect to fix in `provenance_query.py`; pick review tip `6ed2d7566` onto main; reuse Rhys token.

## Progress

- 2026-08-28T05:00Z: worktree/branch cut from remesured main; implementing AE-4/AE-5 tests.
- 2026-08-28: **[x] follow-up.** Substantive REF `588eee2620f8fa99ed6546abf4b50674927c40e8`. Tests: `python3 _src/tests/test_provenance_query.py -v` → **12/12** (7 prior + 5 AE). `provenance_query.py` **not edited**. Rhys REF `91b848933` untouched; TODO.md heading not rewritten. Did not land, did not stamp Acceptance.
