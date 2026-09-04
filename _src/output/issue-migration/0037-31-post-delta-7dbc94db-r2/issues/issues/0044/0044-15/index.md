---
schema_version: "1.0"
id: "0044-15"
level: "task"
parent: "0044"
state: "closed"
visibility: "internal"
prerequisites:
  - "0044-14"
  - "2026"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1244"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0044-15:0044-14 Turn the hygiene check's known blind spot into a machine finding instead of prose. Claimed via `TODO-harry-0044-15-20260822T112753Z.md`; owner_token: `agent:harry:0044-15:20260822T112753Z`. REF: `0d2497caf6967fd52445b653d0f74d8c15ac466e`. **Acceptance: ✓** (2026-08-22, Integrationscheckpoint bestanden). Reviewerin: privilegierte Integratorin `Kathryn-BEllana-20260822T114000Z`, unabhaengig von Implementierer und Dispatcher, gepinnt auf `d4a817680`. Verdikt `accepted`; **Checkpoint bestaetigt, nicht herabgestuft**. Review-REF: `11e3f1642`; Bericht: `docs/campaign-evidence/review-0044-15-20260822/report.md`. Integration nach `main`: `1ff06ccdd` (`--no-ff`, harter Preflight und Hygienepruefung `ok: true` vorab). `DEC-0044-013` erfuellt: getrennte Persona, Briefing und Kontext aufgezeichnet.

## Scope

- **Context:** `0044-14` delivered `_src/tools/check_integration_hygiene.py` and anchored it in `AGENTS.md`/`branch-workflow.md`. Its acceptance review (`Kathryn-BEllana-20260822T120000Z`, verdict `accepted`, checkpoint confirmed, REF `964e6caed`) reproduced the tool's stated limitation in a scratch repository: with a clean index but a tampered working file, the tool reports `PASS`/exit `0` while its own JSON already carries `worktree_equals_index: false`. That is exactly the residual root state of 2026-08-21 which stayed unnoticed for hours — the tool alone would have called it clean. The prose names the limitation honestly and requires the hard root preflight in addition, and the checkpoint held on that basis. But prose is a weaker control than a check, and the reviewer recorded closing it mechanically as a recommendation. Read-only confirmed a second time by QA (`harry`, 2026-08-22, in coordination with `Data`): `worktree_equals_index` is computed and emitted, but is never evaluated into a finding when `index_equals_head` is true.
  - **Assignment note (2026-08-22, Projektleiter `kathryn`):** Raised by QA (`harry`) out of the `0044-14` acceptance review. `Data` performed the scope reconciliation and confirmed that `0044-08` is the blocked, unclaimed integration/review floor and must not be claimed or edited for this correction; this Task exists so the work has its own item. Conflict-free implementation scope: `_src/tools/check_integration_hygiene.py`, `_src/tools/test_check_integration_hygiene.py`, the registered documentation named above, plus own claim and bookkeeping. No governance beyond that documentation, no acceptance, no integration, no `DONE.md`, no `main` mutation by the implementer.
  - **Implementation completion (2026-08-22, `agent:harry:0044-15:20260822T112753Z`):** `MAIN_WORKTREE_DIRTY` now reports tracked working-file divergence only for the worktree checking out `main`; ordinary unstaged changes on item branches remain deliberately non-blocking, and untracked files remain explicitly outside the check. Hermetic tests reproduce the 2026-08-21 clean-index/tampered-root state and the live-item negative case. Validation: Python 3.9.6 `py_compile`; focused `unittest` 5/5; live read-only scan across 101 registered worktrees PASS/0 findings while the dirty `0044-15` item worktree remained non-blocking; focused `automation_safety.py` PASS; `process_doc_doctor` 30 findings identical to the `main` baseline; `git diff --check` PASS. No acceptance, checkpoint crossing, integration, `0044-08` edit, `DONE.md` move, or `main` advance occurred.
  - **Integration review: mandatory.** **Rationale (provisional — conservative default, not an architect decision):** the check is a control other agents will rely on before integration, and over-trusting it is precisely the failure mode `DEC-0044-010` warns about; a false negative here re-establishes the overestimation the `0044-14` review documented. Weighing against a checkpoint: it adds a finding rather than an authority. Set by Projektleiter `kathryn`, who does not set checkpoints; the architect confirms or downgrades it with a recorded justification, at the latest at `0044-08`.
    - **Architect checkpoint decision (2026-08-24, Architect `seven`, Seven of Nine; recorded per `process-roles.md` §Architect and the `AGENTS.md` checkpoint contract):** **confirmed — mandatory; already exercised.** A control every integrator relies on, whose dangerous error direction (a false negative) is silent by construction. Crossed under review: privileged integrator `Kathryn-BEllana-20260822T114000Z`, verdict `accepted`, checkpoint confirmed at review (REF `11e3f1642`). Ratified; no downgrade.

## Acceptance criteria

- **AC-001** A finding code reports a worktree whose files diverge from its index even when the index matches `HEAD`, at minimum for the worktree in which `refs/heads/main` is checked out. The 2026-08-21 root state is covered by a regression test built from a hermetic fixture, not from the live repository. Ordinary uncommitted work in an agent's own item worktree must not become a blocking finding — the check is a quiescence requirement for integration, not an accusation against live work
- **AC-002** the chosen severity and scope make that distinction explicit and are stated where the tool is documented. `AGENTS.md`, `docs/pipeline/branch-workflow.md` and `docs/pipeline/tools.md` are updated so the prose no longer claims a gap that the tool now closes, and still states what remains uncovered

## Definition of Done

Committed with tests covering the new code firing, not firing on a clean worktree, and not firing on ordinary live work; registered documentation updated in the same change; the existing three checks and their exit-code contract are unchanged (exit `2` remains a failure, never a pass). The hard root preflight from `DEC-0044-015` stays required — this Task narrows the gap, it does not remove the second control.
