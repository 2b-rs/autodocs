# Claim — `0038-05.01` correction (symlink-alias regression in `_open_dir_nofollow`)

- `owner_token`: `agent:tom-saru:0038-05.01:correction-20260825T141800Z`
- Agent: `Tom-Saru-20260825T141800Z`, implementer
- Dispatcher: `tom` (Tom Paris), under dispatch from Projektleiterin `kathryn`,
  agent-inbox `1787667291741-0662f663`, thread `0038-05.01`, 2026-08-25T14:14:51Z
- `capability_class`: `unprivileged` (explicitly assigned; direct Git/tests/commits,
  no runner queue)
- Branch: `0038-05.01-correction` (branch names `0038-05.01` / `0038-05` / `0038-05.02`
  already exist in history; a disambiguated correction name was used as briefed)
- Worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/0038-05.01-correction`
- Base: `main` @ `28d7a00918498685b1fc13b711840df415142ecf` (measured 2026-08-25)
- Write scope: `_src/tools/legacy_task_editor.py`, `_src/tests/test_legacy_task_editor.py`,
  this claim, `TODO.md` (line-wise append only)

## Nature of the claim

This is a **new correction claim**, not a resumption of the original `0038-05.01`
implementation claim. Item `0038-05.01` is already `[x]` on `main` (REF
`ffaf3934796023872eb4a58134865c3daf6f5079`); this claim repairs a live, twice-verified
regression inside its work product. No acceptance state is touched.

## Defect

`_src/tools/legacy_task_editor.py:1413` `_open_dir_nofollow()` descended from `/`
component by component and opened **every** component with `O_NOFOLLOW`
unconditionally. On macOS `/var` is a symlink to `/private/var`, so any path below
`/var` — which includes every `tempfile.mkdtemp()` result — failed with:

```
NotADirectoryError: [Errno 20] Not a directory: 'var'
```

Reproduced independently by `belanna` and by `kathryn` against `main`@`28d7a0091`,
and reproduced again here on the correction branch before the fix.

**Measured baseline on `main`@`28d7a0091`:** `11 failed, 41 passed` in
`_src/tests/test_legacy_task_editor.py` (52 tests). The "39/39" figure quoted in the
`0038-05` closure note was obtained with `TMPDIR` relocated outside the `/var` alias —
a documented workaround, not a fix; the suite has since grown to 52 tests.

`_src/tools/runner_transaction.py` had already fixed the identical defect under Task
`0038-10` (`_path_is_relative_to()` at line 190, `current_physical` tracking at lines
213 and 231–237). The fix was never propagated to the sibling file, which had neither
mechanism.

## Correction

Ported the `0038-10` pattern verbatim in shape, adapted only for this function's
extra `create=True` mode:

- added `_path_is_relative_to()` helper (mirrors `runner_transaction.py:190`);
- track `current_physical`, the `realpath` of the prefix descended so far, starting
  at `realpath("/")`;
- on `OSError` with `errno.ENOTDIR`/`errno.ELOOP`, `lstat` the component; if it is a
  real symlink, resolve its target and follow it **only** if the resolved target is
  still under `current_physical` — otherwise re-`raise` the original error;
- `create=True` `mkdir` behaviour is unchanged and sits ahead of the same guard, so
  the escape path cannot be laundered through directory creation.

`O_NOFOLLOW` is retained on every component; nothing is followed unconditionally.
`_src/tools/runner_transaction.py` was **not modified** — out of scope, already correct.

## Evidence

- Substantive fix: `2539db6bf`
- Tests + claim: see branch tip.
- Full suite after fix: **54 passed, 0 failed** (52 pre-existing + 2 new).
- `/var` regression test:
  `OpenDirNofollowTests::test_path_below_symlinked_system_directory_opens` — opens a
  raw `tempfile.mkdtemp()` path (traverses the `/var` alias), asserts the descriptor
  is a directory with the expected inode, and drives `_atomic_write()` end to end
  through the same path. Falls back to an explicitly constructed in-tree alias on
  platforms without the OS alias, so the contract is tested everywhere.
- Adversarial symlink-escape test:
  `OpenDirNofollowTests::test_escaping_directory_symlink_is_still_refused` — builds a
  real escape (`permitted/escape -> outside/`), asserts `_open_dir_nofollow()` raises
  `OSError` (`ENOTDIR`/`ELOOP`), asserts the create-mode `_atomic_write()` path is
  refused too and plants nothing outside, and keeps a positive control that a
  non-escaping sibling still opens.
- **Fault injection proving the escape test has teeth:** with the guard line
  `if not _path_is_relative_to(resolved_target, current_physical): raise` removed,
  the escape test fails:

  ```
  >           editor._open_dir_nofollow(escape / "secret")
  E           AssertionError: OSError not raised
  _src/tests/test_legacy_task_editor.py:1487: AssertionError
  FAILED ...::test_escaping_directory_symlink_is_still_refused
  1 failed, 1 passed
  ```

  The injection was applied to a working copy and reverted in the same shell
  invocation; `git diff --stat` on the tool was empty afterwards and the full suite
  re-ran at 54 passed. Nothing injected was committed.

## Not done / out of scope

- No `Acceptance: ✓` created, altered or removed; no reviewer role assumed.
- Integration checkpoint not crossed — belongs to `belanna`.
- `refs/heads/main` not moved; `DONE.md` untouched; root checkout never written to.
- `runner_transaction.py` untouched.
- No `memory_append` (projectwide safety hold).
