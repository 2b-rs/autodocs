---
schema_version: "1.0"
id: "0044-17"
level: "task"
parent: "0044"
state: "open"
visibility: "internal"
prerequisites:
  - "0044-14"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1279"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

PREREQ: 0044-17:0044-14 Make accepted claim terminality explicit and establish fleet-owned worktree cleanup. Claimed via `TODO-data-0044-17-worktree-lifecycle-20260828.md`, `owner_token: agent:data:0044-17:worktree-lifecycle-20260828`, base `b42db62287c203112ded6c326fa165a7f4ee7131`. REF: `635b9c810dc9fc2ed602116dbd13fba39c2b634d`.

## Scope

- **Implementation completion (2026-08-28, `agent:data:0044-17:worktree-lifecycle-20260828`):** Accepted-item bookkeeping now finalizes only exact `task_id`/`item_id` claims by byte-identical `TODO-*` → `DONE-*` rename; explicit owner cleanup verifies an exact accepted authority ref, clean/unlocked/process-free state and a durable exact item branch; the periodic fallback additionally requires `main` reachability and ignores historical prerequisite claims as leases. Branches/tags are never deleted and no existing live worktree was removed. Adjacent consumers recognize terminal provenance and the publisher excludes it. Focused validation: worktree lifecycle 32/32, Doctor 59/59, Editor 54/54, Publisher 12/12; process-doc finding set equals baseline; live Doctor has no `0044-17` finding. Candidate tip after merging current `main`: `99993cb123d15710fcd346444724e179a726cbaf`.
  - **Integration review:** **mandatory.** **Rationale (Architect):** This mechanism deletes checkout directories. Independent review must falsify every safety gate and confirm that branches, tags, claims, dirty data, and foreign worktrees remain intact.

## Acceptance criteria

- **AC-001** Recording current `Acceptance: ✓` for an item renames only that item's root claim artifacts from `TODO-*` to byte-identical `DONE-*` paths and refuses collisions or ambiguous/missing item identity. The item owner can explicitly remove its own clean, unlocked worktree only after the accepted state and durable item-branch tip are verified
- **AC-002** the operation removes neither branch nor tag. A periodic fallback considers only registered worktrees below the configured root whose branch is an exact item ID, whose exact-item claims are terminal, whose tree is clean and unlocked, and whose HEAD is reachable from `main`
- **AC-003** unsafe or ambiguous candidates are surfaced and retained. Historical prerequisite claims do not masquerade as live leases. No existing worktree is removed during implementation

## Definition of Done

Hermetic tests prove exact-item rename, unrelated-claim preservation, collision refusal, self-cleanup refusal/approval, branch retention, fallback removal of a safe candidate, and retention of dirty, unmerged, unaccepted, active-claim, locked, outside-root, and current-target worktrees. The completion and Feature-integration instructions name the responsible fleet member and the explicit cleanup/fallback commands.
