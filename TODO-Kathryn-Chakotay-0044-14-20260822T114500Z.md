# Claim — Task 0044-14

- `owner_token`: `agent:kathryn-chakotay-20260822t114500z:0044-14:20260822T114500Z`
- `task`: `0044-14`
- `status`: `[x]` implementation complete on branch `0044-14`; governance transfer to `main` pending Projektleitung. Ownership lease ended.
- `capability_class`: `unprivileged`
- `execution_authority`: Direct Git, scripts, and tests permitted. No acceptance, no crossing the mandatory integration checkpoint, no merge to `main`, no `DONE.md` move, no `run.sh`.
- `dispatcher`: `kathryn` (Projektleiter)
- `branch`: `0044-14`
- `worktree`: `/Users/tobias.anton/devel/autodocs/.worktrees/0044-14`
- `predecessor`: `Data-Miles-20260821T195500Z` (session lost on `Data` restart; claim released by kathryn 2026-08-22, recorded in `TODO.md`). Resumed at tip `f3f59e01b`; nothing restarted.
- `base_discovery`: branch tip `f3f59e01b`, based on `main@8f0726aa7`. Merged current `main` (`6a688283b`) into the branch as merge commit `407c231ce` so the governance prose is written against current text. One conflict, in `TODO.md` line 216 only (marker/claim line for `0044-14`); resolved in favour of `main`'s released-claim text, marker set to `[p]` with this claim.
- `merged_prerequisite_branches`: none declared (`0044-14` has no `PREREQ`); `main@6a688283b` merged as above.
- `write_scope`: `AGENTS.md`, `docs/pipeline/branch-workflow.md`, `docs/pipeline/tools.md`, this claim, and `TODO.md` only for the `0044-14` marker/history — all on branch `0044-14`. The root checkout was not written to.
- `execution_scope`: local worktree, plus a throwaway venv at `/tmp/venv-0044-14` for `pytest`. No network beyond `pip install pytest`, no credentials, no runner.

## What was already done (Miles, unchanged)

- `_src/tools/check_integration_hygiene.py` (194 lines) and `_src/tools/test_check_integration_hygiene.py` (96 lines), commit `11d3498e8`; evidence note `66aedc512`; coordination blocker `f3f59e01b`. Reviewed, not rewritten.

## What this session added

- `docs/pipeline/branch-workflow.md`: three new sections — *Where agents mutate: item-owned worktrees only* (root checkout not written to; confirmed mechanism; the `DEC-0044-015` advance procedure), *Pre-integration hygiene check* (invocation, exit codes, finding table, the two honest limitations), *Preserved snapshot tags and recovery* (all eight current `preserved/*` tags with commit and content, retention rule, recovery commands). The Feature-integration procedure gained the hygiene check as step 2 and step 6 now names the `DEC-0044-015` root advance instead of an unqualified merge.
- `AGENTS.md`: new subsection *Agents mutate only in item-owned worktrees; the root checkout is not written to*, four numbered rules (worktree-only mutation; `update-ref` prohibited and how `main` is advanced; run the hygiene check as a hard gate; `preserved/*` retention), pointing at `branch-workflow.md` for detail.
- `docs/pipeline/tools.md`: new section *Integrations-Hygieneprüfung* registering `check_integration_hygiene.py` with purpose, invocation, exit codes, the two limitations, and the test file.

## Validation (real numbers)

- `pytest _src/tools/test_check_integration_hygiene.py -v` in `/tmp/venv-0044-14` (pytest 9.1.1, Python 3.14.7): **3 passed, 0 failed** in 4.89s.
- `python3 -m unittest test_check_integration_hygiene -v` from `_src/tools/`: **Ran 3 tests, OK** (this is the invocation documented in `tools.md`; it requires cwd `_src/tools/` because the test imports the module by bare name).
- Live read-only run `python3 _src/tools/check_integration_hygiene.py --repo .`: `PASS`, EXIT=0, 94 registered worktrees. Confirms kathryn's 2026-08-22 cleanup held.
- `process_doc_doctor.py --json`: 30 findings on this branch, 30 findings on `main` baseline — no regression, and none of the 30 concern the edited files.

