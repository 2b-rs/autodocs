# Claim — Task `0038-29` (review-finding correction)

- **owner_token:** `agent:kathryn-chakotay:0038-29:20260822T124000Z`
- **Agent:** `Kathryn-Chakotay-20260822T124000Z`
- **Runtime:** zed/claude-opus-5
- **capability_class:** `unprivileged` — direct Git, tests, commits. No runner protocol.
- **Dispatcher:** Projektleiter `kathryn` (lower case)
- **Branch / worktree:** `0038-29` in `.worktrees/0038-29`, from tip `77b6337f0`
- **Role:** Implementer correcting the findings of the rejected integration checkpoint review.

## Write scope (exact)

- `_src/tools/publish_approved_subtree.py`
- `_src/tools/test_publish_approved_subtree.py`
- `docs/pipeline/tools.md`
- `TODO.md` (only the `0038-29` block)
- this claim file

## Explicitly not permitted for this session

No publication, no push, no network. No `Acceptance: ✓`, no integration checkpoint
(`0038-29` carries `Integration review: mandatory`), no `DONE.md` move. No mutation of
the root checkout (`DEC-0044-010`), no `git update-ref`, no movement of `refs/heads/main`.
`_src/publish.sh` and `_src/tools/publish_public_site.sh` stay **byte-identical** — this
session documents them, it does not repair them.

## Baseline

- Pre-mutation `python3 _src/tools/check_integration_hygiene.py --repo .worktrees/0038-29`
  → **PASS**, 104 registered worktrees, exit 0.
- Rejecting review: `Kathryn-Kolos-20260822T115500Z`, privileged integrator, branch
  `review-0038-29-kolos-20260822T115500Z`, commit `536860ce4`, report at
  `docs/campaign-evidence/review-0038-29-20260822/report.md`. Verdict `rejected`;
  checkpoint `Integration review: mandatory` **confirmed**, no downgrade.

## Findings and disposition

| Finding | Severity | Disposition |
|---|---|---|
| F1 — completion evidence claims "0 findings for the two new files" | major, mandatory | **fixed** (evidence line corrected to the measured result) |
| F2 — `tools.md` credits `publish_public_site.sh` with revision fidelity it does not have and omits its defect | major, mandatory | **fixed** (table row corrected + explicit defect note with line reference and the condition under which the tool is correct) |
| F3 — "exit 1 = nothing was published" is untrue on the post-verification path | minor, recommended | **fixed, behaviour + assurance**: new `PublicationIncomplete(Refusal)`; the path now says "the destination WAS modified", writes an `"state": "incomplete"` evidence record with `written`/`removed`, appends a `verify-failed` journal record, and the same treatment covers an `OSError` raised mid-write. Exit code stays `1`. Docstring and `tools.md` now state the single exception explicitly. |
| F4 — refusals originating in the destination report `source ...` | minor, recommended | **fixed**: `collect_regular_files(root, label=...)` threaded through `compute_tree_digest` and `destination_inventory`; destination-caused refusals now say `destination subtree ...` |
| F5 — a pre-existing symlink inside the destination subtree blocks publication, undocumented | minor | **documented** in `tools.md` (fail-closed, intentional, operator must resolve such links first) |
| F6 — dry-run points at an evidence record that need not exist | minor | **fixed**: the remainder hint names the evidence record only when `--evidence` was actually given; otherwise it discloses that the full list is not recorded in this run |
| F7 — private-path guard does not check `--destination-root` | informative, no change requested | **no change** — the reviewer expressly requested none; the caller names the destination deliberately |
| F8 — file permissions are not preserved | informative | **documented** in `tools.md` |
| F9 — local TOCTOU residual risk | informative | **no change** — accepted under the "one operator, one machine" threat model; the F3 fix improves its detectability, because a post-verification failure is now recorded instead of silently evidence-less |

### F3 — why the behaviour was changed rather than only the wording

Both routes were open. Correcting only the assurance would leave a real state — a mutated
destination without any evidence record — that nobody can reconstruct afterwards. This tool
exists precisely because an irreversible external effect must be traceable to what was
approved; a failure mode that leaves the destination changed and produces *no* record is the
one outcome that defeats that purpose. The behaviour change is small (a `Refusal` subclass, an
error evidence record, a journal record) and adds no new success path: nothing that used to
exit `0` exits differently, and every pre-write guard keeps its unqualified "nothing was
written" guarantee. The wording was corrected as well, in the module docstring and in
`tools.md`, so the exception is stated where an operator reads it.

