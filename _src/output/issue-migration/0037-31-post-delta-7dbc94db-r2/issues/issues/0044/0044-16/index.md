---
schema_version: "1.0"
id: "0044-16"
level: "task"
parent: "0044"
state: "closed"
visibility: "internal"
prerequisites:
  - "0044-14"
  - "0044-15"
  - "2026"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1253"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0044-16:0044-14, 0044-16:0044-15 Stop the mandatory hygiene check from blocking unrelated agents on a commit that is merely in flight. Claim: `TODO-Harry-Kira-0044-16-20260822T184500Z.md`; owner_token: `agent:harry-kira-20260822t184500z:0044-16:20260822T184500Z`. REF: `42e80f6e7412616999f42a865e3eefe8c985c85a`; candidate tip `e3561d47b4e2e0ddc4ebbf2a5af1bd8f813ab13a`; previous implementation REF `59e5fd79d1501f21ff08d7f6a305f7f97d37ee0b`. Prior review `a141a493817f57ecf076180ccd2854f20207d0a4` remains append-only `rejected`; corrective independent re-review `4b6db41f5e66958eb62b7d0798f4ff7f952c9e4d` is `accepted`.

## Scope

- **Context (observed live on 2026-08-22, twice within 35 minutes):** `_src/tools/check_integration_hygiene.py` samples **every** registered worktree — 108 at the time — and raises `FOREIGN_STAGED_TREE` whenever one's index differs from its `HEAD`. Under `AGENTS.md` a non-zero exit is a **stop, not a warning**, so any single worktree in that state halts every other agent's pre-mutation gate.
    - **14:47Z:** `Harry-Neelix-20260822T164100Z` could not start `0043-05` because `.worktrees/0038-30` had a divergent index. Its owner (`Kathryn-Icheb-20260822T144500Z`, unrelated Task) was simply mid-commit; it finished at 14:52Z and the same check then returned `PASS`/exit `0` at unchanged 108 worktrees.
    - **15:16Z–15:21Z:** `.worktrees/0038-32` held 8 staged paths during an ordinary editing phase and simultaneously blocked **three** lines: `0044-02` preparation (no branch, claim or proposal could be created), `0044-03` preparation, and the commit of `0043-05` — whose implementer had already regenerated and validated the work (5 pages, `--check` 0 deviations, 16 focused tests green) and could not land it.
    - In all four cases the blocked agent acted **correctly**: it did not touch the foreign worktree and escalated instead of deciding. Nothing was wrong, and the stops were still right under the current rule. That is the defect.
  - **Why it gets worse, not better:** the chance that *at least one* of N active agents is inside the seconds between `git add` and `git commit` grows with N; with an editing phase that holds an index for minutes it approaches certainty. A single instantaneous sample cannot distinguish a commit in flight from an abandoned staged tree — they are byte-identical in that sample. The only countermeasure available today is asking every agent to commit more often, which is coordination overhead standing in for a missing signal.
  - **Explicit scope boundary — read before mutating:** whether an unrelated worktree's staged tree should **block** or merely **advise** is a change to a gate that governs the start, validation and integration of other work units. It therefore meets the canonical `cross-item-blast-radius` predicate and requires a conforming `decision-record@v1` plus an independent Architect scope review **before** that mutation. Adding a re-sample and an age field, without changing what blocks, does **not** meet the predicate and needs no such record — start there if you want progress before the decision lands. Do not quietly convert the finding to advisory as a side effect of "fixing the false positive".
  - **Implementation completion (2026-08-22, `agent:harry-kira-20260822t184500z:0044-16:20260822T184500Z`):** `FOREIGN_STAGED_TREE` candidates are re-sampled once after a shared bounded 2.0-second delay and reported only when their index remains divergent; every persistent finding retains the same blocking code/exit behavior and adds `index_age_seconds`, `index_mtime_utc`, and `resample_delay_seconds`. Hermetic validation: 6/6 tests pass, including transient commit completion (no finding), persistent staged tree (finding remains), deterministic 39,600.000-second/11-hour age with parseable UTC mtime, unchanged `MAIN_WORKTREE_DIRTY`, and unchanged stale-after-ref-move signature. The real default-delay fixture completed in 2.746 s (wall 2.87 s); a full rerun after fail-closed index-stat hardening passed in 13.331 s. Live read-only scan with this ordinary dirty item worktree: PASS across 115 worktrees in 50.61 s. Focused automation safety PASS/0; process-doc reports byte-identical to `main` (29 findings); absent-repository probe returned exit 2. The hard root preflight and all-worktree blocking scope remain unchanged. No acceptance, checkpoint crossing, integration, Feature closure, `DONE.md` move, or `main` advance was performed.
  - **Independent review rejection and rework (2026-08-22):** `Data-Geordi-20260822T205520Z` rejected candidate `904414470af2f84be5c3f93109a1c28379758a3e` at review REF `a141a493817f57ecf076180ccd2854f20207d0a4` (`F-0044-16-GEORDI-01`): shared `asdict()` serialization leaked the three age/re-sample keys as `null` into every non-persistent finding. Rework is active and narrowly removes absent optional keys while retaining them on persistent `FOREIGN_STAGED_TREE`; prior completion and rejection history remain authoritative and append-only until a new correction REF is recorded.
  - **Review correction completed (2026-08-22):** REF `42e80f6e7412616999f42a865e3eefe8c985c85a`. Non-persistent findings now omit `index_age_seconds`, `index_mtime_utc`, and `resample_delay_seconds` instead of serializing them as `null`; persistent `FOREIGN_STAGED_TREE` findings retain all three populated values. Red regression reproduced the leak before the fix; afterward the serialization pair and full 6/6 suite passed. `py_compile` PASS; automation safety PASS/0; missing repository remained exit 2; live hygiene PASS across 128 worktrees in 107.25 seconds. Shared re-sampling, blocking semantics, all-worktree enumeration, `MAIN_WORKTREE_DIRTY`, `STALE_AFTER_REF_MOVE`, and the hard root preflight are unchanged. Re-review remains independent; no Acceptance, checkpoint crossing, integration, `main`, or `DONE.md` mutation was performed.
  - **Integration re-review (2026-08-22, `Data-Geordi-20260822T213740Z`, Geordi persona, privileged Integrator, independent of dispatcher Data and implementer Harry-Kira):** verdict `accepted` against exact candidate `e3561d47b4e2e0ddc4ebbf2a5af1bd8f813ab13a`. An independent negative control proved the rejected candidate leaks all three keys for every non-persistent finding code and the corrected candidate omits them entirely; persistent `FOREIGN_STAGED_TREE` retained all populated metadata and blocking exit `1`. One shared resample, transient disappearance, age `39,600.0`, `MAIN_WORKTREE_DIRTY`, `STALE_AFTER_REF_MOVE`, all-worktree scope, hard root preflight, missing-repository exit `2`, focused 6/6, automation safety, process-doc parity, and a live 130-worktree PASS in 133.76 seconds were reconfirmed. Report: `docs/campaign-evidence/review-0044-16-20260822-data-geordi-r2/report.md`; Review REF `4b6db41f5e66958eb62b7d0798f4ff7f952c9e4d`.
  - **Acceptance:** ✓
    - **Disposition:** `completed`
    - **Accepted by:** `Data-Geordi-20260822T213740Z` (Geordi persona, privileged Integrator)
    - **Authority reference:** `dispatch:Data→Data-Geordi-20260822T213740Z:0044-16-re-review:20260822T213740Z`; verbatim briefing recorded under `DEC-0044-013` in the review report.
    - **Accepted at:** `2026-08-22T21:50:52Z`
    - **Accepted baseline:** `e3561d47b4e2e0ddc4ebbf2a5af1bd8f813ab13a` (substantive correction `42e80f6e7412616999f42a865e3eefe8c985c85a`; original substantive `59e5fd79d1501f21ff08d7f6a305f7f97d37ee0b`)
    - **Contract SHA-256:** `70b84a144ccf1a55bc5c70a8829fa7b0860f9adfa77d1b14ee3f491f6e3b51ad`
    - **Work-product manifest SHA-256:** `0ba1d2bb536bbc2f25ae490a8a86773e77052a62ac2459cabef72db0c6d6c135`
    - **Prerequisite-acceptance SHA-256:** `d5eefefdc766150cb757ab599a46cd46d9351ffc456572f5d5189764f431eccc`
    - **Review REF:** `4b6db41f5e66958eb62b7d0798f4ff7f952c9e4d`
  - **Integration review: mandatory.** **Rationale (provisional — conservative default, not an architect decision):** this touches the control that guards every integration; a false negative here restores precisely the overestimation the `0044-14` acceptance review documented. Set by Projektleiter `kathryn`, who does not set checkpoints; the architect confirms or downgrades it with a recorded justification, at the latest at `0044-08`. Origin: suggestion-log entry of 2026-08-22 in `AGENTS.md` (`db03ccef6`), raised after the first occurrence and promoted to an item after the second.
    - **Architect checkpoint decision (2026-08-24, Architect `seven`, Seven of Nine; recorded per `process-roles.md` §Architect and the `AGENTS.md` checkpoint contract):** **confirmed — mandatory.** The node tunes the gate that governs the start and integration of every other work unit; by declared behavior it meets `cross-item-blast-radius` directly. Its wrong error direction — reporting a genuinely stale foreign tree as transient — silently re-opens the failure class `DEC-0044-010` exists to prevent. The item's own scope boundary already requires a `decision-record@v1` plus architect scope review for any block→advise change; this checkpoint is the review floor for whatever lands, not a substitute for that gate.

## Acceptance criteria

- **AC-001** The check can distinguish transient from stale. At minimum it re-samples a worktree that trips `FOREIGN_STAGED_TREE` after a bounded delay and reports it only if it is **still** divergent, and it reports the offending index's age so a reader can tell "0.4s old" from "11 hours old" without rerunning anything. A genuinely abandoned foreign staged tree still trips the check — proven by a hermetic fixture, not asserted. `MAIN_WORKTREE_DIRTY` and the stale-after-ref-move signature are **not** touched: neither is transient by nature, and weakening them would re-open exactly what `DEC-0044-010` exists to prevent. Exit `2` remains a failure, never a pass

## Definition of Done

Committed with tests for transient-not-reported, stale-still-reported, and the age field; real numbers reported; `docs/pipeline/tools.md` and wherever the check is described state the new behaviour and what remains uncovered; the hard root preflight from `DEC-0044-015` stays required and is restated, not relaxed. If the investigation shows the re-sample cannot be made reliable, that is reported rather than a weaker check shipped.
