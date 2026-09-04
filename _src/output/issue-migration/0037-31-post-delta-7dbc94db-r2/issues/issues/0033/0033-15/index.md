---
schema_version: "1.0"
id: "0033-15"
level: "task"
parent: "0033"
state: "closed"
visibility: "internal"
prerequisites:
  - "0033-13"
  - "0033-14"
  - "0033-15.01"
  - "1788"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:963"
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

PREREQ: 0033-15:0033-13, 0033-15:0033-14, 0033-15:0033-15.01 Establish clean-checkout, all-language, deterministic, and review-scoped validation evidence for the repaired feature.

## Scope

Claim: `DONE-worf-0033-15-20260901.md`; owner_token:
  `agent:worf:0033-15:1788275288073-b8528967`.
  - **Acceptance:** ✓
    - **Disposition:** `completed`
    - **Accepted by:** `obrien` (Miles O'Brien, Integrator for Team DeepSpace9)
    - **Authority reference:** `agent-inbox:jadzia→obrien:1788276295860-b301853d` (Offer `1788276295860-b301853d` awarded by coordinator `jadzia` per `docs/pipeline/task-acceptance.md`)
    - **Accepted at:** `2026-09-01T15:30:00Z`
  - **Baseline findings:** `RRB-VALID-001`, `RRB-REGEN-001`, `RRB-PROV-001`.
  - **Previous implementation flaws:** Task `0021-05` changed 4,503 files and silently deployed older stale history rendering; `generate.py --check` covered 428 canonical German pages rather than all translated trees/byte scope; the full validator referenced an uncommitted `check_client_rendered_german.cjs`; and passing output did not detect invalid production-bound request metadata.
  - **Completion evidence (2026-09-01):** Established clean-checkout, all-language, deterministic, and review-scoped validation evidence for Feature 0033 in dedicated worktree. Tests: 100 passed across unified review-request suite via `./test.py --layer review-request --json`. Validation bundle recorded in `docs/evidence/0033-15-validation-bundle.{json,md}`.

## Acceptance criteria

- **AC-001** Every required validator/helper/browser script is tracked and restored from a clean checkout
- **AC-002** verify the already committed migration/quarantine/actionable-rejection dispositions for delayed legacy exports and historical/malformed queue items without mutating the evidence baseline—newly discovered items reopen bounded remediation and require a fresh run
- **AC-003** the full validator, strict request gates, reports, and generation checks run with no missing optional stage silently counted as success. Define whether determinism is byte-for-byte or canonical-semantic and test all configured language trees, assets, page depths, and relevant generated reports. Inventory validation checks review-request metadata corpus-wide. Regeneration is isolated and reviewed: expected Feature `0033` output is separated from unrelated stale generator changes, with any unavoidable baseline migration already identified, approved through `0033-07.03` where privacy-relevant, committed before this validation run, and verified rather than performed here. No ignored transient output is the sole evidence, and no synthetic test artifact or queue/report model leaks into generated production files

## Definition of Done

A retained machine/human-readable validation bundle identifies source commit, dependency/tool/browser versions, exact commands, run identity, inputs, page/record/language counts, subreport completeness, findings, approved legacy dispositions, and output hashes; clean repeated runs reconcile with zero unexplained semantic differences, do not alter their own baseline, and the repository validator exits zero.
