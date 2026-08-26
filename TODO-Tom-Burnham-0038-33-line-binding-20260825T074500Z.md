# Claim: Tom-Burnham-20260825T074500Z — 0038-33-line-binding-correction

owner_token: agent:tom-burnham:0038-33-line-binding-correction:20260825T074500Z

## Assignment

Dispatcher: `tom` (Tom Paris, Team Voyager), 2026-08-25T07:45:00Z, working in
`/Users/tobias.anton/devel/autodocs`, under exact assignment from `jean-luc`
(Team Enterprise) via agent-inbox `1787643582554-60a15526`, thread
`0038-33-line-binding-correction`, 2026-08-25T07:39:42Z.

capability_class: unprivileged
Branch: `0038-33`
Base verified: `d03115278` (tip of `0038-33` at claim time, "Merge updated
0038-14 (0038-10 repair propagated) into 0038-33")
Worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/0038-33`

Write scope: `_src/tests/test_automation_safety.py` (five specified
line-number bindings only) plus this claim file. No other file. No TODO.md
marker changes without stopping and reporting first. No runner_transaction.py
mutation.

## Correction performed

Five `RUNNER_TRANSACTION_ALLOWED_AUTO010` line-number bindings in
`_src/tests/test_automation_safety.py` had drifted from their actual current
lines in `_src/tools/runner_transaction.py`. Updated exactly these five,
symbol name and evidence_sha256 unchanged:

| symbol | old line | new line |
|---|---|---|
| `_atomic_create` | 240 | 277 |
| `Transaction.acquire_lock` | 1698 | 1735 |
| `Transaction.materialize_editor_candidate` | 1839 | 1876 |
| `BranchMergeTransaction._synchronize_worktree` | 3295 | 3332 |
| `_recovery_lease` | 3922 | 3959 |

### Pre-mutation verification (mandatory per briefing §5)

Ran a live `automation_safety.scan_text` over
`_src/tools/runner_transaction.py` before editing (see command below).
Result: all five symbols and their `evidence_sha256` digests matched
exactly, and each reported line matched the "new" value in the briefing's
table (277, 1735, 1876, 3332, 3959). No mismatch found — proceeded with
exactly the five edits as specified.

```
python3 -c "
import sys; sys.path.insert(0, '_src/tools')
import automation_safety as safety
from pathlib import Path
text = Path('_src/tools/runner_transaction.py').read_text(encoding='utf-8')
findings = safety.scan_text('_src/tools/runner_transaction.py', text, 'python')
for f in findings:
    if f.rule == 'AUTO010':
        print(f.line, f.symbol, f.evidence_sha256)
"
```
Output:
```
277 _atomic_create a9585e4f1caf3113aa8a1da53260983471d1e10d5339b4a553f0fcce7a047ea2
1735 Transaction.acquire_lock bbeb1bc976b167dc0d4939d3788858124cb8cfecdc064b4c6bac40cc1f290fd8
1876 Transaction.materialize_editor_candidate 2027934680f43f964b21625c17ce86672422e5584efeaa904d49a4d17baa8d3c
3332 BranchMergeTransaction._synchronize_worktree 2027934680f43f964b21625c17ce86672422e5584efeaa904d49a4d17baa8d3c
3959 _recovery_lease d9bae0d944b115d54df1aa8eb1b10f982d72c3427965fb54b216068970284802
```

### Substantive commit

`928f1ed` on branch `0038-33` (worktree
`/Users/tobias.anton/devel/autodocs/.worktrees/0038-33`). `git diff` against
the parent confirmed only the five integer literals changed (`+5 -5`),
nothing else in the file moved.

### Test result: 122/125 passing, NOT 125/125

`python3 -m pytest _src/tests/test_automation_safety.py -q` →
**3 failed, 122 passed**. The three failures are NOT caused by my edit being
wrong — they are three additional hardcoded line-number lookups elsewhere in
the same test file that reference the *old* (pre-drift) line numbers
directly, outside the `RUNNER_TRANSACTION_ALLOWED_AUTO010` frozenset that was
my exact and only mandate:

- `test_runner_transaction_control_rejects_a_moved_auto010` (line ~1263):
  `next(finding for finding in findings if finding.line == 240)` — still
  looking for line 240, which is now 277.
- `test_runner_transaction_control_rejects_a_renamed_auto010` (line ~1273):
  `finding.line == 1698` — now 1735.
- `test_runner_transaction_control_rejects_changed_evidence_bytes` (line
  ~1285): `finding.line == 1839` — now 1876.

Each raises `StopIteration` because the live scan no longer reports a
finding at the old line.

Per briefing §5 ("do not guess, do not proceed, do not 'fix' it yourself
beyond the five specified line-number edits") and §3 (write scope limited to
exactly the five specified bindings), I did **not** touch these three
additional lookups. Reporting them to Tom rather than guessing/fixing.

### Live automation_safety scan

`python3 _src/tools/automation_safety.py --json` launched as a background
process (full-repo scan, exceeded the 120s foreground timeout in this
environment); result to be appended when it returns, or reported separately
if it does not complete before handoff.

## Scope extension and completion (2026-08-25)

Tom relayed jean-luc's scope extension (agent-inbox `1787644022848-39813957`)
authorizing exactly three more hardcoded `finding.line ==` literal updates in
the same file, for the same three tests already identified above:

| test / lookup | old | new | symbol |
|---|---|---|---|
| `test_runner_transaction_control_rejects_a_moved_auto010` (~line 1263) | 240 | 277 | `_atomic_create` |
| `test_runner_transaction_control_rejects_a_renamed_auto010` (~line 1273) | 1698 | 1735 | `Transaction.acquire_lock` |
| `test_runner_transaction_control_rejects_changed_evidence_bytes` (~line 1285) | 1839 | 1876 | `Transaction.materialize_editor_candidate` |

Before editing, confirmed each lookup still selects the same symbol via the
same mutation-test semantics as before (moved/renamed/evidence-changed
negative tests, each expecting `AssertionError`) — only the literal line
number changes. No digest, symbol, or test-logic change.

Committed separately as `f8f7992` (not folded into `928f1ed`), per Tom's
instruction. `git diff` confirmed only the three literals changed in that
commit.

### All eight literals, taken together

`git diff d03115278 HEAD -- _src/tests/test_automation_safety.py` shows
exactly **8** numeric literal changes across the two commits (`928f1ed` +
`f8f7992`) and nothing else in the file:

- `RUNNER_TRANSACTION_ALLOWED_AUTO010` frozenset (5 entries, `928f1ed`):
  `_atomic_create` 240→277, `Transaction.acquire_lock` 1698→1735,
  `Transaction.materialize_editor_candidate` 1839→1876,
  `BranchMergeTransaction._synchronize_worktree` 3295→3332,
  `_recovery_lease` 3922→3959.
- Three adversarial-test lookups (`f8f7992`), same three symbols as the
  first three frozenset entries above (the moved/renamed/evidence tests
  only exercise those three, not `_synchronize_worktree` or
  `_recovery_lease`): 240→277, 1698→1735, 1839→1876.

Every one of the 8 is a pure line-number update: same symbol name, same
`evidence_sha256` where a digest is present (the frozenset entries; the
three adversarial lookups carry no digest literal of their own — they look
up a `Finding` by line and then operate on whatever digest that live
`Finding` object carries), same test semantics/assertions unchanged. No
symbol was renamed, no digest was altered, no test's expected outcome
(`AssertionError`, `assertEqual`, etc.) was changed.

### Final validation

- `python3 -m pytest _src/tests/test_automation_safety.py -q` → **125 passed**
  (previously 122/125 before the scope-extension commit).
- `python3 -m py_compile _src/tests/test_automation_safety.py` → clean.
- Live full-repo scan: `python3 _src/tools/automation_safety.py --json` run
  to completion in the background (exceeds the 120s foreground timeout in
  this environment; run via `nohup`-style background + completion-marker
  polling). Output at `/tmp/autosafety_full.json` (98.2K), exit code `0`
  recorded in `/tmp/autosafety_full.done`. Parsed result: `"verdict": "PASS"`,
  `0` `policy_errors`. (Note: these are local /tmp scratch paths, not
  repository artifacts; not committed.)
- Diff-check: `git diff d03115278 HEAD -- _src/tests/test_automation_safety.py`
  → exactly 8 numeric literal lines changed, `+8 -8`, nothing else moved.
  `git diff --stat d03115278 HEAD` shows only
  `_src/tests/test_automation_safety.py` (the 8 literals) and this claim
  file changed — no other path touched.

### Final commit SHAs

- `928f1ed` — original five `RUNNER_TRANSACTION_ALLOWED_AUTO010` line
  corrections.
- `f8f7992` — three adversarial-lookup line corrections (scope extension).
- This claim-bookkeeping commit — additive update to `[x]`, see below.

## Status: [x] — implementation complete

All eight line-number corrections applied, verified, and committed across
two path-limited commits on branch `0038-33`. 125/125 tests passing. Live
`automation_safety` scan: PASS, 0 policy_errors. Diff-check confirms no
scope creep. Handed to Tom for handoff to kathryn/belanna. Acceptance review
remains independent (belanna) — not performed or claimed here.
