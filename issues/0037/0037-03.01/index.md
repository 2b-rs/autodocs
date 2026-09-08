---
schema_version: "1.0"
id: "0037-03.01"
level: "subtask"
parent: "0037-03"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-02"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2027"
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
---

## Goal

PREREQ: 0037-03.01:0037-02 Define lifecycle transitions, criterion evidence, decisions, and terminal records in `docs/pipeline/issue-lifecycle.md`. **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `agent:perplexity:0037-03.01`). Abgenommene Baseline `f3adcde91487f774d29b80985f54a5736da556bd`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). issue-lifecycle.md + zwei Schemas vorhanden.

## Scope

- **Closure (2026-08-16):** Lifecycle contract, closure and decision schemas, and positive/negative fixtures were committed in `f3adcde91487f774d29b80985f54a5736da556bd`. JSON syntax and lifecycle fixture semantic checks passed. `9e033f327762e26ba8730ae8ac3e09b388017295` records the initial REF bookkeeping; its heredoc quoting defect omitted this note but did not alter the substantive deliverables. This repair restores the missing closure evidence additively.

## Acceptance criteria

- **AC-001** Map `[ ]/[u]/[p]/[?]/[w]/[x]`
- **AC-002** reserve `[u]` for the next unresolved human decision
- **AC-003** define roles and transition authority
- **AC-004** require checked `AC-NNN` entries with reachable evidence and `closure.json` for completion
- **AC-005** distinguish completed, wontfix, superseded, duplicate, cancelled, and archived-not-accepted
- **AC-006** preserve Feature `0021`'s historical non-acceptance
- **AC-007** and retain the two-commit rule for real commit refs

## Definition of Done

`issues/_schema/issue-closure-v1.schema.json`, `issues/_schema/issue-decision-v1.schema.json`, transition table, authority matrix, and positive/negative fixtures are review-ready and committed.
