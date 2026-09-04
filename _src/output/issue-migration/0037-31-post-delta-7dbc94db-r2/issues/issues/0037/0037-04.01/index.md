---
schema_version: "1.0"
id: "0037-04.01"
level: "subtask"
parent: "0037-04"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2043"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0037-04.01:0037-02 Define typed references, relation semantics, IDs, immutable events, runs, findings, and evidence/privacy classes. REF: 9aae0b7a295800478bc8eb0d0df795283b28c2a5 **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `agent:perplexity:0037-04.01`). Abgenommene Baseline `9aae0b7a295800478bc8eb0d0df795283b28c2a5`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). Vier Provenance-Schemas vorhanden, JSON-syntaktisch gültig.

## Scope

- **Closure (2026-08-16):** Completed all four required schemas, canonical URI-kind and relation endpoint constraints, UUIDv7/replay/collision and privacy/redaction rules, complete endpoint/relation examples, and isolated invalid coverage for every endpoint, relation, classification, and environment rule. Validation passed. REF: `9aae0b7a295800478bc8eb0d0df795283b28c2a5`.

## Acceptance criteria

- **AC-001** `provenance/_schema/typed-reference-v1.schema.json`, `provenance-event-v1.schema.json`, `run-v1.schema.json`, and `finding-v1.schema.json` cover issue/criterion/commit/run/campaign/finding/decision/artifact/artifact-set/record-version/evidence/curation-item endpoints and directional/cardinality rules for detected-during, reported-by, remediates, implements, verifies, triggered, produced-by, derived-from, invalidated-by, regenerated-by, supersedes, published-as, decides, and blocks. Use UUIDv7 for events/runs/findings, canonical typed URIs for references, and explicit synthetic/development-test/production/assessment plus public/internal/restricted classifications

## Definition of Done

Review-ready schemas, relation table, redaction rules, ID collision/replay rules, complete examples, and one invalid fixture per endpoint/relation/classification rule are committed.
