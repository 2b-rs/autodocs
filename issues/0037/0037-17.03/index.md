---
schema_version: "1.0"
id: "0037-17.03"
level: "subtask"
parent: "0037-17"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-17.02"
  - "2026"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2271"
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

PREREQ: 0037-17.03:0037-17.02 Implement bounded forward/reverse trace query APIs and machine-readable output. Claim: `TODO-Gabriel-Rhys-0037-17.03-20260825T085000Z.md`; owner_token `agent:gabriel-rhys-20260825t085000z:0037-17.03:20260825T085000Z`. **REF:** `91b848933fb055d4c51ee62ceba0a1d6e2b8e619`.

## Scope

- **Requirements covered (reciprocal downstream binding):** `RQ-TRACE-02`, `RQ-TRACE-03`, and `RQ-TRACE-04`; trace depth is file and commit level under `DEC-0040-004`.
  - **Acceptance: ✓** (2026-08-28, Integrator `belanna`, independent of Implementer `Gabriel-Rhys`, AE-4+AE-5 follow-up implementer `Quark`/`gabriel`, and lander `paul`). Product REF `91b848933fb055d4c51ee62ceba0a1d6e2b8e619`, landed `32b50e502`; first-review Review-REF `6ed2d7566` (verdict INCONCLUSIVE, AE-4 `record-version`/`curation-item`/`unresolvable` and AE-5 `_add_unique` gaps named); AE follow-up landed `5b054eb0f` (original `588eee262`) then `f191342d4` (original `ebfd52f03`); delta re-verify Review-REF `644213559` (verdict ACCEPTED, both AE-4 gaps and AE-5 duplicate-convergence plus 40-case property closed, Rhys product confirmed byte-identical blob `ceadb8ec`); land AWARD `1787895183474-8261a20b`; this AWARD `1787895955755-cb636121`. No checkpoint crossed (`0037-17.03` unflagged). No upward Feature integration performed.

## Acceptance criteria

- **AC-001** Query by issue, criterion, commit, run, campaign, finding, artifact, artifact-set, record-version, evidence, or curation item
- **AC-002** support depth/type/privacy filters, deterministic ordering, cycle markers, explicit redaction/missing results, and JSON plus concise human output without editing indexes. Queries resolve issue/criterion→evidence→file-and-commit and the reverse file-or-commit→evidence→issue/criterion. File selection resolves through validated artifact path-and-digest records. File and commit resolution are required
- **AC-003** line and symbol identities are neither required query keys nor completion or freshness gates. Missing, dangling, or unresolvable ends are explicit structured results with the exact available path and identifier, and remain distinct from authorized redaction. Queries are read-only

## Definition of Done

Tests assert both directions of the complete causal fixture, privacy enforcement, cycle termination, stable exit codes, and identical answers after index regeneration. Hermetic tests cover both directions at file and commit level, a broken link, a missing evidence set, a renamed file with preserved historical trace, explicit redaction, and identical answers after index regeneration. The tests prove that ordinary line or symbol movement does not invalidate an otherwise unchanged file/commit trace.
