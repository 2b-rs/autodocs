---
schema_version: "1.0"
id: "0038-05"
level: "task"
parent: "0038"
state: "closed"
visibility: "internal"
prerequisites:
  - "0038-05.01"
  - "0038-05.02"
  - "2026"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1664"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0038-05:0038-05.01, 0038-05:0038-05.02 Complete the structural legacy backlog/claim reconciliation editor and its durable transaction integration. REF: 85b6442fa

## Scope

- **Claim (2026-08-17, superseded):** Parent package claimed by privileged agent `Zed` via `TODO-zed-0038-05-20260817-061933-71177f1489a4.md`, `owner_token: agent:zed:0038-05:20260817-061933-71177f1489a4`, base `7d85d4f9b7f2b4fb66af62f278c6d51860da4b02`. This claim predates the actual `.01`/`.02` split resolution below and both Subtasks landed under separate ownership; per `AGENTS.md`'s ownership rules it was stale/superseded and closure was completed under a fresh claim.
  - **Backlog repair (2026-08-17):** The original Task combined a disjoint pure structural planner/single-file promoter with durable multi-file pickup/handoff/finalization integration in `_src/tools/runner_transaction.py`, which is currently owned by foreign active Task `0038-02`. Portable stdlib cannot make multiple independent paths atomically visible, and appropriating that coordinator would violate ownership. The smallest intent-preserving split makes `.01` executable now and gates `.02` on both `.01` and `0038-02`; the parent retains the original complete outcome.
  - **Closed (2026-08-20):** Both Subtasks are terminal (`0038-05.01` REF `ffaf3934796023872eb4a58134865c3daf6f5079`; `0038-05.02` REF `b70238ad0ea186fcf4c28579515b4ec695f048f1`, merged into this closure branch at `69309e732`). Package-level consistency review confirmed all nine `legacy_task_editor.py` typed operations are reachable through `runner_transaction.py`'s single `legacy-editor-candidate-v1` promotion schema via `verify_candidate_for_promotion`; `render_task_closure()` delegates to `lte.parse_backlog` rather than a second parser; `task_bookkeeping_closure.py` is a retired fail-closed stub; and no other competing TODO.md/DONE.md/claim writer exists. Re-ran the full suites with `TMPDIR` outside the macOS `/var` symlink artifact (previously documented at `0038-05.02` closure, not re-litigated): `test_legacy_task_editor` 39/39, `EditorCandidateTransactionTests` 13/13, and the full `RunnerTransactionTests` 48/48 (vs. 41/48 recorded under the symlink artifact) — zero regressions. `automation_safety.py --json` on both files: `verdict: PASS`, zero policy errors. No composition defect found; no source-code fix required. REF: `85b6442fa` (consistency-evidence commit). See `TODO-seven-vorik-0038-05-20260820T192009Z.md` for the complete claim and validation record.
  - **Correction (append-only, 2026-08-25, Integratorin `belanna`):** The "39/39"/"13/13"/"48/48" numbers directly above were obtained, by this closure's own text, with `TMPDIR` relocated **outside** the macOS `/var` symlink specifically to avoid what it called an "environment artifact, not a code defect." That diagnosis was wrong: `0038-05.01`'s independent correction (this reviewer's own finding during this checkpoint, `TODO-Tom-Saru-0038-05.01-correction-20260825T141800Z.md`, merged at `8ddc0fffa`) proves it was a real, live, reproducible bug in `_open_dir_nofollow()`, unrelated to the environment. The composition findings in the paragraph above (nine operations/one schema, no second parser, no competing writer, retired stub) remain independently spot-verified and sound; only the validation-methodology claim is corrected. The record above is left standing, not deleted, per this repository's append-only-correction convention.
  - **Acceptance:** ✓ (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `seven-vorik (0038-05-Commit)`). Abgenommene Baseline `85b6442fa5c2798e2b2485a8108061a5421dbe8d`, gelesen im Licht der obigen Korrektur; Teil der durch Checkpoint `0038-30` induzierten prerequisite-closed Batch. Review-REF `a995f9047`. Komposition-Behauptungen stichprobenartig selbst nachgeprüft (task_bookkeeping_closure.py fail-closed-Stub bestätigt; keine konkurrierende TODO.md/DONE.md-Schreiboperation gefunden). Zugrundeliegender Code jetzt auf main echt grün (nach 0038-05.01-Korrektur), unabhängig von den beiden Subtasks eigenständig bestätigt.

## Acceptance criteria

- **AC-001** The pure editor contract and the durable coordinator integration use one candidate/result schema and operation semantics
- **AC-002** all nine operations are reviewable before mutation, and no free-form or competing authoritative writer remains

## Definition of Done

Both Subtasks are terminal; the complete historical/concurrency/wrong-claim suite passes through planning and the applicable promotion path; unrelated bytes survive; multi-file failures are durably recoverable; and the parent package records consistency evidence with a real REF.
