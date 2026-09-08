---
schema_version: "1.0"
id: "0033-01"
level: "task"
parent: "0033"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:770"
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
  - id: "AC-006"
    status: "active"
  - id: "AC-007"
    status: "active"
  - id: "AC-008"
    status: "active"
  - id: "AC-009"
    status: "active"
---

## Goal

Reproduce and freeze the post-implementation defect baseline without writing to production queues, records, generated sources, or user-owned output. <!-- REF: 93cafc16acaa7222570c230605bf088f279b13f4 -->

## Scope

- **Completion evidence (2026-08-16):** The v1 matrix is `docs/pipeline/review-request-baseline-audit.md`; the pinned manifest/reproducer and 11 focused tests are tracked under `_src/`; retained report `logs/review-request-baseline/0033-01-baseline-v1.json` has SHA-256 `4905b557ebda00618165584e7a152bdf5ea17d796ab26a37be7452293b7e4dc3`.
  - **Baseline result:** 8/8 historical observations and the exact 25/25 focused Feature `0021` tests reproduced; all three `local-*` labels remain `unrecoverable / no independent evidence credit`, with mixed checkpoint trees recorded only as contextual evidence. Every later `0033` Task references one or more stable `RRB-*` findings.
  - **Validation and isolation:** Python compilation, 11 focused tests, relative links, whitespace, report/tool/manifest digest consistency, and full `_src/validate.py` passed. Git status and real `_src/spec/{curation,review}-queue` byte-tree digests were unchanged before/after probes; no production record/generated/user output or root `run.sh` was touched.
  - **Previous implementation flaws to preserve as regression evidence:** The prior 25 focused tests and German generation check passed despite permissive schema validation, optional live-target verification, nonconformant queue normalization, missing production metadata, and absent no-JavaScript behavior. Synthetic fixtures supplied a complete `review_request` object that no production record contained. Later Tasks `0021-06`–`0021-08` were closed with local placeholder refs and must not be treated as independently reproducible evidence.

## Acceptance criteria

- **AC-001** A versioned audit harness runs against the historical committed refs and records commands, tool versions, expected observations, exact artifact hashes, and the committed ref or reproducible tree/patch hash for each later `local-*` closure claim, or an explicit `unrecoverable / no evidence credit` disposition when no task-specific snapshot ever existed
- **AC-002** audit the available cumulative tree without fabricating provenance. It reproduces at the historical refs at least: acceptance of malformed/reserved trust fields
- **AC-003** the non-string-ID `TypeError`
- **AC-004** ingestion without live lookup
- **AC-005** wrong canonical/status/origin/conformance mapping
- **AC-006** one real production page with bare/null target metadata
- **AC-007** the absence of a no-JavaScript path
- **AC-008** and the gap between passing tests and failing production acceptance. Desired fixed behavior is registered as explicitly pending forward regression IDs whose passing gates belong to later implementation/closure tasks
- **AC-009** `0033-01` does not depend on the fixes. Probes use temporary isolated queue/store roots and prove the working tree and real `_src/spec/*-queue` remain unchanged. Audit the implementation, operating guidance, validation claims, release decision, and residual-limit wording of `0021-06`–`0021-08` in addition to `0021-01`–`0021-05`

## Definition of Done

`docs/pipeline/` contains a human-readable finding matrix keyed to every original task/commit-or-tree/criterion; machine-readable baseline fixtures or a reproducer deterministically demonstrate the historical observations and identify pending forward assertions; every later `0033` task references one or more finding IDs.
