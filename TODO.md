# TODO — Open Point List

HOW TO USE:

- *Features* are represented as 2nd level Headings.
- New *Features* shall normally be added to the top of list
- Features consist of *Tasks*.
- a *Feature* is considered complete once all of its *Tasks* are complete.
- Complete *Features* shall be moved to DONE.md and marked with a completion date + time. TODO.md and DONE.md must be committed after each completed feature.

- *Tasks* are dashed items, one line per task, with a completion marker. Examples see below
  [ ] - open. No work has been done w/r to this item
  [u] - unclear. No agentic work can currently be performed on this item because user/manager discussion or clarification is required before proceeding.
  [p] - partially implemented. The agent has started work on this item, but it is not yet complete; use this while work is in progress, including across conversations, so agents can determine the next best unfinished item.
  [?] - unknown - we simply don't know. Next step is to look into the repository and decide whether to amend TODO: or promote do [x]
  [x] - executed - task has been completed. If a task is completed, the results shall be checked in and REF: xxxxxx (git hash) shall be added 
- *Tasks* shall have a granularity so that they can be implemented in one go, i.e. without further user interaction. 
- Agents shall keep these markers up to date while working and in conversation hand-offs: set `[p]` once implementation/investigation has started, set `[u]` only when further progress is blocked on user discussion/decision, and avoid leaving active work as plain `[ ]` when a better state is known.

## ID scheme

- *Feature names* are kept consistent in English (translate on introduction if needed).

- Every *Feature* gets a unique **feature ID**: a 4-digit number with leading zeroes, e.g. `0001`. Feature headings are written as `## Feature: XXXX — <name>`.

- Every *Task* within a feature gets a **task ID** `XXXX-YY`, where `XXXX` is the feature ID and `YY` is a 2-digit task number, unique within that feature (e.g. `0001-01`, `0001-02`). Task IDs are rendered in bold right after the checkbox marker, e.g. `- [ ] **0001-01** ...`.

- A *Task* may be split into **subtasks**, identified as `XXXX-YY.ZZ`, where `ZZ` is a 2-digit subtask number unique within that task (e.g. `0001-01.01`, `0001-01.02`).

- *Tasks* and *Features* may declare **prerequisites** — other tasks/features that must be done first. A prerequisite is written as:

  `XXXX(-YY)?:AAAA(-BB)?`

  - `XXXX` — feature ID of the dependent item (the one that has the prerequisite)
  - `-YY` — optional task number of the dependent item; omitted means the whole feature `XXXX` depends on it
  - `AAAA` — feature ID of the prerequisite (the one depended on)
  - `-BB` — optional task number of the prerequisite; omitted means the dependency is on the whole feature `AAAA`

  Examples:
  - `0002:0001` — Feature `0002` as a whole depends on Feature `0001` as a whole.
  - `0002-09:0001` — Task `0002-09` depends on Feature `0001` as a whole.
  - `0002-09:0001-08` — Task `0002-09` depends specifically on Task `0001-08`.
  - `0006-04.02:0006-04.01` — Subtask `0006-04.02` depends on sibling Subtask `0006-04.01`.

  Prerequisites are noted inline in the task/feature text, e.g. `0002-09:0001-08`.

## Feature: 0007 — Database Quality Assurance

### Campaign A — Baseline

- [u] **0007-01** PREREQ: 0007-01:0006 — Freeze corpus and 200-record benchmark (still not freezable: `review.status = needs_review` on all 200 records, `complete_start = null` on many)
  - 2026-08-12: the 12 headingless-but-populated blockers (all `RS_LT_*`) are resolved. `spec_scrape.py`'s new numbered-subsection heading fallback (commit `fdba7e28`) recovers their real headings from the source PDF; `benchmark-draft.json`'s expected values were updated to match and verified against the source (recount confirms 0 headingless-but-populated entries remain). The remaining freeze blockers are exclusively `review.status`/`complete_start` metadata, not extraction-shape gaps.
  - 2026-08-12: manually truthed the two previously called-out "empty-fields" blockers in `_src/tests/fixtures/spec_extraction/benchmark-draft.json`:
    - `RS_SAF_21101` is intentionally an inline citation in prose on pages 9-10 of `AUTOSAR_AP_RS_PlatformHealthManagement.pdf`, not a formal requirement block; `heading = null`, `fields = {}`, and `complete_start = null` are correct ground truth. Added an explanatory review note.
    - `RS_DIAG_04005` on page 15 of `AUTOSAR_FO_RS_Diagnostics.pdf` is a real formal requirement block (`[RS_Diag_04005] Manage Security Access level handling`); replaced the incorrect empty expected values with the actual heading/fields and `complete_start = true`, with a review note explaining the mixed-case source ID.
  - Recount after this truthing: exactly 12 headingless-but-populated benchmark entries remain, all in `AUTOSAR_FO_RS_LogAndTrace` (`RS_LT_00001`, `00002`, `00003`, `00004`, `00008`, `00028`, `00030`, `00031`, `00032`, `00033`, `00035`, `00037`). This cleanly overlaps with the separate TODO item to model dense definition lists as an explicit record shape.

### Definition-precision follow-ups

- [u] **0007-02** Treat dense definition lists (heading inline, no spec-item marker, e.g. RS_PHM_00001..00003 p.21) as an explicit record shape with its own fixtures
  - 2026-08-12: implemented and shipped the `AUTOSAR_FO_RS_LogAndTrace` variant of this shape (numbered subsection line immediately above a bare `[RS_LT_xxxxx]` marker, e.g. `4.2.1.1.8 The LT shall ...` followed by `[RS_LT_00001] ⌈`) as `spec_scrape.py`'s new `_subsection_heading_before` fallback, commit `fdba7e28`. All 12 affected benchmark entries now have correct headings and the recount confirms 0 headingless-but-populated entries remain.
  - NOT yet verified: the originally cited `RS_PHM_00001..00003` example does not appear in `benchmark-draft.json` at all (no matching IDs found), so it's unconfirmed whether AUTOSAR_AP_RS_PlatformHealthManagement uses the exact same shape or a different one. This item stays open until that case (or another concrete instance beyond RS_LT) is located and confirmed handled.

