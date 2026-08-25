# Claim 0037-15.01

- **owner_token:** `agent:gabriel-book-20260825t090100z:0037-15.01:20260825T090100Z`
- **agent:** Gabriel-Book-20260825T090100Z
- **capability_class:** unprivileged
- **execution_authority:** direct tools; no Acceptance; no checkpoint; no main; no DONE Feature; no push
- **item:** 0037-15.01
- **branch:** 0037-15.01
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/0037-15.01`
- **base:** `dda065a67a5dbfb3469f06d0056e271a3ea5530f` (0037 after 0037-14 merge)
- **startup_review:** Task open at Feature tip; prereqs 0037-06.01 `[x]`, 0037-14 `[x]` on 0037; 0037-17.01 writers present on Feature tip as called library (`_src/tools/provenance_store.py`). Write scope: watermark/reimport tools/tests, disposable temp import roots, provenance run/artifact-set records via 17.01 writers, this claim, 0037-15.01 TODO.md block for `[p]`/`[x]` only.
- **write_scope:** `_src/tools/issue_reimport.py`, `_src/tests/test_issue_reimport.py`, this claim, `TODO.md` 0037-15.01 markers, temp output under test dirs
- **do_not:** mutate 0037-17.03 query APIs or provenance/_views; generated TODO/DONE views; live issues/ except documented atomic promote in tests; 0037-14 importer except as called library
- **next:** closed at `[x]`; product REF `56bf5eb2ae00375f41ec5055d33bedba7121060c`
- **validation:** `python3 _src/tests/test_issue_reimport.py` 7/7 PASS; `py_compile` PASS
