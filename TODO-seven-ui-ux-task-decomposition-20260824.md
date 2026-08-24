# Claim: ui-ux-task-decomposition-20260824 — Architect decomposition of the review-ready UI/UX baseline

- **Item:** `ui-ux-task-decomposition-20260824` (user-directed activity; no existing `TODO.md` Task — this claim is the coordination record per `AGENTS.md`)
- **Owner:** agent `seven` (Architect, Team Voyager)
- **owner_token:** `agent:seven:ui-ux-task-decomposition-20260824:20260824T084450Z`
- **Claimed:** 2026-08-24T08:44:50Z
- **Capability class:** `unprivileged` (direct Shell/Git; no runner protocol)
- **Execution authority:** Dispatcher `jean-luc`, agent-inbox messages `1787560253082-97b68b3e` (assignment), `1787560276239-4bc0e355` (handoff-tip addendum), `1787560513794-0aa2ecf8` (start-proof demand), thread `ui-ux-task-decomposition-20260824`, citing direct current-user assignment of the UI/UX dossier to Jean-Luc with `seven` as distinct Architect for decomposition.
- **Base:** branch `ui-ux-task-decomposition-20260824` cut from baseline handoff tip `40ceb3d2eb4cd818547833c9f5b9ecb50408bf9a` (differs from reviewed substantive candidate `ae11b1f8beacaaf4a84998ed6f99b2d5cf3533fd` only by one claim line recording Troy R2 closure; requirements bytes remain the reviewed `ae11b1f8b` candidate). Worktree `.worktrees/ui-ux-task-decomposition-20260824`.
- **Review evidence consumed independently:** `review-ui-ux-requirements-baseline-20260824` @ `9896d9d2073c91a9345b7c1f03cce3ffa817cb01` (R2 review-ready, no open finding).

## Assigned scope

Decompose Features F-A..F-O plus F-E0 into bounded, executable Task/Subtask **proposals** with exact prerequisites, write/test scopes, outputs, RQ-UIUX/Q/view coverage, capability/resource needs, risks, recovery, and **exactly one terminal integrating Task per Feature with checkpoint rationale**. Explicitly separate: repo restructuring F-E, ticket modernization F-J/F-M, shared foundations, independently parallelizable work. Preserve D-01..D-06 as unresolved inputs — no implementation contract may silently choose them. Identify cross-item gate scopes requiring `decision-record@v1` plus distinct Architect review.

## Write scope (exact)

- NEW `docs/design/ui-ux-task-decomposition.md`
- Targeted refinements to `docs/design/ui-ux-implementation-roadmap.md` only as required for package boundaries
- NEW `TODO-seven-ui-ux-task-decomposition-20260824.md` (this file)

## Prohibitions (from briefing, restated)

No allocation of real Feature/Task/DEC IDs; no mutation of `TODO.md`, governance documents, production sources, root checkout, or `main`; no acceptance, no integration, no checkpoint crossing, no `DONE.md` move.

## Deliverable / completion contract

Commit the proposal on this branch; report exact tip, files, validation, complete coverage of F-A..F-O + F-E0 and RQ-UIUX/Q/view IDs, cycle/deadlock analysis of the proposed prerequisite graph, and the genuine decisions blocking ID allocation.

## Assumptions and constraints recorded at start

1. Safety hold (jean-luc, `1787553077568-ab0bd2ce`; F-BELANNA-SELF-001): `memory_append` is not used; durable lessons land in this claim/deliverable instead.
2. Portfolio boundary (jean-luc, `1787515913246-1ab2ffb4`): nothing here takes `0044-02`, the approval-protocol redesign, or aggregate `0044` integration; any earlier `seven` line-assignments under Kathryn (`0043-04` scope work → `0044-03`) belong to their owning sessions/coordination and are not appropriated by this claim.
3. benjamin's campaign-roadmap broadcast (`1787526859765-23723082`) addresses Data & Seven for a full architectural breakdown; this claim executes the concrete, review-ready slice of that vision under jean-luc's exact assignment and does not open a parallel free-form breakdown.
4. Related in-flight architect work of this session (separate branch, separate scope): checkpoint-confirmation sweep on `architect-checkpoints-seven-20260823` — 12 provisional `Integration review: mandatory` flags confirmed; to be re-based onto current `main` and handed to the Projektleitung. Not part of this item's write scope.

## Progress log

- 2026-08-24T08:44:50Z — branch + worktree created from `40ceb3d2e`; claim authored; start proof to `jean-luc` follows as first commit is made.
