---
schema_version: "1.0"
id: "0037-04.02"
level: "subtask"
parent: "0037-04"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-04.01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2048"
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

PREREQ: 0037-04.02:0037-04.01 Define artifact identity, manifests, storage, indexing inputs, and digest rules REF: b6ebe46faf81cc3cf95def6c7d7e52304fd6a072 **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `agent:perplexity:0037-04.02`). Abgenommene Baseline `b6ebe46faf81cc3cf95def6c7d7e52304fd6a072`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). artifact-set-v1.schema.json + 4 Fixtures vorhanden.

## Scope

- **Closure (2026-08-16):** Defined artifact-set@v1 schema, file/tree digest rules, one-file storage pinning, and disposable index views. Validation passed in request `a1b2c3d4e5f6-impl01`. REF: `b6ebe46faf81cc3cf95def6c7d7e52304fd6a072`.

## Acceptance criteria

- **AC-001** `provenance/_schema/artifact-set-v1.schema.json` uses SHA-256 over canonical JSON
- **AC-002** mutable files require repository-relative path plus byte digest, size, media type, and source commit
- **AC-003** trees use sorted member manifests and a tree digest. Pin one-file stores and atomic create semantics at `provenance/events/YYYY/MM/`, `provenance/artifact-sets/`, `provenance/runs/`, and `provenance/findings/YYYY/MM/`
- **AC-004** indexes under `provenance/_views/` are disposable and never relation authority

## Definition of Done

Review-ready schema and fixtures prove file/tree digest changes, member ordering independence, duplicate/collision rejection, redaction, and index reconstruction inputs.
