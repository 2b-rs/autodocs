---
schema_version: "1.0"
id: "0038-35"
level: "task"
parent: "0038"
state: "open"
visibility: "internal"
prerequisites:
  - "0038-01"
  - "0038-02"
  - "0038-03"
  - "0038-04"
  - "0038-05"
  - "0038-05.01"
  - "0038-05.02"
  - "0038-06"
  - "0038-07"
  - "0038-08"
  - "0038-09"
  - "0038-10"
  - "0038-11"
  - "0038-12"
  - "0038-13"
  - "0038-14"
  - "0038-15"
  - "0038-16"
  - "0038-16.01"
  - "0038-16.02"
  - "0038-17"
  - "0038-18"
  - "0038-19"
  - "0038-20"
  - "0038-21"
  - "0038-22"
  - "0038-23"
  - "0038-24"
  - "0038-25"
  - "0038-26"
  - "0038-27"
  - "0038-28"
  - "0038-29"
  - "0038-30"
  - "0038-31"
  - "0038-32"
  - "0038-33"
  - "0038-34"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1943"
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
---

## Goal

PREREQ: 0038-35:0038-17, 0038-35:0038-01, 0038-35:0038-02, 0038-35:0038-18, 0038-35:0038-25, 0038-35:0038-03, 0038-35:0038-04, 0038-35:0038-05, 0038-35:0038-05.01, 0038-35:0038-05.02, 0038-35:0038-06, 0038-35:0038-07, 0038-35:0038-08, 0038-35:0038-09, 0038-35:0038-10, 0038-35:0038-11, 0038-35:0038-12, 0038-35:0038-13, 0038-35:0038-14, 0038-35:0038-26, 0038-35:0038-29, 0038-35:0038-34, 0038-35:0038-33, 0038-35:0038-32, 0038-35:0038-31, 0038-35:0038-30, 0038-35:0038-27, 0038-35:0038-15, 0038-35:0038-19, 0038-35:0038-20, 0038-35:0038-21, 0038-35:0038-22, 0038-35:0038-23, 0038-35:0038-24, 0038-35:0038-28, 0038-35:0038-16, 0038-35:0038-16.01, 0038-35:0038-16.02 Assemble, independently review, and integrate the complete Feature `0038` closure package. *(terminal integrating task restored by `DEC-0038-005`; architect contract: `docs/campaign-evidence/0038-35/architect-terminal-integration-contract.md`)*

## Scope

- **Implementation order and separation:** A privileged Implementer distinct from Architect Data prepares the aggregate manifest, validation evidence, and closure candidate without accepting or integrating. Independent privileged structured reviewer(s) issue fresh append-only Task decisions for exact pinned `0038-33` and `0038-34` baselines and review the complete prerequisite-closed batch bottom-up. A separately assigned privileged terminal Integrator, distinct from Architect and Implementers, performs the mandatory checkpoint/Feature aggregate review and alone may integrate or close.
  - **Integration review:** **mandatory.** **Rationale (architect):** Architect Data, `DEC-0038-005`: this is Feature `0038`'s exactly-one terminal integrating task and review floor. It composes repository-wide transaction, automation-safety, evidence, runner, publication, and authority controls; a false pass could close the Feature while stale or rejected work remains.
  - **Capability profile:** Implementer `privileged`, cognitive `high`, context `very-large`, direct Git/local validation only; structured reviewers and terminal Integrator `privileged`, independent, cognitive `critical`, exact candidate/target assignment. No role gains authority from capability class, and no network, credentials, publication, or external effect is implied.

## Acceptance criteria

- **AC-001** All 38 pre-existing Feature work units are terminal, reachable, and represented exactly once in a digest-bound aggregate manifest with contract, work-product, marker/REF, Acceptance, review-evidence, validation, recovery, and TODO/DONE block digests. `0038-33` and `0038-34` each have a fresh structured Acceptance decision at their current pinned baseline
- **AC-002** existing acceptances and every historical rejection remain append-only evidence and are not rewritten. The induced prerequisite-closed batch is current and passing
- **AC-003** focused `0038-33`/`0038-34` suites, repository validation, automation-safety validation, backlog/claim/decision structure, manifest recomputation, and `git diff --check` pass on the exact candidate. The 2026-08-21 partial-integration note and R-6 remain unchanged history
- **AC-004** `DEC-0038-005` supersedes only the no-closure condition

## Definition of Done

The implementation and independent review evidence are committed with real REFs and digests; the terminal Integrator records a passing checkpoint and Feature aggregate verdict on the exact candidate, with hygiene and root preflight passing before/after. Only then does the same authorized closure act preserve the complete Feature record while moving Feature `0038` from `TODO.md` to `DONE.md`. Any rejected/inconclusive review, stale pin, missing digest, changed historical record, validation failure, or independence defect stops closure and is recorded append-only; no partial DONE move or silent Integrator repair.
