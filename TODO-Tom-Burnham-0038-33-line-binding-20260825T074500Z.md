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

## Status: reported to dispatcher, not closing claim as [x]

Awaiting Tom's direction on whether the three additional hardcoded
line-number lookups are in-scope for a follow-up correction (would require
write-scope expansion beyond this briefing) or a separate item. No further
mutation performed pending that direction.
