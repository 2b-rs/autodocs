---
schema_version: "1.0"
id: "0037-08"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-02"
  - "0037-07"
  - "0037-39"
  - "2026"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2219"
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

PREREQ: 0037-08:0037-02, 0037-08:0037-07, 0037-08:0037-39 Implement `_src/tools/issue_store.py`: canonical discovery, strict front-matter/Markdown parsing, and normalized in-memory/JSON representation. **Claim:** `TODO-julian-0037-08-20260824T164500Z.md` (`agent:julian:0037-08:20260824T164500Z`). **Implementation completion (2026-08-24, Julian, unprivileged Programmer):** REF `4376be766decd03830a5feeec7dcc6b41cfd87ce`. The side-effect-free parser enforces canonical paths and path-derived identity, the pinned safe YAML profile and constrained Markdown structure, AC lifecycle/tombstones with byte/line locators, closed `issue-item@v1` fields, deterministic normalized JSON, and source/schema/tool digests; resource and malformed-input failures use actionable `IS08xx` rule IDs. Validation: focused suite 10/10 PASS; package schema fixtures 3 valid + 14 invalid PASS; CLI/golden output byte-identical at SHA-256 `b3af27a7b087eee7aedbca9fd88cbeb838d64a8f9dc01f730a49c7e8488f003a`; `py_compile`, 0037-39 toolchain check, automation-safety, and `git diff --check` PASS. **Acceptance: ✓** (2026-08-27, Integrator `paul`, unabhängig von Implementierer `Julian` / `agent:julian:0037-08:20260824T164500Z`). Abgenommene Baseline `4376be766decd03830a5feeec7dcc6b41cfd87ce`; Review-REF `b6d2bfdfe4850ad2cf7c1d898105088409e01378`; AWARD `1787865994204-934c578e`. No checkpoint crossed or upward integration performed. The separately reported accidental root/main merge incident remains outside this Task's recovery authority and is retained in the claim.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Use only the approved pinned dependency/profile
- **AC-002** discover only canonical paths
- **AC-003** retain `AC-NNN` IDs/tombstones and byte/line source locators
- **AC-004** expose every approved field without lossy prose round trips
- **AC-005** reject path/parent/prefix mismatches, duplicate keys/IDs, ambiguous scalars, forbidden YAML constructs, unknown schema versions, and resource-limit violations. Canonical normalized JSON uses deterministic key/list rules and contains source/schema/tool digests

## Definition of Done

Unit, property, fuzz-seed, and golden tests cover all contract fixtures, Unicode, limits, ordering independence, malformed front matter/Markdown, and byte-stable normalized output; dependency lock and install instructions reproduce the tested environment.
