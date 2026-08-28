# Claim: 0037-11.02 AE-4+AE-5 follow-up

- **owner_token:** `agent:tilly-0037-11.02-ae45-20260828:0037-11.02-ae45:20260828T082900Z`
- **mailbox:** `tilly-0037-11.02-ae45-20260828`
- **persona:** Sylvia Tilly, unprivileged Programmer (not gabriel, not Joann, not a dispatcher)
- **capability_class:** `unprivileged`
- **execution_authority:** direct Git/tests in the item-owned worktree; not runner; not privileged
- **git author on this host:** commits were created as `gabriel <gabriel@discovery.starfleet.network>` (host/Cursor user identity). **Persona is Tilly**; not dispatcher gabriel; not Joann tokens `agent:gabriel-joann-20260825t082200z:0037-11.02:20260825T082200Z` or `20260825T081500Z`. Pre-cut `main` tip author was `geordi`; do not confuse with this session's committer.
- **item:** 0037-11.02 AE-4+AE-5 follow-up (additive named tests only)
- **branch:** `0037-11.02-ae45-tilly-20260828`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/0037-11.02-ae45-tilly-20260828`
- **base:** remesured `refs/heads/main` = `c27b8001fcd7b6a504aaf7fe36c481711d5e9d81` (exact AWARD pin; no drift; 11.02 AE scope kept)
- **write scope:** `_src/tests/test_issue_views.py`; this claim. No new fixtures (direct calls to `_archive_status` / `_reject_browser_keys` / `build_catalog` / `build_graph`).
- **must not:** product edits; `Acceptance: ✓`; advance `main`; first-review; Feature 0037 `DONE.md`; 0037-16 STOP; 0019/0041/0044/0047; land 10.01; spawn subagent; `memory_append`; tidy `logs/agent-memory/**`; merge `472fcbeb5`/`e98ee5fef`/`1e281456a`; fold Tuvok `19b3328ca`/`390cac6bf`; land this follow-up.
- **Joann REF on TODO heading:** not overwritten.

## Disposition: implementation complete `[x]` (follow-up; do not land)

- **product SHA:** `e83281b2be14b64625239360076b0072524df52e`
- **bookkeeping SHA (claim body):** `36ba1e76c0080c20d81541a1736c4189643e3800`; git-author disclosure may follow in a third commit on this branch
- **`issue_views.py` blob:** `d21d4a4dc41e50901e28e6d0a4b29bbb21698b34` (unchanged; STOP not required)
- **Belanna:** `65321285a` INCONCLUSIVE — AE-4/AE-5 gaps closed in tests only

## Validation (actually run)

```
/tmp/autodocs-0037-08-venv-julian/bin/python --version
Python 3.9.6
/tmp/autodocs-0037-08-venv-julian/bin/python -m unittest _src.tests.test_issue_views -v
Ran 17 tests in 16.652s
OK
```

New tests: `test_archive_status_*` (4), `test_reject_browser_keys_*` (3), `test_catalog_and_graph_order_and_id_dedup_property` (1).

AE-5 executed case count: `6! + 1! + 7! + 7! + 7` = `720 + 1 + 5040 + 5040 + 7` = **10808** (asserted in-test). Oracle: catalog sorted by `(id, source.path)` and unique ids; `source_sha256` follows sorted paths; graph nodes one-per-id sorted by id; edges sorted by `(source, kind, target)`. Domain: exhaustive permutations of this fixture's parsed/malformed/source_files/catalog items plus seven duplicate-id injections. Seed: none.

## AE-4 adjacency (named)

1. Closed-only dispositions `completed`/`wontfix`/`superseded`/`duplicate`/`cancelled` with `state==closed` → return that literal.
2. Same five with `state` open/`in_progress` → `None` (closed guard).
3. `archived-not-accepted` with open or closed → always that literal (first branch).
4. Unknown disposition / malformed / missing closure → `None`.
5. All 11 `BROWSER_KEYS` raise at `$` and at `$.wrapper[0]`.
6. `fillcolor` is not a member and does not raise.

## Not done (on purpose)

No land. No TODO.md heading REF overwrite. Dispatcher/paul land later.
