---
schema_version: "1.0"
id: "0044-03"
level: "task"
parent: "0044"
state: "closed"
visibility: "internal"
prerequisites:
  - "0044-01"
  - "2026"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1098"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0044-03:0044-01 Answer "Integrationstests?": define which integration tests checkpoints require and how their scope and kind are derived from the architecture. *(architect-elaboration)* REF `431cb9790824a94eebc5bb59e27d6410d2169467` (branch `0044-03`, nach `main` integriert mit Merge `5e1ee62df`). Claim: `TODO-seven-0044-03-20260823T143745Z.md` (`agent:seven:0044-03:20260823T143745Z`, dispatched by `kathryn` under the current-user selection of 2026-08-23; supersedes released preparation claim `TODO-Data-Iris-0044-03-20260822T150415Z.md`, preserved as provenance). Gate state: `DEC-0044-019` and the Architect scope review `docs/dossiers/0044-03-gate-scope-review.md` (verdict `scope-ok-mit-auflagen`) are integrated on `main` — both pre-mutation requirements of the cross-item gate-scope exception were satisfied before implementation. **Implementation complete (2026-08-23, `agent:seven:0044-03:20260823T143745Z`):** New binding rule `docs/pipeline/integration-test-obligation.md` — the integrator executes a checkpoint-specific verification set against the exact integrated candidate, derived via a five-category matrix (architecture risks/seams, interfaces/contracts, invariants, negative/failure/recovery modes, external effects), with a nine-point reproducible evidence minimum, explicit no-automation semantics (bounded manual fallback or checkpoint failure via the existing `[u]` verdict — never a silent pass), strict separation from acceptance authority, and staged activation exactly per `DEC-0044-019` (Feature-`0044` trial checkpoints now; repository-wide dormant until the `0043-07` example is executed and `0044-08` confirms it). Worked example applied to real pending integration `0043-07`: `docs/campaign-evidence/0044-03-worked-example/integration-0043-07-derivation.md`. DoD references added in `task-acceptance.md` §4, `branch-workflow.md` Feature-integration step 4, and `docs/pipeline/README.md`. Validation: `process_doc_doctor` — zero findings attributable to this Task; the single pre-existing error (root-relative link inside a verbatim `AGENTS.md` quote in the Data-Iris preparation dossier) is dispositioned in the claim, not repaired, to preserve quote integrity. Checkpoint inventory re-pinned, identical to `DEC-0044-019` CON-02. Governance-Deliverables mit Merge `5e1ee62df` nach `main` integriert (privilegiert, 2026-08-23); no `Acceptance: ✓` created; no checkpoint crossed.

## Scope

- **Requirements covered:** `RQ-IP-07`.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** adds a review obligation rather than a capability; failure mode is a documented gap, caught at `0044-08`.

## Acceptance criteria

- **AC-001** A documented rule states what an integrator must execute (not only read) at a checkpoint, how the test obligation is derived from the architecture and interface contracts of the integrated items, what evidence the run leaves, and what happens when no automated test exists
- **AC-002** the rule is applied to at least one real pending integration as a worked example

## Definition of Done

Committed; `task-acceptance.md` and `branch-workflow.md` reference the rule; the worked example is retained as evidence.
