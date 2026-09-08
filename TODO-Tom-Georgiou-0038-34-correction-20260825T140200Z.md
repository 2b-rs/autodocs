# Claim — Task 0038-34 correction (post-`[x]` finding repair)

- `owner_token: agent:tom-georgiou:0038-34:20260825T140200Z`
- `capability_class: unprivileged`
- `execution_authority`: direct Git/tests/commits in own worktree; no runner queue.
- Worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/0038-34`; branch `0038-34`.
- Dispatcher: `tom` (Tom Paris). Predecessor implementer: `Tom-Sisko-20260825T091500Z`
  (session went silent ~3.5 h mid-edit; WIP secured by the dispatcher as `f71faa36a`).
- Base at takeover: `f71faa36a` (WIP), on top of `9bcf87edb` (`[x]` bookkeeping).

## Scope

Write scope, exactly as briefed:

- `_src/tests/test_adversarial_evidence.py`
- `docs/campaign-evidence/0038-34-analysis/completion-evidence.md`
- `TODO.md` (line-wise append only, at the existing `0038-34` entry)
- this claim file

Explicitly **not** done: no acceptance credit created/altered/removed; integration
checkpoint not crossed (belongs to `belanna`); `refs/heads/main` untouched; `DONE.md`
untouched; root checkout never written to; no `memory_append`; no policy-JSON
disposition suppression.

## Finding being repaired

Integrator `belanna` measured `automation_safety.py` against the actual candidate
`9bcf87edb` rather than against its completion evidence, and found **FAIL, 3 unresolved
critical findings**, all in `_src/tests/test_adversarial_evidence.py`: line 175 `AUTO010`
(leaking `mkdtemp()` fixture dir), lines 205/221 `AUTO001` (unchecked mutating
`subprocess.run` against the tool's own CLI). No existing disposition covered them. This
falsified the Task's own §5 claim of "zero findings in either file this Task adds".

## Progress log

1. Verified `f71faa36a` contents. Sisko's mechanism-(b) fixture rewrite
   (`TemporaryDirectory()` + `addCleanup`; in-process `mod.main(argv)` via `_run()`;
   new `test_findings_exit_one`) confirmed present. Kept the mechanism; did not switch.
2. Reproduced the failure: `test_malformed_input_exits_two_and_never_passes`,
   `AssertionError: 0 != 2`. 1 failed, 21 passed.
3. **Diagnosis — neither the tool nor the assertion was wrong.**
   `check_adversarial_evidence.main()` does `return 2` in its `except (OSError, ValueError)`
   branch; source and bytecode disagreed. `dis.dis(mod.main)` showed
   `LOAD_CONST 0 (0); RETURN_VALUE` at line 350 where `inspect.getsource` showed
   `return 2`. The module was loading from a **stale cached `.pyc`** under macOS's shared
   cache prefix (`~/Library/Caches/com.apple.python/...`). CPython validates a cached
   `.pyc` on the source's *(mtime, size)* pair only, and two revisions collided exactly:
   `src mtime 1787654168 size 12725` == recorded pyc header. An identical copy of the
   source at a fresh path returned `2`.
   Why it appeared only now: the subprocess harness ran the tool as `__main__`, which
   CPython never loads from the bytecode cache. Going in-process traded that away silently.
4. **Fix, inside write scope:** `_load_tool_from_source()` in the test file compiles the
   tool's source directly instead of importing it, restoring the always-from-source
   property. `_src/tools/check_adversarial_evidence.py` **not** modified — it was correct;
   no scope widening was needed or taken.
5. **Fault injection** (this Task's own rule applied to its own fix): forged a `.pyc` from
   a mutated source (`return 2` → `return 0`) stamped with the real source's
   *(mtime, size)* header. Control (plain `import`): `rc= 0`, original failure reproduced.
   Candidate (`_load_tool_from_source()`): **22/22 pass**. Poisoned artifact removed after.
6. Validation, final:
   - `python3 -m py_compile _src/tests/test_adversarial_evidence.py` → clean
   - `python3 -m pytest _src/tests/test_adversarial_evidence.py -q` → **22 passed**
   - `automation_safety.py --json --path _src/tests/test_adversarial_evidence.py` →
     **PASS**, `findings: 0`, `unresolved_critical: 0`, `policy_errors: 0`
7. Appended §5.1 to `completion-evidence.md`, **append-only**: the original false claim in
   §5 limit 1 is left verbatim and visible; the correction is appended beneath, naming what
   was claimed, that `belanna` falsified it by measuring the candidate rather than the
   report, the real finding set, the chosen mechanism and why disposition-suppression was
   rejected, the coverage tradeoff, and the final verified state.

## Known limit surfaced to the checkpoint reviewer

The in-process `CliFixtures` harness does not cover the `raise SystemExit(main())` line in
`__main__`, nor real process isolation. Recorded in the `CliFixtures` docstring and
restated in `completion-evidence.md` §5.1 so the reviewer does not have to find it in the
source. It is a real coverage reduction accepted in order to remove two correct findings.

The repo-wide `automation_safety` `FAIL` (the `0038-16` disposition expiry and the 22
pre-existing shell findings) is unrelated to this Task, unchanged, and still not repaired
here. Only the attribution clause was false; that part of §5 limit 1 stands.

## Disposition

Correction complete. Task stays `[x]` from `9bcf87edb`; no acceptance semantics reopened.
The mandatory integration checkpoint remains open and belongs to `belanna`.
