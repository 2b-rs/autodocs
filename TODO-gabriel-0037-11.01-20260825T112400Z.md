# Claim: Subtask 0037-11.01

- owner_token: `agent:gabriel:0037-11.01:20260825T112400Z`
- agent/persona: gabriel, unprivileged Programmer, Team Discovery (this Cursor session)
- capability_class: `unprivileged`
- execution_authority: direct local Shell/Git in this dedicated item worktree; no runner queue
- item/branch/worktree: `0037-11.01` / `0037-11.01` / `/Users/tobias.anton/devel/autodocs/.worktrees/0037-11.01`
- Feature base at start: `722aaa2149c78cf705db411a4142c67d92bb1c3d` (`refs/heads/0037` at claim materialization)
- parent Task branch `0037-11`: absent; branch cut from Feature `0037` per dispatcher briefing (not from a missing parent Task branch)
- prerequisite branches: `0037-05`, `0037-08`, `0037-09` already `[x]` on Feature tip; no additional merge required; merged tips = Feature tip `722aaa2149c78cf705db411a4142c67d92bb1c3d`
- startup_review: `TODO.md` Task `0037-11.01`, `AGENTS.md`, `SANDBOX.md`, `docs/pipeline/branch-workflow.md`, jean-luc `1787656989365-99f3c210`, michael `1787656952849-514cb14d` / `1787656628730-2fcbadfd`
- exact_write_scope (product, after claim REF reported):
  - new/extended renderer and tests under `_src/tools/` and `_src/tests/` (and fixture trees they own)
  - optional generated views under a disposable/candidate root only
  - this claim file on branch `0037-11.01`
  - only the `0037-11.01` Task block in `TODO.md` for `[p]`/`[x]` bookkeeping
- exact_write_scope_correction (2026-08-25, additive; supersedes the four bullets immediately above; does not rewrite authority history):
  - `_src/tools/issue_lists.py`
  - `_src/tests/test_issue_lists.py`
  - `_src/tests/fixtures/0037-11.01/` (single owned fixture-root for issue sources, golden generated lists, summaries, and run manifests; all generated TODO.md/DONE.md/summary outputs for this Task live only under this directory)
  - `TODO-gabriel-0037-11.01-20260825T112400Z.md`
  - `TODO.md` (0037-11.01 Task block bookkeeping only)
- forbidden:
  - repository `TODO.md` / `DONE.md` as generated live authority (render into fixtures/candidate roots only)
  - shared root checkout `/Users/tobias.anton/devel/autodocs`
  - other agents' `TODO-<agent-id>.md`
  - Worf set: `0037-10.01`, parent `0037-17`, `0037-22`, `0037-23.01`
  - Acceptance, Integration-review checkpoint merge, Feature `DONE.md` move, `refs/heads/main`
- external_resources: none
- status: `[p]`; claim `86b5f0ec50df04b2c75a82406bdb817cc8414fc4`; PL packet `99cd6b7e25b859a6c8b6fbd87b865f9eaecf3761`. Product mutation remains stopped until this write-scope correction is committed and its REF reported (jean-luc `1787657166190-24e07120`). Michael `1787657240393-f5c6611a` is coordination; it does not override the exact-path stop.
- next_step: commit this additive write-scope correction; report corrective REF; then implement only the exact paths above.

## Authority provenance (stable across sessions)

Mailbox is not authority. Recorded here so the user answer is reachable without a DEC or inbox-id.

- **Direct current-user answer** (Michael Cursor session, reported; this session did not hear it live):
  - Timestamp: `2026-08-25 13:16 +02:00`
  - User verbatim: `A`
  - Prior user text in that session (reported by Michael): `lass uns 11.01 freigeben. Frag mich.`
  - Michael's decision request: `2026-08-25 13:15 +02`
  - Choice A meaning (Michael operative packet): lift Discovery hold on `0037-11.01`; Discovery claims and implements it; product and tests write only fixtures and candidate/disposable roots; a path that writes the repository `TODO.md` or `DONE.md` fails the assignment; live `TODO.md`/`DONE.md` remain authority until cutover; Worf set unchanged; `0033-04.01` / `0041-02` freeze untouched.
- Coordination (not authority):
  - michael `1787656628730-2fcbadfd` HOLD LIFTED / dispatch briefing
  - jean-luc `1787656665571-2a9bfc5f` wait for exact authority reference
  - michael `1787656952849-514cb14d` authority ID: no inbox id, no committed DEC; dispatch on user text `A`
  - jean-luc `1787656989365-99f3c210` user A is valid; materialize claim with this packet; no product mutation until claim REF reported
  - jean-luc `1787657166190-24e07120` STOP product: write scope not exact; additive correction required
  - michael `1787657240393-f5c6611a` PL packet REF `99cd6b7e2`; product unblocked — recorded, not treated as overriding the exact-path stop

## Exact Task text (Feature tip `722aaa2149c78cf705db411a4142c67d92bb1c3d`)

Implement generated `TODO.md`, `DONE.md`, and open/blocked/unclear/owner summaries.

- **Acceptance criteria:** Render every lifecycle/archive disposition truthfully, including superseded/not-accepted; preserve normative text and criterion IDs; include an unambiguous generated warning plus source/schema/tool/config hashes and content-derived generation ID while linking the volatile execution run only from its external manifest; use deterministic ordering; and make manual divergence, omission, duplicated item, or false completion fail validation.
- **Definition of Done:** Golden and repeated clean runs prove byte determinism and exact counts/IDs/state/text reconciliation for open, terminal, and anomalous fixtures.

## Michael operative packet (verbatim from `1787656628730-2fcbadfd`)

```
DISPATCH 0037-11.01 — bound this briefing:
1. capability class: unprivileged (direct execution; no Acceptance, no checkpoint merge, no DONE.md Feature move). Do not brief sandboxed-grunt if the worker will run Git/tests directly.
2. item: 0037-11.01. Branch 0037-11.01 off Feature 0037 at 722aaa214. Worktree owned by the implementer, not the shared root. Prereqs 0037-05/08/09 are already [x] on that tip; merge any still-unintegrated prerequisite branches per branch-workflow.md.
3. write scope (exact): new/extended renderer and tests under _src/tools/ and _src/tests/ (and fixture trees they own). Optional generated views under a disposable/candidate root. Forbidden: repository TODO.md, DONE.md, TODO-<agent-id>.md except the implementer's own claim on the item branch; no root checkout writes.
4. must not: accept work, cross Integration review: mandatory, move a Feature to DONE.md, claim Worf's set, or spawn further dispatch without a new briefing.
DoD remains the Task text: golden and repeated clean runs, byte determinism, fixture reconciliation.
```

## Assumptions

- This session's `owner_token` is minted here and is not reused for another Task.
- Product code, tests, and live-list generation wait until after the claim commit REF is reported.
- Rendering live repository `TODO.md`/`DONE.md` is out of scope for this Task's write path.
