# TODO-perplexity-0037-02.02-a4c7f92e6d18.md — active claim

## Claim identity

- `task_id`: 0037-02.02
- `feature_id`: 0037 — Git-Native Issue Store, Provenance Graph, and Backlog Migration
- `agent`: perplexity (SANDBOXED AGENT PERPLEXITY)
request_id: d18b4f6e93c7
owner_token: agent:perplexity:0037-02.02:d18b4f6e93c7
base_commit: 4b0d7e61ba682ac12bbdbfd1f82cd38733e83ae2
- `claim_opened`: 2026-08-16 (Europe/Berlin)
- `state`: [x]

## Why this Task was self-selected

Per `AGENTS.md` rule 3, scanned `TODO.md` top to bottom for the first open Task with terminal
prerequisites now that `0037-02.01` is `[x]`. `0037-02.02`'s only prerequisite
(`0037-02.02:0037-01`) is satisfied, and it is the first such eligible item in file order.

## Task text (verbatim extract from TODO.md at claim time)

- [ ] **0037-02.02** PREREQ: 0037-02.02:0037-01 Define the constrained Markdown profile and
  stable acceptance-criterion lifecycle in `docs/pipeline/issue-store.md`.
  - **Acceptance criteria:** Normative sections are `Goal`, `Scope`, `Acceptance criteria`,
    and `Definition of Done`; informative findings/history are structurally separate.
    Criteria use item-local `AC-NNN`: append-only allocation, no reuse/renumbering, retained
    withdrawal tombstones, same-intent edit retention, new-ID supersession for changed
    intent/verification, and new-ID plus `derived-from` when moved. Define canonical
    criterion refs, insertion/deletion/move/text-edit algorithms, source locators,
    Unicode/multiline/size rules, and migration assignment by legacy document order.
  - **Definition of Done:** Review-ready valid/invalid Feature, Task, and Subtask Markdown
    fixtures include insert, edit, withdraw, supersede, move, and deterministic legacy
    migration cases; each operation has one expected normalized result.

## Important note on target file

The Task text names `docs/pipeline/issue-store.md` as the target, but that file already
exists (created by Task `0037-01`) and is scoped to paths/identity/authority, not Markdown
body structure/AC lifecycle. Rather than overwrite or awkwardly merge unrelated content,
this claim will ADD a new normative section to the existing `issue-store.md` (matching how
`0037-02.02`'s prerequisite `0037-01` already left room via its §10 "Offene
Anschlusspunkte"), keeping `0037-01`'s existing content untouched. This is recorded here as
a scope decision, not silently — if this is wrong, it is trivial to instead create a
separate file and the drift will show clearly in the diff.

## Intended write scope

- This claim file
- `TODO.md` — only the `0037-02.02` marker and its own claim/progress bullets
- `run.sh` — this claim's runner requests only
- `docs/pipeline/issue-store.md` — APPEND a new section only; no edits to existing §1–§10
- `issues/_schema/fixtures/markdown-profile/` — new subdirectory, valid/invalid Markdown
  fixtures for insert/edit/withdraw/supersede/move/migration cases

## Progress log

- 2026-08-16 — Selected `0037-02.02`; created this claim.
- 2026-08-16 — Marked `0037-02.02` `[p]` in `TODO.md`. Appended a new §11 section
  ("Constrained-Markdown-Profil und AC-Lifecycle") to `docs/pipeline/issue-store.md` without
  modifying its existing §1–§10; renumbered the old §10 to §12. Covers: normative section
  order (Goal/Scope/Acceptance criteria/Definition of Done) vs. informative sections;
  AC-NNN append-only allocation with no reuse/renumbering; withdrawal tombstones;
  same-intent edit retention; supersession with new-ID + `supersedes` back-reference; move
  with new-ID + `derived-from` and atomic two-item commit requirement; canonical
  cross-item criterion refs (`<item-id>#AC-NNN`); the insert/edit/withdraw/supersede/move
  algorithm; source locators; Unicode/multiline/size rules; deterministic legacy-migration
  assignment by document order.
- 2026-08-16 — Created all 12 declared fixtures under
  `issues/_schema/fixtures/markdown-profile/`: valid Feature-minimal, valid Subtask-minimal,
  valid Task-insert, valid Task-edit (same-intent), valid Task-withdraw (tombstone + ID
  never reused), valid Task-supersede, a valid move pair (source tombstone +
  destination derived-from, explicitly noted as requiring one atomic commit), valid
  deterministic legacy-migration (document-order AC-NNN split), and three invalid cases:
  reused withdrawn AC ID, wrong normative-section order, and illegal AC-ID renumbering
  (the latter documented as requiring prior-committed-state context to detect). Verified
  all 12 files present via directory listing.
- 2026-08-16 — Discovered HEAD (`4b0d7e61ba682ac12bbdbfd1f82cd38733e83ae2`, request
  `a4c7f92e6d18`). Minted commit request `d18b4f6e93c7`, published the commit script (same
  proven `grep -qF -e` pattern), executed cleanly on the first attempt.
- 2026-08-16 — **Task closed.** Substantive commit `55abebbb5a4f251da5dc07c6077082d0c5e03fa3`
  (13 paths: modified `issue-store.md` + 12 new fixtures); bookkeeping commit
  `428d308b61583cbf34edd06d23a0b8a9563d38ec` (`TODO.md` only, `REF:` recorded).
  Independently re-verified via fresh grep that `TODO.md` line 113 now reads `[x]
  **0037-02.02** ... REF: 55abebbb5a4f251da5dc07c6077082d0c5e03fa3`. Evidence retained under
  `logs/backlog-bookkeeping-and-commit/0037-02.02-d18b4f6e93c7/`. Definition of Done
  satisfied: review-ready valid/invalid Feature/Task/Subtask fixtures cover insert, edit,
  withdraw, supersede, move, and deterministic legacy migration, each with one declared
  expected normalized result. Singleton runner slot confirmed absent after this run.