## Measurements taken by this session (not copied from the briefing or the review)

- `python3 _src/tools/check_integration_hygiene.py --repo .worktrees/0038-29` → **PASS**,
  104 registered worktrees, exit 0 (before the first mutation).
- Baseline `python3 _src/tools/test_publish_approved_subtree.py` → **22 tests, OK**, exit 0.
- Baseline `python3 _src/tools/automation_safety.py --json` → **`verdict: PASS`, exit 0**;
  counts `unresolved_critical: 0`, `policy_errors: 0`, `advisory: 38`, `disposed_critical: 24`,
  `findings: 73`. On `_src/tools/publish_approved_subtree.py`: **one** finding —
  `AUTO010`, `severity: high`, `status: advisory`, line 432, symbol `apply_plan`,
  evidence `target.unlink()`. On `_src/tools/test_publish_approved_subtree.py`: **0**.
  These numbers reproduce the reviewer's exactly, which confirms F1 and refutes the
  original evidence line.
- Baseline and post-change `compute_tree_digest()` over
  `/tmp/autodocs-0019-10-preview-20260822T003000Z/export` →
  `7c514686ba7241416dbab340b4cad9abe032e2c6150e807b302efac363d08283`, 2248 files —
  **unchanged by this session's edits**.
- After the change: `python3 _src/tools/test_publish_approved_subtree.py` → **30 tests, OK**,
  exit 0. All 22 original tests still pass; one of them
  (`test_dry_run_sample_is_bounded_and_the_remainder_is_disclosed`) was extended to pass
  `--evidence`, because F6 deliberately changes the message in the no-evidence case, and a
  new test covers that case explicitly.
- `_src/publish.sh` and `_src/tools/publish_public_site.sh`: `git status --porcelain` on both
  paths is **empty** — byte-identical, untouched.

### Own reproduction of the F2 defect

Isolated fixture (temporary repository, deleted afterwards): a revision containing
`score/a.html` and `score/b.html`, then a different revision checked out. Reproducing the
`publish_public_site.sh` mechanism (`git ls-tree -r --name-only <rev>` into the file list,
then `tar -cf - -C <repo> -T <list> | tar -xf - -C <out>`) yields:

```
tar: score/a.html: Cannot stat: No such file or directory
tar: score/b.html: Cannot stat: No such file or directory
tar: Error exit delayed from previous errors.
upstream tar rc=1
```

and an **empty** export directory. The failure is additionally masked: in the pipeline only
the *second* `tar`'s status counts, so the run continues. This is the mechanism the
reviewer described; the 2,248-path observation against the real `0019` tree is cited as the
reviewer's measurement, not claimed as mine.

### Finding reported, not repaired: `automation_safety.py` double-counts an uncommitted change

While measuring after the edit but **before** committing, `automation_safety.py --json`
reported **two** `AUTO010` findings on `publish_approved_subtree.py` (lines 432 and 491) with
identical evidence `target.unlink()`, although the file contains that call exactly once.
Cause: `_read_tracked_sources()` (`_src/tools/automation_safety.py:2649`) scans the Git index
version *and* the worktree version whenever they differ, and `_dedupe()` keys on the line
number, so one physical finding appears twice while a change is uncommitted. This is not a
defect of `0038-29`; it is a measurement artifact any agent will hit when running the gate on
an uncommitted tree. It is reported to the dispatcher rather than silently absorbed. The
authoritative post-change number is therefore taken **after** the substantive commit, when
index and worktree agree.

## Governance note (`DEC-0044-012`)

`docs/pipeline/tools.md` is a **governance artifact** and currently exists only on branch
`0038-29`. It must be carried to `main` by the dispatcher/privileged integrator. This session
did not move `refs/heads/main`, crossed no integration checkpoint, granted no `Acceptance: ✓`
and moved nothing to `DONE.md`.

## Provenance

The full verbatim briefing that authorised this work is reproduced in the substantive commit
message on branch `0038-29`.