## Critical review of the tool against the prose (as instructed)

Two gaps were found and are stated in the prose rather than written around:

1. **The check compares index against `HEAD` only.** A worktree whose index matches `HEAD` while its *files* diverge produces **no finding**. That is the exact residual root state kathryn reported on 2026-08-21 09:21Z (index cleared, 127 files still stale) — the tool alone would have called it `PASS`. The prose therefore never claims the check proves the root is clean; it requires the `DEC-0044-015` root preflight (`git diff --quiet`, `git diff --cached --quiet`, `HEAD == refs/heads/main`) *in addition*, and says explicitly that neither replaces the other.
2. **`FOREIGN_STAGED_TREE` fires on ordinary live work.** Any agent staging in its own worktree trips it. The prose states it is not an accusation but a quiescence requirement, and that resolution belongs to the owner — never a reset by the integrator.

Neither is a defect in Miles' tool; both are limits that the prose would have misrepresented if written from the acceptance criteria alone.

## Governance handover — REQUIRED, not done here

`AGENTS.md`, `docs/pipeline/branch-workflow.md` and `docs/pipeline/tools.md` are governance artefacts under `DEC-0044-012` and belong on `main`. They are committed on branch `0044-14` and are **not** carried to `main` by this session. `TODO.md` bookkeeping likewise. `0044-14` carries `Integration review: mandatory`; this session crossed no checkpoint, moved no ref, and touched no foreign claim or worktree.

## Progress

- 2026-08-22T11:45:00Z — Announced, read the full inbox (9 messages), reused the abandoned-but-clean `.worktrees/0044-14` rather than creating a second checkout of the same branch (Git permits only one). Merged current `main`, resolved the single `TODO.md` conflict, wrote the three governance texts, ran the tests and the live scan, recorded the two tool/prose gaps above.

## User-authored prompt provenance (verbatim)

The triggering instruction was a dispatcher briefing from `kathryn`, not a direct user prompt. Its operative content, verbatim in the relevant part:

```
Dein Auftrag: das Offene fertigmachen
1. Prosa-Verankerung. AGENTS.md und docs/pipeline/branch-workflow.md muessen sagen, dass Agenten
ausschliesslich in vorgangseigenen Worktrees mutieren und der Root-Checkout nicht beschrieben wird,
und die Hygienepruefung als Schritt der Integrationsprozedur benennen.
2. Registrierung in docs/pipeline/tools.md
3. Den bestaetigten Mechanismus dokumentieren.
4. preserved/*-Tags dokumentieren.
5. Tests laufen lassen.
6. Bookkeeping.
Auflagen: Miles' Werkzeug ist gut, aber pruef es kritisch, bevor du es verankerst: Deckt sein
Verhalten das ab, was der Prosatext behaupten wird? Wenn Werkzeug und Text auseinanderlaufen,
sag es mir, statt den Text passend zu schreiben.
```

The user prompt that originated this line of work is recorded in the predecessor claim `TODO-Data-Miles-0044-14-20260821T195500Z.md`.

- 2026-08-22T12:20:00Z — Terminal. Commits on `0044-14`: merge of current `main` `407c231ce`; substantive governance prose `649db737b`; bookkeeping `[x]` `f970f1674`. Working tree clean, nothing uncommitted. Root checkout verified untouched (`HEAD` `6a688283b`, empty index, no unstaged tracked change). Deferred-successor recheck: only `0044-08` names `0044-14` as a prerequisite and it is `[ ]`, not `[d]` — no state change owed. Scratch venv `/tmp/venv-0044-14` is disposable and outside the repository. Reported to `kathryn` via agent-inbox, naming the three governance files to be carried to `main`.
