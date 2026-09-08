---
schema_version: "1.0"
id: "0044-13"
level: "task"
parent: "0044"
state: "closed"
visibility: "internal"
prerequisites:
  - "0044-12"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1227"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
  - id: "AC-004"
    status: "active"
  - id: "AC-005"
    status: "active"
---

## Goal

PREREQ: 0044-13:0044-12 Implement the `reference-transaction` hook as the early-detection layer. **REF:** `3818eed3430154a34021f5cb9a242f70c760e89f`. Claim: `TODO-benjamin-0044-13-20260829.md`.

## Scope

- **Integration review (2026-08-29, Integrator `obrien`, independent of Implementer `benjamin`):** Checkpoint passed; reference-transaction hook and documentation integrated. Review REF: `f95e331d55653db3c6046e7f8d3fa8f5c3da4ae9`; Review evidence: `docs/campaign-evidence/0044-13/integration-review-obrien-20260829.md`. Task Acceptance deferred pending prerequisite `0044-12` closure.
  - **Implements:** `DEC-0044-009`.
  - **Context:** Verified in isolated scratch repositories (Kathryn, 2026-08-21, git 2.50.1): the `reference-transaction` hook fires on `git merge --ff-only` **and** on `git update-ref` — the latter bypasses `pre-commit` entirely — and can determine at transaction time that the incoming commits already exist on a foreign branch, which is exactly what no later inspection can establish. All worktrees share the common `.git` directory, so one hook covers every worktree.
  - **Integration review: mandatory.** **Rationale (provisional — conservative default, not an architect decision):** a control agents may come to rely on, and over-trusting it is precisely the failure mode `DEC-0044-009` warns about. Weighing against a checkpoint: the hook changes no authority and blocks nothing. Set by Projektleiter Kathryn as the conservative default because only an architect may record a no-checkpoint justification; to be confirmed or downgraded by the architect, at the latest at `0044-08`.
    - **Architect checkpoint decision (2026-08-24, Architect `seven`, Seven of Nine; recorded per `process-roles.md` §Architect and the `AGENTS.md` checkpoint contract):** **confirmed — mandatory.** The hook grants no authority and blocks nothing, but it installs shared runtime machinery into every ref transaction of the common `.git`, covering all worktrees at once. Both of its failure modes — interfering with a legitimate transaction, and silently not firing while agents come to rely on it — are invisible from the implementer's own vantage, which is exactly the over-trust `DEC-0044-009` warns about. A non-implementer must look at it before it becomes ambient infrastructure.

## Acceptance criteria

- **AC-001** A stdlib-only hook detects and logs foreign-origin absorption at transaction time
- **AC-002** it never blocks a legitimate operation of the documented integration pattern (fast-forward to an item's own already-integrated successor tip)
- **AC-003** an installation path and a check that the hook is present exist
- **AC-004** the hook's own failure never corrupts a ref transaction
- **AC-005** tests cover ff-merge, `update-ref`, and the legitimate carve-outs

## Definition of Done

Committed under `_src/tools/`; installation documented in `SANDBOX.md`/`docs/pipeline/`; registered in `docs/pipeline/tools.md`. **The hook is a net, not the gate** — `DEC-0044-009` requires that a missing, removed, or bypassed hook never counts as "checked"; the integrator's checkpoint verification stays binding. This must be stated where the hook is documented.
