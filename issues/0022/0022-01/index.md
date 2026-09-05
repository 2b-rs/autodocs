---
schema_version: "1.0"
id: "0022-01"
level: "task"
parent: "0022"
state: "open"
visibility: "internal"
prerequisites:
  - "0020-09"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2701"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0022-01:0020-09 Define the per-process system interface plan without waiting for future outputs: for each `SYS.1`–`SYS.5` process, record assessment disposition separately from internal/shared/external execution responsibility, including the assessed unit's exact outcome/activity boundary for every shared process, performer/authority, required input and output types, internal predecessor task or external acceptance gate, configuration/change/problem/risk feedback, and exact completion/evidence gate.

## Scope

- **Implements:** `DEC-0022-001` ([`dec-0022-001.md`](docs/dossiers/dec-0022-001.md)); decomposition per [`0022-feature-breakdown-proposal.md`](docs/dossiers/0022-feature-breakdown-proposal.md).
  - **Integration review: mandatory.** **Rationale (architect):** recorded by Architect `data` in `DEC-0022-001` and its supporting independent review (`PART-01`, `saru`, `scope-ok-with-conditions`): this is the shared cross-Feature interface baseline consumed by at least six later work units, and a false pass can create internal SYS credit or admit an unowned external baseline.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
