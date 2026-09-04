---
schema_version: "1.0"
id: "0020-10"
level: "task"
parent: "0020"
state: "closed"
visibility: "internal"
prerequisites:
  - "0020-01"
  - "0020-02"
  - "0020-03"
  - "0020-04"
  - "0020-05"
  - "0020-06"
  - "0020-07"
  - "0020-08"
  - "0020-09"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2669"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0020-10:0020-01, 0020-10:0020-02, 0020-10:0020-03, 0020-10:0020-04, 0020-10:0020-05, 0020-10:0020-06, 0020-10:0020-07, 0020-10:0020-08, 0020-10:0020-09 Assemble and validate the terminal Feature `0020` integration package without changing the completed child products. Reconcile the ECU scope and supplied-product boundary, responsibility and applicability matrices, evidence-origin/refusal rules, assessment input, work-product/evidence catalogue, and selected-profile execution register into one exact source/REF manifest; retain digest and validation evidence, contrary evidence, complete finding dispositions, recovery instructions, and a prerequisite-closed review/Acceptance handoff. A child inconsistency is returned through a separately owned correction and is not silently repaired here. This Task does not claim ECU process execution, a `PA 1.1` or capability rating, ISO/SAE 21434 or ISO 26262 performance, release approval, residual-risk acceptance, Task Acceptance, or Feature closure. *(terminal integrating task; Implementer, Architect, and Integrator identities distinct)*

## Scope

- **Architecture authority:** `DEC-0020-003`; supporting review `docs/dossiers/0020-feature-closure-architecture-review.md` (`scope-ok-with-conditions`).
  - **Work products and write scope:** `docs/dossiers/0020-terminal-integration-package.md`, `docs/dossiers/0020-terminal-integration-manifest.json`, the worker's canonical awarded claim, and this `0020-10` block for marker/claim/REF bookkeeping only. Branch `0020-10` is pre-provisioned from the Feature `0020` integration baseline containing this governance candidate and every done prerequisite tip.
  - **Test derivation:** integration checks derive from cross-product consistency, evidence-origin refusal, and closure/checkpoint risks. Retain positive and missing/stale/wrong-origin/unsupported-claim/child-conflict fixture results plus `legacy_task_doctor.py`, `process_doc_doctor.py`, and `git diff --check` evidence; exact manifest fields and recovery contract are fixed by the supporting review.
  - **Capability profile:** `unprivileged` Implementer; direct Git and stdlib validation; cognitive demand `high`; large context; CPU under 20 minutes, memory under 1 GiB; no network, credentials, external effects, Acceptance, checkpoint crossing, or `main` advance. The mandatory checkpoint requires a separately assigned `privileged` Integrator.
  - **Integration review: mandatory.** **Rationale (architect):** this is Feature `0020`'s single terminal integrating Task and review floor. Eleven downstream Features consume the parent boundary; a false pass can propagate substituted evidence, an inconsistent responsibility/applicability model, or unsupported rating/release claims into execution, release, and assessment gates.

## Acceptance criteria

- **AC-001** (1) Every Task `0020-01` through `0020-09` is pinned by exact implementation REF and work-product digest, and every prerequisite/claim/review input used by the package is identified. (2) A deterministic consistency matrix proves that the ECU boundary, internal/shared/external responsibility, 14-process applicability, evidence-origin rules, worksheets, catalogue, and selected-profile register agree, or records a blocking returned finding. (3) Validation rejects missing/stale/wrong-origin/cross-product evidence and unsupported ECU-execution, rating, safety, cybersecurity, release, or closure claims without activating a repository-wide default gate. (4) All contrary evidence and findings have explicit open/returned/closed dispositions, owners, and immutable evidence references. (5) The package records recovery and exact handoff data for prerequisite-closed Acceptance and the separately assigned mandatory checkpoint
- **AC-002** it does not perform either action

## Definition of Done

A committed package report and manifest identify the exact candidate, source REFs and digests, consistency/validation commands and results, findings and recovery; identifier/prerequisite/cycle/marker validation and `git diff --check` pass; a distinct privileged Integrator receives the unchanged candidate for the mandatory review. No child deliverable, `Acceptance: ✓`, `DONE.md`, selected-profile responsibility, ECU execution evidence, rating, or release state is changed by implementation completion.
