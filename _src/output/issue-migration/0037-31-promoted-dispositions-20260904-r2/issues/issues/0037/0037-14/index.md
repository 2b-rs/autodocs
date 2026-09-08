---
schema_version: "1.0"
id: "0037-14"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-08"
  - "0037-09"
  - "0037-13"
  - "2026"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2336"
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
---

## Goal

PREREQ: 0037-14:0037-08, 0037-14:0037-09, 0037-14:0037-13 Implement `_src/tools/issue_import_legacy.py` as a deterministic importer into an arbitrary disposable root. **Claim:** `TODO-benjamin-0037-14-20260828.md` (`owner_token: agent:deepspace9:0037-14:20260828T223500Z`). **Implementation completion (2026-08-25, Gabriel-Tilly, unprivileged Programmer):** REF `fb6c8d5956635de502d9e4eeeb62901c418c6a4e`. Deterministic importer writes only under a supplied disposable root; repeated imports are byte-identical (`tree_digest`); live issues/provenance/queue roots and path-escape writes are refused. Validation: `python3 _src/tests/test_issue_import_legacy.py` 8/8 PASS; `py_compile` PASS. No `claim.json`/`closure.json` fabricated; Feature `0021` archived-not-accepted; local-20260815-0021-06..08 receive no evidence credit. **Acceptance: ✓** (2026-08-29T11:24Z, Integrator `obrien`, unabhängig von Implementierer `Gabriel-Tilly` / `agent:gabriel-tilly-20260825t084200z:0037-14:20260825T084200Z` und Dispatcher `benjamin` / `agent:benjamin:0037-14:20260828T223500Z`). Abgenommene Baseline `fb6c8d5956635de502d9e4eeeb62901c418c6a4e`; 8/8 importer tests OK, 126/126 test_issue suite OK, integration hygiene PASS; AWARD `1788002410956-91037acc`. No checkpoint crossed or upward Feature integration performed.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Read named files from an exact Git commit/archive
- **AC-002** preserve IDs/text/source locators/dependencies
- **AC-003** assign `AC-NNN` by legacy document order
- **AC-004** map states/archives under the approved contract
- **AC-005** retain real refs and typed unresolved placeholders without fabricated evidence
- **AC-006** emit no claim/closure/approval absent source support
- **AC-007** create stable blocking findings for ambiguity
- **AC-008** and refuse live `issues/`, provenance, queue, evidence, or generated-output roots

## Definition of Done

Repeated imports of one source commit are byte-identical; malicious/path-confusion and malformed fixtures fail safely; mutation guards prove writes remain under the supplied temporary root.
